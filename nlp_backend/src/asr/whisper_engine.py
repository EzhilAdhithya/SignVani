"""
faster-whisper ASR Engine Wrapper

Thread-safe singleton for offline speech recognition using CTranslate2 int8
quantization. Designed for Raspberry Pi 4 within the <500 MB RAM / <1.5 s
latency envelope (tiny.en model).
"""

import logging
import threading
from typing import Optional, Tuple

import numpy as np

from config.settings import whisper_config, audio_config
from src.utils.exceptions import ModelLoadError

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel as _WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    _WhisperModel = None  # type: ignore
    logger.warning("faster-whisper not installed — WhisperEngine unavailable. "
                   "Install with: pip install faster-whisper")


class WhisperEngine:
    """
    Thread-safe singleton that wraps faster-whisper (CTranslate2 backend).

    Loads once at startup and performs a silent-zeros warmup pass to eliminate
    first-inference JIT latency on RPi4.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            if not FASTER_WHISPER_AVAILABLE:
                raise ModelLoadError(
                    "faster-whisper is not installed. "
                    "Run: pip install faster-whisper")

            self._sample_rate: int = audio_config.SAMPLE_RATE
            self._model: Optional[_WhisperModel] = None
            self._load_model()
            self._initialized = True

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """Download (first run) or load the CTranslate2 Whisper model."""
        import os
        os.makedirs(whisper_config.MODEL_DIR, exist_ok=True)

        logger.info(
            "Loading WhisperModel '%s' "
            "(device=%s, compute_type=%s, model_dir=%s)...",
            whisper_config.MODEL_SIZE,
            whisper_config.DEVICE,
            whisper_config.COMPUTE_TYPE,
            whisper_config.MODEL_DIR,
        )
        try:
            self._model = _WhisperModel(
                whisper_config.MODEL_SIZE,
                device=whisper_config.DEVICE,
                compute_type=whisper_config.COMPUTE_TYPE,
                download_root=whisper_config.MODEL_DIR,
            )
        except Exception as exc:
            raise ModelLoadError(
                f"Failed to load WhisperModel '{whisper_config.MODEL_SIZE}': {exc}"
            ) from exc

        logger.info("WhisperModel loaded. Running warmup pass...")
        self._warmup()
        logger.info("WhisperEngine ready.")

    def _warmup(self) -> None:
        """
        Run one inference over a silent 1-second array.

        CTranslate2 compiles operation graphs on first use; the warmup
        absorbs that cost so the first real utterance is fast.
        Non-fatal if it fails.
        """
        silence = np.zeros(self._sample_rate, dtype=np.float32)
        try:
            segments, _ = self._model.transcribe(
                silence,
                language=whisper_config.LANGUAGE,
                beam_size=whisper_config.BEAM_SIZE,
                vad_filter=whisper_config.VAD_FILTER,
            )
            list(segments)  # faster-whisper uses lazy generators
        except Exception as exc:
            logger.debug("WhisperEngine warmup failed (non-fatal): %s", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def transcribe(
        self,
        audio_np: np.ndarray,
        vad_filter: Optional[bool] = None,
    ) -> Tuple[str, float]:
        """
        Transcribe a float32 audio waveform at 16 kHz.

        Args:
            audio_np:   float32 array of shape (N,), values in [-1.0, 1.0]
            vad_filter: Override the config VAD setting.
                        Pass ``False`` for pre-recorded file uploads so that
                        the Silero VAD does not discard low-level speech.
                        Defaults to ``whisper_config.VAD_FILTER`` (True).

        Returns:
            (text, avg_confidence) — text is empty string on failure.

        Note:
            avg_logprob from faster-whisper is in (-∞, 0]. Values near 0
            indicate high confidence. We map it to [0, 1] via
            ``min(1.0, max(0.0, logprob + 1.0))`` as a rough proxy.
        """
        if self._model is None:
            return "", 0.0

        use_vad = whisper_config.VAD_FILTER if vad_filter is None else vad_filter

        # Timeout slightly longer than SILENCE_TIMEOUT to avoid starving the
        # accumulate-then-flush pattern in WhisperASRWorker.
        if not self._lock.acquire(timeout=5.0):
            logger.warning("WhisperEngine: lock acquisition timeout (5 s)")
            return "", 0.0

        try:
            segments, _ = self._model.transcribe(
                audio_np,
                language=whisper_config.LANGUAGE,
                beam_size=whisper_config.BEAM_SIZE,
                vad_filter=use_vad,
                vad_parameters={"speech_pad_ms": 200},
            )

            parts = []
            confidences = []
            for seg in segments:
                stripped = seg.text.strip()
                if stripped:
                    parts.append(stripped)
                    # avg_logprob ∈ (-∞, 0]; clamp to [0, 1]
                    conf = min(1.0, max(0.0, seg.avg_logprob + 1.0))
                    confidences.append(conf)

            text = " ".join(parts)
            avg_conf = (sum(confidences) / len(confidences)
                        if confidences else 0.0)
            return text, avg_conf

        except Exception as exc:
            logger.error("WhisperEngine transcription error: %s", exc)
            return "", 0.0
        finally:
            self._lock.release()

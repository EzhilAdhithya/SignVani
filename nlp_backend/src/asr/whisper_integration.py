"""
faster-whisper ASR Integration for SignVani

Provides WAV file transcription using the WhisperEngine singleton.
The public interface mirrors VoskASR so api_server.py needs no changes:

    engine = WhisperASR()
    text   = engine.transcribe_audio_file(wav_bytes)  # -> str
"""

import io
import logging
import wave
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

try:
    import scipy.signal as _scipy_signal
    _RESAMPLE_AVAILABLE = True
except ImportError:
    _RESAMPLE_AVAILABLE = False

try:
    from src.asr.whisper_engine import WhisperEngine, FASTER_WHISPER_AVAILABLE
except Exception as _import_err:
    FASTER_WHISPER_AVAILABLE = False
    WhisperEngine = None  # type: ignore
    logger.warning("WhisperEngine unavailable: %s", _import_err)


class WhisperASR:
    """
    File-upload ASR engine backed by faster-whisper.

    Same public API as VoskASR so callers (api_server.py) require no changes.
    """

    def transcribe_audio_file(self, audio_data: bytes) -> str:
        """
        Transcribe WAV audio bytes to text.

        Args:
            audio_data: WAV bytes — any sample rate, mono or stereo.

        Returns:
            Transcribed text string, or empty string on failure / unavailability.
        """
        if not FASTER_WHISPER_AVAILABLE:
            logger.warning(
                "faster-whisper not available — install with: pip install faster-whisper"
            )
            return ""

        try:
            audio_np = self._to_16k_mono_float32(audio_data)
            engine = WhisperEngine()
            # Disable VAD for pre-recorded file uploads — the Silero VAD
            # threshold (0.5) can incorrectly strip low-level or compressed
            # speech in short recordings. VAD is still used for the live
            # streaming worker (WhisperASRWorker).
            text, confidence = engine.transcribe(audio_np, vad_filter=False)
            logger.info("Whisper transcript: '%s' (conf=%.2f)", text, confidence)
            return text
        except Exception as exc:
            logger.error("WhisperASR.transcribe_audio_file error: %s", exc)
            return ""

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_16k_mono_float32(audio_data: bytes) -> np.ndarray:
        """
        Normalise any WAV to a 16 kHz mono float32 numpy array.

        Steps:
        1. Parse WAV header (sample rate, channel count, bit-depth).
        2. Downmix to mono by averaging channels.
        3. Resample to 16 kHz (scipy polyphase filter, or simple decimation
           fallback if scipy is unavailable).
        4. Normalise to [-1.0, 1.0] float32.

        Args:
            audio_data: Raw WAV bytes.

        Returns:
            float32 ndarray suitable for faster-whisper's transcribe().
        """
        with wave.open(io.BytesIO(audio_data)) as wf:
            src_rate = wf.getframerate()
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            raw_frames = wf.readframes(wf.getnframes())

        # Decode to float32 working array
        dtype = np.int16 if sampwidth == 2 else np.int32
        samples = np.frombuffer(raw_frames, dtype=dtype).astype(np.float32)

        # Downmix to mono
        if n_channels > 1:
            samples = samples.reshape(-1, n_channels).mean(axis=1)

        # Resample to 16 kHz
        target_rate = 16_000
        if src_rate != target_rate:
            if _RESAMPLE_AVAILABLE:
                num_samples = int(len(samples) * target_rate / src_rate)
                samples = _scipy_signal.resample(samples, num_samples)
            else:
                # Simple decimation — lower quality but no extra deps
                step = src_rate / target_rate
                indices = np.arange(0, len(samples), step).astype(int)
                indices = indices[indices < len(samples)]
                samples = samples[indices]

        # Normalise to [-1.0, 1.0]
        max_val = float(np.iinfo(np.int16).max)  # 32767
        return np.clip(samples / max_val, -1.0, 1.0).astype(np.float32)

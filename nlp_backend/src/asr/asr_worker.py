"""
ASR Worker Thread

Consumes processed audio chunks from the queue and runs ASR.
Produces TranscriptEvents.
"""

import queue
import threading
import logging
import numpy as np
from typing import Optional

from src.asr.vosk_engine import VoskEngine
from src.nlp.dataclasses import AudioChunk, TranscriptEvent
from config.settings import pipeline_config
from src.utils.exceptions import ASRError

logger = logging.getLogger(__name__)


class ASRWorker(threading.Thread):
    """
    Worker thread that runs Vosk ASR on incoming audio chunks.
    """

    def __init__(self,
                 input_queue: queue.Queue,
                 output_queue: queue.Queue):
        """
        Initialize ASR worker.

        Args:
            input_queue: Queue containing AudioChunk objects
            output_queue: Queue to put TranscriptEvent objects
        """
        super().__init__(name="ASRWorker")
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.daemon = True  # Daemon thread
        self._is_running = False
        self._engine: Optional[VoskEngine] = None

    def run(self):
        """Main loop."""
        logger.info("ASR Worker starting...")
        try:
            self._engine = VoskEngine()
        except Exception as e:
            logger.error(f"Failed to initialize Vosk Engine: {e}")
            return

        self._is_running = True

        while self._is_running:
            try:
                # Get chunk with timeout to allow checking _is_running
                chunk: AudioChunk = self.input_queue.get(timeout=1.0)

                # Convert float32 back to int16 bytes for Vosk
                # Clip to avoid overflow before casting
                # AudioChunk data is float32 [-1.0, 1.0]
                audio_int16 = (np.clip(chunk.data, -1.0, 1.0)
                               * 32767).astype(np.int16)
                audio_bytes = audio_int16.tobytes()

                # Process
                result = self._engine.process_audio(audio_bytes)

                if result and 'text' in result and result['text']:
                    text = result['text']
                    logger.info(f"ASR Recognized: {text}")

                    # Extract confidence from Vosk result if available
                    # Vosk provides word-level confidence in 'result' array
                    confidence = 1.0
                    if 'result' in result and result['result']:
                        # Average word confidences
                        word_confs = [w.get('conf', 1.0)
                                      for w in result['result']]
                        confidence = sum(word_confs) / \
                            len(word_confs) if word_confs else 1.0

                    event = TranscriptEvent(
                        text=text,
                        confidence=confidence,
                        is_final=True
                    )

                    # Put to output queue
                    try:
                        self.output_queue.put(event, timeout=0.5)
                    except queue.Full:
                        logger.warning("Transcript queue full, dropping event")

                self.input_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in ASR worker: {e}")

        logger.info("ASR Worker stopped.")

    def stop(self):
        """Stop the worker thread."""
        self._is_running = False


class WhisperASRWorker(threading.Thread):
    """
    Worker thread that accumulates audio chunks and transcribes with
    faster-whisper (WhisperEngine).

    Design rationale
    ----------------
    Vosk's KaldiRecognizer is a streaming decoder that accepts 20-ms chunks
    one at a time.  Whisper is an encoder-decoder that performs best on
    complete utterances.  This worker therefore:

    1. Accumulates ``AudioChunk.data`` (float32 arrays) in a local buffer.
    2. Flushes on *silence*: when the input queue is empty after
       ``whisper_config.SILENCE_TIMEOUT`` seconds, the speaker has paused
       → treat the buffer as one utterance.
    3. Force-flushes at a 10-second cap to prevent unbounded growth.
    4. Emits a ``TranscriptEvent`` identical to ``ASRWorker`` output, so the
       rest of the pipeline (NLP, SiGML, API) needs no changes.
    """

    def __init__(self, input_queue: queue.Queue, output_queue: queue.Queue):
        super().__init__(name="WhisperASRWorker")
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.daemon = True
        self._is_running = False
        self._engine: Optional[object] = None  # WhisperEngine, imported lazily

    def run(self):
        """Main accumulate-then-flush loop."""
        logger.info("WhisperASR Worker starting...")

        # Lazy import keeps the Vosk path unaffected when faster-whisper is absent
        from src.asr.whisper_engine import WhisperEngine
        from config.settings import whisper_config, audio_config as _audio_cfg

        try:
            self._engine = WhisperEngine()
        except Exception as exc:
            logger.error("Failed to initialize WhisperEngine: %s", exc)
            return

        self._is_running = True
        buffer: list = []
        # 10 s cap: SAMPLE_RATE samples/s × 10 s
        max_buffer_samples: int = _audio_cfg.SAMPLE_RATE * 10

        while self._is_running:
            try:
                chunk: AudioChunk = self.input_queue.get(
                    timeout=whisper_config.SILENCE_TIMEOUT
                )
                buffer.append(chunk.data)  # float32 ndarray
                self.input_queue.task_done()

                # Force flush when 10 s of audio has accumulated
                if sum(len(c) for c in buffer) >= max_buffer_samples:
                    self._flush(buffer)
                    buffer = []

            except queue.Empty:
                # Silence gap reached → end of utterance
                if buffer:
                    self._flush(buffer)
                    buffer = []

            except Exception as exc:
                logger.error("Error in WhisperASR worker: %s", exc)

        logger.info("WhisperASR Worker stopped.")

    def _flush(self, buffer: list) -> None:
        """Concatenate buffered chunks and send them through WhisperEngine."""
        try:
            audio_np = np.concatenate(buffer)
            text, confidence = self._engine.transcribe(audio_np)

            if text:
                logger.info("Whisper Recognized: %s", text)
                event = TranscriptEvent(
                    text=text,
                    confidence=confidence,
                    is_final=True,
                )
                try:
                    self.output_queue.put(event, timeout=0.5)
                except queue.Full:
                    logger.warning(
                        "Transcript queue full, dropping WhisperASR event"
                    )
        except Exception as exc:
            logger.error("WhisperASRWorker._flush error: %s", exc)

    def stop(self):
        """Stop the worker thread."""
        self._is_running = False

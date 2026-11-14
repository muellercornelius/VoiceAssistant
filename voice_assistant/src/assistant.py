from __future__ import annotations

import logging
import queue
import signal
import time
from enum import Enum, auto
from typing import Protocol

import numpy as np

from src.config import AppConfig, ServiceCall

logger = logging.getLogger(__name__)


class WakeWordProtocol(Protocol):
    def detect(self, audio_chunk: np.ndarray) -> tuple[str, float] | None: ...
    def reset(self) -> None: ...


class KeywordProtocol(Protocol):
    def reset(self) -> None: ...
    def accept_chunk(self, audio_chunk: np.ndarray) -> str | None: ...
    def finalize(self) -> str: ...


class HomeAssistantProtocol(Protocol):
    def call_service(self, service_call: ServiceCall) -> bool: ...


class AssistantState(Enum):
    IDLE = auto()
    LISTENING_COMMAND = auto()


class VoiceAssistant:
    """Two-stage local voice assistant: openWakeWord -> Vosk keyword -> Home Assistant."""

    def __init__(
        self,
        config: AppConfig,
        wakeword: WakeWordProtocol,
        recognizer: KeywordProtocol,
        ha_client: HomeAssistantProtocol,
    ) -> None:
        self._config = config
        self._wakeword = wakeword
        self._recognizer = recognizer
        self._ha_client = ha_client
        self._state = AssistantState.IDLE
        self._listen_started_at = 0.0
        self._cooldown_until = 0.0
        self._running = False

    @property
    def state(self) -> AssistantState:
        return self._state

    def process_chunk(self, audio_chunk: np.ndarray, now: float | None = None) -> str | None:
        """Process a single 1D int16 audio chunk. Returns matched command phrase if executed."""
        current_time = time.monotonic() if now is None else now

        if self._state == AssistantState.IDLE:
            if current_time < self._cooldown_until:
                return None
            hit = self._wakeword.detect(audio_chunk)
            if hit is not None:
                name, score = hit
                logger.info("Wake-Word erkannt: '%s' (Score: %.2f) -> höre auf Keyword...", name, score)
                self._wakeword.reset()
                self._recognizer.reset()
                self._state = AssistantState.LISTENING_COMMAND
                self._listen_started_at = current_time
            return None

        # AssistantState.LISTENING_COMMAND
        text = self._recognizer.accept_chunk(audio_chunk)
        if text:
            return self._handle_recognized_text(text, current_time)

        if current_time - self._listen_started_at >= self._config.command.listen_timeout_seconds:
            final_text = self._recognizer.finalize()
            if final_text:
                return self._handle_recognized_text(final_text, current_time)
            logger.info("Kein Keyword innerhalb des Timeouts erkannt.")
            self._finish_listening(current_time)

        return None

    def _handle_recognized_text(self, text: str, current_time: float) -> str | None:
        normalized = " ".join(text.lower().split())
        service_call = self._config.commands.get(normalized)
        self._finish_listening(current_time)

        if service_call is not None:
            logger.info("Keyword erkannt: '%s' -> führe %s.%s aus", normalized, service_call.domain, service_call.service)
            self._ha_client.call_service(service_call)
            return normalized

        logger.info("Unbekannter Befehl ignoriert: '%s'", normalized)
        return None

    def _finish_listening(self, current_time: float) -> None:
        self._wakeword.reset()
        self._state = AssistantState.IDLE
        self._cooldown_until = current_time + self._config.wakeword.cooldown_seconds

    def run(self) -> None:
        import sounddevice as sd

        audio_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=50)
        self._running = True

        def _stop_handler(signum: int, _frame: object) -> None:
            logger.info("Signal %s empfangen, beende Voice Assistant...", signum)
            self._running = False

        signal.signal(signal.SIGINT, _stop_handler)
        signal.signal(signal.SIGTERM, _stop_handler)

        def audio_callback(indata: np.ndarray, _frames: int, _time_info: object, status: sd.CallbackFlags) -> None:
            if status:
                logger.warning("Audio-Stream Status: %s", status)
            chunk = indata[:, 0].copy()
            try:
                audio_queue.put_nowait(chunk)
            except queue.Full:
                pass

        logger.info(
            "Starte Audio-Stream (Rate: %d Hz, Chunk: %d Samples, Device: %s)",
            self._config.audio.sample_rate,
            self._config.audio.chunk_size,
            self._config.audio.input_device if self._config.audio.input_device is not None else "default",
        )

        with sd.InputStream(
            samplerate=self._config.audio.sample_rate,
            blocksize=self._config.audio.chunk_size,
            device=self._config.audio.input_device,
            channels=1,
            dtype="int16",
            callback=audio_callback,
        ):
            logger.info("Voice Assistant bereit. Warte auf Wake-Word...")
            while self._running:
                try:
                    chunk = audio_queue.get(timeout=0.2)
                except queue.Empty:
                    continue
                self.process_chunk(chunk)

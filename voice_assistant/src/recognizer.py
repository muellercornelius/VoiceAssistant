from __future__ import annotations

import json
import logging
from typing import Iterable

import numpy as np

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """Wrapper around openWakeWord using ONNX runtime."""

    def __init__(self, model_name_or_path: str, threshold: float = 0.5) -> None:
        from openwakeword.model import Model

        self._threshold = threshold
        self._model = Model(
            wakeword_models=[model_name_or_path],
            inference_framework="onnx",
        )
        logger.info("openWakeWord geladen: %s (Threshold: %.2f)", model_name_or_path, threshold)

    def detect(self, audio_chunk: np.ndarray) -> tuple[str, float] | None:
        scores = self._model.predict(audio_chunk)
        for name, score in scores.items():
            if score >= self._threshold:
                return name, float(score)
        return None

    def reset(self) -> None:
        self._model.reset()


class KeywordRecognizer:
    """Fast offline German keyword recognizer using Vosk with a constrained grammar."""

    def __init__(self, model_path: str, sample_rate: int, keywords: Iterable[str]) -> None:
        from vosk import KaldiRecognizer, Model, SetLogLevel

        SetLogLevel(-1)
        self._sample_rate = sample_rate
        self._model = Model(model_path)
        keyword_list = sorted({kw.strip().lower() for kw in keywords if kw.strip()})
        # Constrained grammar restricts Vosk to only the configured commands + [unk]
        # for maximum speed and accuracy.
        self._grammar = json.dumps(keyword_list + ["[unk]"], ensure_ascii=False)
        self._recognizer = KaldiRecognizer(self._model, self._sample_rate, self._grammar)
        logger.info("Vosk Keyword-Modell geladen (%d Keywords): %s", len(keyword_list), keyword_list)

    def reset(self) -> None:
        from vosk import KaldiRecognizer

        self._recognizer = KaldiRecognizer(self._model, self._sample_rate, self._grammar)

    def accept_chunk(self, audio_chunk: np.ndarray) -> str | None:
        """Feed int16 PCM chunk. Returns finalized text if utterance ended, else None."""
        pcm_bytes = audio_chunk.tobytes()
        if self._recognizer.AcceptWaveform(pcm_bytes):
            result = json.loads(self._recognizer.Result())
            return self._clean_text(result.get("text", ""))
        return None

    def finalize(self) -> str:
        """Force final result when listen timeout is reached."""
        result = json.loads(self._recognizer.FinalResult())
        return self._clean_text(result.get("text", ""))

    @staticmethod
    def _clean_text(text: str) -> str:
        cleaned = " ".join(text.lower().split())
        if cleaned == "[unk]":
            return ""
        return cleaned.replace("[unk]", "").strip()

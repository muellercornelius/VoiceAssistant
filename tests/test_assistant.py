import numpy as np

from src.assistant import AssistantState, VoiceAssistant
from src.config import (
    AppConfig,
    AudioConfig,
    CommandConfig,
    HomeAssistantConfig,
    ServiceCall,
    WakeWordConfig,
)


class FakeWakeWord:
    def __init__(self) -> None:
        self.next_hit: tuple[str, float] | None = None
        self.resets = 0

    def detect(self, _audio_chunk: np.ndarray) -> tuple[str, float] | None:
        return self.next_hit

    def reset(self) -> None:
        self.resets += 1


class FakeRecognizer:
    def __init__(self) -> None:
        self.next_text: str | None = None
        self.final_text: str = ""
        self.resets = 0

    def reset(self) -> None:
        self.resets += 1

    def accept_chunk(self, _audio_chunk: np.ndarray) -> str | None:
        return self.next_text

    def finalize(self) -> str:
        return self.final_text


class FakeHAClient:
    def __init__(self) -> None:
        self.calls: list[ServiceCall] = []

    def call_service(self, service_call: ServiceCall) -> bool:
        self.calls.append(service_call)
        return True


def _make_config() -> AppConfig:
    return AppConfig(
        wakeword=WakeWordConfig(model="hey_jarvis", threshold=0.5, cooldown_seconds=1.0),
        command=CommandConfig(vosk_model_path="/unused", listen_timeout_seconds=3.0),
        audio=AudioConfig(sample_rate=16000, chunk_size=1280),
        home_assistant=HomeAssistantConfig(url="http://ha.local:8123", token="tok"),
        commands={
            "alles aus": ServiceCall(domain="homeassistant", service="turn_off", data={"entity_id": "all"})
        },
    )


def test_wakeword_then_keyword_triggers_home_assistant() -> None:
    ww = FakeWakeWord()
    rec = FakeRecognizer()
    ha = FakeHAClient()
    assistant = VoiceAssistant(_make_config(), ww, rec, ha)
    chunk = np.zeros(1280, dtype=np.int16)

    assert assistant.state == AssistantState.IDLE

    # Wakeword detected at t=10.0
    ww.next_hit = ("hey_jarvis", 0.91)
    assert assistant.process_chunk(chunk, now=10.0) is None
    assert assistant.state == AssistantState.LISTENING_COMMAND
    assert rec.resets == 1

    # Keyword recognized at t=10.5
    ww.next_hit = None
    rec.next_text = "alles aus"
    matched = assistant.process_chunk(chunk, now=10.5)
    assert matched == "alles aus"
    assert assistant.state == AssistantState.IDLE
    assert len(ha.calls) == 1
    assert ha.calls[0].service == "turn_off"


def test_listen_timeout_uses_final_result_and_returns_idle() -> None:
    ww = FakeWakeWord()
    rec = FakeRecognizer()
    ha = FakeHAClient()
    assistant = VoiceAssistant(_make_config(), ww, rec, ha)
    chunk = np.zeros(1280, dtype=np.int16)

    ww.next_hit = ("hey_jarvis", 0.8)
    assistant.process_chunk(chunk, now=1.0)
    ww.next_hit = None

    # Before timeout: nothing
    assert assistant.process_chunk(chunk, now=2.0) is None
    assert assistant.state == AssistantState.LISTENING_COMMAND

    # At timeout (1.0 + 3.0 = 4.0): finalize returns command
    rec.final_text = "alles aus"
    matched = assistant.process_chunk(chunk, now=4.0)
    assert matched == "alles aus"
    assert assistant.state == AssistantState.IDLE
    assert len(ha.calls) == 1


def test_cooldown_prevents_immediate_retrigger() -> None:
    ww = FakeWakeWord()
    rec = FakeRecognizer()
    ha = FakeHAClient()
    assistant = VoiceAssistant(_make_config(), ww, rec, ha)
    chunk = np.zeros(1280, dtype=np.int16)

    ww.next_hit = ("hey_jarvis", 0.8)
    assistant.process_chunk(chunk, now=10.0)
    rec.next_text = "alles aus"
    assistant.process_chunk(chunk, now=10.2)
    assert assistant.state == AssistantState.IDLE

    # During cooldown (10.2 + 1.0 = 11.2): should ignore wakeword
    rec.next_text = None
    ww.next_hit = ("hey_jarvis", 0.95)
    assistant.process_chunk(chunk, now=10.8)
    assert assistant.state == AssistantState.IDLE

    # After cooldown: should trigger again
    assistant.process_chunk(chunk, now=11.3)
    assert assistant.state == AssistantState.LISTENING_COMMAND

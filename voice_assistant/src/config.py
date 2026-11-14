from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class WakeWordConfig:
    model: str = "hey_jarvis"
    threshold: float = 0.5
    cooldown_seconds: float = 1.5


@dataclass(frozen=True)
class CommandConfig:
    vosk_model_path: str = "/app/models/vosk-model-small-de-0.15"
    listen_timeout_seconds: float = 3.5


@dataclass(frozen=True)
class AudioConfig:
    sample_rate: int = 16000
    chunk_size: int = 1280
    input_device: int | str | None = None


@dataclass(frozen=True)
class HomeAssistantConfig:
    url: str = "http://supervisor/core"
    token: str = ""
    timeout_seconds: float = 5.0


@dataclass(frozen=True)
class ServiceCall:
    domain: str
    service: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AppConfig:
    wakeword: WakeWordConfig
    command: CommandConfig
    audio: AudioConfig
    home_assistant: HomeAssistantConfig
    commands: dict[str, ServiceCall]


def _parse_input_device(raw: Any) -> int | str | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, int):
        return raw
    s = str(raw).strip()
    if s.isdigit():
        return int(s)
    return s


def _load_ha_options() -> dict[str, Any]:
    options_path = Path(os.environ.get("HA_OPTIONS_FILE", "/data/options.json"))
    if not options_path.exists():
        return {}
    with options_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def load_config(path: str | Path = "/config/voice_assistant.yaml") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    ha_options = _load_ha_options()
    commands_raw = raw.get("commands", {})

    wakeword = WakeWordConfig(
        model=str(ha_options.get("wakeword_model") or "hey_jarvis"),
        threshold=float(ha_options.get("threshold", 0.5)),
        cooldown_seconds=float(ha_options.get("cooldown_seconds", 1.5)),
    )

    command = CommandConfig(
        listen_timeout_seconds=float(ha_options.get("listen_timeout_seconds", 3.5)),
    )

    audio = AudioConfig(
        input_device=_parse_input_device(ha_options.get("input_device")),
    )

    home_assistant = HomeAssistantConfig(
        url="http://supervisor/core",
        token=os.environ.get("SUPERVISOR_TOKEN", ""),
    )

    commands: dict[str, ServiceCall] = {}
    for phrase, spec in commands_raw.items():
        normalized = " ".join(str(phrase).lower().split())
        if not normalized:
            continue
        if not isinstance(spec, dict) or "domain" not in spec or "service" not in spec:
            raise ValueError(f"Ungültiger Command-Eintrag für '{phrase}': domain und service erforderlich")
        commands[normalized] = ServiceCall(
            domain=str(spec["domain"]),
            service=str(spec["service"]),
            data=dict(spec.get("data") or {}),
        )

    if not commands:
        raise ValueError("Mindestens ein Command muss in config.yaml unter 'commands' definiert sein.")

    return AppConfig(
        wakeword=wakeword,
        command=command,
        audio=audio,
        home_assistant=home_assistant,
        commands=commands,
    )

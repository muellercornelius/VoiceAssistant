from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


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


def _load_ha_options(options_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(options_path) if options_path is not None else Path(os.environ.get("HA_OPTIONS_FILE", "/data/options.json"))
    if not path.exists():
        raise FileNotFoundError(f"Add-on-Optionsdatei nicht gefunden: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Ungültiges Format in {path}: JSON-Objekt erwartet")
    return data


def _parse_command_data(raw_data: Any, phrase: str) -> dict[str, Any]:
    if raw_data is None or raw_data == "":
        return {}
    if isinstance(raw_data, dict):
        return dict(raw_data)
    if isinstance(raw_data, str):
        try:
            parsed = json.loads(raw_data)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Ungültiges JSON in 'data' für '{phrase}': {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValueError(f"'data' für '{phrase}' muss ein JSON-Objekt sein")
        return parsed
    raise ValueError(f"Ungültiges 'data'-Format für '{phrase}'")


def load_config(options_path: str | Path | None = None) -> AppConfig:
    ha_options = _load_ha_options(options_path)

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

    commands_raw = ha_options.get("commands") or []
    if not isinstance(commands_raw, list):
        raise ValueError("'commands' in den Add-on-Optionen muss eine Liste sein.")

    commands: dict[str, ServiceCall] = {}
    for entry in commands_raw:
        if not isinstance(entry, dict):
            raise ValueError("Jeder Eintrag in 'commands' muss ein Objekt sein.")
        normalized = " ".join(str(entry.get("phrase", "")).lower().split())
        if not normalized:
            continue
        domain = str(entry.get("domain", "")).strip()
        service = str(entry.get("service", "")).strip()
        if not domain or not service:
            raise ValueError(f"Ungültiger Command-Eintrag für '{normalized}': domain und service erforderlich")

        data = _parse_command_data(entry.get("data"), normalized)
        entity_id = str(entry.get("entity_id") or "").strip()
        if entity_id and "entity_id" not in data:
            data["entity_id"] = entity_id

        commands[normalized] = ServiceCall(
            domain=domain,
            service=service,
            data=data,
        )

    if not commands:
        raise ValueError("Mindestens ein Command muss in den Add-on-Optionen unter 'commands' definiert sein.")

    return AppConfig(
        wakeword=wakeword,
        command=command,
        audio=audio,
        home_assistant=home_assistant,
        commands=commands,
    )

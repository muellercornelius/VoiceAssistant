import json
from pathlib import Path
import pytest

from src.config import load_config


def test_load_config_reads_ha_options_and_normalizes_commands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPERVISOR_TOKEN", "sup_tok_123")
    options_file = tmp_path / "options.json"
    options_file.write_text(
        json.dumps(
            {
                "wakeword_model": "alexa",
                "threshold": 0.7,
                "cooldown_seconds": 2.0,
                "listen_timeout_seconds": 4.5,
                "input_device": "1",
                "commands": [
                    {
                        "phrase": "  Alles   Aus ",
                        "domain": "homeassistant",
                        "service": "turn_off",
                        "entity_id": "all",
                    },
                    {
                        "phrase": "lampe dimmen",
                        "domain": "light",
                        "service": "turn_on",
                        "entity_id": "light.schrankbett",
                        "data": '{"brightness": 120}',
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    cfg = load_config(options_file)
    assert cfg.wakeword.model == "alexa"
    assert cfg.wakeword.threshold == 0.7
    assert cfg.wakeword.cooldown_seconds == 2.0
    assert cfg.command.listen_timeout_seconds == 4.5
    assert cfg.audio.input_device == 1
    assert cfg.home_assistant.url == "http://supervisor/core"
    assert cfg.home_assistant.token == "sup_tok_123"
    assert "alles aus" in cfg.commands
    assert cfg.commands["alles aus"].domain == "homeassistant"
    assert cfg.commands["alles aus"].service == "turn_off"
    assert cfg.commands["alles aus"].data == {"entity_id": "all"}
    assert cfg.commands["lampe dimmen"].data == {"entity_id": "light.schrankbett", "brightness": 120}


def test_load_config_requires_commands(tmp_path: Path) -> None:
    options_file = tmp_path / "options.json"
    options_file.write_text('{"commands": []}', encoding="utf-8")
    with pytest.raises(ValueError, match="Mindestens ein Command"):
        load_config(options_file)


def test_load_config_rejects_invalid_data_json(tmp_path: Path) -> None:
    options_file = tmp_path / "options.json"
    options_file.write_text(
        json.dumps(
            {
                "commands": [
                    {
                        "phrase": "licht an",
                        "domain": "light",
                        "service": "turn_on",
                        "data": "{invalid json",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Ungültiges JSON"):
        load_config(options_file)

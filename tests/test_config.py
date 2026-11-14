from pathlib import Path
import pytest

from src.config import load_config


def test_load_config_reads_yaml_and_normalizes_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    monkeypatch.setenv("HA_OPTIONS_FILE", str(tmp_path / "missing_options.json"))

    cfg_file = tmp_path / "voice_assistant.yaml"
    cfg_file.write_text(
        """
commands:
  "  Alles   Aus ":
    domain: "homeassistant"
    service: "turn_off"
    data:
      entity_id: "all"
""",
        encoding="utf-8",
    )

    cfg = load_config(cfg_file)
    assert cfg.wakeword.model == "hey_jarvis"
    assert cfg.wakeword.threshold == 0.5
    assert cfg.home_assistant.url == "http://supervisor/core"
    assert cfg.home_assistant.token == ""
    assert "alles aus" in cfg.commands
    assert cfg.commands["alles aus"].domain == "homeassistant"
    assert cfg.commands["alles aus"].service == "turn_off"
    assert cfg.commands["alles aus"].data == {"entity_id": "all"}


def test_load_config_requires_commands(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("commands: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Mindestens ein Command"):
        load_config(cfg_file)


def test_supervisor_token_and_ha_options(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:

    cfg_file = tmp_path / "assistant_config.yaml"
    cfg_file.write_text(
        """
commands:
  "alles aus":
    domain: "homeassistant"
    service: "turn_off"
""",
        encoding="utf-8",
    )

    options_file = tmp_path / "options.json"
    options_file.write_text(
        '{"wakeword_model": "alexa", "threshold": 0.7, "listen_timeout_seconds": 4.5, "input_device": "1"}',
        encoding="utf-8",
    )

    monkeypatch.setenv("SUPERVISOR_TOKEN", "sup_tok_123")
    monkeypatch.setenv("HA_OPTIONS_FILE", str(options_file))

    cfg = load_config(cfg_file)
    assert cfg.home_assistant.url == "http://supervisor/core"
    assert cfg.home_assistant.token == "sup_tok_123"
    assert cfg.wakeword.model == "alexa"
    assert cfg.wakeword.threshold == 0.7
    assert cfg.command.listen_timeout_seconds == 4.5
    assert cfg.audio.input_device == 1

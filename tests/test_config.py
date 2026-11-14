from pathlib import Path
import pytest

from src.config import load_config


def test_load_config_reads_yaml_and_normalizes_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    monkeypatch.delenv("HA_URL", raising=False)
    monkeypatch.delenv("HA_TOKEN", raising=False)
    monkeypatch.delenv("WAKEWORD_MODEL", raising=False)
    monkeypatch.delenv("INPUT_DEVICE", raising=False)

    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        """
wakeword:
  model: "hey_jarvis"
  threshold: 0.6
  cooldown_seconds: 2.0
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
    assert cfg.wakeword.threshold == 0.6
    assert cfg.home_assistant.url == "http://supervisor/core"
    assert cfg.home_assistant.token == ""
    assert "alles aus" in cfg.commands
    assert cfg.commands["alles aus"].domain == "homeassistant"
    assert cfg.commands["alles aus"].service == "turn_off"
    assert cfg.commands["alles aus"].data == {"entity_id": "all"}


def test_env_overrides(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        """
commands:
  "alles aus":
    domain: "homeassistant"
    service: "turn_off"
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("HA_URL", "http://192.168.1.10:8123/")
    monkeypatch.setenv("HA_TOKEN", "secret_token")
    monkeypatch.setenv("WAKEWORD_MODEL", "/config/models/assistant.onnx")
    monkeypatch.setenv("INPUT_DEVICE", "2")

    cfg = load_config(cfg_file)
    assert cfg.home_assistant.url == "http://192.168.1.10:8123"
    assert cfg.home_assistant.token == "secret_token"
    assert cfg.wakeword.model == "/config/models/assistant.onnx"
    assert cfg.audio.input_device == 2


def test_load_config_requires_commands(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("commands: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Mindestens ein Command"):
        load_config(cfg_file)


def test_supervisor_token_and_ha_options(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HA_URL", raising=False)
    monkeypatch.delenv("HA_TOKEN", raising=False)
    monkeypatch.delenv("WAKEWORD_MODEL", raising=False)
    monkeypatch.delenv("INPUT_DEVICE", raising=False)

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

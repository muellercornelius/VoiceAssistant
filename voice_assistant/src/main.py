from __future__ import annotations

import argparse
import logging
import sys

from src.assistant import VoiceAssistant
from src.config import load_config
from src.home_assistant import HomeAssistantClient
from src.recognizer import KeywordRecognizer, WakeWordDetector


def _list_audio_devices() -> None:
    import sounddevice as sd

    print(sd.query_devices())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lokaler Keyword Voice Assistant (openWakeWord + Vosk + Home Assistant)")
    parser.add_argument("--list-devices", action="store_true", help="Verfügbare Audio-Geräte anzeigen und beenden")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.list_devices:
        _list_audio_devices()
        return 0

    config = load_config()
    ha_client = HomeAssistantClient(config.home_assistant)
    ha_client.check_connection()

    wakeword = WakeWordDetector(
        model_name_or_path=config.wakeword.model,
        threshold=config.wakeword.threshold,
    )
    recognizer = KeywordRecognizer(
        model_path=config.command.vosk_model_path,
        sample_rate=config.audio.sample_rate,
        keywords=config.commands.keys(),
    )

    assistant = VoiceAssistant(
        config=config,
        wakeword=wakeword,
        recognizer=recognizer,
        ha_client=ha_client,
    )
    assistant.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())

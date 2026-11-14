#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="${ASSISTANT_CONFIG_PATH:-/app/assistant_config.yaml}"

# Im Home Assistant OS Add-on-Betrieb existiert /data/options.json
if [ -f /data/options.json ]; then
    CUSTOM_PATH=$(python -c "import json; print(json.load(open('/data/options.json')).get('commands_file', '/config/voice_assistant.yaml'))")
    if [ -n "$CUSTOM_PATH" ]; then
        CONFIG_PATH="$CUSTOM_PATH"
    fi

    # Starter-Konfiguration nach /config/voice_assistant.yaml kopieren, falls noch nicht vorhanden
    if [ ! -f "$CONFIG_PATH" ] && [ -d "$(dirname "$CONFIG_PATH")" ]; then
        cp /app/assistant_config.yaml "$CONFIG_PATH"
        echo "Starter-Konfiguration erstellt unter: $CONFIG_PATH"
    fi
fi

# ALSA -> PulseAudio Routing aktivieren, wenn HA Supervisor PULSE_SERVER bereitstellt
if [ -n "${PULSE_SERVER:-}" ] && [ ! -f /etc/asound.conf ]; then
    printf 'pcm.!default {\n    type pulse\n}\nctl.!default {\n    type pulse\n}\n' > /etc/asound.conf
fi

exec python -m src.main --config "$CONFIG_PATH"

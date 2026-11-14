#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="/config/voice_assistant.yaml"

if [ -f /data/options.json ]; then
    CUSTOM_PATH=$(python -c "import json; print(json.load(open('/data/options.json')).get('commands_file') or '')")
    if [ -n "$CUSTOM_PATH" ]; then
        CONFIG_PATH="$CUSTOM_PATH"
    fi
fi

# Starter-Konfiguration anlegen, falls noch nicht vorhanden
if [ ! -f "$CONFIG_PATH" ] && [ -d "$(dirname "$CONFIG_PATH")" ]; then
    cp /app/assistant_config.yaml "$CONFIG_PATH"
    echo "Starter-Konfiguration erstellt unter: $CONFIG_PATH"
fi

# ALSA -> PulseAudio Routing aktivieren, wenn HA Supervisor PULSE_SERVER bereitstellt
if [ -n "${PULSE_SERVER:-}" ] && [ ! -f /etc/asound.conf ]; then
    printf 'pcm.!default {\n    type pulse\n}\nctl.!default {\n    type pulse\n}\n' > /etc/asound.conf
fi

exec python -m src.main --config "$CONFIG_PATH"

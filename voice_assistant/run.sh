#!/usr/bin/env bash
set -euo pipefail

# ALSA -> PulseAudio Routing aktivieren, wenn HA Supervisor PULSE_SERVER bereitstellt
if [ -n "${PULSE_SERVER:-}" ] && [ ! -f /etc/asound.conf ]; then
    printf 'pcm.!default {\n    type pulse\n}\nctl.!default {\n    type pulse\n}\n' > /etc/asound.conf
fi

exec python -m src.main

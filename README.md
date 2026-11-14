# Lokaler Keyword Voice Assistant (Home Assistant OS Add-on)

Schneller, komplett lokaler Sprachassistent auf Basis von **openWakeWord** (Wake-Word), **Vosk** (deutsches Keyword-Modell mit fester Grammatik) und der **Home Assistant REST API**.

Beispiel: *"Hey Jarvis ... alles aus"* (oder mit eigenem `assistant.onnx`-Modell: *"Assistant ... alles aus"*).

## Installation als Home Assistant OS Add-on (über GitHub)

1. Das Repository zu GitHub pushen (`https://github.com/muellercornelius/VoiceAssistant`).
2. In Home Assistant OS:
   - **Einstellungen → Add-ons → Add-on-Store** öffnen.
   - Oben rechts auf das **Drei-Punkte-Menü → Repositories** klicken.
   - `https://github.com/muellercornelius/VoiceAssistant` hinzufügen.
   - Das Add-on **Keyword Voice Assistant** installieren und starten.
3. Alle Einstellungen (Wake-Word, Threshold, Timeout, Eingabegerät sowie deine Sprachbefehle unter `commands`) werden direkt in der **Add-on-Konfiguration (UI)** gepflegt.
   - Authentifizierung (`SUPERVISOR_TOKEN`) und Audio (`audio: true`) werden vom HAOS Supervisor automatisch bereitgestellt.

## Eigenes Wake-Word „assistant“

`openWakeWord` bringt fertige Modelle wie `hey_jarvis`, `alexa` oder `hey_mycroft` mit. Für das eigene Wake-Word **„assistant“**:
1. Mit dem offiziellen [openWakeWord Training-Notebook](https://github.com/dscripka/openWakeWord#training-new-models) eine `assistant.onnx` erzeugen.
2. Datei unter `/config/models/assistant.onnx` in Home Assistant ablegen.
3. In der Add-on-Konfiguration `wakeword_model: "/config/models/assistant.onnx"` eintragen.

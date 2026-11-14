# Lokaler Keyword Voice Assistant (Home Assistant OS Add-on)

Schneller, komplett lokaler Sprachassistent auf Basis von **openWakeWord** (Wake-Word), **Vosk** (deutsches Keyword-Modell mit fester Grammatik) und der **Home Assistant REST API**.

Beispiel: *"Hey Jarvis ... alles aus"* (oder mit eigenem `assistant.onnx`-Modell: *"Assistant ... alles aus"*).

## Installation als Home Assistant OS Add-on (über GitHub)

1. In [repository.yaml](./repository.yaml) und [voice_assistant/config.yaml](./voice_assistant/config.yaml) die Platzhalter `https://github.com/DEIN-USER/DEIN-REPO` durch deine echte GitHub-Repository-URL ersetzen.
2. Das Repository zu GitHub pushen.
3. In Home Assistant OS:
   - **Einstellungen → Add-ons → Add-on-Store** öffnen.
   - Oben rechts auf das **Drei-Punkte-Menü → Repositories** klicken.
   - Deine GitHub-Repository-URL hinzufügen.
   - Das Add-on **Keyword Voice Assistant** installieren und starten.
4. Beim ersten Start legt das Add-on automatisch eine bearbeitbare Konfigurationsdatei unter `/config/voice_assistant.yaml` in Home Assistant an. Dort kannst du deine Keywords und Service-Aufrufe anpassen (danach Add-on neu starten).
   - Wake-Word, Threshold, Timeout und Eingabegerät lassen sich direkt in der **Add-on-Konfiguration (UI)** einstellen.
   - Authentifizierung (`SUPERVISOR_TOKEN`) und Audio (`audio: true`) werden vom HAOS Supervisor automatisch bereitgestellt.

## Eigenes Wake-Word „assistant“

`openWakeWord` bringt fertige Modelle wie `hey_jarvis`, `alexa` oder `hey_mycroft` mit. Für das eigene Wake-Word **„assistant“**:
1. Mit dem offiziellen [openWakeWord Training-Notebook](https://github.com/dscripka/openWakeWord#training-new-models) eine `assistant.onnx` erzeugen.
2. Datei unter `/config/models/assistant.onnx` in Home Assistant ablegen.
3. In der Add-on-Konfiguration `wakeword_model: "/config/models/assistant.onnx"` eintragen.

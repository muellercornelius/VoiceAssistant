FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libportaudio2 \
    libsndfile1 \
    libasound2-plugins \
    pulseaudio-utils \
    alsa-utils \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Deutsches Vosk-Kleinmodell (~45 MB) vorab herunterladen
RUN mkdir -p /app/models \
    && curl -fsSL https://alphacephei.com/vosk/models/vosk-model-small-de-0.15.zip -o /tmp/vosk-de.zip \
    && unzip -q /tmp/vosk-de.zip -d /app/models \
    && rm /tmp/vosk-de.zip

# openWakeWord Basis- & Standardmodelle vorab herunterladen (ONNX)
RUN python -c "import openwakeword.utils; openwakeword.utils.download_models()"

COPY assistant_config.yaml .
COPY src/ ./src/
COPY run.sh .
RUN chmod +x /app/run.sh

CMD ["/app/run.sh"]

from __future__ import annotations

import logging
import requests

from src.config import HomeAssistantConfig, ServiceCall

logger = logging.getLogger(__name__)


class HomeAssistantClient:
    """Fast HTTP client using a persistent session for Home Assistant REST API calls."""

    def __init__(self, config: HomeAssistantConfig, session: requests.Session | None = None) -> None:
        self._config = config
        self._session = session or requests.Session()
        headers = {"Content-Type": "application/json"}
        if config.token:
            headers["Authorization"] = f"Bearer {config.token}"
        self._session.headers.update(headers)

    def check_connection(self) -> bool:
        if not self._config.token:
            logger.warning("Kein SUPERVISOR_TOKEN gesetzt – ist 'homeassistant_api: true' in config.yaml aktiv?")
        url = f"{self._config.url}/api/"
        try:
            resp = self._session.get(url, timeout=self._config.timeout_seconds)
            if resp.ok:
                logger.info("Home Assistant erreichbar (%s)", self._config.url)
                return True
            logger.warning("Home Assistant antwortete mit Status %s auf %s", resp.status_code, url)
            return False
        except requests.RequestException as exc:
            logger.warning("Home Assistant aktuell nicht erreichbar (%s): %s", url, exc)
            return False

    def call_service(self, service_call: ServiceCall) -> bool:
        url = f"{self._config.url}/api/services/{service_call.domain}/{service_call.service}"
        try:
            resp = self._session.post(
                url,
                json=service_call.data,
                timeout=self._config.timeout_seconds,
            )
            if resp.ok:
                logger.info(
                    "Home Assistant Service ausgeführt: %s.%s (%s)",
                    service_call.domain,
                    service_call.service,
                    service_call.data,
                )
                return True
            logger.error(
                "Home Assistant Fehler (%s) bei %s: %s",
                resp.status_code,
                url,
                resp.text[:200],
            )
            return False
        except requests.RequestException as exc:
            logger.error("Verbindungsfehler zu Home Assistant (%s): %s", url, exc)
            return False

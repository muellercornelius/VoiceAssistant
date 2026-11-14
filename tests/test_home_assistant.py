from unittest.mock import MagicMock
import requests

from src.config import HomeAssistantConfig, ServiceCall
from src.home_assistant import HomeAssistantClient


def test_call_service_posts_expected_url_and_payload() -> None:
    mock_session = MagicMock(spec=requests.Session)
    mock_session.headers = {}
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_session.post.return_value = mock_resp

    client = HomeAssistantClient(
        HomeAssistantConfig(url="http://ha.local:8123", token="my-token", timeout_seconds=3.0),
        session=mock_session,
    )
    ok = client.call_service(ServiceCall(domain="homeassistant", service="turn_off", data={"entity_id": "all"}))

    assert ok is True
    assert mock_session.headers["Authorization"] == "Bearer my-token"
    mock_session.post.assert_called_once_with(
        "http://ha.local:8123/api/services/homeassistant/turn_off",
        json={"entity_id": "all"},
        timeout=3.0,
    )


def test_call_service_handles_http_error() -> None:
    mock_session = MagicMock(spec=requests.Session)
    mock_session.headers = {}
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 401
    mock_resp.text = "Unauthorized"
    mock_session.post.return_value = mock_resp

    client = HomeAssistantClient(
        HomeAssistantConfig(url="http://ha.local:8123", token="bad"),
        session=mock_session,
    )
    assert client.call_service(ServiceCall(domain="light", service="turn_on")) is False


def test_call_service_handles_network_exception() -> None:
    mock_session = MagicMock(spec=requests.Session)
    mock_session.headers = {}
    mock_session.post.side_effect = requests.ConnectionError("refused")

    client = HomeAssistantClient(
        HomeAssistantConfig(url="http://ha.local:8123", token="t"),
        session=mock_session,
    )
    assert client.call_service(ServiceCall(domain="light", service="turn_on")) is False

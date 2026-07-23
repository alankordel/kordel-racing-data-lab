"""Cliente HTTP isolado para a API OpenF1."""

import logging
import time
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)


class OpenF1Error(RuntimeError):
    """Erro compreensível de comunicação com a OpenF1."""


class OpenF1Client:
    ALLOWED_ENDPOINTS = {
        "meetings",
        "sessions",
        "drivers",
        "laps",
        "stints",
        "pit",
        "position",
        "intervals",
        "race_control",
        "weather",
        "session_result",
    }

    def __init__(
        self,
        base_url: str = "https://api.openf1.org/v1",
        timeout: float = 30,
        session: requests.Session | None = None,
        minimum_interval: float = 0.34,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.minimum_interval = minimum_interval
        self._last_request = 0.0

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> list[dict]:
        if endpoint not in self.ALLOWED_ENDPOINTS:
            raise ValueError(f"Endpoint não permitido: {endpoint}")
        wait = self.minimum_interval - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        LOGGER.info("Endpoint consultado: %s", endpoint)
        try:
            response = self.session.get(f"{self.base_url}/{endpoint}", params=params, timeout=self.timeout)
            self._last_request = time.monotonic()
            response.raise_for_status()
            payload = response.json()
        except requests.Timeout as exc:
            raise OpenF1Error(f"Tempo limite excedido em {endpoint}") from exc
        except requests.RequestException as exc:
            raise OpenF1Error(f"Falha HTTP em {endpoint}: {exc}") from exc
        except ValueError as exc:
            raise OpenF1Error(f"Resposta JSON inválida em {endpoint}") from exc
        if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
            raise OpenF1Error(f"Schema inesperado em {endpoint}: esperada uma lista de objetos")
        LOGGER.info("Registros recebidos: %s", len(payload))
        return payload

    def for_session(self, endpoint: str, session_key: int) -> list[dict]:
        return self.get(endpoint, {"session_key": session_key})

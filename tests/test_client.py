from unittest.mock import Mock

import pytest
import requests

from kordel_racing.api.client import OpenF1Client, OpenF1Error


def test_client_returns_json_list():
    response = Mock()
    response.json.return_value = [{"session_key": 1}]
    response.raise_for_status.return_value = None
    session = Mock()
    session.get.return_value = response
    client = OpenF1Client(session=session, minimum_interval=0)

    assert client.get("sessions", {"year": 2025}) == [{"session_key": 1}]
    session.get.assert_called_once()


def test_client_converts_http_error():
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("500")
    session = Mock()
    session.get.return_value = response

    with pytest.raises(OpenF1Error, match="Falha HTTP"):
        OpenF1Client(session=session, minimum_interval=0).get("laps")


def test_client_rejects_unexpected_schema():
    response = Mock()
    response.json.return_value = {"error": "schema"}
    response.raise_for_status.return_value = None
    session = Mock()
    session.get.return_value = response

    with pytest.raises(OpenF1Error, match="Schema inesperado"):
        OpenF1Client(session=session, minimum_interval=0).get("drivers")

import pytest
from fastapi import HTTPException

from api import require_api_key


def test_missing_api_key(monkeypatch):
    monkeypatch.setenv("CLOUDPULSE_API_KEY", "test-secret")

    with pytest.raises(HTTPException) as error:
        require_api_key(None)

    assert error.value.status_code == 401


def test_invalid_api_key(monkeypatch):
    monkeypatch.setenv("CLOUDPULSE_API_KEY", "test-secret")

    with pytest.raises(HTTPException) as error:
        require_api_key("wrong-key")

    assert error.value.status_code == 401


def test_valid_api_key(monkeypatch):
    monkeypatch.setenv("CLOUDPULSE_API_KEY", "test-secret")

    assert require_api_key("test-secret") is True


def test_missing_server_api_key(monkeypatch):
    monkeypatch.delenv("CLOUDPULSE_API_KEY", raising=False)

    with pytest.raises(HTTPException) as error:
        require_api_key("any-key")

    assert error.value.status_code == 503
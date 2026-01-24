"""Tests for Kyro REST client and supporting modules."""

from __future__ import annotations

import pytest

from kyro import KyroConfig, RestClient
from kyro._serialization import dumps, loads, loads_model
from kyro.exceptions import KyroError, KyroHTTPError, KyroValidationError
from pydantic import BaseModel


class _Payload(BaseModel):
    ticker: str
    count: int = 0


def test_config_defaults() -> None:
    cfg = KyroConfig()
    assert str(cfg.base_url) == "https://trading-api.kalshi.com/v2"
    assert cfg.request_timeout == 30.0
    assert cfg.default_headers.get("Accept") == "application/json"
    assert cfg.auth_headers is None


def test_config_custom_headers() -> None:
    cfg = KyroConfig(default_headers={"Accept": "application/xml", "X-Foo": "bar"})
    assert cfg.default_headers["Accept"] == "application/xml"
    assert cfg.default_headers["X-Foo"] == "bar"


def test_dumps_dict() -> None:
    assert dumps({"a": 1}) == b'{"a":1}'


def test_dumps_model() -> None:
    assert dumps(_Payload(ticker="KXBTC", count=2)) == b'{"ticker":"KXBTC","count":2}'


def test_loads() -> None:
    assert loads(b'{"a":1}') == {"a": 1}
    assert loads('{"a":1}') == {"a": 1}


def test_loads_invalid_raises() -> None:
    with pytest.raises(KyroValidationError) as exc_info:
        loads(b"not json")
    assert "Invalid JSON" in str(exc_info.value)


def test_loads_model() -> None:
    m = loads_model(b'{"ticker":"KXBTC","count":1}', _Payload)
    assert m.ticker == "KXBTC"
    assert m.count == 1


def test_loads_model_invalid_raises() -> None:
    with pytest.raises(KyroValidationError) as exc_info:
        loads_model(b'{"ticker":123}', _Payload)
    assert "Validation failed" in str(exc_info.value)
    assert exc_info.value.details is not None


def test_http_error_attrs() -> None:
    err = KyroHTTPError("bad", status=400, response_body={"error": "BadRequest"}, error_code="BadRequest")
    assert err.status == 400
    assert err.response_body == {"error": "BadRequest"}
    assert err.error_code == "BadRequest"


@pytest.mark.asyncio
async def test_rest_client_requires_context() -> None:
    """Using RestClient outside async context manager raises."""
    client = RestClient(KyroConfig())
    with pytest.raises(KyroError) as exc_info:
        await client.get("/markets")
    assert "context" in str(exc_info.value).lower()

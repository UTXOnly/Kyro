"""Tests for RestClient and HTTP behavior."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from kyro import KyroConfig, RestClient
from kyro.exceptions import (
    KyroError,
    KyroHTTPError,
    KyroTimeoutError,
    KyroValidationError,
)


class _EchoModel(BaseModel):
    echo: dict


async def test_rest_client_requires_context() -> None:
    """Using RestClient outside async context manager raises."""
    client = RestClient(KyroConfig())
    with pytest.raises(KyroError) as exc_info:
        await client.get("/markets")
    assert "context" in str(exc_info.value).lower()


async def test_get_200_json(kyro_client: RestClient) -> None:
    data = await kyro_client.get("/exchange/status")
    assert data["exchange_active"] is True
    assert data["trading_active"] is True


async def test_get_204_empty_body_returns_none(kyro_client: RestClient) -> None:
    data = await kyro_client.get("/empty")
    assert data is None


async def test_get_400_raises_http_error(kyro_client: RestClient) -> None:
    with pytest.raises(KyroHTTPError) as exc_info:
        await kyro_client.get("/error400")
    assert exc_info.value.status == 400
    assert exc_info.value.error_code == "BadRequest"
    assert exc_info.value.response_body is not None


async def test_get_404_raises_http_error(kyro_client: RestClient) -> None:
    with pytest.raises(KyroHTTPError) as exc_info:
        await kyro_client.get("/error404")
    assert exc_info.value.status == 404
    assert exc_info.value.error_code == "MarketNotFound"


async def test_get_500_raises_http_error_with_error_code(kyro_client: RestClient) -> None:
    with pytest.raises(KyroHTTPError) as exc_info:
        await kyro_client.get("/error500")
    assert exc_info.value.status == 500
    assert exc_info.value.error_code == "InternalError"


async def test_path_without_leading_slash_normalized(kyro_client: RestClient) -> None:
    data = await kyro_client.get("markets")
    assert "markets" in data
    assert data["markets"] is not None


async def test_get_with_params(kyro_client: RestClient) -> None:
    data = await kyro_client.get("/echo_params", params={"a": "1", "b": "2"})
    assert data == {"a": "1", "b": "2"}


async def test_post_json(kyro_client: RestClient) -> None:
    data = await kyro_client.post("/echo", json={"ticker": "KXBTC", "count": 5})
    assert data["echo"] == {"ticker": "KXBTC", "count": 5}


async def test_post_with_response_model(kyro_client: RestClient) -> None:
    m = await kyro_client.post(
        "/echo",
        json={"x": 1},
        response_model=_EchoModel,
    )
    assert isinstance(m, _EchoModel)
    assert m.echo == {"x": 1}


async def test_put_json(kyro_client: RestClient) -> None:
    data = await kyro_client.put("/echo", json={"action": "update"})
    assert data["echo"] == {"action": "update"}


async def test_patch_json(kyro_client: RestClient) -> None:
    data = await kyro_client.patch("/echo", json={"field": "patched"})
    assert data["echo"] == {"field": "patched"}


async def test_delete_with_body(kyro_client: RestClient) -> None:
    data = await kyro_client.delete("/portfolio/orders/ord-1")
    assert data is not None
    assert "order" in data or "reduced_by" in data


async def test_delete_without_json(kyro_client: RestClient) -> None:
    data = await kyro_client.delete("/portfolio/orders/ord-1")
    assert data is not None


async def test_invalid_json_body_raises_validation_error(
    kyro_client: RestClient,
) -> None:
    with pytest.raises(KyroValidationError) as exc_info:
        await kyro_client.post("/echo", json={"x": object()})  # not JSON-serializable
    assert "serialize" in str(exc_info.value).lower() or "Failed" in str(exc_info.value)


async def test_get_with_response_model(kyro_client: RestClient) -> None:
    class _Status(BaseModel):
        exchange_active: bool
        trading_active: bool

    m = await kyro_client.get("/exchange/status", response_model=_Status)
    assert m.exchange_active is True
    assert m.trading_active is True


async def test_timeout_raises_kyro_timeout_error(kalshi_base_url: str) -> None:
    # Use 0.1 (config minimum); /slow sleeps 5s so request will time out
    cfg = KyroConfig(base_url=kalshi_base_url, request_timeout=0.1)
    async with RestClient(cfg) as client:
        with pytest.raises(KyroTimeoutError) as exc_info:
            await client.get("/slow")
        assert exc_info.value.timeout is not None or "timed out" in str(exc_info.value).lower()

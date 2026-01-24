"""Tests for rest.api modules (exchange, markets, events, orders, portfolio)."""

from __future__ import annotations

from kyro import RestClient
from kyro.rest.api import events, exchange, markets, orders, portfolio


async def test_get_exchange_status(kyro_client: RestClient) -> None:
    data = await exchange.get_exchange_status(kyro_client)
    assert "exchange_active" in data
    assert "trading_active" in data


async def test_get_markets(kyro_client: RestClient) -> None:
    data = await markets.get_markets(kyro_client)
    assert "markets" in data
    assert isinstance(data["markets"], list)
    assert "cursor" in data


async def test_get_markets_with_params(kyro_client: RestClient) -> None:
    data = await markets.get_markets(kyro_client, limit=10, event_ticker="KXBTC-25", status="open")
    assert "markets" in data


async def test_get_market(kyro_client: RestClient) -> None:
    data = await markets.get_market(kyro_client, "KXBTC")
    assert "market" in data
    assert data["market"]["ticker"] == "KXBTC"


async def test_get_market_orderbook(kyro_client: RestClient) -> None:
    data = await markets.get_market_orderbook(kyro_client, "KXBTC")
    assert "orderbook" in data
    assert "yes" in data["orderbook"]
    assert "no" in data["orderbook"]


async def test_get_trades(kyro_client: RestClient) -> None:
    data = await markets.get_trades(kyro_client)
    assert "trades" in data
    assert "cursor" in data


async def test_get_events(kyro_client: RestClient) -> None:
    data = await events.get_events(kyro_client)
    assert "events" in data
    assert "cursor" in data


async def test_get_event(kyro_client: RestClient) -> None:
    data = await events.get_event(kyro_client, "KXBTC-25")
    assert "event" in data
    assert data["event"]["event_ticker"] == "KXBTC-25"
    assert "markets" in data


async def test_get_orders(kyro_client: RestClient) -> None:
    data = await orders.get_orders(kyro_client)
    assert "orders" in data
    assert "cursor" in data


async def test_get_order(kyro_client: RestClient) -> None:
    data = await orders.get_order(kyro_client, "ord-123")
    assert "order" in data
    assert data["order"]["order_id"] == "ord-123"


async def test_create_order(kyro_client: RestClient) -> None:
    data = await orders.create_order(
        kyro_client,
        ticker="KXBTC",
        side="yes",
        action="buy",
        count=1,
    )
    assert "order" in data
    assert "order_id" in data["order"]


async def test_cancel_order(kyro_client: RestClient) -> None:
    data = await orders.cancel_order(kyro_client, "ord-123")
    assert data is not None
    assert "order" in data or "reduced_by" in data


async def test_get_balance(kyro_client: RestClient) -> None:
    data = await portfolio.get_balance(kyro_client)
    assert "balance" in data
    assert "portfolio_value" in data
    assert "updated_ts" in data

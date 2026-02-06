"""Tests for rest.api modules (exchange, markets, events, search, orders, portfolio)."""

from __future__ import annotations

import pytest

from kyro import RestClient
from kyro.exceptions import KyroValidationError
from kyro.rest.api import events, exchange, markets, orders, portfolio, search


async def test_get_exchange_status(kyro_client: RestClient) -> None:
    data = await exchange.get_exchange_status(kyro_client)
    assert "exchange_active" in data
    assert "trading_active" in data


async def test_get_user_data_timestamp(kyro_client: RestClient) -> None:
    data = await exchange.get_user_data_timestamp(kyro_client)
    assert "as_of_time" in data
    assert isinstance(data["as_of_time"], str)


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


async def test_get_live_data(kyro_client: RestClient) -> None:
    data = await markets.get_live_data(kyro_client, "KXBTC-24JAN15")
    assert "ticker" in data
    assert data["ticker"] == "KXBTC-24JAN15"


async def test_get_multiple_live_data(kyro_client: RestClient) -> None:
    data = await markets.get_multiple_live_data(kyro_client, "KXBTC-24JAN15,INXD-25")
    assert "tickers" in data
    assert isinstance(data["tickers"], list)


async def test_get_events(kyro_client: RestClient) -> None:
    data = await events.get_events(kyro_client)
    assert "events" in data
    assert "cursor" in data


async def test_get_event(kyro_client: RestClient) -> None:
    data = await events.get_event(kyro_client, "KXBTC-25")
    assert "event" in data
    assert data["event"]["event_ticker"] == "KXBTC-25"
    assert "markets" in data


async def test_get_event_candlesticks(kyro_client: RestClient) -> None:
    data = await events.get_event_candlesticks(
        kyro_client, "KXBTC", "INXD-25", period_interval=60, limit=100
    )
    assert "candlesticks" in data
    assert isinstance(data["candlesticks"], list)


async def test_get_sports_filters(kyro_client: RestClient) -> None:
    data = await search.get_sports_filters(kyro_client)
    assert "filters_by_sports" in data
    assert "sport_ordering" in data
    assert isinstance(data["sport_ordering"], list)


async def test_get_tags_by_categories(kyro_client: RestClient) -> None:
    data = await search.get_tags_by_categories(kyro_client)
    assert "tags_by_categories" in data


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


async def test_decrease_order(kyro_client: RestClient) -> None:
    data = await orders.decrease_order(kyro_client, "ord-123", reduce_by=1)
    assert data is not None
    assert "order" in data
    assert data["order"]["order_id"] == "ord-123"
    assert "reduced_by" in data


async def test_get_balance(kyro_client: RestClient) -> None:
    data = await portfolio.get_balance(kyro_client)
    assert "balance" in data
    assert "portfolio_value" in data
    assert "updated_ts" in data


async def test_create_order_invalid_side_raises(kyro_client: RestClient) -> None:
    with pytest.raises(KyroValidationError):
        await orders.create_order(
            kyro_client, ticker="KXBTC", side="invalid", action="buy", count=1
        )


async def test_decrease_order_both_groups_raises(kyro_client: RestClient) -> None:
    with pytest.raises(KyroValidationError):
        await orders.decrease_order(
            kyro_client, "ord-123", reduce_by=1, reduce_to=0
        )


async def test_decrease_order_neither_group_raises(kyro_client: RestClient) -> None:
    with pytest.raises(KyroValidationError):
        await orders.decrease_order(kyro_client, "ord-123")


async def test_transfer_invalid_subaccount_raises(kyro_client: RestClient) -> None:
    with pytest.raises(KyroValidationError):
        await portfolio.transfer_between_subaccounts(
            kyro_client,
            client_transfer_id="test-1",
            from_subaccount=33,
            to_subaccount=0,
            amount_cents=1,
        )


async def test_batch_create_orders(kyro_client: RestClient) -> None:
    data = await orders.batch_create_orders(
        kyro_client,
        [
            {"ticker": "KXBTC", "side": "yes", "action": "buy", "count": 1, "yes_price": 50},
            {"ticker": "KXBTC", "side": "no", "action": "buy", "count": 1, "no_price": 55},
        ],
    )
    assert "orders" in data
    assert len(data["orders"]) == 2
    assert data["orders"][0].get("order", {}).get("order_id") == "b-1"


async def test_batch_create_orders_invalid_at_index_raises(kyro_client: RestClient) -> None:
    with pytest.raises(KyroValidationError) as exc_info:
        await orders.batch_create_orders(
            kyro_client,
            [
                {"ticker": "KXBTC", "side": "yes", "action": "buy", "count": 1},
                {"ticker": "KXBTC", "side": "maybe", "action": "buy", "count": 1},
            ],
        )
    assert "index 1" in str(exc_info.value)

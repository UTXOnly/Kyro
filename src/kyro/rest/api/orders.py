"""Order endpoints. Auth required.

Ref: https://docs.kalshi.com/api-reference/orders/create-order
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kyro.rest.client import RestClient


def _clean(params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}


async def get_orders(
    client: RestClient,
    *,
    ticker: str | None = None,
    event_ticker: str | None = None,
    min_ts: int | None = None,
    max_ts: int | None = None,
    status: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
    subaccount: int | None = None,
) -> Any:
    """Get orders. `GET /portfolio/orders`.

    status: resting, canceled, executed. limit 1–200.
    """
    params = _clean({
        "ticker": ticker,
        "event_ticker": event_ticker,
        "min_ts": min_ts,
        "max_ts": max_ts,
        "status": status,
        "limit": limit,
        "cursor": cursor,
        "subaccount": subaccount,
    })
    return await client.get("/portfolio/orders", params=params or None)


async def get_order(client: RestClient, order_id: str) -> Any:
    """Get a single order. `GET /portfolio/orders/{order_id}`."""
    return await client.get(f"/portfolio/orders/{order_id}")


async def create_order(
    client: RestClient,
    *,
    ticker: str,
    side: str,
    action: str,
    count: int | None = None,
    count_fp: str | None = None,
    type: str | None = None,
    yes_price: int | None = None,
    no_price: int | None = None,
    yes_price_dollars: str | None = None,
    no_price_dollars: str | None = None,
    client_order_id: str | None = None,
    expiration_ts: int | None = None,
    time_in_force: str | None = None,
    buy_max_cost: int | None = None,
    post_only: bool | None = None,
    reduce_only: bool | None = None,
    sell_position_floor: int | None = None,
    self_trade_prevention_type: str | None = None,
    order_group_id: str | None = None,
    cancel_order_on_pause: bool | None = None,
    subaccount: int | None = None,
    **extra: Any,
) -> Any:
    """Create an order. `POST /portfolio/orders`.

    Required: ticker, side (yes|no), action (buy|sell). Provide count or count_fp.
    type: limit|market. time_in_force: fill_or_kill|good_till_canceled|immediate_or_cancel.
    yes_price/no_price 1–99 (cents). subaccount default 0.
    """
    body: dict[str, Any] = {
        "ticker": ticker,
        "side": side,
        "action": action,
        **extra,
    }
    if count is not None:
        body["count"] = count
    if count_fp is not None:
        body["count_fp"] = count_fp
    if type is not None:
        body["type"] = type
    if yes_price is not None:
        body["yes_price"] = yes_price
    if no_price is not None:
        body["no_price"] = no_price
    if yes_price_dollars is not None:
        body["yes_price_dollars"] = yes_price_dollars
    if no_price_dollars is not None:
        body["no_price_dollars"] = no_price_dollars
    if client_order_id is not None:
        body["client_order_id"] = client_order_id
    if expiration_ts is not None:
        body["expiration_ts"] = expiration_ts
    if time_in_force is not None:
        body["time_in_force"] = time_in_force
    if buy_max_cost is not None:
        body["buy_max_cost"] = buy_max_cost
    if post_only is not None:
        body["post_only"] = post_only
    if reduce_only is not None:
        body["reduce_only"] = reduce_only
    if sell_position_floor is not None:
        body["sell_position_floor"] = sell_position_floor
    if self_trade_prevention_type is not None:
        body["self_trade_prevention_type"] = self_trade_prevention_type
    if order_group_id is not None:
        body["order_group_id"] = order_group_id
    if cancel_order_on_pause is not None:
        body["cancel_order_on_pause"] = cancel_order_on_pause
    if subaccount is not None:
        body["subaccount"] = subaccount
    return await client.post("/portfolio/orders", json=body)


async def cancel_order(client: RestClient, order_id: str) -> Any:
    """Cancel an order. `DELETE /portfolio/orders/{order_id}`."""
    return await client.delete(f"/portfolio/orders/{order_id}")


async def amend_order(
    client: RestClient,
    order_id: str,
    *,
    yes_price: int | None = None,
    no_price: int | None = None,
    yes_price_dollars: str | None = None,
    no_price_dollars: str | None = None,
    count: int | None = None,
    count_fp: str | None = None,
    expiration_ts: int | None = None,
    **extra: Any,
) -> Any:
    """Amend an order. `POST /portfolio/orders/{order_id}/amend`."""
    body: dict[str, Any] = dict(extra)
    if yes_price is not None:
        body["yes_price"] = yes_price
    if no_price is not None:
        body["no_price"] = no_price
    if yes_price_dollars is not None:
        body["yes_price_dollars"] = yes_price_dollars
    if no_price_dollars is not None:
        body["no_price_dollars"] = no_price_dollars
    if count is not None:
        body["count"] = count
    if count_fp is not None:
        body["count_fp"] = count_fp
    if expiration_ts is not None:
        body["expiration_ts"] = expiration_ts
    return await client.post(f"/portfolio/orders/{order_id}/amend", json=body)


async def decrease_order(
    client: RestClient,
    order_id: str,
    *,
    count: int | None = None,
    count_fp: str | None = None,
    **extra: Any,
) -> Any:
    """Decrease an order size. `POST /portfolio/orders/{order_id}/decrease`."""
    body: dict[str, Any] = dict(extra)
    if count is not None:
        body["count"] = count
    if count_fp is not None:
        body["count_fp"] = count_fp
    return await client.post(f"/portfolio/orders/{order_id}/decrease", json=body)


async def batch_create_orders(client: RestClient, orders: list[dict[str, Any]]) -> Any:
    """Batch create orders. `POST /portfolio/orders/batch`.

    orders: list of order payloads (same shape as create_order body).
    """
    return await client.post("/portfolio/orders/batch", json={"orders": orders})


async def batch_cancel_orders(
    client: RestClient,
    *,
    order_ids: list[str] | None = None,
    ticker: str | None = None,
    **extra: Any,
) -> Any:
    """Batch cancel orders. `DELETE /portfolio/orders/batch`.

    Provide order_ids (list) or ticker to cancel by market.
    """
    body: dict[str, Any] = dict(extra)
    if order_ids is not None:
        body["order_ids"] = order_ids
    if ticker is not None:
        body["ticker"] = ticker
    return await client.delete("/portfolio/orders/batch", json=body if body else None)

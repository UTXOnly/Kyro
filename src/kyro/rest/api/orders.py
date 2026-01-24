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
    params = _clean(
        {
            "ticker": ticker,
            "event_ticker": event_ticker,
            "min_ts": min_ts,
            "max_ts": max_ts,
            "status": status,
            "limit": limit,
            "cursor": cursor,
            "subaccount": subaccount,
        }
    )
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
    body = _clean(
        {
            "ticker": ticker,
            "side": side,
            "action": action,
            "count": count,
            "count_fp": count_fp,
            "type": type,
            "yes_price": yes_price,
            "no_price": no_price,
            "yes_price_dollars": yes_price_dollars,
            "no_price_dollars": no_price_dollars,
            "client_order_id": client_order_id,
            "expiration_ts": expiration_ts,
            "time_in_force": time_in_force,
            "buy_max_cost": buy_max_cost,
            "post_only": post_only,
            "reduce_only": reduce_only,
            "sell_position_floor": sell_position_floor,
            "self_trade_prevention_type": self_trade_prevention_type,
            "order_group_id": order_group_id,
            "cancel_order_on_pause": cancel_order_on_pause,
            "subaccount": subaccount,
            **extra,
        }
    )
    return await client.post("/portfolio/orders", json=body)


async def cancel_order(client: RestClient, order_id: str) -> Any:
    """Cancel an order. `DELETE /portfolio/orders/{order_id}`.

    Response (200): ``{order, reduced_by, reduced_by_fp}`` per
    https://docs.kalshi.com/api-reference/orders/cancel-order
    """
    return await client.delete(f"/portfolio/orders/{order_id}")


async def amend_order(
    client: RestClient,
    order_id: str,
    *,
    ticker: str,
    side: str,
    action: str,
    yes_price: int | None = None,
    no_price: int | None = None,
    yes_price_dollars: str | None = None,
    no_price_dollars: str | None = None,
    count: int | None = None,
    count_fp: str | None = None,
    client_order_id: str | None = None,
    updated_client_order_id: str | None = None,
    expiration_ts: int | None = None,
    **extra: Any,
) -> Any:
    """Amend an order. `POST /portfolio/orders/{order_id}/amend`.

    Kalshi requires ticker, side (yes|no), action (buy|sell) plus any of:
    yes_price, no_price, yes_price_dollars, no_price_dollars, count, count_fp, etc.
    """
    body = _clean(
        {
            "ticker": ticker,
            "side": side,
            "action": action,
            "yes_price": yes_price,
            "no_price": no_price,
            "yes_price_dollars": yes_price_dollars,
            "no_price_dollars": no_price_dollars,
            "count": count,
            "count_fp": count_fp,
            "client_order_id": client_order_id,
            "updated_client_order_id": updated_client_order_id,
            "expiration_ts": expiration_ts,
            **extra,
        }
    )
    return await client.post(f"/portfolio/orders/{order_id}/amend", json=body)


async def decrease_order(
    client: RestClient,
    order_id: str,
    *,
    reduce_by: int | None = None,
    reduce_by_fp: str | None = None,
    reduce_to: int | None = None,
    reduce_to_fp: str | None = None,
    **extra: Any,
) -> Any:
    """Decrease an order size. `POST /portfolio/orders/{order_id}/decrease`.

    Provide exactly one of: (reduce_by or reduce_by_fp) or (reduce_to or reduce_to_fp).
    reduce_by: contracts to reduce by; reduce_to: contracts to reduce to.
    """
    body = _clean(
        {
            "reduce_by": reduce_by,
            "reduce_by_fp": reduce_by_fp,
            "reduce_to": reduce_to,
            "reduce_to_fp": reduce_to_fp,
            **extra,
        }
    )
    return await client.post(f"/portfolio/orders/{order_id}/decrease", json=body)


async def batch_create_orders(client: RestClient, orders: list[dict[str, Any]]) -> Any:
    """Batch create orders. `POST /portfolio/orders/batched`.

    orders: list of order payloads (same shape as create_order body).
    """
    return await client.post("/portfolio/orders/batched", json={"orders": orders})


async def batch_cancel_orders(
    client: RestClient,
    *,
    order_ids: list[str] | None = None,
    ids: list[str] | None = None,
) -> Any:
    """Batch cancel orders. `DELETE /portfolio/orders/batched`.

    Body: {\"ids\": [...]}. Pass order_ids or ids (ids preferred for Kalshi).
    """
    the_ids = ids if ids is not None else order_ids or []
    return await client.delete("/portfolio/orders/batched", json={"ids": the_ids})

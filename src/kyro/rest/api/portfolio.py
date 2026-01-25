"""Portfolio endpoints. Auth required.

Ref: https://docs.kalshi.com/api-reference/portfolio/get-balance
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kyro.rest.client import RestClient


def _clean(params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}


async def get_portfolio(client: RestClient) -> Any:
    """Get portfolio summary. `GET /portfolio`.

    Auth required. May not be available for all accounts; prefer get_balance,
    get_positions, get_fills for specific data.
    """
    return await client.get("/portfolio")


async def get_balance(client: RestClient) -> Any:
    """Get balance and portfolio value. `GET /portfolio/balance`.

    Returns balance (cents), portfolio_value (cents), updated_ts.
    """
    return await client.get("/portfolio/balance")


async def get_positions(
    client: RestClient,
    *,
    cursor: str | None = None,
    limit: int | None = None,
    count_filter: str | None = None,
    ticker: str | None = None,
    event_ticker: str | None = None,
    subaccount: int | None = None,
) -> Any:
    """Get positions. `GET /portfolio/positions`.

    count_filter: position, total_traded (comma-separated). limit 1–1000.
    """
    params = _clean(
        {
            "cursor": cursor,
            "limit": limit,
            "count_filter": count_filter,
            "ticker": ticker,
            "event_ticker": event_ticker,
            "subaccount": subaccount,
        }
    )
    return await client.get("/portfolio/positions", params=params or None)


async def get_fills(
    client: RestClient,
    *,
    ticker: str | None = None,
    event_ticker: str | None = None,
    min_ts: int | None = None,
    max_ts: int | None = None,
    limit: int | None = None,
    cursor: str | None = None,
    subaccount: int | None = None,
) -> Any:
    """Get fill history. `GET /portfolio/fills`."""
    params = _clean(
        {
            "ticker": ticker,
            "event_ticker": event_ticker,
            "min_ts": min_ts,
            "max_ts": max_ts,
            "limit": limit,
            "cursor": cursor,
            "subaccount": subaccount,
        }
    )
    return await client.get("/portfolio/fills", params=params or None)


async def get_settlements(
    client: RestClient,
    *,
    ticker: str | None = None,
    event_ticker: str | None = None,
    min_ts: int | None = None,
    max_ts: int | None = None,
    limit: int | None = None,
    cursor: str | None = None,
    subaccount: int | None = None,
) -> Any:
    """Get settlements. `GET /portfolio/settlements`."""
    params = _clean(
        {
            "ticker": ticker,
            "event_ticker": event_ticker,
            "min_ts": min_ts,
            "max_ts": max_ts,
            "limit": limit,
            "cursor": cursor,
            "subaccount": subaccount,
        }
    )
    return await client.get("/portfolio/settlements", params=params or None)


async def get_total_resting_order_value(client: RestClient) -> Any:
    """Get total value of resting orders (cents). FCM-oriented.

    `GET /portfolio/summary/total_resting_order_value`
    """
    return await client.get("/portfolio/summary/total_resting_order_value")


async def create_subaccount(client: RestClient, *, nickname: str | None = None) -> Any:
    """Create a subaccount. `POST /portfolio/subaccounts`."""
    body = _clean({"nickname": nickname}) if nickname is not None else {}
    return await client.post("/portfolio/subaccounts", json=body)


async def transfer_between_subaccounts(
    client: RestClient,
    *,
    from_subaccount: int,
    to_subaccount: int,
    amount: int,
) -> Any:
    """Transfer between subaccounts. `POST /portfolio/transfers`.

    amount in cents.
    """
    return await client.post(
        "/portfolio/transfers",
        json={
            "from_subaccount": from_subaccount,
            "to_subaccount": to_subaccount,
            "amount": amount,
        },
    )


async def get_all_subaccount_balances(client: RestClient) -> Any:
    """Get all subaccount balances. `GET /portfolio/subaccounts/balances`."""
    return await client.get("/portfolio/subaccounts/balances")


async def get_subaccount_transfers(
    client: RestClient,
    *,
    limit: int | None = None,
    cursor: str | None = None,
) -> Any:
    """Get subaccount transfer history. `GET /portfolio/subaccounts/transfers`."""
    params = _clean({"limit": limit, "cursor": cursor})
    return await client.get("/portfolio/subaccounts/transfers", params=params or None)

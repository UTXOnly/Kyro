"""Exchange endpoints.

Ref: https://docs.kalshi.com/api-reference/exchange/get-exchange-status
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kyro.rest.client import RestClient


async def get_exchange_status(client: RestClient) -> Any:
    """Get exchange status (exchange_active, trading_active, estimated_resume_time).

    `GET /exchange/status` — no auth required.
    """
    return await client.get("/exchange/status")


async def get_exchange_announcements(client: RestClient) -> Any:
    """Get exchange announcements.

    `GET /exchange/announcements` — no auth required.
    """
    return await client.get("/exchange/announcements")


async def get_exchange_schedule(client: RestClient) -> Any:
    """Get exchange schedule.

    `GET /exchange/schedule` — no auth required.
    """
    return await client.get("/exchange/schedule")


async def get_series_fee_changes(
    client: RestClient,
    *,
    series_ticker: str | None = None,
    show_historical: bool | None = None,
) -> Any:
    """Get series fee changes. `GET /series/fee_changes`.

    Query: series_ticker, show_historical (default false).
    """
    params = {
        k: v
        for k, v in (("series_ticker", series_ticker), ("show_historical", show_historical))
        if v is not None
    }
    return await client.get("/series/fee_changes", params=params or None)


async def get_user_data_timestamp(client: RestClient) -> Any:
    """Get user data timestamp (for sync/consistency).

    `GET /exchange/user-data-timestamp` — auth required.
    """
    return await client.get("/exchange/user-data-timestamp")

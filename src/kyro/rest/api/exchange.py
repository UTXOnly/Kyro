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


async def get_series_fee_changes(client: RestClient) -> Any:
    """Get series fee changes.

    `GET /exchange/series-fee-changes`
    """
    return await client.get("/exchange/series-fee-changes")


async def get_user_data_timestamp(client: RestClient) -> Any:
    """Get user data timestamp (for sync/consistency).

    `GET /exchange/user-data-timestamp` — auth required.
    """
    return await client.get("/exchange/user-data-timestamp")

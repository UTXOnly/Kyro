"""Event endpoints.

Ref: https://docs.kalshi.com/api-reference/events/get-events
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kyro.rest.client import RestClient


def _clean(params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}


async def get_events(
    client: RestClient,
    *,
    limit: int | None = None,
    cursor: str | None = None,
    with_nested_markets: bool | None = None,
    with_milestones: bool | None = None,
    status: str | None = None,
    series_ticker: str | None = None,
    min_close_ts: int | None = None,
) -> Any:
    """Get events (excludes multivariate). `GET /events`.

    Query: limit (1–200), cursor, with_nested_markets, with_milestones,
    status (open|closed|settled), series_ticker, min_close_ts (Unix).
    """
    params = _clean(
        {
            "limit": limit,
            "cursor": cursor,
            "with_nested_markets": with_nested_markets,
            "with_milestones": with_milestones,
            "status": status,
            "series_ticker": series_ticker,
            "min_close_ts": min_close_ts,
        }
    )
    return await client.get("/events", params=params or None)


async def get_event(
    client: RestClient,
    event_ticker: str,
    *,
    with_nested_markets: bool | None = None,
) -> Any:
    """Get a single event by ticker. `GET /events/{event_ticker}`."""
    params = _clean({"with_nested_markets": with_nested_markets})
    return await client.get(f"/events/{event_ticker}", params=params or None)


async def get_event_metadata(client: RestClient, event_ticker: str) -> Any:
    """Get event metadata. `GET /events/{event_ticker}/metadata`."""
    return await client.get(f"/events/{event_ticker}/metadata")


async def get_multivariate_events(
    client: RestClient,
    *,
    limit: int | None = None,
    cursor: str | None = None,
) -> Any:
    """Get multivariate events. `GET /events/multivariate`."""
    params = _clean({"limit": limit, "cursor": cursor})
    return await client.get("/events/multivariate", params=params or None)

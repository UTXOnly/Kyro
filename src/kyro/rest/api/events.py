"""Event endpoints.

Ref: https://docs.kalshi.com/api-reference/events/get-events
"""

from __future__ import annotations

import time
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


async def get_event_candlesticks(
    client: RestClient,
    series_ticker: str,
    event_ticker: str,
    *,
    start_ts: int | None = None,
    end_ts: int | None = None,
    period_interval: int | None = None,
    limit: int | None = None,
    include_latest_before_start: bool | None = None,
) -> Any:
    """Get OHLCV candlesticks for an event. `GET /series/{series_ticker}/events/{event_ticker}/candlesticks`.

    start_ts, end_ts (Unix). period_interval: 1, 60, or 1440 (minutes).
    If start_ts/end_ts omitted, uses last 24h. limit 1–1000.
    """
    now = int(time.time())
    if start_ts is None:
        start_ts = now - 86400
    if end_ts is None:
        end_ts = now
    params = _clean(
        {
            "start_ts": start_ts,
            "end_ts": end_ts,
            "period_interval": period_interval,
            "limit": limit,
            "include_latest_before_start": include_latest_before_start,
        }
    )
    return await client.get(
        f"/series/{series_ticker}/events/{event_ticker}/candlesticks",
        params=params or None,
    )


async def get_multivariate_events(
    client: RestClient,
    *,
    limit: int | None = None,
    cursor: str | None = None,
) -> Any:
    """Get multivariate events. `GET /events/multivariate`."""
    params = _clean({"limit": limit, "cursor": cursor})
    return await client.get("/events/multivariate", params=params or None)

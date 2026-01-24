"""Market endpoints.

Ref: https://docs.kalshi.com/api-reference/market/get-markets
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kyro.rest.client import RestClient


def _clean(params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}


async def get_markets(
    client: RestClient,
    *,
    limit: int | None = None,
    cursor: str | None = None,
    event_ticker: str | None = None,
    series_ticker: str | None = None,
    status: str | None = None,
    tickers: str | None = None,
    min_created_ts: int | None = None,
    max_created_ts: int | None = None,
    min_updated_ts: int | None = None,
    min_close_ts: int | None = None,
    max_close_ts: int | None = None,
    min_settled_ts: int | None = None,
    max_settled_ts: int | None = None,
    mve_filter: str | None = None,
) -> Any:
    """Get markets with optional filters. `GET /markets`.

    Query params: limit (1–1000), cursor, event_ticker, series_ticker, status
    (unopened|open|paused|closed|settled), tickers (comma-separated),
    min/max_created_ts, min_updated_ts, min/max_close_ts, min/max_settled_ts,
    mve_filter (only|exclude).
    """
    params = _clean(
        {
            "limit": limit,
            "cursor": cursor,
            "event_ticker": event_ticker,
            "series_ticker": series_ticker,
            "status": status,
            "tickers": tickers,
            "min_created_ts": min_created_ts,
            "max_created_ts": max_created_ts,
            "min_updated_ts": min_updated_ts,
            "min_close_ts": min_close_ts,
            "max_close_ts": max_close_ts,
            "min_settled_ts": min_settled_ts,
            "max_settled_ts": max_settled_ts,
            "mve_filter": mve_filter,
        }
    )
    return await client.get("/markets", params=params or None)


async def get_market(client: RestClient, ticker: str) -> Any:
    """Get a single market by ticker. `GET /markets/{ticker}`."""
    return await client.get(f"/markets/{ticker}")


async def get_market_orderbook(
    client: RestClient,
    ticker: str,
    *,
    depth: int | None = None,
) -> Any:
    """Get orderbook for a market. `GET /markets/{ticker}/orderbook`.

    depth: 0 or omit = all levels; 1–100 = specific depth.
    """
    params = _clean({"depth": depth})
    return await client.get(f"/markets/{ticker}/orderbook", params=params or None)


async def get_trades(
    client: RestClient,
    *,
    limit: int | None = None,
    cursor: str | None = None,
    ticker: str | None = None,
    min_ts: int | None = None,
    max_ts: int | None = None,
) -> Any:
    """Get trades (all markets or filtered by ticker). `GET /markets/trades`.

    Query: limit (1–1000), cursor, ticker, min_ts, max_ts (Unix).
    """
    params = _clean(
        {
            "limit": limit,
            "cursor": cursor,
            "ticker": ticker,
            "min_ts": min_ts,
            "max_ts": max_ts,
        }
    )
    return await client.get("/markets/trades", params=params or None)


async def get_market_candlesticks(
    client: RestClient,
    ticker: str,
    *,
    series_ticker: str,
    start_ts: int | None = None,
    end_ts: int | None = None,
    period_interval: int | None = None,
    limit: int | None = None,
    include_latest_before_start: bool | None = None,
) -> Any:
    """Get OHLCV candlesticks. `GET /series/{series_ticker}/markets/{ticker}/candlesticks`.

    Kalshi requires series_ticker. start_ts, end_ts (Unix), period_interval (1|60|1440 min).
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
        f"/series/{series_ticker}/markets/{ticker}/candlesticks", params=params or None
    )


async def get_series(
    client: RestClient,
    series_ticker: str,
) -> Any:
    """Get a single series by ticker. `GET /series/{series_ticker}`."""
    return await client.get(f"/series/{series_ticker}")


async def get_series_list(
    client: RestClient,
    *,
    limit: int | None = None,
    cursor: str | None = None,
) -> Any:
    """Get list of series. `GET /series`."""
    params = _clean({"limit": limit, "cursor": cursor})
    return await client.get("/series", params=params or None)


async def get_live_data(client: RestClient, ticker: str) -> Any:
    """Get live data for a market. `GET /live-data` with ticker.

    Query: ticker. (Path may vary; using query as in common patterns.)
    """
    return await client.get("/live-data", params={"ticker": ticker})


async def get_multiple_live_data(
    client: RestClient,
    tickers: str,
) -> Any:
    """Get live data for multiple tickers. `GET /live-data` with tickers.

    tickers: comma-separated.
    """
    return await client.get("/live-data", params={"tickers": tickers})

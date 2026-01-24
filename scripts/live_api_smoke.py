#!/usr/bin/env python3
"""
Live API smoke test: calls every kyro endpoint and method against the real Kalshi API.

Run from repo root (venv activated, pip install -e . or .[dev]):

    python scripts/live_api_smoke.py              # production
    KALSHI_DEMO=1 python scripts/live_api_smoke.py   # demo

Auth: set KALSHI_ACCESS_KEY and KALSHI_PRIVATE_KEY or KALSHI_PRIVATE_KEY_PATH so
auth-required endpoints run. Requires: pip install "kyro[auth]". Otherwise they report
"skip (auth required)". Mutating endpoints (create_order, cancel_order, etc.) are
not called; they report "skip (mutating)".
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass

from kyro import RestClient, config_from_env
from kyro.exceptions import KyroConnectionError, KyroHTTPError, KyroTimeoutError
from kyro.rest import events, exchange, markets, orders, portfolio


@dataclass
class Result:
    module: str
    method: str
    status: str  # ok, skip, fail
    detail: str = ""


async def _get_events(client, ctx: dict) -> None:
    r = await events.get_events(client, limit=5)
    evs = r.get("events") or []
    if evs:
        ctx["event_ticker"] = evs[0].get("event_ticker")


async def _get_markets(client, ctx: dict) -> None:
    r = await markets.get_markets(client, limit=5)
    ms = r.get("markets") or []
    if ms:
        ctx["ticker"] = ms[0].get("ticker")
        ctx["series_ticker"] = ms[0].get("series_ticker")


async def _get_series_list(client, ctx: dict) -> None:
    r = await markets.get_series_list(client, limit=5)
    series = r.get("series") or []
    if series and not ctx.get("series_ticker"):
        s = series[0]
        ctx["series_ticker"] = s.get("ticker") or s.get("series_ticker")


def _ticker(ctx: dict) -> str:
    return ctx.get("ticker") or "KXELONMARS-99"


def _event_ticker(ctx: dict) -> str:
    return ctx.get("event_ticker") or "KXELONMARS-99"


def _series_ticker(ctx: dict) -> str:
    return ctx.get("series_ticker") or "KXHIGHNY"


async def main() -> None:
    cfg = config_from_env()
    print(f"Live API smoke test — {cfg.base_url}\n")

    results: list[Result] = []
    ctx: dict = {}

    # (module, method, coro, skip_reason)
    # coro is async (client, ctx) -> None. skip_reason or None.
    cases: list[tuple[str, str, object, str | None]] = [
        # exchange
        ("exchange", "get_exchange_status", lambda c, x: exchange.get_exchange_status(c), None),
        (
            "exchange",
            "get_exchange_announcements",
            lambda c, x: exchange.get_exchange_announcements(c),
            None,
        ),
        ("exchange", "get_exchange_schedule", lambda c, x: exchange.get_exchange_schedule(c), None),
        (
            "exchange",
            "get_series_fee_changes",
            lambda c, x: exchange.get_series_fee_changes(c),
            None,
        ),
        (
            "exchange",
            "get_user_data_timestamp",
            lambda c, x: exchange.get_user_data_timestamp(c),
            None,
        ),
        # events
        ("events", "get_events", _get_events, None),
        ("events", "get_event", lambda c, x: events.get_event(c, _event_ticker(x)), None),
        (
            "events",
            "get_event_metadata",
            lambda c, x: events.get_event_metadata(c, _event_ticker(x)),
            None,
        ),
        (
            "events",
            "get_multivariate_events",
            lambda c, x: events.get_multivariate_events(c, limit=5),
            None,
        ),
        # markets
        ("markets", "get_markets", _get_markets, None),
        ("markets", "get_market", lambda c, x: markets.get_market(c, _ticker(x)), None),
        (
            "markets",
            "get_market_orderbook",
            lambda c, x: markets.get_market_orderbook(c, _ticker(x)),
            None,
        ),
        ("markets", "get_trades", lambda c, x: markets.get_trades(c, limit=5), None),
        (
            "markets",
            "get_market_candlesticks",
            lambda c, x: markets.get_market_candlesticks(c, _ticker(x), limit=5),
            None,
        ),
        ("markets", "get_series_list", _get_series_list, None),
        ("markets", "get_series", lambda c, x: markets.get_series(c, _series_ticker(x)), None),
        ("markets", "get_live_data", lambda c, x: markets.get_live_data(c, _ticker(x)), None),
        (
            "markets",
            "get_multiple_live_data",
            lambda c, x: markets.get_multiple_live_data(c, _ticker(x)),
            None,
        ),
        # orders
        ("orders", "get_orders", lambda c, x: orders.get_orders(c, limit=5), None),
        ("orders", "get_order", lambda c, x: orders.get_order(c, "live-smoke-fake-order-id"), None),
        ("orders", "create_order", None, "mutating"),
        ("orders", "cancel_order", None, "mutating"),
        ("orders", "amend_order", None, "mutating"),
        ("orders", "decrease_order", None, "mutating"),
        ("orders", "batch_create_orders", None, "mutating"),
        ("orders", "batch_cancel_orders", None, "mutating"),
        # portfolio
        ("portfolio", "get_balance", lambda c, x: portfolio.get_balance(c), None),
        ("portfolio", "get_positions", lambda c, x: portfolio.get_positions(c, limit=5), None),
        ("portfolio", "get_fills", lambda c, x: portfolio.get_fills(c, limit=5), None),
        ("portfolio", "get_settlements", lambda c, x: portfolio.get_settlements(c, limit=5), None),
        (
            "portfolio",
            "get_total_resting_order_value",
            lambda c, x: portfolio.get_total_resting_order_value(c),
            None,
        ),
        (
            "portfolio",
            "get_all_subaccount_balances",
            lambda c, x: portfolio.get_all_subaccount_balances(c),
            None,
        ),
        (
            "portfolio",
            "get_subaccount_transfers",
            lambda c, x: portfolio.get_subaccount_transfers(c, limit=5),
            None,
        ),
        ("portfolio", "create_subaccount", None, "mutating"),
        ("portfolio", "transfer_between_subaccounts", None, "mutating"),
    ]

    async with RestClient(cfg) as client:
        for module, method, coro, skip in cases:
            if skip:
                results.append(Result(module, method, "skip", skip))
                continue
            try:
                await coro(client, ctx)
                results.append(Result(module, method, "ok", ""))
            except KyroHTTPError as e:
                if e.status in (401, 403):
                    results.append(Result(module, method, "skip", "auth required"))
                elif e.status == 404:
                    results.append(Result(module, method, "ok", "404 (endpoint reachable)"))
                else:
                    results.append(
                        Result(module, method, "fail", f"{e.status} {e.error_code or ''}")
                    )
            except (KyroConnectionError, KyroTimeoutError) as e:
                results.append(Result(module, method, "fail", str(e)))
            except Exception as e:
                results.append(Result(module, method, "fail", str(e)))

    # report
    w = 28
    print(f"{'Module':<12} {'Method':<{w}} {'Status':<8} Detail")
    print("-" * (12 + w + 8 + 2 + 50))
    for r in results:
        print(f"{r.module:<12} {r.method:<{w}} {r.status:<8} {r.detail}")

    n_ok = sum(1 for r in results if r.status == "ok")
    n_skip = sum(1 for r in results if r.status == "skip")
    n_fail = sum(1 for r in results if r.status == "fail")
    print()
    print(f"Summary: {n_ok} ok, {n_skip} skip, {n_fail} fail")

    if n_fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

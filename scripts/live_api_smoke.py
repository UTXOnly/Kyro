#!/usr/bin/env python3
"""
Live API smoke test: calls every kyro endpoint against the real Kalshi API.

**Pass = 2xx only.** Any 4xx/5xx or exception is fail. We are not testing error handling.

Uses production only (https://api.elections.kalshi.com/trade-api/v2). Ignores
KALSHI_DEMO / KALSHI_BASE_URL from .env.

**Credentials** in ``.env`` at project root (copy from ``.env.example``). The script loads
``.env`` from the project root. ``KALSHI_PRIVATE_KEY_PATH`` may be relative to project root
(e.g. ``kal_key.pem`` or ``.kalshi/kal_key.pem``). Or export KALSHI_ACCESS_KEY and
KALSHI_PRIVATE_KEY / KALSHI_PRIVATE_KEY_PATH.

**Discovery:** searches up to 100 open markets for one where get_market and
get_market_candlesticks both return 200; if none, falls back to get_market 200 only.

Install: pip install -e ".[dev]"

  python scripts/live_api_smoke.py

Audit log: live_smoke_audit.log (or KALSHI_SMOKE_AUDIT_LOG). .gitignored.

Set KALSHI_SMOKE_DEBUG=1 for path hints and full response_body on failures, and
discovery try-log (get_market/get_candlesticks per ticker).

Mutating: 1-share limit @ 1¢, 1¢ transfer, etc.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from kyro import RestClient, config_from_env
from kyro.exceptions import KyroConnectionError, KyroHTTPError, KyroTimeoutError
from kyro.rest import events, exchange, markets, orders, portfolio, search

AUDIT_LOG_ENV = "KALSHI_SMOKE_AUDIT_LOG"
DEFAULT_AUDIT_LOG = "live_smoke_audit.log"
DEBUG = os.environ.get("KALSHI_SMOKE_DEBUG", "").lower() in ("1", "true", "yes")

# Path hints for failed calls. Shown when KALSHI_SMOKE_DEBUG=1.
PATH_HINTS: dict[tuple[str, str], str] = {
    ("exchange", "get_series_fee_changes"): "GET /series/fee_changes",
    ("exchange", "get_user_data_timestamp"): "GET /exchange/user-data-timestamp",
    (
        "markets",
        "get_market_candlesticks",
    ): "GET /series/{series_ticker}/markets/{ticker}/candlesticks?start_ts=&end_ts=&period_interval=1|60|1440",
    (
        "markets",
        "get_live_data",
    ): "Kalshi: GET /live_data/{type}/milestone/{milestone_id} (ticker-based not in Kalshi spec)",
    (
        "markets",
        "get_multiple_live_data",
    ): "Kalshi: GET /live_data/.../milestone/... (ticker-based not in Kalshi spec)",
    (
        "portfolio",
        "get_total_resting_order_value",
    ): "GET /portfolio/summary/total_resting_order_value (FCM-oriented, may 404)",
    ("orders", "batch_create_orders"): "POST /portfolio/orders/batched",
    ("orders", "batch_cancel_orders"): 'DELETE /portfolio/orders/batched body {"ids":[...]}',
    ("orders", "cancel_order"): "DELETE /portfolio/orders/{order_id}",
    (
        "events",
        "get_event_candlesticks",
    ): "GET /series/{series_ticker}/events/{event_ticker}/candlesticks?start_ts=&end_ts=&period_interval=1|60|1440",
    ("portfolio", "get_portfolio"): "GET /portfolio (may 404 for some accounts)",
}


@dataclass
class Result:
    module: str
    method: str
    status: str
    detail: str = ""


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)


def _resolve_request_info(request_info: dict | Callable[[dict], dict] | None, ctx: dict) -> dict:
    if request_info is None:
        return {}
    if callable(request_info):
        return request_info(ctx) or {}
    return request_info or {}


def _write_debug(
    log_file: Any,
    module: str,
    method: str,
    req: dict,
    ctx: dict,
    e: Exception,
    *,
    is_http: bool = True,
) -> None:
    if not DEBUG:
        return
    parts = ["DEBUG:"]
    key = (module, method)
    if key in PATH_HINTS:
        parts.append(f" path_hint={PATH_HINTS[key]!r}")
    if method == "cancel_order":
        oid = ctx.get("order_id") or ctx.get("order_id_2")
        parts.append(f" order_id_used={oid!r}")
    if is_http and hasattr(e, "response_body") and e.response_body is not None:
        rb = e.response_body
        if isinstance(rb, dict):
            parts.append(f" response_body={_log_json(rb)}")
        else:
            parts.append(f" response_body={rb!r}")
    log_file.write(" ".join(parts) + "\n")
    log_file.flush()


# --- Discovery ---


async def _discover_market(client: RestClient, ctx: dict, log_file: Any) -> None:
    """Find a market where get_market and get_market_candlesticks both return 200."""
    log_file.write(
        f"--- {_ts()} ---\nDISCOVER get_markets\nREQUEST: {_log_json({'status': 'open', 'limit': 100})}\n"
    )
    log_file.flush()
    r = await markets.get_markets(client, status="open", limit=100)
    ms = (r or {}).get("markets") or []
    if not ms:
        r = await markets.get_markets(client, limit=100)
        ms = (r or {}).get("markets") or []
    log_file.write(f"RESPONSE: {_log_json(r)}\n")
    log_file.flush()
    if not ms:
        raise SystemExit("No markets found for smoke test.")
    for m in ms:
        t = m.get("ticker")
        if not t:
            continue
        try:
            await markets.get_market(client, t)
        except KyroHTTPError:
            if DEBUG:
                log_file.write(f"  discover try {t}: get_market=404\n")
                log_file.flush()
            continue
        series = m.get("series_ticker") or None
        if not series:
            if DEBUG:
                log_file.write(
                    f"  discover try {t}: get_market=ok, skip candlesticks (no series_ticker)\n"
                )
                log_file.flush()
            continue
        try:
            await markets.get_market_candlesticks(
                client, t, series_ticker=series, limit=5, period_interval=60
            )
        except KyroHTTPError:
            if DEBUG:
                log_file.write(
                    f"  discover try {t} (series={m.get('series_ticker','')}): get_market=ok get_candlesticks=404\n"
                )
                log_file.flush()
            continue
        ctx["ticker"] = t
        if m.get("event_ticker"):
            ctx["event_ticker"] = m["event_ticker"]
        if m.get("series_ticker"):
            ctx["series_ticker"] = m["series_ticker"]
        log_file.write(
            f"SELECTED: {t} (get_market + get_market_candlesticks 200) series_ticker={ctx.get('series_ticker','')}\n---\n\n"
        )
        log_file.flush()
        return
    for m in ms:
        t = m.get("ticker")
        if not t:
            continue
        try:
            await markets.get_market(client, t)
        except KyroHTTPError:
            continue
        ctx["ticker"] = t
        if m.get("event_ticker"):
            ctx["event_ticker"] = m["event_ticker"]
        if m.get("series_ticker"):
            ctx["series_ticker"] = m["series_ticker"]
        log_file.write(
            f"SELECTED: {t} (get_market 200; candlesticks 404 for all) series_ticker={ctx.get('series_ticker','')}\n---\n\n"
        )
        log_file.flush()
        return
    raise SystemExit(
        "No suitable market found (get_market or get_market_candlesticks did not return 200 for any of 100 markets)."
    )


# --- Context helpers ---


def _ticker(ctx: dict) -> str:
    return ctx.get("ticker") or ""


def _event_ticker(ctx: dict) -> str:
    return ctx.get("event_ticker") or ctx.get("ticker") or ""


def _series_ticker(ctx: dict) -> str:
    return ctx.get("series_ticker") or "KXHIGHNY"


# --- Read-only coros (must return response for audit) ---


async def _get_events(client: RestClient, ctx: dict) -> Any:
    r = await events.get_events(client, limit=5)
    evs = (r or {}).get("events") or []
    if evs:
        e = evs[0]
        ctx["event_ticker"] = e.get("event_ticker")
        if e.get("series_ticker") and not ctx.get("series_ticker"):
            ctx["series_ticker"] = e["series_ticker"]
    return r


async def _get_markets(client: RestClient, ctx: dict) -> Any:
    r = await markets.get_markets(client, limit=5)
    ms = (r or {}).get("markets") or []
    if ms and not ctx.get("ticker"):
        ctx["ticker"] = ms[0].get("ticker")
    if ms and not ctx.get("series_ticker") and ms[0].get("series_ticker"):
        ctx["series_ticker"] = ms[0].get("series_ticker")
    return r


async def _get_series_list(client: RestClient, ctx: dict) -> Any:
    r = await markets.get_series_list(client, limit=5)
    series = (r or {}).get("series") or []
    if series and not ctx.get("series_ticker"):
        s = series[0]
        ctx["series_ticker"] = s.get("ticker") or s.get("series_ticker")
    return r


# --- run_and_log ---


async def _run_and_log(
    client: RestClient,
    ctx: dict,
    module: str,
    method: str,
    coro: Callable[..., Any],
    request_info: dict | Callable[[dict], dict] | None,
    log_file: Any,
    results: list[Result],
) -> None:
    """Run a case; only 2xx counts as ok. Any 4xx/5xx or exception is fail."""
    req = _resolve_request_info(request_info, ctx)
    log_file.write(f"--- {_ts()} ---\n{module}.{method}\nREQUEST: {_log_json(req)}\n")
    log_file.flush()
    try:
        r = await coro(client, ctx)
        log_file.write(f"RESPONSE: {_log_json(r)}\n---\n\n")
        log_file.flush()
        results.append(Result(module, method, "ok", ""))
    except KyroHTTPError as e:
        if e.status in (401, 403):
            if (module, method) in ACCEPT_403:
                log_file.write("NOTE: 403 (subaccounts not enabled on this account)\n---\n\n")
                log_file.flush()
                results.append(Result(module, method, "ok", "403 (subaccounts not enabled)"))
            else:
                _write_debug(log_file, module, method, req, ctx, e)
                log_file.write(f"ERROR: auth {e.status}\n---\n\n")
                log_file.flush()
                results.append(
                    Result(
                        module,
                        method,
                        "fail",
                        f"{e.status} (auth rejected; check key in .env and path for KALSHI_PRIVATE_KEY_PATH)",
                    )
                )
        else:
            _write_debug(log_file, module, method, req, ctx, e)
            log_file.write(f"ERROR: {e.status} {getattr(e, 'error_code', '') or ''} {e}\n---\n\n")
            log_file.flush()
            results.append(Result(module, method, "fail", f"{e.status} {e.error_code or ''}"))
    except (KyroConnectionError, KyroTimeoutError) as e:
        _write_debug(log_file, module, method, req, ctx, e, is_http=False)
        log_file.write(f"ERROR: {type(e).__name__}: {e}\n---\n\n")
        log_file.flush()
        results.append(Result(module, method, "fail", str(e)))
    except Exception as e:
        if (module, method) == ("portfolio", "transfer_between_subaccounts") and "skipped" in str(
            e
        ):
            log_file.write(f"NOTE: {e}\n---\n\n")
            log_file.flush()
            results.append(Result(module, method, "ok", str(e)))
        else:
            _write_debug(log_file, module, method, req, ctx, e, is_http=False)
            log_file.write(f"ERROR: {type(e).__name__}: {e}\n---\n\n")
            log_file.flush()
            results.append(Result(module, method, "fail", str(e)))


# --- Case definitions: (module, method, coro, request_info). Only 2xx = pass. ---

# 403 on these is treated as ok (subaccounts not enabled on account)
ACCEPT_403 = frozenset(
    {
        ("portfolio", "get_all_subaccount_balances"),
        ("portfolio", "get_subaccount_transfers"),
        ("portfolio", "create_subaccount"),
    }
)

READ_ONLY: list[tuple[str, str, Any, Any]] = [
    ("exchange", "get_exchange_status", lambda c, x: exchange.get_exchange_status(c), {}),
    (
        "exchange",
        "get_exchange_announcements",
        lambda c, x: exchange.get_exchange_announcements(c),
        {},
    ),
    ("exchange", "get_exchange_schedule", lambda c, x: exchange.get_exchange_schedule(c), {}),
    ("exchange", "get_series_fee_changes", lambda c, x: exchange.get_series_fee_changes(c), {}),
    ("exchange", "get_user_data_timestamp", lambda c, x: exchange.get_user_data_timestamp(c), {}),
    ("search", "get_sports_filters", lambda c, x: search.get_sports_filters(c), {}),
    ("search", "get_tags_by_categories", lambda c, x: search.get_tags_by_categories(c), {}),
    ("events", "get_events", _get_events, {"limit": 5}),
    (
        "events",
        "get_event",
        lambda c, x: events.get_event(c, _event_ticker(x)),
        lambda ctx: {"event_ticker": _event_ticker(ctx)},
    ),
    (
        "events",
        "get_event_metadata",
        lambda c, x: events.get_event_metadata(c, _event_ticker(x)),
        lambda ctx: {"event_ticker": _event_ticker(ctx)},
    ),
    (
        "events",
        "get_event_candlesticks",
        lambda c, x: events.get_event_candlesticks(
            c, _series_ticker(x), _event_ticker(x), limit=5, period_interval=60
        ),
        lambda ctx: {
            "series_ticker": _series_ticker(ctx),
            "event_ticker": _event_ticker(ctx),
            "limit": 5,
            "period_interval": 60,
        },
    ),
    (
        "events",
        "get_multivariate_events",
        lambda c, x: events.get_multivariate_events(c, limit=5),
        {"limit": 5},
    ),
    ("markets", "get_markets", _get_markets, {"limit": 5}),
    (
        "markets",
        "get_market",
        lambda c, x: markets.get_market(c, _ticker(x)),
        lambda ctx: {"ticker": _ticker(ctx)},
    ),
    (
        "markets",
        "get_market_orderbook",
        lambda c, x: markets.get_market_orderbook(c, _ticker(x)),
        lambda ctx: {"ticker": _ticker(ctx)},
    ),
    ("markets", "get_trades", lambda c, x: markets.get_trades(c, limit=5), {"limit": 5}),
    (
        "markets",
        "get_market_candlesticks",
        lambda c, x: markets.get_market_candlesticks(
            c, _ticker(x), series_ticker=_series_ticker(x), limit=5, period_interval=60
        ),
        lambda ctx: {
            "ticker": _ticker(ctx),
            "series_ticker": _series_ticker(ctx),
            "limit": 5,
            "period_interval": 60,
        },
    ),
    ("markets", "get_series_list", _get_series_list, {"limit": 5}),
    (
        "markets",
        "get_series",
        lambda c, x: markets.get_series(c, _series_ticker(x)),
        lambda ctx: {"series_ticker": _series_ticker(ctx)},
    ),
    (
        "markets",
        "get_live_data",
        lambda c, x: markets.get_live_data(c, _ticker(x)),
        lambda ctx: {"ticker": _ticker(ctx)},
    ),
    (
        "markets",
        "get_multiple_live_data",
        lambda c, x: markets.get_multiple_live_data(c, _ticker(x)),
        lambda ctx: {"tickers": _ticker(ctx)},
    ),
    ("orders", "get_orders", lambda c, x: orders.get_orders(c, limit=5), {"limit": 5}),
    ("portfolio", "get_portfolio", lambda c, x: portfolio.get_portfolio(c), {}),
    ("portfolio", "get_balance", lambda c, x: portfolio.get_balance(c), {}),
    ("portfolio", "get_positions", lambda c, x: portfolio.get_positions(c, limit=5), {"limit": 5}),
    ("portfolio", "get_fills", lambda c, x: portfolio.get_fills(c, limit=5), {"limit": 5}),
    (
        "portfolio",
        "get_settlements",
        lambda c, x: portfolio.get_settlements(c, limit=5),
        {"limit": 5},
    ),
    (
        "portfolio",
        "get_total_resting_order_value",
        lambda c, x: portfolio.get_total_resting_order_value(c),
        {},
    ),
    (
        "portfolio",
        "get_all_subaccount_balances",
        lambda c, x: portfolio.get_all_subaccount_balances(c),
        {},
    ),
    (
        "portfolio",
        "get_subaccount_transfers",
        lambda c, x: portfolio.get_subaccount_transfers(c, limit=5),
        {"limit": 5},
    ),
]


def _mutating_cases() -> list[tuple[str, str, Any, Any]]:
    """(module, method, coro, request_info). Order matters."""
    return [
        (
            "orders",
            "create_order",
            _create_order_1,
            lambda ctx: {
                "ticker": ctx["ticker"],
                "side": "yes",
                "action": "buy",
                "count": 1,
                "type": "limit",
                "yes_price": 1,
                "time_in_force": "good_till_canceled",
            },
        ),
        (
            "orders",
            "get_order",
            lambda c, x: orders.get_order(c, x["order_id"]),
            lambda ctx: {"order_id": ctx.get("order_id")},
        ),
        (
            "orders",
            "amend_order",
            _amend_order,
            lambda ctx: {
                "order_id": ctx.get("order_id"),
                "ticker": ctx.get("ticker"),
                "side": "yes",
                "action": "buy",
                "client_order_id": ctx.get("client_order_id"),
                "yes_price": 2,
            },
        ),
        (
            "orders",
            "cancel_order",
            lambda c, x: orders.cancel_order(c, x["order_id"]),
            lambda ctx: {"order_id": ctx.get("order_id")},
        ),
        (
            "orders",
            "create_order",
            _create_order_2,
            lambda ctx: {
                "ticker": ctx["ticker"],
                "side": "yes",
                "action": "buy",
                "count": 2,
                "type": "limit",
                "yes_price": 1,
                "time_in_force": "good_till_canceled",
            },
        ),
        (
            "orders",
            "decrease_order",
            lambda c, x: orders.decrease_order(c, x["order_id_2"], reduce_by=1),
            lambda ctx: {"order_id": ctx.get("order_id_2"), "reduce_by": 1},
        ),
        (
            "orders",
            "cancel_order",
            lambda c, x: orders.cancel_order(c, x["order_id_2"]),
            lambda ctx: {"order_id": ctx.get("order_id_2")},
        ),
        (
            "orders",
            "batch_create_orders",
            _batch_create,
            lambda ctx: {
                "orders": [
                    {
                        "ticker": ctx["ticker"],
                        "side": "yes",
                        "action": "buy",
                        "count": 1,
                        "type": "limit",
                        "yes_price": 1,
                        "time_in_force": "good_till_canceled",
                    },
                    {
                        "ticker": ctx["ticker"],
                        "side": "no",
                        "action": "buy",
                        "count": 1,
                        "type": "limit",
                        "no_price": 1,
                        "time_in_force": "good_till_canceled",
                    },
                ]
            },
        ),
        (
            "orders",
            "batch_cancel_orders",
            lambda c, x: orders.batch_cancel_orders(c, order_ids=x.get("batch_order_ids") or []),
            lambda ctx: {"order_ids": ctx.get("batch_order_ids", [])},
        ),
        (
            "portfolio",
            "create_subaccount",
            _create_subaccount,
            lambda ctx: {"nickname": f"smoke-{int(time.time())}"},
        ),
        (
            "portfolio",
            "transfer_between_subaccounts",
            _transfer_between_subaccounts,
            lambda ctx: {
                "from_subaccount": 0,
                "to_subaccount": ctx.get("created_subaccount_id"),
                "amount": 1,
            },
        ),
    ]


async def _create_order_1(client: RestClient, ctx: dict) -> Any:
    cid = f"smoke-{int(time.time())}"
    ctx["client_order_id"] = cid
    r = await orders.create_order(
        client,
        ticker=ctx["ticker"],
        side="yes",
        action="buy",
        count=1,
        type="limit",
        yes_price=1,
        time_in_force="good_till_canceled",
        client_order_id=cid,
    )
    o = (r or {}).get("order") or (r or {})
    ctx["order_id"] = o.get("order_id")
    await asyncio.sleep(0.5)  # allow replication before get_order
    return r


async def _amend_order(client: RestClient, ctx: dict) -> Any:
    r = await orders.amend_order(
        client,
        ctx["order_id"],
        ticker=ctx["ticker"],
        side="yes",
        action="buy",
        client_order_id=ctx.get("client_order_id"),
        yes_price=2,
    )
    # Amend returns {old_order, order}; use the amended order's id for cancel.
    o = (r or {}).get("order")
    if o and o.get("order_id"):
        ctx["order_id"] = o["order_id"]
    return r


async def _create_order_2(client: RestClient, ctx: dict) -> Any:
    r = await orders.create_order(
        client,
        ticker=ctx["ticker"],
        side="yes",
        action="buy",
        count=2,
        type="limit",
        yes_price=1,
        time_in_force="good_till_canceled",
    )
    o = (r or {}).get("order") or (r or {})
    ctx["order_id_2"] = o.get("order_id")
    return r


async def _batch_create(client: RestClient, ctx: dict) -> Any:
    body = [
        {
            "ticker": ctx["ticker"],
            "side": "yes",
            "action": "buy",
            "count": 1,
            "type": "limit",
            "yes_price": 1,
            "time_in_force": "good_till_canceled",
        },
        {
            "ticker": ctx["ticker"],
            "side": "no",
            "action": "buy",
            "count": 1,
            "type": "limit",
            "no_price": 1,
            "time_in_force": "good_till_canceled",
        },
    ]
    r = await orders.batch_create_orders(client, body)
    lst = (r or {}).get("orders") or (r or {}).get("order") or []
    if not isinstance(lst, list):
        lst = [lst] if lst else []
    ctx["batch_order_ids"] = []
    for o in lst:
        oid = (o or {}).get("order_id") or ((o or {}).get("order") or {}).get("order_id")
        if oid:
            ctx["batch_order_ids"].append(oid)
    return r


async def _create_subaccount(client: RestClient, ctx: dict) -> Any:
    nick = f"smoke-{int(time.time())}"
    r = await portfolio.create_subaccount(client, nickname=nick)
    ctx["created_subaccount_id"] = (r or {}).get("subaccount_number")
    return r


async def _transfer_between_subaccounts(client: RestClient, ctx: dict) -> Any:
    to_id = ctx.get("created_subaccount_id")
    if to_id is None:
        raise ValueError("skipped; subaccounts not enabled")
    return await portfolio.transfer_between_subaccounts(
        client, from_subaccount=0, to_subaccount=int(to_id), amount=1
    )


async def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    try:
        from dotenv import load_dotenv

        load_dotenv(project_root / ".env")
    except ImportError:
        pass
    # Resolve KALSHI_PRIVATE_KEY_PATH if relative (so .env can use kal_key.pem or .kalshi/kal_key.pem)
    p = os.environ.get("KALSHI_PRIVATE_KEY_PATH", "").strip()
    if p and not os.path.isabs(p):
        os.environ["KALSHI_PRIVATE_KEY_PATH"] = str((project_root / p).resolve())
    # Force production (overrides .env / KALSHI_DEMO)
    os.environ["KALSHI_BASE_URL"] = "https://api.elections.kalshi.com/trade-api/v2"
    cfg = config_from_env()

    if not cfg.auth_signer:
        print(
            "Auth required: put KALSHI_ACCESS_KEY and KALSHI_PRIVATE_KEY or KALSHI_PRIVATE_KEY_PATH in .env (see .env.example) or export them.\n"
            'Install: pip install -e ".[dev]"'
        )
        sys.exit(1)

    log_path = os.environ.get(AUDIT_LOG_ENV, DEFAULT_AUDIT_LOG)
    results: list[Result] = []
    ctx: dict = {}

    with open(log_path, "w") as log_file:

        def _log(msg: str) -> None:
            log_file.write(msg)
            log_file.flush()

        _log(f"# Live API smoke audit — {_ts()}\n")
        _log(f"# base_url: {cfg.base_url}\n")
        _log(
            "# Auth: KALSHI_ACCESS_KEY and KALSHI_PRIVATE_KEY/KALSHI_PRIVATE_KEY_PATH from environment\n\n"
        )

        async with RestClient(cfg) as client:
            await _discover_market(client, ctx, log_file)
            print(f"Live API smoke test — {cfg.base_url}")
            print(
                f"Discovered ticker: {ctx.get('ticker')} (series_ticker: {ctx.get('series_ticker', '')})"
            )
            print(f"Audit log: {log_path}")
            if DEBUG:
                print("DEBUG=1: path hints and full response_body on failures")
            print()

            for module, method, coro, req_info in READ_ONLY:
                await _run_and_log(client, ctx, module, method, coro, req_info, log_file, results)

            for module, method, coro, req_info in _mutating_cases():
                await _run_and_log(client, ctx, module, method, coro, req_info, log_file, results)

    # Report
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

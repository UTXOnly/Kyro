"""Local mock Kalshi API server for benchmarks.

Mimics Kalshi response shapes so REST client benchmarks measure client overhead
(parsing, serialization, client logic) instead of network/API variance.

Run in a background thread via run_server_thread() for pytest, or standalone:

    MOCK_KALSHI_PORT=8765 python -m benchmarks.mock_server
"""

from __future__ import annotations

import asyncio
import os
import threading
import time

from aiohttp import web

# --- Richer mock payloads (benchmark‑realistic) ---

MOCK_MARKETS = [
    {"ticker": f"MOCK-{i:02d}", "title": f"Mock market {i}", "status": "open"} for i in range(1, 11)
]

MOCK_EVENTS = [
    {"event_ticker": f"MOCKEVT-{i:02d}", "title": f"Mock event {i}", "status": "open"}
    for i in range(1, 11)
]

MOCK_ORDERBOOK = {
    "orderbook": {
        "yes": [[45, 100], [46, 200], [47, 150], [48, 80], [49, 300]],
        "no": [[55, 120], [54, 180], [53, 90], [52, 200], [51, 110]],
    },
    "orderbook_fp": {},
}

MOCK_ORDERS = [
    {
        "order_id": f"ord-mock-{i}",
        "market_ticker": "MOCK-01",
        "side": "yes",
        "action": "buy",
        "yes_price": 50,
        "no_price": 50,
        "count": 10,
        "status": "resting",
    }
    for i in range(1, 4)
]


def _json(obj: dict) -> web.Response:
    return web.json_response(obj)


async def _exchange_status(_: web.Request) -> web.Response:
    return _json({"exchange_active": True, "trading_active": True})


async def _markets_list(_: web.Request) -> web.Response:
    return _json({"markets": MOCK_MARKETS, "cursor": ""})


async def _market_detail(r: web.Request) -> web.Response:
    t = r.match_info["ticker"]
    return _json({"market": {"ticker": t, "title": f"Mock {t}", "status": "open"}})


async def _market_orderbook(_: web.Request) -> web.Response:
    return _json(MOCK_ORDERBOOK)


async def _markets_trades(_: web.Request) -> web.Response:
    return _json({"trades": [], "cursor": ""})


async def _events_list(_: web.Request) -> web.Response:
    return _json({"events": MOCK_EVENTS, "cursor": ""})


async def _event_detail(r: web.Request) -> web.Response:
    t = r.match_info["ticker"]
    return _json({"event": {"event_ticker": t, "title": f"Mock event {t}"}, "markets": []})


async def _portfolio_balance(_: web.Request) -> web.Response:
    return _json({"balance": 10000, "portfolio_value": 10000, "updated_ts": 0})


async def _portfolio_orders_list(_: web.Request) -> web.Response:
    return _json({"orders": MOCK_ORDERS, "cursor": ""})


def create_mock_kalshi_app() -> web.Application:
    """aiohttp app that mimics Kalshi-style routes and response shapes."""
    app = web.Application()
    app.router.add_get("/exchange/status", _exchange_status)
    app.router.add_get("/markets", _markets_list)
    app.router.add_get(r"/markets/{ticker}", _market_detail)
    app.router.add_get(r"/markets/{ticker}/orderbook", _market_orderbook)
    app.router.add_get("/markets/trades", _markets_trades)
    app.router.add_get("/events", _events_list)
    app.router.add_get(r"/events/{ticker}", _event_detail)
    app.router.add_get("/portfolio/balance", _portfolio_balance)
    app.router.add_get("/portfolio/orders", _portfolio_orders_list)
    return app


async def _run(port: int, stop_event: threading.Event, url_holder: list[str]) -> None:
    app = create_mock_kalshi_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", port)
    await site.start()
    # Resolve actual port when port=0 (OS‑assigned)
    actual = port
    try:
        socks = getattr(getattr(site, "_server", None), "sockets", None) or []
        if socks:
            actual = socks[0].getsockname()[1]
    except Exception:
        pass
    url_holder.append(f"http://127.0.0.1:{actual}")
    await asyncio.to_thread(stop_event.wait)
    await runner.cleanup()


def _thread_main(port: int, stop_event: threading.Event, url_holder: list[str]) -> None:
    asyncio.run(_run(port, stop_event, url_holder))


def run_server_thread(port: int = 0) -> tuple[str, threading.Event, threading.Thread]:
    """Start the mock Kalshi app in a background thread.

    Args:
        port: 0 for OS‑assigned, or a fixed port.

    Returns:
        (base_url, stop_event, thread). Call stop_event.set() then thread.join()
        to shut down.
    """
    stop = threading.Event()
    url_holder: list[str] = []
    thread = threading.Thread(target=_thread_main, args=(port, stop, url_holder))
    thread.start()
    for _ in range(100):
        if url_holder:
            break
        time.sleep(0.02)
    if not url_holder:
        stop.set()
        thread.join(timeout=2)
        raise RuntimeError("Mock Kalshi server did not report URL in time")
    return (url_holder[0], stop, thread)


def run_standalone(port: int | None = None) -> None:
    """Run the mock server in the current process (blocking). For manual/CI use."""
    port = port or int(os.environ.get("MOCK_KALSHI_PORT", "8765"))
    app = create_mock_kalshi_app()
    web.run_app(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    run_standalone()

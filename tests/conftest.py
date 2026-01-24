"""Pytest fixtures for Kyro tests."""

from __future__ import annotations

import asyncio

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer


def _mk_json(obj: dict) -> web.Response:
    return web.json_response(obj)


async def _echo_post(request: web.Request) -> web.Response:
    """Echo JSON body for POST tests."""
    body = await request.json()
    return web.json_response({"echo": body})


async def _echo_params(request: web.Request) -> web.Response:
    """Echo query params as JSON for GET tests."""
    return _mk_json(dict(request.query))


async def _empty(_: web.Request) -> web.Response:
    return web.Response(status=204)


async def _error_400(_: web.Request) -> web.Response:
    return web.json_response({"error": "BadRequest", "message": "invalid"}, status=400)


async def _error_404(_: web.Request) -> web.Response:
    # Use "code" so client's _parse_error_body picks it (error/error_code take precedence)
    return web.json_response({"code": "MarketNotFound", "message": "Not found"}, status=404)


async def _error_500(_: web.Request) -> web.Response:
    return web.json_response(
        {"error_code": "InternalError", "message": "server error"}, status=500
    )


async def _slow(_: web.Request) -> web.Response:
    await asyncio.sleep(5)
    return web.json_response({})


async def _exchange_status(_: web.Request) -> web.Response:
    return _mk_json({"exchange_active": True, "trading_active": True})


async def _markets_list(_: web.Request) -> web.Response:
    return _mk_json({"markets": [{"ticker": "KXBTC"}], "cursor": ""})


async def _market_detail(r: web.Request) -> web.Response:
    return _mk_json({"market": {"ticker": r.match_info["ticker"]}})


async def _market_orderbook(r: web.Request) -> web.Response:
    return _mk_json({"orderbook": {"yes": [], "no": []}, "orderbook_fp": {}})


async def _markets_trades(_: web.Request) -> web.Response:
    return _mk_json({"trades": [], "cursor": ""})


async def _events_list(_: web.Request) -> web.Response:
    return _mk_json({"events": [], "cursor": ""})


async def _event_detail(r: web.Request) -> web.Response:
    return _mk_json({"event": {"event_ticker": r.match_info["ticker"]}, "markets": []})


async def _portfolio_balance(_: web.Request) -> web.Response:
    return _mk_json({"balance": 10000, "portfolio_value": 10000, "updated_ts": 0})


async def _portfolio_orders_list(_: web.Request) -> web.Response:
    return _mk_json({"orders": [], "cursor": ""})


async def _portfolio_order_detail(r: web.Request) -> web.Response:
    return _mk_json({"order": {"order_id": r.match_info["order_id"]}})


async def _portfolio_order_create(_: web.Request) -> web.Response:
    return _mk_json({"order": {"order_id": "ord-1"}})


async def _portfolio_order_delete(r: web.Request) -> web.Response:
    return _mk_json({"order": {"order_id": r.match_info["order_id"]}, "reduced_by": 1})


def create_kalshi_app() -> web.Application:
    """Minimal aiohttp app that mimics Kalshi-style routes for testing."""
    app = web.Application()
    # Exchange
    app.router.add_get("/exchange/status", _exchange_status)
    # Markets
    app.router.add_get("/markets", _markets_list)
    app.router.add_get(r"/markets/{ticker}", _market_detail)
    app.router.add_get(r"/markets/{ticker}/orderbook", _market_orderbook)
    app.router.add_get("/markets/trades", _markets_trades)
    # Events
    app.router.add_get("/events", _events_list)
    app.router.add_get(r"/events/{ticker}", _event_detail)
    # Portfolio (auth-style; we don't enforce auth in tests)
    app.router.add_get("/portfolio/balance", _portfolio_balance)
    app.router.add_get("/portfolio/orders", _portfolio_orders_list)
    app.router.add_get(r"/portfolio/orders/{order_id}", _portfolio_order_detail)
    app.router.add_post("/portfolio/orders", _portfolio_order_create)
    app.router.add_delete(r"/portfolio/orders/{order_id}", _portfolio_order_delete)
    # Test helpers: empty, errors, echo, params, slow
    app.router.add_get("/empty", _empty)
    app.router.add_get("/error400", _error_400)
    app.router.add_get("/error404", _error_404)
    app.router.add_get("/error500", _error_500)
    app.router.add_get("/echo_params", _echo_params)
    app.router.add_get("/slow", _slow)
    app.router.add_post("/echo", _echo_post)
    app.router.add_put("/echo", _echo_post)
    app.router.add_patch("/echo", _echo_post)
    return app


@pytest.fixture
def app() -> web.Application:
    """Application used by aiohttp test server."""
    return create_kalshi_app()


@pytest.fixture
async def kalshi_base_url(app: web.Application) -> str:
    """Base URL for the in-process Kalshi-style test server."""
    server = TestServer(app)
    await server.start_server()
    try:
        yield str(server.make_url("/")).rstrip("/")
    finally:
        await server.close()


@pytest.fixture
async def kyro_client(kalshi_base_url: str):
    """RestClient connected to the in-process test server."""
    from kyro import KyroConfig, RestClient

    cfg = KyroConfig(base_url=kalshi_base_url)
    async with RestClient(cfg) as client:
        yield client

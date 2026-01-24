"""Benchmarks for RestClient against the live Kalshi API.

Uses config_from_env() (KALSHI_ACCESS_KEY, KALSHI_PRIVATE_KEY or KALSHI_PRIVATE_KEY_PATH,
KALSHI_DEMO=1, etc.). Public endpoints work without auth; balance/orders need creds.

Run: pytest benchmarks/bench_rest_client.py -v --benchmark-only
"""

from __future__ import annotations

import asyncio

import pytest

from kyro import RestClient
from kyro.exceptions import KyroHTTPError
from kyro.rest.api import exchange, events, markets, orders, portfolio


async def _one_exchange_status(cfg) -> dict:
    async with RestClient(cfg) as client:
        return await exchange.get_exchange_status(client)


async def _one_get_markets(cfg) -> dict:
    async with RestClient(cfg) as client:
        return await markets.get_markets(client, limit=10)


async def _one_get_events(cfg) -> dict:
    async with RestClient(cfg) as client:
        return await events.get_events(client, limit=10)


async def _one_get_orderbook(cfg, ticker: str) -> dict:
    async with RestClient(cfg) as client:
        return await markets.get_market_orderbook(client, ticker, depth=5)


async def _one_get_balance(cfg) -> dict:
    async with RestClient(cfg) as client:
        return await portfolio.get_balance(client)


async def _one_get_orders(cfg) -> dict:
    async with RestClient(cfg) as client:
        return await orders.get_orders(client, limit=5)


def test_get_exchange_status(benchmark: object, bench_config) -> None:
    def run() -> dict:
        return asyncio.run(_one_exchange_status(bench_config))

    benchmark(run)


def test_get_markets(benchmark: object, bench_config) -> None:
    def run() -> dict:
        return asyncio.run(_one_get_markets(bench_config))

    benchmark(run)


def test_get_events(benchmark: object, bench_config) -> None:
    def run() -> dict:
        return asyncio.run(_one_get_events(bench_config))

    benchmark(run)


def test_get_market_orderbook(benchmark: object, bench_config, bench_ticker: str | None) -> None:
    if not bench_ticker:
        pytest.skip("no ticker from get_markets(limit=1)")

    def run() -> dict:
        return asyncio.run(_one_get_orderbook(bench_config, bench_ticker))

    benchmark(run)


def test_get_balance(benchmark: object, bench_config) -> None:
    if not getattr(bench_config, "auth_signer", None):
        pytest.skip("auth required: set KALSHI_ACCESS_KEY and KALSHI_PRIVATE_KEY or KALSHI_PRIVATE_KEY_PATH")
    try:
        asyncio.run(_one_get_balance(bench_config))
    except KyroHTTPError as e:
        if e.status in (401, 403):
            pytest.skip(f"Kalshi returned {e.status} (key may not be valid for this env)")

    def run() -> dict:
        return asyncio.run(_one_get_balance(bench_config))

    benchmark(run)


def test_get_orders(benchmark: object, bench_config) -> None:
    if not getattr(bench_config, "auth_signer", None):
        pytest.skip("auth required: set KALSHI_ACCESS_KEY and KALSHI_PRIVATE_KEY or KALSHI_PRIVATE_KEY_PATH")
    try:
        asyncio.run(_one_get_orders(bench_config))
    except KyroHTTPError as e:
        if e.status in (401, 403):
            pytest.skip(f"Kalshi returned {e.status} (key may not be valid for this env)")

    def run() -> dict:
        return asyncio.run(_one_get_orders(bench_config))

    benchmark(run)

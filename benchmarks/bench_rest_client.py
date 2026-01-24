"""Benchmarks for RestClient against a local mock Kalshi API.

Runs vs a mock server (benchmarks.mock_server) so results reflect client overhead
(parsing, serialization, client logic) instead of network/API variance. No auth
or live Kalshi credentials needed.

Run: pytest benchmarks/bench_rest_client.py -v --benchmark-only
"""

from __future__ import annotations

import asyncio

import pytest

from kyro import RestClient
from kyro.rest.api import events, exchange, markets, orders, portfolio


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
    def run() -> dict:
        return asyncio.run(_one_get_balance(bench_config))

    benchmark(run)


def test_get_orders(benchmark: object, bench_config) -> None:
    def run() -> dict:
        return asyncio.run(_one_get_orders(bench_config))

    benchmark(run)

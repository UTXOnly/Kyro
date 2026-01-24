"""Benchmarks for RestClient against a local mock Kalshi API.

Runs vs a mock server (benchmarks.mock_server). Each benchmark iteration does
N requests with a **single** RestClient (one event loop, one aiohttp session)
so the reported time reflects HTTP + parsing + client logic, not loop/session
create/teardown. No auth or live Kalshi credentials needed.

Run separately from serialization benchmarks (different scale: ms vs µs):

  pytest benchmarks/bench_rest_client.py -v --benchmark-only

Raw pytest-benchmark output:
  - Mean = time for N requests (one round), not one request.
  - OPS = rounds/sec = 1/Mean, not requests/sec.
  - Per-request (ms) = Mean / N (if Mean in ms) or Mean_ns / 1e6 / N.
  - Requests/sec = OPS * N.
"""

from __future__ import annotations

import asyncio

import pytest

from kyro import RestClient
from kyro.rest.api import events, exchange, markets, orders, portfolio

# Requests per benchmark iteration; shared client amortizes loop/session overhead.
REQUESTS_PER_ROUND = 100

def test_get_exchange_status(benchmark: object, bench_config) -> None:
    async def _run() -> None:
        async with RestClient(bench_config) as client:
            for _ in range(REQUESTS_PER_ROUND):
                await exchange.get_exchange_status(client)

    def run() -> None:
        asyncio.run(_run())

    benchmark(run)


def test_get_markets(benchmark: object, bench_config) -> None:
    async def _run() -> None:
        async with RestClient(bench_config) as client:
            for _ in range(REQUESTS_PER_ROUND):
                await markets.get_markets(client, limit=10)

    def run() -> None:
        asyncio.run(_run())

    benchmark(run)


def test_get_events(benchmark: object, bench_config) -> None:
    async def _run() -> None:
        async with RestClient(bench_config) as client:
            for _ in range(REQUESTS_PER_ROUND):
                await events.get_events(client, limit=10)

    def run() -> None:
        asyncio.run(_run())

    benchmark(run)


def test_get_market_orderbook(benchmark: object, bench_config, bench_ticker: str | None) -> None:
    if not bench_ticker:
        pytest.skip("no ticker from get_markets(limit=1)")

    async def _run() -> None:
        async with RestClient(bench_config) as client:
            for _ in range(REQUESTS_PER_ROUND):
                await markets.get_market_orderbook(client, bench_ticker, depth=5)

    def run() -> None:
        asyncio.run(_run())

    benchmark(run)


def test_get_balance(benchmark: object, bench_config) -> None:
    async def _run() -> None:
        async with RestClient(bench_config) as client:
            for _ in range(REQUESTS_PER_ROUND):
                await portfolio.get_balance(client)

    def run() -> None:
        asyncio.run(_run())

    benchmark(run)


def test_get_orders(benchmark: object, bench_config) -> None:
    async def _run() -> None:
        async with RestClient(bench_config) as client:
            for _ in range(REQUESTS_PER_ROUND):
                await orders.get_orders(client, limit=5)

    def run() -> None:
        asyncio.run(_run())

    benchmark(run)

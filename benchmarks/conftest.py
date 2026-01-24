"""Pytest fixtures for benchmarks: mock Kalshi server and config."""

from __future__ import annotations

import asyncio

import pytest

from benchmarks.mock_server import run_server_thread
from kyro import KyroConfig, RestClient
from kyro.rest.api import markets


@pytest.fixture
def bench_mock_base_url():
    """Base URL of a local mock Kalshi server run in a background thread."""
    url, stop, thread = run_server_thread(port=0)
    yield url
    stop.set()
    thread.join(timeout=2)


@pytest.fixture
def bench_config(bench_mock_base_url: str):
    """KyroConfig pointing at the local mock server for REST client benchmarks."""
    return KyroConfig(base_url=bench_mock_base_url)


@pytest.fixture
def bench_ticker(bench_config: KyroConfig):
    """A market ticker from get_markets(limit=1) for orderbook bench. None if none found."""

    async def _fetch():
        async with RestClient(bench_config) as client:
            out = await markets.get_markets(client, limit=1)
        lst = (out or {}).get("markets") or []
        return lst[0].get("ticker") if lst else None

    try:
        return asyncio.run(_fetch())
    except Exception:
        return None

"""Pytest fixtures for benchmarks: config and ticker from env / live API."""

from __future__ import annotations

import asyncio

import pytest

from kyro import RestClient, config_from_env
from kyro.rest.api import markets


@pytest.fixture
def bench_config():
    """KyroConfig from KALSHI_* env (demo by default). Use for live API benchmarks."""
    return config_from_env(default_demo=True)


@pytest.fixture
def bench_ticker(bench_config):
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

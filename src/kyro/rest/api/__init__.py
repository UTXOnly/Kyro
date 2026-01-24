"""Modular Kalshi API methods.

Maps to `https://docs.kalshi.com/api-reference/`. Each submodule exposes
async functions that take a :class:`kyro.rest.RestClient` as first argument.

Example:
    >>> from kyro import RestClient, KyroConfig
    >>> from kyro.rest.api import exchange, markets, portfolio
    >>> async with RestClient(KyroConfig()) as client:
    ...     status = await exchange.get_exchange_status(client)
    ...     ms = await markets.get_markets(client, limit=10)
    ...     bal = await portfolio.get_balance(client)
"""

from . import exchange, events, markets, orders, portfolio

__all__ = ["exchange", "events", "markets", "orders", "portfolio"]

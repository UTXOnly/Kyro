"""Modular Kalshi API. Pass a :class:`kyro.rest.RestClient` as the first argument.

Example:
    >>> from kyro import RestClient, KyroConfig
    >>> from kyro.rest import exchange, markets, events, orders, portfolio, search
    >>> async with RestClient(KyroConfig()) as client:
    ...     status = await exchange.get_exchange_status(client)
    ...     ms = await markets.get_markets(client, limit=10)
"""

from . import events, exchange, markets, orders, portfolio, search

__all__ = ["exchange", "events", "markets", "orders", "portfolio", "search"]

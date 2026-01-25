"""REST client and modular Kalshi API (exchange, markets, events, orders, portfolio, search)."""

from kyro.rest.api import events, exchange, markets, orders, portfolio, search
from kyro.rest.client import RestClient

__all__ = [
    "RestClient",
    "exchange",
    "events",
    "markets",
    "orders",
    "portfolio",
    "search",
]

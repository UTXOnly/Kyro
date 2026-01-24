"""Kyro — async Kalshi API client (aiohttp, orjson, Pydantic).

Library for building apps. REST client today; WebSocket support later.
"""

from kyro._config import KyroConfig
from kyro._version import __version__
from kyro.exceptions import (
    KyroError,
    KyroHTTPError,
    KyroConnectionError,
    KyroTimeoutError,
    KyroValidationError,
)
from kyro.rest import RestClient

__all__ = [
    "__version__",
    "KyroConfig",
    "KyroError",
    "KyroHTTPError",
    "KyroConnectionError",
    "KyroTimeoutError",
    "KyroValidationError",
    "RestClient",
]

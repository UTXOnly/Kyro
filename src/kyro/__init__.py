"""Kyro — async Kalshi API client (aiohttp, Pydantic).

Library for building apps. REST client today; WebSocket support later.
"""

from kyro._auth import config_from_env
from kyro._config import KyroConfig
from kyro._version import __version__
from kyro.exceptions import (
    KyroConnectionError,
    KyroError,
    KyroHTTPError,
    KyroTimeoutError,
    KyroValidationError,
)
from kyro.rest import RestClient

__all__ = [
    "__version__",
    "KyroConfig",
    "config_from_env",
    "KyroError",
    "KyroHTTPError",
    "KyroConnectionError",
    "KyroTimeoutError",
    "KyroValidationError",
    "RestClient",
]

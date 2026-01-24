"""Client configuration for Kyro (Kalshi API).

:class:`KyroConfig` holds base URL, timeouts, and optional auth. Reused by
the REST client and (later) WebSocket client.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class KyroConfig(BaseModel):
    """Configuration for the Kyro Kalshi client.

    Use this when constructing :class:`kyro.rest.RestClient` or (later) a
    WebSocket client. All fields have sensible defaults for the Kalshi API.

    Example:
        >>> from kyro import RestClient
        >>> from kyro._config import KyroConfig
        >>> cfg = KyroConfig(base_url="https://api.elections.kalshi.com/trade-api/v2")
        >>> async with RestClient(cfg) as client:
        ...     markets = await client.get("/markets")
    """

    base_url: HttpUrl = Field(
        default="https://api.elections.kalshi.com/trade-api/v2",
        description="Kalshi API base URL (production). Use https://demo-api.kalshi.co/trade-api/v2 for demo.",
    )
    request_timeout: float = Field(
        default=30.0,
        ge=0.1,
        le=300.0,
        description="Request timeout in seconds.",
    )
    connect_timeout: float = Field(
        default=10.0,
        ge=0.1,
        le=60.0,
        description="Connection establishment timeout in seconds.",
    )
    default_headers: dict[str, str] = Field(
        default_factory=dict,
        description="Headers sent with every request (e.g. Accept, User-Agent).",
    )
    auth_headers: dict[str, str] | None = Field(
        default=None,
        description="Optional Kalshi auth headers (KALSHI-ACCESS-KEY, etc.). "
        "Ignored when auth_signer is set. For request signing, use config_from_env() or auth_signer.",
    )
    auth_signer: Callable[[str, str, bytes | None], dict[str, str]] | None = Field(
        default=None,
        description="Optional (method, path, body) -> dict of Kalshi auth headers. "
        "When set, used per-request instead of auth_headers. See kyro.config_from_env().",
    )

    model_config = {"frozen": False, "extra": "forbid"}

    def model_post_init(self, __context: Any) -> None:
        if "Accept" not in self.default_headers:
            self.default_headers = {**self.default_headers, "Accept": "application/json"}

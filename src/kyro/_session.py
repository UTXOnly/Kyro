"""Base aiohttp session management for Kyro.

:class:`KyroSession` owns a single :class:`aiohttp.ClientSession` and applies
config (base URL, timeouts, headers). Reused by the REST client and (later)
WebSocket client. Use as an async context manager.
"""

from __future__ import annotations

import logging

import aiohttp

from kyro._config import KyroConfig
from kyro.exceptions import KyroConnectionError, KyroError, KyroTimeoutError

logger = logging.getLogger(__name__)


class KyroSession:
    """Manages a long-lived :class:`aiohttp.ClientSession` for Kyro.

    Use as an async context manager. The inner session is configured with
    base URL, timeouts, and default headers. Connection and timeout errors
    are wrapped as :exc:`KyroConnectionError` and :exc:`KyroTimeoutError`.
    The same session can be reused for REST and (later) WebSocket usage.

    Example:
        >>> cfg = KyroConfig()
        >>> async with KyroSession(cfg) as session:
        ...     async with session.get("/markets") as r:
        ...         data = await r.json()
    """

    def __init__(self, config: KyroConfig) -> None:
        self._config = config
        self._session: aiohttp.ClientSession | None = None

    @property
    def session(self) -> aiohttp.ClientSession:
        """The underlying :class:`aiohttp.ClientSession`. Valid only inside the context."""
        if self._session is None:
            raise KyroError("KyroSession used outside async context manager")
        return self._session

    async def __aenter__(self) -> KyroSession:
        timeout = aiohttp.ClientTimeout(
            total=self._config.request_timeout,
            connect=self._config.connect_timeout,
        )
        headers = {**self._config.default_headers}
        if self._config.auth_headers and not self._config.auth_signer:
            headers.update(self._config.auth_headers)
        base = str(self._config.base_url).rstrip("/") + "/"
        self._session = aiohttp.ClientSession(
            base_url=base,
            timeout=timeout,
            headers=headers,
        )
        await self._session.__aenter__()
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._session is not None:
            await self._session.__aexit__(*args)
            self._session = None

    def _wrap_client_error(self, err: Exception) -> KyroError:
        """Map aiohttp client errors to Kyro exceptions."""
        if isinstance(err, aiohttp.ServerTimeoutError):
            return KyroTimeoutError(
                str(err) or "Request timed out",
                timeout=getattr(err, "timeout", None) or self._config.request_timeout,
            )
        if isinstance(err, (aiohttp.ClientError, ConnectionError, OSError)):
            return KyroConnectionError(str(err))
        return KyroError(str(err))

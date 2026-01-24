"""Async REST client for the Kalshi API.

Uses aiohttp and Pydantic. Built for app integration (library, not CLI).
"""

from __future__ import annotations

import logging
from typing import Any, TypeVar
from urllib.parse import urlparse

import aiohttp
from pydantic import BaseModel

from kyro._config import KyroConfig
from kyro._serialization import dumps, loads, loads_model
from kyro._session import KyroSession
from kyro.exceptions import (
    KyroConnectionError,
    KyroError,
    KyroHTTPError,
    KyroTimeoutError,
    KyroValidationError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class RestClient:
    """Async Kalshi REST API client.

    Use as an async context manager. Wraps :class:`KyroSession` and provides
    :meth:`get`, :meth:`post`, :meth:`put`, :meth:`patch`, :meth:`delete` with
    Pydantic-based JSON serialization and Kyro exception handling.

    Example:
        >>> from kyro import RestClient
        >>> from kyro._config import KyroConfig
        >>> async with RestClient(KyroConfig()) as client:
        ...     data = await client.get("/markets")
        ...     # or: await client.get("/markets", response_model=MarketsResponse)
    """

    def __init__(self, config: KyroConfig | None = None) -> None:
        self._config = config or KyroConfig()
        self._session_mgr = KyroSession(self._config)
        self._session_mgr_entered = False

    async def __aenter__(self) -> RestClient:
        await self._session_mgr.__aenter__()
        self._session_mgr_entered = True
        return self

    async def __aexit__(self, *args: object) -> None:
        self._session_mgr_entered = False
        await self._session_mgr.__aexit__(*args)

    def _ensure_session(self) -> aiohttp.ClientSession:
        if not self._session_mgr_entered:
            raise KyroError("RestClient used outside async context manager")
        return self._session_mgr.session

    def _parse_error_body(self, raw: bytes) -> tuple[Any, str | None]:
        """Parse error response body; return (parsed, optional error_code)."""
        try:
            data = loads(raw)
        except KyroValidationError:
            return raw.decode("utf-8", errors="replace"), None
        if isinstance(data, dict):
            code = data.get("error", data.get("error_code", data.get("code")))
            if isinstance(code, str):
                return data, code
            return data, None
        return data, None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: BaseModel | dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
        response_model: type[T] | None = None,
    ) -> Any:
        session = self._ensure_session()
        # Use a relative path so aiohttp appends to base_url. A leading / would
        # replace the base path (RFC 3986) and drop /trade-api/v2.
        url = path.lstrip("/")
        extra_headers: dict[str, str] | None = None
        body: bytes | None = None
        if json is not None:
            try:
                body = dumps(json)
            except KyroValidationError:
                raise
            except Exception as e:
                raise KyroValidationError(f"Failed to serialize request body: {e}") from e
            extra_headers = {"Content-Type": "application/json"}

        if self._config.auth_signer:
            base_path = urlparse(str(self._config.base_url)).path.rstrip("/") or "/"
            full_path = f"{base_path}/{url}" if url else base_path
            ah = self._config.auth_signer(method, full_path, body)
            extra_headers = {**(extra_headers or {}), **ah}

        try:
            async with session.request(
                method,
                url,
                data=body,
                params=params,
                headers=extra_headers,
            ) as resp:
                raw = await resp.read()
                status = resp.status
        except aiohttp.ServerTimeoutError as e:
            raise KyroTimeoutError(
                str(e) or "Request timed out",
                timeout=getattr(e, "timeout", None) or self._config.request_timeout,
            ) from e
        except TimeoutError as e:
            # aiohttp can raise asyncio.TimeoutError (TimeoutError) on total timeout
            raise KyroTimeoutError(
                str(e) or "Request timed out",
                timeout=self._config.request_timeout,
            ) from e
        except (aiohttp.ClientError, ConnectionError, OSError) as e:
            raise KyroConnectionError(str(e)) from e

        if status >= 400:
            parsed, err_code = self._parse_error_body(raw)
            raise KyroHTTPError(
                "Kalshi API error", status=status, response_body=parsed, error_code=err_code
            )

        if not raw:
            return None

        if response_model is not None:
            return loads_model(raw, response_model)
        return loads(raw)

    async def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        response_model: type[T] | None = None,
    ) -> Any:
        """GET ``path``. Optional ``params``, optional ``response_model`` for validation."""
        return await self._request("GET", path, params=params, response_model=response_model)

    async def post(
        self,
        path: str,
        *,
        json: BaseModel | dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
        response_model: type[T] | None = None,
    ) -> Any:
        """POST ``path`` with optional JSON body and ``response_model``."""
        return await self._request(
            "POST", path, json=json, params=params, response_model=response_model
        )

    async def put(
        self,
        path: str,
        *,
        json: BaseModel | dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
        response_model: type[T] | None = None,
    ) -> Any:
        """PUT ``path`` with optional JSON body and ``response_model``."""
        return await self._request(
            "PUT", path, json=json, params=params, response_model=response_model
        )

    async def patch(
        self,
        path: str,
        *,
        json: BaseModel | dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
        response_model: type[T] | None = None,
    ) -> Any:
        """PATCH ``path`` with optional JSON body and ``response_model``."""
        return await self._request(
            "PATCH", path, json=json, params=params, response_model=response_model
        )

    async def delete(
        self,
        path: str,
        *,
        json: BaseModel | dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
        response_model: type[T] | None = None,
    ) -> Any:
        """DELETE ``path``. Optional ``json`` body, ``params``, ``response_model``."""
        return await self._request(
            "DELETE", path, json=json, params=params, response_model=response_model
        )

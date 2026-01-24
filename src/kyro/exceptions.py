"""Kyro exception hierarchy and Kalshi API error handling.

All Kyro-specific errors inherit from :exc:`KyroError`. Use these in your app's
exception handling (e.g. ``except KyroHTTPError``) when integrating the client.
"""

from __future__ import annotations

from typing import Any


class KyroError(Exception):
    """Base exception for all Kyro (Kalshi client) errors.

    Catch this to handle any Kyro-related failure. More specific subtypes
    exist for HTTP, connection, timeout, and validation errors.
    """

    def __init__(self, message: str, *args: object, **kwargs: Any) -> None:
        super().__init__(message, *args)
        self._message = message

    @property
    def message(self) -> str:
        """Human-readable error message."""
        return self._message


class KyroHTTPError(KyroError):
    """Raised when the Kalshi API returns an error HTTP status (4xx/5xx).

    Attributes:
        status: HTTP status code (e.g. 400, 401, 404, 500).
        response_body: Raw response body, if available (bytes or decoded str).
        error_code: Optional API-level error code from Kalshi response.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int,
        response_body: bytes | str | None = None,
        error_code: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.status = status
        self.response_body = response_body
        self.error_code = error_code


class KyroConnectionError(KyroError):
    """Raised when a network/connection error occurs (DNS, connection refused, etc.)."""

    pass


class KyroTimeoutError(KyroError):
    """Raised when a request times out.

    Attributes:
        timeout: The timeout value that was exceeded (seconds), if known.
    """

    def __init__(self, message: str, *args: object, timeout: float | None = None, **kwargs: Any) -> None:
        super().__init__(message, *args, **kwargs)
        self.timeout = timeout


class KyroValidationError(KyroError):
    """Raised when request/response validation fails (e.g. Pydantic schema mismatch).

    Attributes:
        details: Validation details; often a list of Pydantic ``ErrorDetail``-like dicts.
    """

    def __init__(self, message: str, *args: object, details: Any = None, **kwargs: Any) -> None:
        super().__init__(message, *args, **kwargs)
        self.details = details

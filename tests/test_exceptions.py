"""Tests for Kyro exception types."""

from __future__ import annotations

from kyro.exceptions import (
    KyroConnectionError,
    KyroError,
    KyroHTTPError,
    KyroTimeoutError,
    KyroValidationError,
)


def test_kyro_error_message() -> None:
    err = KyroError("something failed")
    assert str(err) == "something failed"
    assert err.message == "something failed"


def test_kyro_http_error_attrs() -> None:
    err = KyroHTTPError(
        "bad",
        status=400,
        response_body={"error": "BadRequest"},
        error_code="BadRequest",
    )
    assert err.status == 400
    assert err.response_body == {"error": "BadRequest"}
    assert err.error_code == "BadRequest"


def test_kyro_http_error_no_error_code() -> None:
    err = KyroHTTPError("bad", status=500, response_body=b"Internal error")
    assert err.status == 500
    assert err.error_code is None


def test_kyro_http_error_str_includes_status_error_code_response_body() -> None:
    """str(e) must include status, error_code, and response_body so tracebacks are useful."""
    err = KyroHTTPError(
        "Kalshi API error",
        status=404,
        response_body={"code": "MarketNotFound"},
        error_code="MarketNotFound",
    )
    s = str(err)
    assert "status=404" in s
    assert "error_code=" in s
    assert "MarketNotFound" in s
    assert "response_body=" in s


def test_kyro_connection_error() -> None:
    err = KyroConnectionError("Connection refused")
    assert isinstance(err, KyroError)
    assert "Connection refused" in str(err)


def test_kyro_timeout_error() -> None:
    err = KyroTimeoutError("Timed out", timeout=5.0)
    assert isinstance(err, KyroError)
    assert err.timeout == 5.0
    assert "Timed out" in str(err)


def test_kyro_timeout_error_no_timeout() -> None:
    err = KyroTimeoutError("Timed out")
    assert err.timeout is None


def test_kyro_validation_error() -> None:
    details = [{"type": "missing", "loc": ("ticker",)}]
    err = KyroValidationError("Validation failed", details=details)
    assert isinstance(err, KyroError)
    assert err.details == details
    assert "Validation failed" in str(err)


def test_kyro_validation_error_no_details() -> None:
    err = KyroValidationError("Invalid JSON")
    assert err.details is None

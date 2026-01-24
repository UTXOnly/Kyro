"""Tests for KyroConfig."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from kyro import KyroConfig


def test_config_defaults() -> None:
    cfg = KyroConfig()
    assert str(cfg.base_url) == "https://api.elections.kalshi.com/trade-api/v2"
    assert cfg.request_timeout == 30.0
    assert cfg.connect_timeout == 10.0
    assert cfg.default_headers.get("Accept") == "application/json"
    assert cfg.auth_headers is None


def test_config_custom_headers() -> None:
    cfg = KyroConfig(default_headers={"Accept": "application/xml", "X-Foo": "bar"})
    assert cfg.default_headers["Accept"] == "application/xml"
    assert cfg.default_headers["X-Foo"] == "bar"


def test_config_base_url_override() -> None:
    cfg = KyroConfig(base_url="https://demo-api.kalshi.com/v2")
    assert str(cfg.base_url) == "https://demo-api.kalshi.com/v2"


def test_config_adds_accept_if_missing() -> None:
    cfg = KyroConfig(default_headers={"User-Agent": "Kyro/1.0"})
    assert cfg.default_headers["Accept"] == "application/json"
    assert cfg.default_headers["User-Agent"] == "Kyro/1.0"


def test_config_keeps_accept_if_provided() -> None:
    cfg = KyroConfig(default_headers={"Accept": "application/vnd.kalshi.v1+json"})
    assert cfg.default_headers["Accept"] == "application/vnd.kalshi.v1+json"


def test_config_request_timeout_bounds() -> None:
    KyroConfig(request_timeout=0.1)
    KyroConfig(request_timeout=300.0)
    with pytest.raises(ValidationError):
        KyroConfig(request_timeout=0.05)
    with pytest.raises(ValidationError):
        KyroConfig(request_timeout=301.0)


def test_config_connect_timeout_bounds() -> None:
    KyroConfig(connect_timeout=0.1)
    KyroConfig(connect_timeout=60.0)
    with pytest.raises(ValidationError):
        KyroConfig(connect_timeout=0.05)
    with pytest.raises(ValidationError):
        KyroConfig(connect_timeout=61.0)


def test_config_auth_headers() -> None:
    cfg = KyroConfig(auth_headers={"KALSHI-ACCESS-KEY": "key", "KALSHI-ACCESS-SECRET": "secret"})
    assert cfg.auth_headers is not None
    assert cfg.auth_headers["KALSHI-ACCESS-KEY"] == "key"
    assert cfg.auth_headers["KALSHI-ACCESS-SECRET"] == "secret"

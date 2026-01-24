"""Benchmarks for kyro serialization: dumps, loads, loads_model."""

from __future__ import annotations

from pydantic import BaseModel

from kyro._serialization import dumps, loads, loads_model


# --- Data ---

_MEDIUM: bytes = dumps({
    "markets": [{"ticker": f"KXBTC-{i:02d}"} for i in range(50)],
    "cursor": "",
})


class _SmallModel(BaseModel):
    ticker: str
    yes_price: int
    no_price: int


class _NestedModel(BaseModel):
    markets: list[dict]
    cursor: str


# --- Benchmarks ---


def test_dumps_dict(benchmark: object) -> None:
    obj = {"ticker": "KXBTC", "yes_price": 50, "no_price": 50}
    benchmark(dumps, obj)


def test_dumps_pydantic(benchmark: object) -> None:
    obj = _SmallModel(ticker="KXBTC", yes_price=50, no_price=50)
    benchmark(dumps, obj)


def test_loads_small(benchmark: object) -> None:
    raw = b'{"ticker":"KXBTC","yes_price":50,"no_price":50}'
    benchmark(loads, raw)


def test_loads_medium(benchmark: object) -> None:
    raw = _MEDIUM
    benchmark(loads, raw)


def test_loads_model_small(benchmark: object) -> None:
    raw = b'{"ticker":"KXBTC","yes_price":50,"no_price":50}'
    benchmark(loads_model, raw, _SmallModel)


def test_loads_model_nested(benchmark: object) -> None:
    raw = _MEDIUM
    benchmark(loads_model, raw, _NestedModel)

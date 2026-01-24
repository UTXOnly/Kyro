"""Tests for JSON serialization and deserialization."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from kyro._serialization import dumps, loads, loads_model
from kyro.exceptions import KyroValidationError


class _Payload(BaseModel):
    ticker: str
    count: int = 0


def test_dumps_dict() -> None:
    assert dumps({"a": 1}) == b'{"a":1}'


def test_dumps_model() -> None:
    assert dumps(_Payload(ticker="KXBTC", count=2)) == b'{"ticker":"KXBTC","count":2}'


def test_dumps_list() -> None:
    assert dumps([1, 2, "x"]) == b'[1,2,"x"]'


def test_dumps_nested() -> None:
    assert dumps({"a": [1, {"b": 2}]}) == b'{"a":[1,{"b":2}]}'


def test_dumps_nonserializable_raises() -> None:
    with pytest.raises(KyroValidationError) as exc_info:
        dumps({"x": object()})  # not JSON-serializable
    assert "serialize" in str(exc_info.value).lower() or "Failed" in str(exc_info.value)


def test_loads_bytes() -> None:
    assert loads(b'{"a":1}') == {"a": 1}


def test_loads_str() -> None:
    assert loads('{"a":1}') == {"a": 1}


def test_loads_empty_object() -> None:
    assert loads(b"{}") == {}


def test_loads_empty_array() -> None:
    assert loads(b"[]") == []


def test_loads_unicode() -> None:
    data = loads(b'{"x":"\xc3\xa9"}')
    assert data["x"] == "é"


def test_loads_invalid_raises() -> None:
    with pytest.raises(KyroValidationError) as exc_info:
        loads(b"not json")
    assert "Invalid JSON" in str(exc_info.value)


def test_loads_model() -> None:
    m = loads_model(b'{"ticker":"KXBTC","count":1}', _Payload)
    assert m.ticker == "KXBTC"
    assert m.count == 1


def test_loads_model_from_str() -> None:
    m = loads_model('{"ticker":"X","count":0}', _Payload)
    assert m.ticker == "X"
    assert m.count == 0


def test_loads_model_extra_fields_ignored() -> None:
    m = loads_model(b'{"ticker":"KXBTC","count":1,"extra":"ignored"}', _Payload)
    assert m.ticker == "KXBTC"
    assert m.count == 1
    assert not hasattr(m, "extra")


def test_loads_model_invalid_type_raises() -> None:
    with pytest.raises(KyroValidationError) as exc_info:
        loads_model(b'{"ticker":123}', _Payload)
    assert "Validation failed" in str(exc_info.value)
    assert exc_info.value.details is not None


def test_loads_model_missing_required_raises() -> None:
    with pytest.raises(KyroValidationError) as exc_info:
        loads_model(b'{"count":1}', _Payload)
    assert "Validation failed" in str(exc_info.value)
    assert exc_info.value.details is not None


def test_loads_model_invalid_json_raises() -> None:
    with pytest.raises(KyroValidationError) as exc_info:
        loads_model(b"not json", _Payload)
    assert "Validation failed" in str(exc_info.value) or "Invalid" in str(exc_info.value)

"""JSON serialization and deserialization via orjson and Pydantic.

Used by the REST client for request bodies and response parsing. Supports
raw dicts, Pydantic models, and optional validation into a response type.
"""

from __future__ import annotations

from typing import Any, TypeVar

import orjson
from pydantic import BaseModel, ValidationError

from kyro.exceptions import KyroValidationError

T = TypeVar("T", bound=BaseModel)


def dumps(obj: BaseModel | dict[str, Any] | list[Any]) -> bytes:
    """Serialize to JSON bytes using orjson.

    Args:
        obj: A Pydantic model (uses :meth:`~pydantic.BaseModel.model_dump`),
            or a dict/list (passed through to orjson).

    Returns:
        JSON as bytes, UTF-8 encoded.

    Example:
        >>> from pydantic import BaseModel
        >>> class Payload(BaseModel): x: int
        >>> dumps(Payload(x=1))
        b'{"x":1}'
        >>> dumps({"a": 1})
        b'{"a":1}'
    """
    if isinstance(obj, BaseModel):
        data = obj.model_dump(mode="json", exclude_none=False)
        return orjson.dumps(data)
    return orjson.dumps(obj)


def loads(raw: bytes | str) -> Any:
    """Deserialize JSON bytes or string to Python objects using orjson.

    Args:
        raw: JSON as bytes or str.

    Returns:
        Parsed structure (dict, list, etc.). No Pydantic validation.

    Raises:
        KyroValidationError: If orjson fails to parse (invalid JSON).

    Example:
        >>> loads(b'{"a": 1}')
        {'a': 1}
    """
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    try:
        return orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        raise KyroValidationError(f"Invalid JSON: {e}") from e


def loads_model(raw: bytes | str, model: type[T]) -> T:
    """Deserialize JSON into a Pydantic model.

    Args:
        raw: JSON as bytes or str.
        model: Pydantic model class to validate into.

    Returns:
        Validated instance of ``model``.

    Raises:
        KyroValidationError: If JSON is invalid or validation fails.

    Example:
        >>> class Market(BaseModel): ticker: str
        >>> loads_model(b'{"ticker": "KXBTC"}', Market)
        Market(ticker='KXBTC')
    """
    data = loads(raw)
    try:
        return model.model_validate(data)
    except ValidationError as e:
        raise KyroValidationError(
            f"Validation failed for {model.__name__}: {e}",
            details=e.errors(),
        ) from e

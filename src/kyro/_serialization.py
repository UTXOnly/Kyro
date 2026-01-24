"""JSON serialization and deserialization via Pydantic only.

All parsing and serialization goes through Pydantic (no orjson or stdlib json):

- **dumps**: request bodies. BaseModel → model_dump_json; dict/list → TypeAdapter.dump_json.
- **loads**: raw JSON → dict | list via TypeAdapter. Used when response_model is not
  set (e.g. error bodies, or until a response model exists). Prefer loads_model when
  a model exists.
- **loads_model**: response → Pydantic model via model_validate_json (one parse).
  Preferred for API responses; map payloads to models.
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, TypeAdapter, ValidationError

from kyro.exceptions import KyroValidationError

T = TypeVar("T", bound=BaseModel)

# For raw dict/list in/out when no model exists (error bodies, generic payloads).
_AnyJson = TypeAdapter(dict[str, Any] | list[Any])
_DictJson = TypeAdapter(dict[str, Any])
_ListJson = TypeAdapter(list[Any])


def dumps(obj: BaseModel | dict[str, Any] | list[Any]) -> bytes:
    """Serialize to JSON bytes using Pydantic.

    BaseModel → model_dump_json; dict/list → TypeAdapter.dump_json.

    Args:
        obj: Pydantic model, or dict/list (e.g. request body before a model exists).

    Returns:
        JSON as bytes, UTF-8.

    Raises:
        KyroValidationError: If a value is not JSON-serializable (e.g. set, object()).

    Example:
        >>> from pydantic import BaseModel
        >>> class Payload(BaseModel): x: int
        >>> dumps(Payload(x=1))
        b'{"x":1}'
        >>> dumps({"a": 1})
        b'{"a":1}'
    """
    try:
        if isinstance(obj, BaseModel):
            return obj.model_dump_json(exclude_none=False).encode("utf-8")
        if isinstance(obj, dict):
            return _DictJson.dump_json(obj)
        if isinstance(obj, list):
            return _ListJson.dump_json(obj)
    except KyroValidationError:
        raise
    except Exception as e:
        raise KyroValidationError(f"Failed to serialize: {e}") from e
    raise TypeError("dumps requires BaseModel, dict, or list")


def loads(raw: bytes | str) -> dict[str, Any] | list[Any]:
    """Deserialize JSON to dict or list via Pydantic TypeAdapter.

    Use for error bodies or when no response model exists yet. Prefer
    loads_model with a concrete model for API responses.

    Args:
        raw: JSON as bytes or str.

    Returns:
        Top-level dict or list.

    Raises:
        KyroValidationError: Invalid JSON or top-level not dict/list.
    """
    try:
        return _AnyJson.validate_json(raw)
    except ValidationError as e:
        raise KyroValidationError(f"Invalid JSON: {e}") from e


def loads_model(raw: bytes | str, model: type[T]) -> T:
    """Deserialize JSON into a Pydantic model via model_validate_json.

    Uses Pydantic's direct JSON validation (one parse, no intermediate dict).
    Accepts str or bytes.

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
    try:
        return model.model_validate_json(raw)
    except ValidationError as e:
        raise KyroValidationError(
            f"Validation failed for {model.__name__}: {e}",
            details=e.errors(),
        ) from e

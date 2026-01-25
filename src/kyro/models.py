"""Type-safe models and enums aligned with the Kalshi OpenAPI spec.

Use these for validation and IDE support. The API modules validate request
bodies and raise :exc:`KyroValidationError` when values are invalid.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


# --- Enums (str-valued for JSON and API compatibility) ---


class Side(str, Enum):
    """Order side. Use in create_order, amend_order."""

    YES = "yes"
    NO = "no"


class Action(str, Enum):
    """Order action. Use in create_order, amend_order."""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type."""

    LIMIT = "limit"
    MARKET = "market"


class TimeInForce(str, Enum):
    """Order time-in-force."""

    FILL_OR_KILL = "fill_or_kill"
    GOOD_TILL_CANCELED = "good_till_canceled"
    IMMEDIATE_OR_CANCEL = "immediate_or_cancel"


class OrderStatus(str, Enum):
    """Order status filter for get_orders."""

    RESTING = "resting"
    CANCELED = "canceled"
    EXECUTED = "executed"


class MarketStatus(str, Enum):
    """Market status filter."""

    UNOPENED = "unopened"
    OPEN = "open"
    PAUSED = "paused"
    CLOSED = "closed"
    SETTLED = "settled"


class PeriodInterval(int, Enum):
    """Candlestick period in minutes. Use in get_market_candlesticks, get_event_candlesticks."""

    ONE_MIN = 1
    ONE_HOUR = 60
    ONE_DAY = 1440


class SelfTradePreventionType(str, Enum):
    """Self-trade prevention for orders."""

    TAKER_AT_CROSS = "taker_at_cross"
    MAKER = "maker"


# --- Request models (validated before sending) ---


class CreateOrderRequest(BaseModel):
    """Create order body. Required: ticker, side, action. Validated per OpenAPI."""

    model_config = ConfigDict(extra="allow")

    ticker: str = Field(..., min_length=1)
    side: str = Field(..., pattern="^(yes|no)$")
    action: str = Field(..., pattern="^(buy|sell)$")
    count: int | None = Field(None, ge=1)
    count_fp: str | None = None
    type: str | None = Field(None, pattern="^(limit|market)$")
    yes_price: int | None = Field(None, ge=1, le=99)
    no_price: int | None = Field(None, ge=1, le=99)
    yes_price_dollars: str | None = None
    no_price_dollars: str | None = None
    client_order_id: str | None = None
    expiration_ts: int | None = None
    time_in_force: str | None = Field(
        None, pattern="^(fill_or_kill|good_till_canceled|immediate_or_cancel)$"
    )
    buy_max_cost: int | None = None
    post_only: bool | None = None
    reduce_only: bool | None = None
    sell_position_floor: int | None = None
    self_trade_prevention_type: str | None = Field(
        None, pattern="^(taker_at_cross|maker)$"
    )
    order_group_id: str | None = None
    cancel_order_on_pause: bool | None = None
    subaccount: int | None = Field(None, ge=0)


class AmendOrderRequest(BaseModel):
    """Amend order body. Required: ticker, side, action. Validated per OpenAPI."""

    model_config = ConfigDict(extra="allow")

    ticker: str
    side: str = Field(..., pattern="^(yes|no)$")
    action: str = Field(..., pattern="^(buy|sell)$")
    yes_price: int | None = Field(None, ge=1, le=99)
    no_price: int | None = Field(None, ge=1, le=99)
    yes_price_dollars: str | None = None
    no_price_dollars: str | None = None
    count: int | None = Field(None, ge=1)
    count_fp: str | None = None
    client_order_id: str | None = None
    updated_client_order_id: str | None = None
    expiration_ts: int | None = None


class DecreaseOrderRequest(BaseModel):
    """Decrease order body. Exactly one of (reduce_by|reduce_by_fp) or (reduce_to|reduce_to_fp)."""

    model_config = ConfigDict(extra="forbid")

    reduce_by: int | None = Field(None, ge=1)
    reduce_by_fp: str | None = None
    reduce_to: int | None = Field(None, ge=0)
    reduce_to_fp: str | None = None

    @model_validator(mode="after")
    def check_exactly_one_group(self) -> "DecreaseOrderRequest":
        reduce_by_any = self.reduce_by is not None or self.reduce_by_fp is not None
        reduce_to_any = self.reduce_to is not None or self.reduce_to_fp is not None
        if reduce_by_any and reduce_to_any:
            raise ValueError("Provide (reduce_by or reduce_by_fp) OR (reduce_to or reduce_to_fp), not both")
        if not reduce_by_any and not reduce_to_any:
            raise ValueError("Provide (reduce_by or reduce_by_fp) or (reduce_to or reduce_to_fp)")
        return self


class ApplySubaccountTransferRequest(BaseModel):
    """Transfer between subaccounts. Required: client_transfer_id, from_subaccount, to_subaccount, amount_cents."""

    client_transfer_id: str = Field(..., min_length=1)
    from_subaccount: int = Field(..., ge=0, le=32)
    to_subaccount: int = Field(..., ge=0, le=32)
    amount_cents: int


# --- Error response (for parsing 4xx/5xx bodies) ---


class ErrorResponse(BaseModel):
    """Kalshi error body. code and message are common; details and service may be absent."""

    model_config = ConfigDict(extra="ignore")

    code: str | None = None
    message: str | None = None
    details: str | None = None
    service: str | None = None

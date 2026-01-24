# Kyro API Reference

Request/response documentation for every modular method: **exchange**, **markets**, **events**, **orders**, **portfolio**.

- **Import:** `from kyro.rest import exchange, markets, events, orders, portfolio`
- **Client:** Pass `RestClient` as the first argument: `await exchange.get_exchange_status(client)`
- **Base path:** `{KyroConfig.base_url}` (e.g. `https://api.elections.kalshi.com/trade-api/v2`)
- **Auth:** Endpoints marked *Auth required* need `KyroConfig(auth_headers={...})` with KALSHI-ACCESS-KEY, TIMESTAMP, SIGNATURE.

---

## Exchange

No auth unless noted.

---

### `get_exchange_status`

**HTTP:** `GET /exchange/status`  
**Auth:** No

**Usage:**
```python
data = await exchange.get_exchange_status(client)
```

**Response (200):**
```json
{
  "exchange_active": true,
  "trading_active": true,
  "exchange_estimated_resume_time": "2025-01-15T05:31:56Z"
}
```

---

### `get_exchange_announcements`

**HTTP:** `GET /exchange/announcements`  
**Auth:** No

**Usage:**
```python
data = await exchange.get_exchange_announcements(client)
```

**Response (200):** `{ "announcements": [...] }` (structure per Kalshi)

---

### `get_exchange_schedule`

**HTTP:** `GET /exchange/schedule`  
**Auth:** No

**Usage:**
```python
data = await exchange.get_exchange_schedule(client)
```

**Response (200):** schedule object(s) per Kalshi

---

### `get_series_fee_changes`

**HTTP:** `GET /series/fee_changes`  
**Auth:** No

**Usage:**
```python
data = await exchange.get_series_fee_changes(client)
# optional: series_ticker=, show_historical=
```

**Query:** `series_ticker`, `show_historical` (default false).

**Response (200):** `{ "series_fee_change_arr": [...] }` per Kalshi

---

### `get_user_data_timestamp`

**HTTP:** `GET /exchange/user-data-timestamp`  
**Auth:** Yes

**Usage:**
```python
data = await exchange.get_user_data_timestamp(client)
```

**Response (200):** `{ "timestamp": 1704067200 }` or similar

---

## Markets

---

### `get_markets`

**HTTP:** `GET /markets`  
**Auth:** No

**Usage:**
```python
data = await markets.get_markets(
    client,
    limit=10,
    cursor=None,
    event_ticker=None,
    series_ticker=None,
    status="open",
    tickers=None,
    min_created_ts=None,
    max_created_ts=None,
    min_updated_ts=None,
    min_close_ts=None,
    max_close_ts=None,
    min_settled_ts=None,
    max_settled_ts=None,
    mve_filter=None,
)
```

**Query parameters**

| Parameter        | Type | Description                                      |
|-----------------|------|--------------------------------------------------|
| `limit`         | int  | Per page (1–1000)                                |
| `cursor`        | str  | Pagination cursor                                |
| `event_ticker`  | str  | Filter by event ticker                           |
| `series_ticker` | str  | Filter by series ticker                          |
| `status`        | str  | `unopened`, `open`, `paused`, `closed`, `settled`|
| `tickers`       | str  | Comma-separated market tickers                   |
| `min_created_ts`| int  | Min created (Unix)                               |
| `max_created_ts`| int  | Max created (Unix)                               |
| `min_updated_ts`| int  | Min updated (Unix)                               |
| `min_close_ts`  | int  | Min close (Unix)                                 |
| `max_close_ts`  | int  | Max close (Unix)                                 |
| `min_settled_ts`| int  | Min settled (Unix)                               |
| `max_settled_ts`| int  | Max settled (Unix)                               |
| `mve_filter`    | str  | `only` or `exclude` (multivariate)               |

**Response (200):**
```json
{
  "markets": [
    {
      "ticker": "KXBTC-24JAN15",
      "event_ticker": "KXBTC",
      "market_type": "binary",
      "title": "Will Bitcoin close above $100,000 on Jan 15?",
      "status": "open",
      "yes_bid": 45,
      "yes_ask": 47,
      "no_bid": 53,
      "no_ask": 55,
      "last_price": 46,
      "volume": 125000,
      "volume_24h": 12000,
      "open_interest": 50000,
      "liquidity": 25000,
      "open_time": "2024-01-01T00:00:00Z",
      "close_time": "2025-01-15T23:59:59Z",
      "expiration_time": "2025-01-15T23:59:59Z",
      "yes_bid_dollars": "0.4500",
      "yes_ask_dollars": "0.4700",
      "last_price_dollars": "0.4600"
    }
  ],
  "cursor": "eyJ..."
}
```

---

### `get_market`

**HTTP:** `GET /markets/{ticker}`  
**Auth:** No

**Usage:**
```python
data = await markets.get_market(client, "KXBTC-24JAN15")
```

**Response (200):**
```json
{
  "market": {
    "ticker": "KXBTC-24JAN15",
    "event_ticker": "KXBTC",
    "market_type": "binary",
    "title": "Will Bitcoin close above $100,000 on Jan 15?",
    "subtitle": "Bitcoin price",
    "yes_sub_title": "Yes",
    "no_sub_title": "No",
    "status": "open",
    "yes_bid": 45,
    "yes_ask": 47,
    "no_bid": 53,
    "no_ask": 55,
    "last_price": 46,
    "volume": 125000,
    "volume_24h": 12000,
    "open_interest": 50000,
    "liquidity": 25000,
    "tick_size": 1,
    "open_time": "2024-01-01T00:00:00Z",
    "close_time": "2025-01-15T23:59:59Z",
    "expiration_time": "2025-01-15T23:59:59Z",
    "created_time": "2024-01-01T00:00:00Z",
    "updated_time": "2025-01-10T12:00:00Z"
  }
}
```

---

### `get_market_orderbook`

**HTTP:** `GET /markets/{ticker}/orderbook`  
**Auth:** No

Yes and no bids only (yes bid at X ≡ no ask at 100−X).

**Usage:**
```python
data = await markets.get_market_orderbook(client, "KXBTC-24JAN15", depth=10)
```

**Query parameters**

| Parameter | Type | Description                    |
|-----------|------|--------------------------------|
| `depth`   | int  | 0 = all levels; 1–100 = depth  |

**Response (200):**
```json
{
  "orderbook": {
    "yes": [[45, 100], [44, 200], [43, 150]],
    "no": [[55, 80], [56, 120], [57, 90]],
    "yes_dollars": [["0.4500", 100], ["0.4400", 200]],
    "no_dollars": [["0.5500", 80], ["0.5600", 120]]
  },
  "orderbook_fp": {
    "yes_dollars": [["0.4500", "100.00"], ["0.4400", "200.00"]],
    "no_dollars": [["0.5500", "80.00"], ["0.5600", "120.00"]]
  }
}
```

---

### `get_trades`

**HTTP:** `GET /markets/trades`  
**Auth:** No

**Usage:**
```python
data = await markets.get_trades(
    client,
    limit=100,
    cursor=None,
    ticker="KXBTC-24JAN15",
    min_ts=1704067200,
    max_ts=1704153600,
)
```

**Query parameters**

| Parameter | Type | Description             |
|-----------|------|-------------------------|
| `limit`   | int  | Per page (1–1000)       |
| `cursor`  | str  | Pagination cursor       |
| `ticker`  | str  | Filter by market ticker |
| `min_ts`  | int  | Min created (Unix)      |
| `max_ts`  | int  | Max created (Unix)      |

**Response (200):**
```json
{
  "trades": [
    {
      "trade_id": "a1b2c3d4-...",
      "ticker": "KXBTC-24JAN15",
      "price": 46,
      "count": 10,
      "count_fp": "10.00",
      "yes_price": 46,
      "no_price": 54,
      "yes_price_dollars": "0.4600",
      "no_price_dollars": "0.5400",
      "taker_side": "yes",
      "created_time": "2025-01-10T14:30:00Z"
    }
  ],
  "cursor": "eyJ..."
}
```

---

### `get_market_candlesticks`

**HTTP:** `GET /series/{series_ticker}/markets/{ticker}/candlesticks`  
**Auth:** No

**Usage:**
```python
data = await markets.get_market_candlesticks(
    client,
    "KXBTC-24JAN15",
    series_ticker="KXBTC",
    start_ts=1704067200,
    end_ts=1704153600,
    period_interval=60,
    limit=24,
)
```

**Required:** `series_ticker`. If `start_ts`/`end_ts` omitted, uses last 24h.

**Query:** `start_ts`, `end_ts` (Unix), `period_interval` (1|60|1440 minutes), `limit`, `include_latest_before_start`

**Response (200):**
```json
{
  "candlesticks": [
    {
      "start_ts": 1704067200,
      "end_ts": 1704070800,
      "open": 45,
      "high": 47,
      "low": 44,
      "close": 46,
      "volume": 5000
    }
  ]
}
```

---

### `get_series`

**HTTP:** `GET /series/{series_ticker}`  
**Auth:** No

**Usage:**
```python
data = await markets.get_series(client, "KXBTC")
```

**Response (200):**
```json
{
  "series": {
    "ticker": "KXBTC",
    "title": "Bitcoin",
    "category": "Crypto"
  }
}
```

---

### `get_series_list`

**HTTP:** `GET /series`  
**Auth:** No

**Usage:**
```python
data = await markets.get_series_list(client, limit=20, cursor=None)
```

**Query parameters**

| Parameter | Type | Description       |
|-----------|------|-------------------|
| `limit`   | int  | Per page          |
| `cursor`  | str  | Pagination cursor |

**Response (200):**
```json
{
  "series": [
    { "ticker": "KXBTC", "title": "Bitcoin", "category": "Crypto" }
  ],
  "cursor": "eyJ..."
}
```

---

### `get_live_data`

**HTTP:** `GET /live-data?ticker={ticker}`  
**Auth:** No

**Usage:**
```python
data = await markets.get_live_data(client, "KXBTC-24JAN15")
```

**Response (200):** current yes/no bid/ask, last price, volume, etc. (structure per Kalshi)

---

### `get_multiple_live_data`

**HTTP:** `GET /live-data?tickers={ticker1},{ticker2},...`  
**Auth:** No

**Usage:**
```python
data = await markets.get_multiple_live_data(client, "KXBTC-24JAN15,KXETH-24JAN15")
```

**Response (200):** live data per ticker (array or map per Kalshi)

---

## Events

---

### `get_events`

**HTTP:** `GET /events`  
**Auth:** No

Excludes multivariate; use `get_multivariate_events` for those.

**Usage:**
```python
data = await events.get_events(
    client,
    limit=200,
    cursor=None,
    with_nested_markets=None,
    with_milestones=None,
    status="open",
    series_ticker=None,
    min_close_ts=None,
)
```

**Query parameters**

| Parameter             | Type  | Description                          |
|-----------------------|-------|--------------------------------------|
| `limit`               | int   | Per page (1–200)                     |
| `cursor`              | str   | Pagination cursor                    |
| `with_nested_markets` | bool  | Include nested market objects        |
| `with_milestones`     | bool  | Include related milestones           |
| `status`              | str   | `open`, `closed`, `settled`          |
| `series_ticker`       | str   | Filter by series                     |
| `min_close_ts`        | int   | Min close (Unix)                     |

**Response (200):**
```json
{
  "events": [
    {
      "event_ticker": "KXBTC",
      "series_ticker": "KXBTC",
      "title": "Bitcoin",
      "sub_title": "Price milestones",
      "status": "open",
      "strike_date": "2025-01-15T23:59:59Z",
      "markets": []
    }
  ],
  "cursor": "eyJ...",
  "milestones": []
}
```

---

### `get_event`

**HTTP:** `GET /events/{event_ticker}`  
**Auth:** No

**Usage:**
```python
data = await events.get_event(client, "KXBTC", with_nested_markets=True)
```

**Query parameters**

| Parameter             | Type | Description                   |
|-----------------------|------|-------------------------------|
| `with_nested_markets` | bool | Include markets in event      |

**Response (200):**
```json
{
  "event": {
    "event_ticker": "KXBTC",
    "series_ticker": "KXBTC",
    "title": "Bitcoin",
    "status": "open",
    "markets": []
  },
  "markets": []
}
```

---

### `get_event_metadata`

**HTTP:** `GET /events/{event_ticker}/metadata`  
**Auth:** No

**Usage:**
```python
data = await events.get_event_metadata(client, "KXBTC")
```

**Response (200):** metadata object per Kalshi

---

### `get_multivariate_events`

**HTTP:** `GET /events/multivariate`  
**Auth:** No

**Usage:**
```python
data = await events.get_multivariate_events(client, limit=100, cursor=None)
```

**Query parameters**

| Parameter | Type | Description       |
|-----------|------|-------------------|
| `limit`   | int  | Per page          |
| `cursor`  | str  | Pagination cursor |

**Response (200):** `{ "events": [...], "cursor": "..." }` (multivariate shape per Kalshi)

---

## Orders

All order endpoints **require auth**.

---

### `get_orders`

**HTTP:** `GET /portfolio/orders`  
**Auth:** Yes

**Usage:**
```python
data = await orders.get_orders(
    client,
    ticker=None,
    event_ticker=None,
    min_ts=None,
    max_ts=None,
    status="resting",
    limit=100,
    cursor=None,
    subaccount=None,
)
```

**Query parameters**

| Parameter       | Type | Description                        |
|-----------------|------|------------------------------------|
| `ticker`        | str  | Filter by market ticker            |
| `event_ticker`  | str  | Filter by event ticker             |
| `min_ts`        | int  | Min created (Unix)                 |
| `max_ts`        | int  | Max created (Unix)                 |
| `status`        | str  | `resting`, `canceled`, `executed`  |
| `limit`         | int  | Per page (1–200)                   |
| `cursor`        | str  | Pagination cursor                  |
| `subaccount`    | int  | Filter by subaccount               |

**Response (200):**
```json
{
  "orders": [
    {
      "order_id": "ord-...",
      "user_id": "usr-...",
      "ticker": "KXBTC-24JAN15",
      "side": "yes",
      "action": "buy",
      "type": "limit",
      "status": "resting",
      "yes_price": 50,
      "no_price": 50,
      "fill_count": 0,
      "remaining_count": 10,
      "initial_count": 10,
      "created_time": "2025-01-10T14:00:00Z",
      "last_update_time": "2025-01-10T14:00:00Z"
    }
  ],
  "cursor": "eyJ..."
}
```

---

### `get_order`

**HTTP:** `GET /portfolio/orders/{order_id}`  
**Auth:** Yes

**Usage:**
```python
data = await orders.get_order(client, "ord-abc123")
```

**Response (200):**
```json
{
  "order": {
    "order_id": "ord-abc123",
    "ticker": "KXBTC-24JAN15",
    "side": "yes",
    "action": "buy",
    "type": "limit",
    "status": "resting",
    "yes_price": 50,
    "no_price": 50,
    "remaining_count": 10,
    "initial_count": 10,
    "created_time": "2025-01-10T14:00:00Z"
  }
}
```

---

### `create_order`

**HTTP:** `POST /portfolio/orders`  
**Auth:** Yes

**Usage:**
```python
data = await orders.create_order(
    client,
    ticker="KXBTC-24JAN15",
    side="yes",
    action="buy",
    count=10,
    yes_price=50,
    type="limit",
    time_in_force="good_till_canceled",
    client_order_id=None,
    expiration_ts=None,
    buy_max_cost=None,
    post_only=None,
    reduce_only=None,
    self_trade_prevention_type=None,
    order_group_id=None,
    cancel_order_on_pause=None,
    subaccount=0,
)
```

**Body parameters**

| Parameter                   | Type  | Required | Description                                      |
|----------------------------|-------|----------|--------------------------------------------------|
| `ticker`                   | str   | Yes      | Market ticker                                    |
| `side`                     | str   | Yes      | `yes` or `no`                                    |
| `action`                   | str   | Yes      | `buy` or `sell`                                  |
| `count`                    | int   | One of   | Contracts (use `count` or `count_fp`)            |
| `count_fp`                 | str   | One of   | Contracts (fixed-point string)                   |
| `type`                     | str   | No       | `limit` or `market`                              |
| `yes_price`                | int   | No       | 1–99 (cents)                                    |
| `no_price`                 | int   | No       | 1–99 (cents)                                    |
| `yes_price_dollars`        | str   | No       | Price in dollars                                |
| `no_price_dollars`         | str   | No       | Price in dollars                                |
| `client_order_id`          | str   | No       | Client-defined ID                               |
| `expiration_ts`            | int   | No       | Order expiry (Unix)                              |
| `time_in_force`            | str   | No       | `fill_or_kill`, `good_till_canceled`, `immediate_or_cancel` |
| `buy_max_cost`             | int   | No       | Max cost (cents); implies FoK                    |
| `post_only`                | bool  | No       | Post-only                                       |
| `reduce_only`              | bool  | No       | Reduce-only                                     |
| `sell_position_floor`      | int   | No       | Deprecated; use `reduce_only`                    |
| `self_trade_prevention_type`| str  | No       | `taker_at_cross`, `maker`                        |
| `order_group_id`           | str   | No       | Order group                                     |
| `cancel_order_on_pause`    | bool  | No       | Cancel when exchange pauses                     |
| `subaccount`               | int   | No       | Subaccount (default 0)                           |

**Response (201):**
```json
{
  "order": {
    "order_id": "ord-...",
    "ticker": "KXBTC-24JAN15",
    "side": "yes",
    "action": "buy",
    "type": "limit",
    "status": "resting",
    "yes_price": 50,
    "no_price": 50,
    "remaining_count": 10,
    "initial_count": 10,
    "created_time": "2025-01-10T14:00:00Z"
  }
}
```

---

### `cancel_order`

**HTTP:** `DELETE /portfolio/orders/{order_id}`  
**Auth:** Yes

**Usage:**
```python
data = await orders.cancel_order(client, "ord-abc123")
```

**Response (200):**
```json
{
  "order": { "order_id": "ord-abc123", "status": "canceled", ... },
  "reduced_by": 10,
  "reduced_by_fp": "10.00"
}
```

---

### `amend_order`

**HTTP:** `POST /portfolio/orders/{order_id}/amend`  
**Auth:** Yes

**Usage:**
```python
data = await orders.amend_order(
    client,
    "ord-abc123",
    ticker="KXBTC-24JAN15",
    side="yes",
    action="buy",
    yes_price=55,
    no_price=None,
    count=None,
    count_fp=None,
    expiration_ts=None,
)
```

**Body parameters (Kalshi requires ticker, side, action plus any of the optional):**

| Parameter               | Type | Description                          |
|-------------------------|------|--------------------------------------|
| `ticker`                | str  | **Required.** Market ticker.         |
| `side`                  | str  | **Required.** `yes` or `no`.         |
| `action`                | str  | **Required.** `buy` or `sell`.       |
| `yes_price`             | int  | New yes price (1–99)                 |
| `no_price`              | int  | New no price (1–99)                  |
| `yes_price_dollars`     | str  | Yes price (dollars)                  |
| `no_price_dollars`      | str  | No price (dollars)                   |
| `count`                 | int  | New size                             |
| `count_fp`              | str  | New size (fp)                        |
| `client_order_id`       | str  | Original client order ID to amend    |
| `updated_client_order_id` | str | New client order ID after amendment  |
| `expiration_ts`         | int  | New expiry (Unix)                    |

**Response (200):** `{ "old_order": { ... }, "order": { ... } }`

---

### `decrease_order`

**HTTP:** `POST /portfolio/orders/{order_id}/decrease`  
**Auth:** Yes

**Usage:**
```python
# Reduce by 5 contracts:
data = await orders.decrease_order(client, "ord-abc123", reduce_by=5)
# Or reduce to 1 contract:
data = await orders.decrease_order(client, "ord-abc123", reduce_to=1)
```

**Body parameters (exactly one of reduce_by/reduce_by_fp or reduce_to/reduce_to_fp):**

| Parameter     | Type | Description                               |
|---------------|------|-------------------------------------------|
| `reduce_by`   | int  | Contracts to reduce by (≥1)               |
| `reduce_by_fp`| str  | Contracts to reduce by (fp)               |
| `reduce_to`   | int  | Contracts to reduce to (≥0)               |
| `reduce_to_fp`| str  | Contracts to reduce to (fp)               |

**Response (200):** `{ "order": { ... } }`

---

### `batch_create_orders`

**HTTP:** `POST /portfolio/orders/batched`  
**Auth:** Yes

**Usage:**
```python
data = await orders.batch_create_orders(client, [
    {"ticker": "KXBTC-24JAN15", "side": "yes", "action": "buy", "count": 1, "yes_price": 50},
    {"ticker": "KXBTC-24JAN15", "side": "no", "action": "buy", "count": 1, "no_price": 55},
])
```

**Body:** `{ "orders": [ { ... }, ... ] }` — each object same shape as `create_order`.

**Response (200):** `{ "orders": [ { ... }, ... ] }`

---

### `batch_cancel_orders`

**HTTP:** `DELETE /portfolio/orders/batched`  
**Auth:** Yes

**Usage:**
```python
data = await orders.batch_cancel_orders(client, order_ids=["ord-1", "ord-2"])
# or: ids=["ord-1", "ord-2"]
```

**Body:** `{ "ids": ["order_id", ...] }`

**Response (200):** per Kalshi (e.g. `{ "orders": [...] }`)

---

## Portfolio

All portfolio endpoints **require auth**.

---

### `get_balance`

**HTTP:** `GET /portfolio/balance`  
**Auth:** Yes

**Usage:**
```python
data = await portfolio.get_balance(client)
```

**Response (200):**
```json
{
  "balance": 100000,
  "portfolio_value": 105000,
  "updated_ts": 1704067200
}
```

---

### `get_positions`

**HTTP:** `GET /portfolio/positions`  
**Auth:** Yes

**Usage:**
```python
data = await portfolio.get_positions(
    client,
    cursor=None,
    limit=100,
    count_filter="position,total_traded",
    ticker=None,
    event_ticker=None,
    subaccount=None,
)
```

**Query parameters**

| Parameter      | Type | Description                                |
|----------------|------|--------------------------------------------|
| `cursor`       | str  | Pagination cursor                          |
| `limit`        | int  | Per page (1–1000)                          |
| `count_filter` | str  | `position`, `total_traded` (comma-separated)|
| `ticker`       | str  | Filter by market ticker                    |
| `event_ticker` | str  | Filter by event ticker                     |
| `subaccount`   | int  | Filter by subaccount                       |

**Response (200):**
```json
{
  "market_positions": [
    {
      "ticker": "KXBTC-24JAN15",
      "position": 10,
      "position_fp": "10.00",
      "total_traded": 20,
      "market_exposure": 460,
      "realized_pnl": 0,
      "resting_orders_count": 1,
      "fees_paid": 5,
      "last_updated_ts": "2025-01-10T14:00:00Z"
    }
  ],
  "event_positions": [],
  "cursor": "eyJ..."
}
```

---

### `get_fills`

**HTTP:** `GET /portfolio/fills`  
**Auth:** Yes

**Usage:**
```python
data = await portfolio.get_fills(
    client,
    ticker=None,
    event_ticker=None,
    min_ts=None,
    max_ts=None,
    limit=100,
    cursor=None,
    subaccount=None,
)
```

**Query parameters**

| Parameter      | Type | Description             |
|----------------|------|-------------------------|
| `ticker`       | str  | Filter by market        |
| `event_ticker` | str  | Filter by event         |
| `min_ts`       | int  | Min time (Unix)         |
| `max_ts`       | int  | Max time (Unix)         |
| `limit`        | int  | Per page                |
| `cursor`       | str  | Pagination cursor       |
| `subaccount`   | int  | Filter by subaccount    |

**Response (200):** `{ "fills": [...], "cursor": "..." }`

---

### `get_settlements`

**HTTP:** `GET /portfolio/settlements`  
**Auth:** Yes

**Usage:**
```python
data = await portfolio.get_settlements(
    client,
    ticker=None,
    event_ticker=None,
    min_ts=None,
    max_ts=None,
    limit=100,
    cursor=None,
    subaccount=None,
)
```

**Query parameters:** same as `get_fills`.

**Response (200):** `{ "settlements": [...], "cursor": "..." }`

---

### `get_total_resting_order_value`

**HTTP:** `GET /portfolio/summary/total_resting_order_value`  
**Auth:** Yes. FCM-oriented; may 404 for regular accounts.

**Usage:**
```python
data = await portfolio.get_total_resting_order_value(client)
```

**Response (200):** `{ "total_resting_order_value": 1234 }` (cents)

---

### `create_subaccount`

**HTTP:** `POST /portfolio/subaccounts`  
**Auth:** Yes

**Usage:**
```python
data = await portfolio.create_subaccount(client, nickname="trading-1")
```

**Body parameters**

| Parameter  | Type | Description     |
|------------|------|-----------------|
| `nickname` | str  | Optional label  |

**Response (200):** `{ "subaccount": { ... } }` per Kalshi

---

### `transfer_between_subaccounts`

**HTTP:** `POST /portfolio/transfers`  
**Auth:** Yes

**Usage:**
```python
data = await portfolio.transfer_between_subaccounts(
    client,
    from_subaccount=0,
    to_subaccount=1,
    amount=10000,
)
```

**Body parameters**

| Parameter         | Type | Description        |
|-------------------|------|--------------------|
| `from_subaccount` | int  | Source (0 = main)  |
| `to_subaccount`   | int  | Destination        |
| `amount`          | int  | Amount in cents    |

**Response (200):** `{ "transfer": { ... } }` per Kalshi

---

### `get_all_subaccount_balances`

**HTTP:** `GET /portfolio/subaccounts/balances`  
**Auth:** Yes

**Usage:**
```python
data = await portfolio.get_all_subaccount_balances(client)
```

**Response (200):** `{ "subaccount_balances": [...] }` or similar

---

### `get_subaccount_transfers`

**HTTP:** `GET /portfolio/subaccounts/transfers`  
**Auth:** Yes

**Usage:**
```python
data = await portfolio.get_subaccount_transfers(client, limit=50, cursor=None)
```

**Query parameters**

| Parameter | Type | Description       |
|-----------|------|-------------------|
| `limit`   | int  | Per page          |
| `cursor`  | str  | Pagination cursor |

**Response (200):** `{ "transfers": [...], "cursor": "..." }`

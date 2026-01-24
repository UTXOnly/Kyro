# Kyro

**Async Kalshi API client** — aiohttp, orjson, Pydantic. Built for **apps** (library, not CLI).

- **REST client** for Kalshi’s HTTP API (markets, orders, portfolio, etc.).
- **WebSocket** support planned; shared config/session design for reuse.
- **Error handling**: `KyroError`, `KyroHTTPError`, `KyroConnectionError`, `KyroTimeoutError`, `KyroValidationError`.
- **Serialization**: orjson for JSON, Pydantic for request/response models.

## Requirements

- Python ≥ 3.10
- aiohttp, pydantic, orjson

## Install

```bash
pip install -e .
# or: pip install kyro  (when published)
```

## Quick start

```python
import asyncio
from kyro import RestClient, KyroConfig

async def main():
    cfg = KyroConfig()  # defaults: production Kalshi base URL
    async with RestClient(cfg) as client:
        data = await client.get("/markets")
        print(data)

asyncio.run(main())
```

## Configuration

```python
from kyro import KyroConfig

# Production (default)
cfg = KyroConfig(base_url="https://trading-api.kalshi.com/v2")

# Demo
cfg = KyroConfig(base_url="https://demo-api.kalshi.co/trade-api/v2")

# Timeouts, headers
cfg = KyroConfig(
    request_timeout=15.0,
    connect_timeout=5.0,
    default_headers={"User-Agent": "MyApp/1.0"},
)

# Auth (KALSHI-ACCESS-*). Signing (RSA) to be added later.
cfg = KyroConfig(auth_headers={
    "KALSHI-ACCESS-KEY": "your-key-id",
    "KALSHI-ACCESS-TIMESTAMP": "...",
    "KALSHI-ACCESS-SIGNATURE": "...",
})
```

## REST client

```python
from kyro import RestClient, KyroConfig
from pydantic import BaseModel

class Market(BaseModel):
    ticker: str
    title: str | None = None

async with RestClient(KyroConfig()) as client:
    # Raw JSON (dict/list)
    data = await client.get("/markets", params={"limit": 10})

    # Validated Pydantic model
    m = await client.get("/markets/KXBTC", response_model=Market)

    # POST / PUT / PATCH with JSON body
    await client.post("/portfolio/orders", json={"ticker": "KXBTC", "side": "yes", "action": "buy", "count": 1, "yes_price": 50})
```

## Modular API (Kalshi reference)

Modular methods for [Kalshi’s API reference](https://docs.kalshi.com/api-reference/). Pass the `RestClient` as the first argument.

```python
from kyro import RestClient, KyroConfig
from kyro.rest import exchange, markets, events, orders, portfolio

async with RestClient(KyroConfig()) as client:
    # Exchange (no auth)
    status = await exchange.get_exchange_status(client)
    await exchange.get_exchange_announcements(client)
    await exchange.get_exchange_schedule(client)

    # Markets
    ms = await markets.get_markets(client, limit=10, status="open")
    m = await markets.get_market(client, "KXBTC")
    ob = await markets.get_market_orderbook(client, "KXBTC", depth=10)
    trades = await markets.get_trades(client, ticker="KXBTC", limit=50)
    await markets.get_market_candlesticks(client, "KXBTC", period_interval=60)
    await markets.get_series(client, "SOME")
    await markets.get_series_list(client, limit=20)

    # Events
    evs = await events.get_events(client, limit=20, status="open")
    ev = await events.get_event(client, "SOME-EVENT")
    await events.get_multivariate_events(client)

    # Orders (auth)
    ords = await orders.get_orders(client, status="resting", limit=50)
    o = await orders.get_order(client, "order-id")
    await orders.create_order(client, ticker="KXBTC", side="yes", action="buy", count=1, yes_price=50)
    await orders.cancel_order(client, "order-id")
    await orders.amend_order(client, "order-id", yes_price=55)
    await orders.batch_create_orders(client, [{"ticker": "KXBTC", "side": "yes", "action": "buy", "count": 1, "yes_price": 50}])
    await orders.batch_cancel_orders(client, order_ids=["id1", "id2"])

    # Portfolio (auth)
    bal = await portfolio.get_balance(client)
    pos = await portfolio.get_positions(client, limit=100)
    await portfolio.get_fills(client, limit=50)
    await portfolio.get_settlements(client)
    await portfolio.get_total_resting_order_value(client)
```

## Error handling

```python
from kyro import RestClient, KyroConfig
from kyro.exceptions import KyroHTTPError, KyroConnectionError, KyroTimeoutError

async with RestClient(KyroConfig()) as client:
    try:
        await client.get("/markets")
    except KyroHTTPError as e:
        print(e.status, e.response_body, e.error_code)
    except KyroConnectionError:
        print("Network error")
    except KyroTimeoutError as e:
        print("Timeout", e.timeout)
```

## Project layout

```
kyro/
├── src/kyro/
│   ├── __init__.py         # Public API
│   ├── _config.py          # KyroConfig (base URL, timeouts, auth)
│   ├── _session.py         # KyroSession (aiohttp, reuse for REST + WS)
│   ├── _serialization.py   # orjson + Pydantic
│   ├── _version.py
│   ├── exceptions.py       # Kyro* exceptions
│   └── rest/
│       ├── __init__.py     # RestClient + api (exchange, markets, …)
│       ├── client.py       # RestClient
│       └── api/           # Modular Kalshi methods (docs.kalshi.com/api-reference)
│           ├── __init__.py
│           ├── exchange.py
│           ├── markets.py
│           ├── events.py
│           ├── orders.py
│           └── portfolio.py
├── pyproject.toml
├── README.md
└── DESIGN_CHECKLIST.md
```

## Development

```bash
python -m venv .venv && source .venv/bin/activate  # or Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest tests/ -v
ruff check src/
```

## License

MIT

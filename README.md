<p align="center">
  <img src="https://raw.githubusercontent.com/UTXOnly/kyro/testing/assets/cleaned_logo.svg" alt="Kyro" width="420">
</p>

# Kyro

Kyro is an async Python client for the [Kalshi API](https://docs.kalshi.com/api-reference/). Built on aiohttp, orjson, and Pydantic. Library only—no CLI.

- REST client for Kalshi’s HTTP API
- Helpers: `exchange`, `markets`, `events`, `orders`, `portfolio`
- Exceptions: `KyroHTTPError`, `KyroTimeoutError`, `KyroConnectionError`, `KyroValidationError`

---

## Requirements

- Python ≥ 3.10  
- aiohttp, pydantic, orjson

## Install

```bash
pip install -e .
# or: pip install kyro  (when published)
```

On Homebrew Python (macOS) and other [PEP 668](https://peps.python.org/pep-0668/) setups, use a virtual environment first:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

---

## Configuration

```python
from kyro import KyroConfig

# Production (default). Despite "elections" in the host, this serves all Kalshi markets.
cfg = KyroConfig(base_url="https://api.elections.kalshi.com/trade-api/v2")

# Demo
cfg = KyroConfig(base_url="https://demo-api.kalshi.co/trade-api/v2")

# Timeouts and headers
cfg = KyroConfig(
    request_timeout=15.0,
    connect_timeout=5.0,
    default_headers={"User-Agent": "MyApp/1.0"},
)

# Auth (KALSHI-ACCESS-*). RSA signing to be added later.
cfg = KyroConfig(auth_headers={
    "KALSHI-ACCESS-KEY": "your-key-id",
    "KALSHI-ACCESS-TIMESTAMP": "...",
    "KALSHI-ACCESS-SIGNATURE": "...",
})
```

---

## Modular API (exchange, markets, events, orders, portfolio)

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

---

## API Reference

Full request/response docs for **every method** (exchange, markets, events, orders, portfolio):  
**[API_REFERENCE.md](API_REFERENCE.md)**

---

## Examples

The **[examples/](examples/)** directory has standalone scripts that use kyro. They are not part of the library.

From **repo root** with kyro installed (venv activated, `pip install -e .` or `.[dev]`):

- **`fetch_orderbook_example.py`** — Fetches an event, a market, and an orderbook; parses the book (best bid/ask, mid, spread). Uses the **demo API** by default (no keys); production may require auth.

  ```bash
  python examples/fetch_orderbook_example.py
  KALSHI_PRODUCTION=1 python examples/fetch_orderbook_example.py   # production
  ```

---

## Low-level REST client

For paths not covered by the modular API, use the generic client:

```python
from kyro import RestClient, KyroConfig
from pydantic import BaseModel

async with RestClient(KyroConfig()) as client:
    # GET with query params
    data = await client.get("/exchange/status")

    # GET with optional Pydantic validation
    class Market(BaseModel):
        ticker: str
        title: str | None = None
    m = await client.get("/markets/KXBTC-24JAN15", response_model=Market)

    # POST / PUT / PATCH / DELETE
    await client.post("/portfolio/orders", json={"ticker": "KXBTC", "side": "yes", "action": "buy", "count": 1, "yes_price": 50})
    await client.delete("/portfolio/orders/order-id-here")
```

---

## Error handling

```python
from kyro import RestClient, KyroConfig
from kyro.rest import markets
from kyro.exceptions import KyroHTTPError, KyroConnectionError, KyroTimeoutError

async with RestClient(KyroConfig()) as client:
    try:
        await markets.get_markets(client, limit=10)
    except KyroHTTPError as e:
        print(e.status, e.response_body, e.error_code)
    except KyroConnectionError:
        print("Network error")
    except KyroTimeoutError as e:
        print("Timeout", e.timeout)
```

---

## Project layout

```
kyro/
├── src/kyro/
│   ├── __init__.py
│   ├── _config.py
│   ├── _session.py
│   ├── _serialization.py
│   ├── _version.py
│   ├── exceptions.py
│   └── rest/
│       ├── __init__.py      # RestClient, exchange, markets, events, orders, portfolio
│       ├── client.py
│       └── api/
│           ├── __init__.py
│           ├── exchange.py
│           ├── markets.py
│           ├── events.py
│           ├── orders.py
│           └── portfolio.py
├── examples/
│   ├── README.md
│   └── fetch_orderbook_example.py   # fetch markets + orderbook, parse, example logic
├── pyproject.toml
├── README.md
├── API_REFERENCE.md   # Request/response docs for every modular method
└── DESIGN_CHECKLIST.md
```

---

## Development

Create a venv, install with dev extras, then run tests (required on Homebrew Python; see [PEP 668](https://peps.python.org/pep-0668/)):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"     # install only; does not run tests
pytest tests/ -v            # run tests
ruff check src/
```

**Tests:** See [TESTING.md](TESTING.md). Quick runs (venv activated, `.[dev]` already installed):

```bash
pytest tests/ -v
pytest tests/ -v --cov=kyro --cov-report=term-missing
```

**Live API smoke** (every endpoint against the real Kalshi API): `python scripts/live_api_smoke.py` — see [TESTING.md](TESTING.md#live-api-smoke-test).

If `pip install -e ".[dev]"` fails with **`externally-managed-environment`**, create and activate a venv first; do not use `--break-system-packages`.

---

## ⚠️ Disclaimer ⚠️

The author accepts no responsibility for any use of this software. Kyro is provided as-is. You must adhere to all [Kalshi API rules and terms](https://docs.kalshi.com/). When trading or using live funds, use caution and understand the risks. Prefer the [demo environment](https://docs.kalshi.com/getting_started/demo_env) for testing.

---

## License

MIT

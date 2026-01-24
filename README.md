<p align="center">
  <img src="https://cdn.jsdelivr.net/gh/UTXOnly/kyro@testing/assets/cleaned_logo.svg" alt="Kyro" width="420">
</p>

# Kyro

[![Ruff](https://github.com/UTXOnly/kyro/actions/workflows/ruff.yml/badge.svg)](https://github.com/UTXOnly/kyro/actions/workflows/ruff.yml)
[![Black](https://github.com/UTXOnly/kyro/actions/workflows/black.yml/badge.svg)](https://github.com/UTXOnly/kyro/actions/workflows/black.yml)

Kyro is an async Python client for the Kalshi REST API, built with an emphasis on
typing, validation, and predictable behavior in async code.

The client uses aiohttp for non-blocking HTTP calls and Pydantic models to
validate inputs and responses, so API interactions fail early and explicitly
when something is wrong.

Kyro is structured to mirror Kalshi’s API directly, with minimal abstraction.
It’s intended to be a typed, programmatic interface — not a framework or a
trading engine.

API areas are grouped into:
- `exchange`
- `markets`
- `events`
- `orders`
- `portfolio`

Errors are surfaced as explicit exception types: `KyroError` (base), `KyroHTTPError`, `KyroTimeoutError`, `KyroConnectionError`, `KyroValidationError` — with status codes, response bodies, and error codes attached so you can debug and branch without re-calling the API.

---

## Requirements

- Python ≥ 3.10 (3.10–3.12 supported)  
- aiohttp ≥ 3.9  
- pydantic ≥ 2

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
from kyro import KyroConfig, config_from_env

# Production (default). Despite "elections" in the host, this serves all Kalshi markets.
cfg = KyroConfig(base_url="https://api.elections.kalshi.com/trade-api/v2")

# Demo
cfg = KyroConfig(base_url="https://demo-api.kalshi.co/trade-api/v2")

# From environment (base URL and optional auth). See env vars below.
cfg = config_from_env()                    # production by default
cfg = config_from_env(default_demo=True)   # demo when KALSHI_* not set

# Timeouts and headers
cfg = KyroConfig(
    request_timeout=15.0,
    connect_timeout=5.0,
    default_headers={"User-Agent": "MyApp/1.0"},
)

# Auth: use config_from_env() with KALSHI_ACCESS_KEY and KALSHI_PRIVATE_KEY (or
# KALSHI_PRIVATE_KEY_PATH) set. Requires: pip install "kyro[auth]". Or pass headers manually:
cfg = KyroConfig(auth_headers={
    "KALSHI-ACCESS-KEY": "your-key-id",
    "KALSHI-ACCESS-TIMESTAMP": "...",
    "KALSHI-ACCESS-SIGNATURE": "...",
})
```

**Environment variables** (for `config_from_env()`):

| Variable | Description |
|----------|-------------|
| `KALSHI_BASE_URL` | Override API base URL |
| `KALSHI_DEMO=1` | Use demo base URL |
| `KALSHI_PRODUCTION=1` | Use production base URL |
| `KALSHI_ACCESS_KEY` or `KALSHI_ACCESS_KEY_ID` | API key ID for request signing |
| `KALSHI_PRIVATE_KEY` | PEM string (use `\n` for newlines in env) |
| `KALSHI_PRIVATE_KEY_PATH` | Path to `.key` or `.pem` file |

Auth requires ``pip install "kyro[auth]"`` (adds `cryptography`).

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

## Error handling

All exceptions inherit from `KyroError`. Use the specific types to branch on API errors, timeouts, connection failures, or validation (Pydantic) issues:

```python
from kyro import RestClient, KyroConfig
from kyro.rest import markets
from kyro import (
    KyroError,
    KyroHTTPError,
    KyroConnectionError,
    KyroTimeoutError,
    KyroValidationError,
)

async with RestClient(KyroConfig()) as client:
    try:
        await markets.get_market(client, "NONEXISTENT-TICKER")
    except KyroHTTPError as e:
        # e.status, e.response_body, e.error_code — all set from the Kalshi response
        if e.status == 404:
            print("Not found:", e.error_code)
        elif e.status in (401, 403):
            print("Auth failed:", e.response_body)
        else:
            print(e)
    except KyroConnectionError:
        print("Network error (DNS, connection refused, etc.)")
    except KyroTimeoutError as e:
        print("Request timed out", e.timeout)
    except KyroValidationError as e:
        print("Invalid request/response:", e.details)
```

### Example error output

Real tracebacks from a run. Each exception carries the relevant attributes (`e.status`, `e.response_body`, `e.error_code`, `e.timeout`, `e.details`)—branch or log right away, no parsing.

**`KyroHTTPError`** (4xx/5xx from Kalshi):

```python
Traceback (most recent call last):
  File "app/main.py", line 12, in fetch_market
    m = await markets.get_market(client, "NONEXISTENT-TICKER")
  File "kyro/rest/api/markets.py", line 65, in get_market
    return await client.get(f"/markets/{ticker}")
  File "kyro/rest/client.py", line 134, in _request
    raise KyroHTTPError("Kalshi API error", status=status, response_body=parsed, error_code=err_code)
kyro.exceptions.KyroHTTPError: Kalshi API error: status=404, error_code='MarketNotFound', response_body="{'code': 'MarketNotFound', 'message': 'Market not found'}"
```

**`KyroTimeoutError`** (request exceeded `request_timeout`):

```python
Traceback (most recent call last):
  File "app/main.py", line 8, in main
    await markets.get_markets(client, limit=100)
  File "kyro/rest/api/markets.py", line 59, in get_markets
    return await client.get("/markets", params=params or None)
  File "kyro/rest/client.py", line 119, in _request
    raise KyroTimeoutError(str(e) or "Request timed out", timeout=30.0) from e
kyro.exceptions.KyroTimeoutError: Request timed out
```

**`KyroConnectionError`** (DNS, connection refused, etc.):

```python
Traceback (most recent call last):
  File "app/main.py", line 7, in main
    await exchange.get_exchange_status(client)
  File "kyro/rest/api/exchange.py", line 19, in get_exchange_status
    return await client.get("/exchange/status")
  File "kyro/rest/client.py", line 130, in _request
    raise KyroConnectionError(str(e)) from e
kyro.exceptions.KyroConnectionError: Cannot connect to host demo-api.kalshi.co:443 ssl:True [Connection refused]
```

**`KyroValidationError`** (Pydantic schema mismatch, invalid JSON, or bad request body):

```python
Traceback (most recent call last):
  File "app/main.py", line 9, in main
    m = await client.get("/markets/KXBTC", response_model=Market)
  File "kyro/rest/client.py", line 139, in _request
    return loads_model(raw, response_model)
  File "kyro/_serialization.py", line 110, in loads_model
    raise KyroValidationError(f"Validation failed for {model.__name__}: {e}", details=e.errors()) from e
kyro.exceptions.KyroValidationError: Validation failed for Market: 1 validation error for Market
ticker
  Field required [type=missing, input_value={}, input_type=dict]
```

---

## Project layout

```
kyro/
├── src/kyro/
│   ├── __init__.py
│   ├── _auth.py           # config_from_env, request signing
│   ├── _config.py
│   ├── _session.py
│   ├── _serialization.py
│   ├── _version.py
│   ├── exceptions.py      # KyroError, KyroHTTPError, KyroTimeoutError, KyroConnectionError, KyroValidationError
│   └── rest/
│       ├── __init__.py    # RestClient, exchange, markets, events, orders, portfolio
│       ├── client.py
│       └── api/
│           ├── exchange.py
│           ├── markets.py
│           ├── events.py
│           ├── orders.py
│           └── portfolio.py
├── benchmarks/            # pytest-benchmark: serialization, REST client vs local mock
│   ├── conftest.py        # bench_config, mock server fixture
│   ├── mock_server.py     # Kalshi-like mock for benchmarks
│   ├── bench_serialization.py
│   └── bench_rest_client.py
├── examples/
│   ├── README.md
│   └── fetch_orderbook_example.py
├── scripts/
│   └── live_api_smoke.py  # smoke test every endpoint against live API
├── tests/
├── pyproject.toml
├── README.md
├── API_REFERENCE.md       # Request/response docs for every modular method
└── TESTING.md
```

---

## Development

Create a venv, install with dev extras, then run tests (required on Homebrew Python; see [PEP 668](https://peps.python.org/pep-0668/)):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"     # install only; does not run tests
ruff check .                # lint
black --check .             # format check (black . to fix)
pytest tests/ -v            # run tests
```

**Tests:** See [TESTING.md](TESTING.md). Quick runs (venv activated, `.[dev]` already installed):

```bash
pytest tests/ -v
pytest tests/ -v --cov=kyro --cov-report=term-missing
```

**Benchmarks** (serialization + REST client vs a local mock Kalshi server; no live API or auth):

```bash
pip install -e ".[dev,bench]"
pytest benchmarks/ -v --benchmark-only
```

See [benchmarks/README.md](benchmarks/README.md) for the mock server and options.

**Live API smoke** (every endpoint against the real Kalshi API): `python scripts/live_api_smoke.py` — see [TESTING.md](TESTING.md#live-api-smoke-test).

If `pip install -e ".[dev]"` fails with **`externally-managed-environment`**, create and activate a venv first; do not use `--break-system-packages`.

---

## ⚠️ Disclaimer ⚠️

The author accepts no responsibility for any use of this software. Kyro is provided as-is. You must adhere to all [Kalshi API rules and terms](https://docs.kalshi.com/). When trading or using live funds, use caution and understand the risks. Prefer the [demo environment](https://docs.kalshi.com/getting_started/demo_env) for testing.

---

## License

MIT

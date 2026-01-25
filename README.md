<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://cdn.jsdelivr.net/gh/UTXOnly/kyro@main/assets/logo.png">
    <img src="https://cdn.jsdelivr.net/gh/UTXOnly/kyro@main/assets/logo-light-bg.png" alt="Kyro" width="420">
  </picture>
</p>

# Kyro

[![PyPI](https://img.shields.io/pypi/v/kyro.svg)](https://pypi.org/project/kyro/) [![Ruff](https://github.com/UTXOnly/kyro/actions/workflows/ruff.yml/badge.svg)](https://github.com/UTXOnly/kyro/actions/workflows/ruff.yml) [![Black](https://github.com/UTXOnly/kyro/actions/workflows/black.yml/badge.svg)](https://github.com/UTXOnly/kyro/actions/workflows/black.yml) [![Tests](https://github.com/UTXOnly/kyro/actions/workflows/test.yml/badge.svg)](https://github.com/UTXOnly/kyro/actions/workflows/test.yml) [![Benchmarks](https://github.com/UTXOnly/kyro/actions/workflows/benchmarks.yml/badge.svg)](https://github.com/UTXOnly/kyro/actions/workflows/benchmarks.yml)

Kyro is an async Python client library for the Kalshi REST API.

It uses aiohttp for async HTTP requests and Pydantic for request and response
validation. The library mirrors the API surface closely and exposes a typed,
low-level interface.

API areas are grouped into:
- `exchange`
- `markets`
- `events`
- `search`
- `orders`
- `portfolio`

Errors are surfaced as explicit exception types: `KyroError` (base), `KyroHTTPError`, `KyroTimeoutError`, `KyroConnectionError`, `KyroValidationError` — with status codes, response bodies, and error codes attached so you can debug and branch without re-calling the API.

---

## Requirements

- Python ≥ 3.10 (3.10–3.12 supported)  
- aiohttp ≥ 3.9  
- pydantic ≥ 2

## Install

From [PyPI](https://pypi.org/project/kyro/):

```bash
pip install kyro
```

From the repo (development / unreleased):

```bash
pip install -e .
```

Authentication (request signing, `.env` loading) is included in the core package. See [Authentication](#authentication).

On Homebrew Python (macOS) and other [PEP 668](https://peps.python.org/pep-0668/) setups, use a virtual environment first:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install kyro   # or: pip install -e .  for development
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
```

**Environment variables** (for `config_from_env()`): put these in a `.env` in the current directory (copy from `.env.example`) or export them. `.env` is loaded automatically when `config_from_env()` is used.

| Variable | Description |
|----------|-------------|
| `KALSHI_BASE_URL` | Override API base URL |
| `KALSHI_DEMO=1` | Use demo base URL |
| `KALSHI_PRODUCTION=1` | Use production base URL |
| `KALSHI_ACCESS_KEY` or `KALSHI_ACCESS_KEY_ID` | API key ID for request signing |
| `KALSHI_PRIVATE_KEY` | PEM string (use `\n` for newlines in env) |
| `KALSHI_PRIVATE_KEY_PATH` | Path to `.key` or `.pem` file |

---

## Authentication

Kalshi uses **RSA-PSS request signing**. Each authenticated request must include:

- `KALSHI-ACCESS-KEY` — your API key ID  
- `KALSHI-ACCESS-TIMESTAMP` — Unix milliseconds  
- `KALSHI-ACCESS-SIGNATURE` — base64‑encoded signature of `timestamp + method + path` (path without query string), signed with your private key.

Kyro supports three ways to supply auth; **`config_from_env()` is the usual choice.**

### 1. `config_from_env()` (recommended)

Set keys in `.env` or the environment (`.env` is loaded automatically by `config_from_env()`). In `.env` (or export):

```
KALSHI_ACCESS_KEY=your-key-id
KALSHI_PRIVATE_KEY_PATH=/path/to/your.pem
# or inline PEM (use \n for newlines):
# KALSHI_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
```

Then:

```python
from kyro import config_from_env, RestClient

cfg = config_from_env()  # or config_from_env(default_demo=True)
async with RestClient(cfg) as client:
    bal = await client.get("/portfolio/balance")  # auth added automatically
```

- **`cryptography`** and **`python-dotenv`** are core dependencies; signing and `.env` loading work with a plain `pip install kyro`.
- If both `KALSHI_ACCESS_KEY` (or `KALSHI_ACCESS_KEY_ID`) and a private key (from `KALSHI_PRIVATE_KEY` or `KALSHI_PRIVATE_KEY_PATH`) are set, Kyro builds an **auth signer** and attaches the three headers to every request. No extra code.
- `KALSHI_PRIVATE_KEY_PATH` can be relative to the current working directory (e.g. `kal_key.pem` or `.kalshi/kal_key.pem`).
- For inline PEM in `.env`, use `\n` for newlines: `KALSHI_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----"`.

### 2. Static `auth_headers` (manual or pre-signed)

If you generate the three headers yourself (e.g. for testing or a custom pipeline):

```python
from kyro import KyroConfig, RestClient

cfg = KyroConfig(
    base_url="https://api.elections.kalshi.com/trade-api/v2",
    auth_headers={
        "KALSHI-ACCESS-KEY": "your-key-id",
        "KALSHI-ACCESS-TIMESTAMP": "1737654321000",
        "KALSHI-ACCESS-SIGNATURE": "base64-signature...",
    },
)
async with RestClient(cfg) as client:
    ...
```

**Caveat:** the timestamp must be fresh for each request. Kalshi rejects old timestamps, so static `auth_headers` are only suitable for short-lived runs or when you refresh them yourself. For normal use, prefer `config_from_env()` or an `auth_signer`.

### 3. Custom `auth_signer` (advanced)

You can pass a callable that returns the auth headers per request:

```python
from kyro import KyroConfig, RestClient

def my_signer(method: str, path: str, body: bytes | None) -> dict[str, str]:
    # path is the full path (e.g. /trade-api/v2/portfolio/balance), no query string.
    # Return {"KALSHI-ACCESS-KEY": "...", "KALSHI-ACCESS-TIMESTAMP": "...", "KALSHI-ACCESS-SIGNATURE": "..."}
    ...

cfg = KyroConfig(base_url="...", auth_signer=my_signer)
async with RestClient(cfg) as client:
    ...
```

- **`auth_signer`** overrides **`auth_headers`**: if both are set, only the signer is used.
- The signer is called on every request with `(method, path, body)`. Kyro sends whatever headers it returns.

### Which endpoints require auth

| Requires auth | Endpoints |
|---------------|-----------|
| **No** | `exchange.get_exchange_status`, `get_exchange_announcements`, `get_exchange_schedule`, `get_series_fee_changes`; all of `markets.*`, `events.*`, and `search.*` |
| **Yes** | `exchange.get_user_data_timestamp`; all of `orders.*` and `portfolio.*` |

Without auth, public endpoints work as usual. Auth-required calls return `401` if the headers are missing or invalid.

### Getting API keys and keys file

1. Log in at [kalshi.com](https://kalshi.com) → **Account** → **API** (or [API Keys](https://trading.kalshi.com/settings/api)).
2. Create an API key and download the `.pem` (private key). Keep the key ID shown there.
3. Put `KALSHI_ACCESS_KEY=<key-id>` and `KALSHI_PRIVATE_KEY_PATH=/path/to/file.pem` in `.env`, or use `KALSHI_PRIVATE_KEY` with the PEM string.

**Security:** Do not commit `.env` or `.pem` files. Prefer `KALSHI_PRIVATE_KEY_PATH` to a file outside the repo; avoid storing the raw PEM in env if you can.

---

## Modular API (exchange, markets, events, search, orders, portfolio)

```python
from kyro import RestClient, KyroConfig
from kyro.rest import exchange, markets, events, search, orders, portfolio

async with RestClient(KyroConfig()) as client:
    # Exchange (no auth except get_user_data_timestamp)
    status = await exchange.get_exchange_status(client)
    await exchange.get_exchange_announcements(client)
    await exchange.get_exchange_schedule(client)
    await exchange.get_series_fee_changes(client, series_ticker="KXBTC")
    await exchange.get_user_data_timestamp(client)  # auth

    # Markets — filters: series_ticker, event_ticker, status, tickers, min/max_*_ts, cursor
    ms = await markets.get_markets(
        client, series_ticker="KXBTC", limit=10, status="open"
    )
    await markets.get_markets(
        client, event_ticker="INXD-25", limit=5, status="open"
    )
    m = await markets.get_market(client, "KXBTC-24JAN15")
    ob = await markets.get_market_orderbook(client, "KXBTC-24JAN15", depth=10)
    trades = await markets.get_trades(
        client,
        ticker="KXBTC-24JAN15",
        limit=50,
        min_ts=1704067200,
        max_ts=1735689600,
    )
    await markets.get_market_candlesticks(
        client,
        "KXBTC-24JAN15",
        series_ticker="KXBTC",
        period_interval=60,
        limit=100,
    )
    await markets.get_live_data(client, "KXBTC-24JAN15")
    await markets.get_multiple_live_data(client, "KXBTC-24JAN15,INXD-25")
    await markets.get_series(client, "KXBTC")
    await markets.get_series_list(client, limit=20)  # cursor= for pagination

    # Events — filters: series_ticker, status, with_nested_markets, with_milestones, min_close_ts
    evs = await events.get_events(
        client,
        limit=20,
        status="open",
        series_ticker="KXBTC",
        with_nested_markets=True,
    )
    ev = await events.get_event(client, "INXD-25", with_nested_markets=True)
    await events.get_event_metadata(client, "INXD-25")
    await events.get_event_candlesticks(
        client, "KXBTC", "INXD-25", period_interval=60, limit=100
    )
    await events.get_multivariate_events(client, limit=10)

    # Search (no auth)
    await search.get_sports_filters(client)
    await search.get_tags_by_categories(client)

    # Orders (auth) — filters: ticker, event_ticker, status, min_ts, max_ts, cursor, subaccount
    ords = await orders.get_orders(
        client, ticker="KXBTC-24JAN15", status="resting", limit=50
    )
    o = await orders.get_order(client, "order-id")
    await orders.create_order(
        client,
        ticker="KXBTC-24JAN15",
        side="yes",
        action="buy",
        count=1,
        yes_price=50,
        time_in_force="good_till_canceled",
    )
    await orders.cancel_order(client, "order-id")
    await orders.amend_order(
        client, "order-id", ticker="KXBTC-24JAN15", side="yes", action="buy", yes_price=55
    )
    await orders.decrease_order(client, "order-id", reduce_by=1)
    await orders.batch_create_orders(
        client,
        [{"ticker": "KXBTC-24JAN15", "side": "yes", "action": "buy", "count": 1, "yes_price": 50}],
    )
    await orders.batch_cancel_orders(client, order_ids=["id1", "id2"])

    # Portfolio (auth) — filters: ticker, event_ticker, min_ts, max_ts, cursor, subaccount
    await portfolio.get_portfolio(client)
    bal = await portfolio.get_balance(client)
    pos = await portfolio.get_positions(
        client, ticker="KXBTC-24JAN15", limit=100
    )
    await portfolio.get_fills(
        client,
        ticker="KXBTC-24JAN15",
        min_ts=1704067200,
        max_ts=1735689600,
        limit=50,
    )
    await portfolio.get_settlements(
        client, event_ticker="INXD-25", limit=50
    )
    await portfolio.get_total_resting_order_value(client)
```

---

## API Reference

Full request/response docs for **every method** (exchange, markets, events, search, orders, portfolio):  
**[API_REFERENCE.md](API_REFERENCE.md)**

---

## Examples

The **[examples/](examples/)** directory has standalone scripts that use kyro. They are not part of the library.

From **repo root** with kyro installed (venv activated, `pip install -e .` or `.[dev]`):

- **`fetch_orderbook_example.py`** — Fetches an event, a market, and an orderbook; parses the book (best bid/ask, mid, spread). Uses the **demo API** by default (no keys); production may require auth.

  ```bash
  python examples/fetch_orderbook_example.py
  # production: KALSHI_PRODUCTION=1 in .env, or: KALSHI_PRODUCTION=1 python examples/fetch_orderbook_example.py
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
│       ├── __init__.py    # RestClient, exchange, markets, events, search, orders, portfolio
│       ├── client.py
│       └── api/
│           ├── exchange.py
│           ├── markets.py
│           ├── events.py
│           ├── search.py
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

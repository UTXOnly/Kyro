# Testing Kyro

**Run all commands from the repository root** with the venv activated.

## Setup (install only)

Use a **virtual environment** (required on Homebrew Python and other [PEP 668](https://peps.python.org/pep-0668/)–managed systems):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

`pip install -e ".[dev]"` **only installs** the package and dev deps (including pytest); it does **not** run tests. Use the project venv and this install—do **not** rely on `pipx install pytest` or system pytest.

If you see **`error: externally-managed-environment`** when running `pip install`, you need to create and activate a venv first (as above); do not use `--break-system-packages`.

With [uv](https://github.com/astral-sh/uv):

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Run tests

From **repo root**, with venv activated and `.[dev]` installed:

```bash
pytest tests/ -v
```

One-liner to install and run (from repo root, with venv activated):

```bash
pip install -e ".[dev]" && pytest tests/ -v
```

## Coverage

```bash
pytest tests/ -v --cov=kyro --cov-report=term-missing
```

## Benchmarks

**`benchmarks/`** — speed benchmarks for serialization (`dumps`, `loads`, `loads_model`) and RestClient round-trips against the **live Kalshi API** (uses `config_from_env`, network required). Install and run:

```bash
pip install -e ".[dev,bench]"
pytest benchmarks/ -v --benchmark-only
```

Put `KALSHI_DEMO=1` (or `KALSHI_PRODUCTION=1`) and, for `get_balance`/`get_orders`, auth vars in `.env` or export them. Install: `pip install -e ".[dev,bench]"`. See **[benchmarks/README.md](benchmarks/README.md)**. `config_from_env` loads `.env` (included in core).

## Live API smoke test

**`scripts/live_api_smoke.py`** calls every kyro endpoint against the real Kalshi API: it discovers an open market, runs all reads and mutating calls, and writes every request/response to an audit log for review.

From **repo root** (venv activated, network required):

```bash
cp .env.example .env   # edit .env with your production keys
python scripts/live_api_smoke.py     # always uses production (ignores KALSHI_DEMO)
```

**Auth is required.** Put `KALSHI_ACCESS_KEY` and `KALSHI_PRIVATE_KEY` or `KALSHI_PRIVATE_KEY_PATH` in `.env` at project root (copy from `.env.example`). The script loads `.env` from the project root. `KALSHI_PRIVATE_KEY_PATH` may be relative (e.g. `kal_key.pem` or `.kalshi/kal_key.pem`). Install: `pip install -e ".[dev]"`.

- **Pass = 2xx only.** Any 4xx/5xx or exception is **fail**. We are not testing error handling.
- **Audit log** — `live_smoke_audit.log` (or `KALSHI_SMOKE_AUDIT_LOG`). `.gitignore`d.
- **Discovery** — Searches up to 100 open markets for one where `get_market` and `get_market_candlesticks` both return 200; if none, uses first where `get_market` returns 200.
- **Mutating** — 1-share limit @ 1¢, 1¢ `transfer_between_subaccounts`, etc. All mutating endpoints are run.

The script exits with code 1 if any **fail**.

## Options

- **Stop on first failure:** `pytest tests/ -v -x`
- **Run a specific file:** `pytest tests/test_rest_client.py -v`
- **Run a specific test:** `pytest tests/test_rest_client.py::test_get_200_json -v`
- **Verbose logs:** `pytest tests/ -v -s` (show print/log output)

## Troubleshooting

- **`ModuleNotFoundError: No module named 'kyro'`** — Install kyro in your active venv: `pip install -e .` or `pip install -e ".[dev]"`. Run examples from **repo root**: `python examples/fetch_orderbook_example.py` (not from `examples/` unless kyro is on `PYTHONPATH`).

- **`pytest: command not found`** — Use the project venv and `pip install -e ".[dev]"`; pytest is a dev dependency. Run `pytest tests/ -v` from **repo root** (the `tests/` directory is at the root, not inside `examples/`).

- **`error: externally-managed-environment`** — Create and activate a venv first; do not use `--break-system-packages`.

- **`ModuleNotFoundError: No module named 'cryptography'`** — Reinstall kyro so core deps are installed: `pip install -e .` or `pip install -e ".[dev]"`.

## What's tested

- **`test_config.py`** — `KyroConfig`: defaults, base_url, timeouts (bounds), headers, `model_post_init` (Accept), auth_headers.
- **`test_serialization.py`** — `dumps` / `loads` / `loads_model`: dict, list, Pydantic, nested, unicode, invalid JSON, validation errors, extra fields.
- **`test_exceptions.py`** — `KyroError`, `KyroHTTPError`, `KyroConnectionError`, `KyroTimeoutError`, `KyroValidationError` (message and attributes).
- **`test_rest_client.py`** — `RestClient`: context-manager requirement, GET 200/204, 4xx/5xx → `KyroHTTPError`, path normalization, GET params, POST/PUT/PATCH/DELETE with JSON, `response_model`, invalid JSON body → `KyroValidationError`, timeout → `KyroTimeoutError`.
- **`test_api_modules.py`** — `exchange`, `markets`, `events`, `orders`, `portfolio`: one or more functions per module against an in-process Kalshi-style fake server.

- **`scripts/live_api_smoke.py`** — live smoke: every endpoint/method against the real Kalshi **production** API. See **Live API smoke test** above.

Unit/integration tests use an in-process aiohttp app (`create_kalshi_app` in `conftest.py`); no real Kalshi or network. The live smoke script requires network access.

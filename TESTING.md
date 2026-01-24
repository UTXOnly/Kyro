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

Set `KALSHI_DEMO=1` (or `KALSHI_PRODUCTION=1`). For `get_balance` and `get_orders` benchmarks, also set `KALSHI_ACCESS_KEY` and `KALSHI_PRIVATE_KEY` or `KALSHI_PRIVATE_KEY_PATH`, and `pip install -e ".[dev,bench,auth]"`. See **[benchmarks/README.md](benchmarks/README.md)**.

## Live API smoke test

A step above unit tests: **`scripts/live_api_smoke.py`** calls every kyro endpoint and method against the real Kalshi API. Use it to verify the client and API paths with live data.

From **repo root** (venv activated, network required):

```bash
python scripts/live_api_smoke.py              # production (default)
KALSHI_DEMO=1 python scripts/live_api_smoke.py   # demo
```

To run auth-required endpoints: set ``KALSHI_ACCESS_KEY`` and ``KALSHI_PRIVATE_KEY`` or ``KALSHI_PRIVATE_KEY_PATH``. Install the auth extra: ``pip install -e ".[auth]"`` or, if you use dev deps, ``pip install -e ".[dev,auth]"``. (Using ``pip install "kyro[auth]"`` can fail with “does not provide the extra 'auth'” if kyro was originally installed without that extra; see Troubleshooting.)

- **ok** — request succeeded (200 or 404 for missing-by-id reads).
- **skip (auth required)** — 401 or 403; endpoint needs `KyroConfig(auth_headers={...})`.
- **skip (mutating)** — not called; would create/cancel/amend orders or change portfolio (create_order, cancel_order, amend_order, decrease_order, batch_*, create_subaccount, transfer_between_subaccounts).
- **fail** — 4xx/5xx (other than 401, 403, 404), connection error, or timeout.

The script exits with code 1 if any **fail**. Public endpoints (exchange, events, markets reads) should **ok** on production without auth; orders and portfolio will **skip (auth)** without API keys.

## Options

- **Stop on first failure:** `pytest tests/ -v -x`
- **Run a specific file:** `pytest tests/test_rest_client.py -v`
- **Run a specific test:** `pytest tests/test_rest_client.py::test_get_200_json -v`
- **Verbose logs:** `pytest tests/ -v -s` (show print/log output)

## Troubleshooting

- **`ModuleNotFoundError: No module named 'kyro'`** — Install kyro in your active venv: `pip install -e .` or `pip install -e ".[dev]"`. Run examples from **repo root**: `python examples/fetch_orderbook_example.py` (not from `examples/` unless kyro is on `PYTHONPATH`).

- **`pytest: command not found`** — Use the project venv and `pip install -e ".[dev]"`; pytest is a dev dependency. Run `pytest tests/ -v` from **repo root** (the `tests/` directory is at the root, not inside `examples/`).

- **`error: externally-managed-environment`** — Create and activate a venv first; do not use `--break-system-packages`.

- **`kyro 0.1.0 does not provide the extra 'auth'`** or **`ModuleNotFoundError: No module named 'cryptography'`** — The installed kyro was built before the `auth` extra existed, so its metadata and deps are stale. Reinstall with the auth extra: `pip uninstall kyro -y && pip install -e ".[dev,auth]"` (or `.[auth]` if you don’t need dev). Quick workaround: `pip install cryptography`.

## What's tested

- **`test_config.py`** — `KyroConfig`: defaults, base_url, timeouts (bounds), headers, `model_post_init` (Accept), auth_headers.
- **`test_serialization.py`** — `dumps` / `loads` / `loads_model`: dict, list, Pydantic, nested, unicode, invalid JSON, validation errors, extra fields.
- **`test_exceptions.py`** — `KyroError`, `KyroHTTPError`, `KyroConnectionError`, `KyroTimeoutError`, `KyroValidationError` (message and attributes).
- **`test_rest_client.py`** — `RestClient`: context-manager requirement, GET 200/204, 4xx/5xx → `KyroHTTPError`, path normalization, GET params, POST/PUT/PATCH/DELETE with JSON, `response_model`, invalid JSON body → `KyroValidationError`, timeout → `KyroTimeoutError`.
- **`test_api_modules.py`** — `exchange`, `markets`, `events`, `orders`, `portfolio`: one or more functions per module against an in-process Kalshi-style fake server.

- **`scripts/live_api_smoke.py`** — live smoke: every endpoint/method against the real Kalshi API (production or demo). See **Live API smoke test** above.

Unit/integration tests use an in-process aiohttp app (`create_kalshi_app` in `conftest.py`); no real Kalshi or network. The live smoke script requires network access.

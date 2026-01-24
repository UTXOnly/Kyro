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

## Options

- **Stop on first failure:** `pytest tests/ -v -x`
- **Run a specific file:** `pytest tests/test_rest_client.py -v`
- **Run a specific test:** `pytest tests/test_rest_client.py::test_get_200_json -v`
- **Verbose logs:** `pytest tests/ -v -s` (show print/log output)

## Troubleshooting

- **`ModuleNotFoundError: No module named 'kyro'`** — Install kyro in your active venv: `pip install -e .` or `pip install -e ".[dev]"`. Run examples from **repo root**: `python examples/fetch_orderbook_example.py` (not from `examples/` unless kyro is on `PYTHONPATH`).

- **`pytest: command not found`** — Use the project venv and `pip install -e ".[dev]"`; pytest is a dev dependency. Run `pytest tests/ -v` from **repo root** (the `tests/` directory is at the root, not inside `examples/`).

- **`error: externally-managed-environment`** — Create and activate a venv first; do not use `--break-system-packages`.

## What's tested

- **`test_config.py`** — `KyroConfig`: defaults, base_url, timeouts (bounds), headers, `model_post_init` (Accept), auth_headers.
- **`test_serialization.py`** — `dumps` / `loads` / `loads_model`: dict, list, Pydantic, nested, unicode, invalid JSON, validation errors, extra fields.
- **`test_exceptions.py`** — `KyroError`, `KyroHTTPError`, `KyroConnectionError`, `KyroTimeoutError`, `KyroValidationError` (message and attributes).
- **`test_rest_client.py`** — `RestClient`: context-manager requirement, GET 200/204, 4xx/5xx → `KyroHTTPError`, path normalization, GET params, POST/PUT/PATCH/DELETE with JSON, `response_model`, invalid JSON body → `KyroValidationError`, timeout → `KyroTimeoutError`.
- **`test_api_modules.py`** — `exchange`, `markets`, `events`, `orders`, `portfolio`: one or more functions per module against an in-process Kalshi-style fake server.

Tests use an in-process aiohttp app (`create_kalshi_app` in `conftest.py`) that mimics Kalshi routes; no real Kalshi or network.

# Benchmarks

Speed benchmarks for Kyro: serialization (Pydantic) and REST client round-trips against a **local mock Kalshi API**.

## Setup

From **repo root** with venv activated:

```bash
pip install -e ".[dev,bench]"
```

REST client benchmarks use a **local mock server** (no Kalshi credentials or network). Serialization benchmarks need no I/O.

## Run

```bash
pytest benchmarks/ -v --benchmark-only
```

Redirect to a file:

```bash
pytest benchmarks/ -v --benchmark-only > benchmark_results.txt 2>&1
```

Save/compare snapshots:

```bash
pytest benchmarks/ -v --benchmark-only --benchmark-save=baseline
pytest benchmarks/ -v --benchmark-only --benchmark-compare=baseline
```

## What's benchmarked

| File | Benchmarks |
|------|------------|
| `bench_serialization.py` | `dumps` (dict, Pydantic), `loads` (small/medium JSON), `loads_model` (Pydantic validation) |
| `bench_rest_client.py` | Local mock Kalshi API: `get_exchange_status`, `get_markets`, `get_events`, `get_market_orderbook`, `get_balance`, `get_orders` |

REST client benchmarks run against a mock server started in a background thread (`benchmarks.mock_server`). Results reflect **client overhead** (parsing, serialization, client logic) rather than network/API variance. You can increase rounds (e.g. `--benchmark-max-time=5`) for smoother results.

## Run only serialization (no network, no mock server)

```bash
pytest benchmarks/bench_serialization.py -v --benchmark-only
```

## Mock server standalone

Run the mock Kalshi API on a fixed port for manual or CI use:

```bash
MOCK_KALSHI_PORT=8765 python -m benchmarks
```

Or:

```bash
MOCK_KALSHI_PORT=8765 python -m benchmarks.mock_server
```

Or:

```bash
MOCK_KALSHI_PORT=8765 python benchmarks/mock_server.py
```

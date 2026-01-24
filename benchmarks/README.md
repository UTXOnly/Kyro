# Benchmarks

Speed benchmarks for Kyro: serialization (Pydantic) and REST client round-trips against the **live Kalshi API**.

## Setup

From **repo root** with venv activated:

```bash
pip install -e ".[dev,bench]"
```

For REST client benchmarks that need **auth** (balance, orders): also `pip install -e ".[dev,bench,auth]"` and set:

- `KALSHI_ACCESS_KEY` (or `KALSHI_ACCESS_KEY_ID`)
- `KALSHI_PRIVATE_KEY` or `KALSHI_PRIVATE_KEY_PATH`
- `KALSHI_DEMO=1` for demo, or `KALSHI_PRODUCTION=1` for production

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
| `bench_rest_client.py` | Live Kalshi API: `get_exchange_status`, `get_markets`, `get_events`, `get_market_orderbook`, `get_balance`, `get_orders` |

REST client benchmarks use `config_from_env(default_demo=True)` and the real Kalshi API (network required). Public endpoints (exchange, markets, events, orderbook) work without auth; `get_balance` and `get_orders` are skipped unless `KALSHI_ACCESS_KEY` and `KALSHI_PRIVATE_KEY` or `KALSHI_PRIVATE_KEY_PATH` are set.

## Run only serialization (no network)

```bash
pytest benchmarks/bench_serialization.py -v --benchmark-only
```

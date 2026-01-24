# Benchmarks

Speed benchmarks for Kyro in **two separate suites** so different concerns are not mixed:

- **Serialization** — pure CPU: `dumps`, `loads`, `loads_model` (Pydantic). Nanosecond–microsecond scale.
- **REST client** — HTTP round-trips to a **local mock Kalshi API**. Millisecond scale; reflects client overhead (parsing, serialization, client logic), not network or live API variance. No Kalshi credentials needed.

## Setup

From **repo root** with venv activated:

```bash
pip install -e ".[dev,bench]"
```

## Run

Run each suite separately so results stay comparable (serialization vs serialization, HTTP vs HTTP):

### Serialization only (no I/O, no mock server)

```bash
pytest benchmarks/bench_serialization.py -v --benchmark-only
```

### REST client only (uses mock server in background thread)

```bash
pytest benchmarks/bench_rest_client.py -v --benchmark-only
```

### Run both (separate reports; combined output mixes scales)

```bash
pytest benchmarks/ -v --benchmark-only
```

### Save results

```bash
pytest benchmarks/bench_serialization.py -v --benchmark-only > benchmark_serialization.txt 2>&1
pytest benchmarks/bench_rest_client.py -v --benchmark-only > benchmark_rest_client.txt 2>&1
```

### Compare over time (pytest-benchmark)

```bash
pytest benchmarks/bench_serialization.py -v --benchmark-only --benchmark-save=ser-baseline
pytest benchmarks/bench_serialization.py -v --benchmark-only --benchmark-compare=ser-baseline

pytest benchmarks/bench_rest_client.py -v --benchmark-only --benchmark-save=rest-baseline
pytest benchmarks/bench_rest_client.py -v --benchmark-only --benchmark-compare=rest-baseline
```

## What's benchmarked

| Suite | File | Benchmarks |
|-------|------|------------|
| **Serialization** | `bench_serialization.py` | `dumps` (dict, Pydantic), `loads` (small/medium JSON), `loads_model` (Pydantic validation) |
| **REST client** | `bench_rest_client.py` | Mock Kalshi: `get_exchange_status`, `get_markets`, `get_events`, `get_market_orderbook`, `get_balance`, `get_orders` |

REST client benchmarks use `benchmarks.mock_server` in a background thread. You can increase rounds (e.g. `--benchmark-max-time=5`) for smoother HTTP results.

---

## Sample results

Representative numbers from a single run. Regenerate with the commands above; actual values depend on hardware and Python version.

### Serialization

| Benchmark | Mean (µs) | OPS |
|-----------|-----------|-----|
| `test_dumps_dict` | 0.33 | ~3.0M |
| `test_loads_small` | 0.27 | ~3.7M |
| `test_dumps_pydantic` | 0.97 | ~1.0M |
| `test_loads_model_small` | 1.10 | ~910k |
| `test_loads_medium` | 3.06 | ~327k |
| `test_loads_model_nested` | 7.59 | ~132k |

### REST client (local mock server)

| Benchmark | Mean (ms) | OPS |
|-----------|-----------|-----|
| `test_get_exchange_status` | 78.6 | ~12.7 |
| `test_get_markets` | 81.6 | ~12.2 |
| `test_get_market_orderbook` | 146.8 | ~6.8 |
| `test_get_events` | 178.3 | ~5.6 |

*(`test_get_balance` and `test_get_orders` may be skipped if the mock does not expose those routes.)*

---

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

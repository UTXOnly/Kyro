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

Regenerate with the commands above; values depend on hardware and Python.

### Serialization

Each row is **one** `dumps` / `loads` / `loads_model` call. Mean and OPS are per-call from an isolated `bench_serialization` run. The high OPS (millions) is expected for small payloads on a modern CPU.

| Benchmark | Mean (µs) | OPS |
|-----------|-----------|-----|
| `test_dumps_dict` | 0.33 | ~3.0M |
| `test_loads_small` | 0.27 | ~3.7M |
| `test_dumps_pydantic` | 0.97 | ~1.0M |
| `test_loads_model_small` | 1.10 | ~910k |
| `test_loads_medium` | 3.06 | ~327k |
| `test_loads_model_nested` | 7.59 | ~132k |

### REST client (local mock server)

Each benchmark iteration runs **100 requests** with a **single** RestClient (one event loop, one aiohttp session). That amortizes loop/session create/teardown so the timed cost is HTTP + parsing + client logic.

#### Interpreting the raw pytest-benchmark output

The raw output is **not** per-request. Example:

```
Benchmark                    Mean (ms)   OPS
test_get_exchange_status     78.6        ~12.7
test_get_markets             81.6        ~12.2
test_get_market_orderbook    146.8       ~6.8
test_get_events              178.3       ~5.6
```

- **Mean** = time for **one round** = **100 requests**. It is not the time for a single request.
- **OPS** = rounds per second = 1 / Mean. It is **not** requests per second.

**Correct formulas:**

| What you want | Formula | Example (Mean 78.6 ms) |
|---------------|---------|------------------------|
| Per-request (ms) | `Mean / 100` | 78.6 / 100 = **0.79 ms** |
| Requests per second | `OPS × 100` | 12.7 × 100 = **~1,270** |

If Mean is shown in **ns** (e.g. 78_600_000): **per-request (ms) = Mean_ns / 1e6 / 100.**

#### Example per-request results (after applying the formula)

| Benchmark | Raw Mean (ms) | Per-request (ms) | Requests/sec |
|-----------|---------------|------------------|--------------|
| `test_get_exchange_status` | ~80 | ~0.8 | ~1,200 |
| `test_get_markets` | ~80 | ~0.8 | ~1,200 |
| `test_get_market_orderbook` | ~150 | ~1.5 | ~650 |
| `test_get_events` | ~180 | ~1.8 | ~560 |
| `test_get_balance` | ~80 | ~0.8 | ~1,200 |
| `test_get_orders` | ~80 | ~0.8 | ~1,200 |

*Run `pytest benchmarks/bench_rest_client.py -v --benchmark-only` and apply `Mean/100` (or `Mean_ns/1e6/100`) to get your per-request ms. The table above is illustrative for a modern machine; localhost with 100 req/round is typically ~0.8–2 ms per request and hundreds–thousands of requests/sec.*

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

# Examples

Standalone scripts that use the **kyro** client. The logic in these scripts (parsing, signals, etc.) is **not** part of kyro; kyro is a thin API client.

## `fetch_orderbook_example.py`

Fetches live Kalshi data: exchange status, a list of open markets, and one market’s orderbook. It parses the orderbook (best bid/ask, mid, spread, top-of-book size) and runs example “business logic” (e.g. tight spread, liquidity, skew).

**Run (from repo root, with kyro installed):**

```bash
pip install -e .   # or: pip install -e ".[dev]"
python examples/fetch_orderbook_example.py
```

Uses the **Kalshi demo API** by default (no API keys). Production may return 401 without auth.

**Use production instead of demo:**

```bash
KALSHI_PRODUCTION=1 python examples/fetch_orderbook_example.py
```

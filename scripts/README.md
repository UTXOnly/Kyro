# Scripts

## Live API smoke test

**`live_api_smoke.py`** calls every kyro endpoint against the real Kalshi API. It discovers an open market, runs all read and mutating calls, and writes every request/response to an audit log for review.

**Pass = 2xx only.** Any 4xx/5xx or exception is fail (we are not testing error handling).

### Run

From **repo root** (venv activated, network required):

```bash
cp .env.example .env   # edit with your production keys
pip install -e ".[dev]"
python scripts/live_api_smoke.py
```

Uses **production only** (`https://api.elections.kalshi.com/trade-api/v2`). Ignores `KALSHI_DEMO` / `KALSHI_BASE_URL` from `.env`.

### Auth

Auth is required. Put `KALSHI_ACCESS_KEY` and `KALSHI_PRIVATE_KEY` or `KALSHI_PRIVATE_KEY_PATH` in `.env` at project root. `KALSHI_PRIVATE_KEY_PATH` may be relative (e.g. `kal_key.pem` or `.kalshi/kal_key.pem`).

### Audit log

- **Path:** `live_smoke_audit.log` (or set `KALSHI_SMOKE_AUDIT_LOG`)
- **Location:** project root
- **Git:** `.gitignore`d

Each request/response is logged. On 400/404, `ERROR_RESPONSE` and `PATH_HINT` are written to aid diagnosis.

### Debug mode

Set `KALSHI_SMOKE_DEBUG=1` for extra output on failures:

- Path hints and full `response_body` on 4xx/5xx
- `request_info` and `ctx_keys` for each failing call
- Discovery try-log (get_market / get_market_candlesticks per ticker)

```bash
KALSHI_SMOKE_DEBUG=1 python scripts/live_api_smoke.py
```

### Discovery

Searches up to 100 open markets for one where `get_market` and `get_market_candlesticks` both return 200. If none, falls back to the first market where `get_market` returns 200.

### Mutating calls

Places 1-share limit orders @ 1¢, runs amend/cancel/decrease, batch create/cancel, subaccount create/transfer. All mutating endpoints are exercised.

The script exits with code 1 if any call **fails**.

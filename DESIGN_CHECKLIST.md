# Kyro design checklist

Use this to stay on track and prioritize work. Kyro = **async Kalshi API client** (library, not CLI).

---

## ✅ Done

- [x] **Project layout**: `src/kyro`, `pyproject.toml`, deps (aiohttp, pydantic).
- [x] **Exceptions**: `KyroError`, `KyroHTTPError`, `KyroConnectionError`, `KyroTimeoutError`, `KyroValidationError`.
- [x] **Config**: `KyroConfig` (base URL, timeouts, default headers, optional auth headers). Pydantic.
- [x] **Session**: `KyroSession` async context manager, owns `aiohttp.ClientSession`. Reusable for REST + WS.
- [x] **Serialization**: `dumps` / `loads` / `loads_model` (Pydantic only: model_dump_json, TypeAdapter, model_validate_json). Used by REST client.
- [x] **REST client**: `RestClient` async context manager. `get` / `post` / `put` / `patch` / `delete`. Optional `response_model`, `params`, `json` body. Kyro exceptions, Kalshi error parsing.
- [x] **Docs**: Module/client docstrings, README, DESIGN_CHECKLIST.
- [x] **Unit tests**: Pytest + pytest-asyncio. Serialization, config, exceptions, RestClient context-manager check.
- [x] **Modular API**: `kyro.rest` exports exchange, markets, events, orders, portfolio. **API_REFERENCE.md**: request/response docs for every method (exchange, markets, events, orders, portfolio). README links to it.

---

## 🔲 Next / later

- [ ] **Kalshi auth**: RSA-PSS signing (KALSHI-ACCESS-SIGNATURE). Helper to build `auth_headers` from key ID + private key.
- [ ] **WebSocket client**: Reuse `KyroConfig` / `KyroSession` (or shared session). Async iterator / handler for Kalshi WS streams.
- [ ] **Integration tests**: aiohttp test server + RestClient (e.g. pytest-aiohttp or aiohttp.test_utils).
- [ ] **CI**: Lint (ruff), tests, optional type check (pyright/mypy).
- [ ] **Optional models**: Pydantic models for common Kalshi types (Market, Order, etc.) in `kyro.models` or similar.

---

## Design notes

- **Library, not CLI**: No `argparse` / click; all usage is programmatic.
- **Reuse for WS**: `KyroSession` holds one `ClientSession`; REST uses it for HTTP, future WS uses same session for `ws_connect`.
- **Errors**: Always raise Kyro exceptions; map aiohttp / Kalshi errors into them.
- **JSON**: Pydantic only (no orjson or stdlib json). `dumps`: BaseModel→model_dump_json, dict/list→TypeAdapter.dump_json. `loads`: TypeAdapter(dict|list).validate_json for error bodies or until a response model exists. `loads_model`: model_validate_json. Prefer mapping all payloads to Pydantic models.

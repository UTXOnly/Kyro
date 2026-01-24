"""
Example: fetch real Kalshi market and orderbook data, parse the book, and run
example business logic.

This script is for demonstration only. The parsing and business logic below
are NOT part of the kyro library—kyro is a thin API client, not an SDK.

Run from the repo root (with kyro installed, e.g. `pip install -e .`):

    python examples/fetch_orderbook_example.py

Uses the Kalshi **demo** API by default (no auth). To use production:

    KALSHI_PRODUCTION=1 python examples/fetch_orderbook_example.py

Production may return 401 without API keys; the script will suggest trying
the demo or adding auth to KyroConfig.
"""

from __future__ import annotations

import asyncio
import os
import sys

from kyro import KyroConfig, RestClient
from kyro.exceptions import KyroHTTPError
from kyro.rest import exchange, markets


# -----------------------------------------------------------------------------
# Orderbook parsing (example logic — not part of kyro)
# -----------------------------------------------------------------------------

def parse_orderbook(data: dict) -> dict:
    """
    Parse Kalshi orderbook response into best bid/ask, mid, spread, and
    top-of-book liquidity. Yes bid at X ≡ no ask at 100-X.

    `orderbook.yes` / `orderbook.no`: list of [price_cents, quantity].
    Typically best-first (yes = yes bids, no = no bids).
    """
    ob = data.get("orderbook") or {}
    yes_levels = ob.get("yes") or []
    no_levels = ob.get("no") or []

    best_yes_bid = float(yes_levels[0][0]) if yes_levels else None
    best_no_bid = float(no_levels[0][0]) if no_levels else None

    # In a binary market: yes_ask ≈ 100 - no_bid, no_ask ≈ 100 - yes_bid
    best_yes_ask = (100.0 - best_no_bid) if best_no_bid is not None else None
    best_no_ask = (100.0 - best_yes_bid) if best_yes_bid is not None else None

    # Mid and spread in "yes" space (1–99 cents)
    if best_yes_bid is not None and best_yes_ask is not None:
        mid_yes = (best_yes_bid + best_yes_ask) / 2.0
        spread_yes = best_yes_ask - best_yes_bid
    else:
        mid_yes = spread_yes = None

    # Total quantity at top N levels (both sides)
    top_n = 5
    yes_qty = sum(int(y[1]) for y in yes_levels[:top_n])
    no_qty = sum(int(n[1]) for n in no_levels[:top_n])
    total_top_liquidity = yes_qty + no_qty

    return {
        "best_yes_bid": best_yes_bid,
        "best_yes_ask": best_yes_ask,
        "best_no_bid": best_no_bid,
        "best_no_ask": best_no_ask,
        "mid_yes": mid_yes,
        "spread_yes": spread_yes,
        "total_top_liquidity": total_top_liquidity,
        "yes_levels": len(yes_levels),
        "no_levels": len(no_levels),
    }


def run_example_business_logic(ticker: str, parsed: dict) -> None:
    """
    Example-only logic: label spread, liquidity, and skew. This is NOT
    part of kyro; it illustrates how an app might consume parsed data.
    """
    mid = parsed.get("mid_yes")
    spread = parsed.get("spread_yes")
    liq = parsed.get("total_top_liquidity") or 0

    print(f"\n  [example logic] {ticker}")
    if spread is not None:
        if spread <= 5:
            print(f"    -> Tight spread: {spread:.1f}¢ (<= 5¢)")
        else:
            print(f"    -> Spread: {spread:.1f}¢")
    if liq >= 500:
        print(f"    -> Liquid (top-5 size {liq} >= 500)")
    else:
        print(f"    -> Top-5 size: {liq}")
    if mid is not None:
        if mid >= 55:
            print(f"    -> Yes skewed: mid {mid:.1f}¢")
        elif mid <= 45:
            print(f"    -> No skewed: mid {mid:.1f}¢")
        else:
            print(f"    -> Mid: {mid:.1f}¢")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

async def main() -> None:
    use_production = os.environ.get("KALSHI_PRODUCTION", "").strip().lower() in ("1", "true", "yes")
    base = None if use_production else "https://demo-api.kalshi.co/trade-api/v2"
    cfg = KyroConfig(base_url=base) if base else KyroConfig()
    print(f"Using: {cfg.base_url}")

    try:
        async with RestClient(cfg) as client:
            # 1) Exchange status (optional: demo can 404; production can 401 without auth)
            try:
                status = await exchange.get_exchange_status(client)
                print(f"\nExchange: active={status.get('exchange_active')}, trading={status.get('trading_active')}")
            except KyroHTTPError as e:
                if e.status in (401, 404):
                    print(f"\nExchange status: not available ({e.status}), skipping.")
                else:
                    raise

            # 2) Pick an open market
            resp = await markets.get_markets(client, status="open", limit=5)
            ms = resp.get("markets") or []
            if not ms:
                resp = await markets.get_markets(client, limit=5)
                ms = resp.get("markets") or []
            if not ms:
                print("No markets returned. Exiting.")
                return

            ticker = ms[0].get("ticker") or "unknown"
            title = (ms[0].get("title") or "")[:60]
            print(f"\nMarket: {ticker}")
            print(f"  {title}")

            # 3) Orderbook
            ob_resp = await markets.get_market_orderbook(client, ticker, depth=10)
            parsed = parse_orderbook(ob_resp)
            print(f"\nOrderbook (parsed):")
            print(f"  best yes bid={parsed['best_yes_bid']}¢  best yes ask={parsed['best_yes_ask']}¢")
            print(f"  best no  bid={parsed['best_no_bid']}¢  best no  ask={parsed['best_no_ask']}¢")
            print(f"  mid={parsed['mid_yes']}¢  spread={parsed['spread_yes']}¢  top5_size={parsed['total_top_liquidity']}")

            # 4) Example business logic (not part of kyro)
            run_example_business_logic(ticker, parsed)
            print()
    except KyroHTTPError as e:
        if e.status == 401:
            print(
                "\nKalshi returned 401 (unauthorized). Production may require API keys.\n"
                "Try the demo (default):  python examples/fetch_orderbook_example.py\n"
                "Or set KyroConfig(auth_headers={...}) with KALSHI-ACCESS-KEY, etc.",
                file=sys.stderr,
            )
        raise


if __name__ == "__main__":
    asyncio.run(main())

"""
Example: fetch an event, a market, and an orderbook from Kalshi, then print.

Run from the repo root with kyro installed (venv activated, pip install -e . or .[dev]):

    python examples/fetch_orderbook_example.py

Uses the Kalshi **demo** API by default. For production:

    KALSHI_PRODUCTION=1 python examples/fetch_orderbook_example.py

Auth (optional): set KALSHI_ACCESS_KEY and KALSHI_PRIVATE_KEY or KALSHI_PRIVATE_KEY_PATH.
Public endpoints (events, markets, orderbook) do not need auth.

If you get ModuleNotFoundError: No module named 'kyro', install from repo root:
    pip install -e .   # or  pip install -e ".[dev]"
"""

from __future__ import annotations

import asyncio
import sys

from kyro import RestClient, config_from_env
from kyro.exceptions import KyroHTTPError
from kyro.rest import events, markets


def parse_orderbook(data: dict) -> dict:
    """Parse orderbook into best bid/ask, mid, spread, top-of-book size."""
    ob = data.get("orderbook") or {}
    yes_levels = ob.get("yes") or []
    no_levels = ob.get("no") or []

    best_yes_bid = float(yes_levels[0][0]) if yes_levels else None
    best_no_bid = float(no_levels[0][0]) if no_levels else None
    best_yes_ask = (100.0 - best_no_bid) if best_no_bid is not None else None
    best_no_ask = (100.0 - best_yes_bid) if best_yes_bid is not None else None

    if best_yes_bid is not None and best_yes_ask is not None:
        mid_yes = (best_yes_bid + best_yes_ask) / 2.0
        spread_yes = best_yes_ask - best_yes_bid
    else:
        mid_yes = spread_yes = None

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
    }


async def main() -> None:
    cfg = config_from_env(default_demo=True)  # demo by default for safety
    print(f"Using: {cfg.base_url}")

    try:
        async with RestClient(cfg) as client:
            # 1) Fetch an event
            resp = await events.get_events(client, limit=5, status="open")
            evs = resp.get("events") or []
            if not evs:
                resp = await events.get_events(client, limit=5)
                evs = resp.get("events") or []
            if not evs:
                print("No events returned. Exiting.")
                return

            ev = evs[0]
            event_ticker = ev.get("event_ticker") or ""
            title_ev = (ev.get("title") or "")[:60]
            print(f"\nEvent (event_ticker {event_ticker}):")
            print(f"  {title_ev}")

            # 2) Fetch markets for that event (an event can have multiple markets)
            resp = await markets.get_markets(
                client, event_ticker=event_ticker, limit=5, status="open"
            )
            ms = resp.get("markets") or []
            if not ms:
                resp = await markets.get_markets(client, event_ticker=event_ticker, limit=5)
                ms = resp.get("markets") or []
            if not ms:
                print("No markets for this event. Exiting.")
                return

            m = ms[0]
            ticker = m.get("ticker") or "unknown"
            title_m = (m.get("title") or "")[:60]
            print(f"\nMarket (ticker {ticker}):")
            print(f"  {title_m}")
            if ticker == event_ticker:
                print("  (single-market event: market ticker equals event_ticker)")

            # 3) Fetch orderbook and print
            ob_resp = await markets.get_market_orderbook(client, ticker, depth=10)
            parsed = parse_orderbook(ob_resp)
            print("\nOrderbook:")
            print(
                f"  best yes bid={parsed['best_yes_bid']}¢  best yes ask={parsed['best_yes_ask']}¢"
            )
            print(f"  best no  bid={parsed['best_no_bid']}¢  best no  ask={parsed['best_no_ask']}¢")
            print(
                f"  mid={parsed['mid_yes']}¢  spread={parsed['spread_yes']}¢  top5_size={parsed['total_top_liquidity']}"
            )
            print()
    except KyroHTTPError as e:
        if e.status == 401:
            print(
                "\n401 (unauthorized). Set KALSHI_ACCESS_KEY and KALSHI_PRIVATE_KEY (or KALSHI_PRIVATE_KEY_PATH) "
                "and use config_from_env().",
                file=sys.stderr,
            )
        raise


if __name__ == "__main__":
    asyncio.run(main())

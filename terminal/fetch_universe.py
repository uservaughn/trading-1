"""Assemble a broad, liquid US-equity universe from Yahoo's predefined screeners.

Only uses the public predefined-screener endpoint (no crumb, no auth). Unions
several liquidity/momentum lists, keeps NYSE/Nasdaq common stock, drops the
tiny and thin, and writes one ticker per line to terminal/universe_symbols.txt.
Per-symbol sector isn't available from this environment (Yahoo gates it behind a
crumb that 401s here), so downstream sector labels come from the curated map.
"""
from __future__ import annotations

import json
import pathlib
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 Chrome/126.0 Safari/537.36"}
OUT = pathlib.Path(__file__).with_name("universe_symbols.txt")

# Predefined Yahoo screener ids, each up to 250 names, unioned for breadth.
SCREENS = [
    "most_actives", "day_gainers", "day_losers",
    "growth_technology_stocks", "undervalued_large_caps",
    "undervalued_growth_stocks", "aggressive_small_caps",
    "small_cap_gainers", "most_shorted_stocks",
    "portfolio_anchors", "solid_large_growth_funds",
]
# Exchanges we treat as tradeable US listings.
KEEP_EXCH = {"NMS", "NGM", "NCM", "NYQ", "PCX", "ASE", "BATS", "NAS", "NYS"}


def fetch(scr: str, count: int = 250) -> list[dict]:
    url = ("https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
           f"?scrIds={urllib.parse.quote(scr)}&count={count}")
    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read()
        res = json.loads(raw)["finance"]["result"][0]
        return res.get("quotes", [])
    except Exception as exc:  # noqa: BLE001
        print(f"  {scr}: ERROR {type(exc).__name__}")
        return []


def main() -> None:
    seen: dict[str, dict] = {}
    for scr in SCREENS:
        quotes = fetch(scr)
        added = 0
        for q in quotes:
            sym = q.get("symbol", "")
            if not sym or q.get("quoteType") != "EQUITY":
                continue
            if q.get("exchange") not in KEEP_EXCH:
                continue
            if "." in sym or "-" in sym or len(sym) > 5:
                continue  # skip preferreds/warrants/units/foreign classes
            mc = q.get("marketCap") or 0
            adv = q.get("averageDailyVolume3Month") or 0
            if mc < 1e9 or adv < 3e5:
                continue  # liquidity floor: >=$1B cap and >=300k ADV
            if sym not in seen or mc > seen[sym]["mc"]:
                seen[sym] = {"mc": mc, "adv": adv}
            added += 1
        print(f"  {scr}: {len(quotes)} quotes, {added} kept (running unique {len(seen)})")
        time.sleep(0.6)

    syms = sorted(seen, key=lambda s: -seen[s]["mc"])
    OUT.write_text("\n".join(syms) + "\n")
    print(f"\nwrote {len(syms)} symbols -> {OUT}")
    print("top 20 by market cap:", " ".join(syms[:20]))


if __name__ == "__main__":
    main()

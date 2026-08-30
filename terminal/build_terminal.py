#!/usr/bin/env python3
"""Rebuild the Brain Terminal dashboard.

Pipeline: (optionally) refresh brain market data -> start the brain API on a
throwaway port -> pull its payloads -> join per-symbol features straight from
market.db -> inject the snapshot into template.html -> terminal/dist/brain-terminal.html.

    python3 terminal/build_terminal.py                # refresh data, then build
    python3 terminal/build_terminal.py --skip-data    # build from data already in the store
"""
import argparse, datetime as dt, json, os, sqlite3, subprocess, sys, time, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)
BRAIN = os.path.join(REPO, "brain")
DB = os.path.join(BRAIN, "data_cache", "market.db")
PORT = int(os.environ.get("TERMINAL_API_PORT", "8790"))
OUT = os.path.join(ROOT, "dist", "brain-terminal.html")

sys.path.insert(0, BRAIN)


def refresh_data():
    subprocess.run([sys.executable, "-m", "tradingbrain.cli", "data", "bootstrap"],
                   cwd=BRAIN, check=True)


def fetch_api():
    srv = subprocess.Popen([sys.executable, "-m", "tradingbrain.cli", "serve",
                            "--host", "127.0.0.1", "--port", str(PORT)],
                           cwd=BRAIN, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    handler = urllib.request.ProxyHandler({})  # never route localhost through a proxy
    opener = urllib.request.build_opener(handler)
    try:
        for _ in range(60):
            try:
                opener.open(f"http://127.0.0.1:{PORT}/api/status", timeout=2)
                break
            except OSError:
                time.sleep(0.5)
        else:
            raise RuntimeError("brain API did not come up")
        out = {}
        for ep in ("dashboard", "regime", "sectors", "themes", "scan", "research", "risk/guards"):
            with opener.open(f"http://127.0.0.1:{PORT}/api/{ep}", timeout=120) as r:
                out[ep.replace("/", "_")] = json.load(r)
        return out
    finally:
        srv.terminate()
        srv.wait(timeout=10)


def build_snapshot(api):
    from tradingbrain.data.providers.synthetic import THEMES, SECTOR_ETF, UNIVERSE_SPEC

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    sym_ids = {r["symbol"]: r["id"] for r in db.execute("SELECT id, symbol FROM symbols")}
    ids_sym = {v: k for k, v in sym_ids.items()}

    series = {}
    for r in db.execute("SELECT symbol_id, ts, close, volume FROM market_data_daily ORDER BY ts"):
        d = dt.datetime.fromtimestamp(r["ts"], dt.timezone.utc).strftime("%Y-%m-%d")
        series.setdefault(r["symbol_id"], []).append((d, r["close"], r["volume"]))

    def ret(closes, n):
        if len(closes) <= n:
            return None
        prev = closes[-1 - n][1]
        return round((closes[-1][1] / prev - 1) * 100, 2) if prev else None

    def ytd(closes):
        year = closes[-1][0][:4]
        prior = [c for c in closes if c[0][:4] < year]
        if not prior:
            return None
        base = prior[-1][1]
        return round((closes[-1][1] / base - 1) * 100, 2) if base else None

    feat = {}
    for r in db.execute("""
        SELECT sf.* FROM strategy_features sf
        JOIN (SELECT symbol_id, MAX(ts) mts FROM strategy_features
              WHERE timeframe='1d' GROUP BY symbol_id) m
          ON m.symbol_id = sf.symbol_id AND m.mts = sf.ts
        WHERE sf.timeframe='1d'"""):
        feat[r["symbol_id"]] = dict(r)

    sym_themes = {}
    for th, members in THEMES.items():
        for m in members:
            sym_themes.setdefault(m, []).append(th)

    etfs = set(SECTOR_ETF.values()) | {"SPY", "QQQ"}
    rows = []
    for sid, closes in series.items():
        sym = ids_sym.get(sid)
        if not sym or len(closes) < 30:
            continue
        f = feat.get(sid, {})
        spec = UNIVERSE_SPEC.get(sym)
        sector = spec[0] if spec else ("Index/ETF" if sym in etfs else "Other")
        vols = [c[2] for c in closes[-51:-1]]
        avgvol = sum(vols) / len(vols) if vols else None
        g = lambda k, dp=2: round(f[k], dp) if f.get(k) is not None else None
        rows.append({
            "sym": sym, "sector": sector, "themes": sym_themes.get(sym, []),
            "etf": sym in etfs, "close": round(closes[-1][1], 2),
            "d1": ret(closes, 1), "w1": ret(closes, 5), "m1": ret(closes, 21),
            "m3": ret(closes, 63), "m6": ret(closes, 126), "ytd": ytd(closes),
            "rvol": round(closes[-1][2] / avgvol, 2) if avgvol else None,
            "rs": g("relative_strength_pct", 1), "p52": g("pct_from_52w_high", 1),
            "adr": g("adr20"), "dvol": round((f.get("dollar_volume_20d") or 0) / 1e6, 1),
            "a10": f.get("above_10sma"), "a20": f.get("above_20sma"),
            "a50": f.get("above_50sma"), "a200": f.get("above_200sma"),
            "stack": f.get("sma_stack_10_20_50"), "baseq": g("base_quality", 1),
            "qual": f.get("base_qualifies"), "bdist": g("breakout_distance_pct"),
            "cdays": f.get("consolidation_days"),
            "spark": [round(c[1], 2) for c in closes[-64:]],
        })

    def group_rets(members):
        out = {}
        for key, n in (("d1", 1), ("w1", 5), ("m1", 21), ("m3", 63)):
            vals = [ret(series[sym_ids[m]], n) for m in members
                    if m in sym_ids and len(series.get(sym_ids[m], [])) > n]
            vals = [v for v in vals if v is not None]
            out[key] = round(sum(vals) / len(vals), 2) if vals else None
        vals = [ytd(series[sym_ids[m]]) for m in members
                if m in sym_ids and series.get(sym_ids[m])]
        vals = [v for v in vals if v is not None]
        out["ytd"] = round(sum(vals) / len(vals), 2) if vals else None
        return out

    def slim_group(g):
        return {"name": g["name"], "members": g["members"], "score": g["score"],
                "rank": g["rank"], "leaders": g["leaders"][:5],
                "rets": group_rets(g["members"]),
                "pct_above_50": g["components"]["pct_above_50sma"],
                "pct_near_hi": g["components"]["pct_near_52w_high"]}

    regime, dash, scan = api["regime"], api["dashboard"], api["scan"]
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "as_of": api["themes"]["as_of"],
        "data_origin": dash.get("data_origin"),
        "data_note": dash.get("data_note"),
        "regime": {k: regime[k] for k in ("as_of", "label", "volatility_label", "strength",
                                          "breadth", "filter_pass", "filter_detail", "components")},
        "indexes": {s: {"close": round(regime["indexes"][s]["close"], 2),
                        "dd": round(regime["indexes"][s]["drawdown_pct"], 2),
                        "vol": round(regime["indexes"][s]["realized_vol_annual_pct"], 1),
                        "label": regime["indexes"][s]["label"],
                        "d1": ret(series[sym_ids[s]], 1), "ytd": ytd(series[sym_ids[s]]),
                        "spark": [[c[0], round(c[1], 2)] for c in series[sym_ids[s]][-128:]]}
                    for s in ("SPY", "QQQ") if s in sym_ids and s in regime["indexes"]},
        "themes": [slim_group(g) for g in api["themes"]["ranks"]],
        "sectors": [slim_group(g) for g in api["sectors"]["ranks"]],
        "rows": rows,
        "scan": {"strategy": scan["strategy"], "as_of": scan["as_of"], "weights": scan["weights"],
                 "symbols_scanned": scan["symbols_scanned"],
                 "candidates_found": scan["candidates_found"],
                 "breakouts_today": scan["breakouts_today"], "approaching": scan["approaching"],
                 "candidates": [
                     {"symbol": c["symbol"], "state": c["state"], "score": c["score"],
                      "components": {k: {"score": round(v["score"], 1), "weight": v["weight"],
                                         "contribution": round(v["contribution"], 2),
                                         "note": v["note"]}
                                     for k, v in c["components"].items()},
                      "detail": {k: v for k, v in c.items()
                                 if k not in ("components", "symbol", "state", "score", "date")}}
                     for c in scan.get("results", [])]},
        "research": api["research"],
        "guards": api["risk_guards"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-data", action="store_true",
                    help="build from the data already in market.db")
    args = ap.parse_args()
    if not args.skip_data:
        refresh_data()
    api = fetch_api()
    snap = build_snapshot(api)
    tpl = open(os.path.join(ROOT, "template.html")).read()
    payload = json.dumps(snap).replace("</", "<\\/")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write(tpl.replace("__SNAPSHOT_JSON__", payload))
    print(f"{OUT}  {os.path.getsize(OUT)/1024:.0f} KB  as_of {snap['as_of']}  "
          f"{len(snap['rows'])} symbols")


if __name__ == "__main__":
    main()

# trading-1
Vaughn's trading journey

---

## What's in this repo

This repository holds one thing: the **AI Trading Brain** in [`brain/`](brain/README.md)
— a quantitative research and decision-support platform.

It is not a signal service. It turns trading beliefs into measurable rules,
tests those rules against historical data, and reports the result honestly.
Every number it produces carries an evidence class (`SOURCE_FACT`,
`INFERENCE`, `HYPOTHESIS`, `BACKTEST_RESULT`, `LIVE_MARKET_OBSERVATION`,
`MODEL_ESTIMATE`) and no number is allowed to change class silently.

The platform ships a CLI for seeding the knowledge base, bootstrapping market
data and running experiments, plus a local web UI for browsing the results.

### AI Trading Brain — quick start

```
cd brain
python3 -m pip install -r requirements.txt   # numpy is the only hard dependency
python3 -m tradingbrain.cli seed             # knowledge base, concepts, hypotheses
python3 -m tradingbrain.cli data bootstrap   # universe -> history -> features -> context
python3 -m tradingbrain.cli serve            # http://127.0.0.1:8787
```

Tests:

```
cd brain && python3 -m pytest
```

See [`brain/README.md`](brain/README.md) for the evidence-class system that
governs every number the platform reports, and [`brain/ARCHITECTURE.md`](brain/ARCHITECTURE.md)
for how the pieces fit together.

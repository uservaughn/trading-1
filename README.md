# trading-1
Vaughn's trading journey

---

## What's in this repo

Imported from the `proj-1` repository (branch `claude/ai-trading-brain-build-pi2rv3`),
which is being retired. Everything below moved here intact.

| Path | What it is |
|---|---|
| [`brain/`](brain/README.md) | **AI Trading Brain** — quantitative research and decision-support platform. Start here. |
| [`service/`](service/) | Blankd Web Studio — flat-rate website service: landing page, demo sites, outreach templates and pipeline. |
| [`flipfinder/`](flipfinder/README.md) | eBay deal-scanner that finds underpriced listings and does the margin math. |
| [`tracker/`](tracker/) | Simple income/expense ledger with a monthly P&L summary script. |
| [`docs/proj-1-overview.md`](docs/proj-1-overview.md) | The original `proj-1` root README, preserved unchanged in substance. |
| Root `*.md` | Planning and review notes carried over: `PLAN.md`, `GOALS.md`, `DECISIONS.md`, `SCHEDULE.md`, `SCORECARD.md`, and others. |

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

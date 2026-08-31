# Brain Terminal

A Deepvue-inspired dashboard over the AI Trading Brain: theme/sector trackers,
a 96-symbol screener, the SAR momentum scanner and the research lab, rendered
as one self-contained HTML file.

Published as a Claude artifact:
https://claude.ai/code/artifact/723c1b49-8fcc-445e-8ce7-e19730876a03

## Rebuild

```
python3 terminal/build_terminal.py              # refresh market data, then build
python3 terminal/build_terminal.py --skip-data  # reuse data already in the store
```

Output: `terminal/dist/brain-terminal.html` — open it locally, or republish it
to the artifact URL above to update the hosted copy.

The build refreshes the brain's market store (`cli data bootstrap`), starts the
brain API on a throwaway port (default 8790, override with `TERMINAL_API_PORT`),
snapshots its payloads plus per-symbol features from `market.db`, and injects
the JSON into `template.html`.

Everything on the page carries the brain's provenance: when the store was fed by
the synthetic generator (the case in environments with no market-data egress),
the page shows a SYNTHETIC DATA badge and the numbers are not evidence about
real markets.

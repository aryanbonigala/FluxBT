# fluxbt Usage Guide

This guide explains how to install, run, and get the most out of fluxbt, including limitations to keep in mind.

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

Optional: to enable HTML reporting, install jinja2 (installed by default via extras):

```bash
pip install jinja2
```

## Quickstart (CLI)

Run a backtest from yfinance data:

```bash
python -m fluxbt.cli \
  --source yfinance --ticker SPY --interval 1d --start 2015-01-01 \
  --strategy sma --fast 20 --slow 50 \
  --cash 100000 --slippage-bps 1 --commission-bps 2 \
  --out ./runs/spy_sma_20_50 --html-report
```

Run a backtest from CSV data:

```bash
python -m fluxbt.cli \
  --source csv --csv-path path/to/ohlcv.csv \
  --strategy meanrev --window 20 --entry 2.0 --exit 0.5 \
  --cash 100000 --slippage-bps 1 --commission-bps 2 \
  --out ./runs/csv_mr
```

CLI options:
- `--source`: `csv` or `yfinance`
- `--csv-path`: path to CSV with columns `Date|Datetime`, `Open`, `High`, `Low`, `Close`, `Volume`
- `--ticker`, `--interval`, `--start`, `--end`: yfinance parameters
- `--strategy`: `sma` or `meanrev`
- Strategy-specific params: SMA (`--fast`, `--slow`, `--long-only`), Mean Reversion (`--window`, `--entry`, `--exit`, `--allow-short`, optional `--cooldown`)
- Common params: `--size-pct`, `--cash`, `--slippage-bps`, `--commission-bps`, `--out`, `--html-report`

Outputs are saved to `--out` or `./runs/<timestamp>/` and include:
- `history.csv` (ts, price, position, cash, equity, drawdown)
- `equity.png`, `drawdown.png`
- `report.html` (if `--html-report` and jinja2 installed)

## Quickstart (API)

```python
from fluxbt.data.loader import YFinanceLoader
from fluxbt.data.feed import DataFeed
from fluxbt.core.broker import Broker
from fluxbt.core.engine import BacktestEngine
from fluxbt.core.metrics import compute_metrics
from fluxbt.strategies.sma_crossover import SMACrossover

# Load data
df = YFinanceLoader(ticker="SPY", interval="1d", start="2015-01-01").load()
feed = DataFeed(df)

# Run engine
engine = BacktestEngine(feed=feed, broker=Broker(), strategy=SMACrossover())
hist = engine.run()
metrics = compute_metrics(hist["equity"], freq="D")
```

## Getting the most out of fluxbt

- Keep it simple: start with clean daily data and basic params; iterate once the pipeline runs end-to-end.
- Validate data: ensure monotonic `DatetimeIndex` and columns `open, high, low, close, volume` (the loaders normalize common names).
- Use `--out` directories per experiment to keep runs organized.
- Compare strategies consistently: fix `--cash`, `--slippage-bps`, and `--commission-bps` when comparing.
- Volatility: consider scaling position size externally (risk module helpers available) or via strategy logic.
- Reproducibility: pin input ranges (`--start/--end`), record results (`history.csv`), and log config in your own notes or `CHANGELOG.md`.

## Limitations

- Single-asset only: no multi-asset portfolios yet.
- Simple execution model: market orders with slippage/commission bps; no partial fills or advanced order types beyond basic LIMIT structure.
- No intraday market microstructure: signals evaluated per bar; fills use bar close ± slippage.
- Strategy state is in-memory and per-backtest: no warm-start beyond bars provided.
- Metrics are equity-curve based; trade attribution (win/lose per trade) is simplistic via returns; extend as needed.
- yfinance schema variability: we normalize common shapes, but if Yahoo changes formats, CSV loader offers a robust fallback.
- HTML report optional: requires jinja2; skipped otherwise.

## Troubleshooting

- Import errors: activate the venv and reinstall: `pip install -e ".[dev]"`
- Matplotlib on servers/CI: set `MPLBACKEND=Agg` (CI already does this).
- yfinance issues: try a known ticker/interval (`SPY`, `1d`), or use the CSV path instead.
- Lint/format/type: run `ruff check .`, `black --check .`, `mypy .` to diagnose code issues.

## Extending

- Add a new strategy: create `fluxbt/strategies/<name>.py`, implement `Strategy` interface (`reset`, `on_bar`, `params`), export in `fluxbt/strategies/__init__.py`, and wire in `fluxbt/cli.py`.
- Add metrics: extend `fluxbt/core/metrics.py` and surface new values in CLI/report if needed.
- Enhance broker: adjust slippage/commission logic or add order types in `fluxbt/core/broker.py`.

# FluxBT: A Minimal Python Backtesting Framework: A Minimal Python Backtesting Framework

![CI](https://github.com/aryanbonigala/Backtesting-Framework-SP/actions/workflows/ci.yml/badge.svg)

FluxBT is a clean, modular, single-asset backtesting framework targeting students, researchers, and entry-level quants. It provides a simple pipeline:

```
Data (OHLCV) → Strategy Signals → Orders → Simulated Execution (Broker) → Portfolio → Metrics → Plots/Reports → CLI
```

### Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

### Quickstart (CLI)

```bash
python -m FluxBT: A Minimal Python Backtesting Framework.cli run \
  --source yfinance --ticker SPY --interval 1d --start 2015-01-01 \
  --strategy sma --fast 20 --slow 50 \
  --cash 100000 --slippage-bps 1 --commission-bps 2 \
  --out ./runs/spy_sma_20_50 --html-report
```

Mean Reversion example:

```bash
python -m FluxBT: A Minimal Python Backtesting Framework.cli run \
  --source yfinance --ticker QQQ --interval 1d --start 2015-01-01 \
  --strategy meanrev --window 20 --entry 2.0 --exit 0.5 \
  --cash 100000 --slippage-bps 1 --commission-bps 2 \
  --out ./runs/qqq_mr_20_2_05 --html-report
```

### Quickstart (Notebook)

See `examples/example_sma.ipynb` and `examples/example_mean_reversion.ipynb` for end-to-end runs.

### Features & Architecture

- Data loaders: CSV and yfinance, normalized OHLCV
- Strategies: SMA crossover, Mean Reversion (z-score)
- Orders: MARKET/LIMIT, quantities as shares, `PCT:x`, or `CLOSE`
- Broker: slippage (bps), commission (bps)
- Portfolio: cash, position, avg cost, realized PnL, equity, drawdown
- Engine: bar-by-bar loop, position management, history tracking
- Metrics: total return, CAGR, vol, Sharpe, max DD, Calmar, hit rate, avg win/loss, profit factor
- Reporting: matplotlib plots; optional HTML with jinja2
- CLI: Typer interface for repeatable runs

### Example Outputs

Outputs (plots, history CSV, optional HTML) are saved under `./runs/<timestamp>/` or a provided `--out` directory.

### Testing & Quality

Run locally:

```bash
ruff check .
black --check .
mypy .
pytest -q
```

### CI

GitHub Actions workflow runs on Python 3.11 and 3.12: lint (ruff), format check (black), type check (mypy), tests with coverage and uploads `coverage.xml` as an artifact. See `.github/workflows/ci.yml`.

### Roadmap

- Multi-asset support
- Paper trading adapter
- Parameter sweeps/grid search

### License

MIT



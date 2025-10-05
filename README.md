# FluxBT: A Minimal Python Backtesting Framework

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

### Table of Contents

- [Install](#install)
- [Quickstart (CLI)](#quickstart-cli)
- [Quickstart (Notebook)](#quickstart-notebook)
- [Features & Architecture](#features--architecture)
- [Run a Strategy from GitHub (Dynamic Loader)](#run-a-strategy-from-github-dynamic-loader)
- [Example Outputs](#example-outputs)
- [Testing & Quality](#testing--quality)
- [CI](#ci)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Code of Conduct](#code-of-conduct)
- [Security](#security)
- [License](#license)

### Quickstart (CLI)

```bash
python -m fluxbt.cli run \
  --source yfinance --ticker SPY --interval 1d --start 2015-01-01 \
  --strategy sma --fast 20 --slow 50 \
  --cash 100000 --slippage-bps 1 --commission-bps 2 \
  --out ./runs/spy_sma_20_50 --html-report
```

Mean Reversion example:

```bash
python -m fluxbt.cli run \
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
- Dynamic strategy loading from GitHub via `run_github` (no code changes required)

### Run a Strategy from GitHub (Dynamic Loader)

You can fetch a strategy file directly from a public GitHub repo and run a backtest without modifying your codebase.

Security warning: This downloads and executes remote Python code. Only use trusted sources.

Example:

```bash
python -m fluxbt.cli run_github \
  --source yfinance --ticker SPY --interval 1d \
  --repo quantresearch/alpha-strategies \
  --path strategies/momentum.py \
  --branch main \
  --class-name Momentum
```

If `--class-name` is omitted, FluxBT will auto-detect a single subclass of `BaseStrategy` in the file.

#### Template for external strategies (optional metadata)

External strategies can optionally declare `supported_intervals` and `required_columns` to make runs more robust without modifying strategy logic. These are read by the CLI and enforced before the backtest starts.

```python
from __future__ import annotations

import pandas as pd
from fluxbt.strategies import BaseStrategy
from fluxbt.core.orders import Order


class Momentum(BaseStrategy):
    # Optional hints consumed by FluxBT CLI (no effect on strategy logic)
    supported_intervals = ["1d", "1h"]  # e.g., supported yfinance intervals
    required_columns = ["close", "volume"]  # minimal columns needed by this strategy

    def __init__(self, lookback: int = 20, size_pct: float = 0.1) -> None:
        self.lookback = lookback
        self.size_pct = size_pct
        self._prices: list[float] = []

    @property
    def name(self) -> str:
        return "momentum"

    @property
    def params(self) -> dict[str, object]:
        return {"lookback": self.lookback, "size_pct": self.size_pct}

    def reset(self) -> None:
        self._prices = []

    def on_bar(self, ts: pd.Timestamp, bar: dict[str, float]) -> list[Order]:
        # implement your logic; use only fields you truly need
        self._prices.append(bar["close"])  # volume available if needed
        return []
```

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

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

### Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

### Security

See [SECURITY.md](SECURITY.md).



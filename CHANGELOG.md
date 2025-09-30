# Changelog

This file tracks notable changes to the project. Add new entries at the top.

Format guidance:
- Use UTC timestamps (YYYY-MM-DD HH:MM UTC)
- Keep bullets concise and high-signal
- Reference affected modules/files where useful

## 2025-09-30 16:00 UTC
- Initial scaffold of quantbt backtesting framework
- Data: CSV and yfinance loaders; `DataFeed` with validation
- Core: `orders`, `portfolio`, `broker`, `engine`, `metrics`, `risk`, `utils`
- Strategies: SMA Crossover, Mean Reversion
- Reports: plotting and optional HTML (gracefully skipped if jinja2 missing)
- CLI: Typer command for end-to-end runs
- Tests: unit tests for orders, portfolio, engine, metrics (pytest passing)
- Tooling: ruff, black, mypy, pre-commit; GitHub Actions CI

## How to add a new entry
- Add a new `## YYYY-MM-DD HH:MM UTC` section
- Summarize changes in bullets (components/files affected)
- Optionally include PR numbers or commit SHAs once hosted on GitHub

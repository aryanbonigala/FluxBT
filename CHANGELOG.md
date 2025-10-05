# Changelog

This file tracks notable changes to the project. Add new entries at the top.

Format guidance:
- Use UTC timestamps (YYYY-MM-DD HH:MM UTC)
- Keep bullets concise and high-signal
- Reference affected modules/files where useful

## 2025-10-05 00:00 UTC
- Feature: Dynamic GitHub strategy loading via new `run_github` CLI command
  - Added `fluxbt/strategies/remote_loader.py` to fetch and load strategies from public GitHub repos
  - Introduced `BaseStrategy` (kept `Strategy` alias for backward compatibility)
  - Added optional validations in CLI: `supported_intervals`, `required_columns` (no strategy code changes)
  - Added security warning for executing remote code
  - Docs: README updates with usage examples and external strategy template
  - Tooling: added `httpx` dependency for fetching; governance docs; pre-commit config

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

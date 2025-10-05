# Contributing

Thanks for your interest in contributing!

## Setup
- Python 3.11+
- Create a venv and install dev deps:
  ```bash
  python -m venv .venv && source .venv/bin/activate
  pip install -e ".[dev]"
  pre-commit install
  ```

## Workflow
- Create a feature branch.
- Run linters and tests locally:
  ```bash
  ruff check . && black --check . && mypy . && pytest -q
  ```
- Submit a PR with a clear description and rationale.

## Guidelines
- Keep functions small and readable.
- Add/maintain type hints.
- Include/extend tests when changing behavior.
- Update docs/README if user-facing behavior changes.

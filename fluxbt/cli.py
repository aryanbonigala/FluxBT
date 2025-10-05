from __future__ import annotations

import os
from datetime import datetime

import typer

from .data.loader import CSVLoader, YFinanceLoader
from .data.feed import DataFeed
from .core.broker import Broker
from .core.engine import BacktestEngine
from .core.metrics import compute_metrics
from .reports.plotting import plot_drawdown, plot_equity_curve
from .strategies.base import Strategy
from .strategies.sma_crossover import SMACrossover
from .strategies.mean_reversion import MeanReversion
from .strategies import load_github_strategy, StrategyLoadError


app = typer.Typer(help="fluxbt CLI")


@app.command()
def run(
    source: str = typer.Option(..., help="Data source: 'csv' or 'yfinance'"),
    csv_path: str | None = typer.Option(None, help="Path to CSV for --source csv"),
    ticker: str | None = typer.Option(None, help="Ticker for yfinance"),
    interval: str = typer.Option("1d", help="Interval for yfinance"),
    start: str | None = typer.Option(None, help="Start date for yfinance"),
    end: str | None = typer.Option(None, help="End date for yfinance"),
    strategy: str = typer.Option(..., help="Strategy: 'sma' or 'meanrev'"),
    # SMA params
    fast: int = 20,
    slow: int = 50,
    long_only: bool = True,
    # Mean Reversion params
    window: int = 20,
    entry: float = 2.0,
    exit: float = 0.5,
    allow_short: bool = True,
    # Common
    size_pct: float = 0.1,
    cooldown: int = 0,
    cash: float = 100000.0,
    slippage_bps: float = 1.0,
    commission_bps: float = 0.0,
    out: str | None = typer.Option(None, help="Output directory"),
    html_report: bool = typer.Option(
        False, "--html-report/--no-html-report", help="Generate HTML report"
    ),
) -> None:
    if source == "csv":
        if not csv_path:
            raise typer.BadParameter("csv_path required for --source csv")
        df = CSVLoader(csv_path).load()
    elif source == "yfinance":
        if not ticker:
            raise typer.BadParameter("ticker required for --source yfinance")
        df = YFinanceLoader(ticker=ticker, interval=interval, start=start, end=end).load()
    else:
        raise typer.BadParameter("source must be 'csv' or 'yfinance'")

    feed = DataFeed(df)
    broker = Broker(slippage_bps=slippage_bps, commission_bps=commission_bps)

    strat: Strategy
    if strategy == "sma":
        strat = SMACrossover(
            fast=fast, slow=slow, size_pct=size_pct, cooldown=cooldown, long_only=long_only
        )
    elif strategy == "meanrev":
        strat = MeanReversion(
            window=window,
            entry=entry,
            exit=exit,
            size_pct=size_pct,
            cooldown=cooldown,
            allow_short=allow_short,
        )
    else:
        raise typer.BadParameter("strategy must be 'sma' or 'meanrev'")

    engine = BacktestEngine(feed=feed, broker=broker, strategy=strat, initial_cash=cash)
    hist = engine.run()
    equity = hist["equity"]
    drawdown = (equity / equity.cummax() - 1.0).fillna(0.0)
    metrics = compute_metrics(equity, freq="D")

    ts_dir = out or os.path.join("runs", datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(ts_dir, exist_ok=True)
    hist.to_csv(os.path.join(ts_dir, "history.csv"))

    plot_equity_curve(equity, savepath=os.path.join(ts_dir, "equity.png"))
    plot_drawdown(drawdown, savepath=os.path.join(ts_dir, "drawdown.png"))

    typer.echo("Metrics:")
    for k, v in metrics.items():
        typer.echo(f"  {k}: {v:.6f}" if v == v else f"  {k}: nan")

    if html_report:
        try:
            from .reports.report import generate_html_report

            params: dict[str, object] = {"strategy": strategy, **strat.params}
            report_path = generate_html_report(
                params=params, metrics=metrics, equity=equity, out_dir=ts_dir
            )
            if report_path:
                typer.echo(f"HTML report saved to: {report_path}")
        except Exception:
            typer.echo("jinja2 not installed or report generation failed; skipping HTML report.")

    typer.echo(f"Outputs saved in: {ts_dir}")


@app.command()
def run_github(
    source: str = typer.Option(..., help="Data source: 'csv' or 'yfinance'"),
    csv_path: str | None = typer.Option(None, help="Path to CSV for --source csv"),
    ticker: str | None = typer.Option(None, help="Ticker for yfinance"),
    interval: str = typer.Option("1d", help="Interval for yfinance"),
    start: str | None = typer.Option(None, help="Start date for yfinance"),
    end: str | None = typer.Option(None, help="End date for yfinance"),
    repo: str = typer.Option(..., help="GitHub repo in 'owner/repo' format"),
    path: str = typer.Option(..., help="Path to strategy file in the repo"),
    branch: str = typer.Option("main", help="Git branch or tag"),
    class_name: str | None = typer.Option(None, help="Optional strategy class name"),
    cash: float = 100000.0,
    slippage_bps: float = 1.0,
    commission_bps: float = 0.0,
    out: str | None = typer.Option(None, help="Output directory"),
    html_report: bool = typer.Option(
        False, "--html-report/--no-html-report", help="Generate HTML report"
    ),
) -> None:
    # Security notice
    typer.echo(
        "WARNING: You are about to fetch and execute Python code from the internet. "
        "Proceed only if you trust the source."
    )

    if source == "csv":
        if not csv_path:
            raise typer.BadParameter("csv_path required for --source csv")
        df = CSVLoader(csv_path).load()
    elif source == "yfinance":
        if not ticker:
            raise typer.BadParameter("ticker required for --source yfinance")
        df = YFinanceLoader(ticker=ticker, interval=interval, start=start, end=end).load()
    else:
        raise typer.BadParameter("source must be 'csv' or 'yfinance'")

    feed = DataFeed(df)
    broker = Broker(slippage_bps=slippage_bps, commission_bps=commission_bps)

    try:
        try:
            owner, repo_name = repo.split("/", 1)
        except ValueError as exc:
            raise typer.BadParameter("--repo must be in 'owner/repo' format") from exc
        strat = load_github_strategy(
            owner=owner, repo=repo_name, file_path=path, branch=branch, class_name=class_name
        )
    except StrategyLoadError as exc:
        raise typer.BadParameter(str(exc)) from exc

    # Enforce optional strategy metadata without mutating the strategy implementation
    # 1) Supported intervals (timeframes)
    supported = getattr(strat, "supported_intervals", None)
    if supported and source == "yfinance":
        if interval not in set(supported):
            raise typer.BadParameter(
                f"Strategy '{strat.name}' does not support interval '{interval}'. Supported: {sorted(set(supported))}"
            )

    # 2) Required columns - reduce to essentials if specified
    required_cols = getattr(strat, "required_columns", None)
    if required_cols:
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            raise typer.BadParameter(
                f"Data missing required columns for strategy '{strat.name}': {missing_cols}"
            )
        # Keep only necessary columns for accuracy and performance
        df = df[required_cols].copy()
        feed = DataFeed(df)

    engine = BacktestEngine(feed=feed, broker=broker, strategy=strat, initial_cash=cash)
    hist = engine.run()
    equity = hist["equity"]
    drawdown = (equity / equity.cummax() - 1.0).fillna(0.0)
    metrics = compute_metrics(equity, freq="D")

    ts_dir = out or os.path.join("runs", datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(ts_dir, exist_ok=True)
    hist.to_csv(os.path.join(ts_dir, "history.csv"))

    plot_equity_curve(equity, savepath=os.path.join(ts_dir, "equity.png"))
    plot_drawdown(drawdown, savepath=os.path.join(ts_dir, "drawdown.png"))

    typer.echo("Metrics:")
    for k, v in metrics.items():
        typer.echo(f"  {k}: {v:.6f}" if v == v else f"  {k}: nan")

    if html_report:
        try:
            from .reports.report import generate_html_report

            params: dict[str, object] = {"strategy": strat.name, **strat.params}
            report_path = generate_html_report(
                params=params, metrics=metrics, equity=equity, out_dir=ts_dir
            )
            if report_path:
                typer.echo(f"HTML report saved to: {report_path}")
        except Exception:
            typer.echo("jinja2 not installed or report generation failed; skipping HTML report.")

    typer.echo(f"Outputs saved in: {ts_dir}")


if __name__ == "__main__":
    app()

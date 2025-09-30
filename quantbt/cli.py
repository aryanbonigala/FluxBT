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


app = typer.Typer(help="quantbt CLI")


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
            report_path = generate_html_report(params=params, metrics=metrics, equity=equity, out_dir=ts_dir)
            if report_path:
                typer.echo(f"HTML report saved to: {report_path}")
        except Exception:
            typer.echo("jinja2 not installed or report generation failed; skipping HTML report.")

    typer.echo(f"Outputs saved in: {ts_dir}")


if __name__ == "__main__":
    app()

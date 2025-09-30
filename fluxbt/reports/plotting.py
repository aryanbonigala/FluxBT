from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import pandas as pd


def plot_equity_curve(equity: pd.Series, savepath: str | None = None) -> Figure:
    fig, ax = plt.subplots(figsize=(10, 4))
    equity.plot(ax=ax)
    ax.set_title("Equity Curve")
    ax.set_xlabel("Time")
    ax.set_ylabel("Equity")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    if savepath:
        fig.savefig(savepath)
    return fig


def plot_drawdown(drawdown: pd.Series, savepath: str | None = None) -> Figure:
    fig, ax = plt.subplots(figsize=(10, 2.5))
    drawdown.plot(ax=ax)
    ax.set_title("Drawdown")
    ax.set_xlabel("Time")
    ax.set_ylabel("Drawdown")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    if savepath:
        fig.savefig(savepath)
    return fig


def plot_trade_pnl(trades_df: pd.DataFrame, savepath: str | None = None) -> Figure:
    fig, ax = plt.subplots(figsize=(10, 3))
    if not trades_df.empty and "pnl" in trades_df.columns:
        trades_df["pnl"].plot(kind="bar", ax=ax)
    ax.set_title("Trade PnL")
    ax.set_xlabel("Trade #")
    ax.set_ylabel("PnL")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    if savepath:
        fig.savefig(savepath)
    return fig

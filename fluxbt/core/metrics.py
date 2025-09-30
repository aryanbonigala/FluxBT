from __future__ import annotations

from typing import Dict, Literal

import numpy as np
import pandas as pd

from .utils import annualization_factor


def _nan_safe(series: pd.Series) -> pd.Series:
    return series.replace([np.inf, -np.inf], np.nan).dropna()


def compute_metrics(
    equity: pd.Series, freq: Literal["D", "H", "MIN"], rf: float = 0.0
) -> Dict[str, float]:
    equity = equity.dropna()
    if equity.empty:
        return {
            k: float("nan")
            for k in [
                "total_return",
                "cagr",
                "ann_vol",
                "sharpe",
                "max_dd",
                "calmar",
                "hit_rate",
                "avg_win",
                "avg_loss",
                "profit_factor",
            ]
        }

    ret = equity.pct_change().fillna(0.0)
    ann = annualization_factor(freq)

    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    n_periods = max(len(equity) - 1, 1)
    years = n_periods / ann
    if years <= 0:
        cagr = float("nan")
    else:
        cagr = float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1)

    ann_vol = float(ret.std(ddof=0) * np.sqrt(ann)) if len(ret) > 1 else float("nan")
    excess = ret - (rf / ann)
    sharpe = (
        float(excess.mean() / excess.std(ddof=0) * np.sqrt(ann))
        if excess.std(ddof=0) > 0
        else float("nan")
    )

    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max
    max_dd = float(drawdown.min()) if not drawdown.empty else float("nan")
    calmar = float(cagr / abs(max_dd)) if max_dd < 0 else float("nan")

    # Trade stats based on equity swings
    # Identify positive and negative daily returns
    wins = ret[ret > 0]
    losses = ret[ret < 0]
    hit_rate = float(len(wins) / max(len(wins) + len(losses), 1))
    avg_win = float(wins.mean()) if not wins.empty else 0.0
    avg_loss = float(losses.mean()) if not losses.empty else 0.0
    profit_factor = float(wins.sum() / abs(losses.sum())) if abs(losses.sum()) > 0 else float("inf")

    return {
        "total_return": total_return,
        "cagr": cagr,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "max_dd": max_dd,
        "calmar": calmar,
        "hit_rate": hit_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
    }

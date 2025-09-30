from __future__ import annotations

from typing import Literal
import pandas as pd


def annualization_factor(freq: Literal["D", "H", "MIN"]) -> float:
    if freq == "D":
        return 252.0
    if freq == "H":
        return 252.0 * 6.5
    if freq == "MIN":
        return 252.0 * 390.0
    raise ValueError("freq must be one of 'D', 'H', 'MIN'")


def safe_rolling_mean(series: pd.Series, window: int) -> pd.Series:
    if window <= 1:
        return series.copy()
    return series.rolling(window=window, min_periods=window).mean()


def safe_rolling_std(series: pd.Series, window: int) -> pd.Series:
    if window <= 1:
        return pd.Series(0.0, index=series.index)
    return series.rolling(window=window, min_periods=window).std(ddof=0)


def to_timestamp(x: pd.Timestamp | str) -> pd.Timestamp:
    return pd.Timestamp(x)

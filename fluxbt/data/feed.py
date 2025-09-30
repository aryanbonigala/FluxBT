from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterator

import pandas as pd

REQUIRED_COLS = ["open", "high", "low", "close", "volume"]


@dataclass
class DataFeed:
    df: pd.DataFrame

    def __post_init__(self) -> None:
        if not isinstance(self.df.index, pd.DatetimeIndex):
            raise TypeError("DataFeed requires a DatetimeIndex")
        if not self.df.index.is_monotonic_increasing:
            raise ValueError("Time index must be monotonic increasing")
        missing = [c for c in REQUIRED_COLS if c not in self.df.columns]
        if missing:
            raise ValueError(f"DataFeed missing columns: {missing}")

    def iter_bars(self) -> Iterator[tuple[pd.Timestamp, dict[str, float]]]:
        for ts, row in self.df.iterrows():
            bar = {
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
            yield ts, bar

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import pandas as pd


STANDARD_COLUMNS = ["open", "high", "low", "close", "volume"]


class DataLoader(ABC):
    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Return OHLCV dataframe with DatetimeIndex (tz-aware preferred) and
        columns: ['open','high','low','close','volume'] sorted by index.
        """


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping_candidates: dict[str, list[str]] = {
        "open": ["open", "o", "Open", "OPEN"],
        "high": ["high", "h", "High", "HIGH"],
        "low": ["low", "l", "Low", "LOW"],
        "close": ["close", "c", "Close", "Adj Close", "CLOSE", "adj_close", "adj close"],
        "volume": ["volume", "v", "Volume", "VOL", "VOLU", "VOLUME"],
    }
    cols: dict[str, str] = {}
    for std, candidates in mapping_candidates.items():
        for cand in candidates:
            if cand in df.columns:
                cols[cand] = std
                break
    df = df.rename(columns=cols)
    missing = [c for c in STANDARD_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns after normalization: {missing}")
    return df[STANDARD_COLUMNS]


@dataclass
class CSVLoader(DataLoader):
    path: str
    tz: Optional[str] = "UTC"

    def load(self) -> pd.DataFrame:
        df = pd.read_csv(self.path)
        # try common datetime columns
        dt_col_candidates = [
            "datetime",
            "timestamp",
            "date",
            "Date",
            "Datetime",
        ]
        idx = None
        for col in dt_col_candidates:
            if col in df.columns:
                idx = pd.to_datetime(df[col], utc=False, errors="coerce")
                break
        if idx is None:
            # If index is already datetime-like
            try:
                idx = pd.to_datetime(df.index, utc=False, errors="coerce")
            except Exception as exc:  # pragma: no cover - defensive
                raise ValueError("CSV must contain a datetime column or index") from exc
        df.index = idx
        df = df.dropna(axis=0, subset=[df.index.name] if df.index.name else None)
        df = _normalize_columns(df)
        df = df.sort_index()
        if self.tz:
            if df.index.tz is None:
                df.index = df.index.tz_localize(self.tz)
            else:
                df.index = df.index.tz_convert(self.tz)
        return df


@dataclass
class YFinanceLoader(DataLoader):
    ticker: str
    interval: str = "1d"
    start: Optional[str] = None
    end: Optional[str] = None

    def load(self) -> pd.DataFrame:
        import yfinance as yf  # local import to keep optional at runtime

        df = yf.download(
            self.ticker,
            interval=self.interval,
            start=self.start,
            end=self.end,
            auto_adjust=False,
            progress=False,
            group_by="column",
        )
        if not isinstance(df, pd.DataFrame) or df.empty:
            raise ValueError("No data returned from yfinance")
        if isinstance(df.columns, pd.MultiIndex):
            # Flatten common yfinance MultiIndex: (Ticker, Field)
            try:
                df.columns = [
                    c[1] if isinstance(c, tuple) and len(c) > 1 else c for c in df.columns
                ]
            except Exception:
                df = df.droplevel(0, axis=1)
        df = df.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "close",
                "Volume": "volume",
            }
        )
        df = df[STANDARD_COLUMNS]
        df.index = pd.to_datetime(df.index)
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        df = df.sort_index()
        return df

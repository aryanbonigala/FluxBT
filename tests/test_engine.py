from __future__ import annotations

import pandas as pd

from quantbt.core.broker import Broker
from quantbt.core.engine import BacktestEngine
from quantbt.data.feed import DataFeed
from quantbt.strategies.sma_crossover import SMACrossover


def test_engine_runs_and_equity_updates() -> None:
    idx = pd.date_range("2020-01-01", periods=200, freq="D", tz="UTC")
    price = pd.Series(100 + (pd.Series(range(200)) * 0.1).values, index=idx)
    df = pd.DataFrame(
        {"open": price, "high": price, "low": price, "close": price, "volume": 1000.0}
    )
    feed = DataFeed(df)
    broker = Broker(slippage_bps=0, commission_bps=0)
    strat = SMACrossover(fast=5, slow=20, size_pct=0.5, long_only=True)
    engine = BacktestEngine(feed=feed, broker=broker, strategy=strat, initial_cash=10000.0)
    hist = engine.run()
    assert not hist.empty
    assert "equity" in hist.columns
    assert hist["equity"].iloc[-1] >= hist["equity"].iloc[0]

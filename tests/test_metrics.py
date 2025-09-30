from __future__ import annotations

import pandas as pd

from quantbt.core.metrics import compute_metrics


def test_metrics_basic() -> None:
    idx = pd.date_range("2020-01-01", periods=252, freq="D", tz="UTC")
    # deterministic drift
    ret = pd.Series(0.001, index=idx)
    equity = (1 + ret).cumprod()
    m = compute_metrics(equity, freq="D")
    assert m["total_return"] > 0
    assert m["sharpe"] > 0
    assert m["max_dd"] <= 0

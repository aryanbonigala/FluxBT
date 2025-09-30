from __future__ import annotations

import pandas as pd

from quantbt.core.orders import Fill
from quantbt.core.portfolio import Portfolio


def test_portfolio_buy_mark_sell_flow() -> None:
    p = Portfolio(cash=10000)
    ts = pd.Timestamp("2020-01-01", tz="UTC")

    # buy 10 @ 100, no commission
    fill_buy = Fill(order_id="1", ts=ts, price=100.0, qty=10.0, commission=0.0)
    p.apply_trade("BUY", fill_buy)
    p.mark_to_market(100.0)
    assert p.position == 10
    assert p.cash == 10000 - 100 * 10
    assert p.avg_cost == 100.0

    # price moves to 110
    p.mark_to_market(110.0)
    assert p.cash + p.position * 110.0 == p.cash + 1100.0

    # sell 10 @ 110, include commission
    fill_sell = Fill(order_id="2", ts=ts, price=110.0, qty=10.0, commission=1.0)
    p.apply_trade("SELL", fill_sell)
    p.mark_to_market(110.0)
    assert p.position == 0
    # realized pnl: (110-100)*10 - 1 commission accounted when applying sell
    assert abs(p.realized_pnl - (10 * 10 - 1.0)) < 1e-9

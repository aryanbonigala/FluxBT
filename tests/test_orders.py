from __future__ import annotations

import pandas as pd

from quantbt.core.orders import Order, resolve_order_quantity


def test_order_validation_and_qty_parsing() -> None:
    ts = pd.Timestamp("2020-01-01", tz="UTC")
    # valid numeric
    o1 = Order(id="1", ts=ts, side="BUY", qty=10.0)
    assert o1.qty == 10.0
    # valid pct
    o2 = Order(id="2", ts=ts, side="SELL", qty="PCT:0.5")
    assert isinstance(o2.qty, str)
    # valid close
    o3 = Order(id="3", ts=ts, side="BUY", qty="CLOSE")
    assert o3.qty == "CLOSE"

    # qty resolution
    shares = resolve_order_quantity(
        "PCT:0.1", side="BUY", equity=10000, price=100, current_position=0
    )
    assert shares == 10
    shares_close = resolve_order_quantity(
        "CLOSE", side="SELL", equity=10000, price=100, current_position=15
    )
    assert shares_close == 15

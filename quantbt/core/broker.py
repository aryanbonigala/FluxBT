from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from .orders import Fill, Order, resolve_order_quantity


@dataclass
class Broker:
    slippage_bps: float = 1.0
    commission_bps: float = 0.0

    def execute(
        self,
        order: Order,
        price: float,
        ts: pd.Timestamp,
        equity: float,
        current_position: float,
    ) -> Optional[Fill]:
        # Resolve shares
        shares = resolve_order_quantity(order.qty, order.side, equity, price, current_position)
        if shares <= 0:
            return None
        # price with slippage
        slip = price * (self.slippage_bps / 10_000)
        fill_price = price + slip if order.side == "BUY" else price - slip
        commission = fill_price * shares * (self.commission_bps / 10_000)
        return Fill(
            order_id=order.id,
            ts=ts,
            price=float(fill_price),
            qty=float(shares),
            commission=float(commission),
        )

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .orders import Fill


@dataclass
class Portfolio:
    cash: float
    position: float = 0.0
    avg_cost: float = 0.0
    equity: float = 0.0
    realized_pnl: float = 0.0
    trade_log: list[Fill] = field(default_factory=list)

    def apply_fill(self, fill: Fill) -> None:
        # Kept for API completeness; not used in engine
        self.trade_log.append(fill)

    def apply_trade(self, side: str, fill: Fill) -> None:
        qty_signed = fill.qty if side == "BUY" else -fill.qty
        notional = fill.price * fill.qty
        self.cash -= notional if side == "BUY" else -notional
        self.cash -= fill.commission

        new_position = self.position + qty_signed
        if self.position == 0 and qty_signed != 0:
            # opening
            self.avg_cost = fill.price
        elif (self.position > 0 and qty_signed > 0) or (self.position < 0 and qty_signed < 0):
            # adding to same direction: update avg cost
            total_shares = abs(self.position) + abs(qty_signed)
            if total_shares != 0:
                self.avg_cost = (
                    abs(self.position) * self.avg_cost + abs(qty_signed) * fill.price
                ) / total_shares
        else:
            # reducing or flipping: realize PnL on the reduced portion
            closing_qty = min(abs(self.position), abs(qty_signed))
            pnl_per_share = (
                (fill.price - self.avg_cost) if self.position > 0 else (self.avg_cost - fill.price)
            )
            self.realized_pnl += closing_qty * pnl_per_share - fill.commission

        self.position = new_position

    def mark_to_market(self, price: float) -> None:
        unrealized = 0.0
        if self.position != 0:
            direction = 1.0 if self.position > 0 else -1.0
            unrealized = abs(self.position) * (price - self.avg_cost) * direction
        self.equity = (
            self.cash
            + unrealized
            + abs(self.position) * price
            - abs(self.position) * price
            + self.cash * 0
        )
        # Better: equity = cash + position*price
        self.equity = self.cash + self.position * price

    @staticmethod
    def drawdown_series(equity: pd.Series) -> pd.Series:
        if equity.empty:
            return equity
        running_max = equity.cummax()
        dd = (equity - running_max) / running_max
        return dd.fillna(0.0)

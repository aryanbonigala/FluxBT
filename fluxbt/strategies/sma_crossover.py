from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..core.orders import Order, OrderSide
from .base import Strategy


@dataclass
class SMACrossover(Strategy):
    fast: int = 20
    slow: int = 50
    size_pct: float = 0.1
    cooldown: int = 0
    long_only: bool = True

    _prices: list[float] = None  # type: ignore[assignment]
    _cool: int = 0
    _position: int = 0  # -1, 0, 1

    @property
    def name(self) -> str:
        return "sma_crossover"

    @property
    def params(self) -> dict[str, object]:
        return {
            "fast": self.fast,
            "slow": self.slow,
            "size_pct": self.size_pct,
            "cooldown": self.cooldown,
            "long_only": self.long_only,
        }

    def reset(self) -> None:
        self._prices = []
        self._cool = 0
        self._position = 0

    def on_bar(self, ts: pd.Timestamp, bar: dict[str, float]) -> list[Order]:
        self._prices.append(bar["close"])
        orders: list[Order] = []
        if len(self._prices) < max(self.fast, self.slow):
            return orders
        fast_sma = sum(self._prices[-self.fast :]) / self.fast
        slow_sma = sum(self._prices[-self.slow :]) / self.slow

        if self._cool > 0:
            self._cool -= 1
            return orders

        if fast_sma > slow_sma and self._position <= 0:
            # go long
            if self._position < 0:
                # close short first
                orders.append(Order(id=f"{ts}-close", ts=ts, side="BUY", qty="CLOSE"))
            orders.append(Order(id=f"{ts}-buy", ts=ts, side="BUY", qty=f"PCT:{self.size_pct}"))
            self._position = 1
        elif fast_sma < slow_sma and (not self.long_only) and self._position >= 0:
            # go short
            if self._position > 0:
                orders.append(Order(id=f"{ts}-close", ts=ts, side="SELL", qty="CLOSE"))
            orders.append(Order(id=f"{ts}-sell", ts=ts, side="SELL", qty=f"PCT:{self.size_pct}"))
            self._position = -1
        elif (fast_sma <= slow_sma and self._position == 1) or (
            fast_sma >= slow_sma and self._position == -1
        ):
            # exit to flat
            side: OrderSide = "SELL" if self._position == 1 else "BUY"
            orders.append(Order(id=f"{ts}-exit", ts=ts, side=side, qty="CLOSE"))
            self._position = 0
            if self.cooldown > 0:
                self._cool = self.cooldown
        return orders

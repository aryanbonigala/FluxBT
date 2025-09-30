from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..core.orders import Order, OrderSide
from .base import Strategy


@dataclass
class MeanReversion(Strategy):
    window: int = 20
    entry: float = 2.0
    exit: float = 0.5
    size_pct: float = 0.1
    stop_pct: float | None = None
    tp_pct: float | None = None
    cooldown: int = 0
    allow_short: bool = True

    _prices: list[float] = None  # type: ignore[assignment]
    _position: int = 0
    _entry_price: float | None = None
    _cool: int = 0

    @property
    def name(self) -> str:
        return "mean_reversion"

    @property
    def params(self) -> dict[str, object]:
        return {
            "window": self.window,
            "entry": self.entry,
            "exit": self.exit,
            "size_pct": self.size_pct,
            "stop_pct": self.stop_pct,
            "tp_pct": self.tp_pct,
            "cooldown": self.cooldown,
            "allow_short": self.allow_short,
        }

    def reset(self) -> None:
        self._prices = []
        self._position = 0
        self._entry_price = None
        self._cool = 0

    def on_bar(self, ts: pd.Timestamp, bar: dict[str, float]) -> list[Order]:
        price = bar["close"]
        self._prices.append(price)
        orders: list[Order] = []
        if len(self._prices) < self.window:
            return orders

        import statistics

        mu = statistics.mean(self._prices[-self.window :])
        sigma = statistics.pstdev(self._prices[-self.window :]) or 1e-12
        z = (price - mu) / sigma

        if self._cool > 0:
            self._cool -= 1
            return orders

        # exits first
        if self._position != 0:
            if abs(z) < self.exit:
                side: OrderSide = "SELL" if self._position == 1 else "BUY"
                orders.append(Order(id=f"{ts}-exit", ts=ts, side=side, qty="CLOSE"))
                self._position = 0
                self._entry_price = None
                if self.cooldown > 0:
                    self._cool = self.cooldown
                return orders
            if self.stop_pct is not None and self._entry_price is not None:
                if self._position == 1 and price <= self._entry_price * (1 - self.stop_pct):
                    orders.append(Order(id=f"{ts}-sl", ts=ts, side="SELL", qty="CLOSE"))
                    self._position = 0
                    self._entry_price = None
                    if self.cooldown > 0:
                        self._cool = self.cooldown
                    return orders
                if self._position == -1 and price >= self._entry_price * (1 + self.stop_pct):
                    orders.append(Order(id=f"{ts}-sl", ts=ts, side="BUY", qty="CLOSE"))
                    self._position = 0
                    self._entry_price = None
                    if self.cooldown > 0:
                        self._cool = self.cooldown
                    return orders
            if self.tp_pct is not None and self._entry_price is not None:
                if self._position == 1 and price >= self._entry_price * (1 + self.tp_pct):
                    orders.append(Order(id=f"{ts}-tp", ts=ts, side="SELL", qty="CLOSE"))
                    self._position = 0
                    self._entry_price = None
                    if self.cooldown > 0:
                        self._cool = self.cooldown
                    return orders
                if self._position == -1 and price <= self._entry_price * (1 - self.tp_pct):
                    orders.append(Order(id=f"{ts}-tp", ts=ts, side="BUY", qty="CLOSE"))
                    self._position = 0
                    self._entry_price = None
                    if self.cooldown > 0:
                        self._cool = self.cooldown
                    return orders

        # entries
        if z < -self.entry and self._position <= 0:
            if self._position < 0:
                orders.append(Order(id=f"{ts}-close", ts=ts, side="BUY", qty="CLOSE"))
            orders.append(Order(id=f"{ts}-buy", ts=ts, side="BUY", qty=f"PCT:{self.size_pct}"))
            self._position = 1
            self._entry_price = price
        elif self.allow_short and z > self.entry and self._position >= 0:
            if self._position > 0:
                orders.append(Order(id=f"{ts}-close", ts=ts, side="SELL", qty="CLOSE"))
            orders.append(Order(id=f"{ts}-sell", ts=ts, side="SELL", qty=f"PCT:{self.size_pct}"))
            self._position = -1
            self._entry_price = price
        return orders

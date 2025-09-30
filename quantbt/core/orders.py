from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import math
import pandas as pd


OrderSide = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT"]


@dataclass(frozen=True)
class Order:
    id: str
    ts: pd.Timestamp
    side: OrderSide
    qty: float | str  # float shares, "PCT:x", or "CLOSE"
    type: OrderType = "MARKET"
    limit_price: float | None = None

    def __post_init__(self) -> None:
        if self.side not in ("BUY", "SELL"):
            raise ValueError("Order.side must be 'BUY' or 'SELL'")
        if self.type not in ("MARKET", "LIMIT"):
            raise ValueError("Order.type must be 'MARKET' or 'LIMIT'")
        if isinstance(self.qty, (int, float)):
            if self.qty <= 0:
                raise ValueError("Numeric qty must be > 0")
        elif isinstance(self.qty, str):
            if not (self.qty.startswith("PCT:") or self.qty == "CLOSE"):
                raise ValueError("qty string must be 'CLOSE' or 'PCT:x'")
            if self.qty.startswith("PCT:"):
                try:
                    _ = float(self.qty.split(":", 1)[1])
                except Exception as exc:  # pragma: no cover - defensive
                    raise ValueError("Invalid PCT format, expected PCT:<fraction>") from exc
        else:  # pragma: no cover - defensive
            raise TypeError("qty must be float or str")
        if self.type == "LIMIT" and self.limit_price is None:
            raise ValueError("limit_price required for LIMIT orders")


@dataclass(frozen=True)
class Fill:
    order_id: str
    ts: pd.Timestamp
    price: float
    qty: float
    commission: float


def resolve_order_quantity(
    qty_spec: float | str,
    side: OrderSide,
    equity: float,
    price: float,
    current_position: float,
) -> float:
    """Resolve qty specification to numeric shares.

    - float: returned directly
    - "PCT:x": invest fraction x of equity on the given side
    - "CLOSE": close the entire current position (direction inferred)
    """
    if isinstance(qty_spec, (int, float)):
        return float(qty_spec)
    if qty_spec == "CLOSE":
        if current_position == 0:
            return 0.0
        # CLOSE means take the opposite side of current position fully
        return abs(current_position)
    if qty_spec.startswith("PCT:"):
        fraction = float(qty_spec.split(":", 1)[1])
        if fraction <= 0:
            raise ValueError("PCT fraction must be > 0")
        notional = equity * fraction
        shares = math.floor(notional / price)
        return float(max(0, shares))
    raise ValueError("Invalid qty specification")

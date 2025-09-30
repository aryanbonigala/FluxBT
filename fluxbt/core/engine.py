from __future__ import annotations

from dataclasses import dataclass, field
import pandas as pd

from ..data.feed import DataFeed
from ..strategies.base import Strategy
from .broker import Broker
from .orders import Fill
from .portfolio import Portfolio


@dataclass
class BacktestEngine:
    feed: DataFeed
    broker: Broker
    strategy: Strategy
    initial_cash: float = 100_000.0

    fills: list[Fill] = field(default_factory=list)
    history: list[dict[str, float]] = field(default_factory=list)

    def run(self) -> pd.DataFrame:
        portfolio = Portfolio(cash=self.initial_cash)
        self.strategy.reset()
        for ts, bar in self.feed.iter_bars():
            price = float(bar["close"])
            portfolio.mark_to_market(price)
            orders = self.strategy.on_bar(ts, bar)
            for order in orders:
                fill = self.broker.execute(
                    order,
                    price,
                    ts,
                    equity=max(portfolio.cash + portfolio.position * price, 0.0),
                    current_position=portfolio.position,
                )
                if fill is None:
                    continue
                self.fills.append(fill)
                # Infer side from order
                side = order.side
                portfolio.apply_trade(side, fill)
                portfolio.mark_to_market(price)
            dd = (
                Portfolio.drawdown_series(
                    pd.Series(
                        [h["equity"] for h in self.history]
                        + [portfolio.cash + portfolio.position * price]
                    )
                ).iloc[-1]
                if self.history
                else 0.0
            )
            snapshot = {
                "ts": ts,
                "price": price,
                "position": float(portfolio.position),
                "cash": float(portfolio.cash),
                "equity": float(portfolio.cash + portfolio.position * price),
                "drawdown": float(dd),
            }
            self.history.append(snapshot)
        df = pd.DataFrame(self.history)
        df = df.set_index("ts")
        return df

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from ..core.orders import Order


class Strategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    @property
    @abstractmethod
    def params(self) -> dict[str, object]:  # pragma: no cover - interface
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    @abstractmethod
    def on_bar(
        self, ts: pd.Timestamp, bar: dict[str, float]
    ) -> list[Order]:  # pragma: no cover - interface
        raise NotImplementedError

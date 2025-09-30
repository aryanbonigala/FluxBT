from __future__ import annotations

import numpy as np
import pandas as pd

from .utils import annualization_factor


def target_position_scale(returns: pd.Series, freq: str, target_ann_vol: float) -> float:
    if returns.empty:
        return 0.0
    ann = annualization_factor(freq)  # type: ignore[arg-type]
    vol = float(returns.std(ddof=0) * np.sqrt(ann))
    if vol <= 0:
        return 0.0
    return float(target_ann_vol / vol)


def kelly_fraction(win_prob: float, win_loss_ratio: float) -> float:
    """Kelly fraction under simple Bernoulli assumption.
    f* = p - (1-p)/b
    where b is win/loss ratio.
    """
    if not (0.0 < win_prob < 1.0) or win_loss_ratio <= 0:
        return 0.0
    p = win_prob
    b = win_loss_ratio
    frac = p - (1 - p) / b
    return float(max(0.0, min(frac, 1.0)))


def cap_position_fraction(fraction: float, max_abs_fraction: float) -> float:
    if max_abs_fraction <= 0:
        return 0.0
    return float(max(-max_abs_fraction, min(fraction, max_abs_fraction)))

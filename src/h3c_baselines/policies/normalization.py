"""Legacy min-max normalization preserved for frozen DRL policies."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def symmetric_minmax(
    values: NDArray[np.float64],
    lower: NDArray[np.float64],
    upper: NDArray[np.float64],
) -> NDArray[np.float32]:
    if values.shape != lower.shape or values.shape != upper.shape:
        raise ValueError("normalization arrays must have identical shapes")
    if np.any(~np.isfinite(lower)) or np.any(~np.isfinite(upper)) or np.any(upper <= lower):
        raise ValueError("normalization bounds are invalid")
    clean = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    return (2.0 * (clean - lower) / (upper - lower) - 1.0).astype(np.float32)

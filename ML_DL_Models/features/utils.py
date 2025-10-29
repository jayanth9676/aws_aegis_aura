from __future__ import annotations

from functools import lru_cache
from typing import Iterable

import numpy as np
import pandas as pd


@lru_cache(maxsize=1)
def polars_available() -> bool:
    try:  # pragma: no cover - optional dependency
        import polars  # noqa: F401

        return True
    except ImportError:
        return False


def bool_to_int(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "yes", "y"]).astype(int)


def ensure_numeric(df: pd.DataFrame, columns: Iterable[str]) -> None:
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)


def safe_log(series: pd.Series) -> pd.Series:
    return np.log1p(series.clip(lower=0))


def sin_time(value: pd.Series, period: int) -> pd.Series:
    return np.sin(2 * np.pi * value / period)


def cos_time(value: pd.Series, period: int) -> pd.Series:
    return np.cos(2 * np.pi * value / period)


def safe_ratio(numerator: pd.Series, denominator: pd.Series, epsilon: float = 1e-6) -> pd.Series:
    denominator = denominator.replace({0: epsilon})
    return (numerator / denominator).replace([np.inf, -np.inf], 0).fillna(0)


def clip_age(series: pd.Series, lower: int = 18, upper: int = 100) -> pd.Series:
    return series.fillna(series.median()).clip(lower=lower, upper=upper)



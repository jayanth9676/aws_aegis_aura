from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def weighted_scale_pos_weight(y: Iterable[int]) -> float:
    y = np.asarray(list(y))
    positives = max(y.sum(), 1)
    negatives = max(len(y) - positives, 1)
    return negatives / positives


def prepare_numeric(df: pd.DataFrame) -> pd.DataFrame:
    return df.apply(lambda col: pd.to_numeric(col, errors="coerce")).fillna(0).astype(np.float32)


def train_test_split_df(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float,
    random_state: int,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        stratify=y,
        random_state=random_state,
    )
    return X_train, X_test, y_train, y_test



from __future__ import annotations

from typing import Dict, Iterable, Tuple

import pandas as pd
from sklearn.preprocessing import LabelEncoder


def encode_categoricals(df: pd.DataFrame, categorical_cols: Iterable[str]) -> pd.DataFrame:
    df_encoded = df.copy()
    for col in categorical_cols:
        if col not in df_encoded.columns:
            continue
        values = df_encoded[col].astype(str).fillna("Unknown")
        encoder = LabelEncoder()
        encoder.fit(values)
        df_encoded[f"{col}_encoded"] = encoder.transform(values)
    return df_encoded


def encode_categoricals_with_map(
    df: pd.DataFrame,
    categorical_cols: Iterable[str],
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, int]]]:
    df_encoded = df.copy()
    mapping: Dict[str, Dict[str, int]] = {}

    for col in categorical_cols:
        if col not in df_encoded.columns:
            continue
        values = df_encoded[col].astype(str).fillna("Unknown")
        encoder = LabelEncoder()
        encoded = encoder.fit_transform(values)
        df_encoded[f"{col}_encoded"] = encoded
        mapping[col] = {cls: int(code) for cls, code in zip(encoder.classes_, encoder.transform(encoder.classes_))}

    return df_encoded, mapping



from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
import torch
import torch.nn as nn


@dataclass
class BehavioralSequenceConfig:
    input_dim: int
    hidden_dim: int = 128
    num_layers: int = 2
    dropout: float = 0.3


class BehavioralSequenceModel(nn.Module):
    def __init__(self, config: BehavioralSequenceConfig):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=config.input_dim,
            hidden_size=config.hidden_dim,
            num_layers=config.num_layers,
            batch_first=True,
            dropout=config.dropout,
        )
        self.head = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim // 2, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        outputs, _ = self.lstm(x)
        last = outputs[:, -1, :]
        return self.head(last)


def pad_sequences(sequences: np.ndarray, max_len: int) -> np.ndarray:
    if len(sequences) == 0:
        return np.zeros((0, max_len, 0), dtype=np.float32)
    feature_dim = max(seq.shape[-1] if np.asarray(seq).ndim > 1 else 1 for seq in sequences)
    padded = np.zeros((len(sequences), max_len, feature_dim), dtype=np.float32)
    for idx, seq in enumerate(sequences):
        seq = np.asarray(seq, dtype=np.float32)
        if seq.ndim == 1:
            seq = seq.reshape(-1, feature_dim)
        elif seq.shape[1] < feature_dim:
            pad_width = feature_dim - seq.shape[1]
            seq = np.pad(seq, ((0, 0), (0, pad_width)), mode="constant")
        elif seq.shape[1] > feature_dim:
            seq = seq[:, :feature_dim]
        length = min(len(seq), max_len)
        padded[idx, :length, :] = seq[:length]
    return padded



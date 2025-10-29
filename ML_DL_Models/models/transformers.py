from __future__ import annotations

"""Transformer-based models for transaction analysis and categorical embeddings."""

import math
from dataclasses import dataclass
from typing import Dict, Optional

import torch
import torch.nn as nn


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding for transformer inputs."""

    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000) -> None:
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        position = torch.arange(0, max_len, dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe = torch.zeros(max_len, d_model)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # type: ignore[override]
        x = x + self.pe[:, : x.size(1)]
        return self.dropout(x)


@dataclass
class TransactionTransformerConfig:
    input_dim: int
    d_model: int = 128
    nhead: int = 8
    num_layers: int = 3
    dim_feedforward: int = 512
    dropout: float = 0.1
    max_seq_len: int = 32
    learning_rate: float = 1e-3
    weight_decay: float = 1e-5


class TransactionTransformer(nn.Module):
    """Transformer encoder for transaction sequence modelling."""

    def __init__(self, config: TransactionTransformerConfig) -> None:
        super().__init__()
        self.config = config

        self.input_projection = nn.Linear(config.input_dim, config.d_model)
        self.positional_encoding = PositionalEncoding(config.d_model, config.dropout, config.max_seq_len)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.d_model,
            nhead=config.nhead,
            dim_feedforward=config.dim_feedforward,
            dropout=config.dropout,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=config.num_layers)

        self.output_head = nn.Sequential(
            nn.LayerNorm(config.d_model),
            nn.Linear(config.d_model, config.d_model // 2),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model // 2, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor, src_key_padding_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        projected = self.input_projection(x)
        encoded = self.positional_encoding(projected)
        encoded = self.encoder(encoded, src_key_padding_mask=src_key_padding_mask)
        pooled = encoded.mean(dim=1)
        return self.output_head(pooled)


@dataclass
class CategoricalTransformerConfig:
    field_cardinalities: Dict[str, int]
    embedding_dim: int = 64
    nhead: int = 4
    num_layers: int = 2
    dropout: float = 0.1
    learning_rate: float = 1e-3
    weight_decay: float = 1e-5


class CategoricalFeatureTransformer(nn.Module):
    """Transformer that models relationships between categorical features."""

    def __init__(self, config: CategoricalTransformerConfig) -> None:
        super().__init__()
        self.config = config
        self.feature_names = list(config.field_cardinalities.keys())

        self.embeddings = nn.ModuleDict(
            {
                name: nn.Embedding(cardinality + 1, config.embedding_dim, padding_idx=0)
                for name, cardinality in config.field_cardinalities.items()
            }
        )

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.embedding_dim,
            nhead=config.nhead,
            dim_feedforward=config.embedding_dim * 2,
            dropout=config.dropout,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=config.num_layers)

        self.output_head = nn.Sequential(
            nn.LayerNorm(config.embedding_dim),
            nn.Linear(config.embedding_dim, config.embedding_dim // 2),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.embedding_dim // 2, 1),
            nn.Sigmoid(),
        )

    def forward(self, categorical_inputs: Dict[str, torch.Tensor]) -> torch.Tensor:
        embeddings = []
        for name in self.feature_names:
            value = categorical_inputs[name]
            embeddings.append(self.embeddings[name](value))

        stacked = torch.stack(embeddings, dim=1)
        encoded = self.encoder(stacked)
        pooled = encoded.mean(dim=1)
        return self.output_head(pooled)



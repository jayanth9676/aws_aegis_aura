"""Multi-modal fusion models combining heterogeneous fraud detection signals."""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn


@dataclass
class FusionConfig:
    gnn_dim: int = 64
    transformer_dim: int = 128
    tabular_dim: int = 64
    dropout: float = 0.2


class MultiModalFraudFusion(nn.Module):
    """Fuse outputs from classical, graph, and transformer models."""

    def __init__(self, config: FusionConfig) -> None:
        super().__init__()
        self.config = config

        input_dim = config.gnn_dim + config.transformer_dim + config.tabular_dim
        hidden_dim = max(32, input_dim // 2)

        self.network = nn.Sequential(
            nn.LayerNorm(input_dim),
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid(),
        )

    def forward(
        self,
        gnn_embedding: torch.Tensor,
        transformer_embedding: torch.Tensor,
        tabular_embedding: torch.Tensor,
    ) -> torch.Tensor:
        concatenated = torch.cat([gnn_embedding, transformer_embedding, tabular_embedding], dim=1)
        return self.network(concatenated)



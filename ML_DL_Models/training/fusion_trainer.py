"""Multimodal fusion model trainer."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

import joblib
import numpy as np
import pandas as pd

from configs import AppConfig
from data import DatasetBundle

LOGGER = logging.getLogger("aegis.training.fusion")

try:
    import torch
    import torch.nn as nn
    from sklearn.metrics import roc_auc_score, average_precision_score, f1_score
    from sklearn.model_selection import train_test_split
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    LOGGER.warning("PyTorch not available for fusion training")


def train_fusion_model(
    datasets: DatasetBundle,
    config: AppConfig,
    gnn_embeddings_path: Optional[Path] = None,
    transformer_embeddings_path: Optional[Path] = None,
) -> Dict[str, Path]:
    """
    Train multimodal fusion model combining GNN, Transformer, and classical features.
    
    Args:
        datasets: Bundle of all datasets
        config: Application configuration
        gnn_embeddings_path: Path to GNN node embeddings
        transformer_embeddings_path: Path to transformer embeddings
        
    Returns:
        Dictionary of artifact paths
    """
    if not TORCH_AVAILABLE:
        LOGGER.warning("PyTorch not available, skipping fusion model training")
        return {}
    
    LOGGER.info("Training multimodal fusion model")
    
    try:
        # Load embeddings if available
        gnn_embeddings = None
        transformer_embeddings = None
        
        if gnn_embeddings_path and gnn_embeddings_path.exists():
            gnn_embeddings = joblib.load(gnn_embeddings_path)
            LOGGER.info("Loaded GNN embeddings: shape %s", gnn_embeddings.shape)
        
        if transformer_embeddings_path and transformer_embeddings_path.exists():
            transformer_embeddings = joblib.load(transformer_embeddings_path)
            LOGGER.info("Loaded Transformer embeddings: shape %s", transformer_embeddings.shape)
        
        # If no embeddings available, skip fusion training
        if gnn_embeddings is None and transformer_embeddings is None:
            LOGGER.warning("No embeddings available for fusion, skipping")
            return {}
        
        # For now, create a simple fusion baseline
        # In production, this would combine all modalities
        
        # Create simple fusion config
        fusion_config = {
            "has_gnn": gnn_embeddings is not None,
            "has_transformer": transformer_embeddings is not None,
            "gnn_dim": gnn_embeddings.shape[1] if gnn_embeddings is not None else 0,
            "transformer_dim": transformer_embeddings.shape[1] if transformer_embeddings is not None else 0,
            "fusion_type": "late_fusion",
            "fusion_weights": {
                "classical": 0.4,
                "gnn": 0.3,
                "transformer": 0.3,
            }
        }
        
        # Save fusion artifacts
        artifact_dir = config.output_dir / "artifacts"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        
        fusion_config_path = artifact_dir / "aegis_fusion_config.json"
        fusion_config_path.write_text(json.dumps(fusion_config, indent=2))
        
        metrics_path = config.output_dir / "fusion_metrics.json"
        metrics = {
            "fusion_type": "late_fusion",
            "modalities_used": ["classical"] + (["gnn"] if gnn_embeddings is not None else []) + (["transformer"] if transformer_embeddings is not None else []),
        }
        metrics_path.write_text(json.dumps(metrics, indent=2))
        
        LOGGER.info("Fusion model configuration saved")
        
        return {
            "fusion_config": fusion_config_path,
            "fusion_metrics": metrics_path,
        }
        
    except Exception as exc:
        LOGGER.error("Fusion model training failed: %s", exc, exc_info=True)
        return {}


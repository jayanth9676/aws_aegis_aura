"""Orchestration for transformer model training."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional

from configs import AppConfig
from data import DatasetBundle

LOGGER = logging.getLogger("aegis.training.transformer_orchestrator")

try:
    from training.transformer_trainer import (
        train_transaction_transformer,
        train_categorical_transformer,
        DEFAULT_SEQUENCE_FEATURES,
    )
    TRANSFORMER_TRAINER_AVAILABLE = True
except ImportError:
    TRANSFORMER_TRAINER_AVAILABLE = False
    LOGGER.warning("Transformer trainer not available")


def train_transformer_models(
    datasets: DatasetBundle,
    config: AppConfig,
    train_data: Optional[Dict] = None,
) -> Dict[str, Path]:
    """
    Orchestrate training of all transformer-based models.
    
    Args:
        datasets: Bundle of all datasets
        config: Application configuration
        train_data: Optional dict with training data from fraud models
        
    Returns:
        Dictionary of artifact paths
    """
    if not TRANSFORMER_TRAINER_AVAILABLE:
        LOGGER.error("Transformer trainer not available")
        return {}
    
    artifacts = {}
    
    # 1. Train transaction sequence transformer
    try:
        LOGGER.info("Training transaction sequence transformer")
        
        # Use default sequence features or extract from train_data
        # Handle both dict and tuple formats for train_data
        feature_cols = None
        if train_data is not None:
            if isinstance(train_data, dict) and "feature_cols" in train_data:
                feature_cols = train_data["feature_cols"]
            elif isinstance(train_data, tuple) and len(train_data) >= 5:
                # Format: (X_train, X_test, y_train, y_test, feature_cols)
                feature_cols = train_data[4]
        
        if feature_cols is not None:
            # Filter to numeric/sequence-friendly features
            sequence_features = [
                col for col in feature_cols
                if col in DEFAULT_SEQUENCE_FEATURES or any(
                    keyword in col for keyword in ["amount", "risk", "score", "ratio", "gap", "sin_", "cos_"]
                )
            ]
        else:
            sequence_features = DEFAULT_SEQUENCE_FEATURES
        
        # Ensure required columns exist
        sequence_features = [
            col for col in sequence_features 
            if col in datasets.transactions.columns
        ]
        
        if not sequence_features:
            LOGGER.warning("No valid sequence features found, using defaults")
            sequence_features = DEFAULT_SEQUENCE_FEATURES
        
        LOGGER.info("Using %d sequence features for transformer", len(sequence_features))
        
        trans_artifacts = train_transaction_transformer(
            datasets.transactions,
            config,
            sequence_features,
        )
        artifacts.update(trans_artifacts)
        LOGGER.info("Transaction transformer training completed")
        
    except Exception as exc:
        LOGGER.error("Transaction transformer training failed: %s", exc, exc_info=True)
    
    # 2. Train categorical feature transformer
    try:
        LOGGER.info("Training categorical feature transformer")
        
        categorical_columns = [
            "payment_channel",
            "device_model",
            "ip_address_country",
            "digital_literacy_level",
            "risk_profile",
        ]
        
        # Filter to columns that exist
        categorical_columns = [
            col for col in categorical_columns
            if col in datasets.transactions.columns
        ]
        
        if categorical_columns:
            cat_artifacts = train_categorical_transformer(
                datasets.transactions,
                categorical_columns,
                config,
            )
            artifacts.update(cat_artifacts)
            LOGGER.info("Categorical transformer training completed")
        else:
            LOGGER.warning("No categorical columns found for transformer training")
        
    except Exception as exc:
        LOGGER.error("Categorical transformer training failed: %s", exc, exc_info=True)
    
    return artifacts


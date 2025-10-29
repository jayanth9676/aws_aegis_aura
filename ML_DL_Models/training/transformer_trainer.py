"""Training utilities for transformer-based fraud detection models."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from configs import AppConfig
from models.preprocessing import encode_categoricals
from models.transformers import (
    TransactionTransformer,
    TransactionTransformerConfig,
    CategoricalFeatureTransformer,
    CategoricalTransformerConfig,
)

LOGGER = logging.getLogger("aegis.training.transformers")


DEFAULT_SEQUENCE_FEATURES = [
    "amount",
    "log_amount",
    "risk_score",
    "risk_score_gap",
    "relative_amount_to_avg",
    "amount_to_daily_limit_ratio",
    "amount_to_monthly_limit_ratio",
    "sin_hour",
    "cos_hour",
    "sin_day_of_week",
    "cos_day_of_week",
    "known_device",
    "device_trust_gap",
    "anomaly_score",
    "hesitation_indicators",
    "typing_pattern_anomaly",
    "copy_paste_detected",
    "new_payee_flag",
    "authentication_failures",
]


def prepare_transaction_sequences(
    transactions: pd.DataFrame,
    sequence_features: List[str],
    max_seq_len: int,
    group_col: str = "customer_id",
) -> Tuple[np.ndarray, np.ndarray]:
    """Create padded transaction sequences and labels.

    Args:
        transactions: DataFrame with transaction features and labels
        sequence_features: List of feature columns to include
        max_seq_len: Maximum sequence length for padding
        group_col: Column to group sequences by (default customer)

    Returns:
        Tuple of (padded_sequences, labels)
    """

    grouped = []
    labels = []

    for _, group in transactions.groupby(group_col):
        sequence = group[sequence_features].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy()
        label = group["is_fraud"].max()

        if len(sequence) == 0:
            continue

        if len(sequence) >= max_seq_len:
            sequence = sequence[-max_seq_len:]
        else:
            padding = np.zeros((max_seq_len - len(sequence), len(sequence_features)))
            sequence = np.vstack([padding, sequence])

        grouped.append(sequence)
        labels.append(label)

    return np.asarray(grouped, dtype=np.float32), np.asarray(labels, dtype=np.float32)


def train_transaction_transformer(
    transactions: pd.DataFrame,
    config: AppConfig,
    feature_columns: Iterable[str],
) -> Dict[str, Path]:
    """Train transformer model on transaction sequences."""

    LOGGER.info("Preparing transaction sequences for transformer training")
    sequences, labels = prepare_transaction_sequences(
        transactions,
        feature_columns,
        config.behavioral_max_seq_len,
        group_col="customer_id",
    )

    if len(sequences) == 0:
        LOGGER.warning("No sequences generated for transformer training")
        return {}

    X_train, X_test, y_train, y_test = train_test_split(
        sequences,
        labels,
        test_size=config.test_size,
        stratify=labels if len(np.unique(labels)) > 1 else None,
        random_state=config.random_state,
    )

    device = torch.device("cuda" if config.enable_gpu and torch.cuda.is_available() else "cpu")

    model_config = TransactionTransformerConfig(
        input_dim=sequences.shape[-1],
        max_seq_len=config.behavioral_max_seq_len,
    )
    model = TransactionTransformer(model_config).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=model_config.learning_rate, weight_decay=model_config.weight_decay)
    criterion = nn.BCELoss()

    tensor_x_train = torch.tensor(X_train, dtype=torch.float32, device=device)
    tensor_y_train = torch.tensor(y_train, dtype=torch.float32, device=device).unsqueeze(1)
    tensor_x_test = torch.tensor(X_test, dtype=torch.float32, device=device)
    tensor_y_test = torch.tensor(y_test, dtype=torch.float32, device=device).unsqueeze(1)

    best_auc = 0.0
    best_state = None
    patience = 5
    patience_counter = 0

    LOGGER.info("Training transaction transformer (%d sequences)", len(sequences))

    for epoch in range(40):
        model.train()
        optimizer.zero_grad()

        outputs = model(tensor_x_train)
        loss = criterion(outputs, tensor_y_train)
        loss.backward()
        optimizer.step()

        if epoch % 2 == 0:
            model.eval()
            with torch.no_grad():
                preds = model(tensor_x_test)
                y_pred = preds.cpu().numpy().flatten()
                y_true = tensor_y_test.cpu().numpy().flatten()

                if len(np.unique(y_true)) > 1:
                    auc = roc_auc_score(y_true, y_pred)
                    ap = average_precision_score(y_true, y_pred)
                    LOGGER.info(
                        "Transformer epoch %d: loss=%.4f auc=%.4f ap=%.4f",
                        epoch,
                        loss.item(),
                        auc,
                        ap,
                    )

                    if auc > best_auc:
                        best_auc = auc
                        best_state = model.state_dict()
                        patience_counter = 0
                    else:
                        patience_counter += 1

                    if patience_counter >= patience:
                        LOGGER.info("Early stopping transformer training at epoch %d", epoch)
                        break

    if best_state is not None:
        model.load_state_dict(best_state)

    artifact_dir = config.output_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    model_path = artifact_dir / "aegis_transaction_transformer.pt"
    config_path = artifact_dir / "aegis_transaction_transformer_config.json"
    embedding_path = artifact_dir / "aegis_transaction_transformer_embeddings.pkl"
    metrics_path = config.output_dir / "transaction_transformer_metrics.json"

    # Final evaluation
    model.eval()
    metrics = {}
    with torch.no_grad():
        if len(np.unique(y_test)) > 1:
            y_pred = model(tensor_x_test).cpu().numpy().flatten()
            y_true = tensor_y_test.cpu().numpy().flatten()
            metrics = {
                "auc": float(roc_auc_score(y_true, y_pred)),
                "ap": float(average_precision_score(y_true, y_pred)),
                "f1": float(f1_score(y_true, (y_pred > 0.5).astype(int))),
                "precision": float(precision_score(y_true, (y_pred > 0.5).astype(int), zero_division=0)),
                "recall": float(recall_score(y_true, (y_pred > 0.5).astype(int))),
            }
            LOGGER.info("Transaction Transformer Final - AUC: %.3f | AP: %.3f | F1: %.3f", 
                       metrics["auc"], metrics["ap"], metrics["f1"])

    torch.save(
        {
            "state_dict": model.state_dict(),
            "config": model_config.__dict__,
            "feature_columns": list(feature_columns),
            "metrics": metrics,
        },
        model_path,
    )

    config_path.write_text(json.dumps(model_config.__dict__, indent=2))
    joblib.dump(sequences.mean(axis=1), embedding_path)
    metrics_path.write_text(json.dumps(metrics, indent=2))

    return {
        "transaction_transformer_model": model_path,
        "transaction_transformer_config": config_path,
        "transaction_transformer_embeddings": embedding_path,
        "transaction_transformer_metrics": metrics_path,
    }


def train_categorical_transformer(
    transactions: pd.DataFrame,
    categorical_columns: List[str],
    config: AppConfig,
) -> Dict[str, Path]:
    """Train transformer on categorical feature interactions."""

    if not categorical_columns:
        LOGGER.warning("No categorical columns provided for categorical transformer")
        return {}

    LOGGER.info("Training categorical transformer on columns: %s", categorical_columns)

    field_cardinalities = {}
    encoded_inputs = {}

    for column in categorical_columns:
        categories = transactions[column].astype("category")
        transactions[f"{column}_encoded"] = categories.cat.codes + 1  # reserve 0 for padding
        field_cardinalities[column] = len(categories.cat.categories)
        encoded_inputs[column] = torch.tensor(transactions[f"{column}_encoded"].values, dtype=torch.long)

    model_config = CategoricalTransformerConfig(field_cardinalities=field_cardinalities)
    model = CategoricalFeatureTransformer(model_config)

    optimizer = torch.optim.AdamW(model.parameters(), lr=model_config.learning_rate, weight_decay=model_config.weight_decay)
    criterion = nn.BCELoss()

    labels = torch.tensor(transactions["is_fraud"].astype(int).values, dtype=torch.float32).unsqueeze(1)

    best_loss = float("inf")
    best_state = None
    patience = 5
    patience_counter = 0

    for epoch in range(30):
        model.train()
        optimizer.zero_grad()

        outputs = model(encoded_inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        if loss.item() < best_loss - 1e-4:
            best_loss = loss.item()
            best_state = model.state_dict()
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    artifact_dir = config.output_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    model_path = artifact_dir / "aegis_categorical_transformer.pt"
    config_path = artifact_dir / "aegis_categorical_transformer_config.json"

    torch.save(
        {
            "state_dict": model.state_dict(),
            "config": model_config.__dict__,
            "field_cardinalities": field_cardinalities,
            "best_loss": best_loss,
        },
        model_path,
    )

    config_path.write_text(json.dumps(model_config.__dict__, indent=2))

    metrics_path = config.output_dir / "categorical_transformer_metrics.json"
    metrics_path.write_text(json.dumps({"best_loss": best_loss}, indent=2))

    return {
        "categorical_transformer_model": model_path,
        "categorical_transformer_config": config_path,
        "categorical_transformer_metrics": metrics_path,
    }



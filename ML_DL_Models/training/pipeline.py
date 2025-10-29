from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple

import json
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import IsolationForest, StackingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler

import lightgbm as lgb
import xgboost as xgb

from configs import AppConfig
from data import DatasetBundle
from features import build_customer_features, build_graph_features, build_transaction_features
from models.multimodal_fusion import FusionConfig, MultiModalFraudFusion
from models.utils import weighted_scale_pos_weight

try:  # pragma: no cover - optional shap
    from monitoring.shap_explainer import compute_shap_for_model, AegisSHAPExplainer
    SHAP_AVAILABLE = True
except ImportError:  # pragma: no cover
    SHAP_AVAILABLE = False

try:  # pragma: no cover - optional gnn
    from training.gnn_trainer import train_gnn_models
    GNN_AVAILABLE = True
except ImportError:  # pragma: no cover
    GNN_AVAILABLE = False

try:  # pragma: no cover - optional transformers
    from training.transformer_orchestrator import train_transformer_models
    TRANSFORMER_AVAILABLE = True
except ImportError:  # pragma: no cover
    TRANSFORMER_AVAILABLE = False

try:  # pragma: no cover - optional rl
    from training.rl_trainer import train_rl_policy
    RL_AVAILABLE = True
except ImportError:  # pragma: no cover
    RL_AVAILABLE = False

try:  # pragma: no cover - optional fusion
    from training.fusion_trainer import train_fusion_model
    FUSION_AVAILABLE = True
except ImportError:  # pragma: no cover
    FUSION_AVAILABLE = False

LOGGER = logging.getLogger("aegis.training")

try:  # pragma: no cover - optional torch
    import torch
    from torch.utils.data import DataLoader, TensorDataset

    from models.autoencoder import TransactionAutoencoder, TransactionAutoencoderConfig
    from models.sequences import BehavioralSequenceConfig, BehavioralSequenceModel, pad_sequences

    TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover
    TORCH_AVAILABLE = False


def compute_shap_for_all_models(artifacts: Dict[str, Path], config: AppConfig, 
                               X_train: np.ndarray, X_test: np.ndarray, 
                               feature_cols: List[str]) -> Dict[str, Path]:
    """Compute SHAP values for all trained models.
    
    Args:
        artifacts: Dictionary of model artifacts
        config: Application configuration
        X_train: Training data
        X_test: Test data
        feature_cols: List of feature names
        
    Returns:
        Dictionary of SHAP artifact paths
    """
    if not SHAP_AVAILABLE:
        LOGGER.warning("SHAP not available, skipping SHAP computation")
        return {}
    
    LOGGER.info("Computing SHAP values for all models")
    shap_artifacts = {}
    artifact_dir = config.output_dir / "artifacts"
    shap_dir = config.output_dir / "shap_plots"
    shap_dir.mkdir(parents=True, exist_ok=True)
    
    # Models to compute SHAP for
    shap_models = {
        'fraud_xgb': ('xgb', 'tree'),
        'fraud_lgb': ('lgb', 'tree'), 
        'fraud_cat': ('cat', 'tree'),
        'fraud_ensemble': ('ensemble', 'tree'),
    }
    
    for model_key, (model_name, model_type) in shap_models.items():
        model_path = artifacts.get(model_key)
        if model_path and model_path.exists():
            try:
                # Load model
                model = joblib.load(model_path)
                
                # Compute SHAP values
                shap_values, shap_summary = compute_shap_for_model(
                    model, X_train, X_test, feature_cols, model_name, model_type
                )
                
                # Save SHAP artifacts
                explainer = AegisSHAPExplainer(X_train[:config.shap_background], feature_cols)
                shap_paths = explainer.save_shap_artifacts(
                    shap_values, shap_summary, model_name, artifact_dir
                )
                shap_artifacts.update({f"{model_key}_{k}": v for k, v in shap_paths.items()})
                
                LOGGER.info("Computed SHAP for %s", model_name)
                
            except Exception as e:
                LOGGER.error("Failed to compute SHAP for %s: %s", model_name, e)
    
    return shap_artifacts


def train_all_models(
    config: AppConfig,
    datasets: DatasetBundle,
    *,
    include_mule_data: bool = True,
    include_gnn: bool = False,
    include_transformers: bool = False,
    include_rl: bool = False,
) -> Dict[str, Path]:
    config.ensure_paths()
    artifact_dir = config.output_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    customer_features = build_customer_features(
        datasets.customers,
        datasets.accounts,
        datasets.transactions,
        call_history=datasets.call_history,
        fraud_alerts=datasets.fraud_alerts,
    )
    transaction_features = build_transaction_features(
        datasets.transactions,
        customer_features,
        behavioral_events=datasets.behavioral_events,
        accounts=datasets.accounts,
        call_history=datasets.call_history,
        fraud_alerts=datasets.fraud_alerts,
    )
    network_features, _ = build_graph_features(datasets.transactions, datasets.accounts)

    _persist_feature_sets(config, customer_features, transaction_features, network_features)

    # Check for existing artifacts and skip training if already completed
    mule_artifacts = {}
    fraud_artifacts = {}
    train_data = None

    # Skip mule training if artifacts exist
    mule_iso_path = artifact_dir / "aegis_mule_iso_forest.pkl"
    mule_xgb_path = artifact_dir / "aegis_mule_xgb.pkl"
    if not (mule_iso_path.exists() and mule_xgb_path.exists()):
        mule_artifacts = train_mule_models(network_features, config)
    else:
        LOGGER.info("Mule detection models already trained, skipping...")
        mule_artifacts = {
            "mule_iso_forest": mule_iso_path,
            "mule_xgb": mule_xgb_path,
            "mule_scaler": artifact_dir / "aegis_mule_scaler.pkl",
            "mule_metrics": config.output_dir / "mule_metrics.json",
        }

    # Skip fraud training if artifacts exist
    fraud_xgb_path = artifact_dir / "aegis_fraud_xgb.pkl"
    fraud_lgb_path = artifact_dir / "aegis_fraud_lgb.pkl"
    fraud_cat_path = artifact_dir / "aegis_fraud_cat.pkl"
    fraud_ensemble_path = artifact_dir / "aegis_fraud_ensemble.pkl"
    if not (fraud_xgb_path.exists() and fraud_lgb_path.exists() and fraud_cat_path.exists() and fraud_ensemble_path.exists()):
        fraud_artifacts, train_data = train_fraud_models(transaction_features, config)
    else:
        LOGGER.info("Fraud detection models already trained, skipping...")
        fraud_artifacts = {
            "fraud_xgb": fraud_xgb_path,
            "fraud_lgb": fraud_lgb_path,
            "fraud_cat": fraud_cat_path,
            "fraud_ensemble": fraud_ensemble_path,
            "fraud_scaler": artifact_dir / "aegis_fraud_scaler.pkl",
            "fraud_metrics": config.output_dir / "fraud_metrics.json",
            "feature_columns": artifact_dir / "aegis_feature_columns.pkl",
            "risk_metadata": artifact_dir / "aegis_scorer_metadata.json",
        }
        # Load train_data if needed for autoencoder
        if TORCH_AVAILABLE:
            try:
                feature_cols = joblib.load(artifact_dir / "aegis_feature_columns.pkl")
                categorical_cols = [
                    "payment_channel",
                    "device_model",
                    "ip_address_country",
                    "digital_literacy_level",
                    "risk_profile",
                ]
                # Ensure categorical encoding for autoencoder
                from models.preprocessing import encode_categoricals
                transaction_features_encoded = encode_categoricals(transaction_features, categorical_cols)

                # Filter to only the features that exist (handle missing encoded columns gracefully)
                available_features = [col for col in feature_cols if col in transaction_features_encoded.columns]
                if len(available_features) != len(feature_cols):
                    missing = set(feature_cols) - set(available_features)
                    LOGGER.warning("Some features not available for autoencoder, using available subset: %s", missing)
                    feature_cols = available_features

                X = transaction_features_encoded[feature_cols].apply(lambda col: pd.to_numeric(col, errors="coerce")).fillna(0)
                y = transaction_features_encoded["is_fraud"].astype(int)
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=config.test_size, stratify=y, random_state=config.random_state
                )
                train_data = (X_train.values, X_test.values, y_train.values, y_test.values, feature_cols)
            except Exception as e:
                LOGGER.warning("Could not load train_data for autoencoder: %s", e)

    sequence_artifacts = {}
    autoencoder_artifacts = {}

    # Skip sequence training if artifacts exist
    sequence_path = artifact_dir / "aegis_behavior_sequence.pt"
    if not sequence_path.exists():
        if TORCH_AVAILABLE:
            try:
                sequence_artifacts = train_behavioral_sequence_model(
                    datasets.behavioral_events,
                    datasets.transactions,
                    config,
                )
            except ValueError as exc:
                LOGGER.warning("Skipping behavioral sequence training: %s", exc)
        else:
            LOGGER.warning("PyTorch not available; skipping sequence model")
    else:
        LOGGER.info("Behavioral sequence model already trained, skipping...")
        sequence_artifacts = {"behavior_sequence_model": sequence_path}

    # Skip autoencoder training if artifacts exist
    autoencoder_path = artifact_dir / "aegis_transaction_autoencoder.pt"
    if not autoencoder_path.exists():
        if TORCH_AVAILABLE and train_data is not None:
            autoencoder_artifacts = train_autoencoder_model(train_data, config)
        elif not TORCH_AVAILABLE:
            LOGGER.warning("PyTorch not available; skipping autoencoder model")
        else:
            LOGGER.warning("No train_data available for autoencoder training")
    else:
        LOGGER.info("Autoencoder model already trained, skipping...")
        autoencoder_artifacts = {
            "transaction_autoencoder": autoencoder_path,
            "transaction_autoencoder_scaler": artifact_dir / "aegis_transaction_autoencoder_scaler.pkl",
            "transaction_autoencoder_metadata": artifact_dir / "aegis_transaction_autoencoder.json",
        }

    gnn_artifacts: Dict[str, Path] = {}
    transformer_artifacts: Dict[str, Path] = {}
    rl_artifacts: Dict[str, Path] = {}
    fusion_artifacts: Dict[str, Path] = {}

    # Train GNN models if requested and data available
    if include_gnn:
        if GNN_AVAILABLE and include_mule_data:
            try:
                LOGGER.info("Training GNN models with mule data enabled")
                gnn_artifacts = train_gnn_models(datasets.transactions, datasets.accounts, config)
                LOGGER.info("GNN training completed")
            except Exception as exc:
                LOGGER.error("GNN training failed: %s", exc, exc_info=True)
        elif not GNN_AVAILABLE:
            LOGGER.warning("GNN dependencies missing; skipping GNN training")
        else:
            LOGGER.info("Mule data disabled; skipping GNN training")

    # Train Transformer models if requested
    if include_transformers:
        if not TORCH_AVAILABLE or not TRANSFORMER_AVAILABLE:
            LOGGER.warning("Transformer dependencies unavailable; skipping transformer training")
        else:
            try:
                LOGGER.info("Training transformer-based models")
                transformer_artifacts = train_transformer_models(
                    datasets,
                    config,
                    train_data,
                )
                LOGGER.info("Transformer training completed")
            except Exception as exc:
                LOGGER.error("Transformer training failed: %s", exc, exc_info=True)

    # Train RL policy if requested
    if include_rl:
        if not RL_AVAILABLE:
            LOGGER.warning("RL dependencies unavailable; skipping RL training")
        else:
            try:
                LOGGER.info("Training reinforcement learning policy")
                rl_artifacts = train_rl_policy(datasets.transactions, config)
                LOGGER.info("RL training completed")
            except Exception as exc:
                LOGGER.error("RL training failed: %s", exc, exc_info=True)

    artifacts = {
        **mule_artifacts,
        **fraud_artifacts,
        **sequence_artifacts,
        **autoencoder_artifacts,
        **gnn_artifacts,
        **transformer_artifacts,
        **rl_artifacts,
        **fusion_artifacts,
    }
    
    # Compute SHAP values for fraud models if available
    if train_data is not None and SHAP_AVAILABLE:
        try:
            X_train, X_test, y_train, y_test, feature_cols = train_data
            shap_artifacts = compute_shap_for_all_models(artifacts, config, X_train, X_test, feature_cols)
            artifacts.update(shap_artifacts)
            LOGGER.info("SHAP computation completed for %d models", len(shap_artifacts) // 3)
        except Exception as e:
            LOGGER.error("Failed to compute SHAP values: %s", e)

    # Train fusion model if both GNN and transformer embeddings exist
    if include_gnn and include_transformers and gnn_artifacts and transformer_artifacts:
        if not FUSION_AVAILABLE:
            LOGGER.warning("Fusion trainer not available, skipping fusion training")
        else:
            try:
                LOGGER.info("Training multimodal fusion model")
                fusion_artifacts = train_fusion_model(
                    datasets,
                    config,
                    gnn_artifacts.get("gnn_node_embeddings"),
                    transformer_artifacts.get("transaction_transformer_embeddings"),
                )
                LOGGER.info("Fusion model training completed")
                artifacts.update(fusion_artifacts)
            except Exception as exc:
                LOGGER.error("Fusion training failed: %s", exc, exc_info=True)
    
    return artifacts


def train_autoencoder_only(config: AppConfig) -> Dict[str, Path]:
    """Train only the autoencoder model, assuming fraud models are already trained."""
    config.ensure_paths()
    artifact_dir = config.output_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Check if fraud models exist (required for autoencoder training)
    fraud_ensemble_path = artifact_dir / "aegis_fraud_ensemble.pkl"
    if not fraud_ensemble_path.exists():
        raise ValueError("Fraud models must be trained first before training autoencoder. Run full training pipeline.")

    LOGGER.info("Loading datasets for autoencoder training")
    from data import load_datasets
    datasets = load_datasets(config)

    # Build features (same as full pipeline)
    customer_features = build_customer_features(
        datasets.customers,
        datasets.accounts,
        datasets.transactions,
        call_history=datasets.call_history,
        fraud_alerts=datasets.fraud_alerts,
    )
    transaction_features = build_transaction_features(
        datasets.transactions,
        customer_features,
        behavioral_events=datasets.behavioral_events,
        accounts=datasets.accounts,
        call_history=datasets.call_history,
        fraud_alerts=datasets.fraud_alerts,
    )

    # Load fraud model artifacts to get feature columns and prepare train_data
    try:
        feature_cols = joblib.load(artifact_dir / "aegis_feature_columns.pkl")
        categorical_cols = [
            "payment_channel",
            "device_model",
            "ip_address_country",
            "digital_literacy_level",
            "risk_profile",
        ]
        # Ensure categorical encoding for autoencoder
        from models.preprocessing import encode_categoricals
        transaction_features_encoded = encode_categoricals(transaction_features, categorical_cols)

        # Filter to only the features that exist
        available_features = [col for col in feature_cols if col in transaction_features_encoded.columns]
        if len(available_features) != len(feature_cols):
            missing = set(feature_cols) - set(available_features)
            LOGGER.warning("Some features not available, using available subset: %s", missing)
            feature_cols = available_features

        X = transaction_features_encoded[feature_cols].apply(lambda col: pd.to_numeric(col, errors="coerce")).fillna(0)
        y = transaction_features_encoded["is_fraud"].astype(int)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=config.test_size, stratify=y, random_state=config.random_state
        )
        train_data = (X_train.values, X_test.values, y_train.values, y_test.values, feature_cols)

        # Train autoencoder
        if TORCH_AVAILABLE:
            LOGGER.info("Training autoencoder model")
            autoencoder_artifacts = train_autoencoder_model(train_data, config)
            LOGGER.info("Autoencoder training completed")
            return autoencoder_artifacts
        else:
            LOGGER.warning("PyTorch not available; cannot train autoencoder")
            return {}

    except Exception as e:
        LOGGER.error("Failed to train autoencoder: %s", e)
        raise


def train_mule_models(network_features: pd.DataFrame, config: AppConfig) -> Dict[str, Path]:
    LOGGER.info("Training mule detection models")

    # Check for positive samples
    mule_count = network_features["is_mule_account"].sum()
    LOGGER.info(f"Mule accounts found: {mule_count} out of {len(network_features)} total accounts")

    if mule_count == 0:
        LOGGER.warning("No mule accounts found in dataset, skipping mule detection training")
        return {}

    feature_cols = [
        "in_degree",
        "out_degree",
        "total_degree",
        "pagerank_centrality",
        "betweenness_centrality",
        "in_flow",
        "out_flow",
        "flow_ratio",
        "avg_transaction_amount",
    ]
    X = network_features[feature_cols].fillna(0)
    y = network_features["is_mule_account"].astype(int)

    # Handle stratification for imbalanced data
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=config.test_size, stratify=y, random_state=config.random_state
        )
    except ValueError:
        # Fallback if stratification fails (e.g., too few positive samples)
        LOGGER.warning("Stratification failed for mule detection, using random split")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=config.test_size, random_state=config.random_state
        )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    iso_forest = IsolationForest(
        contamination=0.05, random_state=config.random_state, n_jobs=-1
    )
    iso_forest.fit(X_train_scaled)

    param_grid = {
        "max_depth": [4, 6, 8],
        "learning_rate": [0.05, 0.1, 0.2],
        "n_estimators": [200, 300, 400],
        "subsample": [0.7, 0.9],
        "colsample_bytree": [0.7, 0.9],
    }

    base_xgb = xgb.XGBClassifier(
        objective="binary:logistic",
        eval_metric="auc",
        random_state=config.random_state,
        n_jobs=-1,
        scale_pos_weight=weighted_scale_pos_weight(y_train),
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=config.random_state)
    search = RandomizedSearchCV(
        estimator=base_xgb,
        param_distributions=param_grid,
        n_iter=10,
        scoring="roc_auc",
        cv=cv,
        random_state=config.random_state,
        n_jobs=-1,
        verbose=0,
    )
    search.fit(X_train, y_train)
    best_xgb = search.best_estimator_

    calibrated_xgb = CalibratedClassifierCV(best_xgb, method="isotonic", cv=cv)
    calibrated_xgb.fit(X_train, y_train)

    y_pred = calibrated_xgb.predict(X_test)
    y_prob = calibrated_xgb.predict_proba(X_test)[:, 1]

    metrics = {
        "auc": roc_auc_score(y_test, y_prob),
        "average_precision": average_precision_score(y_test, y_prob),
        "f1": f1_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred),
    }
    LOGGER.info("Mule Detection – AUC: %.3f | AP: %.3f | F1: %.3f", metrics["auc"], metrics["average_precision"], metrics["f1"])

    artifact_dir = config.output_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    iso_path = artifact_dir / "aegis_mule_iso_forest.pkl"
    xgb_path = artifact_dir / "aegis_mule_xgb.pkl"
    scaler_path = artifact_dir / "aegis_mule_scaler.pkl"
    metrics_path = config.output_dir / "mule_metrics.json"

    joblib.dump(iso_forest, iso_path)
    joblib.dump(calibrated_xgb, xgb_path)
    joblib.dump(scaler, scaler_path)
    metrics_path.write_text(pd.Series(metrics).to_json())

    return {
        "mule_iso_forest": iso_path,
        "mule_xgb": xgb_path,
        "mule_scaler": scaler_path,
        "mule_metrics": metrics_path,
    }


def train_fraud_models(transaction_features: pd.DataFrame, config: AppConfig) -> Tuple[Dict[str, Path], Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str]]]:
    LOGGER.info("Training fraud detection models")
    categorical_cols = [
        "payment_channel",
        "device_model",
        "ip_address_country",
        "digital_literacy_level",
        "risk_profile",
    ]

    from models.preprocessing import encode_categoricals

    transaction_features = encode_categoricals(transaction_features, categorical_cols)
    feature_cols = [
        "amount",
        "log_amount",
        "hour",
        "day_of_week",
        "is_weekend",
        "is_night",
        "is_business_hours",
        "is_round_amount",
        "sin_hour",
        "cos_hour",
        "sin_day_of_week",
        "cos_day_of_week",
        "age",
        "annual_income",
        "vulnerability_score",
        "credit_score",
        "customer_tenure_years",
        "txn_per_month",
        "alert_to_txn_ratio",
        "call_to_txn_ratio",
        "risk_velocity",
        "risk_score",
        "risk_score_gap",
        "known_device",
        "device_trust_gap",
        "anomaly_score",
        "hesitation_indicators",
        "typing_pattern_anomaly",
        "copy_paste_detected",
        "new_payee_flag",
        "authentication_failures",
        "txn_call_count",
        "txn_escalation_rate",
        "txn_high_priority_rate",
        "txn_avg_alert_risk_score",
        "txn_avg_false_positive_prob",
        "hours_since_last_alert",
        "hours_since_last_call",
        "relative_amount_to_avg",
        "amount_to_daily_limit_ratio",
        "amount_to_monthly_limit_ratio",
        "location_risk_score",
        "amount_risk_score",
        "velocity_risk_score",
    ] + [f"{col}_encoded" for col in categorical_cols if f"{col}_encoded" in transaction_features.columns]

    feature_cols = [col for col in feature_cols if col in transaction_features.columns]

    X = transaction_features[feature_cols].apply(lambda col: pd.to_numeric(col, errors="coerce")).fillna(0)
    y = transaction_features["is_fraud"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.test_size, stratify=y, random_state=config.random_state
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    xgb_model = xgb.XGBClassifier(
        objective="binary:logistic",
        eval_metric="aucpr",
        random_state=config.random_state,
        n_jobs=-1,
    )
    xgb_param_dist = {
        "max_depth": [6, 8, 10],
        "learning_rate": [0.05, 0.1, 0.2],
        "n_estimators": [300, 400, 500],
        "subsample": [0.7, 0.85, 1.0],
        "colsample_bytree": [0.7, 0.85, 1.0],
        "min_child_weight": [1, 3, 5],
        "gamma": [0, 1, 5],
        "scale_pos_weight": [weighted_scale_pos_weight(y_train)],
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=config.random_state)
    xgb_search = RandomizedSearchCV(
        xgb_model,
        xgb_param_dist,
        n_iter=15,
        scoring="average_precision",
        cv=cv,
        n_jobs=-1,
        random_state=config.random_state,
        verbose=0,
    )
    xgb_search.fit(X_train, y_train)
    fraud_xgb_best = xgb_search.best_estimator_

    lgb_model = lgb.LGBMClassifier(
        objective="binary",
        class_weight="balanced",
        random_state=config.random_state,
        n_jobs=-1,
    )
    lgb_param_dist = {
        "num_leaves": [31, 63, 127],
        "max_depth": [-1, 10, 20],
        "learning_rate": [0.05, 0.1, 0.2],
        "n_estimators": [300, 500, 700],
        "subsample": [0.7, 0.9, 1.0],
        "colsample_bytree": [0.7, 0.9, 1.0],
    }
    lgb_search = RandomizedSearchCV(
        lgb_model,
        lgb_param_dist,
        n_iter=15,
        scoring="average_precision",
        cv=cv,
        n_jobs=-1,
        random_state=config.random_state,
        verbose=0,
    )
    lgb_search.fit(X_train, y_train)
    fraud_lgb_best = lgb_search.best_estimator_

    from catboost import CatBoostClassifier

    cat_model = CatBoostClassifier(
        depth=8,
        learning_rate=0.1,
        iterations=400,
        loss_function="Logloss",
        eval_metric="AUC",
        class_weights=[1.0, weighted_scale_pos_weight(y_train)],
        random_seed=config.random_state,
        verbose=False,
    )
    cat_model.fit(X_train, y_train)

    fraud_xgb_cal = CalibratedClassifierCV(fraud_xgb_best, method="isotonic", cv=cv)
    fraud_lgb_cal = CalibratedClassifierCV(fraud_lgb_best, method="isotonic", cv=cv)
    fraud_xgb_cal.fit(X_train, y_train)
    fraud_lgb_cal.fit(X_train, y_train)

    # Use a simpler weighted ensemble instead of stacking
    ensemble = VotingClassifier(
        estimators=[
            ("xgb", fraud_xgb_cal),
            ("lgb", fraud_lgb_cal),
            ("cat", cat_model),
        ],
        voting="soft",  # Use probability-based voting
        weights=[0.4, 0.4, 0.2],  # Give more weight to tree-based models
        n_jobs=-1,
    )
    ensemble.fit(X_train, y_train)

    results = {}
    for name, model in {
        "xgb": fraud_xgb_cal,
        "lgb": fraud_lgb_cal,
        "cat": cat_model,
        "ensemble": ensemble,
    }.items():
        pred = model.predict(X_test)
        if hasattr(model, "predict_proba"):
            prob = model.predict_proba(X_test)[:, 1]
        else:
            prob = model.predict(X_test)
        results[name] = {
            "auc": roc_auc_score(y_test, prob),
            "average_precision": average_precision_score(y_test, prob),
            "f1": f1_score(y_test, pred),
            "precision": precision_score(y_test, pred, zero_division=0),
            "recall": recall_score(y_test, pred),
        }
        LOGGER.info(
            "%s – AUC: %.3f | AP: %.3f | F1: %.3f | P: %.3f | R: %.3f",
            name,
            results[name]["auc"],
            results[name]["average_precision"],
            results[name]["f1"],
            results[name]["precision"],
            results[name]["recall"],
        )

    artifact_dir = config.output_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "fraud_xgb": artifact_dir / "aegis_fraud_xgb.pkl",
        "fraud_lgb": artifact_dir / "aegis_fraud_lgb.pkl",
        "fraud_cat": artifact_dir / "aegis_fraud_cat.pkl",
        "fraud_ensemble": artifact_dir / "aegis_fraud_ensemble.pkl",
        "fraud_scaler": artifact_dir / "aegis_fraud_scaler.pkl",
        "fraud_metrics": config.output_dir / "fraud_metrics.json",
        "feature_columns": artifact_dir / "aegis_feature_columns.pkl",
        "risk_metadata": artifact_dir / "aegis_scorer_metadata.json",
    }

    joblib.dump(fraud_xgb_cal, paths["fraud_xgb"])
    joblib.dump(fraud_lgb_cal, paths["fraud_lgb"])
    joblib.dump(cat_model, paths["fraud_cat"])
    joblib.dump(ensemble, paths["fraud_ensemble"])
    joblib.dump(scaler, paths["fraud_scaler"])
    joblib.dump(feature_cols, paths["feature_columns"])
    paths["fraud_metrics"].write_text(pd.DataFrame(results).to_json())
    paths["risk_metadata"].write_text(
        json.dumps(
            {
                "categorical_columns": categorical_cols,
                "fusion_weights": {"ensemble": 0.6, "sequence": 0.25, "autoencoder": 0.15},
            },
            indent=2,
        )
    )

    train_data = {
        "X_train": X_train.values,
        "X_test": X_test.values,
        "y_train": y_train.values,
        "y_test": y_test.values,
        "feature_cols": feature_cols,
        "X_train_df": X_train.copy(),
        "X_test_df": X_test.copy(),
        "y_train_series": y_train.copy(),
        "y_test_series": y_test.copy(),
    }

    return paths, train_data


def train_behavioral_sequence_model(
    behavioral_events: pd.DataFrame,
    transactions: pd.DataFrame,
    config: AppConfig,
) -> Dict[str, Path]:
    if not TORCH_AVAILABLE:
        LOGGER.warning("PyTorch not available, skipping behavioral sequence model training.")
        return {}

    if behavioral_events.empty:
        LOGGER.warning("No behavioral events available, skipping sequence model training.")
        return {}

    LOGGER.info("Training behavioral sequence model")

    # Import torch locally to ensure it's available
    import torch
    from torch.utils.data import DataLoader, TensorDataset

    merged = behavioral_events.merge(
        transactions[["transaction_id", "is_fraud"]],
        on="transaction_id",
        how="inner",
    )

    feature_cols = [
        "anomaly_score",
        "typing_pattern_anomaly",
        "session_duration_seconds",
        "hesitation_indicators",
    ]
    for col in ["copy_paste_detected", "new_payee_flag", "authentication_failures"]:
        if col in merged.columns:
            merged[col] = merged[col].astype(str).str.lower().isin(["1", "true", "yes"]).astype(int)
            feature_cols.append(col)

    merged.sort_values("event_timestamp", inplace=True)

    sequences: List[np.ndarray] = []
    labels: List[int] = []

    for txn_id, group in merged.groupby("transaction_id"):
        seq = group[feature_cols].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy(dtype=np.float32)
        if not len(seq):
            continue
        sequences.append(seq)
        labels.append(int(group["is_fraud"].iloc[0]))

    if not sequences:
        raise ValueError("Behavioral events did not produce sequences")

    max_len = config.behavioral_max_seq_len
    padded = pad_sequences(np.array(sequences, dtype=object), max_len)
    y = np.asarray(labels, dtype=np.float32)

    dataset = TensorDataset(torch.tensor(padded), torch.tensor(y).unsqueeze(1))
    loader = DataLoader(dataset, batch_size=64, shuffle=True)

    model_config = BehavioralSequenceConfig(input_dim=padded.shape[-1])
    model = BehavioralSequenceModel(model_config)
    criterion = torch.nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)

    best_loss = float("inf")
    patience = 5
    patience_counter = 0
    best_state = model.state_dict()

    for epoch in range(30):
        model.train()
        epoch_loss = 0.0
        for batch_x, batch_y in loader:
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        epoch_loss /= max(len(loader), 1)
        if epoch_loss < best_loss - 1e-4:
            best_loss = epoch_loss
            patience_counter = 0
            best_state = model.state_dict()
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    model.load_state_dict(best_state)

    artifact_dir = config.output_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / "aegis_behavior_sequence.pt"
    import torch

    torch.save(
        {
            "state_dict": model.state_dict(),
            "config": model_config.__dict__,
            "feature_columns": feature_cols,
            "max_len": max_len,
        },
        path,
    )

    return {"behavior_sequence_model": path}


def train_autoencoder_model(train_data: Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str]], config: AppConfig) -> Dict[str, Path]:
    if not TORCH_AVAILABLE:
        LOGGER.warning("PyTorch unavailable; skipping autoencoder training")
        return {}

    X_train, X_test, y_train, y_test, feature_cols = train_data
    benign_train = X_train[y_train == 0]
    if benign_train.size == 0:
        LOGGER.warning("No non-fraud samples available for autoencoder training")
        return {}

    LOGGER.info("Training transaction autoencoder model")

    # Import torch locally to ensure it's available
    import torch
    from torch.utils.data import DataLoader, TensorDataset

    scaler = StandardScaler()
    benign_scaled = scaler.fit_transform(benign_train)
    X_test_scaled = scaler.transform(X_test)

    model_config = TransactionAutoencoderConfig(input_dim=benign_scaled.shape[1], hidden_dim=config.autoencoder_hidden_dim)
    model = TransactionAutoencoder(model_config)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)
    criterion = torch.nn.MSELoss()

    dataset = TensorDataset(torch.tensor(benign_scaled, dtype=torch.float32))
    loader = DataLoader(dataset, batch_size=256, shuffle=True)

    model.train()
    for epoch in range(50):
        epoch_loss = 0.0
        for (batch_x,) in loader:
            optimizer.zero_grad()
            recon = model(batch_x)
            loss = criterion(recon, batch_x)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        if epoch % 10 == 0:
            LOGGER.info("Autoencoder epoch %s loss %.4f", epoch, epoch_loss / max(len(loader), 1))

    model.eval()
    with torch.no_grad():
        recon_errors = model.reconstruction_error(torch.tensor(benign_scaled, dtype=torch.float32)).numpy()
        test_errors = model.reconstruction_error(torch.tensor(X_test_scaled, dtype=torch.float32)).numpy()

    threshold = float(np.mean(recon_errors) + 3 * np.std(recon_errors))
    metadata = {
        "threshold": threshold,
        "mean_error": float(np.mean(recon_errors)),
        "std_error": float(np.std(recon_errors) + 1e-6),
        "feature_columns": feature_cols,
    }

    artifact_dir = config.output_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifact_dir / "aegis_transaction_autoencoder.pt"
    scaler_path = artifact_dir / "aegis_transaction_autoencoder_scaler.pkl"
    metadata_path = artifact_dir / "aegis_transaction_autoencoder.json"

    import torch

    torch.save({"state_dict": model.state_dict(), "config": model_config.__dict__}, model_path)
    joblib.dump(scaler, scaler_path)
    metadata_path.write_text(json.dumps(metadata, indent=2))

    return {
        "transaction_autoencoder": model_path,
        "transaction_autoencoder_scaler": scaler_path,
        "transaction_autoencoder_metadata": metadata_path,
    }


def _persist_feature_sets(
    config: AppConfig,
    customer_features: pd.DataFrame,
    transaction_features: pd.DataFrame,
    network_features: pd.DataFrame,
) -> None:
    feature_dir = config.output_dir / "features"
    feature_dir.mkdir(parents=True, exist_ok=True)
    _write_table(customer_features, feature_dir / "customer_features.parquet")
    _write_table(transaction_features, feature_dir / "transaction_features.parquet")
    _write_table(network_features, feature_dir / "network_features.parquet")


def _write_table(df: pd.DataFrame, path: Path) -> None:
    try:
        # Convert object columns to string to avoid type issues
        df_copy = df.copy()
        for col in df_copy.select_dtypes(include=['object']).columns:
            df_copy[col] = df_copy[col].astype(str)
        df_copy.to_parquet(path, index=False)
    except (ImportError, ModuleNotFoundError, Exception) as e:
        LOGGER.warning("Parquet writing failed (%s); using CSV fallback for %s", str(e), path.name)
        csv_path = path.with_suffix(".csv")
        df.to_csv(csv_path, index=False)




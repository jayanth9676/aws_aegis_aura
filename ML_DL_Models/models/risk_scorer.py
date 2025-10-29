from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd

try:
    import torch
except ImportError:  # pragma: no cover
    torch = None  # type: ignore

TORCH_AVAILABLE = torch is not None

from features import build_customer_features, build_transaction_features
from models.preprocessing import encode_categoricals
from models.utils import prepare_numeric

try:  # pragma: no cover - optional shap
    from monitoring.shap_explainer import load_shap_artifacts
    SHAP_AVAILABLE = True
except ImportError:  # pragma: no cover
    SHAP_AVAILABLE = False


@dataclass
class AegisRiskScorer:
    fraud_models: Dict[str, Any]
    feature_columns: List[str]
    categorical_columns: List[str]
    sequence_model: Optional[Any] = None
    sequence_config: Optional[Dict[str, Any]] = None
    sequence_pad_fn: Optional[Callable[[np.ndarray, int], np.ndarray]] = None
    autoencoder: Optional[Any] = None
    autoencoder_scaler: Optional[Any] = None
    autoencoder_threshold: Optional[float] = None
    autoencoder_mean: Optional[float] = None
    autoencoder_std: Optional[float] = None
    shap_artifacts: Optional[Dict[str, Any]] = None

    def score_transaction(
        self,
        transaction_data: Dict[str, Any],
        customer_data: Dict[str, Any],
        account_data: Optional[Dict[str, Any]] = None,
        call_history: Optional[List[Dict[str, Any]]] = None,
        fraud_alerts: Optional[List[Dict[str, Any]]] = None,
        behavioral_events: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        transactions_df = pd.DataFrame([transaction_data])
        customers_df = pd.DataFrame([customer_data])
        accounts_df = pd.DataFrame(account_data) if account_data else pd.DataFrame()
        call_history_df = pd.DataFrame(call_history or [])
        fraud_alerts_df = pd.DataFrame(fraud_alerts or [])
        behavioral_df = pd.DataFrame(behavioral_events or [])

        customer_features = build_customer_features(
            customers_df,
            accounts_df,
            transactions_df,
            call_history=call_history_df,
            fraud_alerts=fraud_alerts_df,
        )
        transaction_features = build_transaction_features(
            transactions_df,
            customer_features,
            behavioral_events=behavioral_df,
            accounts=accounts_df,
            call_history=call_history_df,
            fraud_alerts=fraud_alerts_df,
        )
        transaction_features = encode_categoricals(transaction_features, self.categorical_columns)

        for col in self.feature_columns:
            if col not in transaction_features.columns:
                transaction_features[col] = 0

        X = prepare_numeric(transaction_features[self.feature_columns])

        scores = {}
        for name, model in self.fraud_models.items():
            try:
                prob = float(model.predict_proba(X)[:, 1][0])
            except AttributeError:
                prob = float(model.predict(X)[0])
            scores[name] = prob

        ensemble_score = float(sum(scores.values()) / len(scores))
        sequence_score = None
        if (
            TORCH_AVAILABLE
            and self.sequence_model is not None
            and self.sequence_config is not None
            and self.sequence_pad_fn is not None
            and behavioral_df is not None
            and not behavioral_df.empty
        ):
            sequence_score = self._sequence_score(behavioral_df)

        autoencoder_score = None
        if (
            TORCH_AVAILABLE
            and self.autoencoder is not None
            and self.autoencoder_scaler is not None
            and self.autoencoder_threshold is not None
            and self.autoencoder_mean is not None
            and self.autoencoder_std is not None
        ):
            autoencoder_score = self._autoencoder_score(X)

        fusion_score = _fuse_scores(ensemble_score, sequence_score, autoencoder_score)
        risk_level, action = _risk_bucket(fusion_score)

        return {
            "overall_risk_score": round(fusion_score, 4),
            "risk_level": risk_level,
            "recommended_action": action,
            "model_scores": {k: round(v, 4) for k, v in scores.items()},
            "timestamp": datetime.utcnow().isoformat(),
            "sequence_score": None if sequence_score is None else round(sequence_score, 4),
            "autoencoder_score": None if autoencoder_score is None else round(autoencoder_score, 4),
        }

    def explain_prediction(
        self,
        transaction_data: Dict[str, Any],
        customer_data: Dict[str, Any],
        account_data: Optional[Dict[str, Any]] = None,
        call_history: Optional[List[Dict[str, Any]]] = None,
        fraud_alerts: Optional[List[Dict[str, Any]]] = None,
        behavioral_events: Optional[List[Dict[str, Any]]] = None,
        model_name: str = "ensemble",
    ) -> Dict[str, Any]:
        """Explain a prediction using SHAP values.
        
        Args:
            transaction_data: Transaction data
            customer_data: Customer data
            account_data: Account data (optional)
            call_history: Call history (optional)
            fraud_alerts: Fraud alerts (optional)
            behavioral_events: Behavioral events (optional)
            model_name: Name of model to explain
            
        Returns:
            Dictionary with explanation details
        """
        if not SHAP_AVAILABLE or self.shap_artifacts is None:
            return {"error": "SHAP explanations not available"}
        
        # Get the base prediction
        prediction = self.score_transaction(
            transaction_data, customer_data, account_data,
            call_history, fraud_alerts, behavioral_events
        )
        
        # Prepare feature data for SHAP
        transactions_df = pd.DataFrame([transaction_data])
        customers_df = pd.DataFrame([customer_data])
        accounts_df = pd.DataFrame(account_data) if account_data else pd.DataFrame()
        call_history_df = pd.DataFrame(call_history or [])
        fraud_alerts_df = pd.DataFrame(fraud_alerts or [])
        behavioral_df = pd.DataFrame(behavioral_events or [])

        customer_features = build_customer_features(
            customers_df,
            accounts_df,
            transactions_df,
            call_history=call_history_df,
            fraud_alerts=fraud_alerts_df,
        )
        transaction_features = build_transaction_features(
            transactions_df,
            customer_features,
            behavioral_events=behavioral_df,
            accounts=accounts_df,
            call_history=call_history_df,
            fraud_alerts=fraud_alerts_df,
        )
        transaction_features = encode_categoricals(transaction_features, self.categorical_columns)

        # Ensure all features are present
        for col in self.feature_columns:
            if col not in transaction_features.columns:
                transaction_features[col] = 0

        X = prepare_numeric(transaction_features[self.feature_columns])
        
        # Get SHAP values for the specified model
        shap_key = f"fraud_{model_name}_shap_values"
        if shap_key not in self.shap_artifacts:
            return {"error": f"SHAP values not available for model: {model_name}"}
        
        shap_values = self.shap_artifacts[shap_key]
        shap_summary = self.shap_artifacts.get(f"fraud_{model_name}_shap_summary", {})
        
        # Get feature importance for this prediction
        if len(shap_values.shape) > 1:
            # For batch prediction, take first sample
            sample_shap = shap_values[0] if len(shap_values) > 0 else np.zeros(len(self.feature_columns))
        else:
            sample_shap = shap_values
        
        # Create feature explanation
        feature_explanations = []
        for i, (feature, shap_val) in enumerate(zip(self.feature_columns, sample_shap)):
            feature_explanations.append({
                "feature": feature,
                "shap_value": round(float(shap_val), 4),
                "feature_value": round(float(X.iloc[0, i]), 4),
                "contribution": "positive" if shap_val > 0 else "negative"
            })
        
        # Sort by absolute SHAP value
        feature_explanations.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        
        return {
            "prediction": prediction,
            "model_explained": model_name,
            "feature_explanations": feature_explanations[:10],  # Top 10 features
            "global_feature_importance": shap_summary.get("top_features", [])[:10],
            "explanation_summary": {
                "total_features": len(self.feature_columns),
                "positive_contributors": len([f for f in feature_explanations if f["shap_value"] > 0]),
                "negative_contributors": len([f for f in feature_explanations if f["shap_value"] < 0]),
                "top_contributor": feature_explanations[0] if feature_explanations else None,
            }
        }


    def _sequence_score(self, behavioral_df: pd.DataFrame) -> float:
        if not TORCH_AVAILABLE:
            return 0.0
        feature_cols = self.sequence_config["feature_columns"]
        max_len = self.sequence_config["max_len"]

        df = behavioral_df[feature_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
        seq = df.to_numpy(dtype=np.float32)
        padded = self.sequence_pad_fn(np.array([seq], dtype=object), max_len)
        tensor = torch.tensor(padded, dtype=torch.float32)
        self.sequence_model.eval()
        with torch.no_grad():
            score = float(self.sequence_model(tensor).numpy().flatten()[0])
        return score

    def _autoencoder_score(self, X: pd.DataFrame) -> float:
        if not TORCH_AVAILABLE:
            return 0.0
        data = self.autoencoder_scaler.transform(X)
        tensor = torch.tensor(data, dtype=torch.float32)
        self.autoencoder.eval()
        with torch.no_grad():
            error = float(self.autoencoder.reconstruction_error(tensor).numpy()[0])
        z = (error - self.autoencoder_mean) / (self.autoencoder_std + 1e-6)
        normalized = 1 / (1 + np.exp(-z))
        return normalized


def _risk_bucket(score: float) -> tuple[str, str]:
    if score >= 0.95:
        return "CRITICAL", "BLOCK_IMMEDIATELY"
    if score >= 0.8:
        return "HIGH", "BLOCK_AND_REVIEW"
    if score >= 0.6:
        return "MEDIUM", "FLAG_FOR_REVIEW"
    return "LOW", "ALLOW"


def load_risk_scorer(artifact_dir: Path) -> AegisRiskScorer:
    fraud_ensemble = joblib.load(artifact_dir / "aegis_fraud_ensemble.pkl")
    fraud_xgb = joblib.load(artifact_dir / "aegis_fraud_xgb.pkl")
    fraud_lgb = joblib.load(artifact_dir / "aegis_fraud_lgb.pkl")
    fraud_cat = joblib.load(artifact_dir / "aegis_fraud_cat.pkl")
    feature_columns = joblib.load(artifact_dir / "aegis_feature_columns.pkl")

    metadata_path = artifact_dir / "aegis_scorer_metadata.json"
    metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
    categorical_columns = metadata.get(
        "categorical_columns",
        [
            "payment_channel",
            "device_model",
            "ip_address_country",
            "digital_literacy_level",
            "risk_profile",
        ],
    )

    sequence_model = None
    sequence_config = None
    sequence_pad_fn: Optional[Callable[[np.ndarray, int], np.ndarray]] = None
    sequence_path = artifact_dir / "aegis_behavior_sequence.pt"
    if TORCH_AVAILABLE and sequence_path.exists():
        from models.sequences import BehavioralSequenceConfig, BehavioralSequenceModel, pad_sequences

        checkpoint = torch.load(sequence_path, map_location=torch.device("cpu"))
        config = checkpoint["config"]
        sequence_model = BehavioralSequenceModel(BehavioralSequenceConfig(**config))
        sequence_model.load_state_dict(checkpoint["state_dict"])
        sequence_config = {
            "feature_columns": checkpoint.get("feature_columns", []),
            "max_len": checkpoint.get("max_len", 32),
        }
        sequence_pad_fn = pad_sequences

    auto_model = None
    auto_scaler = None
    auto_threshold = None
    auto_mean = None
    auto_std = None
    auto_path = artifact_dir / "aegis_transaction_autoencoder.pt"
    auto_scaler_path = artifact_dir / "aegis_transaction_autoencoder_scaler.pkl"
    auto_metadata_path = artifact_dir / "aegis_transaction_autoencoder.json"
    if (
        TORCH_AVAILABLE
        and auto_path.exists()
        and auto_scaler_path.exists()
        and auto_metadata_path.exists()
    ):
        from models.autoencoder import TransactionAutoencoder, TransactionAutoencoderConfig

        checkpoint = torch.load(auto_path, map_location=torch.device("cpu"))
        config = checkpoint["config"]
        auto_model = TransactionAutoencoder(TransactionAutoencoderConfig(**config))
        auto_model.load_state_dict(checkpoint["state_dict"])
        auto_scaler = joblib.load(auto_scaler_path)
        metadata = json.loads(auto_metadata_path.read_text())
        auto_threshold = metadata.get("threshold")
        auto_mean = metadata.get("mean_error")
        auto_std = metadata.get("std_error")

    return AegisRiskScorer(
        fraud_models={
            "ensemble": fraud_ensemble,
            "xgb": fraud_xgb,
            "lgb": fraud_lgb,
            "cat": fraud_cat,
        },
        feature_columns=feature_columns,
        categorical_columns=categorical_columns,
        sequence_model=sequence_model,
        sequence_config=sequence_config,
        sequence_pad_fn=sequence_pad_fn,
        autoencoder=auto_model,
        autoencoder_scaler=auto_scaler,
        autoencoder_threshold=auto_threshold,
        autoencoder_mean=auto_mean,
        autoencoder_std=auto_std,
        shap_artifacts=_load_shap_artifacts(artifact_dir),
    )


def _load_shap_artifacts(artifact_dir: Path) -> Optional[Dict[str, Any]]:
    """Load SHAP artifacts if available.
    
    Args:
        artifact_dir: Directory containing SHAP artifacts
        
    Returns:
        Dictionary of SHAP artifacts or None if not available
    """
    if not SHAP_AVAILABLE:
        return None
    
    shap_artifacts = {}
    shap_models = ['fraud_xgb', 'fraud_lgb', 'fraud_cat', 'fraud_ensemble']
    
    for model_name in shap_models:
        shap_values, shap_summary = load_shap_artifacts(model_name, artifact_dir)
        if shap_values is not None and shap_summary is not None:
            shap_artifacts[f"{model_name}_shap_values"] = shap_values
            shap_artifacts[f"{model_name}_shap_summary"] = shap_summary
    
    return shap_artifacts if shap_artifacts else None


def _fuse_scores(ensemble_score: float, sequence_score: Optional[float], auto_score: Optional[float]) -> float:
    weights = {"ensemble": 0.6, "sequence": 0.25, "auto": 0.15}
    total = ensemble_score * weights["ensemble"]
    denom = weights["ensemble"]
    if sequence_score is not None:
        total += sequence_score * weights["sequence"]
        denom += weights["sequence"]
    if auto_score is not None:
        total += auto_score * weights["auto"]
        denom += weights["auto"]
    return total / denom if denom else ensemble_score



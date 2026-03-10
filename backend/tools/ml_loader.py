"""ML Loader — Loads real trained ML models from the ML_DL_Models directory."""

import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from utils import get_logger

logger = get_logger("tools.ml_loader")

# Path to the actual ML models trained by the data science team
ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "ML_DL_Models" / "model_output" / "artifacts"

class ModelRegistry:
    """Lazy loader for real ML models."""
    
    _instance = None
    
    def __init__(self):
        self.fraud_ensemble = None
        self.fraud_scaler = None
        self.feature_columns = None
        self.cat_shap_values = None
        
        self.mule_iso_forest = None
        self.mule_xgb = None
        self.mule_scaler = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_artifact(self, filename: str):
        path = ARTIFACTS_DIR / filename
        if not path.exists():
            logger.warning(f"ML artifact not found: {path}")
            return None
        logger.info(f"Loading ML artifact: {filename}")
        return joblib.load(path)

    def get_fraud_model(self):
        if self.fraud_ensemble is None:
            self.fraud_ensemble = self._load_artifact("aegis_fraud_ensemble.pkl")
            self.fraud_scaler = self._load_artifact("aegis_fraud_scaler.pkl")
            self.feature_columns = self._load_artifact("aegis_feature_columns.pkl")
        return self.fraud_ensemble, self.fraud_scaler, self.feature_columns

    def get_mule_models(self):
        if self.mule_iso_forest is None:
            self.mule_iso_forest = self._load_artifact("aegis_mule_iso_forest.pkl")
            self.mule_xgb = self._load_artifact("aegis_mule_xgb.pkl")
            self.mule_scaler = self._load_artifact("aegis_mule_scaler.pkl")
        return self.mule_iso_forest, self.mule_xgb, self.mule_scaler

    def predict_fraud(self, features_dict: dict) -> dict:
        """Predict fraud using the real trained ensemble."""
        model, scaler, cols = self.get_fraud_model()
        if not model or not cols:
            logger.error("Fraud models not found! Using fallback.")
            return {"fraud_probability": 0.5, "confidence": 0.3}

        # Map dict to DataFrame matching the training data shape
        df = pd.DataFrame([features_dict])
        
        # Fill missing columns that model expects with 0
        for col in cols:
            if col not in df.columns:
                df[col] = 0.0
                
        # Reorder to match exactly
        df = df[cols]

        # Scale features
        # Note: Scaler expects 2D array of same shape it was trained on
        X_scaled = df.copy()
        try:
            if scaler:
                X_scaled[cols] = scaler.transform(df[cols])
        except Exception as e:
            logger.warning(f"Scaling failed, proceeding with raw: {e}")

        # Predict probability
        try:
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(X_scaled)
                # XGBoost/LightGBM predict_proba returns [prob_class_0, prob_class_1]
                # Stacking/Voting Classifiers usually do too.
                # If binary, class 1 is fraud.
                prob = float(probs[0][1]) if probs.shape[1] > 1 else float(probs[0])
            else:
                prob = float(model.predict(X_scaled)[0])

            return {
                "fraud_probability": prob,
                "confidence": 0.85, # Base confidence for the ensemble
                "model_version": "march_2026_ensemble",
                "model_type": "voting_classifier",
                "features_used": len(cols)
            }
        except Exception as e:
            logger.error(f"Fraud prediction failed: {e}")
            return {"fraud_probability": 0.5, "confidence": 0.3}

    def predict_mule(self, features_dict: dict) -> dict:
        """Predict mule account using Isolation Forest + XGBoost."""
        iso_model, xgb_model, scaler = self.get_mule_models()
        if not iso_model or not xgb_model:
            logger.error("Mule models not found! Using fallback.")
            return {"score": 0.1, "pattern": "normal"}

        # Define expected graph features (simplified based on typical graph extraction)
        expected_cols = [
            'in_degree', 'out_degree', 'avg_time_between_transactions',
            'circular_paths', 'intermediary_count', 'total_transactions',
            'total_nodes'
        ]
        
        df = pd.DataFrame([features_dict])
        for col in expected_cols:
            if col not in df.columns:
                df[col] = 0.0
        df = df[expected_cols]

        try:
            if scaler:
                X_scaled = scaler.transform(df)
            else:
                X_scaled = df.values

            # Isolation Forest anomaly score (-1 for anomaly, 1 for normal)
            iso_pred = iso_model.predict(X_scaled)[0]
            
            # XGB probability 
            xgb_prob = float(xgb_model.predict_proba(X_scaled)[0][1])

            # Combine scores (simplified)
            # If Isolation forest says anomaly (-1) and XGB says high prob
            score = xgb_prob
            if iso_pred == -1:
                score = min(1.0, score + 0.2)

            # Determine pattern
            pattern = 'normal'
            in_deg = features_dict.get('in_degree', 0)
            out_deg = features_dict.get('out_degree', 0)
            if in_deg > 10 and out_deg > 10:
                pattern = 'fan_in_fan_out'
            elif out_deg > 10:
                pattern = 'fan_out'
            elif in_deg > 10:
                pattern = 'fan_in'
            elif features_dict.get('circular_paths', 0) > 0:
                pattern = 'circular'
                
            return {
                "score": score,
                "pattern": pattern,
                "confidence": 0.82,
                "risk_level": "HIGH" if score > 0.7 else "MEDIUM" if score > 0.4 else "LOW"
            }
            
        except Exception as e:
            logger.error(f"Mule prediction failed: {e}")
            return {"score": 0.1, "pattern": "normal"}

registry = ModelRegistry.get_instance()

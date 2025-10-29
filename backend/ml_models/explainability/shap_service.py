"""SHAP explainability service for fraud detection models."""

import os
import pickle
from typing import Dict, List, Tuple
from decimal import Decimal
import numpy as np

try:
    import shap
except ImportError:
    shap = None
    
from utils import get_logger
from config import aws_config

logger = get_logger(__name__)


class SHAPExplainer:
    """SHAP explanation generator for ensemble fraud detection models."""
    
    def __init__(self):
        """Initialize SHAP explainer."""
        self.s3_client = aws_config.s3
        self.model_bucket = os.getenv('ML_MODELS_BUCKET', f'aegis-ml-models-{os.getenv("AWS_ACCOUNT_ID")}')
        self.explainers = {}
        self.feature_names = self._load_feature_names()
    
    def _load_feature_names(self) -> List[str]:
        """Load feature names from S3."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.model_bucket,
                Key='models/feature_names.txt'
            )
            feature_names = response['Body'].read().decode('utf-8').strip().split('\n')
            logger.info(f"Loaded {len(feature_names)} feature names")
            return feature_names
        except Exception as e:
            logger.warning(f"Failed to load feature names from S3, using defaults", error=str(e))
            # Return default feature names based on common fraud detection features
            return self._get_default_feature_names()
    
    def _get_default_feature_names(self) -> List[str]:
        """Get default feature names for fraud detection."""
        return [
            'transaction_amount',
            'amount_vs_median',
            'transaction_count_24h',
            'transaction_count_7d',
            'transaction_count_30d',
            'unique_payees_24h',
            'unique_payees_7d',
            'unique_payees_30d',
            'is_new_payee',
            'days_since_last_transaction',
            'hour_of_day',
            'day_of_week',
            'is_weekend',
            'is_night_time',
            'customer_age_days',
            'customer_risk_tier',
            'payee_cop_match_level',
            'payee_on_watchlist',
            'payee_known_mule',
            'device_anomaly_score',
            'location_anomaly_score',
            'behavioral_anomaly_score',
            'active_call_detected',
            'typing_speed_anomaly',
            'mouse_movement_anomaly',
            'navigation_anomaly',
            'session_duration',
            'payment_channel_encoded',
            'payment_type_encoded',
            'customer_vulnerability_flag'
        ]
    
    def _load_explainer(self, model_name: str) -> shap.TreeExplainer:
        """Load SHAP explainer for model from cache or S3.
        
        Args:
            model_name: Name of the model (xgboost, lightgbm, catboost)
            
        Returns:
            SHAP TreeExplainer instance
        """
        if model_name in self.explainers:
            return self.explainers[model_name]
        
        try:
            # Load model from S3
            model_key = f'models/{model_name}_model.pkl'
            response = self.s3_client.get_object(
                Bucket=self.model_bucket,
                Key=model_key
            )
            model = pickle.loads(response['Body'].read())
            
            # Create TreeExplainer
            explainer = shap.TreeExplainer(model)
            
            # Cache explainer
            self.explainers[model_name] = explainer
            
            logger.info(f"Loaded SHAP explainer for {model_name}")
            return explainer
            
        except Exception as e:
            logger.error(f"Failed to load explainer for {model_name}", error=str(e))
            raise
    
    def explain_prediction(
        self,
        model_name: str,
        features: List[float],
        prediction: float
    ) -> Dict:
        """Generate SHAP explanation for prediction.
        
        Args:
            model_name: Model name (xgboost, lightgbm, catboost)
            features: Feature vector
            prediction: Model prediction (fraud probability)
            
        Returns:
            Dict with SHAP values and top features
        """
        if not shap:
            logger.warning("SHAP library not available, returning mock explanation")
            return self._generate_mock_explanation(features, prediction)
        
        try:
            # Load explainer
            explainer = self._load_explainer(model_name)
            
            # Calculate SHAP values
            features_array = np.array([features])
            shap_values = explainer.shap_values(features_array)
            
            # Handle binary classification output
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Take positive class
            
            # Get SHAP values for this instance
            instance_shap_values = shap_values[0] if len(shap_values.shape) > 1 else shap_values
            
            # Get top contributing features
            top_features = self._get_top_features(features, instance_shap_values)
            
            return {
                'model_name': model_name,
                'prediction': float(prediction),
                'shap_values': [float(v) for v in instance_shap_values],
                'feature_names': self.feature_names,
                'feature_values': [float(v) for v in features],
                'top_features': top_features,
                'base_value': float(explainer.expected_value[1] if isinstance(explainer.expected_value, np.ndarray) else explainer.expected_value)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate SHAP explanation", model_name=model_name, error=str(e))
            return self._generate_mock_explanation(features, prediction)
    
    def _get_top_features(
        self,
        features: List[float],
        shap_values: np.ndarray,
        top_k: int = 5
    ) -> List[Dict]:
        """Get top K contributing features.
        
        Args:
            features: Feature values
            shap_values: SHAP values
            top_k: Number of top features to return
            
        Returns:
            List of dicts with feature name, value, and contribution
        """
        # Get absolute SHAP values for ranking
        abs_shap_values = np.abs(shap_values)
        
        # Get indices of top K features
        top_indices = np.argsort(abs_shap_values)[-top_k:][::-1]
        
        # Build top features list
        top_features = []
        for idx in top_indices:
            feature_name = self.feature_names[idx] if idx < len(self.feature_names) else f"feature_{idx}"
            feature_value = features[idx] if idx < len(features) else 0.0
            shap_contribution = float(shap_values[idx])
            
            top_features.append({
                'name': feature_name,
                'value': float(feature_value),
                'contribution': shap_contribution,
                'abs_contribution': abs(shap_contribution)
            })
        
        return top_features
    
    def _generate_mock_explanation(self, features: List[float], prediction: float) -> Dict:
        """Generate mock explanation when SHAP is unavailable.
        
        Args:
            features: Feature vector
            prediction: Prediction value
            
        Returns:
            Mock SHAP explanation
        """
        # Generate synthetic SHAP values based on feature importance heuristics
        mock_shap_values = []
        for i, feature_value in enumerate(features):
            # Simple heuristic: higher values contribute more
            contribution = (feature_value / 100.0) * (prediction - 0.5) * np.random.uniform(0.5, 1.5)
            mock_shap_values.append(contribution)
        
        # Get top features
        top_features = []
        sorted_indices = sorted(range(len(mock_shap_values)), key=lambda i: abs(mock_shap_values[i]), reverse=True)[:5]
        
        for idx in sorted_indices:
            feature_name = self.feature_names[idx] if idx < len(self.feature_names) else f"feature_{idx}"
            feature_value = features[idx] if idx < len(features) else 0.0
            
            top_features.append({
                'name': feature_name,
                'value': float(feature_value),
                'contribution': mock_shap_values[idx],
                'abs_contribution': abs(mock_shap_values[idx])
            })
        
        return {
            'model_name': 'mock',
            'prediction': float(prediction),
            'shap_values': mock_shap_values,
            'feature_names': self.feature_names,
            'feature_values': [float(v) for v in features],
            'top_features': top_features,
            'base_value': 0.5,
            'is_mock': True
        }
    
    def explain_ensemble(
        self,
        model_predictions: Dict[str, float],
        features: List[float],
        ensemble_weights: Dict[str, float] = None
    ) -> Dict:
        """Generate ensemble explanation from multiple models.
        
        Args:
            model_predictions: Dict of model_name -> prediction
            features: Feature vector
            ensemble_weights: Model weights for ensemble
            
        Returns:
            Combined SHAP explanation
        """
        if ensemble_weights is None:
            ensemble_weights = {
                'xgboost': 0.4,
                'lightgbm': 0.4,
                'catboost': 0.2
            }
        
        explanations = {}
        combined_shap_values = np.zeros(len(features))
        
        # Get explanation for each model
        for model_name, prediction in model_predictions.items():
            if model_name in ensemble_weights:
                explanation = self.explain_prediction(model_name, features, prediction)
                explanations[model_name] = explanation
                
                # Weight SHAP values
                weight = ensemble_weights[model_name]
                model_shap_values = np.array(explanation['shap_values'])
                combined_shap_values += weight * model_shap_values
        
        # Calculate weighted ensemble prediction
        ensemble_prediction = sum(
            model_predictions[model] * ensemble_weights.get(model, 0.0)
            for model in model_predictions
        )
        
        # Get top features from combined SHAP values
        top_features = self._get_top_features(features, combined_shap_values)
        
        return {
            'ensemble_prediction': float(ensemble_prediction),
            'model_predictions': {k: float(v) for k, v in model_predictions.items()},
            'ensemble_weights': ensemble_weights,
            'combined_shap_values': [float(v) for v in combined_shap_values],
            'feature_names': self.feature_names,
            'feature_values': [float(v) for v in features],
            'top_features': top_features,
            'individual_explanations': explanations
        }


# Global SHAP explainer instance
_shap_explainer = None


def get_shap_explainer() -> SHAPExplainer:
    """Get global SHAP explainer instance."""
    global _shap_explainer
    if _shap_explainer is None:
        _shap_explainer = SHAPExplainer()
    return _shap_explainer


def generate_shap_explanation(
    model_name: str,
    features: List[float],
    prediction: float
) -> Dict:
    """Generate SHAP explanation for prediction.
    
    Convenience function that uses global explainer instance.
    
    Args:
        model_name: Model name
        features: Feature vector
        prediction: Model prediction
        
    Returns:
        SHAP explanation dict
    """
    explainer = get_shap_explainer()
    return explainer.explain_prediction(model_name, features, prediction)


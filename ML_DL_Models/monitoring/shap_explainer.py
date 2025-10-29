"""SHAP explainability utilities for Aegis ML models."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
import shap

LOGGER = logging.getLogger("aegis.monitoring.shap")


class AegisSHAPExplainer:
    """Centralized SHAP explainer for all Aegis models."""
    
    def __init__(self, background_data: np.ndarray, feature_names: List[str]):
        """Initialize SHAP explainer with background data.
        
        Args:
            background_data: Background dataset for SHAP computation
            feature_names: List of feature names
        """
        self.background_data = background_data
        self.feature_names = feature_names
        self.explainers: Dict[str, Any] = {}
        
    def create_tree_explainer(self, model: Any, model_name: str) -> shap.TreeExplainer:
        """Create TreeExplainer for tree-based models (XGBoost, LightGBM, CatBoost).
        
        Args:
            model: Trained tree-based model (may be wrapped in CalibratedClassifierCV)
            model_name: Name identifier for the model
            
        Returns:
            TreeExplainer instance
        """
        try:
            # Unwrap the model if it's wrapped in CalibratedClassifierCV
            from sklearn.calibration import CalibratedClassifierCV
            base_model = model
            if isinstance(model, CalibratedClassifierCV):
                # Use the first calibrated classifier's base estimator
                if hasattr(model, 'calibrated_classifiers_') and len(model.calibrated_classifiers_) > 0:
                    base_model = model.calibrated_classifiers_[0].estimator
                    LOGGER.info("Unwrapped CalibratedClassifierCV for %s", model_name)
            
            explainer = shap.TreeExplainer(base_model)
            self.explainers[model_name] = explainer
            LOGGER.info("Created TreeExplainer for %s", model_name)
            return explainer
        except Exception as e:
            LOGGER.error("Failed to create TreeExplainer for %s: %s", model_name, e)
            raise
    
    def create_linear_explainer(self, model: Any, model_name: str) -> shap.LinearExplainer:
        """Create LinearExplainer for linear models.
        
        Args:
            model: Trained linear model
            model_name: Name identifier for the model
            
        Returns:
            LinearExplainer instance
        """
        try:
            explainer = shap.LinearExplainer(model, self.background_data)
            self.explainers[model_name] = explainer
            LOGGER.info("Created LinearExplainer for %s", model_name)
            return explainer
        except Exception as e:
            LOGGER.error("Failed to create LinearExplainer for %s: %s", model_name, e)
            raise
    
    def create_deep_explainer(self, model: Any, model_name: str, 
                            background_sample: Optional[np.ndarray] = None) -> shap.DeepExplainer:
        """Create DeepExplainer for neural network models.
        
        Args:
            model: Trained neural network model
            model_name: Name identifier for the model
            background_sample: Background sample for SHAP computation
            
        Returns:
            DeepExplainer instance
        """
        try:
            background = background_sample if background_sample is not None else self.background_data
            explainer = shap.DeepExplainer(model, background)
            self.explainers[model_name] = explainer
            LOGGER.info("Created DeepExplainer for %s", model_name)
            return explainer
        except Exception as e:
            LOGGER.error("Failed to create DeepExplainer for %s: %s", model_name, e)
            raise
    
    def compute_shap_values(self, model: Any, X: np.ndarray, model_name: str, 
                          model_type: str = "tree") -> Tuple[np.ndarray, Dict[str, Any]]:
        """Compute SHAP values for a model.
        
        Args:
            model: Trained model
            X: Input data for SHAP computation
            model_name: Name identifier for the model
            model_type: Type of model ("tree", "linear", "deep", "ensemble")
            
        Returns:
            Tuple of (shap_values, shap_summary)
        """
        try:
            # Check if this is a VotingClassifier (ensemble) - use Kernel explainer instead
            from sklearn.ensemble import VotingClassifier
            if isinstance(model, VotingClassifier):
                LOGGER.info("Using KernelExplainer for VotingClassifier %s", model_name)
                # Use a smaller background sample for kernel explainer (it's slower)
                background_sample = shap.sample(self.background_data, min(100, len(self.background_data)))
                explainer = shap.KernelExplainer(model.predict_proba, background_sample)
                self.explainers[model_name] = explainer
                # Compute SHAP values (only for positive class)
                shap_values = explainer.shap_values(X[:min(500, len(X))])  # Limit samples for speed
                if isinstance(shap_values, list) and len(shap_values) == 2:
                    shap_values = shap_values[1]  # Positive class
                # Pad with zeros if we limited samples
                if len(shap_values) < len(X):
                    LOGGER.warning("Limited SHAP computation to %d samples for ensemble model", len(shap_values))
                    X = X[:len(shap_values)]
            else:
                if model_name not in self.explainers:
                    if model_type == "tree" or model_type == "ensemble":
                        explainer = self.create_tree_explainer(model, model_name)
                    elif model_type == "linear":
                        explainer = self.create_linear_explainer(model, model_name)
                    elif model_type == "deep":
                        explainer = self.create_deep_explainer(model, model_name)
                    else:
                        raise ValueError(f"Unsupported model_type: {model_type}")
                else:
                    explainer = self.explainers[model_name]
                
                # Compute SHAP values
                shap_values = explainer.shap_values(X)
                
                # Handle binary classification (take positive class)
                if isinstance(shap_values, list) and len(shap_values) == 2:
                    shap_values = shap_values[1]  # Take positive class
            
            # Create summary statistics
            shap_summary = self._create_shap_summary(shap_values, X)
            
            LOGGER.info("Computed SHAP values for %s: shape %s", model_name, shap_values.shape)
            return shap_values, shap_summary
            
        except Exception as e:
            LOGGER.error("Failed to compute SHAP values for %s: %s", model_name, e)
            raise
    
    def _create_shap_summary(self, shap_values: np.ndarray, X: np.ndarray) -> Dict[str, Any]:
        """Create summary statistics from SHAP values.
        
        Args:
            shap_values: SHAP values array
            X: Original input data
            
        Returns:
            Dictionary with SHAP summary statistics
        """
        # Feature importance (mean absolute SHAP values)
        feature_importance = np.abs(shap_values).mean(axis=0)
        
        # Create DataFrame with feature names
        shap_df = pd.DataFrame({
            'feature': self.feature_names,
            'mean_abs_shap': feature_importance,
            'mean_shap': shap_values.mean(axis=0),
            'std_shap': shap_values.std(axis=0),
            'min_shap': shap_values.min(axis=0),
            'max_shap': shap_values.max(axis=0),
        }).sort_values('mean_abs_shap', ascending=False)
        
        # Global statistics
        summary = {
            'feature_importance': shap_df.to_dict('records'),
            'global_stats': {
                'total_features': len(self.feature_names),
                'mean_abs_shap': float(np.abs(shap_values).mean()),
                'std_abs_shap': float(np.abs(shap_values).std()),
                'max_abs_shap': float(np.abs(shap_values).max()),
            },
            'top_features': shap_df.head(10).to_dict('records'),
        }
        
        return summary
    
    def save_shap_artifacts(self, shap_values: np.ndarray, shap_summary: Dict[str, Any],
                          model_name: str, output_dir: Path) -> Dict[str, Path]:
        """Save SHAP values and summary to files.
        
        Args:
            shap_values: SHAP values array
            shap_summary: SHAP summary statistics
            model_name: Name identifier for the model
            output_dir: Output directory for artifacts
            
        Returns:
            Dictionary of saved file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save SHAP values
        shap_values_path = output_dir / f"{model_name}_shap_values.pkl"
        joblib.dump(shap_values, shap_values_path)
        
        # Save SHAP summary
        shap_summary_path = output_dir / f"{model_name}_shap_summary.json"
        import json
        shap_summary_path.write_text(json.dumps(shap_summary, indent=2))
        
        # Save feature importance CSV
        feature_importance_path = output_dir / f"{model_name}_feature_importance.csv"
        pd.DataFrame(shap_summary['feature_importance']).to_csv(
            feature_importance_path, index=False
        )
        
        LOGGER.info("Saved SHAP artifacts for %s to %s", model_name, output_dir)
        
        return {
            'shap_values': shap_values_path,
            'shap_summary': shap_summary_path,
            'feature_importance': feature_importance_path,
        }


def compute_shap_for_model(model: Any, X_train: np.ndarray, X_test: np.ndarray,
                          feature_names: List[str], model_name: str,
                          model_type: str = "tree", 
                          background_size: int = 500) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Convenience function to compute SHAP values for a single model.
    
    Args:
        model: Trained model
        X_train: Training data
        X_test: Test data for SHAP computation
        feature_names: List of feature names
        model_name: Name identifier for the model
        model_type: Type of model ("tree", "linear", "deep")
        background_size: Size of background sample for SHAP
        
    Returns:
        Tuple of (shap_values, shap_summary)
    """
    # Sample background data
    if len(X_train) > background_size:
        background_indices = np.random.choice(len(X_train), background_size, replace=False)
        background_data = X_train[background_indices]
    else:
        background_data = X_train
    
    # Create explainer
    explainer = AegisSHAPExplainer(background_data, feature_names)
    
    # Compute SHAP values
    return explainer.compute_shap_values(model, X_test, model_name, model_type)


def load_shap_artifacts(model_name: str, artifact_dir: Path) -> Tuple[Optional[np.ndarray], Optional[Dict[str, Any]]]:
    """Load SHAP artifacts for a model.
    
    Args:
        model_name: Name identifier for the model
        artifact_dir: Directory containing SHAP artifacts
        
    Returns:
        Tuple of (shap_values, shap_summary)
    """
    shap_values_path = artifact_dir / f"{model_name}_shap_values.pkl"
    shap_summary_path = artifact_dir / f"{model_name}_shap_summary.json"
    
    shap_values = None
    shap_summary = None
    
    if shap_values_path.exists():
        shap_values = joblib.load(shap_values_path)
        LOGGER.info("Loaded SHAP values for %s", model_name)
    
    if shap_summary_path.exists():
        import json
        shap_summary = json.loads(shap_summary_path.read_text())
        LOGGER.info("Loaded SHAP summary for %s", model_name)
    
    return shap_values, shap_summary

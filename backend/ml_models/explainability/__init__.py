"""SHAP explainability module for Aegis fraud prevention platform."""

from .shap_service import SHAPExplainer, generate_shap_explanation

__all__ = ['SHAPExplainer', 'generate_shap_explanation']


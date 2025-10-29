"""SHAP visualization utilities for Aegis ML models."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import shap

LOGGER = logging.getLogger("aegis.monitoring.shap_viz")


class AegisSHAPVisualizer:
    """SHAP visualization generator for Aegis models."""
    
    def __init__(self, output_dir: Path):
        """Initialize visualizer with output directory.
        
        Args:
            output_dir: Directory to save visualization plots
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style
        plt.style.use('default')
        sns.set_palette("husl")
        
    def create_summary_plot(self, shap_values: np.ndarray, X: np.ndarray,
                          feature_names: List[str], model_name: str,
                          plot_type: str = "dot", max_display: int = 20) -> Path:
        """Create SHAP summary plot.
        
        Args:
            shap_values: SHAP values array
            X: Original input data
            feature_names: List of feature names
            model_name: Name identifier for the model
            plot_type: Type of plot ("dot", "bar", "violin")
            max_display: Maximum number of features to display
            
        Returns:
            Path to saved plot
        """
        try:
            # Create SHAP Explanation object
            explanation = shap.Explanation(
                values=shap_values,
                base_values=np.zeros(len(shap_values)),  # Assuming binary classification
                data=X,
                feature_names=feature_names
            )
            
            # Create plot
            plt.figure(figsize=(12, 8))
            
            if plot_type == "dot":
                shap.plots.beeswarm(explanation, max_display=max_display, show=False)
            elif plot_type == "bar":
                shap.plots.bar(explanation, max_display=max_display, show=False)
            elif plot_type == "violin":
                shap.plots.violin(explanation, max_display=max_display, show=False)
            else:
                raise ValueError(f"Unsupported plot_type: {plot_type}")
            
            plt.title(f"SHAP Summary Plot - {model_name} ({plot_type})")
            plt.tight_layout()
            
            # Save plot
            plot_path = self.output_dir / f"{model_name}_shap_summary_{plot_type}.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            LOGGER.info("Created SHAP summary plot for %s: %s", model_name, plot_path)
            return plot_path
            
        except Exception as e:
            LOGGER.error("Failed to create summary plot for %s: %s", model_name, e)
            plt.close()
            raise
    
    def create_waterfall_plot(self, shap_values: np.ndarray, X: np.ndarray,
                            feature_names: List[str], model_name: str,
                            sample_idx: int = 0) -> Path:
        """Create SHAP waterfall plot for individual prediction.
        
        Args:
            shap_values: SHAP values array
            X: Original input data
            feature_names: List of feature names
            model_name: Name identifier for the model
            sample_idx: Index of sample to explain
            
        Returns:
            Path to saved plot
        """
        try:
            # Create SHAP Explanation object for single sample
            explanation = shap.Explanation(
                values=shap_values[sample_idx],
                base_values=0.0,  # Assuming binary classification
                data=X[sample_idx],
                feature_names=feature_names
            )
            
            # Create waterfall plot
            plt.figure(figsize=(10, 8))
            shap.plots.waterfall(explanation, show=False)
            plt.title(f"SHAP Waterfall Plot - {model_name} (Sample {sample_idx})")
            plt.tight_layout()
            
            # Save plot
            plot_path = self.output_dir / f"{model_name}_shap_waterfall_sample_{sample_idx}.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            LOGGER.info("Created SHAP waterfall plot for %s: %s", model_name, plot_path)
            return plot_path
            
        except Exception as e:
            LOGGER.error("Failed to create waterfall plot for %s: %s", model_name, e)
            plt.close()
            raise
    
    def create_dependence_plot(self, shap_values: np.ndarray, X: np.ndarray,
                             feature_names: List[str], model_name: str,
                             feature_idx: int, interaction_idx: Optional[int] = None) -> Path:
        """Create SHAP dependence plot for feature interactions.
        
        Args:
            shap_values: SHAP values array
            X: Original input data
            feature_names: List of feature names
            model_name: Name identifier for the model
            feature_idx: Index of feature to plot
            interaction_idx: Index of interaction feature (optional)
            
        Returns:
            Path to saved plot
        """
        try:
            # Create SHAP Explanation object
            explanation = shap.Explanation(
                values=shap_values,
                base_values=np.zeros(len(shap_values)),
                data=X,
                feature_names=feature_names
            )
            
            # Create dependence plot
            plt.figure(figsize=(10, 8))
            
            if interaction_idx is not None:
                shap.plots.scatter(
                    explanation[:, feature_idx],
                    color=explanation[:, interaction_idx],
                    show=False
                )
                plt.title(f"SHAP Dependence Plot - {model_name}\n"
                         f"{feature_names[feature_idx]} vs {feature_names[interaction_idx]}")
            else:
                shap.plots.scatter(explanation[:, feature_idx], show=False)
                plt.title(f"SHAP Dependence Plot - {model_name}\n{feature_names[feature_idx]}")
            
            plt.tight_layout()
            
            # Save plot
            interaction_suffix = f"_vs_{feature_names[interaction_idx]}" if interaction_idx is not None else ""
            plot_path = self.output_dir / f"{model_name}_shap_dependence_{feature_names[feature_idx]}{interaction_suffix}.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            LOGGER.info("Created SHAP dependence plot for %s: %s", model_name, plot_path)
            return plot_path
            
        except Exception as e:
            LOGGER.error("Failed to create dependence plot for %s: %s", model_name, e)
            plt.close()
            raise
    
    def create_force_plot(self, shap_values: np.ndarray, X: np.ndarray,
                        feature_names: List[str], model_name: str,
                        sample_idx: int = 0) -> Path:
        """Create SHAP force plot for individual prediction.
        
        Args:
            shap_values: SHAP values array
            X: Original input data
            feature_names: List of feature names
            model_name: Name identifier for the model
            sample_idx: Index of sample to explain
            
        Returns:
            Path to saved HTML plot
        """
        try:
            # Create SHAP Explanation object for single sample
            explanation = shap.Explanation(
                values=shap_values[sample_idx],
                base_values=0.0,
                data=X[sample_idx],
                feature_names=feature_names
            )
            
            # Create force plot
            force_plot = shap.plots.force(explanation, show=False)
            
            # Save as HTML
            plot_path = self.output_dir / f"{model_name}_shap_force_sample_{sample_idx}.html"
            shap.save_html(str(plot_path), force_plot)
            
            LOGGER.info("Created SHAP force plot for %s: %s", model_name, plot_path)
            return plot_path
            
        except Exception as e:
            LOGGER.error("Failed to create force plot for %s: %s", model_name, e)
            raise
    
    def create_feature_importance_comparison(self, shap_summaries: Dict[str, Dict[str, Any]],
                                           top_n: int = 15) -> Path:
        """Create comparison plot of feature importance across models.
        
        Args:
            shap_summaries: Dictionary of model_name -> shap_summary
            top_n: Number of top features to display
            
        Returns:
            Path to saved plot
        """
        try:
            # Extract top features for each model
            model_features = {}
            for model_name, summary in shap_summaries.items():
                top_features = summary['top_features'][:top_n]
                model_features[model_name] = {
                    feat['feature']: feat['mean_abs_shap'] 
                    for feat in top_features
                }
            
            # Create comparison DataFrame
            all_features = set()
            for features in model_features.values():
                all_features.update(features.keys())
            
            comparison_df = pd.DataFrame(index=list(all_features))
            for model_name, features in model_features.items():
                comparison_df[model_name] = comparison_df.index.map(features)
            
            comparison_df = comparison_df.fillna(0)
            
            # Create heatmap
            plt.figure(figsize=(12, max(8, len(all_features) * 0.4)))
            sns.heatmap(comparison_df, annot=True, fmt='.3f', cmap='YlOrRd', cbar_kws={'label': 'Mean |SHAP|'})
            plt.title(f'Feature Importance Comparison Across Models (Top {top_n} Features)')
            plt.xlabel('Models')
            plt.ylabel('Features')
            plt.tight_layout()
            
            # Save plot
            plot_path = self.output_dir / "feature_importance_comparison.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            LOGGER.info("Created feature importance comparison plot: %s", plot_path)
            return plot_path
            
        except Exception as e:
            LOGGER.error("Failed to create feature importance comparison: %s", e)
            plt.close()
            raise
    
    def generate_model_report(self, model_name: str, shap_values: np.ndarray,
                            X: np.ndarray, feature_names: List[str],
                            shap_summary: Dict[str, Any]) -> Dict[str, Path]:
        """Generate comprehensive SHAP report for a model.
        
        Args:
            model_name: Name identifier for the model
            shap_values: SHAP values array
            X: Original input data
            feature_names: List of feature names
            shap_summary: SHAP summary statistics
            
        Returns:
            Dictionary of generated plot paths
        """
        LOGGER.info("Generating SHAP report for %s", model_name)
        
        plots = {}
        
        try:
            # Summary plots
            plots['summary_dot'] = self.create_summary_plot(
                shap_values, X, feature_names, model_name, "dot"
            )
            plots['summary_bar'] = self.create_summary_plot(
                shap_values, X, feature_names, model_name, "bar"
            )
            
            # Waterfall plot for first sample
            plots['waterfall'] = self.create_waterfall_plot(
                shap_values, X, feature_names, model_name, 0
            )
            
            # Force plot for first sample
            plots['force'] = self.create_force_plot(
                shap_values, X, feature_names, model_name, 0
            )
            
            # Dependence plots for top 3 features
            top_features = shap_summary['top_features'][:3]
            for i, feat in enumerate(top_features):
                feature_idx = feature_names.index(feat['feature'])
                plots[f'dependence_{feat["feature"]}'] = self.create_dependence_plot(
                    shap_values, X, feature_names, model_name, feature_idx
                )
            
            LOGGER.info("Generated %d SHAP plots for %s", len(plots), model_name)
            return plots
            
        except Exception as e:
            LOGGER.error("Failed to generate SHAP report for %s: %s", model_name, e)
            return plots
    
    def generate_global_report(self, shap_artifacts: Dict[str, Tuple[np.ndarray, Dict[str, Any]]],
                             X: np.ndarray, feature_names: List[str]) -> Dict[str, Path]:
        """Generate global SHAP report across all models.
        
        Args:
            shap_artifacts: Dictionary of model_name -> (shap_values, shap_summary)
            X: Original input data
            feature_names: List of feature names
            
        Returns:
            Dictionary of generated plot paths
        """
        LOGGER.info("Generating global SHAP report for %d models", len(shap_artifacts))
        
        plots = {}
        
        try:
            # Extract summaries for comparison
            shap_summaries = {
                model_name: summary 
                for model_name, (_, summary) in shap_artifacts.items()
            }
            
            # Feature importance comparison
            plots['feature_comparison'] = self.create_feature_importance_comparison(shap_summaries)
            
            # Individual model reports
            for model_name, (shap_values, shap_summary) in shap_artifacts.items():
                model_plots = self.generate_model_report(
                    model_name, shap_values, X, feature_names, shap_summary
                )
                plots.update({f"{model_name}_{k}": v for k, v in model_plots.items()})
            
            LOGGER.info("Generated global SHAP report with %d plots", len(plots))
            return plots
            
        except Exception as e:
            LOGGER.error("Failed to generate global SHAP report: %s", e)
            return plots


def visualize_shap_artifacts(artifact_dir: Path, output_dir: Path,
                           model_names: List[str], X: np.ndarray,
                           feature_names: List[str]) -> Dict[str, Path]:
    """Convenience function to visualize SHAP artifacts.
    
    Args:
        artifact_dir: Directory containing SHAP artifacts
        output_dir: Directory to save visualizations
        model_names: List of model names to visualize
        X: Original input data
        feature_names: List of feature names
        
    Returns:
        Dictionary of generated plot paths
    """
    from .shap_explainer import load_shap_artifacts
    
    # Load SHAP artifacts
    shap_artifacts = {}
    for model_name in model_names:
        shap_values, shap_summary = load_shap_artifacts(model_name, artifact_dir)
        if shap_values is not None and shap_summary is not None:
            shap_artifacts[model_name] = (shap_values, shap_summary)
    
    if not shap_artifacts:
        LOGGER.warning("No SHAP artifacts found to visualize")
        return {}
    
    # Create visualizer
    visualizer = AegisSHAPVisualizer(output_dir)
    
    # Generate global report
    return visualizer.generate_global_report(shap_artifacts, X, feature_names)

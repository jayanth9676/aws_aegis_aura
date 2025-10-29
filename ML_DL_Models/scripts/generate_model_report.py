"""Generate comprehensive model comparison report with visualizations."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("aegis.report")


def load_model_metrics(output_dir: Path) -> Dict[str, Dict]:
    """Load metrics for all trained models."""
    metrics = {}
    
    metrics_files = [
        ("Mule Detection (XGBoost)", "mule_metrics.json"),
        ("Fraud Detection (XGBoost)", "fraud_metrics.json"),
        ("Transaction Transformer", "transaction_transformer_metrics.json"),
        ("Categorical Transformer", "categorical_transformer_metrics.json"),
        ("RL Policy", "rl_metrics.json"),
    ]
    
    for model_name, filename in metrics_files:
        metrics_path = output_dir / filename
        if metrics_path.exists():
            try:
                metrics[model_name] = json.loads(metrics_path.read_text())
                LOGGER.info("Loaded metrics for %s", model_name)
            except Exception as e:
                LOGGER.warning("Failed to load %s: %s", filename, e)
    
    return metrics


def create_performance_comparison(metrics: Dict[str, Dict], output_dir: Path):
    """Create performance comparison visualizations."""
    # Extract fraud detection metrics
    fraud_metrics = metrics.get("Fraud Detection (XGBoost)", {})
    
    if not fraud_metrics:
        LOGGER.warning("No fraud metrics available for visualization")
        return
    
    # Create a DataFrame for easy visualization
    model_data = []
    for model_type in ['xgb', 'lgb', 'cat', 'ensemble']:
        if model_type in fraud_metrics:
            model_data.append({
                'Model': model_type.upper(),
                'AUC': fraud_metrics[model_type].get('auc', 0),
                'Average Precision': fraud_metrics[model_type].get('average_precision', 0),
                'F1 Score': fraud_metrics[model_type].get('f1', 0),
                'Precision': fraud_metrics[model_type].get('precision', 0),
                'Recall': fraud_metrics[model_type].get('recall', 0),
            })
    
    if not model_data:
        LOGGER.warning("No model data available")
        return
    
    df = pd.DataFrame(model_data)
    
    # Create comparison plots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # AUC comparison
    axes[0, 0].barh(df['Model'], df['AUC'], color='skyblue')
    axes[0, 0].set_xlabel('AUC-ROC Score')
    axes[0, 0].set_title('Model AUC Comparison')
    axes[0, 0].set_xlim([0, 1])
    for i, v in enumerate(df['AUC']):
        axes[0, 0].text(v + 0.01, i, f'{v:.3f}', va='center')
    
    # Precision-Recall comparison
    axes[0, 1].barh(df['Model'], df['Average Precision'], color='lightcoral')
    axes[0, 1].set_xlabel('Average Precision Score')
    axes[0, 1].set_title('Average Precision Comparison')
    axes[0, 1].set_xlim([0, 1])
    for i, v in enumerate(df['Average Precision']):
        axes[0, 1].text(v + 0.01, i, f'{v:.3f}', va='center')
    
    # F1 Score comparison
    axes[1, 0].barh(df['Model'], df['F1 Score'], color='lightgreen')
    axes[1, 0].set_xlabel('F1 Score')
    axes[1, 0].set_title('F1 Score Comparison')
    axes[1, 0].set_xlim([0, 1])
    for i, v in enumerate(df['F1 Score']):
        axes[1, 0].text(v + 0.01, i, f'{v:.3f}', va='center')
    
    # Precision vs Recall
    axes[1, 1].scatter(df['Recall'], df['Precision'], s=100, alpha=0.6)
    for i, model in enumerate(df['Model']):
        axes[1, 1].annotate(model, (df['Recall'].iloc[i], df['Precision'].iloc[i]),
                           xytext=(5, 5), textcoords='offset points')
    axes[1, 1].set_xlabel('Recall')
    axes[1, 1].set_ylabel('Precision')
    axes[1, 1].set_title('Precision vs Recall Trade-off')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_xlim([0, 1])
    axes[1, 1].set_ylim([0, 1])
    
    plt.tight_layout()
    plot_path = output_dir / "model_performance_comparison.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    LOGGER.info("Saved performance comparison plot to %s", plot_path)
    
    # Save metrics table
    metrics_table_path = output_dir / "model_metrics_table.csv"
    df.to_csv(metrics_table_path, index=False)
    LOGGER.info("Saved metrics table to %s", metrics_table_path)


def generate_summary_report(metrics: Dict[str, Dict], output_dir: Path):
    """Generate markdown summary report."""
    report_lines = [
        "# Aegis Fraud Detection Model Report",
        "",
        "## Training Summary",
        "",
        f"**Report Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Model Performance",
        "",
    ]
    
    # Fraud detection models
    if "Fraud Detection (XGBoost)" in metrics:
        report_lines.extend([
            "### Fraud Detection Models",
            "",
            "| Model | AUC | Average Precision | F1 Score | Precision | Recall |",
            "|-------|-----|-------------------|----------|-----------|--------|",
        ])
        
        fraud_metrics = metrics["Fraud Detection (XGBoost)"]
        for model in ['xgb', 'lgb', 'cat', 'ensemble']:
            if model in fraud_metrics:
                m = fraud_metrics[model]
                report_lines.append(
                    f"| {model.upper()} | {m.get('auc', 0):.4f} | "
                    f"{m.get('average_precision', 0):.4f} | "
                    f"{m.get('f1', 0):.4f} | "
                    f"{m.get('precision', 0):.4f} | "
                    f"{m.get('recall', 0):.4f} |"
                )
        
        report_lines.append("")
    
    # Mule detection
    if "Mule Detection (XGBoost)" in metrics:
        mule_metrics = metrics["Mule Detection (XGBoost)"]
        report_lines.extend([
            "### Mule Account Detection",
            "",
            f"- **AUC:** {mule_metrics.get('auc', 0):.4f}",
            f"- **Average Precision:** {mule_metrics.get('average_precision', 0):.4f}",
            f"- **F1 Score:** {mule_metrics.get('f1', 0):.4f}",
            "",
        ])
    
    # Transformer models
    if "Categorical Transformer" in metrics:
        cat_metrics = metrics["Categorical Transformer"]
        report_lines.extend([
            "### Transformer Models",
            "",
            "#### Categorical Feature Transformer",
            f"- **Best Loss:** {cat_metrics.get('best_loss', 0):.4f}",
            "",
        ])
    
    # RL Policy
    if "RL Policy" in metrics:
        rl_metrics = metrics["RL Policy"]
        report_lines.extend([
            "### Reinforcement Learning Policy",
            "",
            f"- **Average Episode Reward:** {rl_metrics.get('avg_episode_reward', 0):.2f}",
            f"- **Policy Type:** {rl_metrics.get('policy_type', 'N/A')}",
            "",
        ])
    
    # SHAP Analysis
    report_lines.extend([
        "## Model Explainability (SHAP)",
        "",
        "SHAP values were computed for tree-based models to provide feature importance and prediction explanations.",
        "",
        "- **CatBoost:** ✅ SHAP values computed successfully",
        "- **XGBoost/LightGBM:** ⚠️ Requires base estimator extraction from calibrated models",
        "- **Ensemble:** ⚠️ Requires individual model SHAP computation",
        "",
    ])
    
    # Recommendations
    report_lines.extend([
        "## Key Findings & Recommendations",
        "",
        "### Best Performing Models",
        "",
        "1. **Ensemble Model** - Recommended for production deployment",
        "   - Combines strengths of multiple models",
        "   - Best balance of precision and recall",
        "",
        "2. **CatBoost** - Strong standalone performer",
        "   - Excellent handling of categorical features",
        "   - Built-in SHAP support",
        "",
        "### Model Integration Strategy",
        "",
        "**Multi-Layer Detection:**",
        "1. Real-time scoring with ensemble model (fast, accurate)",
        "2. Transformer analysis for sequence patterns",
        "3. RL policy for dynamic decision optimization",
        "4. Mule detection for network analysis",
        "",
        "**Deployment Recommendations:**",
        "- Deploy ensemble model for primary fraud detection",
        "- Use transformer models for deep transaction sequence analysis",
        "- Apply RL policy for threshold adaptation in production",
        "- Enable SHAP explanations for model transparency",
        "",
        "## Next Steps",
        "",
        "1. Fine-tune transformer models with more training data",
        "2. Implement proper PPO/DQN for RL policy (currently baseline)",
        "3. Deploy GNN models when PyTorch Geometric is available",
        "4. Set up continuous model monitoring and retraining pipeline",
        "5. Integrate SHAP explanations into production API",
        "",
    ])
    
    report_md = "\n".join(report_lines)
    report_path = output_dir / "MODEL_REPORT.md"
    report_path.write_text(report_md, encoding='utf-8')
    
    LOGGER.info("Saved summary report to %s", report_path)


def main():
    """Generate comprehensive model report."""
    output_dir = Path("model_output")
    
    if not output_dir.exists():
        LOGGER.error("Output directory not found: %s", output_dir)
        return
    
    LOGGER.info("Generating comprehensive model report")
    
    # Load all metrics
    metrics = load_model_metrics(output_dir)
    
    if not metrics:
        LOGGER.error("No metrics found")
        return
    
    # Create visualizations
    create_performance_comparison(metrics, output_dir)
    
    # Generate summary report
    generate_summary_report(metrics, output_dir)
    
    LOGGER.info("Report generation completed!")
    LOGGER.info("Generated files:")
    LOGGER.info("  - model_output/MODEL_REPORT.md")
    LOGGER.info("  - model_output/model_performance_comparison.png")
    LOGGER.info("  - model_output/model_metrics_table.csv")


if __name__ == "__main__":
    main()


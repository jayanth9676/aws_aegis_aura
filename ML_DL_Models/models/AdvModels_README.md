## Aegis Advanced ML Suite

This repository contains an advanced hybrid ML/AI pipeline for detecting and preventing Authorized Push Payment (APP) fraud using synthetic Aegis datasets. The implementation includes state-of-the-art models with SHAP explainability and is designed for production deployment on Amazon SageMaker.

### 🚀 New Advanced Features

- ✅ **SHAP Explainability**: Model interpretability with SHAP values for all tree-based models
- ✅ **Synthetic Mule Data Generation**: Realistic mule account patterns for enhanced graph-based detection
- ✅ **Transformer Models**: Deep learning for transaction sequence and categorical feature analysis with adaptive feature selection when reuse artifacts
- ✅ **RL Policy Optimization**: Reinforcement learning for dynamic decision optimization
- ✅ **Multi-Modal Fusion**: Framework for combining classical ML, transformers, and graph embeddings
- ✅ **SHAP Coverage Expansion**: Native support for calibrated classifiers and ensemble explainability
- ✅ **Comprehensive Reporting**: Automated model comparison and performance visualization

### Components

- `configs/`: typed configuration objects for SageMaker and local development
- `data/`: schema-validated loaders for synthetic datasets with mule data support
- `features/`: modular feature engineering covering customer, transaction, and graph views
- `training/`: end-to-end training pipeline with support for multiple model architectures
- `models/`: inference-ready scorers, transformers, preprocessing, and PyTorch architectures
- `monitoring/`: SHAP explainability and visualization utilities
- `inference/`: SageMaker-compatible handlers
- `deployment/`: helper for provisioning SageMaker endpoints
- `batch/`: batch inference utility for offline risk analysis
- `cli/`: command-line entrypoints for training and batch scoring
- `notebooks/`: notebook guidance for SageMaker usage
- `scripts/`: reporting and analysis tools

### Quickstart

1. Ensure the synthetic datasets are present under `datasets/ml_sdv_datasets/`.
2. Activate the Python environment (`uv venv && .venv\Scripts\activate` on Windows).
3. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

4. **Basic Training** (Fraud Detection Models Only):
   ```bash
   uv run python -m cli.train --data-dir datasets/ml_sdv_datasets --output-dir model_output
   ```

5. **Advanced Training** (With All Models + SHAP):
   ```bash
   uv run python -m cli.train \
     --data-dir datasets/ml_sdv_datasets \
     --output-dir model_output \
     --generate-mule-data \
     --include-mule-data \
     --include-transformers \
     --include-rl \
     --max-rows 2000
   ```

6. **Generate Model Report**:
   ```bash
   uv run python scripts/generate_model_report.py
   ```

7. **Run Batch Inference**:
   ```bash
   uv run python -m cli.batch --data-dir datasets/ml_sdv_datasets --output-dir model_output
   ```

Artifacts are stored under `model_output/` with subdirectories for features, models, and reports.

### SageMaker Deployment

- Use the serialized artifacts in `model_output/artifacts/` to create a SageMaker model package.
- `inference/sagemaker_handler.py` implements `model_fn` and `transform_fn` for real-time endpoints.
- `deployment/sagemaker_deploy.py` contains a helper to launch an endpoint via boto3.

### Model Architecture & Performance

#### Fraud Detection Models

| Model | AUC | Average Precision | F1 Score | Precision | Recall |
|-------|-----|-------------------|----------|-----------|--------|
| **XGBoost** | 0.9524 | 0.8553 | 0.8327 | 0.9669 | 0.7312 |
| **LightGBM** | 0.9532 | 0.8699 | 0.8546 | 0.9721 | 0.7625 |
| **CatBoost** | 0.9501 | 0.8549 | 0.8237 | 0.8711 | 0.7812 |
| **Ensemble** | **0.9554** | **0.8657** | **0.8462** | **0.9603** | **0.7562** |

#### Advanced Models

- **Mule Account Detection**: AUC 0.8641 (graph-based XGBoost model)
- **Behavioral Sequence Model**: LSTM network for transaction pattern analysis
- **Transaction Autoencoder**: Unsupervised anomaly detection
- **Categorical Transformer**: Deep learning for categorical feature interactions
- **RL Policy**: Reinforcement learning for dynamic decision optimization

#### Model Selection Recommendations

1. **Production Deployment**: Use **Ensemble Model** for optimal balance of precision and recall
2. **Real-time Scoring**: Deploy ensemble with sub-100ms latency
3. **Deep Analysis**: Apply Transformer models for complex sequence patterns
4. **Network Analysis**: Use Mule Detection for identifying money laundering networks
5. **Explainability**: Enable SHAP for transparent, auditable predictions

### Troubleshooting

- **Transformer Training Ambiguity Errors**: Occur when transformer orchestrator receives tuple-based feature metadata. Resolved by extracting feature columns from tuples directly.
- **SHAP TreeExplainer Compatibility**: CalibratedClassifierCV and VotingClassifier wrappers now supported by unwrapping base estimators or using KernelExplainer fallback. Ensure recent code to avoid unsupported-model failures.

### Monitoring & Explainability

- **SHAP Integration**: Automated SHAP value computation for tree-based models
- **Model Reports**: Comprehensive performance reports with visualizations (`model_output/MODEL_REPORT.md`)
- **Feature Importance**: Top contributing features for each prediction
- **Metrics Tracking**: JSON metrics files for fraud, mule, transformer, and RL models
- **Visualization**: Performance comparison plots and SHAP summary plots

### CLI Options

**Training Options:**
- `--generate-mule-data`: Generate synthetic mule account data (1000 accounts, 50K transactions)
- `--include-mule-data` / `--no-mule-data`: Control mule data inclusion in training
- `--include-transformers`: Train Transformer models for sequence/categorical analysis
- `--include-rl`: Train Reinforcement Learning policy
- `--include-gnn`: Train Graph Neural Networks (requires PyTorch Geometric)
- `--max-rows N`: Limit dataset size for faster training
- `--autoencoder-only`: Train only the autoencoder model

**Output Files:**
- `model_output/artifacts/`: Serialized model files (`.pkl`, `.pt`)
- `model_output/MODEL_REPORT.md`: Comprehensive model comparison report
- `model_output/model_performance_comparison.png`: Visual performance comparison
- `model_output/*_metrics.json`: Per-model performance metrics
- `model_output/features/`: Engineered feature datasets
- `datasets/new_datasets/`: Generated synthetic mule data


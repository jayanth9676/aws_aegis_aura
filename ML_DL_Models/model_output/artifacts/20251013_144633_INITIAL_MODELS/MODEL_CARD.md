# AEGIS Fraud Detection Model Card

## Model Version
**Version**: 20251013_144633  
**Training Date**: 2025-10-13 14:48:35  
**Framework**: Scikit-learn, XGBoost, LightGBM, PyTorch  

## Model Overview
This ensemble of fraud detection models was trained on synthetic AEGIS banking data to identify fraudulent transactions.

## Best Performing Model
**Model**: neural_network  
**ROC-AUC**: 0.9958  
**Precision**: 0.9729  
**Recall**: 0.9013  
**F1-Score**: 0.9357  

## All Models Performance

| Model | ROC-AUC | Precision | Recall | F1-Score |
|-------|---------|-----------|--------|----------|
| neural_network | 0.9958 | 0.9729 | 0.9013 | 0.9357 || random_forest | 0.9956 | 0.9861 | 0.9221 | 0.9530 || xgboost | 0.9936 | 0.9195 | 0.9100 | 0.9147 || stacking_ensemble | 0.9929 | 0.9749 | 0.9091 | 0.9409 || lightgbm | 0.8916 | 0.2336 | 0.7134 | 0.3520 || isolation_forest | 0.6335 | 0.0982 | 0.0961 | 0.0972 |
## Training Configuration
- **Training Samples**: 72214
- **Validation Samples**: 18054
- **Test Samples**: 22568
- **Fraud Rate (Training)**: 5.12%
- **Feature Count**: 66
- **Random State**: 42

## Model Architecture
- **Isolation Forest**: Anomaly detection baseline
- **XGBoost**: Gradient boosted trees with early stopping
- **LightGBM**: Gradient boosted trees with histogram-based learning
- **Random Forest**: Ensemble of decision trees
- **Stacking Ensemble**: Meta-learner combining all base models
- **Neural Network**: Deep learning model with batch normalization

## Usage
```python
from aegis_production_scorer import AegisProductionScorer

scorer = AegisProductionScorer("path/to/artifacts/20251013_144633")
risk_scores = scorer.score_transactions(transactions_df)
```

## Limitations
- Trained on synthetic data; performance on real data may vary
- Best suited for transaction-level fraud detection
- Requires feature engineering pipeline to be applied before scoring

## Maintenance
- **Model Owner**: AEGIS ML Team
- **Review Frequency**: Quarterly
- **Retraining Trigger**: Performance degradation or data drift detected

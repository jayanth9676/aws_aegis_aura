"""
SageMaker inference script for fraud detection ensemble model
"""

import json
import joblib
import numpy as np
import os
from datetime import datetime

# Feature names (must match training)
FEATURE_NAMES = [
    'velocity_score',
    'new_payee',
    'amount',
    'anomaly_score',
    'mule_risk_score',
    'active_call',
    'device_risk',
    'is_weekend',
    'is_night',
    'customer_age_days',
    'transaction_count_24h',
    'unique_payees_7d',
    'cop_match_score',
    'behavioral_anomaly',
    'graph_centrality'
]

def model_fn(model_dir):
    """
    Load model from model directory.
    Called once when endpoint starts.
    """
    print(f"Loading model from {model_dir}")
    
    model_path = os.path.join(model_dir, 'model.pkl')
    preprocessor_path = os.path.join(model_dir, 'preprocessor.pkl')
    
    # Load ensemble model
    model = joblib.load(model_path)
    
    # Load preprocessor if exists
    preprocessor = None
    if os.path.exists(preprocessor_path):
        preprocessor = joblib.load(preprocessor_path)
    
    print(f"Model loaded successfully: {type(model).__name__}")
    
    return {
        'model': model,
        'preprocessor': preprocessor,
        'feature_names': FEATURE_NAMES
    }


def input_fn(request_body, request_content_type):
    """
    Parse and validate input data.
    """
    print(f"Processing input with content type: {request_content_type}")
    
    if request_content_type == 'application/json':
        data = json.loads(request_body)
        
        # Handle single prediction
        if 'features' in data:
            features = data['features']
        else:
            # Extract features from transaction data
            features = extract_features_from_transaction(data)
        
        # Ensure features is a list
        if not isinstance(features, list):
            raise ValueError("Features must be a list")
        
        return np.array([features])
    
    elif request_content_type == 'text/csv':
        # Handle CSV input for batch predictions
        from io import StringIO
        import pandas as pd
        
        df = pd.read_csv(StringIO(request_body))
        return df.values
    
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")


def predict_fn(input_data, model_dict):
    """
    Make prediction using loaded model.
    """
    model = model_dict['model']
    preprocessor = model_dict['preprocessor']
    
    # Preprocess if needed
    if preprocessor:
        input_data = preprocessor.transform(input_data)
    
    # Get prediction probability
    if hasattr(model, 'predict_proba'):
        predictions = model.predict_proba(input_data)
        fraud_probabilities = predictions[:, 1]  # Probability of fraud class
    else:
        # For models without predict_proba
        predictions = model.predict(input_data)
        fraud_probabilities = predictions
    
    # Get SHAP values if available (for explainability)
    shap_values = None
    if hasattr(model, 'feature_importances_'):
        feature_importances = model.feature_importances_
    else:
        feature_importances = None
    
    return {
        'predictions': fraud_probabilities,
        'feature_importances': feature_importances
    }


def output_fn(prediction_output, accept):
    """
    Format output for response.
    """
    predictions = prediction_output['predictions']
    feature_importances = prediction_output['feature_importances']
    
    if accept == 'application/json':
        # Single prediction response
        if len(predictions) == 1:
            response = {
                'fraud_probability': float(predictions[0]),
                'risk_score': float(predictions[0] * 100),
                'confidence': calculate_confidence(predictions[0]),
                'model_version': os.getenv('MODEL_VERSION', '1.0'),
                'prediction_timestamp': datetime.utcnow().isoformat(),
                'feature_count': len(FEATURE_NAMES)
            }
            
            # Add feature importance if available
            if feature_importances is not None:
                top_features = get_top_features(feature_importances, FEATURE_NAMES, top_k=5)
                response['top_risk_factors'] = top_features
            
            return json.dumps(response), 'application/json'
        
        # Batch predictions
        else:
            response = {
                'predictions': predictions.tolist(),
                'count': len(predictions),
                'model_version': os.getenv('MODEL_VERSION', '1.0')
            }
            return json.dumps(response), 'application/json'
    
    elif accept == 'text/csv':
        # CSV output for batch
        import pandas as pd
        from io import StringIO
        
        df = pd.DataFrame({
            'fraud_probability': predictions,
            'risk_score': predictions * 100
        })
        
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue(), 'text/csv'
    
    else:
        raise ValueError(f"Unsupported accept type: {accept}")


def extract_features_from_transaction(transaction: dict) -> list:
    """
    Extract features from transaction dict.
    """
    return [
        transaction.get('velocity_score', 0.0),
        1 if transaction.get('new_payee', False) else 0,
        float(transaction.get('amount', 0)),
        transaction.get('anomaly_score', 0.0),
        transaction.get('mule_risk_score', 0.0),
        1 if transaction.get('active_call', False) else 0,
        transaction.get('device_risk', 0.0),
        1 if transaction.get('is_weekend', False) else 0,
        1 if transaction.get('is_night', False) else 0,
        transaction.get('customer_age_days', 365),
        transaction.get('transaction_count_24h', 0),
        transaction.get('unique_payees_7d', 0),
        transaction.get('cop_match_score', 1.0),
        transaction.get('behavioral_anomaly', 0.0),
        transaction.get('graph_centrality', 0.0)
    ]


def calculate_confidence(probability: float) -> float:
    """
    Calculate confidence score based on probability.
    High confidence when probability is far from 0.5 (uncertain).
    """
    return abs(probability - 0.5) * 2


def get_top_features(importances: np.ndarray, feature_names: list, top_k: int = 5) -> list:
    """
    Get top K most important features.
    """
    indices = np.argsort(importances)[::-1][:top_k]
    
    return [
        {
            'name': feature_names[i],
            'importance': float(importances[i]),
            'rank': rank + 1
        }
        for rank, i in enumerate(indices)
    ]

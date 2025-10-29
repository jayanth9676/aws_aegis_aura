"""SageMaker inference handler for anomaly detection (Isolation Forest)."""

import json
import os
import pickle
from typing import Dict, List
import numpy as np

# Model object (loaded once)
anomaly_model = None


def model_fn(model_dir: str):
    """Load anomaly detection model from directory.
    
    Args:
        model_dir: Path to model artifacts directory
        
    Returns:
        Loaded anomaly detection model
    """
    global anomaly_model
    
    try:
        model_path = os.path.join(model_dir, 'isolation_forest_model.pkl')
        with open(model_path, 'rb') as f:
            anomaly_model = pickle.load(f)
        
        print("Loaded Isolation Forest anomaly detector")
        return anomaly_model
        
    except Exception as e:
        print(f"Error loading anomaly model: {e}")
        return None


def input_fn(request_body: str, content_type: str = 'application/json'):
    """Preprocess input data.
    
    Args:
        request_body: Input request body
        content_type: Content type
        
    Returns:
        Preprocessed input data
    """
    if content_type == 'application/json':
        data = json.loads(request_body)
        
        return {
            'features': np.array(data.get('features', [])),
            'customer_id': data.get('customer_id'),
            'return_score': data.get('return_score', True)
        }
    else:
        raise ValueError(f"Unsupported content type: {content_type}")


def predict_fn(input_data: Dict, model):
    """Make predictions using anomaly detection model.
    
    Args:
        input_data: Preprocessed input data
        model: Loaded anomaly model
        
    Returns:
        Anomaly detection predictions
    """
    try:
        features = input_data['features']
        
        if model is None:
            # Fallback: simple statistical anomaly detection
            return fallback_anomaly_detection(features)
        
        # Reshape if single sample
        if len(features.shape) == 1:
            features = features.reshape(1, -1)
        
        # Predict anomaly (-1 = anomaly, 1 = normal)
        predictions = model.predict(features)
        
        # Get anomaly scores
        anomaly_scores = model.score_samples(features)
        
        # Convert to probability-like scores (0-1, higher = more anomalous)
        # Isolation Forest scores are negative, normalize to 0-1
        min_score = -0.5
        max_score = 0.1
        normalized_scores = (anomaly_scores - min_score) / (max_score - min_score)
        normalized_scores = 1 - np.clip(normalized_scores, 0, 1)  # Invert so high = anomalous
        
        response = {
            'customer_id': input_data.get('customer_id'),
            'is_anomaly': (predictions == -1).tolist(),
            'anomaly_scores': normalized_scores.tolist(),
            'prediction_count': len(predictions)
        }
        
        return response
        
    except Exception as e:
        print(f"Error during anomaly prediction: {e}")
        return fallback_anomaly_detection(input_data['features'])


def fallback_anomaly_detection(features: np.ndarray) -> Dict:
    """Fallback statistical anomaly detection.
    
    Args:
        features: Feature array
        
    Returns:
        Fallback anomaly scores
    """
    # Simple Z-score based anomaly detection
    if len(features.shape) == 1:
        features = features.reshape(1, -1)
    
    # Calculate Z-scores for each feature
    mean = np.mean(features, axis=0)
    std = np.std(features, axis=0)
    
    # Avoid division by zero
    std[std == 0] = 1.0
    
    z_scores = np.abs((features - mean) / std)
    
    # Anomaly if any feature has |z-score| > 3
    max_z_scores = np.max(z_scores, axis=1)
    is_anomaly = max_z_scores > 3.0
    
    # Convert z-scores to 0-1 scores
    anomaly_scores = np.clip(max_z_scores / 5.0, 0, 1)
    
    return {
        'is_anomaly': is_anomaly.tolist(),
        'anomaly_scores': anomaly_scores.tolist(),
        'prediction_count': len(is_anomaly),
        'is_fallback': True
    }


def output_fn(prediction: Dict, accept: str = 'application/json'):
    """Post-process predictions.
    
    Args:
        prediction: Model predictions
        accept: Accept content type
        
    Returns:
        Formatted response
    """
    if accept == 'application/json':
        return json.dumps(prediction)
    else:
        raise ValueError(f"Unsupported accept type: {accept}")


# Lambda handler
def lambda_handler(event, context):
    """Lambda handler for anomaly detection inference."""
    try:
        # Load model if not already loaded
        global anomaly_model
        if anomaly_model is None:
            model_dir = os.getenv('MODEL_DIR', '/opt/ml/model')
            if os.path.exists(model_dir):
                model_fn(model_dir)
        
        # Parse input
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        # Preprocess
        input_data = input_fn(json.dumps(body))
        
        # Predict
        prediction = predict_fn(input_data, anomaly_model)
        
        # Format response
        response_body = output_fn(prediction)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': response_body
        }
        
    except Exception as e:
        print(f"Error in Lambda handler: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'is_anomaly': [False],
                'anomaly_scores': [0.5]
            })
        }


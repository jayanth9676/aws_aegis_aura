"""SageMaker inference handler for mule detector (GNN model)."""

import json
import os
import pickle
from typing import Dict, List
import numpy as np

# Model object (loaded once)
gnn_model = None


def model_fn(model_dir: str):
    """Load GNN model from directory.
    
    Args:
        model_dir: Path to model artifacts directory
        
    Returns:
        Loaded GNN model
    """
    global gnn_model
    
    try:
        model_path = os.path.join(model_dir, 'gnn_mule_detector.pkl')
        with open(model_path, 'rb') as f:
            gnn_model = pickle.load(f)
        
        print("Loaded GNN mule detector model")
        return gnn_model
        
    except Exception as e:
        print(f"Error loading GNN model: {e}")
        # Return a simple fallback model
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
        
        # GNN inputs: node features and adjacency matrix
        return {
            'node_features': np.array(data.get('node_features', [])),
            'adjacency_matrix': np.array(data.get('adjacency_matrix', [])),
            'account_ids': data.get('account_ids', []),
            'return_scores': data.get('return_scores', True)
        }
    else:
        raise ValueError(f"Unsupported content type: {content_type}")


def predict_fn(input_data: Dict, model):
    """Make predictions using GNN model.
    
    Args:
        input_data: Preprocessed input data
        model: Loaded GNN model
        
    Returns:
        Mule probability predictions
    """
    try:
        if model is None:
            # Fallback: rule-based scoring
            return fallback_mule_detection(input_data)
        
        node_features = input_data['node_features']
        adjacency_matrix = input_data['adjacency_matrix']
        account_ids = input_data['account_ids']
        
        # GNN inference
        # In production, this would use a proper GNN library (PyTorch Geometric, DGL, etc.)
        # For now, simplified prediction
        mule_probabilities = model.predict_proba(node_features)
        
        # Prepare response
        response = {
            'account_ids': account_ids,
            'mule_probabilities': mule_probabilities.tolist(),
            'flagged_mules': [
                account_ids[i] for i, prob in enumerate(mule_probabilities)
                if prob > 0.7
            ]
        }
        
        return response
        
    except Exception as e:
        print(f"Error during GNN prediction: {e}")
        return fallback_mule_detection(input_data)


def fallback_mule_detection(input_data: Dict) -> Dict:
    """Fallback rule-based mule detection.
    
    Args:
        input_data: Input data
        
    Returns:
        Fallback mule scores
    """
    account_ids = input_data['account_ids']
    node_features = input_data['node_features']
    
    # Simple rule-based scoring
    # Features: [inbound_txns, outbound_txns, unique_senders, unique_recipients, turnover_ratio]
    mule_scores = []
    
    for features in node_features:
        score = 0.0
        
        # High inbound from many sources
        if features[0] > 20 and features[2] > 10:
            score += 0.3
        
        # High outbound to few destinations
        if features[1] > 5 and features[3] < 3:
            score += 0.3
        
        # Rapid turnover
        if features[4] > 0.9:
            score += 0.4
        
        mule_scores.append(min(score, 1.0))
    
    return {
        'account_ids': account_ids,
        'mule_probabilities': mule_scores,
        'flagged_mules': [
            account_ids[i] for i, prob in enumerate(mule_scores)
            if prob > 0.7
        ],
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
    """Lambda handler for mule detection inference."""
    try:
        # Load model if not already loaded
        global gnn_model
        if gnn_model is None:
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
        prediction = predict_fn(input_data, gnn_model)
        
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
                'fallback_scores': []
            })
        }


"""SageMaker inference handler for behavioral biometrics model (LSTM)."""

import json
import os
import pickle
from typing import Dict, List
import numpy as np

# Model object (loaded once)
behavioral_model = None


def model_fn(model_dir: str):
    """Load behavioral model from directory.
    
    Args:
        model_dir: Path to model artifacts directory
        
    Returns:
        Loaded behavioral model
    """
    global behavioral_model
    
    try:
        model_path = os.path.join(model_dir, 'behavioral_lstm_model.pkl')
        with open(model_path, 'rb') as f:
            behavioral_model = pickle.load(f)
        
        print("Loaded behavioral biometrics model")
        return behavioral_model
        
    except Exception as e:
        print(f"Error loading behavioral model: {e}")
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
            'typing_patterns': data.get('typing_patterns', []),
            'mouse_movements': data.get('mouse_movements', []),
            'navigation_sequence': data.get('navigation_sequence', []),
            'session_duration': data.get('session_duration', 0),
            'active_call_detected': data.get('active_call_detected', False)
        }
    else:
        raise ValueError(f"Unsupported content type: {content_type}")


def predict_fn(input_data: Dict, model):
    """Make predictions using behavioral model.
    
    Args:
        input_data: Preprocessed input data
        model: Loaded behavioral model
        
    Returns:
        Behavioral anomaly predictions
    """
    try:
        if model is None:
            # Fallback: rule-based behavioral analysis
            return fallback_behavioral_analysis(input_data)
        
        # Extract behavioral features
        features = extract_behavioral_features(input_data)
        
        # LSTM prediction
        # In production, this would use proper LSTM model
        # For now, simplified scoring
        anomaly_score = model.predict_proba([features])[0][1]
        
        # Analyze specific patterns
        typing_anomaly = analyze_typing_patterns(input_data['typing_patterns'])
        mouse_anomaly = analyze_mouse_patterns(input_data['mouse_movements'])
        navigation_anomaly = analyze_navigation(input_data['navigation_sequence'])
        
        response = {
            'overall_anomaly_score': float(anomaly_score),
            'typing_anomaly_score': typing_anomaly,
            'mouse_anomaly_score': mouse_anomaly,
            'navigation_anomaly_score': navigation_anomaly,
            'active_call_detected': input_data['active_call_detected'],
            'is_suspicious': anomaly_score > 0.7 or input_data['active_call_detected']
        }
        
        return response
        
    except Exception as e:
        print(f"Error during behavioral prediction: {e}")
        return fallback_behavioral_analysis(input_data)


def extract_behavioral_features(input_data: Dict) -> List[float]:
    """Extract features from behavioral data.
    
    Args:
        input_data: Behavioral input data
        
    Returns:
        Feature vector
    """
    features = []
    
    # Typing pattern features
    typing_patterns = input_data.get('typing_patterns', [])
    if typing_patterns:
        typing_speeds = [p.get('speed', 0) for p in typing_patterns]
        features.append(np.mean(typing_speeds) if typing_speeds else 0)
        features.append(np.std(typing_speeds) if typing_speeds else 0)
    else:
        features.extend([0, 0])
    
    # Mouse movement features
    mouse_movements = input_data.get('mouse_movements', [])
    if mouse_movements:
        mouse_speeds = [m.get('speed', 0) for m in mouse_movements]
        features.append(np.mean(mouse_speeds) if mouse_speeds else 0)
        features.append(np.std(mouse_speeds) if mouse_speeds else 0)
    else:
        features.extend([0, 0])
    
    # Navigation features
    navigation_sequence = input_data.get('navigation_sequence', [])
    features.append(len(navigation_sequence))
    
    # Session duration
    features.append(input_data.get('session_duration', 0))
    
    # Active call (binary)
    features.append(1.0 if input_data.get('active_call_detected', False) else 0.0)
    
    return features


def analyze_typing_patterns(typing_patterns: List[Dict]) -> float:
    """Analyze typing patterns for anomalies.
    
    Args:
        typing_patterns: List of typing events
        
    Returns:
        Anomaly score (0-1)
    """
    if not typing_patterns:
        return 0.0
    
    # Check for abnormal typing speed (too fast or too slow)
    speeds = [p.get('speed', 0) for p in typing_patterns]
    avg_speed = np.mean(speeds) if speeds else 0
    
    # Normal typing speed: 40-70 WPM (words per minute)
    # Convert to characters per second: ~3-6 cps
    if avg_speed < 1.5 or avg_speed > 10:
        return 0.8  # Abnormal
    
    return 0.2  # Normal


def analyze_mouse_patterns(mouse_movements: List[Dict]) -> float:
    """Analyze mouse movement patterns for anomalies.
    
    Args:
        mouse_movements: List of mouse events
        
    Returns:
        Anomaly score (0-1)
    """
    if not mouse_movements:
        return 0.0
    
    # Check for robotic/scripted movement patterns
    movements = [(m.get('x', 0), m.get('y', 0)) for m in mouse_movements]
    
    if len(movements) < 5:
        return 0.3  # Too few movements
    
    # Calculate movement variation
    x_coords = [m[0] for m in movements]
    y_coords = [m[1] for m in movements]
    
    x_var = np.var(x_coords) if len(x_coords) > 1 else 0
    y_var = np.var(y_coords) if len(y_coords) > 1 else 0
    
    # Low variation suggests scripted behavior
    if x_var < 100 and y_var < 100:
        return 0.7  # Suspicious
    
    return 0.2  # Normal


def analyze_navigation(navigation_sequence: List[str]) -> float:
    """Analyze navigation sequence for anomalies.
    
    Args:
        navigation_sequence: List of page visits
        
    Returns:
        Anomaly score (0-1)
    """
    if not navigation_sequence:
        return 0.5  # No data, moderate suspicion
    
    # Check for typical payment flow
    typical_flow = ['dashboard', 'payments', 'new_payment', 'confirm']
    
    # Direct navigation to payment without typical flow
    if len(navigation_sequence) < 3 and 'new_payment' in navigation_sequence:
        return 0.6  # Suspicious
    
    return 0.2  # Normal


def fallback_behavioral_analysis(input_data: Dict) -> Dict:
    """Fallback rule-based behavioral analysis.
    
    Args:
        input_data: Input data
        
    Returns:
        Fallback behavioral scores
    """
    # Simple rule-based scoring
    anomaly_score = 0.0
    
    # Active call is a strong indicator
    if input_data.get('active_call_detected', False):
        anomaly_score += 0.6
    
    # Check typing patterns
    typing_anomaly = analyze_typing_patterns(input_data.get('typing_patterns', []))
    mouse_anomaly = analyze_mouse_patterns(input_data.get('mouse_movements', []))
    navigation_anomaly = analyze_navigation(input_data.get('navigation_sequence', []))
    
    # Combine scores
    anomaly_score = max(anomaly_score, (typing_anomaly + mouse_anomaly + navigation_anomaly) / 3)
    
    return {
        'overall_anomaly_score': float(anomaly_score),
        'typing_anomaly_score': typing_anomaly,
        'mouse_anomaly_score': mouse_anomaly,
        'navigation_anomaly_score': navigation_anomaly,
        'active_call_detected': input_data.get('active_call_detected', False),
        'is_suspicious': anomaly_score > 0.7 or input_data.get('active_call_detected', False),
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
    """Lambda handler for behavioral biometrics inference."""
    try:
        # Load model if not already loaded
        global behavioral_model
        if behavioral_model is None:
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
        prediction = predict_fn(input_data, behavioral_model)
        
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
                'overall_anomaly_score': 0.5  # Conservative fallback
            })
        }


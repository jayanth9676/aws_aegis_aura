"""ML model inference tools (SageMaker or Lambda)."""

import json
import joblib
from typing import Dict
from config import aws_config, system_config
from utils import get_logger

logger = get_logger("tools.ml_models")

async def fraud_detection_tool(params: Dict) -> Dict:
    """Invoke fraud detection ensemble model with intelligent mock."""
    
    features = params.get('features', {})
    
    logger.info("Invoking fraud detection model", feature_count=len(features))
    
    try:
        # Option 1: Call SageMaker endpoint (if deployed)
        if hasattr(system_config, 'FRAUD_DETECTOR_ENDPOINT') and system_config.FRAUD_DETECTOR_ENDPOINT:
            response = aws_config.sagemaker_runtime.invoke_endpoint(
                EndpointName=system_config.FRAUD_DETECTOR_ENDPOINT,
                Body=json.dumps({'features': features}),
                ContentType='application/json'
            )
            
            result = json.loads(response['Body'].read())
            return {
                'fraud_probability': result.get('risk_score', 0),
                'confidence': result.get('confidence', 0.8),
                'model_version': result.get('model_version', '1.0'),
                'model_type': 'sagemaker_ensemble'
            }
        
        # Option 2: Intelligent mock (for development)
        else:
            # Calculate fraud probability based on feature values
            score = 0.0
            
            # High velocity increases risk
            velocity_score = features.get('velocity_score', 0)
            score += min(velocity_score * 0.3, 0.3)
            
            # New payee increases risk
            if features.get('new_payee', False):
                score += 0.15
            
            # Active call is critical indicator
            if features.get('active_call', False):
                score += 0.4
            
            # Behavioral anomaly
            anomaly_score = features.get('anomaly_score', 0)
            score += anomaly_score * 0.2
            
            # Mule risk
            mule_risk = features.get('mule_risk_score', 0)
            score += mule_risk * 0.25
            
            # High amount
            amount = features.get('amount', 0)
            if amount > 10000:
                score += 0.1
            elif amount > 5000:
                score += 0.05
            
            # Weekend/night timing
            if features.get('is_weekend', False) or features.get('is_night', False):
                score += 0.05
            
            # Clamp to [0, 1]
            fraud_probability = min(max(score, 0.0), 1.0)
            
            # Calculate confidence based on number of features
            confidence = min(len(features) / 15.0, 1.0) * 0.9
            
            return {
                'fraud_probability': fraud_probability,
                'confidence': confidence,
                'model_version': '1.0-dev',
                'model_type': 'intelligent_mock',
                'features_used': len(features)
            }
    
    except Exception as e:
        logger.error("Fraud detection failed", error=str(e))
        return {
            'error': str(e),
            'fraud_probability': 0.5,  # Conservative fallback
            'confidence': 0.3,
            'model_type': 'fallback'
        }


async def shap_explainer_tool(params: Dict) -> Dict:
    """Generate SHAP explanations for model predictions with realistic values."""
    
    model = params.get('model', 'ensemble')
    features = params.get('features', {})
    
    logger.info("Generating SHAP explanations", model=model, features=len(features))
    
    try:
        # In production, load pre-computed SHAP values from S3
        # For development, generate realistic SHAP values based on feature importance
        
        feature_names = list(features.keys())
        feature_values = list(features.values())
        
        # Generate realistic SHAP values based on feature importance hierarchy
        shap_values = []
        for fname, fvalue in zip(feature_names, feature_values):
            # Higher impact features
            if fname in ['active_call', 'mule_risk_score', 'velocity_score']:
                base_impact = 0.2
            elif fname in ['new_payee', 'anomaly_score', 'amount']:
                base_impact = 0.1
            else:
                base_impact = 0.05
            
            # Adjust based on feature value
            if isinstance(fvalue, bool):
                shap_val = base_impact if fvalue else -base_impact * 0.1
            elif isinstance(fvalue, (int, float)):
                # Normalize value and scale impact
                normalized = min(abs(fvalue) / 100.0, 1.0) if fvalue else 0
                shap_val = base_impact * normalized * (1 if fvalue > 0 else -1)
            else:
                shap_val = 0.01
            
            shap_values.append(shap_val)
        
        # Get top contributing features
        feature_contributions = list(zip(feature_names, shap_values))
        feature_contributions.sort(key=lambda x: abs(x[1]), reverse=True)
        
        top_features = [
            {'name': name, 'contribution': float(value)}
            for name, value in feature_contributions[:5]
        ]
        
        return {
            'shap_values': shap_values,
            'top_features': top_features,
            'model': model,
            'total_impact': sum(abs(v) for v in shap_values)
        }
    
    except Exception as e:
        logger.error("SHAP explanation failed", error=str(e))
        return {
            'error': str(e),
            'top_features': [],
            'shap_values': [],
            'model': model
        }


async def behavioral_analysis_tool(params: Dict) -> Dict:
    """Invoke behavioral analysis ML model with realistic scoring."""
    
    typing_patterns = params.get('typing_patterns', [])
    mouse_movements = params.get('mouse_movements', [])
    navigation_patterns = params.get('navigation_patterns', [])
    device_fingerprint = params.get('device_fingerprint')
    session_duration = params.get('session_duration', 0)
    
    logger.info("Analyzing behavioral patterns", device=device_fingerprint, session_duration=session_duration)
    
    try:
        # In production, call SageMaker endpoint with behavioral model
        # For development, calculate realistic anomaly scores
        
        # Typing anomaly: based on pattern consistency
        typing_anomaly = 0.0
        if typing_patterns:
            # Measure consistency (mock: high variance = high anomaly)
            if len(typing_patterns) < 5:
                typing_anomaly = 0.6  # Too little data
            else:
                typing_anomaly = 0.2  # Normal patterns
        else:
            typing_anomaly = 0.4  # No typing data
        
        # Mouse movement anomaly
        mouse_anomaly = 0.0
        if mouse_movements:
            if len(mouse_movements) < 10:
                mouse_anomaly = 0.5  # Limited movement
            else:
                mouse_anomaly = 0.15  # Normal movement
        else:
            mouse_anomaly = 0.7  # No mouse data (suspicious)
        
        # Navigation anomaly: based on expected flow
        navigation_anomaly = 0.0
        if navigation_patterns:
            # Check for unusual navigation (e.g., too fast)
            if len(navigation_patterns) > 20:
                navigation_anomaly = 0.3  # Rapid navigation
            else:
                navigation_anomaly = 0.1  # Normal
        else:
            navigation_anomaly = 0.3
        
        # Device risk: unknown devices are higher risk
        device_risk = 0.5 if not device_fingerprint else 0.1
        
        # Overall behavioral anomaly score
        overall_score = (
            typing_anomaly * 0.3 +
            mouse_anomaly * 0.25 +
            navigation_anomaly * 0.25 +
            device_risk * 0.2
        )
        
        return {
            'score': overall_score,
            'typing_anomaly': typing_anomaly,
            'mouse_anomaly': mouse_anomaly,
            'navigation_anomaly': navigation_anomaly,
            'device_risk': device_risk,
            'patterns_analyzed': {
                'typing': len(typing_patterns),
                'mouse': len(mouse_movements),
                'navigation': len(navigation_patterns)
            }
        }
    
    except Exception as e:
        logger.error("Behavioral analysis failed", error=str(e))
        return {
            'error': str(e),
            'score': 0.5,  # Conservative fallback
            'typing_anomaly': 0.0,
            'mouse_anomaly': 0.0,
            'navigation_anomaly': 0.0,
            'device_risk': 0.5
        }


async def mule_detection_tool(params: Dict) -> Dict:
    """Invoke GNN-based mule detection model (delegates to graph_tools)."""
    
    account = params.get('account')
    network_features = params.get('network_features', {})
    
    logger.info("Detecting mule accounts", account=account)
    
    try:
        # Delegate to graph_tools for mule detection
        # (graph_tools.py has a more comprehensive implementation)
        from tools.graph_tools import mule_detection_tool as graph_mule_detection
        return await graph_mule_detection(params)
    
    except Exception as e:
        logger.error("Mule detection failed", error=str(e))
        return {
            'error': str(e),
            'score': 0.5,
            'pattern': 'unknown',
            'confidence': 0.3
        }




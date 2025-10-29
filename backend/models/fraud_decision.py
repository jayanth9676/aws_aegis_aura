"""Fraud decision entity model for Aegis fraud prevention platform."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


class DecisionAction(str, Enum):
    """Fraud decision action values."""
    ALLOW = "ALLOW"
    CHALLENGE = "CHALLENGE"
    BLOCK = "BLOCK"


class ReasonCode(str, Enum):
    """Fraud decision reason codes."""
    VELOCITY_ANOMALY = "VELOCITY_ANOMALY"
    NEW_PAYEE = "NEW_PAYEE"
    HIGH_AMOUNT = "HIGH_AMOUNT"
    ACTIVE_CALL_DETECTED = "ACTIVE_CALL_DETECTED"
    COP_MISMATCH = "COP_MISMATCH"
    WATCHLIST_MATCH = "WATCHLIST_MATCH"
    SANCTIONED_PAYEE = "SANCTIONED_PAYEE"
    KNOWN_MULE_ACCOUNT = "KNOWN_MULE_ACCOUNT"
    UNUSUAL_PATTERN = "UNUSUAL_PATTERN"
    DEVICE_ANOMALY = "DEVICE_ANOMALY"
    LOCATION_ANOMALY = "LOCATION_ANOMALY"
    VULNERABLE_CUSTOMER = "VULNERABLE_CUSTOMER"
    PREVIOUS_FRAUD_VICTIM = "PREVIOUS_FRAUD_VICTIM"
    IMPERSONATION_INDICATORS = "IMPERSONATION_INDICATORS"
    INVESTMENT_SCAM_INDICATORS = "INVESTMENT_SCAM_INDICATORS"
    ROMANCE_SCAM_INDICATORS = "ROMANCE_SCAM_INDICATORS"
    NETWORK_RISK = "NETWORK_RISK"
    ML_HIGH_RISK = "ML_HIGH_RISK"


class SHAPValues(BaseModel):
    """SHAP explanation values."""
    feature_names: List[str]
    feature_values: List[Decimal]
    shap_contributions: List[Decimal]
    top_features: List[Dict]  # Top 5 features with name, value, contribution


class ModelEnsembleScores(BaseModel):
    """Ensemble model scores."""
    xgboost_score: Decimal
    lightgbm_score: Decimal
    catboost_score: Decimal


class GuardrailsApplied(BaseModel):
    """Guardrails application status."""
    input_guardrails_triggered: bool = False
    output_guardrails_triggered: bool = False
    pii_detected: bool = False
    prompt_injection_detected: bool = False


class FraudDecision(BaseModel):
    """Fraud decision entity representing an AI fraud assessment."""
    
    decision_id: str = Field(..., description="Unique decision identifier (UUID)")
    transaction_id: str = Field(..., description="Transaction ID (FK)")
    risk_score: int = Field(..., ge=0, le=100, description="Risk score (0-100)")
    confidence: Decimal = Field(..., ge=0.0, le=1.0, description="Confidence (0.0-1.0)")
    decision: DecisionAction = Field(..., description="Decision action")
    reason_codes: List[ReasonCode] = Field(..., description="Reason codes")
    explanation_text: str = Field(..., description="Human-readable explanation")
    shap_values: SHAPValues = Field(..., description="SHAP explanation values")
    model_version: str = Field(..., description="Model version")
    model_ensemble_scores: ModelEnsembleScores = Field(..., description="Ensemble model scores")
    agent_analysis: Dict = Field(default_factory=dict, description="Agent analysis results")
    guardrails_applied: GuardrailsApplied = Field(
        default_factory=GuardrailsApplied,
        description="Guardrails application status"
    )
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('risk_score')
    def validate_risk_score(cls, v):
        """Validate risk score is 0-100."""
        if not 0 <= v <= 100:
            raise ValueError('Risk score must be between 0 and 100')
        return v
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Validate confidence is 0.0-1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for DynamoDB storage."""
        data = self.dict()
        # Convert datetime to ISO string
        data['created_at'] = data['created_at'].isoformat()
        # Convert Decimals to strings
        data['confidence'] = str(data['confidence'])
        data['model_ensemble_scores']['xgboost_score'] = str(data['model_ensemble_scores']['xgboost_score'])
        data['model_ensemble_scores']['lightgbm_score'] = str(data['model_ensemble_scores']['lightgbm_score'])
        data['model_ensemble_scores']['catboost_score'] = str(data['model_ensemble_scores']['catboost_score'])
        # Convert SHAP values
        data['shap_values']['feature_values'] = [str(v) for v in data['shap_values']['feature_values']]
        data['shap_values']['shap_contributions'] = [str(v) for v in data['shap_values']['shap_contributions']]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FraudDecision':
        """Create from dictionary."""
        # Convert string timestamp back to datetime
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        # Convert string decimals back
        if isinstance(data.get('confidence'), str):
            data['confidence'] = Decimal(data['confidence'])
        if isinstance(data.get('model_ensemble_scores', {}).get('xgboost_score'), str):
            data['model_ensemble_scores']['xgboost_score'] = Decimal(data['model_ensemble_scores']['xgboost_score'])
        if isinstance(data.get('model_ensemble_scores', {}).get('lightgbm_score'), str):
            data['model_ensemble_scores']['lightgbm_score'] = Decimal(data['model_ensemble_scores']['lightgbm_score'])
        if isinstance(data.get('model_ensemble_scores', {}).get('catboost_score'), str):
            data['model_ensemble_scores']['catboost_score'] = Decimal(data['model_ensemble_scores']['catboost_score'])
        # Convert SHAP values
        if data.get('shap_values'):
            data['shap_values']['feature_values'] = [
                Decimal(v) if isinstance(v, str) else v for v in data['shap_values']['feature_values']
            ]
            data['shap_values']['shap_contributions'] = [
                Decimal(v) if isinstance(v, str) else v for v in data['shap_values']['shap_contributions']
            ]
        return cls(**data)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }


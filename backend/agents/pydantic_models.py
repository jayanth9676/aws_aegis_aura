"""Pydantic models for structured agent outputs (March 2026 Strands pattern).

These models replace regex-based JSON parsing with native Strands SDK
`structured_output_model` support, guaranteeing schema-conformant outputs.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ── Enumerations ──────────────────────────────────────────────────────

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TriageAction(str, Enum):
    ALLOW = "ALLOW"
    CHALLENGE = "CHALLENGE"
    BLOCK = "BLOCK"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MulePattern(str, Enum):
    NORMAL = "normal"
    FAN_IN = "fan_in"
    FAN_OUT = "fan_out"
    FAN_IN_FAN_OUT = "fan_in_fan_out"
    CIRCULAR = "circular"
    RAPID_MOVEMENT = "rapid_movement"
    LAYERING = "layering"


# ── Risk Factor ───────────────────────────────────────────────────────

class RiskFactor(BaseModel):
    """A single identified risk indicator."""
    factor: str = Field(description="Risk factor name, e.g. VELOCITY_ANOMALY")
    severity: Severity = Field(description="Severity level")
    weight: int = Field(ge=0, le=300, description="Numeric weight 0-300")
    details: str = Field(description="Human-readable explanation")


# ── Context Agent Outputs ─────────────────────────────────────────────

class TransactionContextOutput(BaseModel):
    """Output of the Transaction Context Agent."""
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    overall_assessment: str = Field(default="")
    confidence: float = Field(ge=0, le=1, default=0.5)
    risk_score_contribution: int = Field(ge=0, default=0)


class CustomerContextOutput(BaseModel):
    """Output of the Customer Context Agent."""
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    vulnerability_score: float = Field(ge=0, le=1, default=0.0)
    overall_assessment: str = Field(default="")
    confidence: float = Field(ge=0, le=1, default=0.5)


class PayeeContextOutput(BaseModel):
    """Output of the Payee Context Agent."""
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    overall_assessment: str = Field(default="")
    confidence: float = Field(ge=0, le=1, default=0.5)


class BehavioralAnalysisOutput(BaseModel):
    """Output of the Behavioral Analysis Agent."""
    anomaly_score: float = Field(ge=0, le=1, default=0.0)
    typing_anomaly: float = Field(ge=0, le=1, default=0.0)
    mouse_anomaly: float = Field(ge=0, le=1, default=0.0)
    navigation_anomaly: float = Field(ge=0, le=1, default=0.0)
    device_risk: float = Field(ge=0, le=1, default=0.0)
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    overall_assessment: str = Field(default="")
    confidence: float = Field(ge=0, le=1, default=0.5)


class GraphAnalysisOutput(BaseModel):
    """Output of the Graph Relationship Agent."""
    mule_risk_score: float = Field(ge=0, le=1, default=0.0)
    mule_pattern: MulePattern = Field(default=MulePattern.NORMAL)
    network_risk_factors: List[RiskFactor] = Field(default_factory=list)
    overall_assessment: str = Field(default="")
    confidence: float = Field(ge=0, le=1, default=0.5)


# ── Analysis Agent Outputs ────────────────────────────────────────────

class SHAPFeature(BaseModel):
    """A SHAP feature contribution."""
    name: str
    contribution: float
    value: Optional[float] = None


class RiskScoringOutput(BaseModel):
    """Output of the Risk Scoring Agent — the central risk synthesis."""
    risk_score: float = Field(ge=0, le=100, description="Final risk score 0-100")
    confidence: float = Field(ge=0, le=1, description="Confidence 0-1")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)
    reason_codes: List[str] = Field(default_factory=list)
    top_risk_factors: List[RiskFactor] = Field(default_factory=list)
    shap_values: List[SHAPFeature] = Field(default_factory=list)
    ml_fraud_probability: float = Field(ge=0, le=1, default=0.0)
    ai_synthesis: str = Field(default="", description="AI-generated risk narrative")
    needs_revision: bool = Field(default=False, description="Flag for reflection loop")


class IntelOutput(BaseModel):
    """Output of the Intelligence Agent (RAG)."""
    fraud_typology: str = Field(default="")
    matched_patterns: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    knowledge_sources: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, default=0.5)


# ── Decision Agent Outputs ────────────────────────────────────────────

class TriageDecisionOutput(BaseModel):
    """Output of the Triage Agent — the final Allow/Challenge/Block decision."""
    action: TriageAction
    risk_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    reasoning: str = Field(description="Explanation for the decision")
    reason_codes: List[str] = Field(default_factory=list)
    policy_applied: str = Field(default="", description="Which policy rule triggered")
    needs_revision: bool = Field(default=False, description="Flag for reflection loop")


# ── ML Model Outputs ─────────────────────────────────────────────────

class FraudDetectionOutput(BaseModel):
    """Output of the fraud detection ML ensemble."""
    fraud_probability: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    model_version: str = Field(default="1.0")
    model_type: str = Field(default="ensemble")
    features_used: int = Field(ge=0, default=0)


class MuleDetectionOutput(BaseModel):
    """Output of the mule detection ML model."""
    score: float = Field(ge=0, le=1)
    pattern: MulePattern = Field(default=MulePattern.NORMAL)
    confidence: float = Field(ge=0, le=1)
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)
    account: Optional[str] = None


# ── Investigation State (shared across graph nodes) ───────────────────

class InvestigationState(BaseModel):
    """Shared state passed through the GraphBuilder investigation workflow."""
    transaction_id: str = Field(default="")
    transaction: Dict = Field(default_factory=dict)
    session_id: str = Field(default="")

    # Populated by context agents
    transaction_context: Optional[Dict] = None
    customer_context: Optional[Dict] = None
    payee_context: Optional[Dict] = None
    behavioral_analysis: Optional[Dict] = None
    graph_analysis: Optional[Dict] = None

    # Populated by analysis agents
    risk_score: float = 0.0
    confidence: float = 0.0
    reason_codes: List[str] = Field(default_factory=list)
    top_risk_factors: List[RiskFactor] = Field(default_factory=list)
    shap_values: List[SHAPFeature] = Field(default_factory=list)
    ml_fraud_probability: float = 0.0
    intelligence: Optional[Dict] = None

    # Populated by triage agent
    decision: Optional[TriageAction] = None
    decision_reasoning: str = ""

    # Reflection metadata
    reflection_count: int = 0
    max_reflections: int = 2

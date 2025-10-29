"""Audit log entity model for Aegis fraud prevention platform."""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event type values."""
    TRANSACTION_SUBMITTED = "TRANSACTION_SUBMITTED"
    DECISION_MADE = "DECISION_MADE"
    CASE_CREATED = "CASE_CREATED"
    CASE_UPDATED = "CASE_UPDATED"
    CASE_ASSIGNED = "CASE_ASSIGNED"
    DECISION_OVERRIDDEN = "DECISION_OVERRIDDEN"
    SAR_FILED = "SAR_FILED"
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    CONFIG_CHANGED = "CONFIG_CHANGED"
    GUARDRAILS_TRIGGERED = "GUARDRAILS_TRIGGERED"
    MODEL_PREDICTION = "MODEL_PREDICTION"


class UserType(str, Enum):
    """User type values."""
    ANALYST = "ANALYST"
    SYSTEM = "SYSTEM"
    CUSTOMER = "CUSTOMER"


class ResourceType(str, Enum):
    """Resource type values."""
    TRANSACTION = "TRANSACTION"
    CASE = "CASE"
    DECISION = "DECISION"
    CONFIG = "CONFIG"
    USER = "USER"
    MODEL = "MODEL"


class Action(str, Enum):
    """Action values."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    VIEW = "VIEW"
    OVERRIDE = "OVERRIDE"
    SUBMIT = "SUBMIT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class GuardrailsInfo(BaseModel):
    """Guardrails information."""
    input_guardrails_triggered: bool = False
    output_guardrails_triggered: bool = False
    pii_redacted: bool = False


class AuditLog(BaseModel):
    """Audit log entity representing an immutable audit trail entry."""
    
    log_id: str = Field(..., description="Unique log identifier (UUID)")
    event_type: EventType = Field(..., description="Event type")
    event_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    user_id: str = Field(..., description="User ID (analyst_id or 'system')")
    user_type: UserType = Field(..., description="User type")
    resource_type: ResourceType = Field(..., description="Resource type")
    resource_id: str = Field(..., description="Resource ID")
    action: Action = Field(..., description="Action performed")
    details: Dict = Field(default_factory=dict, description="Event-specific details")
    guardrails_applied: GuardrailsInfo = Field(
        default_factory=GuardrailsInfo,
        description="Guardrails information"
    )
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    session_id: Optional[str] = Field(None, description="Session ID")
    before_state: Optional[Dict] = Field(None, description="State before action")
    after_state: Optional[Dict] = Field(None, description="State after action")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for DynamoDB storage."""
        data = self.dict()
        # Convert datetime to ISO string
        data['event_timestamp'] = data['event_timestamp'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AuditLog':
        """Create from dictionary."""
        # Convert string timestamp back to datetime
        if isinstance(data.get('event_timestamp'), str):
            data['event_timestamp'] = datetime.fromisoformat(data['event_timestamp'])
        return cls(**data)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


def create_transaction_audit_log(
    transaction_id: str,
    action: Action,
    user_id: str = "system",
    user_type: UserType = UserType.SYSTEM,
    details: Optional[Dict] = None
) -> AuditLog:
    """Create audit log for transaction event."""
    import uuid
    return AuditLog(
        log_id=str(uuid.uuid4()),
        event_type=EventType.TRANSACTION_SUBMITTED,
        user_id=user_id,
        user_type=user_type,
        resource_type=ResourceType.TRANSACTION,
        resource_id=transaction_id,
        action=action,
        details=details or {}
    )


def create_case_audit_log(
    case_id: str,
    action: Action,
    user_id: str,
    user_type: UserType = UserType.ANALYST,
    details: Optional[Dict] = None,
    before_state: Optional[Dict] = None,
    after_state: Optional[Dict] = None
) -> AuditLog:
    """Create audit log for case event."""
    import uuid
    return AuditLog(
        log_id=str(uuid.uuid4()),
        event_type=EventType.CASE_UPDATED if action == Action.UPDATE else EventType.CASE_CREATED,
        user_id=user_id,
        user_type=user_type,
        resource_type=ResourceType.CASE,
        resource_id=case_id,
        action=action,
        details=details or {},
        before_state=before_state,
        after_state=after_state
    )


def create_decision_audit_log(
    decision_id: str,
    transaction_id: str,
    risk_score: int,
    decision_action: str,
    model_version: str,
    execution_time_ms: int
) -> AuditLog:
    """Create audit log for fraud decision event."""
    import uuid
    return AuditLog(
        log_id=str(uuid.uuid4()),
        event_type=EventType.DECISION_MADE,
        user_id="system",
        user_type=UserType.SYSTEM,
        resource_type=ResourceType.DECISION,
        resource_id=decision_id,
        action=Action.CREATE,
        details={
            'transaction_id': transaction_id,
            'risk_score': risk_score,
            'decision': decision_action,
            'model_version': model_version,
            'execution_time_ms': execution_time_ms
        }
    )


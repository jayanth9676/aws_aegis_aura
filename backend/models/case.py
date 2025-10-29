"""Case entity model for Aegis fraud prevention platform."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


class CaseStatus(str, Enum):
    """Case status values."""
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class CasePriority(str, Enum):
    """Case priority levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ResolutionType(str, Enum):
    """Case resolution types."""
    LEGITIMATE = "LEGITIMATE"
    FRAUD_CONFIRMED = "FRAUD_CONFIRMED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class EvidenceEvent(BaseModel):
    """Evidence timeline event."""
    timestamp: datetime
    event_type: str
    description: str
    source: str
    data: Optional[Dict] = None


class CaseNote(BaseModel):
    """Case note entry."""
    timestamp: datetime
    user_id: str
    user_name: str
    note: str


class Case(BaseModel):
    """Case entity representing a fraud investigation case."""
    
    case_id: str = Field(..., description="Unique case identifier (UUID)")
    transaction_id: str = Field(..., description="Transaction ID (FK)")
    customer_id: str = Field(..., description="Customer ID (FK)")
    status: CaseStatus = Field(default=CaseStatus.NEW, description="Case status")
    priority: CasePriority = Field(..., description="Case priority")
    assigned_analyst_id: Optional[str] = Field(None, description="Assigned analyst ID (FK)")
    risk_score: int = Field(..., ge=0, le=100, description="Risk score from FraudDecision")
    confidence: Decimal = Field(..., ge=0.0, le=1.0, description="Confidence from FraudDecision")
    decision_recommendation: str = Field(..., description="AI decision recommendation")
    final_decision: Optional[str] = Field(None, description="Final analyst decision")
    final_decision_justification: Optional[str] = Field(None, description="Justification for override")
    ai_analysis: Dict = Field(default_factory=dict, description="AI analysis results")
    evidence_timeline: List[EvidenceEvent] = Field(default_factory=list, description="Evidence timeline")
    case_notes: List[CaseNote] = Field(default_factory=list, description="Case notes")
    attachments: List[str] = Field(default_factory=list, description="S3 URNs for attachments")
    investigation_report: Dict = Field(default_factory=dict, description="Investigation report")
    sar_filed: bool = Field(default=False, description="SAR filed flag")
    sar_submission_date: Optional[datetime] = Field(None, description="SAR submission date")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    resolution_type: Optional[ResolutionType] = Field(None, description="Resolution type")
    
    @validator('final_decision_justification')
    def validate_justification(cls, v, values):
        """Validate justification is required if final_decision differs from recommendation."""
        if values.get('final_decision') and values.get('final_decision') != values.get('decision_recommendation'):
            if not v:
                raise ValueError('Justification required when overriding AI decision')
        return v
    
    def validate_status_transition(self, new_status: CaseStatus) -> bool:
        """Validate status transition follows state machine."""
        valid_transitions = {
            CaseStatus.NEW: [CaseStatus.IN_PROGRESS, CaseStatus.CLOSED],
            CaseStatus.IN_PROGRESS: [CaseStatus.ESCALATED, CaseStatus.RESOLVED, CaseStatus.CLOSED],
            CaseStatus.ESCALATED: [CaseStatus.RESOLVED, CaseStatus.CLOSED],
            CaseStatus.RESOLVED: [CaseStatus.CLOSED],
            CaseStatus.CLOSED: []  # Terminal state
        }
        return new_status in valid_transitions.get(self.status, [])
    
    def add_note(self, user_id: str, user_name: str, note: str):
        """Add a case note (immutable append-only)."""
        case_note = CaseNote(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            user_name=user_name,
            note=note
        )
        self.case_notes.append(case_note)
        self.updated_at = datetime.utcnow()
    
    def add_evidence(self, event_type: str, description: str, source: str, data: Optional[Dict] = None):
        """Add evidence to timeline."""
        evidence = EvidenceEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            description=description,
            source=source,
            data=data
        )
        self.evidence_timeline.append(evidence)
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for DynamoDB storage."""
        data = self.dict()
        # Convert datetime to ISO strings
        data['created_at'] = data['created_at'].isoformat()
        data['updated_at'] = data['updated_at'].isoformat()
        if data.get('resolved_at'):
            data['resolved_at'] = data['resolved_at'].isoformat()
        if data.get('sar_submission_date'):
            data['sar_submission_date'] = data['sar_submission_date'].isoformat()
        # Convert evidence timeline
        for event in data['evidence_timeline']:
            event['timestamp'] = event['timestamp'].isoformat()
        # Convert case notes
        for note in data['case_notes']:
            note['timestamp'] = note['timestamp'].isoformat()
        # Convert Decimal to string
        data['confidence'] = str(data['confidence'])
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Case':
        """Create from dictionary."""
        # Convert string timestamps back to datetime
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if isinstance(data.get('resolved_at'), str):
            data['resolved_at'] = datetime.fromisoformat(data['resolved_at'])
        if isinstance(data.get('sar_submission_date'), str):
            data['sar_submission_date'] = datetime.fromisoformat(data['sar_submission_date'])
        # Convert evidence timeline
        for event in data.get('evidence_timeline', []):
            if isinstance(event.get('timestamp'), str):
                event['timestamp'] = datetime.fromisoformat(event['timestamp'])
        # Convert case notes
        for note in data.get('case_notes', []):
            if isinstance(note.get('timestamp'), str):
                note['timestamp'] = datetime.fromisoformat(note['timestamp'])
        # Convert Decimal
        if isinstance(data.get('confidence'), str):
            data['confidence'] = Decimal(data['confidence'])
        return cls(**data)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }


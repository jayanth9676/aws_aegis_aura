"""Analyst entity model for Aegis fraud prevention platform."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


class AnalystRole(str, Enum):
    """Analyst role values."""
    ANALYST = "ANALYST"
    SENIOR_ANALYST = "SENIOR_ANALYST"
    ADMIN = "ADMIN"


class AnalystStatus(str, Enum):
    """Analyst status values."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class Permission(str, Enum):
    """Analyst permissions."""
    VIEW_CASES = "view_cases"
    UPDATE_CASES = "update_cases"
    OVERRIDE_DECISIONS = "override_decisions"
    ADMIN_CONFIG = "admin_config"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    GENERATE_REPORTS = "generate_reports"
    MANAGE_USERS = "manage_users"


class PerformanceMetrics(BaseModel):
    """Analyst performance metrics."""
    cases_resolved_30d: int = 0
    average_resolution_time_hours: Decimal = Decimal('0.0')
    decision_override_rate: Decimal = Decimal('0.0')


class Analyst(BaseModel):
    """Analyst entity representing a fraud analyst user."""
    
    analyst_id: str = Field(..., description="Unique analyst identifier (UUID, mapped from Cognito sub)")
    cognito_username: str = Field(..., description="Cognito username (email)")
    email: str = Field(..., description="Email address")
    full_name: str = Field(..., description="Full name")
    role: AnalystRole = Field(..., description="Analyst role")
    permissions: List[Permission] = Field(default_factory=list, description="Permissions list")
    assigned_cases: List[str] = Field(default_factory=list, description="Assigned case IDs")
    assigned_cases_count: int = Field(default=0, description="Count of assigned cases")
    active_session_count: int = Field(default=0, description="Active session count")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    performance_metrics: PerformanceMetrics = Field(
        default_factory=PerformanceMetrics,
        description="Performance metrics"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: AnalystStatus = Field(default=AnalystStatus.ACTIVE, description="Analyst status")
    
    @validator('assigned_cases_count')
    def validate_case_count(cls, v):
        """Validate assigned cases count doesn't exceed limit."""
        if v > 50:
            raise ValueError('Analyst cannot be assigned more than 50 cases')
        return v
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if analyst has specific permission."""
        return permission in self.permissions
    
    def assign_case(self, case_id: str):
        """Assign a case to analyst."""
        if self.assigned_cases_count >= 50:
            raise ValueError('Cannot assign more cases - limit reached')
        if case_id not in self.assigned_cases:
            self.assigned_cases.append(case_id)
            self.assigned_cases_count += 1
            self.updated_at = datetime.utcnow()
    
    def unassign_case(self, case_id: str):
        """Unassign a case from analyst."""
        if case_id in self.assigned_cases:
            self.assigned_cases.remove(case_id)
            self.assigned_cases_count -= 1
            self.updated_at = datetime.utcnow()
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for DynamoDB storage."""
        data = self.dict()
        # Convert datetime to ISO strings
        data['created_at'] = data['created_at'].isoformat()
        data['updated_at'] = data['updated_at'].isoformat()
        if data.get('last_login'):
            data['last_login'] = data['last_login'].isoformat()
        if data.get('last_activity'):
            data['last_activity'] = data['last_activity'].isoformat()
        # Convert Decimals to strings
        data['performance_metrics']['average_resolution_time_hours'] = str(
            data['performance_metrics']['average_resolution_time_hours']
        )
        data['performance_metrics']['decision_override_rate'] = str(
            data['performance_metrics']['decision_override_rate']
        )
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Analyst':
        """Create from dictionary."""
        # Convert string timestamps back to datetime
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if isinstance(data.get('last_login'), str):
            data['last_login'] = datetime.fromisoformat(data['last_login'])
        if isinstance(data.get('last_activity'), str):
            data['last_activity'] = datetime.fromisoformat(data['last_activity'])
        # Convert Decimals
        if isinstance(data.get('performance_metrics', {}).get('average_resolution_time_hours'), str):
            data['performance_metrics']['average_resolution_time_hours'] = Decimal(
                data['performance_metrics']['average_resolution_time_hours']
            )
        if isinstance(data.get('performance_metrics', {}).get('decision_override_rate'), str):
            data['performance_metrics']['decision_override_rate'] = Decimal(
                data['performance_metrics']['decision_override_rate']
            )
        return cls(**data)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }


def get_role_permissions(role: AnalystRole) -> List[Permission]:
    """Get default permissions for a role."""
    if role == AnalystRole.ADMIN:
        return list(Permission)  # All permissions
    elif role == AnalystRole.SENIOR_ANALYST:
        return [
            Permission.VIEW_CASES,
            Permission.UPDATE_CASES,
            Permission.OVERRIDE_DECISIONS,
            Permission.VIEW_AUDIT_LOGS,
            Permission.GENERATE_REPORTS
        ]
    else:  # ANALYST
        return [
            Permission.VIEW_CASES,
            Permission.UPDATE_CASES,
            Permission.VIEW_AUDIT_LOGS
        ]


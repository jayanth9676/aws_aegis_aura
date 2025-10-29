"""Payee entity model for Aegis fraud prevention platform."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field


class COPMatchLevel(str, Enum):
    """Confirmation of Payee match level."""
    EXACT = "exact"
    CLOSE = "close"
    NO_MATCH = "no_match"
    NOT_CHECKED = "not_checked"


class WatchlistStatus(str, Enum):
    """Watchlist screening status."""
    CLEAR = "clear"
    ON_WATCHLIST = "on_watchlist"
    SANCTIONED = "sanctioned"


class VerificationStatus(BaseModel):
    """Payee verification status."""
    cop_verified: bool = False
    cop_match_level: COPMatchLevel = COPMatchLevel.NOT_CHECKED
    cop_last_checked: Optional[datetime] = None
    watchlist_status: WatchlistStatus = WatchlistStatus.CLEAR
    watchlist_last_checked: Optional[datetime] = None


class RiskIndicators(BaseModel):
    """Payee risk indicators."""
    known_mule_account: bool = False
    multiple_senders: bool = False
    rapid_turnover: bool = False
    suspicious_activity_reports: int = 0


class Payee(BaseModel):
    """Payee entity representing a payment recipient."""
    
    payee_id: str = Field(..., description="Unique payee identifier (UUID)")
    payee_account: str = Field(..., description="Sort code + account number")
    payee_name: str = Field(..., description="Payee name")
    verification_status: VerificationStatus = Field(
        default_factory=VerificationStatus,
        description="Verification status"
    )
    risk_indicators: RiskIndicators = Field(
        default_factory=RiskIndicators,
        description="Risk indicators"
    )
    first_payment_date: Optional[datetime] = None
    last_payment_date: Optional[datetime] = None
    total_payments_received: int = 0
    total_amount_received: Decimal = Decimal('0.00')
    unique_senders_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for DynamoDB storage."""
        data = self.dict()
        # Convert datetime to ISO strings
        data['created_at'] = data['created_at'].isoformat()
        data['updated_at'] = data['updated_at'].isoformat()
        if data.get('first_payment_date'):
            data['first_payment_date'] = data['first_payment_date'].isoformat()
        if data.get('last_payment_date'):
            data['last_payment_date'] = data['last_payment_date'].isoformat()
        if data['verification_status'].get('cop_last_checked'):
            data['verification_status']['cop_last_checked'] = data['verification_status']['cop_last_checked'].isoformat()
        if data['verification_status'].get('watchlist_last_checked'):
            data['verification_status']['watchlist_last_checked'] = data['verification_status']['watchlist_last_checked'].isoformat()
        # Convert Decimal to string
        data['total_amount_received'] = str(data['total_amount_received'])
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Payee':
        """Create from dictionary."""
        # Convert string timestamps back to datetime
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if isinstance(data.get('first_payment_date'), str):
            data['first_payment_date'] = datetime.fromisoformat(data['first_payment_date'])
        if isinstance(data.get('last_payment_date'), str):
            data['last_payment_date'] = datetime.fromisoformat(data['last_payment_date'])
        if isinstance(data.get('verification_status', {}).get('cop_last_checked'), str):
            data['verification_status']['cop_last_checked'] = datetime.fromisoformat(
                data['verification_status']['cop_last_checked']
            )
        if isinstance(data.get('verification_status', {}).get('watchlist_last_checked'), str):
            data['verification_status']['watchlist_last_checked'] = datetime.fromisoformat(
                data['verification_status']['watchlist_last_checked']
            )
        # Convert string amount back to Decimal
        if isinstance(data.get('total_amount_received'), str):
            data['total_amount_received'] = Decimal(data['total_amount_received'])
        return cls(**data)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }


"""Transaction entity model for Aegis fraud prevention platform."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


class TransactionStatus(str, Enum):
    """Transaction status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentChannel(str, Enum):
    """Payment channel types."""
    MOBILE_APP = "mobile_app"
    WEB = "web"
    BRANCH = "branch"
    ATM = "atm"


class PaymentType(str, Enum):
    """Payment type values."""
    FASTER_PAYMENT = "faster_payment"
    CHAPS = "chaps"
    BACS = "bacs"


class SessionData(BaseModel):
    """Session data for behavioral analysis."""
    session_id: str
    typing_patterns: Optional[List[Dict]] = None
    mouse_movements: Optional[List[Dict]] = None
    navigation_sequence: Optional[List[str]] = None
    active_call_detected: Optional[bool] = None
    time_on_page_seconds: Optional[int] = None


class Transaction(BaseModel):
    """Transaction entity representing a payment request."""
    
    transaction_id: str = Field(..., description="Unique transaction identifier (UUID)")
    customer_id: str = Field(..., description="Customer identifier (FK)")
    payee_account: str = Field(..., description="Payee account number")
    payee_name: str = Field(..., description="Payee name")
    amount: Decimal = Field(..., description="Transaction amount")
    currency: str = Field(default="GBP", description="ISO 4217 currency code")
    payment_channel: PaymentChannel = Field(..., description="Payment channel")
    payment_type: PaymentType = Field(..., description="Payment type")
    device_fingerprint: Optional[str] = Field(None, description="Device fingerprint")
    ip_address: Optional[str] = Field(None, description="IP address")
    session_data: Optional[SessionData] = Field(None, description="Session data")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Update timestamp")
    status: TransactionStatus = Field(default=TransactionStatus.PENDING, description="Transaction status")
    decision_id: Optional[str] = Field(None, description="Fraud decision ID (FK)")
    case_id: Optional[str] = Field(None, description="Case ID if escalated (FK)")
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate amount is positive with max 2 decimal places."""
        if v <= 0:
            raise ValueError('Amount must be positive')
        if v.as_tuple().exponent < -2:
            raise ValueError('Amount must have maximum 2 decimal places')
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code."""
        # Simple validation for common codes, can be expanded
        valid_currencies = ['GBP', 'EUR', 'USD']
        if v not in valid_currencies:
            raise ValueError(f'Currency must be one of {valid_currencies}')
        return v
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for DynamoDB storage."""
        data = self.dict()
        # Convert datetime to ISO string
        data['created_at'] = data['created_at'].isoformat()
        data['updated_at'] = data['updated_at'].isoformat()
        # Convert Decimal to string for JSON serialization
        data['amount'] = str(data['amount'])
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Transaction':
        """Create from dictionary."""
        # Convert string timestamps back to datetime
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        # Convert string amount back to Decimal
        if isinstance(data.get('amount'), str):
            data['amount'] = Decimal(data['amount'])
        return cls(**data)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }


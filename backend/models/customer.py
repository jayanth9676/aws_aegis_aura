"""Customer entity model for Aegis fraud prevention platform."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


class RiskTier(str, Enum):
    """Customer risk tier values."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class VulnerabilityIndicator(str, Enum):
    """Customer vulnerability indicators."""
    ELDERLY = "elderly"
    RECENTLY_BEREAVED = "recently_bereaved"
    COGNITIVE_IMPAIRMENT = "cognitive_impairment"
    FINANCIAL_DIFFICULTY = "financial_difficulty"
    MENTAL_HEALTH = "mental_health"
    LANGUAGE_BARRIER = "language_barrier"


class AccountType(str, Enum):
    """Account type values."""
    PERSONAL = "personal"
    BUSINESS = "business"


class KYCData(BaseModel):
    """Know Your Customer data."""
    date_of_birth: date
    postcode: str
    account_creation_date: date
    account_type: AccountType
    employment_status: Optional[str] = None
    income_band: Optional[str] = None
    
    @validator('date_of_birth')
    def validate_age(cls, v):
        """Validate customer is 18+ years old."""
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError('Customer must be 18 years or older')
        return v


class RiskProfile(BaseModel):
    """Customer risk profile."""
    risk_tier: RiskTier
    vulnerability_indicators: List[VulnerabilityIndicator] = []
    previous_fraud_victim: bool = False
    account_takeover_history: bool = False


class TransactionHistorySummary(BaseModel):
    """Transaction history summary statistics."""
    total_transactions_30d: int = 0
    total_amount_30d: Decimal = Decimal('0.00')
    unique_payees_30d: int = 0
    max_single_transaction_30d: Decimal = Decimal('0.00')
    typical_transaction_amount: Decimal = Decimal('0.00')
    typical_transaction_frequency: str = "weekly"  # daily | weekly | monthly


class Customer(BaseModel):
    """Customer entity representing a bank customer."""
    
    customer_id: str = Field(..., description="Unique customer identifier (UUID)")
    external_customer_id: str = Field(..., description="Bank's internal customer ID")
    account_number: str = Field(..., description="Encrypted account number")
    kyc_data: KYCData = Field(..., description="KYC information")
    risk_profile: RiskProfile = Field(..., description="Risk profile")
    transaction_history_summary: TransactionHistorySummary = Field(
        default_factory=TransactionHistorySummary,
        description="Transaction history summary"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for DynamoDB storage."""
        data = self.dict()
        # Convert dates to ISO strings
        data['created_at'] = data['created_at'].isoformat()
        data['updated_at'] = data['updated_at'].isoformat()
        data['kyc_data']['date_of_birth'] = data['kyc_data']['date_of_birth'].isoformat()
        data['kyc_data']['account_creation_date'] = data['kyc_data']['account_creation_date'].isoformat()
        # Convert Decimals to strings
        data['transaction_history_summary']['total_amount_30d'] = str(
            data['transaction_history_summary']['total_amount_30d']
        )
        data['transaction_history_summary']['max_single_transaction_30d'] = str(
            data['transaction_history_summary']['max_single_transaction_30d']
        )
        data['transaction_history_summary']['typical_transaction_amount'] = str(
            data['transaction_history_summary']['typical_transaction_amount']
        )
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Customer':
        """Create from dictionary."""
        # Convert string timestamps back to datetime
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        # Convert KYC dates
        if isinstance(data.get('kyc_data', {}).get('date_of_birth'), str):
            data['kyc_data']['date_of_birth'] = date.fromisoformat(data['kyc_data']['date_of_birth'])
        if isinstance(data.get('kyc_data', {}).get('account_creation_date'), str):
            data['kyc_data']['account_creation_date'] = date.fromisoformat(data['kyc_data']['account_creation_date'])
        # Convert Decimals
        if isinstance(data.get('transaction_history_summary', {}).get('total_amount_30d'), str):
            data['transaction_history_summary']['total_amount_30d'] = Decimal(
                data['transaction_history_summary']['total_amount_30d']
            )
        if isinstance(data.get('transaction_history_summary', {}).get('max_single_transaction_30d'), str):
            data['transaction_history_summary']['max_single_transaction_30d'] = Decimal(
                data['transaction_history_summary']['max_single_transaction_30d']
            )
        if isinstance(data.get('transaction_history_summary', {}).get('typical_transaction_amount'), str):
            data['transaction_history_summary']['typical_transaction_amount'] = Decimal(
                data['transaction_history_summary']['typical_transaction_amount']
            )
        return cls(**data)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }


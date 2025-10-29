"""Neptune graph schema definitions for Aegis fraud prevention platform."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field


class AccountType(str, Enum):
    """Account type values."""
    PERSONAL = "personal"
    BUSINESS = "business"


class FlaggingAlgorithm(str, Enum):
    """Mule flagging algorithm types."""
    ISOLATION_FOREST = "isolation_forest"
    GNN = "gnn"
    MANUAL = "manual"
    RULE_BASED = "rule_based"


class SuspectedTypology(str, Enum):
    """Suspected mule network typology."""
    LAYERING = "layering"
    STRUCTURING = "structuring"
    CASH_OUT = "cash_out"
    MONEY_MULE = "money_mule"


class AccountVertex(BaseModel):
    """Account vertex schema for Neptune graph."""
    
    # Vertex ID
    account_id: str = Field(..., description="Unique account identifier")
    
    # Properties
    account_number: str
    account_type: AccountType
    creation_date: datetime
    mule_probability: Decimal = Field(default=Decimal('0.0'), ge=0.0, le=1.0)
    is_flagged_mule: bool = False
    flagged_date: Optional[datetime] = None
    flagging_algorithm: Optional[FlaggingAlgorithm] = None
    
    # Transaction statistics
    total_inbound_transactions: int = 0
    total_outbound_transactions: int = 0
    total_inbound_amount: Decimal = Decimal('0.0')
    total_outbound_amount: Decimal = Decimal('0.0')
    unique_senders: int = 0
    unique_recipients: int = 0
    rapid_turnover_ratio: Decimal = Decimal('0.0')
    
    def to_properties(self) -> Dict:
        """Convert to Neptune properties dict."""
        props = {
            'account_number': self.account_number,
            'account_type': self.account_type.value,
            'creation_date': self.creation_date.isoformat(),
            'mule_probability': float(self.mule_probability),
            'is_flagged_mule': self.is_flagged_mule,
            'total_inbound_transactions': self.total_inbound_transactions,
            'total_outbound_transactions': self.total_outbound_transactions,
            'total_inbound_amount': float(self.total_inbound_amount),
            'total_outbound_amount': float(self.total_outbound_amount),
            'unique_senders': self.unique_senders,
            'unique_recipients': self.unique_recipients,
            'rapid_turnover_ratio': float(self.rapid_turnover_ratio),
        }
        
        if self.flagged_date:
            props['flagged_date'] = self.flagged_date.isoformat()
        if self.flagging_algorithm:
            props['flagging_algorithm'] = self.flagging_algorithm.value
        
        return props
    
    @classmethod
    def from_properties(cls, vertex_id: str, properties: Dict) -> 'AccountVertex':
        """Create from Neptune properties dict."""
        data = {
            'account_id': vertex_id,
            'account_number': properties.get('account_number'),
            'account_type': properties.get('account_type'),
            'creation_date': datetime.fromisoformat(properties.get('creation_date')),
            'mule_probability': Decimal(str(properties.get('mule_probability', 0.0))),
            'is_flagged_mule': properties.get('is_flagged_mule', False),
            'total_inbound_transactions': properties.get('total_inbound_transactions', 0),
            'total_outbound_transactions': properties.get('total_outbound_transactions', 0),
            'total_inbound_amount': Decimal(str(properties.get('total_inbound_amount', 0.0))),
            'total_outbound_amount': Decimal(str(properties.get('total_outbound_amount', 0.0))),
            'unique_senders': properties.get('unique_senders', 0),
            'unique_recipients': properties.get('unique_recipients', 0),
            'rapid_turnover_ratio': Decimal(str(properties.get('rapid_turnover_ratio', 0.0))),
        }
        
        if properties.get('flagged_date'):
            data['flagged_date'] = datetime.fromisoformat(properties.get('flagged_date'))
        if properties.get('flagging_algorithm'):
            data['flagging_algorithm'] = properties.get('flagging_algorithm')
        
        return cls(**data)


class PaymentEdge(BaseModel):
    """Payment edge schema for Neptune graph."""
    
    transaction_id: str
    amount: Decimal
    timestamp: datetime
    payment_channel: str
    risk_score: int = Field(ge=0, le=100)
    
    def to_properties(self) -> Dict:
        """Convert to Neptune properties dict."""
        return {
            'transaction_id': self.transaction_id,
            'amount': float(self.amount),
            'timestamp': self.timestamp.isoformat(),
            'payment_channel': self.payment_channel,
            'risk_score': self.risk_score,
        }
    
    @classmethod
    def from_properties(cls, properties: Dict) -> 'PaymentEdge':
        """Create from Neptune properties dict."""
        return cls(
            transaction_id=properties.get('transaction_id'),
            amount=Decimal(str(properties.get('amount'))),
            timestamp=datetime.fromisoformat(properties.get('timestamp')),
            payment_channel=properties.get('payment_channel'),
            risk_score=properties.get('risk_score', 0),
        )


class MuleNetworkVertex(BaseModel):
    """Mule network cluster vertex schema for Neptune graph."""
    
    # Vertex ID
    network_id: str = Field(..., description="Unique network identifier")
    
    # Properties
    detection_date: datetime
    confidence_score: Decimal = Field(ge=0.0, le=1.0)
    account_count: int
    transaction_count: int
    total_amount: Decimal
    suspected_typology: SuspectedTypology
    analyst_reviewed: bool = False
    case_id: Optional[str] = None
    
    def to_properties(self) -> Dict:
        """Convert to Neptune properties dict."""
        props = {
            'detection_date': self.detection_date.isoformat(),
            'confidence_score': float(self.confidence_score),
            'account_count': self.account_count,
            'transaction_count': self.transaction_count,
            'total_amount': float(self.total_amount),
            'suspected_typology': self.suspected_typology.value,
            'analyst_reviewed': self.analyst_reviewed,
        }
        
        if self.case_id:
            props['case_id'] = self.case_id
        
        return props
    
    @classmethod
    def from_properties(cls, vertex_id: str, properties: Dict) -> 'MuleNetworkVertex':
        """Create from Neptune properties dict."""
        data = {
            'network_id': vertex_id,
            'detection_date': datetime.fromisoformat(properties.get('detection_date')),
            'confidence_score': Decimal(str(properties.get('confidence_score'))),
            'account_count': properties.get('account_count'),
            'transaction_count': properties.get('transaction_count'),
            'total_amount': Decimal(str(properties.get('total_amount'))),
            'suspected_typology': properties.get('suspected_typology'),
            'analyst_reviewed': properties.get('analyst_reviewed', False),
        }
        
        if properties.get('case_id'):
            data['case_id'] = properties.get('case_id')
        
        return cls(**data)


# Gremlin query templates
GREMLIN_QUERIES = {
    'add_account': """
        g.addV('account')
         .property(id, accountId)
         .property('account_number', accountNumber)
         .property('account_type', accountType)
         .property('creation_date', creationDate)
         .property('mule_probability', muleProbability)
         .property('is_flagged_mule', isFlaggedMule)
    """,
    
    'add_payment': """
        g.V(fromAccount)
         .addE('payment')
         .to(__.V(toAccount))
         .property('transaction_id', transactionId)
         .property('amount', amount)
         .property('timestamp', timestamp)
         .property('payment_channel', paymentChannel)
         .property('risk_score', riskScore)
    """,
    
    'get_account': """
        g.V(accountId).valueMap(true)
    """,
    
    'update_account_stats': """
        g.V(accountId)
         .property('total_inbound_transactions', inboundTxns)
         .property('total_outbound_transactions', outboundTxns)
         .property('total_inbound_amount', inboundAmount)
         .property('total_outbound_amount', outboundAmount)
         .property('unique_senders', uniqueSenders)
         .property('unique_recipients', uniqueRecipients)
         .property('rapid_turnover_ratio', turnoverRatio)
    """,
}


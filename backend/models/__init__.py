"""Data models for Aegis fraud prevention platform."""

from .transaction import Transaction, TransactionStatus
from .customer import Customer, RiskTier, VulnerabilityIndicator
from .payee import Payee, COPMatchLevel, WatchlistStatus
from .fraud_decision import FraudDecision, DecisionAction, ReasonCode
from .case import Case, CaseStatus, CasePriority, ResolutionType
from .analyst import Analyst, AnalystRole, AnalystStatus
from .audit_log import AuditLog, EventType, UserType, ResourceType, Action

__all__ = [
    # Transaction
    'Transaction',
    'TransactionStatus',
    
    # Customer
    'Customer',
    'RiskTier',
    'VulnerabilityIndicator',
    
    # Payee
    'Payee',
    'COPMatchLevel',
    'WatchlistStatus',
    
    # Fraud Decision
    'FraudDecision',
    'DecisionAction',
    'ReasonCode',
    
    # Case
    'Case',
    'CaseStatus',
    'CasePriority',
    'ResolutionType',
    
    # Analyst
    'Analyst',
    'AnalystRole',
    'AnalystStatus',
    
    # Audit Log
    'AuditLog',
    'EventType',
    'UserType',
    'ResourceType',
    'Action',
]


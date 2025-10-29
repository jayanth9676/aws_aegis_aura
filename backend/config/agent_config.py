"""Agent configuration for Aegis multi-agent system."""

import os
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class AgentConfig:
    """Configuration for individual agents."""
    
    name: str
    model_id: str = "global.anthropic.claude-sonnet-4-20250514-v1:0"
    embedding_model_id: str = "amazon.titan-embed-text-v2:0"
    description: str = "Fraud analysis and risk assessment"
    guardrails_id: Optional[str] = None
    guardrails_version: str = "DRAFT"
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    
    # AgentCore Memory settings
    session_ttl: int = 3600  # 1 hour
    long_term_storage: bool = True
    
    # Performance settings
    timeout_seconds: int = 30
    max_retries: int = 3
    
    @classmethod
    def supervisor_config(cls) -> 'AgentConfig':
        """Configuration for Supervisor Agent."""
        return cls(
            name="supervisor_agent",
            description="Central orchestrator for fraud investigations. Coordinates multiple context agents, synthesizes evidence, and determines final fraud decisions.",
            temperature=0.5,
            timeout_seconds=60
        )
    
    @classmethod
    def transaction_context_config(cls) -> 'AgentConfig':
        """Configuration for Transaction Context Agent."""
        return cls(
            name="transaction_context_agent",
            description="Analyzes transaction patterns, velocity anomalies, and Confirmation of Payee (CoP) verification results to identify transaction-level fraud risks.",
            temperature=0.3,
            timeout_seconds=15
        )
    
    @classmethod
    def customer_context_config(cls) -> 'AgentConfig':
        """Configuration for Customer Context Agent."""
        return cls(
            name="customer_context_agent",
            description="Analyzes customer profiles, demographics, vulnerability factors, and fraud history to assess customer-specific risks including scam susceptibility.",
            temperature=0.3,
            timeout_seconds=15
        )
    
    @classmethod
    def behavioral_analysis_config(cls) -> 'AgentConfig':
        """Configuration for Behavioral Analysis Agent."""
        return cls(
            name="behavioral_analysis_agent",
            description="Analyzes real-time behavioral biometrics including typing speed, mouse patterns, navigation flow, active call detection, and hesitation signals to identify coerced, coached, or fraudulent user behavior.",
            temperature=0.2,
            timeout_seconds=20
        )
    
    @classmethod
    def risk_scoring_config(cls) -> 'AgentConfig':
        """Configuration for Risk Scoring Agent."""
        return cls(
            name="risk_scoring_agent",
            description="Synthesizes evidence from all context agents and ML models to generate comprehensive risk scores with SHAP explanations for model transparency.",
            temperature=0.1,
            timeout_seconds=25
        )
    
    @classmethod
    def dialogue_config(cls) -> 'AgentConfig':
        """Configuration for Dialogue Agent with Guardrails."""
        return cls(
            name="dialogue_agent",
            description="Engages customers with conversational AI to verify suspicious transactions, educate about scams, and gather additional context through empathetic dialogue.",
            guardrails_id=os.getenv('DIALOGUE_GUARDRAILS_ID'),
            temperature=0.8,
            max_tokens=500,
            timeout_seconds=20
        )
    
    @classmethod
    def investigation_config(cls) -> 'AgentConfig':
        """Configuration for Investigation Agent."""
        return cls(
            name="investigation_agent",
            temperature=0.6,
            max_tokens=8192,
            timeout_seconds=120
        )
    
    @classmethod
    def payee_context_config(cls) -> 'AgentConfig':
        """Configuration for Payee Context Agent."""
        return cls(
            name="payee_context_agent",
            description="Analyzes payee verification (CoP), watchlist screening, and account history to identify potentially fraudulent or high-risk payment recipients.",
            temperature=0.3,
            timeout_seconds=15
        )
    
    @classmethod
    def graph_relationship_config(cls) -> 'AgentConfig':
        """Configuration for Graph Relationship Agent."""
        return cls(
            name="graph_relationship_agent",
            description="Analyzes transaction networks using Neptune graph database and GNN models to detect mule accounts, money laundering patterns (fan-out, fan-in, circular flows, layering), and suspicious network structures.",
            temperature=0.2,
            timeout_seconds=25
        )
    
    @classmethod
    def intel_config(cls) -> 'AgentConfig':
        """Configuration for Intel Agent."""
        return cls(
            name="intel_agent",
            description="Performs Retrieval-Augmented Generation (RAG) queries against Bedrock Knowledge Base to retrieve fraud typologies, investigation SOPs, and regulatory guidance for identified scam patterns.",
            temperature=0.4,
            timeout_seconds=30
        )
    
    @classmethod
    def triage_config(cls) -> 'AgentConfig':
        """Configuration for Triage Agent."""
        return cls(
            name="triage_agent",
            description="Makes policy-driven decisions (Allow/Challenge/Block) based on risk scores, confidence levels, and institutional risk appetite thresholds.",
            temperature=0.2,
            timeout_seconds=15
        )
    
    @classmethod
    def policy_decision_config(cls) -> 'AgentConfig':
        """Configuration for Policy Decision Agent."""
        return cls(
            name="policy_decision_agent",
            description="Captures analyst decisions, compares with AI recommendations, analyzes disagreements, and generates feedback for continuous model improvement and policy refinement.",
            temperature=0.2,
            timeout_seconds=20
        )
    
    @classmethod
    def regulatory_reporting_config(cls) -> 'AgentConfig':
        """Configuration for Regulatory Reporting Agent."""
        return cls(
            name="regulatory_reporting_agent",
            description="Generates compliant Suspicious Activity Reports (SAR/STR) with AI-powered narrative creation, ensuring regulatory requirements are met while providing clear, factual documentation of fraud indicators.",
            temperature=0.2,
            timeout_seconds=30
        )


# Agent config instances for easy access
SUPERVISOR_CONFIG = AgentConfig.supervisor_config()
TRANSACTION_CONTEXT_CONFIG = AgentConfig.transaction_context_config()
CUSTOMER_CONTEXT_CONFIG = AgentConfig.customer_context_config()
PAYEE_CONTEXT_CONFIG = AgentConfig.payee_context_config()
BEHAVIORAL_ANALYSIS_CONFIG = AgentConfig.behavioral_analysis_config()
GRAPH_RELATIONSHIP_CONFIG = AgentConfig.graph_relationship_config()
RISK_SCORING_CONFIG = AgentConfig.risk_scoring_config()
INTEL_CONFIG = AgentConfig.intel_config()
TRIAGE_CONFIG = AgentConfig.triage_config()
DIALOGUE_CONFIG = AgentConfig.dialogue_config()
INVESTIGATION_CONFIG = AgentConfig.investigation_config()
POLICY_DECISION_CONFIG = AgentConfig.policy_decision_config()
REGULATORY_REPORTING_CONFIG = AgentConfig.regulatory_reporting_config()


class SystemConfig:
    """Global system configuration."""
    
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID')
    
    # AWS Resources
    KNOWLEDGE_BASE_ID = os.getenv('KNOWLEDGE_BASE_ID')
    NEPTUNE_ENDPOINT = os.getenv('NEPTUNE_ENDPOINT')
    
    # DynamoDB Tables
    CASES_TABLE = os.getenv('CASES_TABLE', 'aegis-cases')
    TRANSACTIONS_TABLE = os.getenv('TRANSACTIONS_TABLE', 'aegis-transactions')
    CUSTOMERS_TABLE = os.getenv('CUSTOMERS_TABLE', 'aegis-customers')
    AUDIT_LOGS_TABLE = os.getenv('AUDIT_LOGS_TABLE', 'aegis-audit-logs')
    
    # S3 Buckets
    ML_MODELS_BUCKET = os.getenv('ML_MODELS_BUCKET', f'aegis-ml-models-{os.getenv("AWS_ACCOUNT_ID")}')
    DOCUMENTS_BUCKET = os.getenv('DOCUMENTS_BUCKET', f'aegis-kb-documents-{os.getenv("AWS_ACCOUNT_ID")}')
    
    # SageMaker Endpoints
    FRAUD_DETECTOR_ENDPOINT = os.getenv('FRAUD_DETECTOR_ENDPOINT', 'aegis-fraud-detector')
    MULE_DETECTOR_ENDPOINT = os.getenv('MULE_DETECTOR_ENDPOINT', 'aegis-mule-detector')
    BEHAVIORAL_MODEL_ENDPOINT = os.getenv('BEHAVIORAL_MODEL_ENDPOINT', 'aegis-behavioral-model')
    ANOMALY_DETECTOR_ENDPOINT = os.getenv('ANOMALY_DETECTOR_ENDPOINT', 'aegis-anomaly-detector')
    
    # Risk Thresholds
    BLOCK_THRESHOLD = float(os.getenv('BLOCK_THRESHOLD', '85'))
    CHALLENGE_THRESHOLD = float(os.getenv('CHALLENGE_THRESHOLD', '60'))
    HIGH_CONFIDENCE_THRESHOLD = float(os.getenv('HIGH_CONFIDENCE_THRESHOLD', '0.8'))
    
    # Performance Targets
    MAX_LATENCY_MS = int(os.getenv('MAX_LATENCY_MS', '500'))
    TARGET_FALSE_POSITIVE_RATE = float(os.getenv('TARGET_FALSE_POSITIVE_RATE', '0.03'))
    
    # Compliance
    AUDIT_LOG_RETENTION_YEARS = int(os.getenv('AUDIT_LOG_RETENTION_YEARS', '7'))
    
system_config = SystemConfig()




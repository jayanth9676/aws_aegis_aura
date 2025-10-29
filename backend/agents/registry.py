"""Agent registry for tool invocation."""

from tools import register_agent_tool

# Import all agents
from agents.context.transaction_context_agent import TransactionContextAgent
from agents.context.customer_context_agent import CustomerContextAgent
from agents.context.payee_context_agent import PayeeContextAgent
from agents.context.behavioral_analysis_agent import BehavioralAnalysisAgent
from agents.context.graph_relationship_agent import GraphRelationshipAgent
from agents.analysis.risk_scoring_agent import RiskScoringAgent
from agents.analysis.intel_agent import IntelAgent
from agents.decision.triage_agent import TriageAgent
from agents.decision.dialogue_agent import DialogueAgent
from agents.decision.investigation_agent import InvestigationAgent
from agents.decision.policy_decision_agent import PolicyDecisionAgent
from agents.decision.regulatory_reporting_agent import RegulatoryReportingAgent

# Register all agents as callable tools
register_agent_tool('TransactionContextAgent', TransactionContextAgent)
register_agent_tool('CustomerContextAgent', CustomerContextAgent)
register_agent_tool('PayeeContextAgent', PayeeContextAgent)
register_agent_tool('BehavioralAnalysisAgent', BehavioralAnalysisAgent)
register_agent_tool('GraphRelationshipAgent', GraphRelationshipAgent)
register_agent_tool('RiskScoringAgent', RiskScoringAgent)
register_agent_tool('IntelAgent', IntelAgent)
register_agent_tool('TriageAgent', TriageAgent)
register_agent_tool('DialogueAgent', DialogueAgent)
register_agent_tool('InvestigationAgent', InvestigationAgent)
register_agent_tool('PolicyDecisionAgent', PolicyDecisionAgent)
register_agent_tool('RegulatoryReportingAgent', RegulatoryReportingAgent)

__all__ = [
    'TransactionContextAgent',
    'CustomerContextAgent',
    'PayeeContextAgent',
    'BehavioralAnalysisAgent',
    'GraphRelationshipAgent',
    'RiskScoringAgent',
    'IntelAgent',
    'TriageAgent',
    'DialogueAgent',
    'InvestigationAgent',
    'PolicyDecisionAgent',
    'RegulatoryReportingAgent'
]


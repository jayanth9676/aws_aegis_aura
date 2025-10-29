"""AgentCore Gateway tools for Aegis platform."""

from typing import Dict, Callable, Optional, Any
import inspect
import asyncio
from decimal import Decimal

def decimal_to_python(obj):
    """Convert Decimal types to Python native types for JSON serialization."""
    if isinstance(obj, list):
        return [decimal_to_python(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        # Convert Decimal to int if it's a whole number, otherwise float
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj

# Tool registry
_TOOL_REGISTRY: Dict[str, Callable] = {}
_AGENT_REGISTRY: Dict[str, Callable] = {}

def register_tool(name: str):
    """Decorator to register a tool."""
    def decorator(func: Callable) -> Callable:
        _TOOL_REGISTRY[name] = func
        return func
    return decorator

def register_agent_tool(name: str, agent_class):
    """Register an agent as a callable tool."""
    _AGENT_REGISTRY[name] = agent_class
    return agent_class

def get_tool(name: str) -> Optional[Callable]:
    """Get a registered tool by name."""
    tool = _TOOL_REGISTRY.get(name)
    if tool:
        return tool
    
    # Check if it's an agent tool
    agent_class = _AGENT_REGISTRY.get(name)
    if agent_class:
        # Return a function that instantiates and executes the agent
        async def agent_executor(params: Dict) -> Dict:
            try:
                # Convert Decimal types in params
                clean_params = decimal_to_python(params)
                
                # Create agent instance (agents create their own config internally)
                agent = agent_class()
                
                # Execute agent
                result = await agent.execute(clean_params)
                
                # Convert Decimal types in result
                return decimal_to_python(result)
            except Exception as e:
                return {'error': str(e), 'agent': name}
        
        return agent_executor
    
    return None

async def invoke_tool(name: str, params: Dict) -> Dict:
    """Invoke a tool by name with parameters."""
    tool = get_tool(name)
    if not tool:
        return {'error': f'Tool not found: {name}'}
    
    try:
        # Convert Decimal types in params
        clean_params = decimal_to_python(params)
        
        # Check if async
        if inspect.iscoroutinefunction(tool):
            result = await tool(clean_params)
        else:
            result = tool(clean_params)
            # If result is a coroutine, await it
            if inspect.iscoroutine(result):
                result = await result
        
        # Convert Decimal types in result
        return decimal_to_python(result)
    except Exception as e:
        return {'error': str(e), 'tool': name}

# Import and register all tools
from .payment_tools import (
    transaction_analysis_tool,
    payment_api_tool,
    velocity_analysis_tool
)

from .customer_tools import (
    customer_analysis_tool,
    fraud_history_tool
)

from .verification_tools import (
    verification_of_payee_tool,
    watchlist_tool
)

from .graph_tools import (
    graph_analysis_tool,
    mule_detection_tool as graph_mule_detection
)

from .ml_model_tools import (
    fraud_detection_tool,
    shap_explainer_tool,
    behavioral_analysis_tool,
    mule_detection_tool
)

from .knowledge_base_tools import (
    knowledge_base_tool,
    payee_analysis_tool
)

from .case_management_tools import (
    escalation_tool,
    case_management_tool,
    feedback_storage_tool,
    model_review_queue_tool
)

from .regulatory_tools import (
    sar_storage_tool,
    fraud_history_tool as regulatory_fraud_history,
    velocity_analysis_tool as regulatory_velocity
)

# Import agents to register as tools
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

# Register tools
register_tool('TransactionAnalysisTool')(transaction_analysis_tool)
register_tool('PaymentAPITool')(payment_api_tool)
register_tool('VelocityAnalysisTool')(velocity_analysis_tool)
register_tool('CustomerAnalysisTool')(customer_analysis_tool)
register_tool('FraudHistoryTool')(fraud_history_tool)
register_tool('VerificationOfPayeeTool')(verification_of_payee_tool)
register_tool('WatchlistTool')(watchlist_tool)
register_tool('GraphAnalysisTool')(graph_analysis_tool)
register_tool('FraudDetectionTool')(fraud_detection_tool)
register_tool('SHAPExplainerTool')(shap_explainer_tool)
register_tool('BehavioralAnalysisTool')(behavioral_analysis_tool)
register_tool('MuleDetectionTool')(mule_detection_tool)
register_tool('KnowledgeBaseTool')(knowledge_base_tool)
register_tool('PayeeAnalysisTool')(payee_analysis_tool)
register_tool('EscalationTool')(escalation_tool)
register_tool('CaseManagementTool')(case_management_tool)
register_tool('FeedbackStorageTool')(feedback_storage_tool)
register_tool('ModelReviewQueueTool')(model_review_queue_tool)
register_tool('SARStorageTool')(sar_storage_tool)

# Register agents as tools
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
    'register_tool',
    'register_agent_tool',
    'get_tool',
    'invoke_tool',
    'transaction_analysis_tool',
    'payment_api_tool',
    'verification_of_payee_tool',
    'fraud_detection_tool',
    'knowledge_base_tool'
]




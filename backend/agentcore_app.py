"""AgentCore Runtime Application Wrapper for Aegis Platform."""

import asyncio
from typing import Dict, List, Optional

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from agents.supervisor_agent import SupervisorAgent
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

from utils import get_logger

logger = get_logger(__name__)


class AegisAgentCoreApp:
    """AgentCore Runtime application for Aegis fraud prevention platform."""
    
    def __init__(self):
        """Initialize AgentCore application with all agents."""
        self.app = BedrockAgentCoreApp()
        self.agents = {}
        self.supervisor_agent = None
        
        logger.info("Initializing Aegis AgentCore Application")
    
    async def initialize(self):
        """Initialize AgentCore Runtime components."""
        try:
            # Initialize Supervisor Agent
            logger.info("Initializing Supervisor Agent...")
            self.supervisor_agent = SupervisorAgent()
            self.agents['supervisor'] = self.supervisor_agent

            # Initialize all other agents
            logger.info("Initializing Context Agents...")
            self.agents['transaction_context'] = TransactionContextAgent()
            self.agents['customer_context'] = CustomerContextAgent()
            self.agents['payee_context'] = PayeeContextAgent()
            self.agents['behavioral_analysis'] = BehavioralAnalysisAgent()
            self.agents['graph_relationship'] = GraphRelationshipAgent()

            logger.info("Initializing Analysis Agents...")
            self.agents['risk_scoring'] = RiskScoringAgent()
            self.agents['intel'] = IntelAgent()

            logger.info("Initializing Decision Agents...")
            self.agents['triage'] = TriageAgent()
            self.agents['dialogue'] = DialogueAgent()
            self.agents['investigation'] = InvestigationAgent()
            self.agents['policy_decision'] = PolicyDecisionAgent()
            self.agents['regulatory_reporting'] = RegulatoryReportingAgent()

            logger.info(f"AgentCore application initialized successfully with {len(self.agents)} agents")

        except Exception as e:
            logger.error(f"Failed to initialize AgentCore application", error=str(e))
            raise
    
    async def investigate_transaction(self, transaction_data: Dict) -> Dict:
        """Investigate a transaction using the supervisor agent.
        
        Args:
            transaction_data: Transaction details
            
        Returns:
            Investigation result with decision and evidence
        """
        try:
            logger.info(
                "Starting transaction investigation",
                transaction_id=transaction_data.get('transaction_id')
            )

            result = await self.supervisor_agent.investigate_transaction(transaction_data)

            logger.info(
                "Transaction investigation completed",
                transaction_id=transaction_data.get('transaction_id'),
                decision=result.get('decision')
            )

            return result

        except Exception as e:
            logger.error(
                "Transaction investigation failed",
                transaction_id=transaction_data.get('transaction_id'),
                error=str(e)
            )
            return {
                'success': False,
                'error': str(e),
                'decision': 'ALLOW',
                'reason': 'System error during investigation'
            }
    
    async def engage_customer(self, transaction_data: Dict, risk_factors: List[str]) -> Dict:
        """Engage customer via dialogue agent.
        
        Args:
            transaction_data: Transaction details
            risk_factors: List of identified risk factors
            
        Returns:
            Dialogue response and assessment
        """
        try:
            dialogue_agent = self.agents.get('dialogue')
            if dialogue_agent:
                result = await dialogue_agent.engage_customer(transaction_data, risk_factors)
            else:
                result = {'success': False, 'error': 'Dialogue agent not initialized'}
            return result
        except Exception as e:
            logger.error("Customer engagement failed", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'message': 'Unable to engage customer at this time'
            }
    
    async def create_investigation_case(self, transaction_data: Dict, fraud_decision: Dict) -> Dict:
        """Create investigation case via investigation agent.
        
        Args:
            transaction_data: Transaction details
            fraud_decision: Fraud decision details
            
        Returns:
            Case creation result
        """
        try:
            investigation_agent = self.agents.get('investigation')
            if investigation_agent:
                result = await investigation_agent.create_case(transaction_data, fraud_decision)
            else:
                result = {'success': False, 'error': 'Investigation agent not initialized'}
            return result
        except Exception as e:
            logger.error("Case creation failed", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    async def query_intelligence(self, query: str) -> Dict:
        """Query fraud intelligence via intel agent.
        
        Args:
            query: Intelligence query
            
        Returns:
            Intelligence query results
        """
        try:
            intel_agent = self.agents.get('intel')
            if intel_agent:
                result = await intel_agent.query(query)
            else:
                result = {'success': False, 'error': 'Intel agent not initialized', 'documents': []}
            return result
        except Exception as e:
            logger.error("Intelligence query failed", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'documents': []
            }
    
    async def shutdown(self):
        """Shutdown AgentCore application."""
        try:
            # Cleanup any resources if needed
            logger.info("AgentCore application shutdown complete")
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))


# Global application instance
aegis_app: Optional[AegisAgentCoreApp] = None


async def get_aegis_app() -> AegisAgentCoreApp:
    """Get or create Aegis AgentCore application instance."""
    global aegis_app
    if aegis_app is None:
        aegis_app = AegisAgentCoreApp()
        await aegis_app.initialize()
    return aegis_app


async def shutdown_aegis_app():
    """Shutdown Aegis AgentCore application."""
    global aegis_app
    if aegis_app is not None:
        await aegis_app.shutdown()
        aegis_app = None


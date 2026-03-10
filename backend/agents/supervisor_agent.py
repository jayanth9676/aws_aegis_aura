"""Supervisor Agent — Dynamic Orchestration with Strands SDK GraphBuilder.

Migrated from static asyncio.gather() to a state-based workflow utilizing 
the March 2026 standard `GraphBuilder` with conditional edges.
"""

from typing import Dict, Any
import time

from strands import GraphBuilder, Agent

from agents.base_agent import AegisBaseAgent, create_agent, record_investigation_summary, store_memory
from agents.pydantic_models import InvestigationState, TriageAction
from config import AgentConfig, agentcore_config
from utils import trace_operation, get_logger

logger = get_logger("agent.supervisor")


# ── Conditional Edge Functions ──────────────────────────────────────────

def needs_behavioral_analysis(state: InvestigationState) -> bool:
    """Only route to behavioral if device or session data is available in the payload."""
    tx = state.transaction
    return bool(tx.get("session_data") or tx.get("device_fingerprint"))

def needs_graph_analysis(state: InvestigationState) -> bool:
    """Only route to graph analysis if this is not a known/saved payee."""
    tx = state.transaction
    return tx.get("is_saved_payee", False) is False

def needs_reflection(state: InvestigationState) -> bool:
    """Reflection loop condition for Triage to self-correct."""
    if not state.decision:
        return False
    if state.reflection_count >= state.max_reflections:
        return False
    
    # If the decision is BLOCK but risk score was low, force reflection.
    if state.decision == TriageAction.BLOCK and state.risk_score < 40.0:
        return True
    
    # Needs revision flag explicitly set by the triage model.
    if getattr(state, "needs_revision", False):
        return True
    
    return False

def triage_complete(state: InvestigationState) -> bool:
    """Condition to exit reflection loop and proceed to post-triage."""
    return not needs_reflection(state)


class SupervisorAgent(AegisBaseAgent):
    """Central orchestrator managing the fraud workflow via GraphBuilder."""
    
    def __init__(self):
        super().__init__("supervisor_agent", AgentConfig.supervisor_config())
        self._graph = self._build_investigation_graph()

    def _build_investigation_graph(self):
        """Build the dynamic orchestration Graph using Strands SDK."""
        builder = GraphBuilder()
        
        # ── Nodes: Context Gathering (Parallel by default when executed) ──
        builder.add_node(self._node_transaction_context, "transaction_context")
        builder.add_node(self._node_customer_context, "customer_context")
        builder.add_node(self._node_payee_context, "payee_context")
        builder.add_node(self._node_behavioral_analysis, "behavioral_analysis")
        builder.add_node(self._node_graph_analysis, "graph_analysis")
        
        # ── Nodes: Synthesis & Decision ──
        builder.add_node(self._node_risk_scoring, "risk_scoring")
        builder.add_node(self._node_intel, "intel")
        builder.add_node(self._node_triage, "triage")
        builder.add_node(self._node_post_triage, "post_triage")
        
        # ── Edges: Conditional Routing ──
        # Entry starts context agents
        builder.add_edge("__start__", "transaction_context")
        builder.add_edge("__start__", "customer_context")
        builder.add_edge("__start__", "payee_context")
        
        builder.add_edge("__start__", "behavioral_analysis", condition=needs_behavioral_analysis)
        builder.add_edge("__start__", "graph_analysis", condition=needs_graph_analysis)
        
        # Context merges into analysis (implicit synchronization in Strands Graph)
        builder.add_edge("transaction_context", "risk_scoring")
        builder.add_edge("customer_context", "risk_scoring")
        builder.add_edge("payee_context", "risk_scoring")
        builder.add_edge("behavioral_analysis", "risk_scoring")
        builder.add_edge("graph_analysis", "risk_scoring")
        
        builder.add_edge("risk_scoring", "intel")
        builder.add_edge("intel", "triage")
        
        # ── Edges: Reflection Loop ──
        builder.add_edge("triage", "triage", condition=needs_reflection)
        builder.add_edge("triage", "post_triage", condition=triage_complete)
        
        # Graph constraints
        builder.set_max_node_executions(15)  # Max total steps
        builder.set_execution_timeout(10.0)   # Low latency limit per FinCon papers
        builder.reset_on_revisit(True)       # Reset node state if reflecting
        
        return builder.build()

    # ──────────────────────────────────────────────────────────────────
    # Node Implementation Wrappers (Adapter layer for the graph)
    # ──────────────────────────────────────────────────────────────────
    async def _node_transaction_context(self, state: InvestigationState) -> InvestigationState:
        res = await self.invoke_tool("TransactionContextAgent", {'transaction': state.transaction, 'session_id': state.session_id})
        state.transaction_context = res
        return state

    async def _node_customer_context(self, state: InvestigationState) -> InvestigationState:
        res = await self.invoke_tool("CustomerContextAgent", {'customer_id': state.transaction.get('customer_id'), 'session_id': state.session_id})
        state.customer_context = res
        return state

    async def _node_payee_context(self, state: InvestigationState) -> InvestigationState:
        res = await self.invoke_tool("PayeeContextAgent", {
            'payee_account': state.transaction.get('payee_account'),
            'payee_name': state.transaction.get('payee_name'),
            'session_id': state.session_id
        })
        state.payee_context = res
        return state

    async def _node_behavioral_analysis(self, state: InvestigationState) -> InvestigationState:
        res = await self.invoke_tool("BehavioralAnalysisAgent", {
            'session_data': state.transaction.get('session_data', {}),
            'device_fingerprint': state.transaction.get('device_fingerprint'),
            'session_id': state.session_id
        })
        state.behavioral_analysis = res
        return state

    async def _node_graph_analysis(self, state: InvestigationState) -> InvestigationState:
        res = await self.invoke_tool("GraphRelationshipAgent", {
            'sender_account': state.transaction.get('sender_account'),
            'receiver_account': state.transaction.get('payee_account'),
            'session_id': state.session_id
        })
        state.graph_analysis = res
        return state

    async def _node_risk_scoring(self, state: InvestigationState) -> InvestigationState:
        context_results = {
            'transaction_context': state.transaction_context,
            'customer_context': state.customer_context,
            'payee_context': state.payee_context,
            'behavioral_analysis': state.behavioral_analysis,
            'graph_analysis': state.graph_analysis
        }
        res = await self.invoke_tool("RiskScoringAgent", {
            'context_results': {k: v for k, v in context_results.items() if v},
            'transaction': state.transaction,
            'session_id': state.session_id
        })
        
        # Apply output directly into Pydantic schema structure
        state.risk_score = res.get("risk_score", 0.0)
        state.confidence = res.get("confidence", 0.0)
        state.top_risk_factors = res.get("top_risk_factors", [])
        state.shap_values = res.get("shap_values", [])
        state.ml_fraud_probability = res.get("ml_fraud_probability", 0.0)
        state.reason_codes = res.get("reason_codes", [])
        return state
        
    async def _node_intel(self, state: InvestigationState) -> InvestigationState:
        context_results = {
            'transaction_context': state.transaction_context,
            'customer_context': state.customer_context
        }
        res = await self.invoke_tool("IntelAgent", {
            'transaction': state.transaction,
            'context_results': {k: v for k, v in context_results.items() if v},
            'session_id': state.session_id
        })
        state.intelligence = res
        return state

    async def _node_triage(self, state: InvestigationState) -> InvestigationState:
        state.reflection_count += 1
        evidence = {
            'transaction': state.transaction,
            'risk_score': state.risk_score,
            'top_risk_factors': [rf if isinstance(rf, dict) else rf.model_dump() for rf in state.top_risk_factors],
            'intelligence': state.intelligence,
            'reflection_count': state.reflection_count
        }
        
        res = await self.invoke_tool("TriageAgent", {
            'risk_score': state.risk_score,
            'confidence': state.confidence,
            'evidence': evidence,
            'session_id': state.session_id,
            'prior_decision': state.decision  # Passed during reflection
        })
        
        state.decision = res.get("action", TriageAction.ALLOW)
        state.decision_reasoning = res.get("reasoning", "")
        # Reflection signal from the LLM
        state.needs_revision = res.get("needs_revision", False) 
        return state

    async def _node_post_triage(self, state: InvestigationState) -> InvestigationState:
        """Saves investigation data and spawns subsequent systems based on triage result."""
        decision_payload = {
            'action': state.decision,
            'risk_score': state.risk_score,
            'reason_codes': state.reason_codes,
            'context_results': {
                'transaction': state.transaction_context,
                'customer': state.customer_context,
                'payee': state.payee_context,
                'graph': state.graph_analysis,
                'behavioral': state.behavioral_analysis
            },
            'analysis_results': {
                'confidence': state.confidence,
                'shap_values': [sv if isinstance(sv, dict) else sv.model_dump() for sv in state.shap_values],
                'ml_fraud_probability': state.ml_fraud_probability
            },
            'transaction': state.transaction,
            'transaction_id': state.session_id,
            'success': True
        }
        
        if state.session_id:
            await self.store_memory(f'session:{state.session_id}:decision_summary', decision_payload, ttl=agentcore_config.long_term_ttl)
            await record_investigation_summary(state.session_id, decision_payload, actor_id=self.name)
        
        action = state.decision
        case_id = f"CASE-{state.session_id}"
        
        # Fire and forget Case Management
        try:
            await self.invoke_tool('CaseManagementTool', {
                'action': 'create',
                'case_data': {
                    'case_id': case_id,
                    'transaction_id': state.session_id,
                    'customer_id': state.transaction.get('customer_id'),
                    'status': 'ESCALATED' if action in {TriageAction.BLOCK, TriageAction.CHALLENGE} else 'RESOLVED',
                    'priority': 'CRITICAL' if action == TriageAction.BLOCK else ('HIGH' if action == TriageAction.CHALLENGE else 'LOW'),
                    'risk_score': int(round(state.risk_score or 0)),
                    'reason_codes': state.reason_codes,
                    'decision': action
                }
            })
        except Exception:
            pass  # Suppressed for node

        return state

    # ──────────────────────────────────────────────────────────────────
    # Main Execution Entrypoint
    # ──────────────────────────────────────────────────────────────────
    @trace_operation("investigate_transaction_graph")
    async def investigate_transaction(self, transaction_data: Dict) -> Dict:
        """Initialize the state and execute the orchestrator graph."""
        session_id = transaction_data.get('transaction_id') or transaction_data.get('id', str(time.time()))
        
        self.logger.info("Starting Graph-based workflow", transaction_id=session_id)
        
        # 1. Initialize Invocation State (March 2026 Graph pattern)
        state = InvestigationState(
            transaction_id=session_id,
            session_id=session_id,
            transaction=transaction_data
        )
        
        # 2. Execute Graph (Run all connected nodes iteratively)
        final_state = await self._graph.ainvoke(state)
        
        self.logger.info(
            "Graph workflow complete", 
            transaction_id=session_id, 
            decision=final_state.decision,
            risk_score=final_state.risk_score,
            loop_iterations=final_state.reflection_count
        )
        
        return {
            'action': final_state.decision,
            'risk_score': final_state.risk_score,
            'confidence': final_state.confidence,
            'reason_codes': final_state.reason_codes,
            'top_risk_factors': [rf if isinstance(rf, dict) else rf.model_dump() for rf in final_state.top_risk_factors],
            'shap_values': [sv if isinstance(sv, dict) else sv.model_dump() for sv in final_state.shap_values],
            'transaction': transaction_data,
            'transaction_id': session_id,
            'success': True
        }
    
    async def execute(self, input_data: Dict) -> Dict:
        return await self.investigate_transaction(input_data)

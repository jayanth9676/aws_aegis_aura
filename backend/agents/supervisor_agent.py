"""Supervisor Agent — Dynamic Orchestration with Strands SDK GraphBuilder.

Migrated from static asyncio.gather() to a state-based workflow utilizing 
the March 2026 standard `GraphBuilder` with conditional edges.
"""

from typing import Dict, Any
import time

try:
    from strands import GraphBuilder, Agent
    STRANDS_AVAILABLE = True
except (ImportError, Exception):
    STRANDS_AVAILABLE = False
    Agent = None  # type: ignore

    class GraphBuilder:
        """Fallback graph builder using asyncio.gather() when strands SDK unavailable."""
        def __init__(self):
            self._nodes = {}
            self._edges = []
            self._conditional_edges = []
            self._entry = None

        def add_node(self, fn, name):
            self._nodes[name] = fn
            return self

        def add_edge(self, src, dst, condition=None, **kwargs):
            """Accept condition= kwarg used by supervisor_agent (ignored in fallback)."""
            self._edges.append((src, dst, condition))
            return self

        def add_conditional_edges(self, src, condition, mapping, **kwargs):
            self._conditional_edges.append((src, condition, mapping))
            return self

        def set_entry_point(self, name):
            self._entry = name
            return self

        def compile(self):
            return self

        async def ainvoke(self, state):
            import asyncio

            async def _run_node(fn, name):
                try:
                    result = fn(state)
                    if asyncio.iscoroutine(result):
                        result = await result
                    if isinstance(result, dict):
                        for k, v in result.items():
                            if hasattr(state, k):
                                setattr(state, k, v)
                except Exception:
                    pass  # individual node failures are non-fatal

            # Run all non-virtual nodes in registration order
            await asyncio.gather(*[
                _run_node(fn, name)
                for name, fn in self._nodes.items()
                if name not in ("__start__", "__end__")
            ])
            return state



from agents.base_agent import AegisBaseAgent, create_agent, record_investigation_summary, store_memory
from agents.pydantic_models import InvestigationState, TriageAction
from config import AgentConfig, agentcore_config
from utils import trace_operation, get_logger
from agentcore_app import get_aegis_app

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

    async def _invoke_agent(self, agent_id: str, tool_name: str, payload: Dict) -> Dict:
        """Helper to invoke initialized singletons instead of instantiating tools."""
        app = await get_aegis_app()
        agent = app.agents.get(agent_id)
        if agent:
            # Bypass tool registry overhead, directly execute singleton
            return await agent.execute(payload)
        
        # Fallback to tool registry if not in app agents
        return await self.invoke_tool(tool_name, payload)

    def _build_investigation_graph(self):
        """Build the dynamic orchestration Graph using Strands SDK (or asyncio fallback)."""
        if not STRANDS_AVAILABLE:
            # Strands DLL unavailable — return sentinel; investigate_transaction will
            # invoke node functions directly via asyncio.gather().
            return None

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
        builder.add_edge("__start__", "transaction_context")
        builder.add_edge("__start__", "customer_context")
        builder.add_edge("__start__", "payee_context")

        builder.add_edge("__start__", "behavioral_analysis", condition=needs_behavioral_analysis)
        builder.add_edge("__start__", "graph_analysis", condition=needs_graph_analysis)

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
        builder.set_max_node_executions(15)
        builder.set_execution_timeout(10.0)
        builder.reset_on_revisit(True)

        return builder.build()

    # ──────────────────────────────────────────────────────────────────
    # Node Implementation Wrappers (Adapter layer for the graph)
    # ──────────────────────────────────────────────────────────────────
    async def _node_transaction_context(self, state: InvestigationState) -> InvestigationState:
        res = await self._invoke_agent("transaction_context", "TransactionContextAgent", {'transaction': state.transaction, 'session_id': state.session_id})
        state.transaction_context = res
        return state

    async def _node_customer_context(self, state: InvestigationState) -> InvestigationState:
        res = await self._invoke_agent("customer_context", "CustomerContextAgent", {'customer_id': state.transaction.get('customer_id'), 'session_id': state.session_id})
        state.customer_context = res
        return state

    async def _node_payee_context(self, state: InvestigationState) -> InvestigationState:
        res = await self._invoke_agent("payee_context", "PayeeContextAgent", {
            'payee_account': state.transaction.get('payee_account'),
            'payee_name': state.transaction.get('payee_name'),
            'session_id': state.session_id
        })
        state.payee_context = res
        return state

    async def _node_behavioral_analysis(self, state: InvestigationState) -> InvestigationState:
        res = await self._invoke_agent("behavioral_analysis", "BehavioralAnalysisAgent", {
            'session_data': state.transaction.get('session_data', {}),
            'device_fingerprint': state.transaction.get('device_fingerprint'),
            'session_id': state.session_id
        })
        state.behavioral_analysis = res
        return state

    async def _node_graph_analysis(self, state: InvestigationState) -> InvestigationState:
        res = await self._invoke_agent("graph_relationship", "GraphRelationshipAgent", {
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
        res = await self._invoke_agent("risk_scoring", "RiskScoringAgent", {
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
        res = await self._invoke_agent("intel", "IntelAgent", {
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
        
        res = await self._invoke_agent("triage", "TriageAgent", {
            'risk_score': state.risk_score,
            'confidence': state.confidence,
            'evidence': evidence,
            'session_id': state.session_id,
            'prior_decision': state.decision,
            'prior_reasoning': state.decision_reasoning
        })
        
        state.decision = res.get("action", TriageAction.ALLOW)
        state.priority = res.get("priority", "MEDIUM")
        state.decision_reasoning = res.get("reasoning", "")
        # Reflection signal from the LLM
        state.needs_revision = res.get("needs_revision", False) 
        
        # Log event trajectory (Event Sourced state)
        if state.session_id:
            import json
            log_data = json.dumps(res, default=str)
            await self.store_memory(f'session:{state.session_id}:triage_log:{state.reflection_count}', log_data, ttl=1200)

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
                    'priority': getattr(state, "priority", None) or ('CRITICAL' if action == TriageAction.BLOCK else ('HIGH' if action == TriageAction.CHALLENGE else 'LOW')),
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
        import asyncio as _asyncio
        session_id = transaction_data.get('transaction_id') or transaction_data.get('id', str(time.time()))

        self.logger.info("Starting Graph-based workflow", transaction_id=session_id)

        # 1. Initialize Invocation State
        state = InvestigationState(
            transaction_id=session_id,
            session_id=session_id,
            transaction=transaction_data
        )

        # 2a. Strands Graph execution (when SDK is available)
        if self._graph is not None:
            final_state = await self._graph.ainvoke(state)
        else:
            # 2b. Asyncio fallback — mirrors the graph execution order
            # Phase 1: context nodes in parallel
            context_tasks = [
                self._node_transaction_context(state),
                self._node_customer_context(state),
                self._node_payee_context(state),
            ]
            if needs_behavioral_analysis(state):
                context_tasks.append(self._node_behavioral_analysis(state))
            if needs_graph_analysis(state):
                context_tasks.append(self._node_graph_analysis(state))
            try:
                await _asyncio.gather(*context_tasks, return_exceptions=True)
            except Exception:
                pass

            # Phase 2: analysis in sequence
            for node_fn in [
                self._node_risk_scoring,
                self._node_intel,
                self._node_triage,
                self._node_post_triage,
            ]:
                try:
                    await node_fn(state)
                except Exception as node_err:
                    self.logger.warning("Node failed in asyncio fallback", node=node_fn.__name__, error=str(node_err))
            final_state = state

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

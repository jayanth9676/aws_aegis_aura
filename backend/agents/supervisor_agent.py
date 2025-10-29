"""Supervisor Agent - Central orchestrator for fraud investigation workflow."""

import asyncio
import time
from typing import Any, Dict, List, Tuple

from agents.base_agent import AegisBaseAgent
from config import AgentConfig, agentcore_config
from utils import trace_operation

class SupervisorAgent(AegisBaseAgent):
    """Central orchestrator managing the entire fraud investigation workflow."""
    
    def __init__(self):
        config = AgentConfig.supervisor_config()
        super().__init__("supervisor_agent", config)
    
    @trace_operation("investigate_transaction")
    async def investigate_transaction(self, transaction_data: Dict) -> Dict:
        """Orchestrate parallel agent investigation for a transaction."""
        
        session_id = transaction_data.get('transaction_id', transaction_data.get('id'))
        
        if session_id:
            await self.store_memory(
                f'session:{session_id}:transaction',
                transaction_data,
                ttl=self.config.session_ttl
            )
        
        self.logger.info(
            "Starting fraud investigation",
            transaction_id=session_id,
            amount=transaction_data.get('amount'),
            customer_id=transaction_data.get('customer_id')
        )
        
        # Step 1: Parallel context agent invocation
        context_results = await self._invoke_context_agents(transaction_data, session_id)
        
        # Step 2: Analysis agents
        analysis_results = await self._invoke_analysis_agents(
            context_results,
            transaction_data,
            session_id
        )
        
        # Step 3: Triage decision
        decision = await self._invoke_triage_agent(
            analysis_results,
            context_results,
            transaction_data,
            session_id
        )
        
        # Store complete investigation in memory and session logs
        investigation_summary = {
            'transaction_id': session_id,
            'context_results': context_results,
            'analysis_results': analysis_results,
            'decision': decision,
            'timestamp': transaction_data.get('timestamp')
        }

        await self.record_investigation_summary(session_id, investigation_summary)
        
        self.logger.info(
            "Investigation completed",
            transaction_id=session_id,
            decision=decision.get('action'),
            risk_score=analysis_results.get('risk_score')
        )
        
        # Return comprehensive investigation results
        decision_payload = {
            **decision,
            'context_results': context_results,
            'analysis_results': analysis_results,
            'risk_score': analysis_results.get('risk_score', 0),
            'confidence': analysis_results.get('confidence', 0),
            'reason_codes': analysis_results.get('reason_codes', []),
            'shap_values': analysis_results.get('shap_values', []),
            'top_risk_factors': analysis_results.get('top_risk_factors', []),
            'transaction': transaction_data,
            'transaction_id': session_id,
            'success': True
        }

        if session_id:
            await self.store_memory(
                f'session:{session_id}:decision_summary',
                decision_payload,
                ttl=agentcore_config.long_term_ttl
            )

        await self._post_triage_actions(decision_payload, session_id, transaction_data)

        return decision_payload
    
    async def _invoke_context_agents(self, transaction_data: Dict, session_id: str) -> Dict:
        """Invoke all context agents in parallel."""
        
        self.logger.info("Invoking context agents in parallel")
        
        tasks: Dict[str, Tuple[str, Dict[str, Any]]] = {
            'transaction_context': (
                'TransactionContextAgent',
                {'transaction': transaction_data, 'session_id': session_id}
            ),
            'customer_context': (
                'CustomerContextAgent',
                {'customer_id': transaction_data.get('customer_id'), 'session_id': session_id}
            ),
            'payee_context': (
                'PayeeContextAgent',
                {
                    'payee_account': transaction_data.get('payee_account'),
                    'payee_name': transaction_data.get('payee_name'),
                    'session_id': session_id
                }
            ),
            'behavioral_analysis': (
                'BehavioralAnalysisAgent',
                {
                    'session_data': transaction_data.get('session_data', {}),
                    'device_fingerprint': transaction_data.get('device_fingerprint'),
                    'session_id': session_id
                }
            ),
            'graph_analysis': (
                'GraphRelationshipAgent',
                {
                    'sender_account': transaction_data.get('sender_account'),
                    'receiver_account': transaction_data.get('payee_account'),
                    'entities': {
                        'sender_account': transaction_data.get('sender_account'),
                        'receiver_account': transaction_data.get('payee_account')
                    },
                    'session_id': session_id
                }
            )
        }

        results: Dict[str, Dict] = {}
        for name, (tool_name, params) in tasks.items():
            start_time = time.time()
            try:
                results[name] = await asyncio.wait_for(
                    self.invoke_tool(tool_name, params),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                self.logger.warning("Context agent %s timed out", name)
                results[name] = {'error': 'timeout'}
            except Exception as exc:
                self.logger.warning("Context agent %s failed", name, error=str(exc))
                results[name] = {'error': str(exc)}
            finally:
                results[name]['latency_ms'] = (time.time() - start_time) * 1000

        await self.store_memory(
            f'session:{session_id}:context_snapshot',
            results,
            ttl=self.config.session_ttl
        )

        return results
    
    async def _invoke_analysis_agents(
        self,
        context_results: Dict,
        transaction_data: Dict,
        session_id: str
    ) -> Dict:
        """Invoke analysis agents to generate risk scores and intelligence."""
        
        self.logger.info("Invoking analysis agents")
        
        # Parallel analysis
        tasks = {
            'risk_assessment': (
                'RiskScoringAgent',
                {
                    'context_results': context_results,
                    'transaction': transaction_data,
                    'session_id': session_id
                }
            ),
            'intelligence': (
                'IntelAgent',
                {
                    'transaction': transaction_data,
                    'context_results': context_results,
                    'session_id': session_id
                }
            )
        }

        results: Dict[str, Dict] = {}
        for name, (tool, params) in tasks.items():
            try:
                results[name] = await asyncio.wait_for(
                    self.invoke_tool(tool, params),
                    timeout=25.0
                )
            except asyncio.TimeoutError:
                self.logger.warning("Analysis agent %s timed out", name)
                results[name] = {'error': 'timeout'}
            except Exception as exc:
                self.logger.warning("Analysis agent %s failed", name, error=str(exc))
                results[name] = {'error': str(exc)}

        risk_assessment = results.get('risk_assessment', {})
        intelligence = results.get('intelligence', {})
        
        return {
            'risk_score': risk_assessment.get('risk_score', 0),
            'confidence': risk_assessment.get('confidence', 0),
            'top_risk_factors': risk_assessment.get('top_risk_factors', []),
            'shap_values': risk_assessment.get('shap_values', []),
            'reason_codes': risk_assessment.get('reason_codes', []),
            'intelligence': intelligence
        }
    
    async def _invoke_triage_agent(
        self,
        analysis_results: Dict,
        context_results: Dict,
        transaction_data: Dict,
        session_id: str
    ) -> Dict:
        """Invoke triage agent to make final decision."""
        
        self.logger.info(
            "Invoking triage agent",
            risk_score=analysis_results.get('risk_score'),
            confidence=analysis_results.get('confidence')
        )
        
        decision = await self.invoke_tool('TriageAgent', {
            'risk_score': analysis_results.get('risk_score', 0),
            'confidence': analysis_results.get('confidence', 0),
            'session_id': session_id,
            'evidence': {
                'transaction': transaction_data,
                'context_results': context_results,
                'analysis_results': analysis_results
            }
        })
        
        return decision
    
    async def execute(self, input_data: Dict) -> Dict:
        """Execute supervisor agent logic."""
        return await self.investigate_transaction(input_data)

    async def _post_triage_actions(self, decision_payload: Dict, session_id: str, transaction_data: Dict) -> None:
        """Trigger downstream agents based on triage outcome."""

        action = decision_payload.get('action')
        if not action:
            return

        transaction = transaction_data or {}

        case_id = f"CASE-{session_id}"
        try:
            await self.invoke_tool('CaseManagementTool', {
                'action': 'create',
                'case_data': {
                    'case_id': case_id,
                    'transaction_id': transaction.get('transaction_id', session_id),
                    'customer_id': transaction.get('customer_id'),
                    'status': 'ESCALATED' if action in {'BLOCK', 'CHALLENGE'} else 'RESOLVED',
                    'priority': 'CRITICAL' if action == 'BLOCK' else ('HIGH' if action == 'CHALLENGE' else 'LOW'),
                    'risk_score': int(round(decision_payload.get('risk_score', 0) or 0)),
                    'reason_codes': decision_payload.get('reason_codes', []),
                    'decision': action,
                    'transaction': transaction,
                    'context_results': decision_payload.get('context_results'),
                    'analysis_results': decision_payload.get('analysis_results'),
                    'session_id': session_id
                }
            })
        except Exception as exc:  # pragma: no cover
            self.logger.error(
                "Failed to persist case data",
                transaction_id=session_id,
                error=str(exc)
            )

        try:
            if action == 'CHALLENGE':
                await self.invoke_tool('DialogueAgent', {
                    'transaction': transaction,
                    'risk_factors': decision_payload.get('reason_codes', []),
                    'session_id': session_id,
                    'risk_score': decision_payload.get('risk_score'),
                    'analysis_results': decision_payload.get('analysis_results')
                })

            if action in {'BLOCK', 'CHALLENGE'}:
                await self.invoke_tool('InvestigationAgent', {
                    'case_id': case_id,
                    'transaction': transaction,
                    'analysis_results': decision_payload.get('analysis_results'),
                    'context_results': decision_payload.get('context_results'),
                    'session_id': session_id
                })

            await self.invoke_tool('PolicyDecisionAgent', {
                'case_id': case_id,
                'analyst_id': 'system-supervisor',
                'decision': action,
                'risk_score': decision_payload.get('risk_score'),
                'context_results': decision_payload.get('context_results'),
                'analysis_results': decision_payload.get('analysis_results'),
                'session_id': session_id
            })

            if action == 'BLOCK':
                await self.invoke_tool('RegulatoryReportingAgent', {
                    'case_id': case_id,
                    'analyst_decision': action,
                    'transaction': transaction,
                    'context_results': decision_payload.get('context_results'),
                    'analysis_results': decision_payload.get('analysis_results'),
                    'risk_score': decision_payload.get('risk_score'),
                    'session_id': session_id
                })

        except Exception as exc:  # pragma: no cover - downstream errors logged
            self.logger.error(
                "Post-triage orchestration failed",
                transaction_id=session_id,
                action=action,
                error=str(exc)
            )




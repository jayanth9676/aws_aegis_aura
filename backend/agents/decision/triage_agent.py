"""Triage Agent - Policy-driven decision making (Allow/Challenge/Block)."""

from typing import Dict
from agents.base_agent import AegisBaseAgent
from config import AgentConfig, system_config

class TriageAgent(AegisBaseAgent):
    """Makes policy-driven decisions based on risk score and evidence."""
    
    def __init__(self, name: str = "triage_agent", config: AgentConfig = None):
        if config is None:
            config = AgentConfig.triage_config()
        super().__init__(name, config)
    
    async def execute(self, input_data: Dict) -> Dict:
        """Execute triage logic to determine action with AI-assisted decision making."""
        
        risk_score = input_data.get('risk_score', 0)
        confidence = input_data.get('confidence', 0)
        evidence = input_data.get('evidence', {})
        
        transaction = evidence.get('transaction', {})
        transaction_id = transaction.get('transaction_id', transaction.get('id'))
        
        self.logger.info(
            "Triaging transaction with AI assistance",
            transaction_id=transaction_id,
            risk_score=risk_score,
            confidence=confidence
        )
        
        # Clear-cut cases: Use policy thresholds directly
        if risk_score >= system_config.BLOCK_THRESHOLD and confidence >= system_config.HIGH_CONFIDENCE_THRESHOLD:
            # High risk + high confidence = BLOCK
            return await self._block_and_escalate(transaction_id, risk_score, evidence)

        if risk_score < system_config.CHALLENGE_THRESHOLD and confidence >= 0.7:
            # Low risk + decent confidence = ALLOW
            return await self._allow(transaction_id, risk_score, evidence)
        
        # Edge cases: Use AI to make nuanced decision
        else:
            self.logger.info(
                "Using AI for nuanced triage decision",
                transaction_id=transaction_id,
                risk_score=risk_score,
                confidence=confidence
            )
            
            decision_prompt = """Make a triage decision for this transaction based on risk evidence:

Risk Score: {risk_score:.1f}/100
Confidence: {confidence:.2f}

Policy Thresholds:
- Block Threshold: {block_threshold}
- Challenge Threshold: {challenge_threshold}
- High Confidence Threshold: {confidence_threshold}

Evidence Summary:
{evidence_summary}

Based on this evidence, decide whether to:
1. ALLOW - Low risk, proceed with transaction
2. CHALLENGE - Moderate risk, engage customer dialogue for verification
3. BLOCK - High risk, block transaction and escalate to analyst

Consider:
- Risk score vs thresholds
- Confidence level in the assessment
- Presence of CRITICAL risk factors
- Customer vulnerability factors
- Potential for false positives

Return your response as JSON with this structure:
{{
    "decision": "ALLOW" | "CHALLENGE" | "BLOCK",
    "reasoning": "Brief explanation of decision (2-3 sentences)",
    "confidence": 0.85,
    "override_applied": true | false,
    "override_reason": "Explanation if overriding policy threshold"
}}""".format(
                risk_score=risk_score,
                confidence=confidence,
                block_threshold=system_config.BLOCK_THRESHOLD,
                challenge_threshold=system_config.CHALLENGE_THRESHOLD,
                confidence_threshold=system_config.HIGH_CONFIDENCE_THRESHOLD,
                evidence_summary=self._summarize_evidence(evidence)
            )
            
            # Get AI decision
            ai_decision = await self.reason_with_bedrock(
                prompt=decision_prompt,
                context={'risk_score': risk_score, 'evidence': evidence}
            )
            
            # Extract decision
            if not ai_decision.get('fallback') and ai_decision.get('decision'):
                action = ai_decision.get('decision', '').upper()
                reasoning = ai_decision.get('reasoning', '')
                
                self.logger.info(
                    "AI triage decision made",
                    action=action,
                    reasoning=reasoning,
                    transaction_id=transaction_id
                )
                
                # Execute the AI-recommended action
                result = None
                if action == 'BLOCK':
                    result = await self._block_and_escalate(transaction_id, risk_score, evidence, ai_reasoning=reasoning)
                elif action == 'CHALLENGE':
                    result = await self._challenge(transaction_id, risk_score, evidence, ai_reasoning=reasoning)
                else:  # ALLOW
                    result = await self._allow(transaction_id, risk_score, evidence, ai_reasoning=reasoning)

                if transaction_id:
                    await self.record_investigation_summary(transaction_id, {
                        'decision': result,
                        'evidence': evidence,
                        'ai_decision': ai_decision
                    })

                    return result
            else:
                # AI failed, use fallback policy
                self.logger.warning("AI decision failed, using fallback policy")
                if risk_score >= system_config.CHALLENGE_THRESHOLD:
                    return await self._challenge(transaction_id, risk_score, evidence)
                else:
                    return await self._allow(transaction_id, risk_score, evidence)
    
    async def _block_and_escalate(self, transaction_id: str, risk_score: float, evidence: Dict, ai_reasoning: str = None) -> Dict:
        """Block transaction and escalate to analyst."""
        
        self.logger.info(
            "BLOCKING transaction - high fraud risk",
            transaction_id=transaction_id,
            risk_score=risk_score,
            ai_reasoning=ai_reasoning
        )
        
        # Block payment
        await self.invoke_tool('PaymentAPITool', {
            'action': 'block',
            'transaction_id': transaction_id,
            'reason': f'High fraud risk (score: {risk_score})'
        })
        
        # Escalate to analyst
        await self.invoke_tool('EscalationTool', {
            'transaction_id': transaction_id,
            'priority': 'HIGH',
            'risk_score': risk_score,
            'evidence': evidence,
            'action': 'BLOCKED',
            'ai_reasoning': ai_reasoning
        })
        
        return {
            'action': 'BLOCK',
            'risk_score': risk_score,
            'transaction_id': transaction_id,
            'escalated': True,
            'message': 'Transaction blocked due to high fraud risk',
            'ai_reasoning': ai_reasoning,
            'reasoning_source': 'ai' if ai_reasoning else 'policy'
        }
    
    async def _challenge(self, transaction_id: str, risk_score: float, evidence: Dict, ai_reasoning: str = None) -> Dict:
        """Challenge customer with dynamic dialogue."""
        
        self.logger.info(
            "CHALLENGING transaction - moderate risk",
            transaction_id=transaction_id,
            risk_score=risk_score,
            ai_reasoning=ai_reasoning
        )
        
        # Hold payment temporarily
        await self.invoke_tool('PaymentAPITool', {
            'action': 'hold',
            'transaction_id': transaction_id,
            'reason': f'Additional verification required (score: {risk_score})',
            'hold_duration_seconds': 900  # 15 minutes
        })
        
        # Invoke dialogue agent
        dialogue_result = await self.invoke_tool('DialogueAgent', {
            'transaction': evidence.get('transaction', {}),
            'risk_factors': evidence.get('analysis', {}).get('reason_codes', []),
            'risk_score': risk_score,
            'ai_reasoning': ai_reasoning
        })
        
        return {
            'action': 'CHALLENGE',
            'risk_score': risk_score,
            'transaction_id': transaction_id,
            'dialogue_initiated': True,
            'message': dialogue_result.get('message'),
            'dialogue_url': f'/customer/dialogue/{transaction_id}',
            'ai_reasoning': ai_reasoning,
            'reasoning_source': 'ai' if ai_reasoning else 'policy'
        }
    
    async def _allow(self, transaction_id: str, risk_score: float, evidence: Dict, ai_reasoning: str = None) -> Dict:
        """Allow transaction to proceed."""
        
        self.logger.info(
            "ALLOWING transaction - low risk",
            transaction_id=transaction_id,
            risk_score=risk_score,
            ai_reasoning=ai_reasoning
        )
        
        # Allow payment
        await self.invoke_tool('PaymentAPITool', {
            'action': 'allow',
            'transaction_id': transaction_id
        })
        
        return {
            'action': 'ALLOW',
            'risk_score': risk_score,
            'transaction_id': transaction_id,
            'message': 'Transaction approved',
            'ai_reasoning': ai_reasoning,
            'reasoning_source': 'ai' if ai_reasoning else 'policy'
        }
    
    def _summarize_evidence(self, evidence: Dict) -> str:
        """Summarize evidence for AI decision making."""
        if not evidence:
            return "No evidence available"
        
        summary = ""
        
        # Transaction details
        transaction = evidence.get('transaction', {})
        if transaction:
            summary += f"Transaction: £{transaction.get('amount', 0):.2f} to {transaction.get('payee_name', 'Unknown')}\n"
        
        # Risk factors
        analysis = evidence.get('analysis', {})
        if analysis:
            reason_codes = analysis.get('reason_codes', [])
            if reason_codes:
                summary += f"\nRisk Factors ({len(reason_codes)}):\n"
                for code in reason_codes[:5]:  # Top 5
                    summary += f"  - {code}\n"
        
        # Context agent results
        context_results = evidence.get('context_results', {})
        if context_results:
            summary += "\nAgent Assessments:\n"
            for agent, result in context_results.items():
                if isinstance(result, dict):
                    if result.get('ai_assessment'):
                        summary += f"  {agent}: {result.get('ai_assessment')[:100]}...\n"
                    risk_contribution = result.get('risk_score_contribution', 0)
                    if risk_contribution:
                        summary += f"    Risk contribution: {risk_contribution:.1f}\n"
        
        return summary.strip() if summary else "Minimal evidence available"




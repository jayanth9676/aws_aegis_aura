"""Triage Agent - Policy-driven decision making with Reflection Loop."""

import json
from typing import Dict, Any

from agents.base_agent import AegisBaseAgent
from agents.pydantic_models import TriageDecisionOutput, TriageAction
from config import AgentConfig, system_config


class TriageAgent(AegisBaseAgent):
    """Makes policy-driven decisions based on risk score and evidence, with reflection."""
    
    def __init__(self, name: str = "triage_agent", config: AgentConfig = None):
        if config is None:
            config = AgentConfig.triage_config()
        super().__init__(name, config)
    
    async def execute(self, input_data: Dict) -> Dict:
        """Execute triage logic to determine action with AI-assisted decision making via Pydantic."""
        
        risk_score = input_data.get('risk_score', 0)
        confidence = input_data.get('confidence', 0)
        evidence = input_data.get('evidence', {})
        prior_decision = input_data.get('prior_decision')
        
        self.logger.info(
            "Triaging transaction",
            risk_score=risk_score,
            confidence=confidence,
            prior_action=prior_decision
        )
        
        reasoning_prompt = f"""You are the final decision-maker in the Aegis fraud prevention system.
Based on the evidence, determine the final action: ALLOW, CHALLENGE, or BLOCK.
You must also determine an appropriate escalation priority: LOW, MEDIUM, HIGH, or CRITICAL.

Rules:
- Usually BLOCK if risk_score >= {system_config.BLOCK_THRESHOLD}
- Usually CHALLENGE if risk_score >= {system_config.CHALLENGE_THRESHOLD} and < {system_config.BLOCK_THRESHOLD}
- If you disagree with the rule-based thresholds, explain why.

Reflection:
{'Prior to this, a decision of ' + str(prior_decision) + ' was made but questioned. Please reconsider your choice.' if prior_decision else ''}
If you are BLOCKING but the risk is borderline (e.g. 70-85), you may set needs_revision=true to request a reflection loop.

Evidence Summaries:
{json.dumps(self._summarize_evidence(evidence), indent=2)}

Risk Score: {risk_score} (Confidence: {confidence})

Provide your response as structured output conforming to the required schema."""

        # Call Bedrock natively
        try:
            # We use the internal Strands Agent (self._strands_agent) and request structured output
            response_json = await self.reason_with_bedrock(
                prompt=reasoning_prompt,
                context={},
                response_model=TriageDecisionOutput
            )
            
            # Extract data from the assumed Strands structured output
            action_str = response_json.get("action", "ALLOW")
            if hasattr(action_str, "value"): action_str = action_str.value
            if isinstance(action_str, str): action_str = action_str.upper()
            action = TriageAction[action_str] if action_str in ["ALLOW", "CHALLENGE", "BLOCK"] else TriageAction.ALLOW
            
            priority_str = response_json.get("priority", "MEDIUM")
            if hasattr(priority_str, "value"): priority_str = priority_str.value
            if isinstance(priority_str, str): priority_str = priority_str.upper()
            
            return {
                'action': action,
                'priority': priority_str,
                'risk_score': response_json.get("risk_score", risk_score),
                'confidence': response_json.get("confidence", confidence),
                'reasoning': response_json.get("reasoning", "No AI reasoning provided"),
                'reason_codes': response_json.get("reason_codes", []),
                'policy_applied': response_json.get("policy_applied", "AI_HYBRID"),
                'needs_revision': response_json.get("needs_revision", False)
            }
            
        except Exception as e:
            self.logger.warning("AI triage failed. Falling back to simple policy rules.", error=str(e))
            # Fallback logic
            action = TriageAction.ALLOW
            if risk_score >= system_config.BLOCK_THRESHOLD:
                action = TriageAction.BLOCK
            elif risk_score >= system_config.CHALLENGE_THRESHOLD:
                action = TriageAction.CHALLENGE
                
            return {
                'action': action,
                'risk_score': risk_score,
                'confidence': confidence,
                'reasoning': "Rule-based fallback due to AI error.",
                'reason_codes': [],
                'policy_applied': "FAILSAFE_RULES",
                'needs_revision': False
            }

    def _summarize_evidence(self, evidence: Dict) -> Dict:
        """Summarize evidence to avoid token bloat."""
        if not evidence:
            return {}
        
        summary = {
            'top_risk_factors': [],
            'transaction_amount': evidence.get('transaction', {}).get('amount')
        }
        
        # Extract top risk factors across all context agents safely
        top_risk_factors = evidence.get('top_risk_factors', [])
        for factor in top_risk_factors:
            if isinstance(factor, dict):
                summary['top_risk_factors'].append({
                    'factor': factor.get('factor'),
                    'severity': factor.get('severity'),
                    'weight': factor.get('weight')
                })
                
        # Intel summary
        intel = evidence.get('intelligence', {})
        if intel:
            summary['fraud_typology'] = intel.get('fraud_typology')
            
        return summary

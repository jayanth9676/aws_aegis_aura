"""Dialogue Agent - Customer-facing conversational agent with Bedrock Guardrails."""

from typing import Dict
from agents.base_agent import AegisBaseAgent
from config import AgentConfig

class DialogueAgent(AegisBaseAgent):
    """Customer-facing dialogue agent with Bedrock Guardrails for safety."""
    
    def __init__(self, name: str = "dialogue_agent", config: AgentConfig = None):
        if config is None:
            config = AgentConfig.dialogue_config()
        super().__init__(name, config)
    
    async def execute(self, input_data: Dict) -> Dict:
        """Generate contextual customer dialogue with AI and Guardrails."""
        
        transaction = input_data.get('transaction', {})
        risk_factors = input_data.get('risk_factors', [])
        risk_score = input_data.get('risk_score', 0)
        conversation_history = input_data.get('conversation_history', [])
        customer_response = input_data.get('customer_response', '')
        
        self.logger.info(
            "Generating customer dialogue with AI",
            transaction_id=transaction.get('transaction_id'),
            risk_score=risk_score,
            risk_factors_count=len(risk_factors),
            turn_number=len(conversation_history)
        )
        
        # Use AI to generate contextual, adaptive dialogue
        dialogue_prompt = """Generate a customer-facing message for this fraud prevention scenario:

Transaction Context:
{transaction_summary}

Risk Assessment:
- Risk Score: {risk_score:.0f}/100
- Risk Factors: {risk_factors_summary}

Conversation History:
{conversation_history}

Customer's Last Response: "{customer_response}"

Generate a supportive, empathetic message that:
1. Acknowledges the customer's situation
2. Asks targeted verification questions based on the specific risk factors
3. Provides relevant scam awareness education
4. Offers clear next steps (proceed with verification, cancel, or contact us)
5. Is conversational and non-alarmist

Return your response as JSON with this structure:
{{
    "message": "Your conversational message to the customer",
    "questions": ["Specific question 1", "Specific question 2"],
    "education_tip": "Brief scam awareness tip relevant to this situation",
    "recommended_action": "VERIFY" | "CANCEL" | "ESCALATE",
    "tone": "supportive" | "cautious" | "urgent",
    "confidence": 0.85
}}""".format(
            transaction_summary=self._summarize_transaction(transaction),
            risk_score=risk_score,
            risk_factors_summary=self._summarize_risk_factors(risk_factors),
            conversation_history=self._format_conversation_history(conversation_history),
            customer_response=customer_response if customer_response else "N/A (first message)"
        )
        
        # Get AI-generated dialogue with Guardrails applied
        # Guardrails will:
        # - Filter harmful content
        # - Redact PII
        # - Deny off-topic responses
        # - Ensure grounding in evidence
        ai_dialogue = await self.reason_with_bedrock(
            prompt=dialogue_prompt,
            context={'transaction': transaction, 'risk_factors': risk_factors}
        )
        
        # Fallback to template-based response if AI fails
        if ai_dialogue.get('fallback') or not ai_dialogue.get('message'):
            self.logger.warning("AI dialogue failed, using template fallback")
            response_data = self._generate_template_response(transaction, risk_factors, risk_score)
            reasoning_source = 'template'
        else:
            response_data = {
                'message': ai_dialogue.get('message', ''),
                'questions': ai_dialogue.get('questions', []),
                'education_tip': ai_dialogue.get('education_tip', ''),
                'recommended_action': ai_dialogue.get('recommended_action', 'VERIFY'),
                'tone': ai_dialogue.get('tone', 'supportive'),
                'confidence': ai_dialogue.get('confidence', 0.7)
            }
            reasoning_source = 'ai'
        
        self.logger.info(
            "Dialogue generated",
            transaction_id=transaction.get('transaction_id'),
            guardrails_applied=bool(self.guardrails_id),
            reasoning_source=reasoning_source
        )
        
        return {
            **response_data,
            'guardrails_applied': bool(self.guardrails_id),
            'risk_factors_addressed': risk_factors,
            'reasoning_source': reasoning_source
        }
    
    def _build_dialogue_prompt(self, transaction: Dict, risk_factors: list, risk_score: float) -> str:
        """Build contextual prompt for customer dialogue."""
        
        amount = transaction.get('amount', 0)
        payee_name = transaction.get('payee_name', 'the recipient')
        customer_name = transaction.get('customer_name', 'Customer')
        
        # Identify primary risk factors
        primary_risks = []
        
        if 'NEW_PAYEE_HIGH_AMOUNT' in risk_factors:
            primary_risks.append(f"large payment to a new recipient ({payee_name})")
        
        if 'ACTIVE_CALL_DETECTED' in risk_factors:
            primary_risks.append("active phone call during the transaction")
        
        if 'PAYEE_VERIFICATION_MISMATCH' in risk_factors:
            primary_risks.append("payee name mismatch")
        
        if 'VELOCITY_ANOMALY' in risk_factors:
            primary_risks.append("unusual payment pattern")
        
        # Build prompt
        prompt = f"""You are a fraud prevention assistant helping protect {customer_name} from potential scams.

Transaction Details:
- Amount: £{amount:,.2f}
- Recipient: {payee_name}
- Risk Score: {risk_score:.0f}/100

Risk Indicators Detected:
{chr(10).join(f'- {risk}' for risk in primary_risks) if primary_risks else '- General risk indicators'}

Generate a supportive, non-alarming message to the customer that:
1. Explains we've detected risk indicators
2. Asks specific verification questions based on the risk factors
3. Provides helpful fraud awareness tips
4. Offers a safe way to cancel or proceed

Be empathetic, clear, and focus on customer protection. Do NOT provide financial or legal advice.
"""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for dialogue agent."""
        return """You are Aegis Fraud Protection Assistant. Your role is to:
- Protect customers from APP (Authorized Push Payment) fraud
- Ask targeted questions to verify transaction legitimacy
- Educate customers about scam tactics
- Provide a supportive, non-judgmental experience
- NEVER provide financial or legal advice
- NEVER be alarmist or create panic
- ALWAYS be respectful of customer intelligence
- ALWAYS provide clear options to proceed or cancel

If a customer insists on proceeding despite warnings, respect their decision while documenting their choice."""
    
    def _summarize_transaction(self, transaction: Dict) -> str:
        """Summarize transaction for AI prompt."""
        amount = transaction.get('amount', 0)
        payee = transaction.get('payee_name', 'Unknown recipient')
        account = transaction.get('payee_account', 'Unknown account')
        
        return f"""
- Amount: £{amount:,.2f}
- Recipient: {payee}
- Account: {account}
- Transaction ID: {transaction.get('transaction_id', 'N/A')}
"""
    
    def _summarize_risk_factors(self, risk_factors: list) -> str:
        """Summarize risk factors for AI prompt."""
        if not risk_factors:
            return "No specific risk factors identified"
        
        return "\n".join([f"  - {factor.replace('_', ' ').title()}" for factor in risk_factors[:5]])
    
    def _format_conversation_history(self, conversation_history: list) -> str:
        """Format conversation history for AI prompt."""
        if not conversation_history:
            return "No previous conversation (first interaction)"
        
        formatted = []
        for i, turn in enumerate(conversation_history[-3:], 1):  # Last 3 turns
            role = turn.get('role', 'unknown')
            message = turn.get('message', '')
            formatted.append(f"{i}. {role.upper()}: {message}")
        
        return "\n".join(formatted) if formatted else "No previous conversation"
    
    def _generate_template_response(self, transaction: Dict, risk_factors: list, risk_score: float) -> Dict:
        """Generate template-based response as fallback."""
        amount = transaction.get('amount', 0)
        payee = transaction.get('payee_name', 'the recipient')
        
        # Determine tone based on risk score
        if risk_score >= 80:
            tone = 'urgent'
            action = 'CANCEL'
            message = f"""We've detected high-risk indicators for your £{amount:,.2f} payment to {payee}.

For your security, we strongly recommend canceling this payment and verifying the recipient through a trusted channel.

Can you confirm:
- Did you initiate this payment yourself?
- Have you verified the recipient's identity independently?
- Are you currently on a phone call with someone instructing you?

If you're unsure, please cancel and contact us directly at 0800-FRAUD-HELP."""

        elif risk_score >= 60:
            tone = 'cautious'
            action = 'VERIFY'
            message = f"""We need to verify your £{amount:,.2f} payment to {payee} for security reasons.

Please answer these verification questions:
- How do you know the recipient?
- Have you made payments to them before?
- Did anyone contact you about this payment?

This helps us protect you from potential fraud."""

        else:
            tone = 'supportive'
            action = 'VERIFY'
            message = f"""We're completing a quick security check for your £{amount:,.2f} payment to {payee}.

This is routine for your protection. Can you confirm this payment is legitimate?"""
        
        return {
            'message': message,
            'questions': [
                "Did you initiate this payment yourself?",
                "How do you know the recipient?"
            ],
            'education_tip': "Fraudsters often impersonate trusted organizations. Always verify through official channels.",
            'recommended_action': action,
            'tone': tone,
            'confidence': 0.6
        }




"""Transaction Context Agent - Transaction analysis and velocity detection."""

from typing import Dict
from agents.base_agent import AegisBaseAgent
from config import AgentConfig

class TransactionContextAgent(AegisBaseAgent):
    """Analyzes transaction history, velocity patterns, and payee verification."""
    
    def __init__(self):
        config = AgentConfig.transaction_context_config()
        super().__init__("transaction_context_agent", config)
    
    async def execute(self, input_data: Dict) -> Dict:
        """Analyze transaction context using AI reasoning."""
        
        transaction = input_data.get('transaction', {})
        session_id = input_data.get('session_id')
        customer_id = transaction.get('customer_id')
        
        self.logger.info(
            "Analyzing transaction context with AI",
            customer_id=customer_id,
            amount=transaction.get('amount')
        )
        
        # Get transaction history
        history = await self.invoke_tool('TransactionAnalysisTool', {
            'customer_id': customer_id,
            'lookback_days': 90
        })
        
        # Velocity analysis
        velocity = await self.invoke_tool('VelocityAnalysisTool', {
            'transaction': transaction,
            'history': history
        })
        
        # Verification of Payee (CoP)
        cop_result = await self.invoke_tool('VerificationOfPayeeTool', {
            'payee_account': transaction.get('payee_account'),
            'payee_name': transaction.get('payee_name'),
            'sort_code': transaction.get('sort_code')
        })
        
        # Use AI to analyze transaction context
        analysis_prompt = """Analyze this transaction context for fraud risk factors:

Transaction Details:
- Amount: {amount}
- Payee: {payee_name}
- Payee Account: {payee_account}

Transaction History (last 90 days):
{history_summary}

Velocity Analysis:
{velocity_summary}

Confirmation of Payee (CoP) Result:
{cop_summary}

Based on this evidence, identify all fraud risk factors. For each risk factor:
1. Name the risk factor (e.g., "PAYEE_VERIFICATION_MISMATCH", "VELOCITY_ANOMALY")
2. Assign a severity level: LOW, MEDIUM, HIGH, or CRITICAL
3. Assign a numerical weight (0-200 points)
4. Provide a brief explanation

Return your response as JSON with this structure:
{{
    "risk_factors": [
        {{
            "factor": "RISK_FACTOR_NAME",
            "severity": "HIGH",
            "weight": 180,
            "details": "Explanation of why this is a risk"
        }}
    ],
    "overall_assessment": "Brief summary of transaction risk",
    "confidence": 0.85
}}""".format(
            amount=transaction.get('amount', 0),
            payee_name=transaction.get('payee_name', 'Unknown'),
            payee_account=transaction.get('payee_account', 'Unknown'),
            history_summary=self._summarize_history(history),
            velocity_summary=self._summarize_velocity(velocity),
            cop_summary=self._summarize_cop(cop_result)
        )
        
        # Get AI analysis
        ai_analysis = await self.reason_with_bedrock(
            prompt=analysis_prompt,
            context={'transaction': transaction, 'history': history, 'velocity': velocity, 'cop': cop_result}
        )
        
        # Extract risk factors from AI response
        risk_factors = ai_analysis.get('risk_factors', [])
        
        # Fallback to rule-based if AI fails
        if not risk_factors or ai_analysis.get('fallback'):
            self.logger.warning("AI analysis failed, using rule-based fallback")
            risk_factors = self._assess_risk(history, velocity, cop_result, transaction)
            overall_assessment = "Rule-based analysis (AI unavailable)"
            confidence = 0.5
        else:
            overall_assessment = ai_analysis.get('overall_assessment', '')
            confidence = ai_analysis.get('confidence', 0.7)
        
        result = {
            'agent': 'transaction_context',
            'risk_factors': risk_factors,
            'evidence': {
                'history': history,
                'velocity': velocity,
                'cop_result': cop_result
            },
            'risk_score_contribution': sum(rf.get('weight', 0) for rf in risk_factors),
            'ai_assessment': overall_assessment,
            'confidence': confidence,
            'reasoning_source': 'ai' if not ai_analysis.get('fallback') else 'rules'
        }

        if session_id:
            await self.store_memory(
                f'session:{session_id}:transaction_context',
                result,
                ttl=self.config.session_ttl
            )

        return result
    
    def _assess_risk(self, history: Dict, velocity: Dict, cop: Dict, transaction: Dict) -> list:
        """Assess transaction risk factors."""
        risk_factors = []
        
        # CoP mismatch
        if cop.get('match_status') not in ['MATCH', 'CLOSE_MATCH']:
            risk_factors.append({
                'factor': 'PAYEE_VERIFICATION_MISMATCH',
                'severity': 'HIGH',
                'weight': 200,
                'details': f"CoP status: {cop.get('match_status')}"
            })
        
        # Velocity anomaly
        if velocity.get('velocity_score', 0) > 0.7:
            risk_factors.append({
                'factor': 'VELOCITY_ANOMALY',
                'severity': 'MEDIUM',
                'weight': 150,
                'details': f"Velocity score: {velocity.get('velocity_score')}"
            })
        
        # New payee with high amount
        if velocity.get('new_payee') and transaction.get('amount', 0) > 1000:
            risk_factors.append({
                'factor': 'NEW_PAYEE_HIGH_AMOUNT',
                'severity': 'HIGH',
                'weight': 180,
                'details': f"New payee, amount: {transaction.get('amount')}"
            })
        
        # Round amount (potential indicator)
        amount = transaction.get('amount', 0)
        if amount > 0 and amount % 100 == 0:
            risk_factors.append({
                'factor': 'ROUND_AMOUNT',
                'severity': 'LOW',
                'weight': 20,
                'details': f"Round amount: {amount}"
            })
        
        return risk_factors
    
    def _summarize_history(self, history: Dict) -> str:
        """Summarize transaction history for AI context."""
        if not history or 'error' in history:
            return "No transaction history available"
        
        transactions = history.get('transactions', [])
        count = history.get('count', len(transactions))
        total_amount = history.get('total_amount', 0)
        
        return f"Total transactions: {count}, Total amount: £{total_amount:,.2f}"
    
    def _summarize_velocity(self, velocity: Dict) -> str:
        """Summarize velocity analysis for AI context."""
        if not velocity or 'error' in velocity:
            return "Velocity analysis unavailable"
        
        velocity_score = velocity.get('velocity_score', 0)
        new_payee = velocity.get('new_payee', False)
        rapid_succession = velocity.get('rapid_succession', False)
        
        return f"Velocity score: {velocity_score:.2f}, New payee: {new_payee}, Rapid succession: {rapid_succession}"
    
    def _summarize_cop(self, cop: Dict) -> str:
        """Summarize CoP verification result for AI context."""
        if not cop or 'error' in cop:
            return "CoP verification unavailable"
        
        match_status = cop.get('match_status', 'UNKNOWN')
        confidence = cop.get('confidence', 0)
        
        return f"Match status: {match_status}, Confidence: {confidence:.2f}"




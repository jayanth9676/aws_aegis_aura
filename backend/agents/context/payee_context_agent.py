"""Payee Context Agent - Payee verification and risk assessment."""

from typing import Dict
from agents.base_agent import AegisBaseAgent
from config import AgentConfig

class PayeeContextAgent(AegisBaseAgent):
    """Analyzes payee risk, verification status, and watchlist hits."""
    
    def __init__(self):
        config = AgentConfig.payee_context_config()
        super().__init__("payee_context_agent", config)
    
    async def execute(self, input_data: Dict) -> Dict:
        """Analyze payee context using AI reasoning."""
        
        payee_account = input_data.get('payee_account')
        payee_name = input_data.get('payee_name')
        session_id = input_data.get('session_id')
        
        self.logger.info(
            "Analyzing payee context with AI",
            payee_account=payee_account,
            payee_name=payee_name
        )
        
        # Confirmation of Payee verification
        cop_result = await self.invoke_tool('VerificationOfPayeeTool', {
            'payee_account': payee_account,
            'payee_name': payee_name,
            'sort_code': input_data.get('sort_code')
        })
        
        # Watchlist screening
        watchlist_result = await self.invoke_tool('WatchlistTool', {
            'entity': payee_account,
            'entity_type': 'account'
        })
        
        # Payee history analysis
        payee_history = await self.invoke_tool('PayeeAnalysisTool', {
            'payee_account': payee_account,
            'lookback_months': 12
        })
        
        # Use AI to analyze payee risk
        analysis_prompt = """Analyze this payee for fraud risk factors:

Payee Information:
- Account: {payee_account}
- Name: {payee_name}

Confirmation of Payee (CoP) Verification:
{cop_summary}

Watchlist Screening:
{watchlist_summary}

Payee Account History:
{history_summary}

Based on this evidence, identify all payee-related fraud risk factors. For each risk factor:
1. Name the risk factor (e.g., "PAYEE_NAME_MISMATCH", "WATCHLIST_HIT", "NEW_PAYEE_ACCOUNT")
2. Assign a severity level: LOW, MEDIUM, HIGH, or CRITICAL
3. Assign a numerical weight (0-300 points, higher for watchlist hits)
4. Provide a brief explanation

Return your response as JSON with this structure:
{{
    "risk_factors": [
        {{
            "factor": "RISK_FACTOR_NAME",
            "severity": "CRITICAL",
            "weight": 250,
            "details": "Explanation of payee risk"
        }}
    ],
    "overall_assessment": "Brief summary of payee risk",
    "confidence": 0.90
}}""".format(
            payee_account=payee_account,
            payee_name=payee_name,
            cop_summary=self._summarize_cop(cop_result),
            watchlist_summary=self._summarize_watchlist(watchlist_result),
            history_summary=self._summarize_payee_history(payee_history)
        )
        
        # Get AI analysis
        ai_analysis = await self.reason_with_bedrock(
            prompt=analysis_prompt,
            context={'cop': cop_result, 'watchlist': watchlist_result, 'history': payee_history}
        )
        
        # Extract risk factors from AI response
        risk_factors = ai_analysis.get('risk_factors', [])
        
        # Fallback to rule-based if AI fails
        if not risk_factors or ai_analysis.get('fallback'):
            self.logger.warning("AI analysis failed, using rule-based fallback")
            risk_factors = self._assess_risk(cop_result, watchlist_result, payee_history)
            overall_assessment = "Rule-based analysis (AI unavailable)"
            confidence = 0.5
        else:
            overall_assessment = ai_analysis.get('overall_assessment', '')
            confidence = ai_analysis.get('confidence', 0.7)
        
        result = {
            'agent': 'payee_context',
            'risk_factors': risk_factors,
            'evidence': {
                'cop_result': cop_result,
                'watchlist': watchlist_result,
                'history': payee_history
            },
            'risk_score_contribution': sum(rf.get('weight', 0) for rf in risk_factors),
            'ai_assessment': overall_assessment,
            'confidence': confidence,
            'reasoning_source': 'ai' if not ai_analysis.get('fallback') else 'rules'
        }

        if session_id:
            await self.store_memory(
                f'session:{session_id}:payee_context',
                result,
                ttl=self.config.session_ttl
            )

        return result
    
    def _assess_risk(self, cop: Dict, watchlist: Dict, history: Dict) -> list:
        """Assess payee-related risk factors."""
        risk_factors = []
        
        # CoP mismatch
        if cop.get('match_status') == 'NO_MATCH':
            risk_factors.append({
                'factor': 'PAYEE_NAME_MISMATCH',
                'severity': 'CRITICAL',
                'weight': 250,
                'details': f"Name mismatch: Expected '{cop.get('verified_name')}'"
            })
        elif cop.get('match_status') == 'CLOSE_MATCH':
            risk_factors.append({
                'factor': 'PAYEE_NAME_CLOSE_MATCH',
                'severity': 'HIGH',
                'weight': 150,
                'details': 'Name similar but not exact match'
            })
        
        # Watchlist hit
        if watchlist.get('hit'):
            risk_factors.append({
                'factor': 'PAYEE_WATCHLIST_HIT',
                'severity': 'CRITICAL',
                'weight': 300,
                'details': f"Watchlist: {watchlist.get('source')}, Risk: {watchlist.get('risk_level')}"
            })
        
        # New payee account
        if history.get('is_new_account'):
            risk_factors.append({
                'factor': 'NEW_PAYEE_ACCOUNT',
                'severity': 'MEDIUM',
                'weight': 80,
                'details': f"Account age: {history.get('account_age_days', 0)} days"
            })
        
        # High volume receiver
        if history.get('incoming_transaction_count', 0) > 100:
            risk_factors.append({
                'factor': 'HIGH_VOLUME_RECEIVER',
                'severity': 'MEDIUM',
                'weight': 90,
                'details': f"Received {history.get('incoming_transaction_count')} transactions in 30 days"
            })
        
        return risk_factors
    
    def _summarize_cop(self, cop: Dict) -> str:
        """Summarize CoP verification result for AI context."""
        if not cop or 'error' in cop:
            return "CoP verification unavailable"
        
        match_status = cop.get('match_status', 'UNKNOWN')
        confidence = cop.get('confidence', 0)
        verified_name = cop.get('verified_name', 'Unknown')
        
        return f"Match status: {match_status}, Verified name: {verified_name}, Confidence: {confidence:.2f}"
    
    def _summarize_watchlist(self, watchlist: Dict) -> str:
        """Summarize watchlist screening result for AI context."""
        if not watchlist or 'error' in watchlist:
            return "Watchlist screening unavailable"
        
        hit = watchlist.get('hit', False)
        if hit:
            source = watchlist.get('source', 'Unknown')
            risk_level = watchlist.get('risk_level', 'Unknown')
            return f"WATCHLIST HIT - Source: {source}, Risk Level: {risk_level}"
        else:
            return "No watchlist hits"
    
    def _summarize_payee_history(self, history: Dict) -> str:
        """Summarize payee account history for AI context."""
        if not history or 'error' in history:
            return "Payee history unavailable"
        
        is_new = history.get('is_new_account', False)
        account_age = history.get('account_age_days', 0)
        tx_count = history.get('incoming_transaction_count', 0)
        total_received = history.get('total_received', 0)
        
        if is_new:
            return f"NEW ACCOUNT - Age: {account_age} days, Received {tx_count} transactions (£{total_received:,.2f})"
        else:
            return f"Established account - Age: {account_age} days, Received {tx_count} transactions (£{total_received:,.2f})"


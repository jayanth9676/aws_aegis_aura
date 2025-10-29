"""Customer Context Agent - Customer profile and vulnerability assessment."""

from typing import Dict
from agents.base_agent import AegisBaseAgent
from config import AgentConfig

class CustomerContextAgent(AegisBaseAgent):
    """Analyzes customer profile, history, and vulnerability factors."""
    
    def __init__(self):
        config = AgentConfig.customer_context_config()
        super().__init__("customer_context_agent", config)
    
    async def execute(self, input_data: Dict) -> Dict:
        """Analyze customer context using AI reasoning."""
        
        customer_id = input_data.get('customer_id')
        session_id = input_data.get('session_id')
        session_id = input_data.get('session_id')
        
        self.logger.info(
            "Analyzing customer context with AI",
            customer_id=customer_id
        )
        
        # Get customer profile
        profile = await self.invoke_tool('CustomerAnalysisTool', {
            'customer_id': customer_id
        })
        
        # Calculate vulnerability score (keep rule-based for now as baseline)
        vulnerability = self._assess_vulnerability(profile)
        
        # Check fraud history
        fraud_history = await self.invoke_tool('FraudHistoryTool', {
            'customer_id': customer_id,
            'lookback_months': 24
        })
        
        # Use AI to analyze customer context
        analysis_prompt = """Analyze this customer profile for fraud vulnerability and risk factors:

Customer Profile:
- Age: {age}
- Account Age: {account_age_days} days
- Digital Literacy: {digital_literacy}
- Financial Stress Indicators: {financial_stress}

Vulnerability Assessment:
{vulnerability_summary}

Fraud History (last 24 months):
{fraud_history_summary}

Transaction Context:
{transaction_context}

Based on this evidence, identify all customer-related fraud risk factors. For each risk factor:
1. Name the risk factor (e.g., "HIGH_CUSTOMER_VULNERABILITY", "PREVIOUS_FRAUD_VICTIM")
2. Assign a severity level: LOW, MEDIUM, HIGH, or CRITICAL
3. Assign a numerical weight (0-200 points)
4. Provide a brief explanation

Return your response as JSON with this structure:
{{
    "risk_factors": [
        {{
            "factor": "RISK_FACTOR_NAME",
            "severity": "HIGH",
            "weight": 150,
            "details": "Explanation of customer-specific risk"
        }}
    ],
    "overall_assessment": "Brief summary of customer vulnerability",
    "confidence": 0.85
}}""".format(
            age=profile.get('age', 'Unknown'),
            account_age_days=profile.get('account_age_days', 0),
            digital_literacy=profile.get('digital_literacy', 'medium'),
            financial_stress=profile.get('financial_stress_indicators', 0),
            vulnerability_summary=self._summarize_vulnerability(vulnerability),
            fraud_history_summary=self._summarize_fraud_history(fraud_history),
            transaction_context=self._summarize_transaction_context(input_data)
        )
        
        # Get AI analysis
        ai_analysis = await self.reason_with_bedrock(
            prompt=analysis_prompt,
            context={'profile': profile, 'vulnerability': vulnerability, 'fraud_history': fraud_history}
        )
        
        # Extract risk factors from AI response
        risk_factors = ai_analysis.get('risk_factors', [])
        
        # Fallback to rule-based if AI fails
        if not risk_factors or ai_analysis.get('fallback'):
            self.logger.warning("AI analysis failed, using rule-based fallback")
            risk_factors = self._assess_risk(profile, vulnerability, fraud_history)
            overall_assessment = "Rule-based analysis (AI unavailable)"
            confidence = 0.5
        else:
            overall_assessment = ai_analysis.get('overall_assessment', '')
            confidence = ai_analysis.get('confidence', 0.7)
        
        result = {
            'agent': 'customer_context',
            'risk_factors': risk_factors,
            'vulnerability_score': vulnerability['score'],
            'evidence': {
                'profile': profile,
                'vulnerability': vulnerability,
                'fraud_history': fraud_history
            },
            'risk_score_contribution': sum(rf.get('weight', 0) for rf in risk_factors),
            'ai_assessment': overall_assessment,
            'confidence': confidence,
            'reasoning_source': 'ai' if not ai_analysis.get('fallback') else 'rules'
        }

        if session_id:
            await self.store_memory(
                f'session:{session_id}:customer_context',
                result,
                ttl=self.config.session_ttl
            )

        return result
    
    def _assess_vulnerability(self, profile: Dict) -> Dict:
        """Assess customer vulnerability based on demographics and behavior."""
        
        score = 0.0
        factors = []
        
        age = profile.get('age', 0)
        
        # Age-based vulnerability
        if age > 70:
            score += 0.3
            factors.append('elderly')
        elif age < 25:
            score += 0.2
            factors.append('young_adult')
        
        # Digital literacy indicators
        if profile.get('digital_literacy', 'medium') == 'low':
            score += 0.25
            factors.append('low_digital_literacy')
        
        # Recent life events
        if profile.get('recent_life_events'):
            score += 0.2
            factors.append('recent_life_changes')
        
        # Financial stress
        if profile.get('financial_stress_indicators', 0) > 2:
            score += 0.15
            factors.append('financial_stress')
        
        return {
            'score': min(score, 1.0),
            'factors': factors
        }
    
    def _assess_risk(self, profile: Dict, vulnerability: Dict, fraud_history: Dict) -> list:
        """Assess customer-related risk factors."""
        risk_factors = []
        
        # Previous fraud victim
        if fraud_history.get('victim_count', 0) > 0:
            risk_factors.append({
                'factor': 'PREVIOUS_FRAUD_VICTIM',
                'severity': 'HIGH',
                'weight': 150,
                'details': f"Victim of {fraud_history.get('victim_count')} previous scams"
            })
        
        # High vulnerability
        if vulnerability['score'] > 0.6:
            risk_factors.append({
                'factor': 'HIGH_CUSTOMER_VULNERABILITY',
                'severity': 'MEDIUM',
                'weight': 100,
                'details': f"Vulnerability factors: {', '.join(vulnerability['factors'])}"
            })
        
        # New customer
        account_age_days = profile.get('account_age_days', 0)
        if account_age_days < 90:
            risk_factors.append({
                'factor': 'NEW_CUSTOMER_ACCOUNT',
                'severity': 'LOW',
                'weight': 50,
                'details': f"Account age: {account_age_days} days"
            })
        
        return risk_factors
    
    def _summarize_vulnerability(self, vulnerability: Dict) -> str:
        """Summarize vulnerability assessment for AI context."""
        if not vulnerability:
            return "No vulnerability assessment available"
        
        score = vulnerability.get('score', 0)
        factors = vulnerability.get('factors', [])
        
        if factors:
            return f"Vulnerability score: {score:.2f}, Factors: {', '.join(factors)}"
        else:
            return f"Vulnerability score: {score:.2f} (low risk)"
    
    def _summarize_fraud_history(self, fraud_history: Dict) -> str:
        """Summarize fraud history for AI context."""
        if not fraud_history or 'error' in fraud_history:
            return "No fraud history available"
        
        victim_count = fraud_history.get('victim_count', 0)
        perpetrator_count = fraud_history.get('perpetrator_count', 0)
        
        if victim_count > 0:
            return f"Previous fraud victim ({victim_count} incidents)"
        elif perpetrator_count > 0:
            return f"Previous fraud alerts ({perpetrator_count} incidents)"
        else:
            return "Clean fraud history"
    
    def _summarize_transaction_context(self, input_data: Dict) -> str:
        """Summarize transaction context from input data."""
        transaction = input_data.get('transaction', {})
        if not transaction:
            return "No transaction context provided"
        
        amount = transaction.get('amount', 0)
        payee = transaction.get('payee_name', 'Unknown')
        
        return f"Transaction: £{amount:,.2f} to {payee}"


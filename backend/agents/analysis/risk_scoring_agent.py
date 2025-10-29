"""Risk Scoring Agent - Synthesizes context and generates final risk score."""

from typing import Dict, List
from agents.base_agent import AegisBaseAgent
from config import AgentConfig

class RiskScoringAgent(AegisBaseAgent):
    """Synthesizes all context agent outputs and generates final risk score with SHAP explanations."""
    
    def __init__(self):
        config = AgentConfig.risk_scoring_config()
        super().__init__("risk_scoring_agent", config)
    
    async def execute(self, input_data: Dict) -> Dict:
        """Generate comprehensive risk score using AI synthesis."""
        
        context_results = input_data.get('context_results', {})
        transaction = input_data.get('transaction', {})
        session_id = input_data.get('session_id')
        
        self.logger.info(
            "Generating risk score with AI synthesis",
            transaction_id=transaction.get('transaction_id')
        )
        
        # Extract features from context
        features = self._extract_features(context_results, transaction)
        
        # Invoke ML fraud detection model
        ml_score = await self.invoke_tool('FraudDetectionTool', {
            'features': features
        })
        
        # Get SHAP explanations
        shap_explanations = await self.invoke_tool('SHAPExplainerTool', {
            'model': 'ensemble',
            'features': features
        })
        
        # Calculate baseline weighted ensemble risk score
        final_risk_score = self._calculate_ensemble_risk_score(
            context_results,
            ml_score
        )
        
        # Use AI to synthesize all evidence and refine risk assessment
        synthesis_prompt = """Synthesize this fraud detection evidence and refine the risk assessment:

Context Agent Results:
{context_summary}

ML Model Prediction:
{ml_summary}

SHAP Feature Importance:
{shap_summary}

Baseline Calculated Risk Score: {baseline_score:.1f}/100

Based on ALL available evidence:
1. Assess if the baseline risk score is accurate or needs adjustment
2. Identify the most critical risk factors
3. Provide a confidence level (0-1) for this assessment
4. Generate 3-5 human-readable reason codes explaining the decision

Return your response as JSON with this structure:
{{
    "adjusted_risk_score": 85.5,
    "adjustment_reasoning": "Brief explanation of any score adjustment",
    "critical_factors": ["Most important risk factor 1", "Most important risk factor 2"],
    "confidence": 0.92,
    "reason_codes": ["REASON_CODE_1", "REASON_CODE_2"],
    "overall_assessment": "Brief summary of fraud risk"
}}""".format(
            context_summary=self._summarize_context_results(context_results),
            ml_summary=self._summarize_ml_score(ml_score),
            shap_summary=self._summarize_shap(shap_explanations),
            baseline_score=final_risk_score
        )
        
        # Get AI synthesis
        ai_synthesis = await self.reason_with_bedrock(
            prompt=synthesis_prompt,
            context={'context': context_results, 'ml': ml_score, 'shap': shap_explanations}
        )
        
        # Use AI-adjusted score if available, otherwise use baseline
        if not ai_synthesis.get('fallback') and ai_synthesis.get('adjusted_risk_score') is not None:
            final_risk_score = min(max(ai_synthesis.get('adjusted_risk_score', final_risk_score), 0), 100)
            reason_codes = ai_synthesis.get('reason_codes', self._generate_reason_codes(context_results, shap_explanations))
            confidence = ai_synthesis.get('confidence', self._calculate_confidence(context_results, ml_score))
            ai_assessment = ai_synthesis.get('overall_assessment', '')
            reasoning_source = 'ai'
        else:
            # Fallback to rule-based
            self.logger.warning("AI synthesis failed, using rule-based risk scoring")
            reason_codes = self._generate_reason_codes(context_results, shap_explanations)
            confidence = self._calculate_confidence(context_results, ml_score)
            ai_assessment = "Rule-based scoring (AI unavailable)"
            reasoning_source = 'rules'
        
        result = {
            'risk_score': final_risk_score,
            'confidence': confidence,
            'top_risk_factors': shap_explanations.get('top_features', []),
            'shap_values': shap_explanations.get('shap_values', []),
            'reason_codes': reason_codes,
            'ml_score': ml_score.get('fraud_probability', 0),
            'context_scores': self._extract_context_scores(context_results),
            'ai_assessment': ai_assessment,
            'reasoning_source': reasoning_source,
            'adjustment_reasoning': ai_synthesis.get('adjustment_reasoning', '') if not ai_synthesis.get('fallback') else ''
        }

        if session_id:
            await self.store_memory(
                f'session:{session_id}:risk_assessment',
                result,
                ttl=self.config.session_ttl
            )

        return result
    
    def _extract_features(self, context_results: Dict, transaction: Dict) -> Dict:
        """Extract features for ML model."""
        
        features = {
            # Transaction features
            'amount': transaction.get('amount', 0),
            'is_round_amount': transaction.get('amount', 0) % 100 == 0,
            'hour': transaction.get('hour', 12),
            'is_weekend': transaction.get('is_weekend', False),
            'is_night': transaction.get('is_night', False),
            
            # Context-derived features
            'velocity_score': context_results.get('transaction_context', {}).get('evidence', {}).get('velocity', {}).get('velocity_score', 0),
            'new_payee': context_results.get('transaction_context', {}).get('evidence', {}).get('velocity', {}).get('new_payee', False),
            'anomaly_score': context_results.get('behavioral_analysis', {}).get('anomaly_score', 0),
            'active_call': context_results.get('behavioral_analysis', {}).get('duress_signals', {}).get('active_call', False),
            'mule_risk_score': context_results.get('graph_analysis', {}).get('mule_risk_score', 0),
            
            # Customer features
            'customer_vulnerability_score': context_results.get('customer_context', {}).get('vulnerability_score', 0),
            'customer_age': context_results.get('customer_context', {}).get('age', 0)
        }
        
        return features
    
    def _calculate_ensemble_risk_score(self, context_results: Dict, ml_score: Dict) -> float:
        """Calculate weighted ensemble risk score."""
        
        # Extract scores from context agents
        transaction_score = sum(
            rf.get('weight', 0)
            for rf in context_results.get('transaction_context', {}).get('risk_factors', [])
        )
        
        behavioral_score = sum(
            rf.get('weight', 0)
            for rf in context_results.get('behavioral_analysis', {}).get('risk_factors', [])
        )
        
        graph_score = context_results.get('graph_analysis', {}).get('mule_risk_score', 0) * 100
        
        # ML model score (0-1) converted to 0-100
        ml_fraud_score = ml_score.get('fraud_probability', 0) * 100
        
        # Weighted ensemble
        weights = {
            'ml_model': 0.4,
            'transaction': 0.25,
            'behavioral': 0.25,
            'graph': 0.1
        }
        
        final_score = (
            weights['ml_model'] * ml_fraud_score +
            weights['transaction'] * min(transaction_score, 100) +
            weights['behavioral'] * min(behavioral_score, 100) +
            weights['graph'] * min(graph_score, 100)
        )
        
        return min(final_score, 100)
    
    def _calculate_confidence(self, context_results: Dict, ml_score: Dict) -> float:
        """Calculate confidence score based on data completeness."""
        
        # Check which agents provided results
        agents_succeeded = sum([
            1 if context_results.get('transaction_context') and not context_results.get('transaction_context', {}).get('error') else 0,
            1 if context_results.get('customer_context') and not context_results.get('customer_context', {}).get('error') else 0,
            1 if context_results.get('behavioral_analysis') and not context_results.get('behavioral_analysis', {}).get('error') else 0,
            1 if context_results.get('graph_analysis') and not context_results.get('graph_analysis', {}).get('error') else 0,
            1 if ml_score and not ml_score.get('error') else 0
        ])
        
        # Confidence based on completeness
        base_confidence = agents_succeeded / 5.0
        
        # Boost confidence if critical signals are present
        has_critical_signals = any([
            context_results.get('behavioral_analysis', {}).get('duress_signals', {}).get('active_call'),
            any(rf.get('severity') == 'CRITICAL' for rf in context_results.get('behavioral_analysis', {}).get('risk_factors', []))
        ])
        
        if has_critical_signals:
            base_confidence = min(base_confidence + 0.2, 1.0)
        
        return base_confidence
    
    def _generate_reason_codes(self, context_results: Dict, shap_explanations: Dict) -> List[str]:
        """Generate human-readable reason codes."""
        
        reason_codes = []
        
        # From context agents
        for agent_name, agent_result in context_results.items():
            if isinstance(agent_result, dict):
                risk_factors = agent_result.get('risk_factors', [])
                for rf in risk_factors:
                    if rf.get('severity') in ['CRITICAL', 'HIGH']:
                        reason_codes.append(rf.get('factor', 'UNKNOWN'))
        
        # From SHAP top features
        top_features = shap_explanations.get('top_features', [])
        for feature in top_features[:3]:
            if feature.get('contribution', 0) > 0.1:
                reason_codes.append(f"HIGH_{feature.get('name', 'FEATURE').upper()}")
        
        return list(set(reason_codes))[:10]  # Deduplicate and limit
    
    def _extract_context_scores(self, context_results: Dict) -> Dict:
        """Extract individual context agent scores."""
        return {
            'transaction': context_results.get('transaction_context', {}).get('risk_score_contribution', 0),
            'customer': context_results.get('customer_context', {}).get('risk_score_contribution', 0),
            'behavioral': context_results.get('behavioral_analysis', {}).get('risk_score_contribution', 0),
            'graph': context_results.get('graph_analysis', {}).get('mule_risk_score', 0)
        }
    
    def _summarize_context_results(self, context_results: Dict) -> str:
        """Summarize all context agent results for AI prompt."""
        if not context_results:
            return "No context data available"
        
        summary = ""
        for agent_name, agent_result in context_results.items():
            if isinstance(agent_result, dict) and not agent_result.get('error'):
                summary += f"\n{agent_name.replace('_', ' ').title()}:\n"
                
                # AI assessment if available
                if agent_result.get('ai_assessment'):
                    summary += f"  Assessment: {agent_result.get('ai_assessment')}\n"
                
                # Risk factors
                risk_factors = agent_result.get('risk_factors', [])
                if risk_factors:
                    summary += f"  Risk Factors ({len(risk_factors)}):\n"
                    for rf in risk_factors[:5]:  # Top 5
                        summary += f"    - {rf.get('factor')} ({rf.get('severity')}): {rf.get('details', '')}\n"
                
                # Risk score contribution
                contribution = agent_result.get('risk_score_contribution', 0)
                summary += f"  Risk Score Contribution: {contribution:.1f}\n"
        
        return summary.strip() if summary else "No context results available"
    
    def _summarize_ml_score(self, ml_score: Dict) -> str:
        """Summarize ML model prediction for AI prompt."""
        if not ml_score or ml_score.get('error'):
            return "ML model prediction unavailable"
        
        fraud_prob = ml_score.get('fraud_probability', 0)
        model_confidence = ml_score.get('confidence', 0)
        
        summary = f"""
- Fraud Probability: {fraud_prob:.2%}
- Model Confidence: {model_confidence:.2%}
- Risk Level: {'CRITICAL' if fraud_prob > 0.8 else 'HIGH' if fraud_prob > 0.6 else 'MEDIUM' if fraud_prob > 0.4 else 'LOW'}
"""
        return summary.strip()
    
    def _summarize_shap(self, shap_explanations: Dict) -> str:
        """Summarize SHAP explanations for AI prompt."""
        if not shap_explanations or shap_explanations.get('error'):
            return "SHAP explanations unavailable"
        
        top_features = shap_explanations.get('top_features', [])
        if not top_features:
            return "No feature importance data available"
        
        summary = "Top Contributing Features:\n"
        for i, feature in enumerate(top_features[:5], 1):
            name = feature.get('name', 'Unknown')
            contribution = feature.get('contribution', 0)
            summary += f"{i}. {name}: {contribution:+.3f}\n"
        
        return summary.strip()




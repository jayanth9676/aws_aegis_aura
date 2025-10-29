"""Policy Decision Agent - Human-in-the-loop decision capture and feedback."""

from typing import Dict
from datetime import datetime
from agents.base_agent import AegisBaseAgent
from config import AgentConfig

class PolicyDecisionAgent(AegisBaseAgent):
    """Captures analyst decisions and feedback for model improvement."""
    
    def __init__(self, name: str = "policy_decision_agent", config: AgentConfig = None):
        if config is None:
            config = AgentConfig.policy_decision_config()
        super().__init__(name, config)
    
    async def execute(self, input_data: Dict) -> Dict:
        """Process analyst decision and capture feedback."""
        
        case_id = input_data.get('case_id')
        analyst_decision = input_data.get('decision')
        analyst_id = input_data.get('analyst_id')
        session_id = input_data.get('session_id')
        
        self.logger.info(
            "Processing analyst decision",
            case_id=case_id,
            decision=analyst_decision,
            analyst_id=analyst_id
        )
        
        # Retrieve original AI decision
        if input_data.get('context_results'):
            case_data = input_data
        else:
            case_data = await self.invoke_tool('CaseManagementTool', {
                'action': 'get',
                'case_id': case_id
            })
        
        ai_decision = case_data.get('action')
        ai_risk_score = case_data.get('risk_score', 0)
        
        # Compare decisions
        agreement = (analyst_decision == ai_decision)
        
        # Capture feedback
        feedback = {
            'case_id': case_id,
            'analyst_id': analyst_id,
            'analyst_decision': analyst_decision,
            'analyst_reasoning': input_data.get('reasoning', ''),
            'ai_decision': ai_decision,
            'ai_risk_score': ai_risk_score,
            'agreement': agreement,
            'timestamp': datetime.utcnow().isoformat(),
            'review_time_seconds': input_data.get('review_time_seconds', 0)
        }
        
        # Store feedback for model retraining
        await self._store_feedback(feedback)
        
        # Update case status
        await self.invoke_tool('CaseManagementTool', {
            'action': 'update',
            'case_id': case_id,
            'updates': {
                'status': 'RESOLVED',
                'analyst_decision': analyst_decision,
                'analyst_id': analyst_id,
                'resolved_at': datetime.utcnow().isoformat()
            }
        })
        
        # If disagreement, use AI to analyze and provide insights
        disagreement_analysis = None
        if not agreement:
            disagreement_analysis = await self._analyze_disagreement(feedback, case_data)
            await self._trigger_model_review(feedback, case_data, disagreement_analysis)
        
        result = {
            'feedback_captured': True,
            'agreement': agreement,
            'case_updated': True,
            'feedback_id': feedback['case_id'],
            'disagreement_analysis': disagreement_analysis
        }

        if session_id:
            await self.store_memory(
                f'session:{session_id}:policy_feedback',
                result,
                ttl=None
            )

        return result
    
    async def _store_feedback(self, feedback: Dict):
        """Store feedback in long-term memory for model retraining."""
        
        # Store in persistent memory
        await self.store_memory(
            f'feedback:{feedback["case_id"]}',
            feedback,
            ttl=None  # Persistent
        )
        
        # Also store in feedback queue for batch processing
        await self.invoke_tool('FeedbackStorageTool', {
            'feedback': feedback
        })
    
    async def _analyze_disagreement(self, feedback: Dict, case_data: Dict) -> Dict:
        """Use AI to analyze why analyst disagreed with AI decision."""
        
        self.logger.info("Analyzing AI-Analyst disagreement with AI", case_id=feedback['case_id'])
        
        analysis_prompt = """Analyze this disagreement between AI recommendation and analyst decision:

AI Recommendation:
- Decision: {ai_decision}
- Risk Score: {ai_risk_score}/100
- Risk Factors: {risk_factors}

Analyst Decision:
- Decision: {analyst_decision}
- Reasoning: {analyst_reasoning}
- Review Time: {review_time} seconds

Case Context:
{case_summary}

Analyze this disagreement and provide insights:

Return your response as JSON with this structure:
{{
    "disagreement_category": "FALSE_POSITIVE" | "FALSE_NEGATIVE" | "POLICY_INTERPRETATION" | "CONTEXTUAL_FACTORS" | "MODEL_LIMITATION",
    "likely_cause": "Brief explanation of why the disagreement occurred",
    "model_improvement_areas": ["Area 1", "Area 2"],
    "policy_recommendations": ["Recommendation 1", "Recommendation 2"],
    "requires_urgent_review": true | false,
    "confidence": 0.85
}}""".format(
            ai_decision=feedback['ai_decision'],
            ai_risk_score=feedback['ai_risk_score'],
            risk_factors=', '.join(case_data.get('reason_codes', [])[:5]),
            analyst_decision=feedback['analyst_decision'],
            analyst_reasoning=feedback.get('analyst_reasoning', 'No reasoning provided'),
            review_time=feedback.get('review_time_seconds', 0),
            case_summary=self._summarize_case(case_data)
        )
        
        ai_analysis = await self.reason_with_bedrock(
            prompt=analysis_prompt,
            context={'feedback': feedback, 'case': case_data}
        )
        
        if not ai_analysis.get('fallback'):
            return {
                'disagreement_category': ai_analysis.get('disagreement_category', 'UNKNOWN'),
                'likely_cause': ai_analysis.get('likely_cause', ''),
                'model_improvement_areas': ai_analysis.get('model_improvement_areas', []),
                'policy_recommendations': ai_analysis.get('policy_recommendations', []),
                'requires_urgent_review': ai_analysis.get('requires_urgent_review', False),
                'confidence': ai_analysis.get('confidence', 0.5)
            }
        else:
            # Fallback to basic categorization
            return {
                'disagreement_category': 'UNKNOWN',
                'likely_cause': 'AI analysis unavailable',
                'model_improvement_areas': ['Requires manual review'],
                'policy_recommendations': ['Review case manually'],
                'requires_urgent_review': feedback['ai_risk_score'] > 80,
                'confidence': 0.3
            }
    
    async def _trigger_model_review(self, feedback: Dict, case_data: Dict, disagreement_analysis: Dict = None):
        """Trigger model review when analyst disagrees with AI."""
        
        self.logger.warning(
            "AI-Analyst disagreement detected",
            case_id=feedback['case_id'],
            ai_decision=feedback['ai_decision'],
            analyst_decision=feedback['analyst_decision'],
            disagreement_category=disagreement_analysis.get('disagreement_category') if disagreement_analysis else None
        )
        
        # Determine priority based on analysis
        priority = 'CRITICAL' if (disagreement_analysis and disagreement_analysis.get('requires_urgent_review')) else (
            'HIGH' if case_data.get('risk_score', 0) > 80 else 'MEDIUM'
        )
        
        # Queue for model team review
        await self.invoke_tool('ModelReviewQueueTool', {
            'feedback': feedback,
            'case_data': case_data,
            'disagreement_analysis': disagreement_analysis,
            'priority': priority
        })
    
    def _summarize_case(self, case_data: Dict) -> str:
        """Summarize case for AI prompt."""
        if not case_data:
            return "No case data available"
        
        return f"""
- Case ID: {case_data.get('case_id', 'N/A')}
- Risk Score: {case_data.get('risk_score', 0)}/100
- Amount: £{case_data.get('transaction', {}).get('amount', 0):,.2f}
- Payee: {case_data.get('transaction', {}).get('payee_name', 'Unknown')}
- Pattern: {case_data.get('pattern_type', 'Unknown')}
- Key Risk Factors: {', '.join(case_data.get('reason_codes', [])[:3])}
"""


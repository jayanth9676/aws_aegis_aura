"""Investigation Agent - Deep-dive analysis and analyst co-pilot."""

from typing import Dict
from agents.base_agent import AegisBaseAgent
from config import AgentConfig

class InvestigationAgent(AegisBaseAgent):
    """Provides deep-dive investigation support for analysts with AI co-pilot capabilities."""
    
    def __init__(self, name: str = "investigation_agent", config: AgentConfig = None):
        if config is None:
            config = AgentConfig.investigation_config()
        super().__init__(name, config)
    
    async def execute(self, input_data: Dict) -> Dict:
        """Execute investigation analysis or respond to analyst query."""
        
        query_type = input_data.get('query_type', 'analysis')
        
        if query_type == 'copilot':
            return await self._handle_copilot_query(input_data)
        else:
            return await self._perform_investigation(input_data)
    
    async def _perform_investigation(self, input_data: Dict) -> Dict:
        """Perform comprehensive investigation analysis with AI insights."""
        
        case_id = input_data.get('case_id')
        session_id = input_data.get('session_id')
        
        self.logger.info("Performing deep investigation with AI", case_id=case_id)
        
        # Retrieve full case data
        if input_data.get('transaction') and input_data.get('context_results'):
            case_data = input_data
        else:
            case_data = await self.invoke_tool('CaseManagementTool', {
                'action': 'get',
                'case_id': case_id
            })
        
        # Query knowledge base for similar cases
        similar_cases = await self.query_knowledge_base(
            f"similar fraud cases {case_data.get('pattern_type')}",
            top_k=5
        )
        
        # Build comprehensive timeline
        timeline = await self._build_timeline(case_data)
        
        # Use AI to generate comprehensive investigation insights
        investigation_prompt = """Analyze this fraud case and provide comprehensive investigation insights:

Case Details:
{case_summary}

Timeline of Events:
{timeline_summary}

Similar Historical Cases:
{similar_cases_summary}

Provide a detailed investigation analysis:

Return your response as JSON with this structure:
{{
    "case_assessment": "Comprehensive analysis of the case (3-4 sentences)",
    "fraud_pattern": "Identified fraud pattern type and characteristics",
    "key_evidence": ["Critical evidence item 1", "Critical evidence item 2", "Critical evidence item 3"],
    "investigative_actions": ["Recommended action 1", "Recommended action 2", "Recommended action 3"],
    "regulatory_considerations": "Relevant regulatory requirements (SAR, STR, etc.)",
    "recommended_decision": "APPROVE" | "DECLINE" | "ESCALATE" | "REQUEST_MORE_INFO",
    "confidence": 0.88,
    "priority": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
}}""".format(
            case_summary=self._summarize_case(case_data),
            timeline_summary=self._summarize_timeline(timeline),
            similar_cases_summary=self._summarize_similar_cases(similar_cases)
        )
        
        # Get AI analysis
        ai_analysis = await self.reason_with_bedrock(
            prompt=investigation_prompt,
            context={'case': case_data, 'similar': similar_cases}
        )
        
        # Fallback to rule-based recommendations if AI fails
        if ai_analysis.get('fallback'):
            self.logger.warning("AI investigation failed, using rule-based fallback")
            recommendations = await self._generate_recommendations(case_data, similar_cases)
            reasoning_source = 'rules'
        else:
            recommendations = {
                'case_assessment': ai_analysis.get('case_assessment', ''),
                'fraud_pattern': ai_analysis.get('fraud_pattern', ''),
                'key_evidence': ai_analysis.get('key_evidence', []),
                'investigative_actions': ai_analysis.get('investigative_actions', []),
                'regulatory_considerations': ai_analysis.get('regulatory_considerations', ''),
                'recommended_decision': ai_analysis.get('recommended_decision', 'REQUEST_MORE_INFO'),
                'confidence': ai_analysis.get('confidence', 0.7),
                'priority': ai_analysis.get('priority', 'MEDIUM')
            }
            reasoning_source = 'ai'
        
        result = {
            'case_id': case_id,
            'timeline': timeline,
            'similar_cases': similar_cases,
            'recommendations': recommendations,
            'analysis_complete': True,
            'reasoning_source': reasoning_source
        }

        if session_id:
            await self.store_memory(
                f'session:{session_id}:investigation_recommendations',
                result,
                ttl=self.config.long_term_storage and self.config.session_ttl or None
            )

        return result
    
    async def _handle_copilot_query(self, input_data: Dict) -> Dict:
        """Handle analyst co-pilot conversational query with enhanced AI."""
        
        query = input_data.get('query', '')
        context = input_data.get('context', {})
        case_id = context.get('case_id')
        
        self.logger.info("Handling copilot query with AI", query=query[:100], case_id=case_id)
        
        # If query is about a specific case, retrieve case data
        case_context = ""
        if case_id:
            case_data = await self.invoke_tool('CaseManagementTool', {
                'action': 'get',
                'case_id': case_id
            })
            case_context = f"\nActive Case Context:\n{self._summarize_case(case_data)}"
        
        # Query knowledge base if relevant
        kb_context = ""
        if any(keyword in query.lower() for keyword in ['pattern', 'scam', 'fraud', 'typology', 'procedure', 'regulatory']):
            kb_results = await self.query_knowledge_base(query, top_k=3)
            kb_context = f"\nKnowledge Base References:\n{self._summarize_kb_results(kb_results)}"
        
        # Build enhanced co-pilot prompt
        copilot_prompt = f"""You are an AI co-pilot assisting a fraud analyst with expertise in APP fraud prevention.

Analyst Query: {query}

Dashboard Context:
- Active Cases: {context.get('active_cases', 0)}
- High-Risk Alerts Today: {context.get('recent_alerts', 0)}
- Cases Pending Review: {context.get('pending_cases', 0)}
{case_context}
{kb_context}

Provide a helpful, actionable response. Be specific, reference concrete fraud patterns, and provide next steps when appropriate.

Response:"""
        
        response = await self.invoke_bedrock(
            prompt=copilot_prompt,
            system_prompt="You are an expert fraud analyst AI assistant with deep knowledge of APP fraud, investigation procedures, and regulatory requirements. Be concise, actionable, and always ground your responses in evidence.",
            max_tokens=1000,
            temperature=0.6
        )
        
        return {
            'response': response,
            'query': query,
            'type': 'copilot',
            'case_id': case_id,
            'kb_references': len(kb_context) > 0
        }
    
    async def _build_timeline(self, case_data: Dict) -> list:
        """Build comprehensive event timeline."""
        
        events = []
        
        # Transaction event
        if case_data.get('transaction'):
            events.append({
                'timestamp': case_data['transaction'].get('timestamp'),
                'type': 'transaction',
                'description': f"Transaction initiated: £{case_data['transaction'].get('amount', 0):,.2f}",
                'importance': 'high'
            })
        
        # Risk assessment event
        if case_data.get('created_at'):
            events.append({
                'timestamp': case_data.get('created_at'),
                'type': 'assessment',
                'description': f"AI Risk Assessment: {case_data.get('risk_score', 0)}/100",
                'importance': 'high'
            })
        
        # Sort by timestamp
        events.sort(key=lambda x: x['timestamp'])
        
        return events
    
    async def _generate_recommendations(self, case_data: Dict, similar_cases: list) -> list:
        """Generate investigation recommendations."""
        
        recommendations = []
        
        risk_score = case_data.get('risk_score', 0)
        
        if risk_score > 85:
            recommendations.append({
                'priority': 'URGENT',
                'action': 'Contact customer immediately on verified phone number',
                'rationale': 'High fraud risk detected'
            })
            
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Verify payee independently',
                'rationale': 'Confirm legitimacy of recipient'
            })
        
        # Check for active call indicator
        if 'ACTIVE_CALL_DETECTED' in case_data.get('reason_codes', []):
            recommendations.append({
                'priority': 'CRITICAL',
                'action': 'Potential coaching/duress - prioritize customer safety',
                'rationale': 'Active phone call during transaction is a critical fraud indicator'
            })
        
        return recommendations
    
    def _summarize_case(self, case_data: Dict) -> str:
        """Summarize case data for AI prompt."""
        if not case_data:
            return "No case data available"
        
        summary = f"""
- Case ID: {case_data.get('case_id', 'N/A')}
- Risk Score: {case_data.get('risk_score', 0)}/100
- Status: {case_data.get('status', 'Unknown')}
- Pattern Type: {case_data.get('pattern_type', 'Unknown')}
- Amount: £{case_data.get('transaction', {}).get('amount', 0):,.2f}
- Payee: {case_data.get('transaction', {}).get('payee_name', 'Unknown')}
- Risk Factors: {', '.join(case_data.get('reason_codes', [])[:3])}
"""
        return summary.strip()
    
    def _summarize_timeline(self, timeline: list) -> str:
        """Summarize timeline for AI prompt."""
        if not timeline:
            return "No timeline events available"
        
        summary = []
        for i, event in enumerate(timeline[:5], 1):  # Top 5 events
            summary.append(f"{i}. {event.get('timestamp', 'Unknown')}: {event.get('description', 'N/A')}")
        
        return "\n".join(summary)
    
    def _summarize_similar_cases(self, similar_cases: list) -> str:
        """Summarize similar cases for AI prompt."""
        if not similar_cases:
            return "No similar cases found"
        
        summary = []
        for i, case in enumerate(similar_cases[:3], 1):  # Top 3 similar cases
            content = case.get('content', '')
            summary.append(f"{i}. {content[:200]}...")
        
        return "\n\n".join(summary)
    
    def _summarize_kb_results(self, kb_results: list) -> str:
        """Summarize knowledge base results for AI prompt."""
        if not kb_results:
            return "No knowledge base results"
        
        summary = []
        for i, result in enumerate(kb_results[:3], 1):
            content = result.get('content', '')
            summary.append(f"{i}. {content[:150]}...")
        
        return "\n".join(summary)


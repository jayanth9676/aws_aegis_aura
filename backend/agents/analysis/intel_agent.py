"""Intel Agent - Retrieval-Augmented Generation for fraud intelligence."""

from typing import Dict, List
from agents.base_agent import AegisBaseAgent
from config import AgentConfig

class IntelAgent(AegisBaseAgent):
    """Queries Bedrock Knowledge Base for fraud typologies, SOPs, and regulatory guidance."""
    
    def __init__(self):
        config = AgentConfig.intel_config()
        super().__init__("intel_agent", config)
    
    async def execute(self, input_data: Dict) -> Dict:
        """Retrieve contextual intelligence from Knowledge Base."""
        
        transaction = input_data.get('transaction', {})
        context_results = input_data.get('context_results', {})
        session_id = input_data.get('session_id')
        
        self.logger.info(
            "Querying knowledge base for fraud intelligence",
            transaction_id=transaction.get('transaction_id')
        )
        
        # Identify potential fraud pattern
        pattern_type = self._identify_pattern_type(transaction, context_results)
        
        # Query KB for relevant typologies
        typology_docs = await self.query_knowledge_base(
            f"fraud typology {pattern_type} indicators red flags",
            top_k=3
        )
        
        # Query KB for investigation procedures
        sop_docs = await self.query_knowledge_base(
            f"investigation procedure {pattern_type} scam",
            top_k=2
        )
        
        # Query KB for regulatory guidance
        regulatory_docs = await self.query_knowledge_base(
            f"regulatory requirements suspicious activity reporting {pattern_type}",
            top_k=2
        )
        
        # Synthesize intelligence
        intelligence = await self._synthesize_intelligence(
            pattern_type,
            typology_docs,
            sop_docs,
            regulatory_docs
        )
        
        result = {
            'agent': 'intel',
            'pattern_type': pattern_type,
            'relevant_typologies': [self._extract_key_points(doc) for doc in typology_docs],
            'sop_guidance': [self._extract_key_points(doc) for doc in sop_docs],
            'regulatory_guidance': [self._extract_key_points(doc) for doc in regulatory_docs],
            'intelligence_summary': intelligence
        }

        if session_id:
            await self.store_memory(
                f'session:{session_id}:intelligence',
                result,
                ttl=self.config.session_ttl
            )

        return result
    
    def _identify_pattern_type(self, transaction: Dict, context_results: Dict) -> str:
        """Identify likely fraud pattern type based on evidence."""
        
        # Check for active call (impersonation scam indicator)
        behavioral = context_results.get('behavioral_analysis', {})
        if behavioral.get('duress_signals', {}).get('active_call'):
            return 'impersonation'
        
        # Check for new payee + high amount (romance/investment scam)
        transaction_context = context_results.get('transaction_context', {})
        velocity = transaction_context.get('evidence', {}).get('velocity', {})
        if velocity.get('new_payee') and transaction.get('amount', 0) > 5000:
            return 'romance_or_investment'
        
        # Check for CoP mismatch (invoice redirection)
        cop = transaction_context.get('evidence', {}).get('cop_result', {})
        if cop.get('match_status') in ['NO_MATCH', 'CLOSE_MATCH']:
            return 'invoice_redirection'
        
        # Check for mule network pattern
        graph = context_results.get('graph_analysis', {})
        if graph.get('mule_risk_score', 0) > 0.6:
            return 'money_mule'
        
        # Default to general APP scam
        return 'authorized_push_payment'
    
    def _extract_key_points(self, doc: Dict) -> Dict:
        """Extract key points from retrieved document."""
        return {
            'content': doc.get('content', '')[:500],  # First 500 chars
            'source': doc.get('source', ''),
            'relevance_score': doc.get('score', 0.0)
        }
    
    async def _synthesize_intelligence(
        self,
        pattern_type: str,
        typology_docs: List[Dict],
        sop_docs: List[Dict],
        regulatory_docs: List[Dict]
    ) -> str:
        """Synthesize intelligence summary using Claude."""
        
        # Build context for synthesis
        context = f"""Pattern Type: {pattern_type}

Fraud Typology Information:
{self._format_docs(typology_docs)}

Investigation Procedures:
{self._format_docs(sop_docs)}

Regulatory Guidance:
{self._format_docs(regulatory_docs)}
"""
        
        prompt = f"""Based on the following fraud intelligence, provide a concise summary (2-3 sentences) of:
1. The likely fraud typology
2. Key red flags to watch for
3. Recommended investigative actions

{context}

Summary:"""
        
        try:
            summary = await self.invoke_bedrock(
                prompt=prompt,
                system_prompt="You are a fraud intelligence analyst. Provide concise, actionable intelligence summaries.",
                max_tokens=300,
                temperature=0.3
            )
            return summary
        except Exception as e:
            self.logger.error("Failed to synthesize intelligence", error=str(e))
            return f"Pattern identified: {pattern_type}. Review knowledge base documents for details."
    
    def _format_docs(self, docs: List[Dict]) -> str:
        """Format documents for prompt context."""
        if not docs:
            return "No relevant documents found."
        
        formatted = []
        for i, doc in enumerate(docs, 1):
            formatted.append(f"{i}. {doc.get('content', '')[:300]}...")
        
        return "\n\n".join(formatted)


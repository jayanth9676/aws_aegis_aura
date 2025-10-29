"""Knowledge Base RAG tools for Bedrock KB with intelligent fallbacks."""

from typing import Dict, List
from config import aws_config, system_config
from utils import get_logger

logger = get_logger("tools.knowledge_base")

async def knowledge_base_tool(params: Dict) -> Dict:
    """Query Bedrock Knowledge Base for RAG with mock fallback."""
    
    query = params.get('query')
    top_k = params.get('top_k', 5)
    
    logger.info("Querying knowledge base", query=query[:100], top_k=top_k)
    
    try:
        # Try to query actual Bedrock KB
        if hasattr(system_config, 'KNOWLEDGE_BASE_ID') and system_config.KNOWLEDGE_BASE_ID:
            response = aws_config.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=system_config.KNOWLEDGE_BASE_ID,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': top_k
                    }
                }
            )
            
            documents = [{
                'content': r['content']['text'],
                'source': r.get('location', {}).get('s3Location', {}).get('uri', 'unknown'),
                'score': r.get('score', 0.0),
                'metadata': r.get('metadata', {})
            } for r in response.get('retrievalResults', [])]
            
            logger.info("Knowledge base query completed", results=len(documents))
            
            return {'documents': documents, 'source': 'bedrock_kb'}
        
        else:
            # Fallback to mock knowledge base
            logger.warning("Knowledge Base not configured, using mock responses")
            return _generate_mock_kb_response(query, top_k)
    
    except Exception as e:
        logger.error("Knowledge base query failed", error=str(e))
        # Return mock fallback on error
        return _generate_mock_kb_response(query, top_k)


def _generate_mock_kb_response(query: str, top_k: int = 5) -> Dict:
    """Generate mock KB responses based on query keywords."""
    
    query_lower = query.lower()
    documents = []
    
    # Pattern-based mock responses
    if 'fraud' in query_lower or 'scam' in query_lower:
        documents.append({
            'content': """APP Fraud Typologies: Authorized Push Payment fraud involves social engineering tactics where victims are manipulated into making payments to fraudsters. Common patterns include impersonation scams (bank officials, police), invoice redirection, romance scams, and investment fraud. Key indicators: active phone calls during transactions, new payees, unusual amounts, customer hesitation.""",
            'source': 'mock://fraud_typologies.pdf',
            'score': 0.92
        })
    
    if 'investigation' in query_lower or 'procedure' in query_lower or 'sop' in query_lower:
        documents.append({
            'content': """Investigation Procedures: For suspected APP fraud cases, analysts should: 1) Verify customer contact details through independent channels, 2) Review transaction patterns for velocity anomalies, 3) Check for duress indicators in behavioral data, 4) Investigate payee verification results, 5) Analyze network relationships for mule patterns, 6) Document all evidence thoroughly, 7) Escalate high-risk cases to senior analysts.""",
            'source': 'mock://investigation_sops.pdf',
            'score': 0.88
        })
    
    if 'regulatory' in query_lower or 'sar' in query_lower or 'str' in query_lower:
        documents.append({
            'content': """Regulatory Reporting Requirements: Under UK Money Laundering Regulations 2017 and POCA 2002, firms must submit Suspicious Activity Reports (SARs) to the National Crime Agency within specified timeframes. SARs must include: detailed narrative of suspicious activity, customer and beneficiary details, transaction information, rationale for suspicion, and supporting evidence. Filing deadline: typically 30 days from suspicion.""",
            'source': 'mock://regulatory_requirements.pdf',
            'score': 0.85
        })
    
    if 'mule' in query_lower or 'network' in query_lower:
        documents.append({
            'content': """Money Mule Detection: Money mules are individuals who transfer stolen funds on behalf of fraudsters. Indicators include: rapid money movement through accounts, fan-in/fan-out transaction patterns, circular flows, high transaction velocity, new accounts with unusual activity, intermediary behavior in transaction chains. GNN models can detect complex mule networks.""",
            'source': 'mock://mule_detection_guide.pdf',
            'score': 0.90
        })
    
    if 'impersonation' in query_lower or 'social engineering' in query_lower:
        documents.append({
            'content': """Impersonation Fraud: Fraudsters impersonate trusted entities (banks, police, government, utility companies) to manipulate victims. Red flags: urgency tactics, threats of account closure, requests to move money to 'safe accounts', pressure to act immediately, phone call guidance during transactions. Critical indicator: active phone calls during payment initiation.""",
            'source': 'mock://impersonation_fraud.pdf',
            'score': 0.87
        })
    
    # Always add a general fraud prevention document
    documents.append({
        'content': """General Fraud Prevention: Effective fraud prevention requires layered defenses: real-time transaction monitoring, behavioral biometrics, network analysis, customer education, and human oversight for high-risk cases. False positive rates should be balanced against fraud detection rates. Customer experience is important - avoid unnecessary friction for legitimate transactions.""",
        'source': 'mock://fraud_prevention_best_practices.pdf',
        'score': 0.75
    })
    
    # Return top_k results
    documents = documents[:top_k]
    
    return {
        'documents': documents,
        'source': 'mock_kb',
        'note': 'Mock KB responses - configure KNOWLEDGE_BASE_ID for real Bedrock KB'
    }


async def payee_analysis_tool(params: Dict) -> Dict:
    """Analyze payee history and patterns."""
    
    payee_account = params.get('payee_account')
    lookback_months = params.get('lookback_months', 12)
    
    logger.info("Analyzing payee history", payee_account=payee_account)
    
    try:
        # Query transactions table for this payee
        table = aws_config.dynamodb.Table(system_config.TRANSACTIONS_TABLE)
        from boto3.dynamodb.conditions import Attr
        from datetime import datetime, timedelta
        
        # Calculate lookback date
        lookback_date = (datetime.utcnow() - timedelta(days=lookback_months * 30)).isoformat()
        
        # Scan for transactions to this payee
        response = table.scan(
            FilterExpression=Attr('payee_account').eq(payee_account) & 
                           Attr('timestamp').gte(lookback_date),
            Limit=500
        )
        
        transactions = response.get('Items', [])
        
        # Calculate statistics
        total_amount = sum(float(t.get('amount', 0)) for t in transactions)
        unique_senders = len(set(t.get('sender_account') for t in transactions))
        
        return {
            'payee_account': payee_account,
            'transaction_count': len(transactions),
            'total_amount_received': total_amount,
            'unique_senders': unique_senders,
            'avg_transaction_amount': total_amount / max(len(transactions), 1),
            'lookback_months': lookback_months,
            'first_seen': min((t.get('timestamp') for t in transactions), default=None) if transactions else None,
            'last_seen': max((t.get('timestamp') for t in transactions), default=None) if transactions else None
        }
    
    except Exception as e:
        logger.error("Payee analysis failed", error=str(e))
        return {
            'error': str(e),
            'payee_account': payee_account,
            'transaction_count': 0
        }




"""Graph database tools for network analysis (Neptune simulation via DynamoDB).

March 2026: Updated to use real ML model artifacts (Isolation Forest + XGBoost)
via the `tools.ml_loader.registry` rather than simple rule-based mock matching.
"""

from typing import Dict, List
from datetime import datetime
from strands import tool
from config import aws_config, system_config
from utils import get_logger
from tools.ml_loader import registry

logger = get_logger("tools.graph")

@tool
async def graph_analysis_tool(sender: str, receiver: str, depth: int = 3) -> Dict:
    """Analyze transaction network using DynamoDB (simulating Neptune graph routing).
    
    #Args:
        sender: Sender account identifier
        receiver: Receiver account identifier
        depth: Graph traversal depth
        
    #Returns:
        Graph network features like in_degree, out_degree, circular paths, etc.
    """
    logger.info(
        "Analyzing transaction network from DynamoDB",
        sender=sender,
        receiver=receiver,
        depth=depth
    )
    
    try:
        table = aws_config.dynamodb.Table(system_config.TRANSACTIONS_TABLE)
        from boto3.dynamodb.conditions import Attr
        
        response = table.scan(
            FilterExpression=(
                Attr('sender_account').eq(sender) | 
                Attr('payee_account').eq(receiver) |
                Attr('sender_account').eq(receiver) |
                Attr('payee_account').eq(sender)
            ),
            Limit=1000
        )
        transactions = response.get('Items', [])
        
        features = _calculate_network_features(transactions, sender, receiver)
        
        network = {
            'sender': sender,
            'receiver': receiver,
            'path_exists': len(transactions) > 0,
            'depth_analyzed': depth,
            'total_transactions': len(transactions),
            'total_nodes': len(set([t.get('sender_account') for t in transactions] + 
                                   [t.get('payee_account') for t in transactions]))
        }
        
        return {
            'network': network,
            'features': features
        }
    
    except Exception as e:
        logger.error("Graph analysis failed", error=str(e))
        return {
            'error': str(e),
            'network': {'sender': sender, 'receiver': receiver, 'path_exists': False},
            'features': {'out_degree': 0, 'in_degree': 0, 'avg_time_between_transactions': float('inf')}
        }


def _calculate_network_features(transactions: List[Dict], sender: str, receiver: str) -> Dict:
    """Calculate network features from transaction data."""
    if not transactions:
        return {
            'out_degree': 0, 'in_degree': 0, 'avg_time_between_transactions': float('inf'),
            'circular_paths': 0, 'intermediary_count': 0, 'total_nodes': 0, 'total_edges': 0
        }
    
    out_degree = len(set([t.get('payee_account') for t in transactions if t.get('sender_account') == sender]))
    in_degree = len(set([t.get('sender_account') for t in transactions if t.get('payee_account') == receiver]))
    
    timestamps = []
    for t in transactions:
        try:
            ts = datetime.fromisoformat(t.get('timestamp', ''))
            timestamps.append(ts)
        except Exception:
            pass
            
    timestamps.sort()
    if len(timestamps) > 1:
        time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps)-1)]
        avg_time = sum(time_diffs) / len(time_diffs)
    else:
        avg_time = float('inf')
    
    circular = any(t.get('sender_account') == receiver and t.get('payee_account') == sender for t in transactions)
    
    all_accounts = set()
    for t in transactions:
        all_accounts.add(t.get('sender_account'))
        all_accounts.add(t.get('payee_account'))
        
    intermediaries = all_accounts - {sender, receiver}
    
    return {
        'out_degree': out_degree,
        'in_degree': in_degree,
        'avg_time_between_transactions': avg_time,
        'circular_paths': 1 if circular else 0,
        'intermediary_count': len(intermediaries),
        'total_nodes': len(all_accounts),
        'total_edges': len(transactions)
    }


@tool
async def mule_detection_tool(account: str, network_features: Dict) -> Dict:
    """Detect mule account patterns using real GNN/Isolation Forest features via registry.
    
    #Args:
        account: Account identifier
        network_features: Dictionary of network features calculated by graph_analysis_tool
    
    #Returns:
        Mule score probability and predicted network pattern type.
    """
    logger.info("Running real ML mule detection", account=account)
    
    try:
        # Ask registry to predict probability based on isolation forest / xgboost
        result = registry.predict_mule(network_features)
        result["account"] = account
        return result
    except Exception as e:
        logger.error("Mule detection failed", error=str(e))
        return {
            'error': str(e),
            'score': 0.5,
            'pattern': 'unknown',
            'confidence': 0.3,
            'risk_level': 'MEDIUM',
            'account': account
        }

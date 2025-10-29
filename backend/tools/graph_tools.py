"""Graph database tools for network analysis (Neptune simulation via DynamoDB)."""

from typing import Dict, List
from datetime import datetime, timedelta
from config import aws_config, system_config
from utils import get_logger

logger = get_logger("tools.graph")

async def graph_analysis_tool(params: Dict) -> Dict:
    """Analyze transaction network using DynamoDB (simulates Neptune graph)."""
    
    sender = params.get('sender')
    receiver = params.get('receiver')
    depth = params.get('depth', 3)
    
    logger.info(
        "Analyzing transaction network from DynamoDB",
        sender=sender,
        receiver=receiver,
        depth=depth
    )
    
    try:
        # Query DynamoDB transactions table to build network
        table = aws_config.dynamodb.Table(system_config.TRANSACTIONS_TABLE)
        
        # Get transactions involving sender and receiver
        from boto3.dynamodb.conditions import Attr
        
        # Scan for relevant transactions (in production, would use Neptune)
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
        
        # Calculate network features
        features = _calculate_network_features(transactions, sender, receiver)
        
        # Build network structure
        network = {
            'sender': sender,
            'receiver': receiver,
            'path_exists': len(transactions) > 0,
            'depth_analyzed': depth,
            'total_transactions': len(transactions),
            'total_nodes': len(set([t.get('sender_account') for t in transactions] + 
                                   [t.get('payee_account') for t in transactions]))
        }
        
        logger.info(
            "Network analysis complete",
            nodes=network['total_nodes'],
            transactions=len(transactions)
        )
        
        return {
            'network': network,
            'features': features
        }
    
    except Exception as e:
        logger.error("Graph analysis failed", error=str(e))
        # Return safe defaults
        return {
            'error': str(e),
            'network': {
                'sender': sender,
                'receiver': receiver,
                'path_exists': False,
                'depth_analyzed': 0,
                'total_transactions': 0,
                'total_nodes': 0
            },
            'features': {
                'out_degree': 0,
                'in_degree': 0,
                'avg_time_between_transactions': float('inf'),
                'circular_paths': 0,
                'intermediary_count': 0,
                'total_nodes': 0,
                'total_edges': 0
            }
        }


def _calculate_network_features(transactions: List[Dict], sender: str, receiver: str) -> Dict:
    """Calculate network features from transaction data."""
    
    if not transactions:
        return {
            'out_degree': 0,
            'in_degree': 0,
            'avg_time_between_transactions': float('inf'),
            'circular_paths': 0,
            'intermediary_count': 0,
            'total_nodes': 0,
            'total_edges': len(transactions)
        }
    
    # Calculate out-degree (unique recipients from sender)
    out_degree = len(set([t.get('payee_account') for t in transactions 
                         if t.get('sender_account') == sender]))
    
    # Calculate in-degree (unique senders to receiver)
    in_degree = len(set([t.get('sender_account') for t in transactions 
                        if t.get('payee_account') == receiver]))
    
    # Calculate time between transactions
    timestamps = []
    for t in transactions:
        try:
            ts = datetime.fromisoformat(t.get('timestamp', ''))
            timestamps.append(ts)
        except:
            pass
    
    timestamps.sort()
    
    if len(timestamps) > 1:
        time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                     for i in range(len(timestamps)-1)]
        avg_time = sum(time_diffs) / len(time_diffs)
    else:
        avg_time = float('inf')
    
    # Detect circular paths (simplified: if sender also receives from receiver)
    circular = any(t.get('sender_account') == receiver and t.get('payee_account') == sender 
                  for t in transactions)
    circular_paths = 1 if circular else 0
    
    # Count unique intermediaries
    all_accounts = set()
    for t in transactions:
        all_accounts.add(t.get('sender_account'))
        all_accounts.add(t.get('payee_account'))
    
    # Intermediaries are accounts that are not sender or receiver
    intermediaries = all_accounts - {sender, receiver}
    
    return {
        'out_degree': out_degree,
        'in_degree': in_degree,
        'avg_time_between_transactions': avg_time,
        'circular_paths': circular_paths,
        'intermediary_count': len(intermediaries),
        'total_nodes': len(all_accounts),
        'total_edges': len(transactions)
    }


async def mule_detection_tool(params: Dict) -> Dict:
    """Detect mule account patterns using GNN features (simulated)."""
    
    account = params.get('account')
    network_features = params.get('network_features', {})
    
    logger.info("Running mule detection", account=account)
    
    try:
        # Simulate GNN-based mule detection
        # In production, would call SageMaker endpoint with trained GNN model
        
        # Simple rule-based scoring for now
        score = 0.0
        pattern = 'normal'
        
        # High in-degree + high out-degree = potential mule
        in_deg = network_features.get('in_degree', 0)
        out_deg = network_features.get('out_degree', 0)
        
        if in_deg > 10 and out_deg > 10:
            score = 0.8
            pattern = 'fan_in_fan_out'
        elif out_deg > 15:
            score = 0.7
            pattern = 'fan_out'
        elif in_deg > 15:
            score = 0.75
            pattern = 'fan_in'
        elif network_features.get('circular_paths', 0) > 0:
            score = 0.65
            pattern = 'circular'
        elif network_features.get('avg_time_between_transactions', float('inf')) < 300:
            score = 0.6
            pattern = 'rapid_movement'
        else:
            score = 0.1
            pattern = 'normal'
        
        return {
            'score': score,
            'pattern': pattern,
            'confidence': 0.85,
            'risk_level': 'HIGH' if score > 0.7 else 'MEDIUM' if score > 0.5 else 'LOW',
            'account': account
        }
    
    except Exception as e:
        logger.error("Mule detection failed", error=str(e))
        return {
            'error': str(e),
            'score': 0.5,
            'pattern': 'unknown',
            'confidence': 0.3
        }



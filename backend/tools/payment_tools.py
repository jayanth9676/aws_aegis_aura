"""Payment and transaction analysis tools."""

from typing import Dict
from datetime import datetime, timedelta
from config import aws_config, system_config
from utils import get_logger

logger = get_logger("tools.payment")

async def transaction_analysis_tool(params: Dict) -> Dict:
    """Retrieve and analyze transaction history from DynamoDB."""
    
    customer_id = params.get('customer_id')
    lookback_days = params.get('lookback_days', 90)
    
    logger.info("Analyzing transaction history", customer_id=customer_id)
    
    try:
        # Query DynamoDB for transactions
        table = aws_config.dynamodb.Table(system_config.TRANSACTIONS_TABLE)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Query transactions using customer_id and date range
        # Note: This assumes you have a GSI on customer_id and timestamp
        try:
            from boto3.dynamodb.conditions import Key
            
            response = table.query(
                IndexName='customer-timestamp-index',  # Requires GSI
                KeyConditionExpression=Key('customer_id').eq(customer_id) &
                                      Key('timestamp').between(
                                          start_date.isoformat(),
                                          end_date.isoformat()
                                      ),
                Limit=1000
            )
            
            transactions = response.get('Items', [])
            
        except Exception as query_error:
            # Fallback: Scan with filter (slower but works without GSI)
            logger.warning(f"Query failed, using scan fallback: {query_error}")
            from boto3.dynamodb.conditions import Attr
            
            response = table.scan(
                FilterExpression=Attr('customer_id').eq(customer_id),
                Limit=500
            )
            
            transactions = response.get('Items', [])
            # Filter by date in application layer
            transactions = [
                t for t in transactions
                if start_date.isoformat() <= t.get('timestamp', '') <= end_date.isoformat()
            ]
        
        # Analyze transactions
        total_amount = sum(float(t.get('amount', 0)) for t in transactions)
        payee_accounts = set(t.get('payee_account') for t in transactions if t.get('payee_account'))
        
        analysis = {
            'transactions': transactions,
            'count': len(transactions),
            'total_amount': total_amount,
            'avg_amount': total_amount / max(len(transactions), 1),
            'unique_payees': len(payee_accounts),
            'lookback_days': lookback_days,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }
        
        logger.info(
            "Transaction analysis completed",
            customer_id=customer_id,
            count=len(transactions)
        )
        
        return analysis
    
    except Exception as e:
        logger.error("Transaction analysis failed", error=str(e))
        return {'error': str(e), 'transactions': [], 'count': 0, 'total_amount': 0}


async def payment_api_tool(params: Dict) -> Dict:
    """Hold, block, or allow payment."""
    
    action = params.get('action')  # 'hold', 'block', 'allow'
    transaction_id = params.get('transaction_id')
    reason = params.get('reason', '')
    
    logger.info(
        "Payment action",
        action=action,
        transaction_id=transaction_id
    )
    
    try:
        # Update transaction status in DynamoDB
        table = aws_config.dynamodb.Table(system_config.TRANSACTIONS_TABLE)
        
        table.update_item(
            Key={'transaction_id': transaction_id},
            UpdateExpression='SET #status = :status, #reason = :reason, #updated_at = :updated_at',
            ExpressionAttributeNames={
                '#status': 'status',
                '#reason': 'action_reason',
                '#updated_at': 'updated_at'
            },
            ExpressionAttributeValues={
                ':status': action.upper(),
                ':reason': reason,
                ':updated_at': datetime.now().isoformat()
            }
        )
        
        # Trigger EventBridge event for real-time UI update
        aws_config.eventbridge.put_events(
            Entries=[{
                'Source': 'aegis.payment',
                'DetailType': f'transaction.{action}',
                'Detail': f'{{"transaction_id": "{transaction_id}", "action": "{action}"}}'
            }]
        )
        
        return {
            'status': action,
            'transaction_id': transaction_id,
            'success': True
        }
    
    except Exception as e:
        logger.error("Payment action failed", error=str(e))
        return {'error': str(e), 'success': False}


async def velocity_analysis_tool(params: Dict) -> Dict:
    """Analyze transaction velocity and patterns."""
    
    transaction = params.get('transaction', {})
    history = params.get('history', {})
    
    payee_account = transaction.get('payee_account')
    amount = transaction.get('amount', 0)
    
    logger.info("Analyzing velocity", payee_account=payee_account)
    
    try:
        # Calculate velocity score
        recent_count = history.get('transaction_count', 0)
        avg_amount = history.get('avg_amount', 0)
        
        # Velocity indicators
        is_outlier = amount > (avg_amount * 3) if avg_amount > 0 else False
        new_payee = True  # Would check in history
        
        velocity_score = 0.0
        if is_outlier:
            velocity_score += 0.4
        if new_payee:
            velocity_score += 0.3
        if recent_count > 10:
            velocity_score += 0.2
        
        return {
            'velocity_score': min(velocity_score, 1.0),
            'is_outlier': is_outlier,
            'new_payee': new_payee,
            'recent_transaction_count': recent_count
        }
    
    except Exception as e:
        logger.error("Velocity analysis failed", error=str(e))
        return {'error': str(e)}




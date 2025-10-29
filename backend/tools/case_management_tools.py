"""Case management and escalation tools."""

from typing import Dict
from datetime import datetime
from config import aws_config, system_config
from utils import get_logger

logger = get_logger("tools.case_management")

async def escalation_tool(params: Dict) -> Dict:
    """Escalate case to analyst for review."""
    
    transaction_id = params.get('transaction_id')
    priority = params.get('priority', 'MEDIUM')
    risk_score = params.get('risk_score', 0)
    evidence = params.get('evidence', {})
    action = params.get('action', 'HOLD')
    
    logger.info(
        "Escalating case",
        transaction_id=transaction_id,
        priority=priority
    )
    
    try:
        # Create case in DynamoDB
        table = aws_config.dynamodb.Table(system_config.CASES_TABLE)
        
        case_id = f"CASE-{transaction_id}"
        
        table.put_item(
            Item={
                'case_id': case_id,
                'transaction_id': transaction_id,
                'status': 'ESCALATED',
                'priority': priority,
                'risk_score': int(risk_score),
                'action_taken': action,
                'evidence': str(evidence),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'assigned_to': None
            }
        )
        
        # Trigger notification to analysts (EventBridge)
        aws_config.eventbridge.put_events(
            Entries=[{
                'Source': 'aegis.escalation',
                'DetailType': 'case.escalated',
                'Detail': f'{{"case_id": "{case_id}", "priority": "{priority}"}}'
            }]
        )
        
        return {
            'case_id': case_id,
            'escalated': True,
            'priority': priority
        }
    
    except Exception as e:
        logger.error("Escalation failed", error=str(e))
        return {'error': str(e), 'escalated': False}


async def case_management_tool(params: Dict) -> Dict:
    """Full CRUD operations for case management."""
    
    action = params.get('action')  # 'create', 'update', 'get', 'list'
    case_id = params.get('case_id')
    
    logger.info("Case management action", action=action, case_id=case_id)
    
    try:
        table = aws_config.dynamodb.Table(system_config.CASES_TABLE)
        
        if action == 'create':
            # Create new case
            case_data = params.get('case_data', {})
            case_id = case_data.get('case_id', f"AEGIS-CASE-{datetime.utcnow().timestamp()}")
            
            item = {
                'case_id': case_id,
                'transaction_id': case_data.get('transaction_id'),
                'customer_id': case_data.get('customer_id'),
                'status': case_data.get('status', 'OPEN'),
                'priority': case_data.get('priority', 'MEDIUM'),
                'risk_score': case_data.get('risk_score', 0),
                'reason_codes': case_data.get('reason_codes', []),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'assigned_to': case_data.get('assigned_to'),
                'transaction': case_data.get('transaction', {}),
                'context_results': case_data.get('context_results', {}),
                'pattern_type': case_data.get('pattern_type', 'unknown')
            }
            
            table.put_item(Item=item)
            
            logger.info(f"Case created: {case_id}")
            return {'success': True, 'case_id': case_id, 'created': True}
        
        elif action == 'get' and case_id:
            # Get specific case
            response = table.get_item(Key={'case_id': case_id})
            item = response.get('Item')
            
            if item:
                return item
            else:
                return {'error': 'Case not found', 'case_id': case_id}
        
        elif action == 'update' and case_id:
            # Update existing case
            updates = params.get('updates', {})
            
            if not updates:
                return {'error': 'No updates provided'}
            
            # Build update expression
            update_expr = "SET updated_at = :updated_at"
            expr_values = {':updated_at': datetime.utcnow().isoformat()}
            
            for key, value in updates.items():
                if key != 'case_id':  # Don't update primary key
                    update_expr += f", {key} = :{key}"
                    expr_values[f':{key}'] = value
            
            table.update_item(
                Key={'case_id': case_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
            
            logger.info(f"Case updated: {case_id}", updates=list(updates.keys()))
            return {'success': True, 'case_id': case_id, 'updated': True}
        
        elif action == 'list':
            # List cases with optional filters
            status_filter = params.get('status')
            limit = params.get('limit', 100)
            
            if status_filter:
                # Filter by status using GSI
                from boto3.dynamodb.conditions import Key
                response = table.query(
                    IndexName='status-index',
                    KeyConditionExpression=Key('status').eq(status_filter),
                    Limit=limit
                )
            else:
                # Scan all cases (expensive, use with caution)
                response = table.scan(Limit=limit)
            
            cases = response.get('Items', [])
            
            logger.info(f"Listed {len(cases)} cases")
            return {'cases': cases, 'count': len(cases)}
        
        elif action == 'delete' and case_id:
            # Delete case (soft delete by updating status)
            table.update_item(
                Key={'case_id': case_id},
                UpdateExpression="SET #status = :status, updated_at = :updated_at",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'DELETED',
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Case deleted: {case_id}")
            return {'success': True, 'case_id': case_id, 'deleted': True}
        
        else:
            return {'error': 'Invalid action or missing required parameters', 'action': action}
    
    except Exception as e:
        logger.error("Case management failed", error=str(e), action=action)
        return {'error': str(e), 'action': action}


async def feedback_storage_tool(params: Dict) -> Dict:
    """Store analyst feedback for model improvement."""
    
    feedback = params.get('feedback', {})
    
    logger.info("Storing analyst feedback", case_id=feedback.get('case_id'))
    
    try:
        # Store in DynamoDB feedback table
        table = aws_config.dynamodb.Table('aegis-feedback')  # Create this table
        
        feedback_id = f"FEEDBACK-{datetime.utcnow().timestamp()}"
        
        try:
            table.put_item(
                Item={
                    'feedback_id': feedback_id,
                    'case_id': feedback.get('case_id'),
                    'analyst_id': feedback.get('analyst_id'),
                    'analyst_decision': feedback.get('analyst_decision'),
                    'ai_decision': feedback.get('ai_decision'),
                    'agreement': feedback.get('agreement', False),
                    'analyst_reasoning': feedback.get('analyst_reasoning', ''),
                    'timestamp': datetime.utcnow().isoformat(),
                    'review_time_seconds': feedback.get('review_time_seconds', 0)
                }
            )
            
            return {'success': True, 'feedback_id': feedback_id}
        
        except aws_config.dynamodb.meta.client.exceptions.ResourceNotFoundException:
            logger.warning("Feedback table not found, using fallback")
            return {'success': False, 'note': 'Feedback table not available', 'feedback_id': feedback_id}
    
    except Exception as e:
        logger.error("Feedback storage failed", error=str(e))
        return {'error': str(e), 'success': False}


async def model_review_queue_tool(params: Dict) -> Dict:
    """Queue cases for model team review."""
    
    feedback = params.get('feedback', {})
    case_data = params.get('case_data', {})
    priority = params.get('priority', 'MEDIUM')
    
    logger.info("Queuing for model review", case_id=feedback.get('case_id'), priority=priority)
    
    try:
        # Queue in DynamoDB
        table = aws_config.dynamodb.Table('aegis-model-review-queue')
        
        queue_id = f"REVIEW-{datetime.utcnow().timestamp()}"
        
        try:
            table.put_item(
                Item={
                    'queue_id': queue_id,
                    'case_id': feedback.get('case_id'),
                    'priority': priority,
                    'feedback': feedback,
                    'case_summary': {
                        'risk_score': case_data.get('risk_score', 0),
                        'pattern_type': case_data.get('pattern_type', 'unknown')
                    },
                    'status': 'PENDING',
                    'created_at': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Queued for review: {queue_id}")
            return {'success': True, 'queue_id': queue_id, 'priority': priority}
        
        except aws_config.dynamodb.meta.client.exceptions.ResourceNotFoundException:
            logger.warning("Review queue table not found, using fallback")
            return {'success': False, 'note': 'Review queue not available'}
    
    except Exception as e:
        logger.error("Model review queue failed", error=str(e))
        return {'error': str(e), 'success': False}




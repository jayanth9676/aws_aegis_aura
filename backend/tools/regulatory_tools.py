"""Regulatory compliance and SAR filing tools."""

from typing import Dict
from datetime import datetime
from config import aws_config, system_config
from utils import get_logger

logger = get_logger("tools.regulatory")

async def sar_storage_tool(params: Dict) -> Dict:
    """Store Suspicious Activity Report for regulatory filing."""
    
    sar_document = params.get('sar_document', {})
    
    logger.info("Storing SAR document", sar_id=sar_document.get('sar_id'))
    
    try:
        # Store SAR in DynamoDB
        table = aws_config.dynamodb.Table('aegis-sars')
        
        sar_id = sar_document.get('sar_id', f"SAR-{datetime.utcnow().timestamp()}")
        
        try:
            # Prepare item for storage
            item = {
                'sar_id': sar_id,
                'case_id': sar_document.get('case_id'),
                'report_date': sar_document.get('report_date', datetime.utcnow().isoformat()),
                'institution': sar_document.get('institution', 'Aegis Bank'),
                'narrative': sar_document.get('narrative', ''),
                'subject': sar_document.get('subject', {}),
                'suspicious_activity': sar_document.get('suspicious_activity', {}),
                'reason_codes': sar_document.get('reason_codes', []),
                'analyst_id': sar_document.get('analyst_id'),
                'status': sar_document.get('status', 'DRAFT'),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            table.put_item(Item=item)
            
            logger.info(f"SAR stored successfully: {sar_id}")
            
            return {
                'success': True,
                'sar_id': sar_id,
                'status': item['status']
            }
        
        except aws_config.dynamodb.meta.client.exceptions.ResourceNotFoundException:
            logger.warning("SAR table not found, using fallback storage")
            # Fallback: Store in S3
            return await _store_sar_in_s3(sar_id, sar_document)
    
    except Exception as e:
        logger.error("SAR storage failed", error=str(e))
        return {
            'error': str(e),
            'success': False,
            'sar_id': sar_document.get('sar_id')
        }


async def _store_sar_in_s3(sar_id: str, sar_document: Dict) -> Dict:
    """Fallback: Store SAR in S3 if DynamoDB table doesn't exist."""
    
    try:
        import json
        
        # Store in S3 bucket
        bucket = 'aegis-sars'  # Would be configured
        key = f"sars/{sar_id}.json"
        
        aws_config.s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(sar_document, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"SAR stored in S3: s3://{bucket}/{key}")
        
        return {
            'success': True,
            'sar_id': sar_id,
            'storage': 's3',
            'location': f"s3://{bucket}/{key}"
        }
    
    except Exception as e:
        logger.error("S3 SAR storage failed", error=str(e))
        return {
            'error': str(e),
            'success': False,
            'sar_id': sar_id,
            'fallback_failed': True
        }


async def fraud_history_tool(params: Dict) -> Dict:
    """Retrieve customer's fraud history."""
    
    customer_id = params.get('customer_id')
    lookback_months = params.get('lookback_months', 24)
    
    logger.info("Retrieving fraud history", customer_id=customer_id)
    
    try:
        # Query cases table for this customer
        table = aws_config.dynamodb.Table(system_config.CASES_TABLE)
        from boto3.dynamodb.conditions import Key
        from datetime import datetime, timedelta
        
        # Calculate lookback date
        lookback_date = (datetime.utcnow() - timedelta(days=lookback_months * 30)).isoformat()
        
        try:
            # Query using customer-cases-index GSI
            response = table.query(
                IndexName='customer-cases-index',
                KeyConditionExpression=Key('customer_id').eq(customer_id),
                FilterExpression='created_at >= :lookback',
                ExpressionAttributeValues={':lookback': lookback_date},
                Limit=100
            )
            
            cases = response.get('Items', [])
            
        except:
            # Fallback: Scan (slower)
            from boto3.dynamodb.conditions import Attr
            response = table.scan(
                FilterExpression=Attr('customer_id').eq(customer_id) & 
                               Attr('created_at').gte(lookback_date),
                Limit=100
            )
            cases = response.get('Items', [])
        
        # Calculate fraud statistics
        total_cases = len(cases)
        confirmed_fraud = len([c for c in cases if c.get('status') in ['FRAUD_CONFIRMED', 'BLOCKED']])
        victim_count = len([c for c in cases if c.get('action') in ['BLOCK', 'CHALLENGE']])
        
        return {
            'customer_id': customer_id,
            'total_cases': total_cases,
            'confirmed_fraud_cases': confirmed_fraud,
            'victim_incidents': victim_count,
            'cases': cases[:10],  # Return latest 10
            'lookback_months': lookback_months,
            'has_fraud_history': total_cases > 0
        }
    
    except Exception as e:
        logger.error("Fraud history retrieval failed", error=str(e))
        return {
            'error': str(e),
            'customer_id': customer_id,
            'total_cases': 0,
            'has_fraud_history': False
        }


async def velocity_analysis_tool(params: Dict) -> Dict:
    """Analyze transaction velocity for anomalies."""
    
    transaction = params.get('transaction', {})
    history = params.get('history', {})
    
    customer_id = transaction.get('customer_id')
    current_amount = float(transaction.get('amount', 0))
    
    logger.info("Analyzing transaction velocity", customer_id=customer_id)
    
    try:
        # Extract history data
        transactions = history.get('transactions', [])
        historical_count = history.get('count', 0)
        historical_avg = history.get('avg_amount', 0)
        historical_total = history.get('total_amount', 0)
        
        # Calculate velocity metrics
        velocity_score = 0.0
        anomaly_indicators = []
        
        # 1. Amount anomaly
        if historical_avg > 0:
            amount_ratio = current_amount / historical_avg
            if amount_ratio > 3.0:
                velocity_score += 0.4
                anomaly_indicators.append('LARGE_AMOUNT_DEVIATION')
            elif amount_ratio > 2.0:
                velocity_score += 0.2
                anomaly_indicators.append('MODERATE_AMOUNT_DEVIATION')
        elif current_amount > 5000:
            # No history but large amount
            velocity_score += 0.3
            anomaly_indicators.append('LARGE_AMOUNT_NO_HISTORY')
        
        # 2. Frequency anomaly (if transactions occurred recently)
        recent_transactions = [t for t in transactions if t.get('timestamp', '')]
        if len(recent_transactions) > 10:
            velocity_score += 0.3
            anomaly_indicators.append('HIGH_FREQUENCY')
        
        # 3. New payee + high amount
        payee_account = transaction.get('payee_account')
        known_payees = set(t.get('payee_account') for t in transactions)
        if payee_account not in known_payees and current_amount > 1000:
            velocity_score += 0.3
            anomaly_indicators.append('NEW_PAYEE_HIGH_AMOUNT')
        
        # Normalize velocity score to [0, 1]
        velocity_score = min(velocity_score, 1.0)
        
        return {
            'velocity_score': velocity_score,
            'anomaly_indicators': anomaly_indicators,
            'historical_avg_amount': historical_avg,
            'current_amount': current_amount,
            'amount_deviation': (current_amount / historical_avg) if historical_avg > 0 else 0,
            'recent_transaction_count': len(recent_transactions),
            'new_payee': payee_account not in known_payees
        }
    
    except Exception as e:
        logger.error("Velocity analysis failed", error=str(e))
        return {
            'error': str(e),
            'velocity_score': 0.5,  # Conservative fallback
            'anomaly_indicators': []
        }





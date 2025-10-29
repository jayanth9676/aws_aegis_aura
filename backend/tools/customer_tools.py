"""Customer data and KYC tools."""

from typing import Dict
from config import aws_config, system_config
from utils import get_logger

logger = get_logger("tools.customer")

async def customer_analysis_tool(params: Dict) -> Dict:
    """Retrieve customer profile and history from DynamoDB."""
    
    customer_id = params.get('customer_id')
    
    logger.info("Analyzing customer profile", customer_id=customer_id)
    
    try:
        # Query DynamoDB for customer data
        table = aws_config.dynamodb.Table(system_config.CUSTOMERS_TABLE)
        
        try:
            response = table.get_item(Key={'customer_id': customer_id})
            
            if 'Item' not in response:
                logger.warning(f"Customer not found: {customer_id}")
                # Return default profile if customer not found
                return {
                    'customer_id': customer_id,
                    'age': 45,
                    'account_age_days': 365,
                    'digital_literacy': 'medium',
                    'recent_life_events': False,
                    'financial_stress_indicators': 0,
                    'error': 'Customer not found in database'
                }
            
            customer = response['Item']
            
            # Extract and flatten customer data
            from datetime import datetime
            
            account_opened = customer.get('account_information', {}).get('account_opened_date', '')
            account_age_days = 0
            if account_opened:
                try:
                    opened_date = datetime.fromisoformat(account_opened)
                    account_age_days = (datetime.now() - opened_date).days
                except:
                    pass
            
            profile = {
                'customer_id': customer_id,
                'age': customer.get('personal_information', {}).get('age', 45),
                'account_age_days': account_age_days,
                'digital_literacy': customer.get('digital_literacy', 'medium'),
                'recent_life_events': customer.get('recent_life_events', False),
                'financial_stress_indicators': customer.get('financial_stress_indicators', 0),
                'vulnerability_score': customer.get('risk_profile', {}).get('vulnerability_score', 0.1),
                'fraud_history': customer.get('risk_profile', {}).get('fraud_history', False),
                'kyc_status': customer.get('risk_profile', {}).get('kyc_status', 'VERIFIED'),
                'name': customer.get('personal_information', {}).get('name_full', 'Unknown'),
                'account_type': customer.get('account_information', {}).get('account_type', 'CURRENT')
            }
            
            logger.info(
                "Customer profile retrieved",
                customer_id=customer_id,
                age=profile['age'],
                account_age_days=account_age_days
            )
            
            return profile
        
        except Exception as query_error:
            logger.error(f"DynamoDB query failed: {query_error}")
            # Fallback to mock profile
            return {
                'customer_id': customer_id,
                'age': 45,
                'account_age_days': 365,
                'digital_literacy': 'medium',
                'recent_life_events': False,
                'financial_stress_indicators': 0,
                'error': f'Database query failed: {str(query_error)}'
            }
    
    except Exception as e:
        logger.error("Customer analysis failed", error=str(e))
        return {'error': str(e), 'customer_id': customer_id}

async def fraud_history_tool(params: Dict) -> Dict:
    """Check customer's fraud history from transactions and cases."""
    
    customer_id = params.get('customer_id')
    lookback_months = params.get('lookback_months', 24)
    
    logger.info("Checking fraud history", customer_id=customer_id)
    
    try:
        from datetime import datetime, timedelta
        from boto3.dynamodb.conditions import Key, Attr
        
        # Query transactions for fraud indicators
        transactions_table = aws_config.dynamodb.Table(system_config.TRANSACTIONS_TABLE)
        cases_table = aws_config.dynamodb.Table(system_config.CASES_TABLE)
        
        # Calculate lookback date
        lookback_date = (datetime.now() - timedelta(days=lookback_months * 30)).isoformat()
        
        # Query transactions marked as fraud
        try:
            tx_response = transactions_table.query(
                IndexName='customer-timestamp-index',
                KeyConditionExpression=Key('customer_id').eq(customer_id) &
                                      Key('timestamp').gte(lookback_date),
                FilterExpression=Attr('is_fraud').eq(True),
                Limit=100
            )
            
            fraud_transactions = tx_response.get('Items', [])
            
        except Exception as tx_error:
            logger.warning(f"Transaction query failed, using scan: {tx_error}")
            # Fallback to scan
            tx_response = transactions_table.scan(
                FilterExpression=Attr('customer_id').eq(customer_id) & 
                                Attr('is_fraud').eq(True),
                Limit=50
            )
            fraud_transactions = tx_response.get('Items', [])
        
        # Query cases for this customer
        try:
            case_response = cases_table.query(
                IndexName='customer-cases-index',
                KeyConditionExpression=Key('customer_id').eq(customer_id) &
                                      Key('created_date').gte(lookback_date),
                Limit=100
            )
            
            customer_cases = case_response.get('Items', [])
            
        except Exception as case_error:
            logger.warning(f"Cases query failed, using scan: {case_error}")
            case_response = cases_table.scan(
                FilterExpression=Attr('customer_id').eq(customer_id),
                Limit=50
            )
            customer_cases = case_response.get('Items', [])
        
        # Count different fraud types
        victim_count = len([t for t in fraud_transactions if t.get('is_fraud')])
        blocked_count = len([t for t in fraud_transactions if t.get('status') == 'BLOCKED'])
        case_count = len(customer_cases)
        resolved_fraud_cases = len([c for c in customer_cases if 'Resolved - Fraud' in c.get('status', '')])
        
        history = {
            'customer_id': customer_id,
            'victim_count': victim_count,
            'perpetrator_count': 0,  # Would need separate flagging system
            'blocked_transactions': blocked_count,
            'total_cases': case_count,
            'resolved_fraud_cases': resolved_fraud_cases,
            'lookback_months': lookback_months,
            'recent_fraud_transactions': fraud_transactions[:5],  # Most recent 5
            'recent_cases': customer_cases[:5]
        }
        
        logger.info(
            "Fraud history retrieved",
            customer_id=customer_id,
            victim_count=victim_count,
            case_count=case_count
        )
        
        return history
    
    except Exception as e:
        logger.error("Fraud history check failed", error=str(e))
        return {
            'error': str(e),
            'customer_id': customer_id,
            'victim_count': 0,
            'blocked_transactions': 0,
            'lookback_months': lookback_months
        }

async def payee_analysis_tool(params: Dict) -> Dict:
    """Analyze payee account history."""
    
    payee_account = params.get('payee_account')
    lookback_months = params.get('lookback_months', 12)
    
    logger.info("Analyzing payee account", payee_account=payee_account)
    
    try:
        # Mock payee analysis
        analysis = {
            'payee_account': payee_account,
            'is_new_account': False,
            'account_age_days': 365,
            'incoming_transaction_count': 45,
            'total_received': 125000,
            'lookback_months': lookback_months
        }
        
        return analysis
    
    except Exception as e:
        logger.error("Payee analysis failed", error=str(e))
        return {'error': str(e)}


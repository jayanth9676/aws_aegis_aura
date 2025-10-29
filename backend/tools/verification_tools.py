"""Verification tools for payee and watchlist checks."""

from typing import Dict
from config import aws_config, system_config
from utils import get_logger

logger = get_logger("tools.verification")

async def verification_of_payee_tool(params: Dict) -> Dict:
    """Confirmation of Payee (CoP) verification with real DB lookups."""
    
    payee_account = params.get('payee_account')
    payee_name = params.get('payee_name', '').lower().strip()
    sort_code = params.get('sort_code', '')
    
    logger.info("Verifying payee with DB lookup", payee_account=payee_account, payee_name=payee_name)
    
    try:
        # Query DynamoDB for payee account information
        # In production, this would call Pay.UK CoP API
        table = aws_config.dynamodb.Table('aegis-payees')  # Create this table for payee registry
        
        try:
            # Try to find payee in registry
            response = table.get_item(
                Key={'payee_account': payee_account}
            )
            
            if 'Item' in response:
                registered_payee = response['Item']
                registered_name = registered_payee.get('name', '').lower().strip()
                
                # Calculate name match score
                match_score = _calculate_name_match(payee_name, registered_name)
                
                if match_score > 0.9:
                    match_status = 'MATCH'
                    confidence = match_score
                elif match_score > 0.7:
                    match_status = 'CLOSE_MATCH'
                    confidence = match_score
                else:
                    match_status = 'NO_MATCH'
                    confidence = 1.0 - match_score
                
                return {
                    'match_status': match_status,
                    'confidence': confidence,
                    'verified_name': registered_payee.get('name', ''),
                    'provided_name': payee_name,
                    'payee_account': payee_account,
                    'match_score': match_score,
                    'service': 'aegis_payee_registry',
                    'account_age_days': registered_payee.get('account_age_days', 0),
                    'previous_transactions': registered_payee.get('transaction_count', 0)
                }
            else:
                # Payee not in registry - treat as new payee
                logger.warning(f"Payee not in registry: {payee_account}")
                return {
                    'match_status': 'NOT_AVAILABLE',
                    'confidence': 0.5,
                    'verified_name': None,
                    'provided_name': payee_name,
                    'payee_account': payee_account,
                    'service': 'aegis_payee_registry',
                    'note': 'New payee - not in registry'
                }
        
        except aws_config.dynamodb.meta.client.exceptions.ResourceNotFoundException:
            logger.warning("Payee registry table not found, using fallback")
            # Fallback to basic logic if table doesn't exist
            return {
                'match_status': 'NOT_AVAILABLE',
                'confidence': 0.5,
                'verified_name': None,
                'provided_name': payee_name,
                'payee_account': payee_account,
                'service': 'fallback',
                'note': 'Payee registry not available'
            }
    
    except Exception as e:
        logger.error("CoP verification failed", error=str(e))
        return {
            'match_status': 'ERROR',
            'error': str(e),
            'confidence': 0.0
        }


def _calculate_name_match(name1: str, name2: str) -> float:
    """Calculate fuzzy name match score between 0 and 1."""
    import difflib
    
    # Simple similarity ratio
    similarity = difflib.SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
    
    # Boost score if both names contain same key words
    words1 = set(name1.lower().split())
    words2 = set(name2.lower().split())
    
    if words1 and words2:
        word_overlap = len(words1.intersection(words2)) / max(len(words1), len(words2))
        similarity = (similarity + word_overlap) / 2
    
    return similarity


async def watchlist_tool(params: Dict) -> Dict:
    """Check against internal and external watchlists with real DB queries."""
    
    entity = params.get('entity')  # Account number, name, etc.
    entity_type = params.get('entity_type', 'account')
    
    logger.info("Checking watchlist with DB query", entity=entity, entity_type=entity_type)
    
    try:
        # Query DynamoDB watchlist table
        # In production, also check external watchlists (OFAC, sanctions lists, etc.)
        table = aws_config.dynamodb.Table('aegis-watchlist')
        
        try:
            # Query watchlist by entity
            from boto3.dynamodb.conditions import Key
            
            response = table.query(
                IndexName='entity-index',  # Requires GSI on entity field
                KeyConditionExpression=Key('entity').eq(entity)
            )
            
            watchlist_entries = response.get('Items', [])
            
            if watchlist_entries:
                # Found watchlist hit
                entry = watchlist_entries[0]  # Take first match
                
                logger.warning(f"Watchlist hit detected: {entity}", 
                             risk_level=entry.get('risk_level'),
                             source=entry.get('source'))
                
                return {
                    'hit': True,
                    'risk_level': entry.get('risk_level', 'HIGH'),
                    'source': entry.get('source', 'internal_watchlist'),
                    'entity': entity,
                    'entity_type': entity_type,
                    'match_details': entry.get('reason', 'Watchlist match found'),
                    'added_date': entry.get('added_date'),
                    'match_count': len(watchlist_entries)
                }
            else:
                # No watchlist hit - check against known fraud patterns
                # Could also query external APIs here (OFAC, sanctions, etc.)
                
                return {
                    'hit': False,
                    'risk_level': 'LOW',
                    'entity': entity,
                    'entity_type': entity_type,
                    'checked_sources': ['internal_watchlist']
                }
        
        except aws_config.dynamodb.meta.client.exceptions.ResourceNotFoundException:
            logger.warning("Watchlist table not found, using fallback")
            # Fallback if table doesn't exist
            return {
                'hit': False,
                'risk_level': 'UNKNOWN',
                'entity': entity,
                'entity_type': entity_type,
                'note': 'Watchlist not available',
                'checked_sources': []
            }
    
    except Exception as e:
        logger.error("Watchlist check failed", error=str(e))
        return {
            'error': str(e),
            'hit': False,
            'risk_level': 'UNKNOWN',
            'entity': entity
        }




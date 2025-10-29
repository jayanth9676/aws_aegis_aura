"""Mule network detection queries for Neo4j graph database."""

from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta

from .client import Neo4jClient
from .schemas import AccountVertex, MuleNetworkVertex
from utils import get_logger

logger = get_logger(__name__)


class MuleDetectionQueries:
    """Mule network detection queries using Cypher."""
    
    def __init__(self, client: Neo4jClient):
        """Initialize with Neo4j client.
        
        Args:
            client: Neo4j client instance
        """
        self.client = client
    
    def find_suspicious_accounts(
        self,
        min_inbound_txns: int = 20,
        min_unique_senders: int = 10,
        min_outbound_txns: int = 5,
        max_unique_recipients: int = 3,
        min_turnover_ratio: float = 0.9
    ) -> List[Dict]:
        """Find accounts with mule characteristics.
        
        Args:
            min_inbound_txns: Minimum inbound transactions
            min_unique_senders: Minimum unique senders
            min_outbound_txns: Minimum outbound transactions
            max_unique_recipients: Maximum unique recipients
            min_turnover_ratio: Minimum rapid turnover ratio
            
        Returns:
            List of suspicious account IDs with scores
        """
        query = """
            g.V().hasLabel('account')
             .has('total_inbound_transactions', gt(minInbound))
             .has('unique_senders', gt(minSenders))
             .has('total_outbound_transactions', gt(minOutbound))
             .has('unique_recipients', lt(maxRecipients))
             .has('rapid_turnover_ratio', gt(minTurnover))
             .project('account_id', 'mule_probability', 'stats')
             .by(id)
             .by('mule_probability')
             .by(valueMap('total_inbound_transactions', 'unique_senders', 
                         'total_outbound_transactions', 'unique_recipients', 
                         'rapid_turnover_ratio'))
        """
        
        bindings = {
            'minInbound': min_inbound_txns,
            'minSenders': min_unique_senders,
            'minOutbound': min_outbound_txns,
            'maxRecipients': max_unique_recipients,
            'minTurnover': min_turnover_ratio
        }
        
        try:
            results = self.client.execute_query(query, bindings)
            logger.info(f"Found {len(results)} suspicious accounts", count=len(results))
            return results
        except Exception as e:
            logger.error(f"Failed to find suspicious accounts", error=str(e))
            return []
    
    def find_connected_accounts(
        self,
        account_id: str,
        max_hops: int = 3,
        time_window_days: int = 30
    ) -> List[str]:
        """Find accounts connected within N hops.
        
        Args:
            account_id: Source account ID
            max_hops: Maximum traversal depth
            time_window_days: Time window for recent transactions
            
        Returns:
            List of connected account IDs
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=time_window_days)).isoformat()
        
        query = f"""
            g.V(accountId)
             .repeat(outE('payment').has('timestamp', gt(cutoffDate)).inV())
             .times({max_hops})
             .dedup()
             .id()
        """
        
        bindings = {
            'accountId': account_id,
            'cutoffDate': cutoff_date
        }
        
        try:
            results = self.client.execute_query(query, bindings)
            logger.debug(
                f"Found connected accounts",
                source_account=account_id,
                connected_count=len(results)
            )
            return [str(r) for r in results]
        except Exception as e:
            logger.error(
                f"Failed to find connected accounts",
                account_id=account_id,
                error=str(e)
            )
            return []
    
    def calculate_network_centrality(self, account_id: str) -> Dict:
        """Calculate network centrality metrics for account.
        
        Args:
            account_id: Account ID
            
        Returns:
            Dict with in_degree, out_degree, betweenness
        """
        query = """
            g.V(accountId)
             .project('id', 'in_degree', 'out_degree')
             .by(id)
             .by(inE('payment').count())
             .by(outE('payment').count())
        """
        
        bindings = {'accountId': account_id}
        
        try:
            results = self.client.execute_query(query, bindings)
            if results:
                return results[0]
            return {'id': account_id, 'in_degree': 0, 'out_degree': 0}
        except Exception as e:
            logger.error(
                f"Failed to calculate centrality",
                account_id=account_id,
                error=str(e)
            )
            return {'id': account_id, 'in_degree': 0, 'out_degree': 0}
    
    def detect_rapid_money_movement(
        self,
        account_id: str,
        time_window_hours: int = 24
    ) -> Dict:
        """Detect rapid money movement patterns.
        
        Args:
            account_id: Account ID
            time_window_hours: Time window in hours
            
        Returns:
            Dict with rapid movement statistics
        """
        cutoff_time = (datetime.utcnow() - timedelta(hours=time_window_hours)).isoformat()
        
        query = """
            g.V(accountId)
             .local(
                 __.bothE('payment')
                   .has('timestamp', gt(cutoffTime))
                   .values('amount')
                   .fold()
             )
             .project('total_volume', 'transaction_count')
             .by(__.unfold().sum())
             .by(__.unfold().count())
        """
        
        bindings = {
            'accountId': account_id,
            'cutoffTime': cutoff_time
        }
        
        try:
            results = self.client.execute_query(query, bindings)
            if results:
                return {
                    'account_id': account_id,
                    'time_window_hours': time_window_hours,
                    'total_volume': results[0].get('total_volume', 0),
                    'transaction_count': results[0].get('transaction_count', 0)
                }
            return {
                'account_id': account_id,
                'time_window_hours': time_window_hours,
                'total_volume': 0,
                'transaction_count': 0
            }
        except Exception as e:
            logger.error(
                f"Failed to detect rapid movement",
                account_id=account_id,
                error=str(e)
            )
            return {
                'account_id': account_id,
                'time_window_hours': time_window_hours,
                'total_volume': 0,
                'transaction_count': 0
            }
    
    def find_common_beneficiary_clusters(
        self,
        min_cluster_size: int = 5,
        min_shared_beneficiaries: int = 2
    ) -> List[Dict]:
        """Find clusters of accounts sending to common beneficiaries.
        
        Args:
            min_cluster_size: Minimum accounts in cluster
            min_shared_beneficiaries: Minimum shared beneficiaries
            
        Returns:
            List of clusters with account IDs
        """
        # This is a complex query that finds groups of accounts
        # sending payments to the same small set of beneficiaries
        query = """
            g.V().hasLabel('account')
             .where(
                 __.outE('payment').inV()
                   .groupCount()
                   .unfold()
                   .select(values)
                   .is(gte(minShared))
             )
             .group()
             .by(
                 __.outE('payment').inV().id().fold()
             )
             .unfold()
             .select(values)
             .where(__.count(local).is(gte(minClusterSize)))
        """
        
        bindings = {
            'minClusterSize': min_cluster_size,
            'minShared': min_shared_beneficiaries
        }
        
        try:
            results = self.client.execute_query(query, bindings)
            logger.info(f"Found {len(results)} beneficiary clusters", count=len(results))
            return results
        except Exception as e:
            logger.error(f"Failed to find beneficiary clusters", error=str(e))
            return []
    
    def get_transaction_path(
        self,
        from_account_id: str,
        to_account_id: str,
        max_hops: int = 5
    ) -> Optional[List[str]]:
        """Find transaction path between two accounts.
        
        Args:
            from_account_id: Source account
            to_account_id: Destination account
            max_hops: Maximum path length
            
        Returns:
            List of account IDs in path, or None if no path exists
        """
        query = f"""
            g.V(fromAccount)
             .repeat(outE('payment').inV().simplePath())
             .until(__.hasId(toAccount))
             .times({max_hops})
             .path()
             .by(id)
             .limit(1)
        """
        
        bindings = {
            'fromAccount': from_account_id,
            'toAccount': to_account_id
        }
        
        try:
            results = self.client.execute_query(query, bindings)
            if results:
                path = results[0]
                logger.debug(
                    f"Found transaction path",
                    from_account=from_account_id,
                    to_account=to_account_id,
                    path_length=len(path)
                )
                return [str(node) for node in path]
            return None
        except Exception as e:
            logger.error(
                f"Failed to find transaction path",
                from_account=from_account_id,
                to_account=to_account_id,
                error=str(e)
            )
            return None
    
    def update_mule_probability(self, account_id: str, probability: float):
        """Update mule probability score for account.
        
        Args:
            account_id: Account ID
            probability: Mule probability (0.0-1.0)
        """
        try:
            self.client.update_vertex_properties(
                account_id,
                {
                    'mule_probability': probability,
                    'is_flagged_mule': probability > 0.7,
                    'flagged_date': datetime.utcnow().isoformat() if probability > 0.7 else None,
                    'flagging_algorithm': 'gnn' if probability > 0.7 else None
                }
            )
            logger.info(
                f"Updated mule probability",
                account_id=account_id,
                probability=probability
            )
        except Exception as e:
            logger.error(
                f"Failed to update mule probability",
                account_id=account_id,
                error=str(e)
            )


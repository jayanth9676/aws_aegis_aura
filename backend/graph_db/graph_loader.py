"""Graph loader for ingesting transactions into Neo4j from DynamoDB."""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
import uuid

from .client import Neo4jClient
from .schemas import AccountVertex, PaymentEdge, AccountType
from models import Transaction
from utils import get_logger

logger = get_logger(__name__)


class GraphLoader:
    """Load transaction data into Neo4j graph database."""
    
    def __init__(self, client: Neo4jClient):
        """Initialize with Neo4j client.
        
        Args:
            client: Neo4j client instance
        """
        self.client = client
    
    def load_transaction(self, transaction: Transaction) -> bool:
        """Load single transaction into graph.
        
        Creates account vertices if they don't exist and adds payment edge.
        
        Args:
            transaction: Transaction model instance
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure customer account vertex exists
            customer_account_id = f"account:{transaction.customer_id}"
            if not self.client.get_vertex(customer_account_id):
                self._create_account_vertex(
                    customer_account_id,
                    transaction.customer_id,
                    AccountType.PERSONAL
                )
            
            # Ensure payee account vertex exists
            payee_account_id = f"account:{transaction.payee_account}"
            if not self.client.get_vertex(payee_account_id):
                self._create_account_vertex(
                    payee_account_id,
                    transaction.payee_account,
                    AccountType.PERSONAL  # Default, can be updated later
                )
            
            # Create payment edge
            payment_edge = PaymentEdge(
                transaction_id=transaction.transaction_id,
                amount=transaction.amount,
                timestamp=transaction.created_at,
                payment_channel=transaction.payment_channel.value,
                risk_score=0  # Will be updated when fraud decision is made
            )
            
            self.client.add_edge(
                label='payment',
                from_vertex_id=customer_account_id,
                to_vertex_id=payee_account_id,
                properties=payment_edge.to_properties()
            )
            
            # Update account statistics
            self._update_account_stats(customer_account_id, payee_account_id)
            
            logger.info(
                f"Loaded transaction into graph",
                transaction_id=transaction.transaction_id,
                from_account=customer_account_id,
                to_account=payee_account_id
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to load transaction into graph",
                transaction_id=transaction.transaction_id,
                error=str(e)
            )
            return False
    
    def _create_account_vertex(
        self,
        account_id: str,
        account_number: str,
        account_type: AccountType
    ):
        """Create account vertex in graph.
        
        Args:
            account_id: Vertex ID
            account_number: Account number
            account_type: Account type
        """
        account_vertex = AccountVertex(
            account_id=account_id,
            account_number=account_number,
            account_type=account_type,
            creation_date=datetime.utcnow()
        )
        
        self.client.add_vertex(
            label='account',
            vertex_id=account_id,
            properties=account_vertex.to_properties()
        )
        
        logger.debug(f"Created account vertex", account_id=account_id)
    
    def _update_account_stats(self, sender_id: str, recipient_id: str):
        """Update transaction statistics for accounts.
        
        Args:
            sender_id: Sender account vertex ID
            recipient_id: Recipient account vertex ID
        """
        try:
            # Update sender (outbound) stats
            self._update_single_account_stats(sender_id, is_sender=True)
            
            # Update recipient (inbound) stats
            self._update_single_account_stats(recipient_id, is_sender=False)
            
        except Exception as e:
            logger.error(
                f"Failed to update account stats",
                sender_id=sender_id,
                recipient_id=recipient_id,
                error=str(e)
            )
    
    def _update_single_account_stats(self, account_id: str, is_sender: bool):
        """Update statistics for a single account.
        
        Args:
            account_id: Account vertex ID
            is_sender: True if this is the sending account
        """
        # Query for transaction statistics
        if is_sender:
            # Outbound transactions
            query = """
                g.V(accountId)
                 .project('total_txns', 'total_amount', 'unique_counterparties')
                 .by(outE('payment').count())
                 .by(outE('payment').values('amount').sum())
                 .by(outE('payment').inV().dedup().count())
            """
        else:
            # Inbound transactions
            query = """
                g.V(accountId)
                 .project('total_txns', 'total_amount', 'unique_counterparties')
                 .by(inE('payment').count())
                 .by(inE('payment').values('amount').sum())
                 .by(inE('payment').outV().dedup().count())
            """
        
        bindings = {'accountId': account_id}
        results = self.client.execute_query(query, bindings)
        
        if results:
            stats = results[0]
            
            # Prepare update properties
            if is_sender:
                properties = {
                    'total_outbound_transactions': stats.get('total_txns', 0),
                    'total_outbound_amount': float(stats.get('total_amount', 0.0)),
                    'unique_recipients': stats.get('unique_counterparties', 0)
                }
            else:
                properties = {
                    'total_inbound_transactions': stats.get('total_txns', 0),
                    'total_inbound_amount': float(stats.get('total_amount', 0.0)),
                    'unique_senders': stats.get('unique_counterparties', 0)
                }
            
            # Update vertex
            self.client.update_vertex_properties(account_id, properties)
            
            # Calculate and update rapid turnover ratio if we have both inbound and outbound data
            if not is_sender:
                self._calculate_rapid_turnover(account_id)
    
    def _calculate_rapid_turnover(self, account_id: str):
        """Calculate rapid turnover ratio for account.
        
        Rapid turnover = outbound amount / inbound amount within 24 hours
        
        Args:
            account_id: Account vertex ID
        """
        from datetime import timedelta
        
        cutoff_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        
        query = """
            g.V(accountId)
             .project('inbound_24h', 'outbound_24h')
             .by(
                 inE('payment')
                 .has('timestamp', gt(cutoffTime))
                 .values('amount')
                 .sum()
             )
             .by(
                 outE('payment')
                 .has('timestamp', gt(cutoffTime))
                 .values('amount')
                 .sum()
             )
        """
        
        bindings = {
            'accountId': account_id,
            'cutoffTime': cutoff_time
        }
        
        results = self.client.execute_query(query, bindings)
        
        if results:
            data = results[0]
            inbound = float(data.get('inbound_24h', 0.0))
            outbound = float(data.get('outbound_24h', 0.0))
            
            # Calculate turnover ratio
            if inbound > 0:
                turnover_ratio = outbound / inbound
            else:
                turnover_ratio = 0.0
            
            # Update vertex
            self.client.update_vertex_properties(
                account_id,
                {'rapid_turnover_ratio': turnover_ratio}
            )
    
    def bulk_load_transactions(self, transactions: List[Transaction]) -> Dict[str, int]:
        """Bulk load multiple transactions into graph.
        
        Args:
            transactions: List of Transaction instances
            
        Returns:
            Dict with success/failure counts
        """
        success_count = 0
        failure_count = 0
        
        logger.info(f"Starting bulk load", transaction_count=len(transactions))
        
        for transaction in transactions:
            if self.load_transaction(transaction):
                success_count += 1
            else:
                failure_count += 1
        
        logger.info(
            f"Bulk load completed",
            success_count=success_count,
            failure_count=failure_count
        )
        
        return {
            'success': success_count,
            'failure': failure_count,
            'total': len(transactions)
        }
    
    def update_payment_risk_score(self, transaction_id: str, risk_score: int):
        """Update risk score for payment edge.
        
        Args:
            transaction_id: Transaction ID
            risk_score: Risk score (0-100)
        """
        query = """
            g.E()
             .has('transaction_id', transactionId)
             .property('risk_score', riskScore)
        """
        
        bindings = {
            'transactionId': transaction_id,
            'riskScore': risk_score
        }
        
        try:
            self.client.execute_query(query, bindings)
            logger.debug(
                f"Updated payment risk score",
                transaction_id=transaction_id,
                risk_score=risk_score
            )
        except Exception as e:
            logger.error(
                f"Failed to update payment risk score",
                transaction_id=transaction_id,
                error=str(e)
            )
    
    def get_account_network(
        self,
        account_id: str,
        depth: int = 2,
        include_properties: bool = True
    ) -> Dict:
        """Get account network for visualization.
        
        Args:
            account_id: Central account ID
            depth: Network depth (hops)
            include_properties: Include vertex/edge properties
            
        Returns:
            Dict with nodes and edges for D3.js visualization
        """
        # Get connected vertices
        query = f"""
            g.V(accountId)
             .repeat(__.bothE('payment').bothV().simplePath())
             .times({depth})
             .dedup()
        """
        
        if include_properties:
            query += ".valueMap(true)"
        else:
            query += ".id()"
        
        bindings = {'accountId': account_id}
        
        try:
            vertices = self.client.execute_query(query, bindings)
            
            # Get edges between these vertices
            edge_query = f"""
                g.V(accountId)
                 .repeat(__.bothE('payment').bothV().simplePath())
                 .times({depth})
                 .dedup()
                 .bothE('payment')
                 .dedup()
            """
            
            if include_properties:
                edge_query += ".valueMap(true).with(WithOptions.tokens)"
            
            edges = self.client.execute_query(edge_query, bindings)
            
            return {
                'nodes': vertices,
                'edges': edges,
                'center_node': account_id
            }
            
        except Exception as e:
            logger.error(
                f"Failed to get account network",
                account_id=account_id,
                error=str(e)
            )
            return {'nodes': [], 'edges': [], 'center_node': account_id}


"""Neo4j graph database client wrapper with connection pooling."""

import os
from typing import Any, Dict, List, Optional
from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import Neo4jError

from utils import get_logger

logger = get_logger(__name__)


class Neo4jClient:
    """Neo4j client wrapper with connection pooling and retry logic."""
    
    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        max_retries: int = 3,
        timeout_seconds: int = 30
    ):
        """Initialize Neo4j client.
        
        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
            database: Neo4j database name
            max_retries: Maximum retry attempts
            timeout_seconds: Query timeout in seconds
        """
        self.uri = uri or os.getenv('NEO4J_URI')
        self.username = username or os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD')
        self.database = database or os.getenv('NEO4J_DATABASE', 'neo4j')
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        
        if not self.uri or not self.password:
            raise ValueError("Neo4j URI and password must be configured")
        
        # Initialize driver
        self._driver: Optional[Driver] = None
        
        logger.info(f"Neo4j client initialized", uri=self.uri, database=self.database)
    
    @property
    def driver(self) -> Driver:
        """Get Neo4j driver instance."""
        if not self._driver:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
        return self._driver
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.driver.session(database=self.database)
    
    def execute_query(self, query: str, parameters: Optional[Dict] = None) -> List[Any]:
        """Execute Cypher query with retry logic.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of query results
        """
        retries = 0
        parameters = parameters or {}
        
        while retries < self.max_retries:
            try:
                logger.debug(f"Executing Neo4j query", query=query[:200])
                with self.get_session() as session:
                    result = session.run(query, parameters)
                    records = [record.data() for record in result]
                logger.debug(f"Query completed", result_count=len(records))
                return records
            except Neo4jError as e:
                retries += 1
                logger.warning(
                    f"Query failed, retry {retries}/{self.max_retries}",
                    error=str(e),
                    query=query[:200]
                )
                if retries >= self.max_retries:
                    logger.error(f"Query failed after {self.max_retries} retries", error=str(e))
                    raise
        
        return []
    
    def add_node(self, label: str, node_id: str, properties: Dict) -> Dict:
        """Add node to graph.
        
        Args:
            label: Node label
            node_id: Node ID
            properties: Node properties
            
        Returns:
            Created node properties
        """
        try:
            properties_copy = properties.copy()
            properties_copy['id'] = node_id
            
            query = f"""
            MERGE (n:{label} {{id: $node_id}})
            SET n += $properties
            RETURN n
            """
            
            result = self.execute_query(query, {
                'node_id': node_id,
                'properties': properties_copy
            })
            
            logger.debug(f"Added node", label=label, node_id=node_id)
            return result[0]['n'] if result else {}
        except Exception as e:
            logger.error(f"Failed to add node", label=label, node_id=node_id, error=str(e))
            raise
    
    def add_relationship(
        self,
        relationship_type: str,
        from_node_id: str,
        to_node_id: str,
        properties: Optional[Dict] = None
    ) -> Dict:
        """Add relationship between nodes.
        
        Args:
            relationship_type: Relationship type
            from_node_id: Source node ID
            to_node_id: Target node ID
            properties: Relationship properties
            
        Returns:
            Created relationship properties
        """
        try:
            properties = properties or {}
            
            query = f"""
            MATCH (from {{id: $from_id}})
            MATCH (to {{id: $to_id}})
            MERGE (from)-[r:{relationship_type}]->(to)
            SET r += $properties
            RETURN r
            """
            
            result = self.execute_query(query, {
                'from_id': from_node_id,
                'to_id': to_node_id,
                'properties': properties
            })
            
            logger.debug(
                f"Added relationship",
                type=relationship_type,
                from_node=from_node_id,
                to_node=to_node_id
            )
            return result[0]['r'] if result else {}
        except Exception as e:
            logger.error(
                f"Failed to add relationship",
                type=relationship_type,
                from_node=from_node_id,
                to_node=to_node_id,
                error=str(e)
            )
            raise
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """Get node by ID.
        
        Args:
            node_id: Node ID
            
        Returns:
            Node properties dict or None
        """
        try:
            query = """
            MATCH (n {id: $node_id})
            RETURN n
            """
            result = self.execute_query(query, {'node_id': node_id})
            if result:
                return result[0]['n']
            return None
        except Exception as e:
            logger.error(f"Failed to get node", node_id=node_id, error=str(e))
            return None
    
    def update_node_properties(self, node_id: str, properties: Dict):
        """Update node properties.
        
        Args:
            node_id: Node ID
            properties: Properties to update
        """
        try:
            query = """
            MATCH (n {id: $node_id})
            SET n += $properties
            RETURN n
            """
            self.execute_query(query, {
                'node_id': node_id,
                'properties': properties
            })
            logger.debug(f"Updated node properties", node_id=node_id)
        except Exception as e:
            logger.error(f"Failed to update node", node_id=node_id, error=str(e))
            raise
    
    def delete_node(self, node_id: str):
        """Delete node and its relationships.
        
        Args:
            node_id: Node ID
        """
        try:
            query = """
            MATCH (n {id: $node_id})
            DETACH DELETE n
            """
            self.execute_query(query, {'node_id': node_id})
            logger.debug(f"Deleted node", node_id=node_id)
        except Exception as e:
            logger.error(f"Failed to delete node", node_id=node_id, error=str(e))
            raise
    
    def close(self):
        """Close connections."""
        try:
            if self._driver:
                self._driver.close()
            logger.info("Neo4j driver closed")
        except Exception as e:
            logger.error(f"Error closing driver", error=str(e))
    
    def verify_connectivity(self) -> bool:
        """Verify connection to Neo4j database."""
        try:
            with self.get_session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("Neo4j connectivity verified")
            return True
        except Exception as e:
            logger.error(f"Neo4j connectivity check failed", error=str(e))
            return False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


"""Graph Neural Network models for mule account detection and transaction analysis."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F

LOGGER = logging.getLogger("aegis.models.gnn")

try:
    from torch_geometric.nn import SAGEConv, GATConv, GCNConv, global_mean_pool
    from torch_geometric.data import Data, Batch
    PYG_AVAILABLE = True
except ImportError:
    PYG_AVAILABLE = False
    LOGGER.warning("PyTorch Geometric not available. GNN models will not work.")


@dataclass
class GraphSAGEConfig:
    """Configuration for GraphSAGE model."""
    num_node_features: int
    hidden_channels: int = 64
    num_layers: int = 3
    dropout: float = 0.3
    learning_rate: float = 0.001
    weight_decay: float = 1e-5


@dataclass
class TemporalGNNConfig:
    """Configuration for Temporal Graph Neural Network."""
    num_features: int
    hidden_dim: int = 128
    num_heads: int = 4
    num_layers: int = 2
    dropout: float = 0.3
    learning_rate: float = 0.001
    weight_decay: float = 1e-5


class GraphSAGEMuleDetector(torch.nn.Module):
    """GraphSAGE model for mule account detection.
    
    Uses GraphSAGE to learn node embeddings that capture account relationships
    and transaction patterns for identifying mule accounts.
    """
    
    def __init__(self, config: GraphSAGEConfig):
        super().__init__()
        if not PYG_AVAILABLE:
            raise ImportError("PyTorch Geometric is required for GNN models")
        
        self.config = config
        self.num_layers = config.num_layers
        
        # GraphSAGE layers
        self.convs = torch.nn.ModuleList()
        self.convs.append(SAGEConv(config.num_node_features, config.hidden_channels))
        
        for _ in range(config.num_layers - 2):
            self.convs.append(SAGEConv(config.hidden_channels, config.hidden_channels))
        
        if config.num_layers > 1:
            self.convs.append(SAGEConv(config.hidden_channels, config.hidden_channels // 2))
        
        self.dropout = torch.nn.Dropout(config.dropout)
        self.classifier = torch.nn.Linear(config.hidden_channels // 2, 1)
        
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, 
                batch: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Forward pass through GraphSAGE layers.
        
        Args:
            x: Node features [num_nodes, num_features]
            edge_index: Edge indices [2, num_edges]
            batch: Batch indices for graph-level tasks (optional)
            
        Returns:
            Node embeddings or graph-level predictions
        """
        # GraphSAGE forward pass
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if i < len(self.convs) - 1:  # Don't apply activation after last layer
                x = F.relu(x)
                x = self.dropout(x)
        
        # For node classification (mule detection)
        if batch is None:
            return torch.sigmoid(self.classifier(x))
        
        # For graph-level tasks (if needed)
        x = global_mean_pool(x, batch)
        return torch.sigmoid(self.classifier(x))
    
    def get_node_embeddings(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """Get node embeddings without classification head.
        
        Args:
            x: Node features
            edge_index: Edge indices
            
        Returns:
            Node embeddings
        """
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if i < len(self.convs) - 1:
                x = F.relu(x)
                x = self.dropout(x)
        return x


class TemporalGraphNetwork(torch.nn.Module):
    """Temporal Graph Neural Network for transaction flow analysis.
    
    Combines GRU for temporal evolution with Graph Attention Networks
    for spatial relationships in transaction networks.
    """
    
    def __init__(self, config: TemporalGNNConfig):
        super().__init__()
        if not PYG_AVAILABLE:
            raise ImportError("PyTorch Geometric is required for GNN models")
        
        self.config = config
        
        # Temporal encoding with GRU
        self.gru = torch.nn.GRU(
            config.num_features, 
            config.hidden_dim, 
            batch_first=True,
            dropout=config.dropout if config.num_layers > 1 else 0
        )
        
        # Graph attention layers for spatial relationships
        self.gat_layers = torch.nn.ModuleList()
        self.gat_layers.append(GATConv(
            config.hidden_dim, 
            config.hidden_dim // config.num_heads, 
            heads=config.num_heads, 
            dropout=config.dropout
        ))
        
        for _ in range(config.num_layers - 1):
            self.gat_layers.append(GATConv(
                config.hidden_dim, 
                config.hidden_dim // config.num_heads, 
                heads=config.num_heads, 
                dropout=config.dropout
            ))
        
        # Final classification layer
        self.classifier = torch.nn.Linear(config.hidden_dim, 1)
        self.dropout = torch.nn.Dropout(config.dropout)
        
    def forward(self, node_features_sequence: torch.Tensor, 
                edge_index: torch.Tensor) -> torch.Tensor:
        """Forward pass through temporal GNN.
        
        Args:
            node_features_sequence: Temporal node features [batch, seq_len, num_features]
            edge_index: Edge indices [2, num_edges]
            
        Returns:
            Node-level predictions
        """
        # Temporal encoding
        gru_out, _ = self.gru(node_features_sequence)
        x = gru_out[:, -1, :]  # Take last timestep
        
        # Spatial graph convolution
        for gat in self.gat_layers:
            x = gat(x, edge_index)
            x = F.elu(x)
            x = self.dropout(x)
        
        return torch.sigmoid(self.classifier(x))
    
    def get_temporal_embeddings(self, node_features_sequence: torch.Tensor,
                              edge_index: torch.Tensor) -> torch.Tensor:
        """Get temporal node embeddings without classification head.
        
        Args:
            node_features_sequence: Temporal node features
            edge_index: Edge indices
            
        Returns:
            Temporal node embeddings
        """
        # Temporal encoding
        gru_out, _ = self.gru(node_features_sequence)
        x = gru_out[:, -1, :]
        
        # Spatial graph convolution
        for gat in self.gat_layers:
            x = gat(x, edge_index)
            x = F.elu(x)
            x = self.dropout(x)
        
        return x


class HeterogeneousGraphNetwork(torch.nn.Module):
    """Heterogeneous Graph Network for multi-entity relationships.
    
    Handles different types of nodes (accounts, customers, transactions)
    and edges (transactions, ownership, etc.) in the fraud detection graph.
    """
    
    def __init__(self, node_types: List[str], edge_types: List[str],
                 node_feature_dims: Dict[str, int], hidden_dim: int = 128):
        super().__init__()
        if not PYG_AVAILABLE:
            raise ImportError("PyTorch Geometric is required for GNN models")
        
        self.node_types = node_types
        self.edge_types = edge_types
        self.hidden_dim = hidden_dim
        
        # Node type embeddings
        self.node_embeddings = torch.nn.ModuleDict({
            node_type: torch.nn.Linear(node_feature_dims[node_type], hidden_dim)
            for node_type in node_types
        })
        
        # Edge type attention layers
        self.edge_attention = torch.nn.ModuleDict({
            edge_type: GATConv(hidden_dim, hidden_dim // 4, heads=4, dropout=0.1)
            for edge_type in edge_types
        })
        
        # Final classifier
        self.classifier = torch.nn.Linear(hidden_dim, 1)
        
    def forward(self, node_features: Dict[str, torch.Tensor],
                edge_indices: Dict[str, torch.Tensor]) -> torch.Tensor:
        """Forward pass through heterogeneous graph.
        
        Args:
            node_features: Dictionary of node features by type
            edge_indices: Dictionary of edge indices by type
            
        Returns:
            Node-level predictions
        """
        # Embed node features
        embedded_nodes = {}
        for node_type, features in node_features.items():
            embedded_nodes[node_type] = self.node_embeddings[node_type](features)
        
        # Apply edge-specific attention
        final_embeddings = {}
        for edge_type, edge_index in edge_indices.items():
            if edge_type in self.edge_attention:
                # This is a simplified version - in practice, you'd need
                # to handle different node types connected by each edge type
                for node_type, features in embedded_nodes.items():
                    if node_type not in final_embeddings:
                        final_embeddings[node_type] = features
                    else:
                        final_embeddings[node_type] += self.edge_attention[edge_type](
                            features, edge_index
                        )
        
        # Combine embeddings (simplified - would need proper aggregation)
        combined_embeddings = torch.cat(list(final_embeddings.values()), dim=0)
        return torch.sigmoid(self.classifier(combined_embeddings))


def build_graph_from_transactions(transactions_df, accounts_df, 
                                node_features: Optional[Dict[str, List[str]]] = None) -> Data:
    """Build PyTorch Geometric graph from transaction and account data.
    
    Args:
        transactions_df: DataFrame with transaction data
        accounts_df: DataFrame with account data
        node_features: Dictionary of feature names by node type
        
    Returns:
        PyTorch Geometric Data object
    """
    if not PYG_AVAILABLE:
        raise ImportError("PyTorch Geometric is required for graph construction")
    
    # Create node mapping
    all_accounts = set(transactions_df['source_account_id'].unique()) | \
                  set(transactions_df['destination_account_id'].unique())
    account_to_idx = {acc: idx for idx, acc in enumerate(sorted(all_accounts))}
    
    # Build edge list
    edges = []
    edge_attrs = []
    
    for _, txn in transactions_df.iterrows():
        src_idx = account_to_idx[txn['source_account_id']]
        dst_idx = account_to_idx[txn['destination_account_id']]
        
        edges.append([src_idx, dst_idx])
        edge_attrs.append([
            txn.get('amount', 0.0),
            txn.get('risk_score', 0.0),
            txn.get('is_fraud', 0.0)
        ])
    
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    edge_attr = torch.tensor(edge_attrs, dtype=torch.float)
    
    # Build node features
    if node_features is None:
        # Default features: account properties
        node_feature_names = [
            'daily_limit', 'monthly_limit', 'is_mule_account',
            'in_degree', 'out_degree', 'total_degree'
        ]
    else:
        node_feature_names = node_features.get('accounts', [])
    
    # Create node feature matrix
    node_features_list = []
    for account_id in sorted(all_accounts):
        account_data = accounts_df[accounts_df['account_id'] == account_id]
        if len(account_data) > 0:
            features = [account_data.iloc[0].get(feat, 0.0) for feat in node_feature_names]
        else:
            features = [0.0] * len(node_feature_names)
        node_features_list.append(features)
    
    x = torch.tensor(node_features_list, dtype=torch.float)
    
    # Create labels (mule account detection)
    y = []
    for account_id in sorted(all_accounts):
        account_data = accounts_df[accounts_df['account_id'] == account_id]
        if len(account_data) > 0:
            y.append(float(account_data.iloc[0].get('is_mule_account', False)))
        else:
            y.append(0.0)
    
    y = torch.tensor(y, dtype=torch.float).unsqueeze(1)
    
    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)


def create_temporal_graph_data(transactions_df, accounts_df, 
                             time_window_days: int = 7) -> List[Data]:
    """Create temporal graph data for time-series analysis.
    
    Args:
        transactions_df: DataFrame with transaction data
        accounts_df: DataFrame with account data
        time_window_days: Number of days per time window
        
    Returns:
        List of Data objects for each time window
    """
    if not PYG_AVAILABLE:
        raise ImportError("PyTorch Geometric is required for temporal graph construction")
    
    # Convert transaction dates
    transactions_df = transactions_df.copy()
    transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])
    
    # Create time windows
    start_date = transactions_df['transaction_date'].min()
    end_date = transactions_df['transaction_date'].max()
    
    temporal_graphs = []
    current_date = start_date
    
    while current_date < end_date:
        window_end = current_date + pd.Timedelta(days=time_window_days)
        
        # Filter transactions in current window
        window_transactions = transactions_df[
            (transactions_df['transaction_date'] >= current_date) &
            (transactions_df['transaction_date'] < window_end)
        ]
        
        if len(window_transactions) > 0:
            # Build graph for this time window
            graph_data = build_graph_from_transactions(window_transactions, accounts_df)
            temporal_graphs.append(graph_data)
        
        current_date = window_end
    
    return temporal_graphs


# Utility functions for graph analysis
def compute_graph_metrics(graph_data: Data) -> Dict[str, float]:
    """Compute graph-level metrics for analysis.
    
    Args:
        graph_data: PyTorch Geometric Data object
        
    Returns:
        Dictionary of graph metrics
    """
    if not PYG_AVAILABLE:
        return {}
    
    num_nodes = graph_data.x.size(0)
    num_edges = graph_data.edge_index.size(1)
    
    # Basic metrics
    metrics = {
        'num_nodes': num_nodes,
        'num_edges': num_edges,
        'density': (2 * num_edges) / (num_nodes * (num_nodes - 1)) if num_nodes > 1 else 0.0,
        'avg_degree': (2 * num_edges) / num_nodes if num_nodes > 0 else 0.0,
    }
    
    # Node feature statistics
    if graph_data.x.size(1) > 0:
        metrics.update({
            'avg_node_features': float(graph_data.x.mean()),
            'std_node_features': float(graph_data.x.std()),
        })
    
    # Edge attribute statistics
    if hasattr(graph_data, 'edge_attr') and graph_data.edge_attr is not None:
        metrics.update({
            'avg_edge_attr': float(graph_data.edge_attr.mean()),
            'std_edge_attr': float(graph_data.edge_attr.std()),
        })
    
    return metrics


def visualize_graph_structure(graph_data: Data, output_path: Optional[str] = None) -> None:
    """Visualize graph structure (requires matplotlib and networkx).
    
    Args:
        graph_data: PyTorch Geometric Data object
        output_path: Path to save visualization (optional)
    """
    try:
        import matplotlib.pyplot as plt
        import networkx as nx
    except ImportError:
        LOGGER.warning("matplotlib and networkx required for graph visualization")
        return
    
    if not PYG_AVAILABLE:
        LOGGER.warning("PyTorch Geometric required for graph visualization")
        return
    
    # Convert to NetworkX for visualization
    G = nx.Graph()
    
    # Add nodes
    for i in range(graph_data.x.size(0)):
        G.add_node(i, features=graph_data.x[i].tolist())
    
    # Add edges
    edge_index = graph_data.edge_index.numpy()
    for i in range(edge_index.shape[1]):
        src, dst = edge_index[0, i], edge_index[1, i]
        G.add_edge(src, dst)
    
    # Create visualization
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, k=1, iterations=50)
    
    # Color nodes by mule status if available
    if hasattr(graph_data, 'y') and graph_data.y is not None:
        node_colors = ['red' if y.item() > 0.5 else 'blue' for y in graph_data.y]
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=100, alpha=0.7)
    else:
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=100, alpha=0.7)
    
    nx.draw_networkx_edges(G, pos, alpha=0.5, edge_color='gray')
    nx.draw_networkx_labels(G, pos, font_size=8)
    
    plt.title("Transaction Network Graph")
    plt.axis('off')
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        LOGGER.info("Graph visualization saved to %s", output_path)
    else:
        plt.show()
    
    plt.close()

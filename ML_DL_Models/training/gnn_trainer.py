"""Training pipeline for Graph Neural Network models."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from configs import AppConfig
from models.gnn_models import (
    GraphSAGEMuleDetector, GraphSAGEConfig, TemporalGraphNetwork, TemporalGNNConfig,
    build_graph_from_transactions, create_temporal_graph_data, compute_graph_metrics
)

LOGGER = logging.getLogger("aegis.training.gnn")

try:
    from torch_geometric.data import Data, Batch
    from torch_geometric.loader import DataLoader as PyGDataLoader
    PYG_AVAILABLE = True
except ImportError:
    PYG_AVAILABLE = False
    LOGGER.warning("PyTorch Geometric not available. GNN training will not work.")


def train_graphsage_model(graph_data, config: AppConfig) -> Dict[str, Path]:
    """Train GraphSAGE model for mule account detection.
    
    Args:
        graph_data: PyTorch Geometric Data object
        config: Application configuration
        
    Returns:
        Dictionary of saved model artifacts
    """
    if not PYG_AVAILABLE:
        LOGGER.warning("PyTorch Geometric not available, skipping GraphSAGE training")
        return {}
    
    LOGGER.info("Training GraphSAGE model for mule detection")
    
    # Model configuration
    model_config = GraphSAGEConfig(
        num_node_features=graph_data.x.size(1),
        hidden_channels=64,
        num_layers=3,
        dropout=0.3
    )
    
    # Initialize model
    model = GraphSAGEMuleDetector(model_config)
    optimizer = torch.optim.Adam(model.parameters(), lr=model_config.learning_rate, 
                                weight_decay=model_config.weight_decay)
    criterion = torch.nn.BCELoss()
    
    # Split data
    num_nodes = graph_data.x.size(0)
    train_mask = torch.zeros(num_nodes, dtype=torch.bool)
    val_mask = torch.zeros(num_nodes, dtype=torch.bool)
    test_mask = torch.zeros(num_nodes, dtype=torch.bool)
    
    # Create stratified split based on labels
    labels = graph_data.y.squeeze().numpy()
    train_indices, temp_indices = train_test_split(
        np.arange(num_nodes), test_size=0.4, stratify=labels, random_state=config.random_state
    )
    val_indices, test_indices = train_test_split(
        temp_indices, test_size=0.5, stratify=labels[temp_indices], random_state=config.random_state
    )
    
    train_mask[train_indices] = True
    val_mask[val_indices] = True
    test_mask[test_indices] = True
    
    # Training loop
    best_val_auc = 0.0
    best_model_state = None
    patience = 10
    patience_counter = 0
    
    for epoch in range(100):
        model.train()
        optimizer.zero_grad()
        
        # Forward pass
        out = model(graph_data.x, graph_data.edge_index)
        loss = criterion(out[train_mask], graph_data.y[train_mask])
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Validation
        if epoch % 10 == 0:
            model.eval()
            with torch.no_grad():
                val_out = model(graph_data.x, graph_data.edge_index)
                val_loss = criterion(val_out[val_mask], graph_data.y[val_mask])
                
                # Calculate metrics
                val_pred = val_out[val_mask].cpu().numpy()
                val_true = graph_data.y[val_mask].cpu().numpy()
                
                if len(np.unique(val_true)) > 1:  # Check if we have both classes
                    val_auc = roc_auc_score(val_true, val_pred)
                    
                    if val_auc > best_val_auc:
                        best_val_auc = val_auc
                        best_model_state = model.state_dict().copy()
                        patience_counter = 0
                    else:
                        patience_counter += 1
                    
                    LOGGER.info("Epoch %d: Train Loss: %.4f, Val Loss: %.4f, Val AUC: %.4f", 
                               epoch, loss.item(), val_loss.item(), val_auc)
                    
                    if patience_counter >= patience:
                        LOGGER.info("Early stopping at epoch %d", epoch)
                        break
    
    # Load best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    # Final evaluation
    model.eval()
    with torch.no_grad():
        test_out = model(graph_data.x, graph_data.edge_index)
        test_pred = test_out[test_mask].cpu().numpy()
        test_true = graph_data.y[test_mask].cpu().numpy()
        
        if len(np.unique(test_true)) > 1:
            test_auc = roc_auc_score(test_true, test_pred)
            test_ap = average_precision_score(test_true, test_pred)
            test_f1 = f1_score(test_true, (test_pred > 0.5).astype(int))
            test_precision = precision_score(test_true, (test_pred > 0.5).astype(int), zero_division=0)
            test_recall = recall_score(test_true, (test_pred > 0.5).astype(int))
            
            metrics = {
                'test_auc': test_auc,
                'test_ap': test_ap,
                'test_f1': test_f1,
                'test_precision': test_precision,
                'test_recall': test_recall,
                'best_val_auc': best_val_auc
            }
            
            LOGGER.info("GraphSAGE Final - AUC: %.3f | AP: %.3f | F1: %.3f | P: %.3f | R: %.3f",
                       test_auc, test_ap, test_f1, test_precision, test_recall)
        else:
            LOGGER.warning("Only one class in test set, cannot compute metrics")
            metrics = {'test_auc': 0.0, 'test_ap': 0.0, 'test_f1': 0.0, 
                      'test_precision': 0.0, 'test_recall': 0.0, 'best_val_auc': best_val_auc}
    
    # Save artifacts
    artifact_dir = config.output_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = artifact_dir / "aegis_graphsage_mule_detector.pt"
    config_path = artifact_dir / "aegis_graphsage_config.json"
    metrics_path = config.output_dir / "graphsage_metrics.json"
    
    torch.save({
        'state_dict': model.state_dict(),
        'config': model_config.__dict__,
        'graph_metrics': compute_graph_metrics(graph_data)
    }, model_path)
    
    import json
    config_path.write_text(json.dumps(model_config.__dict__, indent=2))
    metrics_path.write_text(json.dumps(metrics, indent=2))
    
    return {
        'graphsage_model': model_path,
        'graphsage_config': config_path,
        'graphsage_metrics': metrics_path,
    }


def train_temporal_gnn_model(temporal_graphs: List[Data], config: AppConfig) -> Dict[str, Path]:
    """Train Temporal GNN model for transaction flow analysis.
    
    Args:
        temporal_graphs: List of temporal graph data
        config: Application configuration
        
    Returns:
        Dictionary of saved model artifacts
    """
    if not PYG_AVAILABLE or not temporal_graphs:
        LOGGER.warning("PyTorch Geometric not available or no temporal graphs, skipping Temporal GNN training")
        return {}
    
    LOGGER.info("Training Temporal GNN model with %d time windows", len(temporal_graphs))
    
    # Model configuration
    model_config = TemporalGNNConfig(
        num_features=temporal_graphs[0].x.size(1),
        hidden_dim=128,
        num_heads=4,
        num_layers=2,
        dropout=0.3
    )
    
    # Initialize model
    model = TemporalGraphNetwork(model_config)
    optimizer = torch.optim.Adam(model.parameters(), lr=model_config.learning_rate,
                                weight_decay=model_config.weight_decay)
    criterion = torch.nn.BCELoss()
    
    # Prepare temporal sequences
    sequences = []
    labels = []
    
    for graph in temporal_graphs:
        if graph.x.size(0) > 0:
            # Use node features as sequence (simplified - in practice you'd have time series)
            seq = graph.x.unsqueeze(0)  # Add batch dimension
            sequences.append(seq)
            labels.append(graph.y.mean().item())  # Graph-level label
    
    if not sequences:
        LOGGER.warning("No valid sequences for temporal GNN training")
        return {}
    
    # Convert to tensors
    X = torch.cat(sequences, dim=0)
    y = torch.tensor(labels, dtype=torch.float).unsqueeze(1)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.test_size, random_state=config.random_state
    )
    
    # Training loop
    best_test_auc = 0.0
    best_model_state = None
    patience = 10
    patience_counter = 0
    
    for epoch in range(50):
        model.train()
        optimizer.zero_grad()
        
        # Forward pass (using first graph's edge structure for all)
        edge_index = temporal_graphs[0].edge_index
        out = model(X_train, edge_index)
        loss = criterion(out, y_train)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Validation
        if epoch % 5 == 0:
            model.eval()
            with torch.no_grad():
                test_out = model(X_test, edge_index)
                test_loss = criterion(test_out, y_test)
                
                # Calculate metrics
                test_pred = test_out.cpu().numpy()
                test_true = y_test.cpu().numpy()
                
                if len(np.unique(test_true)) > 1:
                    test_auc = roc_auc_score(test_true, test_pred)
                    
                    if test_auc > best_test_auc:
                        best_test_auc = test_auc
                        best_model_state = model.state_dict().copy()
                        patience_counter = 0
                    else:
                        patience_counter += 1
                    
                    LOGGER.info("Epoch %d: Train Loss: %.4f, Test Loss: %.4f, Test AUC: %.4f",
                               epoch, loss.item(), test_loss.item(), test_auc)
                    
                    if patience_counter >= patience:
                        LOGGER.info("Early stopping at epoch %d", epoch)
                        break
    
    # Load best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    # Final evaluation
    model.eval()
    with torch.no_grad():
        final_out = model(X_test, edge_index)
        final_pred = final_out.cpu().numpy()
        final_true = y_test.cpu().numpy()
        
        if len(np.unique(final_true)) > 1:
            final_auc = roc_auc_score(final_true, final_pred)
            final_ap = average_precision_score(final_true, final_pred)
            final_f1 = f1_score(final_true, (final_pred > 0.5).astype(int))
            final_precision = precision_score(final_true, (final_pred > 0.5).astype(int), zero_division=0)
            final_recall = recall_score(final_true, (final_pred > 0.5).astype(int))
            
            metrics = {
                'test_auc': final_auc,
                'test_ap': final_ap,
                'test_f1': final_f1,
                'test_precision': final_precision,
                'test_recall': final_recall,
                'best_test_auc': best_test_auc
            }
            
            LOGGER.info("Temporal GNN Final - AUC: %.3f | AP: %.3f | F1: %.3f | P: %.3f | R: %.3f",
                       final_auc, final_ap, final_f1, final_precision, final_recall)
        else:
            LOGGER.warning("Only one class in test set, cannot compute metrics")
            metrics = {'test_auc': 0.0, 'test_ap': 0.0, 'test_f1': 0.0,
                      'test_precision': 0.0, 'test_recall': 0.0, 'best_test_auc': best_test_auc}
    
    # Save artifacts
    artifact_dir = config.output_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = artifact_dir / "aegis_temporal_gnn.pt"
    config_path = artifact_dir / "aegis_temporal_gnn_config.json"
    metrics_path = config.output_dir / "temporal_gnn_metrics.json"
    
    torch.save({
        'state_dict': model.state_dict(),
        'config': model_config.__dict__,
        'num_sequences': len(sequences)
    }, model_path)
    
    import json
    config_path.write_text(json.dumps(model_config.__dict__, indent=2))
    metrics_path.write_text(json.dumps(metrics, indent=2))
    
    return {
        'temporal_gnn_model': model_path,
        'temporal_gnn_config': config_path,
        'temporal_gnn_metrics': metrics_path,
    }


def train_gnn_models(transactions_df: pd.DataFrame, accounts_df: pd.DataFrame, 
                    config: AppConfig) -> Dict[str, Path]:
    """Train all GNN models for fraud detection.
    
    Args:
        transactions_df: DataFrame with transaction data
        accounts_df: DataFrame with account data
        config: Application configuration
        
    Returns:
        Dictionary of saved model artifacts
    """
    if not PYG_AVAILABLE:
        LOGGER.warning("PyTorch Geometric not available, skipping GNN training")
        return {}
    
    LOGGER.info("Starting GNN model training pipeline")
    
    artifacts = {}
    
    try:
        # Build graph from transactions
        LOGGER.info("Building transaction graph")
        graph_data = build_graph_from_transactions(transactions_df, accounts_df)
        
        # Compute and log graph metrics
        graph_metrics = compute_graph_metrics(graph_data)
        LOGGER.info("Graph metrics: %s", graph_metrics)
        
        # Train GraphSAGE model
        graphsage_artifacts = train_graphsage_model(graph_data, config)
        artifacts.update(graphsage_artifacts)
        
        # Create temporal graphs and train Temporal GNN
        LOGGER.info("Creating temporal graph data")
        temporal_graphs = create_temporal_graph_data(transactions_df, accounts_df)
        
        if temporal_graphs:
            temporal_artifacts = train_temporal_gnn_model(temporal_graphs, config)
            artifacts.update(temporal_artifacts)
        else:
            LOGGER.warning("No temporal graphs created, skipping Temporal GNN training")
        
        LOGGER.info("GNN training completed successfully")
        
    except Exception as e:
        LOGGER.error("GNN training failed: %s", e, exc_info=True)
        raise
    
    return artifacts


def evaluate_gnn_models(artifacts: Dict[str, Path], transactions_df: pd.DataFrame,
                       accounts_df: pd.DataFrame, config: AppConfig) -> Dict[str, float]:
    """Evaluate trained GNN models.
    
    Args:
        artifacts: Dictionary of model artifacts
        transactions_df: DataFrame with transaction data
        accounts_df: DataFrame with account data
        config: Application configuration
        
    Returns:
        Dictionary of evaluation metrics
    """
    if not PYG_AVAILABLE:
        return {}
    
    LOGGER.info("Evaluating GNN models")
    
    results = {}
    
    try:
        # Build test graph
        graph_data = build_graph_from_transactions(transactions_df, accounts_df)
        
        # Evaluate GraphSAGE if available
        graphsage_path = artifacts.get('graphsage_model')
        if graphsage_path and graphsage_path.exists():
            LOGGER.info("Evaluating GraphSAGE model")
            
            # Load model
            checkpoint = torch.load(graphsage_path, map_location=torch.device('cpu'))
            model_config = GraphSAGEConfig(**checkpoint['config'])
            model = GraphSAGEMuleDetector(model_config)
            model.load_state_dict(checkpoint['state_dict'])
            model.eval()
            
            # Evaluate
            with torch.no_grad():
                predictions = model(graph_data.x, graph_data.edge_index)
                pred_np = predictions.cpu().numpy()
                true_np = graph_data.y.cpu().numpy()
                
                if len(np.unique(true_np)) > 1:
                    auc = roc_auc_score(true_np, pred_np)
                    ap = average_precision_score(true_np, pred_np)
                    f1 = f1_score(true_np, (pred_np > 0.5).astype(int))
                    
                    results['graphsage_auc'] = auc
                    results['graphsage_ap'] = ap
                    results['graphsage_f1'] = f1
                    
                    LOGGER.info("GraphSAGE Evaluation - AUC: %.3f | AP: %.3f | F1: %.3f", auc, ap, f1)
        
        # Evaluate Temporal GNN if available
        temporal_path = artifacts.get('temporal_gnn_model')
        if temporal_path and temporal_path.exists():
            LOGGER.info("Evaluating Temporal GNN model")
            
            # Load model
            checkpoint = torch.load(temporal_path, map_location=torch.device('cpu'))
            model_config = TemporalGNNConfig(**checkpoint['config'])
            model = TemporalGraphNetwork(model_config)
            model.load_state_dict(checkpoint['state_dict'])
            model.eval()
            
            # Create temporal sequences for evaluation
            temporal_graphs = create_temporal_graph_data(transactions_df, accounts_df)
            
            if temporal_graphs:
                sequences = []
                labels = []
                
                for graph in temporal_graphs:
                    if graph.x.size(0) > 0:
                        seq = graph.x.unsqueeze(0)
                        sequences.append(seq)
                        labels.append(graph.y.mean().item())
                
                if sequences:
                    X = torch.cat(sequences, dim=0)
                    y = torch.tensor(labels, dtype=torch.float).unsqueeze(1)
                    edge_index = temporal_graphs[0].edge_index
                    
                    with torch.no_grad():
                        predictions = model(X, edge_index)
                        pred_np = predictions.cpu().numpy()
                        true_np = y.cpu().numpy()
                        
                        if len(np.unique(true_np)) > 1:
                            auc = roc_auc_score(true_np, pred_np)
                            ap = average_precision_score(true_np, pred_np)
                            f1 = f1_score(true_np, (pred_np > 0.5).astype(int))
                            
                            results['temporal_gnn_auc'] = auc
                            results['temporal_gnn_ap'] = ap
                            results['temporal_gnn_f1'] = f1
                            
                            LOGGER.info("Temporal GNN Evaluation - AUC: %.3f | AP: %.3f | F1: %.3f", auc, ap, f1)
        
    except Exception as e:
        LOGGER.error("GNN evaluation failed: %s", e, exc_info=True)
    
    return results

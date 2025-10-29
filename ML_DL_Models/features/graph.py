from __future__ import annotations

from typing import Tuple

import networkx as nx
import pandas as pd

from .utils import bool_to_int, safe_ratio


def build_graph_features(transactions: pd.DataFrame, accounts: pd.DataFrame) -> Tuple[pd.DataFrame, nx.DiGraph]:
    edges = transactions[[
        "source_account_id",
        "destination_account_id",
        "amount",
        "transaction_id",
    ]].dropna(subset=["source_account_id", "destination_account_id"])

    graph = nx.from_pandas_edgelist(
        edges,
        source="source_account_id",
        target="destination_account_id",
        edge_attr=["amount", "transaction_id"],
        create_using=nx.DiGraph(),
    )

    if graph.number_of_nodes() == 0:
        df = accounts[["account_id", "customer_id", "is_mule_account"]].copy()
        for col in [
            "in_degree",
            "out_degree",
            "total_degree",
            "pagerank_centrality",
            "betweenness_centrality",
            "in_flow",
            "out_flow",
            "flow_ratio",
            "avg_transaction_amount",
        ]:
            df[col] = 0.0
        return df, graph

    pagerank_scores = nx.pagerank(graph, max_iter=100)
    betweenness_scores = nx.betweenness_centrality(graph, k=min(200, len(graph.nodes())))
    in_degrees = dict(graph.in_degree())
    out_degrees = dict(graph.out_degree())

    in_flow = {
        node: sum(data["amount"] for _, _, data in graph.in_edges(node, data=True))
        for node in graph.nodes
    }
    out_flow = {
        node: sum(data["amount"] for _, _, data in graph.out_edges(node, data=True))
        for node in graph.nodes
    }

    records = []
    for account_id in accounts["account_id"]:
        in_deg = in_degrees.get(account_id, 0)
        out_deg = out_degrees.get(account_id, 0)
        in_amt = in_flow.get(account_id, 0.0)
        out_amt = out_flow.get(account_id, 0.0)
        total_deg = in_deg + out_deg

        records.append(
            {
                "account_id": account_id,
                "in_degree": in_deg,
                "out_degree": out_deg,
                "total_degree": total_deg,
                "pagerank_centrality": pagerank_scores.get(account_id, 0.0),
                "betweenness_centrality": betweenness_scores.get(account_id, 0.0),
                "in_flow": in_amt,
                "out_flow": out_amt,
                "flow_ratio": safe_ratio(pd.Series([out_amt]), pd.Series([in_amt])).iloc[0],
                "avg_transaction_amount": safe_ratio(pd.Series([in_amt + out_amt]), pd.Series([total_deg])).iloc[0],
            }
        )

    network_df = pd.DataFrame.from_records(records)
    features = accounts[["account_id", "customer_id", "is_mule_account"]].merge(network_df, on="account_id", how="left")
    features = features.fillna(0.0)
    features["is_mule_account"] = bool_to_int(features["is_mule_account"])
    return features, graph



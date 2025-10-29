from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd

from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import IsolationForest, RandomForestClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

import lightgbm as lgb
import networkx as nx
import xgboost as xgb

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset

    TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    TORCH_AVAILABLE = False

try:
    import shap

    SHAP_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    SHAP_AVAILABLE = False


# ---------------------------------------------------------------------------
# Configuration & Logging
# ---------------------------------------------------------------------------


def build_logger(verbose: bool = True) -> logging.Logger:
    logger = logging.getLogger("aegis_training")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO if verbose else logging.WARNING)
    return logger


LOGGER = build_logger()


@dataclass
class TrainingConfig:
    data_dir: Path
    output_dir: Path
    random_state: int = 42
    test_size: float = 0.2
    enable_deep_learning: bool = True
    shap_sample: int = 1000
    shap_background: int = 1000

    def ensure_paths(self) -> None:
        self.data_dir = self.data_dir.resolve()
        if not self.data_dir.exists():
            raise FileNotFoundError(
                f"Dataset directory not found at {self.data_dir}. "
                "Please stage the ML SDV datasets before running training."
            )

        self.output_dir = self.output_dir.resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "logs").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "artifacts").mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------


def load_datasets(config: TrainingConfig) -> Dict[str, pd.DataFrame]:
    data_dir = config.data_dir
    metadata_path = data_dir / "aegis_metadata.json"

    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Metadata file missing: {metadata_path}. Ensure dataset generation has been run."
        )

    LOGGER.info("Loading datasets from %s", data_dir)
    with metadata_path.open("r", encoding="utf-8") as meta_file:
        metadata = json.load(meta_file)

    def _load_csv(filename: str) -> pd.DataFrame:
        path = data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Required dataset not found: {path}")
        df = pd.read_csv(path)
        LOGGER.info("   ✓ Loaded %s (%s rows)", filename, f"{len(df):,}")
        return df

    datasets = {
        "customers": _load_csv("synthetic_aegis_customers.csv"),
        "accounts": _load_csv("synthetic_aegis_accounts.csv"),
        "transactions": _load_csv("synthetic_aegis_transactions.csv"),
        "call_history": _load_csv("synthetic_aegis_call_history.csv"),
        "behavioral_events": _load_csv("synthetic_aegis_behavioral_events.csv"),
        "fraud_alerts": _load_csv("synthetic_aegis_fraud_alerts.csv"),
        "metadata": metadata,
    }

    # Validate schemas using metadata definitions
    def _validate(df: pd.DataFrame, key: str) -> None:
        expected_cols = set(metadata["tables"][key]["columns"].keys())
        df_cols = set(df.columns)
        missing = expected_cols - df_cols
        if missing:
            raise ValueError(f"{key} missing expected columns: {sorted(missing)}")
        extra = df_cols - expected_cols
        if extra:
            LOGGER.warning("%s has unexpected columns: %s", key, sorted(extra))

    _validate(datasets["customers"], "aegis_customers")
    _validate(datasets["accounts"], "aegis_accounts")
    _validate(datasets["transactions"], "aegis_transactions")
    _validate(datasets["call_history"], "aegis_call_history")
    _validate(datasets["behavioral_events"], "aegis_behavioral_events")
    _validate(datasets["fraud_alerts"], "aegis_fraud_alerts")

    fraud_rate = datasets["transactions"]["is_fraud"].mean()
    LOGGER.info("   - Dataset fraud rate: %.2f%%", fraud_rate * 100)

    return datasets


# ---------------------------------------------------------------------------
# Feature Engineering
# ---------------------------------------------------------------------------


class AegisFeatureEngine:
    def __init__(self):
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.standard_zero_fill_cols = [
            "total_balance",
            "avg_balance",
            "std_amount",
            "avg_risk_score",
            "anomaly_score",
        ]

    # --- Helpers -----------------------------------------------------------------
    @staticmethod
    def _bool_to_int(series: pd.Series) -> pd.Series:
        return series.astype(str).str.lower().isin(["true", "1", "yes", "y"]).astype(int)

    @staticmethod
    def _ensure_numeric(df: pd.DataFrame, columns: List[str]) -> None:
        for col in columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # --- Customer-Level Feature Engineering --------------------------------------
    def create_customer_features(
        self,
        customers_df: pd.DataFrame,
        accounts_df: pd.DataFrame,
        transactions_df: pd.DataFrame,
        call_history_df: Optional[pd.DataFrame] = None,
        fraud_alerts_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        LOGGER.info("   Creating customer-level features ...")
        customers_df = customers_df.copy()
        accounts_df = accounts_df.copy()
        transactions_df = transactions_df.copy()

        self._ensure_numeric(customers_df, ["annual_income", "credit_score", "vulnerability_score"])
        self._ensure_numeric(accounts_df, ["balance", "daily_limit", "monthly_limit"])
        self._ensure_numeric(transactions_df, ["amount", "risk_score"])

        for col in ["known_device", "ctr_flag", "sar_flag"]:
            if col in transactions_df.columns:
                transactions_df[col] = self._bool_to_int(transactions_df[col])

        customers_df["age"] = (
            datetime.now() - pd.to_datetime(customers_df["date_of_birth"], errors="coerce")
        ).dt.days.div(365.25)
        customers_df["age"] = (
            customers_df["age"].fillna(customers_df["age"].median()).clip(lower=18, upper=100)
        )

        customers_df["customer_tenure_years"] = (
            datetime.now() - pd.to_datetime(customers_df["onboarding_date"], errors="coerce")
        ).dt.days.div(365.25).fillna(0).clip(lower=0)

        account_aggs = accounts_df.groupby("customer_id").agg(
            account_count=("account_id", "count"),
            total_balance=("balance", "sum"),
            avg_balance=("balance", "mean"),
            max_balance=("balance", "max"),
            balance_std=("balance", "std"),
            max_daily_limit=("daily_limit", "max"),
            max_monthly_limit=("monthly_limit", "max"),
            mule_account_count=("is_mule_account", lambda x: self._bool_to_int(x).sum()),
        ).reset_index().fillna(0)

        txn_aggs = transactions_df.groupby("customer_id").agg(
            txn_count=("transaction_id", "count"),
            total_amount=("amount", "sum"),
            avg_amount=("amount", "mean"),
            std_amount=("amount", "std"),
            max_amount=("amount", "max"),
            min_amount=("amount", "min"),
            fraud_count=("is_fraud", "sum"),
            fraud_rate=("is_fraud", "mean"),
            avg_risk_score=("risk_score", "mean"),
            max_risk_score=("risk_score", "max"),
            known_device_rate=("known_device", "mean"),
            ctr_count=("ctr_flag", "sum"),
            sar_count=("sar_flag", "sum"),
        ).reset_index().fillna(0)

        customer_features = customers_df.merge(account_aggs, on="customer_id", how="left")
        customer_features = customer_features.merge(txn_aggs, on="customer_id", how="left")

        if call_history_df is not None and not call_history_df.empty:
            customer_features = customer_features.merge(
                self._merge_call_history_customer(call_history_df), on="customer_id", how="left"
            )

        if fraud_alerts_df is not None and not fraud_alerts_df.empty:
            customer_features = customer_features.merge(
                self._merge_fraud_alerts_customer(fraud_alerts_df), on="customer_id", how="left"
            )

        for optional_col in [
            "total_calls",
            "alert_count",
            "avg_escalation_level",
            "avg_false_positive_prob",
        ]:
            if optional_col not in customer_features.columns:
                customer_features[optional_col] = 0.0

        numeric_cols = customer_features.select_dtypes(include=[np.number]).columns
        customer_features[numeric_cols] = customer_features[numeric_cols].fillna(0)

        customer_features["balance_to_income_ratio"] = (
            customer_features["total_balance"] / (customer_features["annual_income"] + 1)
        )
        customer_features["avg_txn_to_balance_ratio"] = (
            customer_features["avg_amount"] / (customer_features["avg_balance"] + 1)
        )
        customer_features["risk_velocity"] = (
            customer_features["fraud_count"] / (customer_features["txn_count"] + 1)
        )
        customer_features["mule_account_ratio"] = (
            customer_features["mule_account_count"] / (customer_features["account_count"] + 1)
        )
        customer_features["accounts_per_year"] = (
            customer_features["account_count"] / (customer_features["customer_tenure_years"] + 0.1)
        )
        customer_features["txn_per_month"] = (
            customer_features["txn_count"] / (customer_features["customer_tenure_years"] * 12 + 1)
        )
        customer_features["alert_to_txn_ratio"] = (
            customer_features["alert_count"] / (customer_features["txn_count"] + 1)
        )
        customer_features["escalated_alert_ratio"] = (
            customer_features["avg_escalation_level"] / (customer_features["alert_count"] + 1)
        )
        customer_features["call_to_txn_ratio"] = (
            customer_features["total_calls"] / (customer_features["txn_count"] + 1)
        )
        customer_features["avg_alert_false_positive"] = customer_features[
            "avg_false_positive_prob"
        ]

        return customer_features

    # --- Transaction-Level Feature Engineering ----------------------------------
    def create_transaction_features(
        self,
        transactions_df: pd.DataFrame,
        customers_df: pd.DataFrame,
        behavioral_events_df: pd.DataFrame,
        accounts_df: Optional[pd.DataFrame] = None,
        call_history_df: Optional[pd.DataFrame] = None,
        fraud_alerts_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        LOGGER.info("   Creating transaction-level features ...")
        transactions_df = transactions_df.copy()
        self._ensure_numeric(transactions_df, ["amount", "risk_score"])

        for col in ["known_device", "is_flagged", "ctr_flag", "sar_flag"]:
            if col in transactions_df.columns:
                transactions_df[col] = self._bool_to_int(transactions_df[col])

        transactions_df["transaction_datetime"] = pd.to_datetime(
            transactions_df["transaction_date"] + " " + transactions_df["transaction_time"]
        )
        transactions_df["hour"] = transactions_df["transaction_datetime"].dt.hour
        transactions_df["day_of_week"] = transactions_df["transaction_datetime"].dt.dayofweek
        transactions_df["is_weekend"] = transactions_df["day_of_week"].isin([5, 6]).astype(int)
        transactions_df["is_night"] = transactions_df["hour"].isin(list(range(22, 24)) + list(range(0, 6))).astype(int)
        transactions_df["log_amount"] = np.log1p(transactions_df["amount"])
        transactions_df["is_round_amount"] = (
            (transactions_df["amount"] % 100 == 0) & (transactions_df["amount"] > 0)
        ).astype(int)
        transactions_df["is_business_hours"] = transactions_df["hour"].between(8, 18).astype(int)
        transactions_df["sin_hour"] = np.sin(2 * np.pi * transactions_df["hour"] / 24)
        transactions_df["cos_hour"] = np.cos(2 * np.pi * transactions_df["hour"] / 24)
        transactions_df["sin_day_of_week"] = np.sin(
            2 * np.pi * transactions_df["day_of_week"] / 7
        )
        transactions_df["cos_day_of_week"] = np.cos(
            2 * np.pi * transactions_df["day_of_week"] / 7
        )

        enriched_customer_cols = [
            "customer_id",
            "age",
            "annual_income",
            "is_vulnerable",
            "vulnerability_score",
            "credit_score",
            "digital_literacy_level",
            "risk_profile",
            "customer_tenure_years",
            "txn_per_month",
            "alert_to_txn_ratio",
            "call_to_txn_ratio",
            "risk_velocity",
            "avg_risk_score",
            "max_risk_score",
            "known_device_rate",
        ]

        transactions_df = transactions_df.merge(
            customers_df[[c for c in enriched_customer_cols if c in customers_df.columns]],
            on="customer_id",
            how="left",
        )

        if "is_vulnerable" in transactions_df.columns:
            transactions_df["is_vulnerable"] = self._bool_to_int(
                transactions_df["is_vulnerable"]
            )

        if accounts_df is not None and not accounts_df.empty:
            accounts_subset = accounts_df[[
                "account_id",
                "daily_limit",
                "monthly_limit",
                "is_mule_account",
                "customer_id",
            ]].copy()
            self._ensure_numeric(accounts_subset, ["daily_limit", "monthly_limit"])
            accounts_subset["is_mule_account"] = self._bool_to_int(accounts_subset["is_mule_account"])

            source_accounts = accounts_subset.rename(
                columns={
                    "account_id": "source_account_id",
                    "daily_limit": "source_daily_limit",
                    "monthly_limit": "source_monthly_limit",
                    "is_mule_account": "source_is_mule_account",
                }
            )
            dest_accounts = accounts_subset.rename(
                columns={
                    "account_id": "destination_account_id",
                    "daily_limit": "destination_daily_limit",
                    "monthly_limit": "destination_monthly_limit",
                    "is_mule_account": "destination_is_mule_account",
                }
            )

            transactions_df = transactions_df.merge(source_accounts, on="source_account_id", how="left")
            transactions_df = transactions_df.merge(dest_accounts, on="destination_account_id", how="left")

            transactions_df["amount_to_daily_limit_ratio"] = transactions_df["amount"] / (
                transactions_df["source_daily_limit"] + 1
            )
            transactions_df["amount_to_monthly_limit_ratio"] = transactions_df["amount"] / (
                transactions_df["source_monthly_limit"] + 1
            )

        risk_map = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        for col in ["location_risk", "amount_risk", "velocity_risk"]:
            if col in transactions_df.columns:
                transactions_df[f"{col}_score"] = (
                    transactions_df[col].astype(str).str.lower().map(risk_map).fillna(0)
                )

        if behavioral_events_df is not None and not behavioral_events_df.empty:
            behavioral_aggs = behavioral_events_df.groupby("transaction_id").agg(
                anomaly_score=("anomaly_score", "mean"),
                hesitation_indicators=("hesitation_indicators", "sum"),
                typing_pattern_anomaly=("typing_pattern_anomaly", "mean"),
                copy_paste_detected=("copy_paste_detected", "max"),
                new_payee_flag=("new_payee_flag", "max"),
                authentication_failures=("authentication_failures", "sum"),
            ).reset_index()
            transactions_df = transactions_df.merge(behavioral_aggs, on="transaction_id", how="left")

        if call_history_df is not None and not call_history_df.empty:
            transactions_df = self._merge_call_history_transaction(transactions_df, call_history_df)

        if fraud_alerts_df is not None and not fraud_alerts_df.empty:
            transactions_df = self._merge_fraud_alerts_transaction(transactions_df, fraud_alerts_df)

        if "avg_amount" in transactions_df.columns:
            transactions_df["relative_amount_to_avg"] = (
                transactions_df["amount"]
                / transactions_df["avg_amount"].replace({0: np.nan})
            ).replace([np.inf, -np.inf], 0).fillna(0)
        else:
            transactions_df["relative_amount_to_avg"] = 0.0

        transactions_df["risk_score_gap"] = (
            transactions_df.get("risk_score", 0) - transactions_df.get("avg_risk_score", 0)
        )
        transactions_df["device_trust_gap"] = (
            transactions_df.get("known_device", 0) - transactions_df.get("known_device_rate", 0)
        )

        fill_cols = [col for col in self.standard_zero_fill_cols if col in transactions_df.columns]
        transactions_df[fill_cols] = transactions_df[fill_cols].fillna(0)

        numeric_cols = transactions_df.select_dtypes(include=[np.number]).columns
        transactions_df[numeric_cols] = transactions_df[numeric_cols].fillna(0)

        if accounts_df is not None and not accounts_df.empty:
            customer_network_stats = accounts_df.groupby("customer_id").agg(
                source_mule_account_rate=("is_mule_account", lambda x: self._bool_to_int(x).mean()),
            ).reset_index()
            transactions_df = transactions_df.merge(
                customer_network_stats, on="customer_id", how="left"
            )
            transactions_df["source_mule_account_rate"] = transactions_df[
                "source_mule_account_rate"
            ].fillna(0)

        return transactions_df

    # --- Network Feature Engineering --------------------------------------------
    def create_network_features(
        self, transactions_df: pd.DataFrame, accounts_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, nx.DiGraph]:
        LOGGER.info("   Creating network/graph features ...")
        edges = transactions_df[[
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
            zero_df = accounts_df[["account_id", "customer_id", "is_mule_account"]].copy()
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
                zero_df[col] = 0.0
            return zero_df, graph

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

        def _safe_ratio(numerator: float, denominator: float) -> float:
            denominator = denominator if denominator != 0 else 1e-6
            return numerator / denominator

        records = []
        for account_id in accounts_df["account_id"]:
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
                    "flow_ratio": _safe_ratio(out_amt, in_amt),
                    "avg_transaction_amount": _safe_ratio(in_amt + out_amt, total_deg),
                }
            )

        network_df = pd.DataFrame.from_records(records)
        network_features = accounts_df[["account_id", "customer_id", "is_mule_account"]].merge(
            network_df, on="account_id", how="left"
        )
        network_features = network_features.fillna(0.0)
        return network_features, graph

    # --- Aggregation Helpers ----------------------------------------------------
    def _merge_call_history_customer(self, call_history_df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {
            "customer_id",
            "call_id",
            "call_date",
            "call_time",
            "call_type",
            "call_outcome_category",
            "call_duration_seconds",
            "resolution_time_hours",
            "call_quality_score",
            "risk_level",
            "escalated",
        }
        if call_history_df is None or call_history_df.empty or not required_cols.issubset(
            call_history_df.columns
        ):
            return pd.DataFrame({"customer_id": []})

        call_history = call_history_df.copy()
        call_history["call_date"] = pd.to_datetime(call_history["call_date"], errors="coerce")
        call_history["call_datetime"] = pd.to_datetime(
            call_history["call_date"].dt.strftime("%Y-%m-%d")
            + " "
            + call_history["call_time"],
            errors="coerce",
        )
        self._ensure_numeric(call_history, ["call_duration_seconds", "resolution_time_hours", "call_quality_score"])
        call_history["is_inbound"] = call_history["call_type"].str.lower().eq("inbound").astype(int)
        call_history["is_escalated"] = self._bool_to_int(call_history["escalated"])
        call_history["outcome_reached"] = call_history["call_outcome_category"].str.lower().eq("customer reached").astype(int)
        call_history["is_high_risk_call"] = call_history["risk_level"].str.lower().eq("high").astype(int)

        call_aggs = call_history.groupby("customer_id").agg(
            total_calls=("call_id", "count"),
            inbound_call_rate=("is_inbound", "mean"),
            escalated_call_rate=("is_escalated", "mean"),
            outcome_reached_rate=("outcome_reached", "mean"),
            avg_call_duration=("call_duration_seconds", "mean"),
            max_call_duration=("call_duration_seconds", "max"),
            avg_call_quality=("call_quality_score", "mean"),
            avg_resolution_hours=("resolution_time_hours", "mean"),
            high_risk_call_rate=("is_high_risk_call", "mean"),
        ).fillna(0)
        return call_aggs.reset_index()

    def _merge_fraud_alerts_customer(self, fraud_alerts_df: pd.DataFrame) -> pd.DataFrame:
        required_cols = {
            "customer_id",
            "alert_id",
            "priority",
            "status",
            "escalation_level",
            "alert_date",
            "alert_time",
            "risk_score",
            "false_positive_probability",
        }
        if fraud_alerts_df is None or fraud_alerts_df.empty or not required_cols.issubset(
            fraud_alerts_df.columns
        ):
            return pd.DataFrame({"customer_id": []})

        alerts = fraud_alerts_df.copy()
        priority_map = {"critical": 3, "high": 2, "medium": 1, "low": 0}
        status_map = {"open": 0, "closed": 1, "resolved": 1}
        escalation_map = {"l3": 3, "l2": 2, "l1": 1}

        alerts["priority_level"] = alerts["priority"].str.lower().map(priority_map).fillna(1)
        alerts["is_escalated_alert"] = alerts["escalation_level"].str.lower().map(escalation_map).fillna(0)
        alerts["is_closed_alert"] = alerts["status"].str.lower().map(status_map).fillna(0)
        alerts["alert_date"] = pd.to_datetime(alerts["alert_date"], errors="coerce")
        alerts["alert_datetime"] = pd.to_datetime(
            alerts["alert_date"].dt.strftime("%Y-%m-%d") + " " + alerts["alert_time"],
            errors="coerce",
        )

        alert_aggs = alerts.groupby("customer_id").agg(
            alert_count=("alert_id", "count"),
            critical_alert_rate=("priority_level", lambda x: np.mean(x == 3)),
            high_alert_rate=("priority_level", lambda x: np.mean(x >= 2)),
            avg_alert_risk_score=("risk_score", "mean"),
            avg_false_positive_prob=("false_positive_probability", "mean"),
            avg_escalation_level=("is_escalated_alert", "mean"),
            alert_closure_rate=("is_closed_alert", "mean"),
        ).fillna(0)
        return alert_aggs.reset_index()

    def _merge_call_history_transaction(
        self, transaction_features: pd.DataFrame, call_history_df: pd.DataFrame
    ) -> pd.DataFrame:
        required_cols = {
            "transaction_id",
            "call_id",
            "call_date",
            "call_time",
            "call_duration_seconds",
            "resolution_time_hours",
            "escalated",
            "call_outcome_category",
        }
        if call_history_df is None or call_history_df.empty or not required_cols.issubset(
            call_history_df.columns
        ):
            return transaction_features

        call_history = call_history_df.copy()
        call_history["call_date"] = pd.to_datetime(call_history["call_date"], errors="coerce")
        call_history["call_datetime"] = pd.to_datetime(
            call_history["call_date"].dt.strftime("%Y-%m-%d")
            + " "
            + call_history["call_time"],
            errors="coerce",
        )
        self._ensure_numeric(call_history, ["call_duration_seconds", "resolution_time_hours"])
        call_history["is_escalated"] = self._bool_to_int(call_history["escalated"])
        call_history["outcome_reached"] = call_history[
            "call_outcome_category"
        ].str.lower().eq("customer reached").astype(int)

        txn_call_aggs = call_history.groupby("transaction_id").agg(
            txn_call_count=("call_id", "count"),
            txn_escalation_rate=("is_escalated", "mean"),
            txn_outcome_reached_rate=("outcome_reached", "mean"),
            txn_avg_call_duration=("call_duration_seconds", "mean"),
            txn_avg_resolution_hours=("resolution_time_hours", "mean"),
            last_call_datetime=("call_datetime", "max"),
        ).reset_index()

        merged = transaction_features.merge(txn_call_aggs, on="transaction_id", how="left")
        merged["hours_since_last_call"] = (
            merged["transaction_datetime"] - merged["last_call_datetime"]
        ).dt.total_seconds() / 3600
        merged["hours_since_last_call"] = merged["hours_since_last_call"].fillna(0).clip(lower=0)
        merged.drop(columns=["last_call_datetime"], inplace=True)
        return merged

    def _merge_fraud_alerts_transaction(
        self, transaction_features: pd.DataFrame, fraud_alerts_df: pd.DataFrame
    ) -> pd.DataFrame:
        required_cols = {
            "transaction_id",
            "alert_id",
            "priority",
            "alert_date",
            "alert_time",
            "risk_score",
            "false_positive_probability",
        }
        if fraud_alerts_df is None or fraud_alerts_df.empty or not required_cols.issubset(
            fraud_alerts_df.columns
        ):
            return transaction_features

        alerts = fraud_alerts_df.copy()
        priority_map = {"critical": 3, "high": 2, "medium": 1, "low": 0}
        alerts["priority_level"] = alerts["priority"].str.lower().map(priority_map).fillna(1)
        alerts["alert_date"] = pd.to_datetime(alerts["alert_date"], errors="coerce")
        alerts["alert_datetime"] = pd.to_datetime(
            alerts["alert_date"].dt.strftime("%Y-%m-%d") + " " + alerts["alert_time"],
            errors="coerce",
        )

        txn_alert_aggs = alerts.groupby("transaction_id").agg(
            txn_alert_count=("alert_id", "count"),
            txn_high_priority_rate=("priority_level", lambda x: np.mean(x >= 2)),
            txn_avg_alert_risk_score=("risk_score", "mean"),
            txn_avg_false_positive_prob=("false_positive_probability", "mean"),
            last_alert_datetime=("alert_datetime", "max"),
        ).reset_index()

        merged = transaction_features.merge(txn_alert_aggs, on="transaction_id", how="left")
        merged["hours_since_last_alert"] = (
            merged["transaction_datetime"] - merged["last_alert_datetime"]
        ).dt.total_seconds() / 3600
        merged["hours_since_last_alert"] = merged["hours_since_last_alert"].fillna(0).clip(lower=0)
        merged.drop(columns=["last_alert_datetime"], inplace=True)
        return merged

    # --- Encoding ---------------------------------------------------------------
    def encode_categorical_features(
        self, df: pd.DataFrame, categorical_cols: List[str]
    ) -> pd.DataFrame:
        df_encoded = df.copy()
        for col in categorical_cols:
            if col not in df_encoded.columns:
                continue
            values = df_encoded[col].astype(str).fillna("Unknown")
            if col not in self.label_encoders:
                encoder = LabelEncoder()
                encoder.fit(values)
                self.label_encoders[col] = encoder
            encoder = self.label_encoders[col]
            unseen = np.setdiff1d(values.unique(), encoder.classes_)
            if unseen.size > 0:
                encoder.classes_ = np.concatenate([encoder.classes_, unseen])
            df_encoded[f"{col}_encoded"] = encoder.transform(values)
        return df_encoded


# ---------------------------------------------------------------------------
# Model Training Utilities
# ---------------------------------------------------------------------------


def _weighted_scale_pos_weight(y: pd.Series) -> float:
    positives = max(y.sum(), 1)
    negatives = max(len(y) - positives, 1)
    return negatives / positives


def train_mule_models(
    network_features: pd.DataFrame, config: TrainingConfig
) -> Tuple[Dict[str, Any], Dict[str, float]]:
    LOGGER.info("[STEP 3] Training mule detection models ...")
    feature_cols = [
        "in_degree",
        "out_degree",
        "total_degree",
        "pagerank_centrality",
        "betweenness_centrality",
        "in_flow",
        "out_flow",
        "flow_ratio",
        "avg_transaction_amount",
    ]

    X = network_features[feature_cols].fillna(0)
    y = network_features["is_mule_account"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.test_size, stratify=y, random_state=config.random_state
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    iso_forest = IsolationForest(
        contamination=0.05, random_state=config.random_state, n_jobs=-1
    )
    iso_forest.fit(X_train_scaled)

    param_grid = {
        "max_depth": [4, 6, 8],
        "learning_rate": [0.05, 0.1, 0.2],
        "n_estimators": [200, 300, 400],
        "subsample": [0.7, 0.9],
        "colsample_bytree": [0.7, 0.9],
    }

    base_xgb = xgb.XGBClassifier(
        objective="binary:logistic",
        eval_metric="auc",
        random_state=config.random_state,
        n_jobs=-1,
        scale_pos_weight=_weighted_scale_pos_weight(y_train),
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=config.random_state)
    search = RandomizedSearchCV(
        estimator=base_xgb,
        param_distributions=param_grid,
        n_iter=10,
        scoring="roc_auc",
        cv=cv,
        random_state=config.random_state,
        n_jobs=-1,
        verbose=0,
    )
    search.fit(X_train, y_train)
    best_xgb = search.best_estimator_

    calibrated_xgb = CalibratedClassifierCV(best_xgb, method="isotonic", cv=cv)
    calibrated_xgb.fit(X_train, y_train)

    y_pred = calibrated_xgb.predict(X_test)
    y_prob = calibrated_xgb.predict_proba(X_test)[:, 1]

    metrics = {
        "auc": roc_auc_score(y_test, y_prob),
        "average_precision": average_precision_score(y_test, y_prob),
        "f1": f1_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred),
    }
    LOGGER.info(
        "   Mule Detection – AUC: %.3f | AP: %.3f | F1: %.3f",
        metrics["auc"],
        metrics["average_precision"],
        metrics["f1"],
    )

    models = {
        "iso_forest": iso_forest,
        "xgb_calibrated": calibrated_xgb,
        "scaler": scaler,
    }
    return models, metrics


def _prepare_numeric_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    object_cols = df.select_dtypes(include=["object"]).columns
    if len(object_cols) > 0:
        LOGGER.warning("Converting %d object columns to numeric: %s", len(object_cols), list(object_cols))
    df = df.apply(lambda col: pd.to_numeric(col, errors="coerce")).fillna(0)
    return df.astype(np.float32)


def train_fraud_models(
    transaction_features: pd.DataFrame,
    config: TrainingConfig,
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, float]], Optional[np.ndarray]]:
    LOGGER.info("[STEP 4] Training fraud detection models ...")
    categorical_cols = [
        "payment_channel",
        "device_model",
        "ip_address_country",
        "digital_literacy_level",
        "risk_profile",
    ]

    feature_engine = AegisFeatureEngine()
    transaction_features_encoded = feature_engine.encode_categorical_features(
        transaction_features, categorical_cols
    )

    feature_cols = [
        "amount",
        "log_amount",
        "hour",
        "day_of_week",
        "is_weekend",
        "is_night",
        "is_business_hours",
        "is_round_amount",
        "sin_hour",
        "cos_hour",
        "sin_day_of_week",
        "cos_day_of_week",
        "age",
        "annual_income",
        "vulnerability_score",
        "credit_score",
        "customer_tenure_years",
        "txn_per_month",
        "alert_to_txn_ratio",
        "call_to_txn_ratio",
        "risk_velocity",
        "risk_score",
        "risk_score_gap",
        "known_device",
        "device_trust_gap",
        "anomaly_score",
        "hesitation_indicators",
        "typing_pattern_anomaly",
        "copy_paste_detected",
        "new_payee_flag",
        "authentication_failures",
        "txn_call_count",
        "txn_escalation_rate",
        "txn_high_priority_rate",
        "txn_avg_alert_risk_score",
        "txn_avg_false_positive_prob",
        "hours_since_last_alert",
        "hours_since_last_call",
        "relative_amount_to_avg",
        "amount_to_daily_limit_ratio",
        "amount_to_monthly_limit_ratio",
        "location_risk_score",
        "amount_risk_score",
        "velocity_risk_score",
    ] + [f"{col}_encoded" for col in categorical_cols if f"{col}_encoded" in transaction_features_encoded.columns]

    feature_cols = [col for col in feature_cols if col in transaction_features_encoded.columns]
    X = transaction_features_encoded[feature_cols]
    y = transaction_features_encoded["is_fraud"].astype(int)

    X = _prepare_numeric_dataframe(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=config.test_size,
        stratify=y,
        random_state=config.random_state,
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    LOGGER.info("   Tuning XGBoost via RandomizedSearchCV ...")
    xgb_model = xgb.XGBClassifier(
        objective="binary:logistic",
        eval_metric="aucpr",
        random_state=config.random_state,
        n_jobs=-1,
    )
    xgb_param_dist = {
        "max_depth": [6, 8, 10],
        "learning_rate": [0.05, 0.1, 0.2],
        "n_estimators": [300, 400, 500],
        "subsample": [0.7, 0.85, 1.0],
        "colsample_bytree": [0.7, 0.85, 1.0],
        "min_child_weight": [1, 3, 5],
        "gamma": [0, 1, 5],
        "scale_pos_weight": [_weighted_scale_pos_weight(y_train)],
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=config.random_state)
    xgb_search = RandomizedSearchCV(
        xgb_model,
        xgb_param_dist,
        n_iter=15,
        scoring="average_precision",
        cv=cv,
        n_jobs=-1,
        random_state=config.random_state,
        verbose=0,
    )
    xgb_search.fit(X_train, y_train)
    fraud_xgb_best = xgb_search.best_estimator_

    LOGGER.info("   Tuning LightGBM via RandomizedSearchCV ...")
    lgb_model = lgb.LGBMClassifier(
        objective="binary",
        class_weight="balanced",
        random_state=config.random_state,
        n_jobs=-1,
    )
    lgb_param_dist = {
        "num_leaves": [31, 63, 127],
        "max_depth": [-1, 10, 20],
        "learning_rate": [0.05, 0.1, 0.2],
        "n_estimators": [300, 500, 700],
        "subsample": [0.7, 0.9, 1.0],
        "colsample_bytree": [0.7, 0.9, 1.0],
    }
    lgb_search = RandomizedSearchCV(
        lgb_model,
        lgb_param_dist,
        n_iter=15,
        scoring="average_precision",
        cv=cv,
        n_jobs=-1,
        random_state=config.random_state,
        verbose=0,
    )
    lgb_search.fit(X_train, y_train)
    fraud_lgb_best = lgb_search.best_estimator_

    LOGGER.info("   Tuning RandomForest via RandomizedSearchCV ...")
    rf_model = RandomForestClassifier(
        n_estimators=400,
        max_depth=None,
        min_samples_split=5,
        class_weight="balanced_subsample",
        random_state=config.random_state,
        n_jobs=-1,
    )
    rf_param_dist = {
        "n_estimators": [300, 400, 600],
        "max_depth": [12, 18, None],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "max_features": ["sqrt", "log2"],
    }
    rf_search = RandomizedSearchCV(
        rf_model,
        rf_param_dist,
        n_iter=10,
        scoring="average_precision",
        cv=cv,
        n_jobs=-1,
        random_state=config.random_state,
        verbose=0,
    )
    rf_search.fit(X_train, y_train)
    fraud_rf_best = rf_search.best_estimator_

    LOGGER.info("   Calibrating base models ...")
    fraud_xgb_cal = CalibratedClassifierCV(fraud_xgb_best, method="isotonic", cv=cv)
    fraud_lgb_cal = CalibratedClassifierCV(fraud_lgb_best, method="isotonic", cv=cv)
    fraud_rf_cal = CalibratedClassifierCV(fraud_rf_best, method="isotonic", cv=cv)

    fraud_xgb_cal.fit(X_train, y_train)
    fraud_lgb_cal.fit(X_train, y_train)
    fraud_rf_cal.fit(X_train, y_train)

    nn_prob = None
    nn_model = None
    if TORCH_AVAILABLE and config.enable_deep_learning:
        LOGGER.info("   Training deep neural network with early stopping ...")

        class FraudNet(nn.Module):
            def __init__(self, input_size: int):
                super().__init__()
                self.layers = nn.Sequential(
                    nn.Linear(input_size, 512),
                    nn.BatchNorm1d(512),
                    nn.ReLU(),
                    nn.Dropout(0.4),
                    nn.Linear(512, 256),
                    nn.BatchNorm1d(256),
                    nn.ReLU(),
                    nn.Dropout(0.4),
                    nn.Linear(256, 128),
                    nn.BatchNorm1d(128),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(128, 64),
                    nn.BatchNorm1d(64),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(64, 1),
                    nn.Sigmoid(),
                )

            def forward(self, x):
                return self.layers(x)

        X_train_tensor = torch.FloatTensor(X_train_scaled)
        y_train_tensor = torch.FloatTensor(y_train.values.reshape(-1, 1))
        X_test_tensor = torch.FloatTensor(X_test_scaled)

        nn_model = FraudNet(X_train_scaled.shape[1])
        class_weights = torch.tensor([_weighted_scale_pos_weight(y_train)], dtype=torch.float32)
        criterion = nn.BCELoss(weight=class_weights)
        optimizer = optim.Adam(nn_model.parameters(), lr=0.001, weight_decay=1e-5)

        batch_size = 1024
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

        best_loss = float("inf")
        patience = 5
        patience_counter = 0
        best_state: Optional[Dict[str, torch.Tensor]] = None

        nn_model.train()
        for epoch in range(100):
            epoch_loss = 0.0
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = nn_model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()

            epoch_loss /= max(len(train_loader), 1)
            if epoch_loss + 1e-4 < best_loss:
                best_loss = epoch_loss
                patience_counter = 0
                best_state = nn_model.state_dict()
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    LOGGER.info("   Early stopping triggered (best loss %.4f)", best_loss)
                    break

        if best_state is not None:
            nn_model.load_state_dict(best_state)
        nn_model.eval()
        with torch.no_grad():
            nn_prob = nn_model(X_test_tensor).numpy().flatten()

    base_models = {
        "xgb": fraud_xgb_cal,
        "lgb": fraud_lgb_cal,
        "rf": fraud_rf_cal,
    }
    if nn_model is not None:
        base_models["nn"] = nn_model

    ensemble = StackingClassifier(
        estimators=[("xgb", fraud_xgb_cal), ("lgb", fraud_lgb_cal), ("rf", fraud_rf_cal)],
        final_estimator=LogisticRegression(class_weight="balanced", max_iter=1000),
        cv=cv,
        n_jobs=-1,
        passthrough=True,
    )
    ensemble.fit(X_train, y_train)

    models = {
        "base_models": base_models,
        "ensemble": ensemble,
        "scaler": scaler,
        "feature_engine": feature_engine,
        "feature_columns": feature_cols,
        "categorical_columns": categorical_cols,
    }

    LOGGER.info("[STEP 5] Evaluating models ...")
    evaluation_results: Dict[str, Dict[str, float]] = {}
    model_predictions: Dict[str, np.ndarray] = {}

    def _evaluate(name: str, model) -> Dict[str, float]:
        if name == "nn" and nn_prob is not None:
            pred_prob = nn_prob
            pred = (pred_prob > 0.5).astype(int)
        else:
            pred = model.predict(X_test)
            pred_prob = model.predict_proba(X_test)[:, 1]
        evaluation_results[name] = {
            "auc": roc_auc_score(y_test, pred_prob),
            "average_precision": average_precision_score(y_test, pred_prob),
            "f1": f1_score(y_test, pred),
            "precision": precision_score(y_test, pred, zero_division=0),
            "recall": recall_score(y_test, pred),
        }
        model_predictions[name] = pred_prob
        LOGGER.info(
            "   %-20s AUC: %.3f | AP: %.3f | F1: %.3f | P: %.3f | R: %.3f",
            name,
            evaluation_results[name]["auc"],
            evaluation_results[name]["average_precision"],
            evaluation_results[name]["f1"],
            evaluation_results[name]["precision"],
            evaluation_results[name]["recall"],
        )
        return evaluation_results[name]

    for name, model in [
        ("XGBoost", fraud_xgb_cal),
        ("LightGBM", fraud_lgb_cal),
        ("RandomForest", fraud_rf_cal),
        ("Ensemble", ensemble),
    ]:
        _evaluate(name, model)

    if nn_prob is not None:
        evaluation_results["DeepNeuralNetwork"] = {
            "auc": roc_auc_score(y_test, nn_prob),
            "average_precision": average_precision_score(y_test, nn_prob),
            "f1": f1_score(y_test, (nn_prob > 0.5).astype(int)),
            "precision": precision_score(y_test, (nn_prob > 0.5).astype(int), zero_division=0),
            "recall": recall_score(y_test, (nn_prob > 0.5).astype(int)),
        }
        LOGGER.info(
            "   %-20s AUC: %.3f | AP: %.3f | F1: %.3f | P: %.3f | R: %.3f",
            "DeepNeuralNetwork",
            evaluation_results["DeepNeuralNetwork"]["auc"],
            evaluation_results["DeepNeuralNetwork"]["average_precision"],
            evaluation_results["DeepNeuralNetwork"]["f1"],
            evaluation_results["DeepNeuralNetwork"]["precision"],
            evaluation_results["DeepNeuralNetwork"]["recall"],
        )

    return models, evaluation_results, nn_prob


# ---------------------------------------------------------------------------
# Production Risk Scorer
# ---------------------------------------------------------------------------


def build_production_scorer(
    mule_models: Dict[str, Any],
    fraud_models: Dict[str, Any],
    feature_columns: List[str],
    categorical_columns: List[str],
    feature_engine: AegisFeatureEngine,
    scaler: StandardScaler,
) -> Any:
    LOGGER.info("[STEP 6] Building production risk scorer ...")

    class AegisProductionRiskScorer:
        def __init__(self):
            self.mule_model = mule_models["xgb_calibrated"]
            self.fraud_models = fraud_models
            self.feature_engine = feature_engine
            self.scaler = scaler
            self.feature_columns = feature_columns
            self.categorical_cols = categorical_columns
            self.risk_thresholds = {
                "low": 0.3,
                "medium": 0.6,
                "high": 0.8,
                "critical": 0.95,
            }

        def score_transaction(
            self,
            transaction_data: Dict[str, Any],
            customer_data: Dict[str, Any],
            account_data: Optional[Dict[str, Any]] = None,
            call_history: Optional[List[Dict[str, Any]]] = None,
            fraud_alerts: Optional[List[Dict[str, Any]]] = None,
        ) -> Dict[str, Any]:
            transactions_df = pd.DataFrame([transaction_data])
            customers_df = pd.DataFrame([customer_data])
            accounts_df = pd.DataFrame([account_data]) if account_data else pd.DataFrame()
            call_history_df = pd.DataFrame(call_history) if call_history else pd.DataFrame()
            fraud_alerts_df = pd.DataFrame(fraud_alerts) if fraud_alerts else pd.DataFrame()

            customer_features = self.feature_engine.create_customer_features(
                customers_df,
                accounts_df,
                transactions_df,
                call_history_df=call_history_df,
                fraud_alerts_df=fraud_alerts_df,
            )
            transaction_features = self.feature_engine.create_transaction_features(
                transactions_df,
                customer_features,
                behavioral_events_df=pd.DataFrame(),
                accounts_df=accounts_df,
                call_history_df=call_history_df,
                fraud_alerts_df=fraud_alerts_df,
            )
            transaction_features = self.feature_engine.encode_categorical_features(
                transaction_features, self.categorical_cols
            )

            for col in self.feature_columns:
                if col not in transaction_features.columns:
                    transaction_features[col] = 0
            transaction_features = transaction_features[self.feature_columns].fillna(0)

            fraud_scores = {}
            for name, model in self.fraud_models.items():
                try:
                    fraud_scores[name] = float(
                        model.predict_proba(transaction_features)[:, 1][0]
                    )
                except Exception:  # pragma: no cover - safety net
                    fraud_scores[name] = float(model.predict(transaction_features)[0])

            ensemble_score = float(np.mean(list(fraud_scores.values())))
            if ensemble_score >= self.risk_thresholds["critical"]:
                risk_level = "CRITICAL"
                action = "BLOCK_IMMEDIATELY"
            elif ensemble_score >= self.risk_thresholds["high"]:
                risk_level = "HIGH"
                action = "BLOCK_AND_REVIEW"
            elif ensemble_score >= self.risk_thresholds["medium"]:
                risk_level = "MEDIUM"
                action = "FLAG_FOR_REVIEW"
            else:
                risk_level = "LOW"
                action = "ALLOW"

            return {
                "overall_risk_score": round(ensemble_score, 4),
                "risk_level": risk_level,
                "recommended_action": action,
                "model_scores": {k: round(v, 4) for k, v in fraud_scores.items()},
                "timestamp": datetime.now().isoformat(),
            }

    return AegisProductionRiskScorer()


# ---------------------------------------------------------------------------
# Artifact Persistence & Reporting
# ---------------------------------------------------------------------------


def save_artifacts(
    config: TrainingConfig,
    mule_models: Dict[str, Any],
    mule_metrics: Dict[str, float],
    fraud_models: Dict[str, Any],
    fraud_metrics: Dict[str, Dict[str, float]],
    risk_scorer: Any,
) -> None:
    LOGGER.info("[STEP 7] Saving model artifacts ...")
    import joblib

    artifact_dir = config.output_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "mule_detector": mule_models["xgb_calibrated"],
        "mule_scaler": mule_models["scaler"],
        "fraud_xgb": fraud_models["base_models"]["xgb"],
        "fraud_lgb": fraud_models["base_models"]["lgb"],
        "fraud_rf": fraud_models["base_models"]["rf"],
        "fraud_ensemble": fraud_models["ensemble"],
        "risk_scorer": risk_scorer,
        "feature_engine": fraud_models["feature_engine"],
        "scaler": fraud_models["scaler"],
        "feature_columns": fraud_models["feature_columns"],
        "categorical_columns": fraud_models["categorical_columns"],
        "mule_metrics": mule_metrics,
        "fraud_metrics": fraud_metrics,
    }

    for name, artifact in payload.items():
        artifact_path = artifact_dir / f"aegis_{name}.pkl"
        joblib.dump(artifact, artifact_path)
        LOGGER.info("   ✓ Saved %s", artifact_path.name)

    metrics_path = config.output_dir / "training_metrics.json"
    metrics_content = {
        "timestamp": datetime.now().isoformat(),
        "mule_metrics": mule_metrics,
        "fraud_metrics": fraud_metrics,
    }
    metrics_path.write_text(json.dumps(metrics_content, indent=2))
    LOGGER.info("   ✓ Saved training metrics -> %s", metrics_path)


# ---------------------------------------------------------------------------
# SHAP Explainability (Optional)
# ---------------------------------------------------------------------------


def run_shap_analysis(
    model,
    X_train: np.ndarray,
    X_test: np.ndarray,
    config: TrainingConfig,
) -> None:
    if not SHAP_AVAILABLE:
        LOGGER.info("SHAP not available. Skipping explainability step.")
        return

    LOGGER.info("[STEP 8] Running SHAP explainability (sample size=%d) ...", config.shap_sample)
    try:
        sample_background = X_train[: config.shap_background]
        sample_test = X_test[: config.shap_sample]
        explainer = shap.Explainer(model, sample_background)
        shap_values = explainer(sample_test)
        shap.summary_plot(shap_values, sample_test, show=False)
        LOGGER.info("   ✓ SHAP summary plot generated (not displayed in script mode)")
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.warning("SHAP analysis failed: %s", exc)


# ---------------------------------------------------------------------------
# Main Orchestration
# ---------------------------------------------------------------------------


def main(cli_args: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Train Aegis APP fraud detection models")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "datasets" / "ml_sdv_datasets",
        help="Directory containing synthetic Aegis SDV datasets",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "model_output",
        help="Directory to store trained artifacts and metrics",
    )
    parser.add_argument(
        "--disable-deep-learning",
        action="store_true",
        help="Skip training the optional PyTorch neural network",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of data to use as the test set",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--shap-sample",
        type=int,
        default=1000,
        help="Number of test samples to evaluate with SHAP (if available)",
    )

    args = parser.parse_args(cli_args)

    config = TrainingConfig(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        random_state=args.random_state,
        test_size=args.test_size,
        enable_deep_learning=not args.disable_deep_learning and TORCH_AVAILABLE,
        shap_sample=args.shap_sample,
    )
    config.ensure_paths()

    LOGGER.info("=" * 80)
    LOGGER.info("AEGIS ADVANCED ML/DL TRAINING PIPELINE – START")
    LOGGER.info("Output directory: %s", config.output_dir)
    LOGGER.info("=" * 80)

    datasets = load_datasets(config)

    feature_engine = AegisFeatureEngine()
    customer_features = feature_engine.create_customer_features(
        datasets["customers"],
        datasets["accounts"],
        datasets["transactions"],
        call_history_df=datasets["call_history"],
        fraud_alerts_df=datasets["fraud_alerts"],
    )
    transaction_features = feature_engine.create_transaction_features(
        datasets["transactions"],
        customer_features,
        datasets["behavioral_events"],
        accounts_df=datasets["accounts"],
        call_history_df=datasets["call_history"],
        fraud_alerts_df=datasets["fraud_alerts"],
    )
    network_features, _ = feature_engine.create_network_features(
        datasets["transactions"], datasets["accounts"]
    )

    mule_models, mule_metrics = train_mule_models(network_features, config)
    fraud_models, fraud_metrics, nn_prob = train_fraud_models(transaction_features, config)

    risk_scorer = build_production_scorer(
        mule_models,
        fraud_models,
        fraud_models["feature_columns"],
        fraud_models["categorical_columns"],
        fraud_models["feature_engine"],
        fraud_models["scaler"],
    )

    save_artifacts(config, mule_models, mule_metrics, fraud_models, fraud_metrics, risk_scorer)

    if SHAP_AVAILABLE:
        run_shap_analysis(
            fraud_models["ensemble"],
            fraud_models["scaler"].transform(
                transaction_features[fraud_models["feature_columns"]].fillna(0).values
            ),
            fraud_models["scaler"].transform(
                transaction_features[fraud_models["feature_columns"]].fillna(0).values
            ),
            config,
        )

    LOGGER.info("=" * 80)
    LOGGER.info("AEGIS TRAINING COMPLETE – artifacts stored in %s", config.output_dir)
    LOGGER.info("=" * 80)


if __name__ == "__main__":
    main()
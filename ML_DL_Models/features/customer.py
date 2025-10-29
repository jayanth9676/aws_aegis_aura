from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd

from .utils import bool_to_int, clip_age, ensure_numeric, safe_ratio


def build_customer_features(
    customers: pd.DataFrame,
    accounts: pd.DataFrame,
    transactions: pd.DataFrame,
    call_history: Optional[pd.DataFrame] = None,
    fraud_alerts: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    customers = customers.copy()
    accounts = accounts.copy()
    transactions = transactions.copy()

    ensure_numeric(customers, ["annual_income", "credit_score", "vulnerability_score"])
    ensure_numeric(accounts, ["balance", "daily_limit", "monthly_limit"])
    ensure_numeric(transactions, ["amount", "risk_score"])

    for col in ["known_device", "ctr_flag", "sar_flag", "is_fraud"]:
        if col in transactions.columns:
            transactions[col] = bool_to_int(transactions[col])

    customers["age"] = clip_age(
        (datetime.now() - pd.to_datetime(customers["date_of_birth"], errors="coerce")).dt.days / 365.25
    )
    customers["customer_tenure_years"] = (
        (datetime.now() - pd.to_datetime(customers["onboarding_date"], errors="coerce")).dt.days / 365.25
    ).fillna(0).clip(lower=0)

    account_aggs = accounts.groupby("customer_id").agg(
        account_count=("account_id", "count"),
        total_balance=("balance", "sum"),
        avg_balance=("balance", "mean"),
        max_balance=("balance", "max"),
        balance_std=("balance", "std"),
        daily_limit_max=("daily_limit", "max"),
        monthly_limit_max=("monthly_limit", "max"),
        mule_account_count=("is_mule_account", lambda x: bool_to_int(x).sum()),
    ).reset_index().fillna(0)

    txn_aggs = transactions.groupby("customer_id").agg(
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

    features = customers.merge(account_aggs, on="customer_id", how="left")
    features = features.merge(txn_aggs, on="customer_id", how="left")

    if call_history is not None and not call_history.empty:
        features = features.merge(_call_history_aggs(call_history), on="customer_id", how="left")

    if fraud_alerts is not None and not fraud_alerts.empty:
        features = features.merge(_fraud_alert_aggs(fraud_alerts), on="customer_id", how="left")

    for col in [
        "total_calls",
        "alert_count",
        "avg_escalation_level",
        "avg_false_positive_prob",
    ]:
        if col not in features:
            features[col] = 0.0

    numeric_cols = features.select_dtypes(include=["number"]).columns
    features[numeric_cols] = features[numeric_cols].fillna(0)

    features["balance_to_income_ratio"] = safe_ratio(features["total_balance"], features["annual_income"] + 1)
    features["avg_txn_to_balance_ratio"] = safe_ratio(features["avg_amount"], features["avg_balance"] + 1)
    features["risk_velocity"] = safe_ratio(features["fraud_count"], features["txn_count"] + 1)
    features["mule_account_ratio"] = safe_ratio(features["mule_account_count"], features["account_count"] + 1)
    features["accounts_per_year"] = safe_ratio(features["account_count"], features["customer_tenure_years"] + 0.1)
    features["txn_per_month"] = safe_ratio(features["txn_count"], features["customer_tenure_years"] * 12 + 1)
    features["alert_to_txn_ratio"] = safe_ratio(features["alert_count"], features["txn_count"] + 1)
    features["call_to_txn_ratio"] = safe_ratio(features["total_calls"], features["txn_count"] + 1)

    return features


def _call_history_aggs(call_history: pd.DataFrame) -> pd.DataFrame:
    required = {
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
    if not required.issubset(call_history.columns):
        return pd.DataFrame({"customer_id": []})

    df = call_history.copy()
    df["call_date"] = pd.to_datetime(df["call_date"], errors="coerce")
    df["call_datetime"] = pd.to_datetime(
        df["call_date"].dt.strftime("%Y-%m-%d") + " " + df["call_time"], errors="coerce"
    )
    ensure_numeric(df, ["call_duration_seconds", "resolution_time_hours", "call_quality_score"])
    df["is_inbound"] = df["call_type"].str.lower().eq("inbound").astype(int)
    df["is_escalated"] = bool_to_int(df["escalated"])
    df["outcome_reached"] = df["call_outcome_category"].str.lower().eq("customer reached").astype(int)
    df["is_high_risk_call"] = df["risk_level"].str.lower().eq("high").astype(int)

    aggs = df.groupby("customer_id").agg(
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
    return aggs.reset_index()


def _fraud_alert_aggs(fraud_alerts: pd.DataFrame) -> pd.DataFrame:
    required = {
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
    if not required.issubset(fraud_alerts.columns):
        return pd.DataFrame({"customer_id": []})

    df = fraud_alerts.copy()
    priority_map = {"critical": 3, "high": 2, "medium": 1, "low": 0}
    status_map = {"open": 0, "closed": 1, "resolved": 1}
    escalation_map = {"l3": 3, "l2": 2, "l1": 1}

    df["priority_level"] = df["priority"].str.lower().map(priority_map).fillna(1)
    df["is_escalated_alert"] = df["escalation_level"].str.lower().map(escalation_map).fillna(0)
    df["is_closed_alert"] = df["status"].str.lower().map(status_map).fillna(0)
    df["alert_date"] = pd.to_datetime(df["alert_date"], errors="coerce")
    df["alert_datetime"] = pd.to_datetime(
        df["alert_date"].dt.strftime("%Y-%m-%d") + " " + df["alert_time"], errors="coerce"
    )

    aggs = df.groupby("customer_id").agg(
        alert_count=("alert_id", "count"),
        critical_alert_rate=("priority_level", lambda x: (x == 3).mean()),
        high_alert_rate=("priority_level", lambda x: (x >= 2).mean()),
        avg_alert_risk_score=("risk_score", "mean"),
        avg_false_positive_prob=("false_positive_probability", "mean"),
        avg_escalation_level=("is_escalated_alert", "mean"),
        alert_closure_rate=("is_closed_alert", "mean"),
    ).fillna(0)
    return aggs.reset_index()



from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from .utils import bool_to_int, cos_time, ensure_numeric, safe_log, safe_ratio, sin_time


def build_transaction_features(
    transactions: pd.DataFrame,
    customer_features: pd.DataFrame,
    behavioral_events: Optional[pd.DataFrame] = None,
    accounts: Optional[pd.DataFrame] = None,
    call_history: Optional[pd.DataFrame] = None,
    fraud_alerts: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    df = transactions.copy()
    ensure_numeric(df, ["amount", "risk_score"])

    for col in ["known_device", "is_flagged", "ctr_flag", "sar_flag", "is_fraud"]:
        if col in df.columns:
            df[col] = bool_to_int(df[col])

    df["transaction_datetime"] = pd.to_datetime(
        df["transaction_date"] + " " + df["transaction_time"], errors="coerce"
    )
    df["hour"] = df["transaction_datetime"].dt.hour
    df["day_of_week"] = df["transaction_datetime"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["is_night"] = df["hour"].isin(list(range(22, 24)) + list(range(0, 6))).astype(int)
    df["is_business_hours"] = df["hour"].between(8, 18).astype(int)
    df["log_amount"] = safe_log(df["amount"])
    df["is_round_amount"] = (df["amount"] % 100 == 0) & (df["amount"] > 0)
    df["sin_hour"] = sin_time(df["hour"], 24)
    df["cos_hour"] = cos_time(df["hour"], 24)
    df["sin_day_of_week"] = sin_time(df["day_of_week"], 7)
    df["cos_day_of_week"] = cos_time(df["day_of_week"], 7)

    enriched_cols = [
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
    merge_cols = [col for col in enriched_cols if col in customer_features.columns]

    df = df.merge(customer_features[merge_cols], on="customer_id", how="left")

    if "is_vulnerable" in df.columns:
        df["is_vulnerable"] = bool_to_int(df["is_vulnerable"])

    if accounts is not None and not accounts.empty:
        accounts_subset = accounts[[
            "account_id",
            "daily_limit",
            "monthly_limit",
            "is_mule_account",
            "customer_id",
        ]].copy()
        ensure_numeric(accounts_subset, ["daily_limit", "monthly_limit"])
        accounts_subset["is_mule_account"] = bool_to_int(accounts_subset["is_mule_account"])

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

        df = df.merge(source_accounts, on="source_account_id", how="left")
        df = df.merge(dest_accounts, on="destination_account_id", how="left")
        df["amount_to_daily_limit_ratio"] = safe_ratio(df["amount"], df["source_daily_limit"] + 1)
        df["amount_to_monthly_limit_ratio"] = safe_ratio(df["amount"], df["source_monthly_limit"] + 1)

    risk_map = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    for col in ["location_risk", "amount_risk", "velocity_risk"]:
        if col in df.columns:
            df[f"{col}_score"] = df[col].astype(str).str.lower().map(risk_map).fillna(0)

    if behavioral_events is not None and not behavioral_events.empty:
        df = df.merge(_behavioral_aggs(behavioral_events), on="transaction_id", how="left")

    if call_history is not None and not call_history.empty:
        df = df.merge(_call_aggs(call_history), on="transaction_id", how="left")
        if "last_call_datetime" in df.columns:
            df["hours_since_last_call"] = (
                df["transaction_datetime"] - df["last_call_datetime"]
            ).dt.total_seconds().div(3600).fillna(0).clip(lower=0)
            df.drop(columns=["last_call_datetime"], inplace=True)

    if fraud_alerts is not None and not fraud_alerts.empty:
        df = df.merge(_alert_aggs(fraud_alerts), on="transaction_id", how="left")
        if "last_alert_datetime" in df.columns:
            df["hours_since_last_alert"] = (
                df["transaction_datetime"] - df["last_alert_datetime"]
            ).dt.total_seconds().div(3600).fillna(0).clip(lower=0)
            df.drop(columns=["last_alert_datetime"], inplace=True)

    if "avg_amount" in df.columns:
        df["relative_amount_to_avg"] = safe_ratio(df["amount"], df["avg_amount"].replace({0: np.nan}))
    else:
        df["relative_amount_to_avg"] = 0.0

    df["risk_score_gap"] = df.get("risk_score", 0) - df.get("avg_risk_score", 0)
    df["device_trust_gap"] = df.get("known_device", 0) - df.get("known_device_rate", 0)

    fill_cols = [
        "total_balance",
        "avg_balance",
        "std_amount",
        "avg_risk_score",
        "anomaly_score",
    ]
    for col in fill_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    numeric_cols = df.select_dtypes(include=["number"]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    if accounts is not None and not accounts.empty:
        customer_network = accounts.groupby("customer_id").agg(
            source_mule_account_rate=("is_mule_account", lambda x: bool_to_int(x).mean()),
        ).reset_index()
        df = df.merge(customer_network, on="customer_id", how="left")
        df["source_mule_account_rate"] = df["source_mule_account_rate"].fillna(0)

    return df


def _behavioral_aggs(behavioral_events: pd.DataFrame) -> pd.DataFrame:
    required = {
        "transaction_id",
        "anomaly_score",
        "behavioral_flags",
        "session_duration_seconds",
        "hesitation_indicators",
        "typing_pattern_anomaly",
        "copy_paste_detected",
        "new_payee_flag",
        "authentication_failures",
    }
    if not required.issubset(behavioral_events.columns):
        return pd.DataFrame({"transaction_id": []})

    df = behavioral_events.copy()
    for col in ["copy_paste_detected", "new_payee_flag", "authentication_failures"]:
        df[col] = bool_to_int(df[col])

    aggs = df.groupby("transaction_id").agg(
        anomaly_score=("anomaly_score", "mean"),
        hesitation_indicators=("hesitation_indicators", "sum"),
        typing_pattern_anomaly=("typing_pattern_anomaly", "mean"),
        copy_paste_detected=("copy_paste_detected", "max"),
        new_payee_flag=("new_payee_flag", "max"),
        authentication_failures=("authentication_failures", "sum"),
    ).reset_index()
    return aggs


def _call_aggs(call_history: pd.DataFrame) -> pd.DataFrame:
    required = {
        "transaction_id",
        "call_id",
        "call_date",
        "call_time",
        "call_duration_seconds",
        "resolution_time_hours",
        "escalated",
        "call_outcome_category",
    }
    if not required.issubset(call_history.columns):
        return pd.DataFrame({"transaction_id": []})

    df = call_history.copy()
    df["call_date"] = pd.to_datetime(df["call_date"], errors="coerce")
    df["call_datetime"] = pd.to_datetime(
        df["call_date"].dt.strftime("%Y-%m-%d") + " " + df["call_time"], errors="coerce"
    )
    ensure_numeric(df, ["call_duration_seconds", "resolution_time_hours"])
    df["is_escalated"] = bool_to_int(df["escalated"])
    df["outcome_reached"] = df["call_outcome_category"].str.lower().eq("customer reached").astype(int)

    aggs = df.groupby("transaction_id").agg(
        txn_call_count=("call_id", "count"),
        txn_escalation_rate=("is_escalated", "mean"),
        txn_outcome_reached_rate=("outcome_reached", "mean"),
        txn_avg_call_duration=("call_duration_seconds", "mean"),
        txn_avg_resolution_hours=("resolution_time_hours", "mean"),
        last_call_datetime=("call_datetime", "max"),
    ).reset_index()

    aggs["last_call_datetime"] = pd.to_datetime(aggs["last_call_datetime"])
    return aggs


def _alert_aggs(fraud_alerts: pd.DataFrame) -> pd.DataFrame:
    required = {
        "transaction_id",
        "alert_id",
        "priority",
        "alert_date",
        "alert_time",
        "risk_score",
        "false_positive_probability",
    }
    if not required.issubset(fraud_alerts.columns):
        return pd.DataFrame({"transaction_id": []})

    df = fraud_alerts.copy()
    priority_map = {"critical": 3, "high": 2, "medium": 1, "low": 0}
    df["priority_level"] = df["priority"].str.lower().map(priority_map).fillna(1)
    df["alert_date"] = pd.to_datetime(df["alert_date"], errors="coerce")
    df["alert_datetime"] = pd.to_datetime(
        df["alert_date"].dt.strftime("%Y-%m-%d") + " " + df["alert_time"], errors="coerce"
    )

    aggs = df.groupby("transaction_id").agg(
        txn_alert_count=("alert_id", "count"),
        txn_high_priority_rate=("priority_level", lambda x: (x >= 2).mean()),
        txn_avg_alert_risk_score=("risk_score", "mean"),
        txn_avg_false_positive_prob=("false_positive_probability", "mean"),
        last_alert_datetime=("alert_datetime", "max"),
    ).reset_index()
    aggs["last_alert_datetime"] = pd.to_datetime(aggs["last_alert_datetime"])
    return aggs



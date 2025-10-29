from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd

from configs import AppConfig
from data import load_datasets
from models import load_risk_scorer


def run_batch_inference(config: AppConfig, limit: int | None = None) -> Path:
    datasets = load_datasets(config)
    if limit:
        datasets = datasets.limit_rows(limit)

    artifact_dir = config.output_dir / "artifacts"
    scorer = load_risk_scorer(artifact_dir)

    scores = []
    for _, txn in datasets.transactions.iterrows():
        customer = datasets.customers[datasets.customers["customer_id"] == txn["customer_id"]].iloc[0].to_dict()
        score = scorer.score_transaction(
            txn.to_dict(),
            customer,
        )
        scores.append({"transaction_id": txn["transaction_id"], **score})

    output_path = config.output_dir / f"batch_scores_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.json"
    output_path.write_text(json.dumps(scores, indent=2))
    return output_path



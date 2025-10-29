from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from models import load_risk_scorer


SAGEMAKER_CONTENT_TYPE = "application/json"


class AegisSageMakerHandler:
    def __init__(self, model_dir: str | Path):
        self.model_dir = Path(model_dir)
        self.scorer = load_risk_scorer(self.model_dir)

    def predict(self, payload: str) -> Dict[str, Any]:
        data = json.loads(payload)
        transaction = data["transaction"]
        customer = data["customer"]
        account = data.get("account")
        call_history = data.get("call_history")
        fraud_alerts = data.get("fraud_alerts")
        behavioral_events = data.get("behavioral_events")

        return self.scorer.score_transaction(
            transaction,
            customer,
            account_data=account,
            call_history=call_history,
            fraud_alerts=fraud_alerts,
            behavioral_events=behavioral_events,
        )


def model_fn(model_dir: str):  # pragma: no cover - SageMaker entrypoint
    return AegisSageMakerHandler(model_dir)


def transform_fn(handler: AegisSageMakerHandler, data: bytes, content_type: str, accept: str):
    if content_type != SAGEMAKER_CONTENT_TYPE:
        raise ValueError(f"Unsupported content type: {content_type}")
    result = handler.predict(data.decode("utf-8"))
    body = json.dumps(result)
    return body, accept



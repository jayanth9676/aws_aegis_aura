"""Bedrock AgentCore entrypoints for the Aegis platform."""

from __future__ import annotations

from typing import Any, Dict

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from utils import get_logger

from agentcore_app import get_aegis_app


app = BedrockAgentCoreApp(debug=True)
logger = get_logger(__name__)


@app.entrypoint
async def investigate(payload: Dict[str, Any], context: Dict[str, Any]):  # pylint: disable=unused-argument
    """AgentCore entrypoint for transaction investigations."""

    logger.debug(
        "agentcore.entrypoint.invoke",
        payload_preview=_safe_preview(payload),
        context_preview=_safe_preview(context),
    )

    aegis_app = await get_aegis_app()

    try:
        result = await aegis_app.investigate_transaction(payload)
        logger.info(
            "agentcore.entrypoint.success",
            decision=result.get("decision"),
            action=result.get("action"),
            risk_score=result.get("risk_score"),
        )
        return result
    except Exception as exc:  # pragma: no cover - defensive logging layer
        logger.error(
            "agentcore.entrypoint.failure",
            error=str(exc),
            payload_preview=_safe_preview(payload),
        )
        raise


__all__ = ["app"]


def _safe_preview(payload: Dict[str, Any], max_len: int = 512) -> str:
    """Create a safe, truncated string preview of the payload for logging."""

    if payload is None:
        return "<null>"

    try:
        import json

        preview = json.dumps(payload, default=str)
    except Exception:  # pragma: no cover - logging safety net
        preview = str(payload)

    if len(preview) > max_len:
        preview = preview[: max_len - 3] + "..."

    return preview


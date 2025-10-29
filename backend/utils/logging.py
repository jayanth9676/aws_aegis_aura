"""Structured logging utilities for the Aegis platform."""

from __future__ import annotations

import json
import logging
import os
import sys
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, Optional


DEFAULT_LOG_LEVEL = os.getenv("AEGIS_LOG_LEVEL", "DEBUG").upper()
# DEFAULT_LOG_LEVEL = os.getenv("AEGIS_LOG_LEVEL", "INFO").upper()
ENABLE_DEBUG_CONTEXT = os.getenv("AEGIS_DEBUG_CONTEXT", "1") == "1"


def _json_dumps(data: Dict[str, Any]) -> str:
    """Serialize log data to JSON, falling back to safe string representation."""

    with suppress(TypeError, ValueError):
        return json.dumps(data, default=str)

    # Fallback when serialization fails
    safe_data = {}
    for key, value in data.items():
        try:
            safe_data[key] = json.dumps(value, default=str)
        except Exception:  # pragma: no cover - defensive fallback
            safe_data[key] = str(value)

    return json.dumps(safe_data, default=str)


@dataclass
class StructuredLogger:
    """JSON-structured logger with optional rich context for debugging."""

    name: str
    level: int = field(default_factory=lambda: getattr(logging, DEFAULT_LOG_LEVEL, logging.INFO))

    def __post_init__(self) -> None:
        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(self.level)

        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(_StructuredFormatter())
            self._logger.addHandler(handler)

    def _log(self, level: str, message: str, **kwargs: Any) -> None:
        payload: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "logger_name": self.name,
            "message": message,
        }

        if kwargs:
            payload["context"] = kwargs

        if ENABLE_DEBUG_CONTEXT and level in {"DEBUG", "ERROR", "CRITICAL"}:
            payload["debug"] = _collect_debug_context()

        log_level = getattr(logging, level, logging.INFO)
        self._logger.log(log_level, _json_dumps(payload))

    def debug(self, message: str, **kwargs: Any) -> None:
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        self._log("CRITICAL", message, **kwargs)


class _StructuredFormatter(logging.Formatter):
    """Formatter that trusts the message to already be valid JSON."""

    def format(self, record: logging.LogRecord) -> str:
        return record.getMessage()


def _collect_debug_context() -> Dict[str, Any]:
    """Collect additional debug context such as environment, process info, etc."""

    context: Dict[str, Any] = {
        "pid": os.getpid(),
        "cwd": os.getcwd(),
    }

    # Include selected environment variables for debugging if whitelisted
    for env_name in [
        "AWS_REGION",
        "BEDROCK_AGENT_ID",
        "BEDROCK_GUARDRAILS_ID",
    ]:
        value = os.getenv(env_name)
        if value:
            context[f"env_{env_name.lower()}"] = value

    return context


@lru_cache(maxsize=128)
def get_logger(name: str) -> StructuredLogger:
    """Return a cached structured logger instance."""

    logger = StructuredLogger(name)

    if ENABLE_DEBUG_CONTEXT:
        logger.debug("logger.initialised", configured_level=DEFAULT_LOG_LEVEL)

    return logger




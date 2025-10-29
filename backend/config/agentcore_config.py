"""AgentCore runtime, memory, and gateway configuration utilities."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AgentCoreConfig:
    """Centralized configuration for AgentCore integration."""

    region: str
    runtime_arn: Optional[str]
    runtime_endpoint: Optional[str]
    execution_role_arn: Optional[str]
    memory_id: Optional[str]
    memory_event_expiry_days: int
    default_session_ttl: int
    long_term_ttl: int
    gateway_id: Optional[str]
    gateway_endpoint: Optional[str]
    gateway_client_id: Optional[str]
    gateway_client_secret: Optional[str]
    gateway_token_endpoint: Optional[str]
    gateway_scope: Optional[str]
    gateway_access_token: Optional[str]

    @property
    def gateway_configured(self) -> bool:
        has_endpoint = bool(self.gateway_endpoint)
        has_static_token = bool(self.gateway_access_token)
        has_client_credentials = all(
            [
                self.gateway_client_id,
                self.gateway_token_endpoint,
                self.gateway_client_secret,
            ]
        )
        return has_endpoint and (has_static_token or has_client_credentials)


def _get_env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


agentcore_config = AgentCoreConfig(
    region=os.getenv("AWS_REGION", "us-east-1"),
    runtime_arn=os.getenv("AGENTCORE_RUNTIME_ARN"),
    runtime_endpoint=os.getenv("AGENTCORE_RUNTIME_ENDPOINT"),
    execution_role_arn=os.getenv("AGENTCORE_EXECUTION_ROLE_ARN"),
    memory_id=os.getenv("AGENTCORE_MEMORY_ID"),
    memory_event_expiry_days=_get_env_int("MEMORY_EVENT_EXPIRY_DAYS", 30),
    default_session_ttl=_get_env_int("MEMORY_TTL_DEFAULT", 3600),
    long_term_ttl=_get_env_int("MEMORY_TTL_LONG_TERM", 86400),
    gateway_id=os.getenv("AGENTCORE_GATEWAY_ID"),
    gateway_endpoint=os.getenv("AGENTCORE_GATEWAY_ENDPOINT"),
    gateway_client_id=os.getenv("GATEWAY_CLIENT_ID"),
    gateway_client_secret=os.getenv("GATEWAY_CLIENT_SECRET"),
    gateway_token_endpoint=os.getenv("GATEWAY_TOKEN_ENDPOINT"),
    gateway_scope=os.getenv("GATEWAY_SCOPE", "invoke"),
    gateway_access_token=os.getenv("GATEWAY_ACCESS_TOKEN"),
)


__all__ = ["AgentCoreConfig", "agentcore_config"]


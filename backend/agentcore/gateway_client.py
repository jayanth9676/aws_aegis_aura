"""AgentCore Gateway client wrapper for tool invocation."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, Optional

import aiohttp
import requests
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient

from config import agentcore_config


class AgentCoreGatewayClient:
    """Gateway invoker that prefers AgentCore Gateway when configured."""

    def __init__(self, logger):
        self._logger = logger
        self._config = agentcore_config
        self._gateway_client: Optional[GatewayClient] = None
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[float] = None

        if self._config.gateway_configured:
            try:
                self._gateway_client = GatewayClient(region_name=self._config.region)
            except Exception as exc:  # pragma: no cover - handled via logs
                self._logger.warning(
                    "Failed to initialise Gateway client, falling back to local tools",
                    error=str(exc)
                )
                self._gateway_client = None

    async def _ensure_access_token(self) -> Optional[str]:
        if not self._gateway_client:
            return None

        if self._access_token:
            if self._token_expiry is None or time.time() < self._token_expiry:
                self._logger.debug(
                    "gateway.token.cached",
                    expires_at=self._token_expiry,
                )
                return self._access_token
            self._logger.info("Cached gateway token expired; refreshing…")
            self._access_token = None
            self._token_expiry = None

        if self._config.gateway_access_token:
            self._logger.debug("gateway.token.using_static")
            self._access_token = self._config.gateway_access_token
            return self._access_token

        if not (self._config.gateway_client_id and self._config.gateway_token_endpoint):
            self._logger.error("Gateway client credentials missing; cannot fetch token")
            return None

        try:
            response = requests.post(
                self._config.gateway_token_endpoint,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._config.gateway_client_id,
                    "client_secret": self._config.gateway_client_secret,
                    "scope": self._config.gateway_scope or "invoke",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            token = payload.get("access_token")
            if not token:
                raise ValueError("access_token missing from token response")
            self._access_token = token
            expires_in = payload.get("expires_in")
            self._token_expiry = time.time() + int(expires_in) - 60 if expires_in else None
            self._logger.debug(
                "gateway.token.acquired",
                expires_in=expires_in,
            )
            return token
        except Exception as exc:  # pragma: no cover
            self._logger.error("Failed to acquire Gateway access token", error=str(exc))
            return None

    async def invoke(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if self._config.gateway_configured and self._gateway_client:
            start_time = time.time()
            token = await self._ensure_access_token()
            if token:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            self._config.gateway_endpoint,
                            headers={
                                "Authorization": f"Bearer {token}",
                                "Content-Type": "application/json",
                            },
                            data=json.dumps(
                                {
                                    "jsonrpc": "2.0",
                                    "id": "invoke",
                                    "method": "tools/call",
                                    "params": {
                                        "name": tool_name,
                                        "arguments": params,
                                    },
                                }
                            ),
                        ) as response:
                            payload = await response.json()
                            self._logger.debug(
                                "gateway.invoke.response",
                                tool=tool_name,
                                status=response.status,
                                latency_ms=(time.time() - start_time) * 1000,
                            )
                            if "error" in payload:
                                raise RuntimeError(payload["error"])
                            return payload.get("result", {})
                except Exception as exc:
                    self._logger.error(
                        "Gateway invocation failed, falling back to local tool",
                        tool=tool_name,
                        error=str(exc),
                        latency_ms=(time.time() - start_time) * 1000,
                    )
                    self._access_token = None

        # Fallback: invoke local registered tool
        try:
            start_time = time.time()
            from tools import get_tool

            tool_function = get_tool(tool_name)
            if not tool_function:
                raise ValueError(f"Tool not found: {tool_name}")

            result = tool_function(params)
            if asyncio.iscoroutine(result):
                result = await result
            self._logger.debug(
                "gateway.local_tool.success",
                tool=tool_name,
                latency_ms=(time.time() - start_time) * 1000,
            )
            return result
        except Exception as exc:  # pragma: no cover - handled via logs
            self._logger.error("Local tool invocation failed", tool=tool_name, error=str(exc))
            return {"error": str(exc)}


__all__ = ["AgentCoreGatewayClient"]


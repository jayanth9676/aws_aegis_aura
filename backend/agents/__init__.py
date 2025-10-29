"""Aegis multi-agent system package."""

from .base_agent import AegisBaseAgent
from agentcore.memory_manager import AgentCoreMemoryManager
from agentcore.gateway_client import AgentCoreGatewayClient

# Backwards-compatible aliases for legacy imports
AgentCoreMemory = AgentCoreMemoryManager
AgentCoreGateway = AgentCoreGatewayClient

__all__ = [
    "AegisBaseAgent",
    "AgentCoreMemory",
    "AgentCoreGateway",
]




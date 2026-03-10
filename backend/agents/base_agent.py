"""Base agent utilities for Aegis — built on Strands Agents SDK v1.0.

This replaces the old AegisBaseAgent(ABC) with a modern factory that
creates real `strands.Agent` instances while preserving AgentCore
Memory and Gateway integrations.

March 2026 patterns applied:
  • from strands import Agent, tool          (native SDK)
  • Pydantic structured_output_model         (no regex JSON parsing)
  • invocation_state for shared context      (replaces manual dict passing)
  • Bedrock model provider                   (native Strands provider)
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from strands import Agent, tool
from strands.models.bedrock import BedrockModel

from config import AgentConfig, system_config, agentcore_config
from utils import get_logger, metrics_tracker

# AgentCore Memory — preserved from the original system
from agentcore.memory_manager import AgentCoreMemoryManager

logger = get_logger("agents.base")

# ── Global Memory Manager (shared across all agents) ──────────────────

_memory: Optional[AgentCoreMemoryManager] = None


def get_memory() -> AgentCoreMemoryManager:
    """Return the shared AgentCore Memory manager (lazy-initialised)."""
    global _memory
    if _memory is None:
        _memory = AgentCoreMemoryManager(logger)
    return _memory


# ── Bedrock Model Factory ─────────────────────────────────────────────

def create_bedrock_model(
    model_id: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    top_p: float = 0.9,
    region: Optional[str] = None,
) -> BedrockModel:
    """Create a Strands BedrockModel with the given parameters."""
    return BedrockModel(
        model_id=model_id or "us.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name=region or os.getenv("AWS_REGION", "us-east-1"),
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
    )


# ── Strands Agent Factory ─────────────────────────────────────────────

def create_agent(
    name: str,
    system_prompt: str,
    tools: Optional[List] = None,
    config: Optional[AgentConfig] = None,
    model_id: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> Agent:
    """Create a fully-configured Strands Agent.

    This is the single entry-point for agent creation across the Aegis
    platform.  It wires up the Bedrock model provider and suppresses
    intermediate output (callback_handler=None) so that orchestrator
    agents only see final results.
    """
    cfg = config or AgentConfig(name=name)
    model = create_bedrock_model(
        model_id=model_id or cfg.model_id,
        temperature=temperature if temperature is not None else cfg.temperature,
        max_tokens=max_tokens or cfg.max_tokens,
        top_p=cfg.top_p,
    )

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=tools or [],
        callback_handler=None,  # suppress intermediate streaming in sub-agents
    )

    logger.info("Created Strands agent", agent_name=name, model_id=cfg.model_id)
    return agent


# ── Memory Helpers (for use inside @tool functions) ───────────────────

async def store_memory(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Store a value in AgentCore Memory."""
    ttl = ttl or agentcore_config.session_ttl
    return await get_memory().put(key, value, ttl)


async def retrieve_memory(key: str) -> Optional[Any]:
    """Retrieve a value from AgentCore Memory."""
    return await get_memory().get(key)


async def record_investigation_summary(
    session_id: str, summary: Dict[str, Any], actor_id: str = "aegis_platform"
) -> None:
    """Persist a complete investigation summary to AgentCore Memory."""
    await get_memory().record_investigation_summary(session_id, summary, actor_id)


# ── Performance Tracking Decorator ────────────────────────────────────

def track_agent(name: str):
    """Decorator that records latency + success/failure for an agent tool."""
    def decorator(fn):
        import functools

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = fn(*args, **kwargs)
                latency_ms = (time.time() - start) * 1000
                metrics_tracker.track_agent_performance(name, success=True, latency_ms=latency_ms)
                logger.info("Agent completed", agent=name, latency_ms=round(latency_ms, 1))
                return result
            except Exception as exc:
                latency_ms = (time.time() - start) * 1000
                metrics_tracker.track_agent_performance(name, success=False, latency_ms=latency_ms)
                logger.error("Agent failed", agent=name, error=str(exc), latency_ms=round(latency_ms, 1))
                raise
        return wrapper
    return decorator


# ── Legacy Compatibility Layer ─────────────────────────────────────────
# Kept so that existing code that imports AegisBaseAgent does not break
# during migration.  New code should use create_agent() and @tool.

class AegisBaseAgent:
    """Legacy compatibility shim — wraps a Strands Agent under the old interface."""

    def __init__(self, name: str, config: AgentConfig):
        self.name = name
        self.config = config
        self.logger = get_logger(f"agent.{name}")
        self._memory = get_memory()

        # Create a Strands Agent internally
        self._strands_agent = create_agent(
            name=name,
            system_prompt=self._build_system_prompt(),
            config=config,
        )

    def _build_system_prompt(self) -> str:
        return (
            f"You are {self.name}, an AI agent in the Aegis fraud prevention system.\n"
            f"Your role: {self.config.description}\n\n"
            "Guidelines:\n"
            "- Analyze data objectively and thoroughly\n"
            "- Identify fraud risk factors with clear reasoning\n"
            "- Provide structured, actionable insights\n"
            "- Be concise but comprehensive\n"
            "- Focus on evidence-based conclusions"
        )

    async def invoke_tool(self, tool_name: str, params: Dict) -> Dict:
        from tools import invoke_tool as _invoke
        return await _invoke(tool_name, params)

    async def store_memory(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        return await store_memory(key, value, ttl or self.config.session_ttl)

    async def retrieve_memory(self, key: str) -> Optional[Any]:
        return await retrieve_memory(key)

    async def record_investigation_summary(self, session_id: str, summary: Dict) -> None:
        await record_investigation_summary(session_id, summary, actor_id=self.name)

    async def invoke_bedrock(self, prompt: str, **kwargs) -> str:
        """Invoke the internal Strands Agent and return text."""
        result = self._strands_agent(prompt)
        return str(result)

    async def reason_with_bedrock(self, prompt: str, context: Dict, output_format: str = "json") -> Dict:
        """Use the Strands Agent for reasoning with structured output."""
        import json as _json

        context_str = _json.dumps(context, indent=2, default=str)
        full_prompt = f"Context Data:\n{context_str}\n\nTask:\n{prompt}"
        if output_format == "json":
            full_prompt += "\n\nProvide your response as valid JSON only."

        result_text = await self.invoke_bedrock(full_prompt)

        if output_format == "json":
            try:
                import re
                json_match = re.search(r'\{[\s\S]*\}', result_text)
                if json_match:
                    return _json.loads(json_match.group())
                return _json.loads(result_text)
            except _json.JSONDecodeError:
                return {"response": result_text, "parsed": False}
        return {"response": result_text}

    async def query_knowledge_base(self, query: str, top_k: int = 5) -> List[Dict]:
        from config import aws_config
        try:
            if not system_config.KNOWLEDGE_BASE_ID:
                return self._get_fallback_intelligence(query)
            response = aws_config.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=system_config.KNOWLEDGE_BASE_ID,
                retrievalQuery={"text": query},
                retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": top_k}},
            )
            return [
                {
                    "content": r["content"]["text"],
                    "source": r.get("location", {}).get("s3Location", {}).get("uri", "unknown"),
                    "score": r.get("score", 0.0),
                }
                for r in response.get("retrievalResults", [])
            ]
        except Exception:
            return self._get_fallback_intelligence(query)

    def _get_fallback_intelligence(self, query: str) -> List[Dict]:
        q = query.lower()
        if "impersonation" in q:
            text = "Impersonation fraud: unsolicited contact, urgent requests, mismatched communication."
        elif "investment" in q or "romance" in q:
            text = "Investment/romance scams: emotional manipulation, false return promises."
        elif "invoice" in q or "redirection" in q:
            text = "Invoice redirection: intercepted communications, changed payment details."
        elif "mule" in q or "money laundering" in q:
            text = "Money mule: rapid fund movement, circular flows, no legitimate purpose."
        else:
            text = "APP fraud: urgency, emotional manipulation, new payees, behavioural anomalies."
        return [{"content": text, "source": "fallback_intelligence", "score": 0.8}]

    async def execute(self, input_data: Dict) -> Dict:
        raise NotImplementedError("Subclasses must implement execute()")

    async def __call__(self, input_data: Dict) -> Dict:
        start = time.time()
        try:
            result = await self.execute(input_data)
            latency_ms = (time.time() - start) * 1000
            metrics_tracker.track_agent_performance(self.name, success=True, latency_ms=latency_ms)
            return result
        except Exception as exc:
            latency_ms = (time.time() - start) * 1000
            metrics_tracker.track_agent_performance(self.name, success=False, latency_ms=latency_ms)
            return {"success": False, "error": str(exc), "agent": self.name}

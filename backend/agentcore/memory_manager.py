"""AgentCore Memory integration helpers for the Aegis platform."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional, Tuple

from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole
from bedrock_agentcore.memory.session import MemorySessionManager

from config import agentcore_config


DEFAULT_ACTOR_ID = "aegis_platform"


def _serialize_value(value: Any) -> str:
    try:
        return json.dumps(value, default=str)
    except Exception:
        return json.dumps({'repr': repr(value)})


def _parse_memory_key(key: str) -> Tuple[str, str, str]:
    parts = key.split(":")
    scope = parts[0] if parts else "misc"
    session_id = parts[1] if len(parts) > 1 else "default"
    sub_key = ":".join(parts[2:]) if len(parts) > 2 else ""
    return scope, session_id, sub_key


class AgentCoreMemoryManager:
    """Helper for writing structured events to AgentCore Memory."""

    def __init__(self, logger):
        self._logger = logger
        self._config = agentcore_config
        self._memory_id = self._config.memory_id
        self._client: Optional[MemoryClient] = None
        self._session_managers: Dict[str, MemorySessionManager] = {}
        self._fallback_store: Dict[str, Any] = {}

        if self._memory_id:
            try:
                self._client = MemoryClient(region_name=self._config.region)
            except Exception as exc:  # pragma: no cover - handled via logs
                self._logger.warning(
                    "Failed to initialise AgentCore Memory client, falling back to local store",
                    error=str(exc)
                )
                self._client = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_session_manager(self, session_id: str) -> Optional[MemorySessionManager]:
        if not self._client or not self._memory_id:
            return None

        if session_id not in self._session_managers:
            self._session_managers[session_id] = MemorySessionManager(
                memory_id=self._memory_id,
                region_name=self._config.region
            )
        return self._session_managers[session_id]

    async def _create_event(  # pylint: disable=too-many-arguments
        self,
        actor_id: str,
        session_id: str,
        messages: List[Tuple[str, str]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        if not self._client or not self._memory_id:
            return

        def _write():
            self._client.create_event(
                memory_id=self._memory_id,
                actor_id=actor_id,
                session_id=session_id,
                metadata=metadata or {},
                messages=messages,
            )

        await asyncio.to_thread(_write)

    # ------------------------------------------------------------------
    # Public API (compatible with legacy key-value helpers)
    # ------------------------------------------------------------------
    async def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        self._fallback_store[key] = value

        if not self._client or not self._memory_id:
            return True

        scope, session_id, sub_key = _parse_memory_key(key)
        payload = {
            "key": key,
            "scope": scope,
            "sub_key": sub_key,
            "ttl": ttl,
            "value": value,
        }

        await self._create_event(
            actor_id=DEFAULT_ACTOR_ID,
            session_id=session_id,
            messages=[(_serialize_value(payload), MessageRole.ASSISTANT.value)],
            metadata={"type": "kv_store", "scope": scope},
        )

        return True

    async def get(self, key: str) -> Optional[Any]:
        if key in self._fallback_store:
            return self._fallback_store[key]

        # Future enhancement: query AgentCore memory for persisted record
        return None

    async def delete(self, key: str) -> bool:
        if key in self._fallback_store:
            del self._fallback_store[key]
        # AgentCore Memory does not yet expose delete for individual events
        return True

    # ------------------------------------------------------------------
    # Higher level helpers used by agents
    # ------------------------------------------------------------------
    async def record_session_turn(
        self,
        session_id: str,
        messages: List[ConversationalMessage],
        actor_id: str = DEFAULT_ACTOR_ID
    ) -> None:
        manager = self._get_session_manager(session_id)
        if not manager:
            return

        def _write():
            session = manager.create_memory_session(actor_id=actor_id, session_id=session_id)
            session.add_turns(messages=messages)

        await asyncio.to_thread(_write)

    async def record_investigation_summary(
        self,
        session_id: str,
        summary: Dict[str, Any],
        actor_id: str = DEFAULT_ACTOR_ID
    ) -> None:
        await self._create_event(
            actor_id=actor_id,
            session_id=session_id,
            messages=[(
                _serialize_value({"summary": summary}),
                MessageRole.ASSISTANT.value
            )],
            metadata={"type": "investigation_summary"},
        )

    async def get_recent_session_context(
        self,
        session_id: str,
        actor_id: str = DEFAULT_ACTOR_ID,
        k: int = 5
    ) -> List[List[ConversationalMessage]]:
        manager = self._get_session_manager(session_id)
        if not manager:
            return []

        def _read():
            session = manager.create_memory_session(actor_id=actor_id, session_id=session_id)
            return session.get_last_k_turns(k=k)

        return await asyncio.to_thread(_read)


__all__ = ["AgentCoreMemoryManager"]


from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid

from observability.langsmith_tracing import trace_agent


@dataclass
class ConversationState:
    session_id: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    last_agent: str | None = None
    last_entities: dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ConversationMemory:
    def __init__(self) -> None:
        self._store: dict[str, ConversationState] = {}

    @trace_agent("memory_get_or_create", run_type="chain", tags=["memory"])
    def get_or_create(self, session_id: str | None = None) -> ConversationState:
        sid = session_id or str(uuid.uuid4())
        if sid not in self._store:
            self._store[sid] = ConversationState(session_id=sid)
        return self._store[sid]

    @trace_agent("memory_add_message", run_type="chain", tags=["memory"])
    def add_message(self, session_id: str, role: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        state = self.get_or_create(session_id)
        state.messages.append({
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        })
        state.updated_at = datetime.utcnow().isoformat()

    def recent_messages(self, session_id: str, limit: int = 8) -> list[dict[str, Any]]:
        return self.get_or_create(session_id).messages[-limit:]

    @trace_agent("memory_update_entities", run_type="chain", tags=["memory"])
    def update_entities(self, session_id: str, entities: dict[str, str]) -> None:
        state = self.get_or_create(session_id)
        state.last_entities.update({k: v for k, v in entities.items() if v})
        state.updated_at = datetime.utcnow().isoformat()


memory = ConversationMemory()

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import uuid

from observability.langsmith_tracing import trace_agent, safe_trace_payload


@dataclass
class A2AMessage:
    protocol: str
    message_id: str
    from_agent: str
    to_agent: str
    task: str
    user_query: str
    session_id: str
    entities: dict[str, str]
    memory: list[dict[str, Any]]
    payload: dict[str, Any]

    @classmethod
    @trace_agent("a2a_create_message", run_type="chain", tags=["a2a"] )
    def create(
        cls,
        from_agent: str,
        to_agent: str,
        task: str,
        user_query: str,
        session_id: str,
        entities: dict[str, str],
        memory: list[dict[str, Any]],
        payload: dict[str, Any] | None = None,
    ) -> "A2AMessage":
        return cls(
            protocol="a2a-local-json-v1",
            message_id=str(uuid.uuid4()),
            from_agent=from_agent,
            to_agent=to_agent,
            task=task,
            user_query=user_query,
            session_id=session_id,
            entities=safe_trace_payload(entities),
            memory=safe_trace_payload(memory),
            payload=safe_trace_payload(payload or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

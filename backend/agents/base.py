from __future__ import annotations
from typing import Any

from services.a2a import A2AMessage
from services.reasoning import reasoning_service
from observability.langsmith_tracing import trace_agent, safe_trace_payload


class AgentResponse(dict):
    pass


class BaseAgent:
    name = "BaseAgent"

    def handle(self, message: A2AMessage) -> dict[str, Any]:
        raise NotImplementedError

    @trace_agent("specialist_agent_build_response", run_type="chain", tags=["agent-response"])
    def build_response(self, message: A2AMessage, evidence: dict[str, Any], table_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        reasoning = reasoning_service.reason(
            agent_name=self.name,
            user_query=message.user_query,
            evidence=evidence,
            memory=message.memory,
        )
        return {
            "agent": self.name,
            "a2a": message.to_dict(),
            "evidence": safe_trace_payload(evidence),
            "summary": reasoning,
            "table": {
                "rows": table_rows or self._rows_from_evidence(evidence),
                "sql": None,
                "type": "mcp_tool_result",
            },
            "suggested_questions": self.suggested_questions(message, evidence),
        }

    def _rows_from_evidence(self, evidence: dict[str, Any]) -> list[dict[str, Any]]:
        if isinstance(evidence.get("dealer_360"), dict):
            # Dealer 360 questions should show the dealer-level row first.
            # Previously context-pack responses could show only the warranty trend
            # table because recent_warranty_performance appeared before dealer_360.
            return [evidence["dealer_360"]]
        if isinstance(evidence.get("locations"), list):
            return evidence["locations"][:10]
        if isinstance(evidence.get("recent_events"), list):
            return evidence["recent_events"][:10]
        if isinstance(evidence.get("recent_warranty_performance"), list):
            return evidence["recent_warranty_performance"][:10]
        if isinstance(evidence.get("claim"), dict):
            return [evidence["claim"]]
        return []

    def suggested_questions(self, message: A2AMessage, evidence: dict[str, Any]) -> list[str]:
        return [
            "Can you explain the key risk?",
            "What should be the next action?",
            "Show the evidence used for this answer.",
        ]

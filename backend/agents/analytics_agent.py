from __future__ import annotations
from typing import Any

from agents.base import BaseAgent
from services.a2a import A2AMessage
from services.genie_mcp_bridge import genie_mcp_bridge
from services.reasoning import reasoning_service
from observability.langsmith_tracing import trace_agent, safe_trace_payload


class AnalyticsAgent(BaseAgent):
    """Analytics Agent for revenue ranking, comparison, KPI, and trend questions.

    Flow: Analytics Agent -> Databricks Genie MCP -> GPT-5.5/fallback reasoning.
    """

    name = "Analytics Agent"

    @trace_agent("analytics_agent_run", run_type="chain", tags=["specialist-agent", "analytics", "genie"])
    def handle(self, message: A2AMessage) -> dict[str, Any]:
        genie_result = genie_mcp_bridge.ask_sync(message.user_query, session_id=message.session_id)
        evidence = {
            "found": genie_result.get("found", False),
            "source": genie_result.get("source", "databricks_genie_mcp"),
            "question": message.user_query,
            "genie_answer": genie_result.get("answer"),
            "rows": genie_result.get("rows", []),
            "chart": genie_result.get("chart"),
            "sql": genie_result.get("sql"),
            "raw_response": genie_result.get("raw_response"),
        }

        reasoning = reasoning_service.reason(
            agent_name=self.name,
            user_query=message.user_query,
            evidence=safe_trace_payload(evidence),
            memory=message.memory,
        )

        rows = genie_result.get("rows") or []
        return {
            "agent": self.name,
            "a2a": message.to_dict(),
            "evidence": safe_trace_payload(evidence),
            "summary": reasoning,
            "table": {
                "rows": rows,
                "sql": genie_result.get("sql"),
                "type": "databricks_genie_result",
                "raw_response": safe_trace_payload(genie_result),
            },
            "chart": genie_result.get("chart"),
            "suggested_questions": self.suggested_questions(message, evidence),
        }

    def suggested_questions(self, message: A2AMessage, evidence: dict[str, Any]) -> list[str]:
        return [
            "Show monthly revenue trend across all markets.",
            "Compare customer satisfaction score by dealer.",
            "Show top 10 dealers by revenue.",
        ]

from __future__ import annotations
from typing import Any
from agents.base import BaseAgent
from services.a2a import A2AMessage
from services.mcp_bridge import mcp_bridge
from observability.langsmith_tracing import trace_agent


class PartsAgent(BaseAgent):
    name = "Parts Agent"

    @trace_agent("parts_agent_run", run_type="chain", tags=["specialist-agent"])
    def handle(self, message: A2AMessage) -> dict[str, Any]:
        part_number = message.entities.get("part_number")
        market_code = message.entities.get("market_code")
        if not part_number:
            evidence = {"found": False, "message": "Please provide a part number such as P001."}
        else:
            evidence = mcp_bridge.call_tool_sync(
                "check_part_availability",
                {"part_number": part_number, "market_code": market_code, "limit": 10},
            )
        return self.build_response(message, evidence)

    def suggested_questions(self, message: A2AMessage, evidence: dict[str, Any]) -> list[str]:
        part = message.entities.get("part_number", "this part")
        return [
            f"Is there an alternate part for {part}?",
            f"Is a reman option available for {part}?",
            "Which dealer has the best stock position?",
        ]

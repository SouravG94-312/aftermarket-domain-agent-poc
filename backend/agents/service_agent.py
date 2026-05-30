from __future__ import annotations
from typing import Any
from agents.base import BaseAgent
from services.a2a import A2AMessage
from services.mcp_bridge import mcp_bridge
from observability.langsmith_tracing import trace_agent


class ServiceAgent(BaseAgent):
    name = "Service Agent"

    @trace_agent("service_agent_run", run_type="chain", tags=["specialist-agent"])
    def handle(self, message: A2AMessage) -> dict[str, Any]:
        vin = message.entities.get("vin")
        if not vin:
            evidence = {"found": False, "message": "Please provide a VIN such as VINDEF000123."}
        else:
            evidence = mcp_bridge.call_tool_sync("get_vehicle_service_history", {"vin": vin, "limit": 8})
        return self.build_response(message, evidence)

    def suggested_questions(self, message: A2AMessage, evidence: dict[str, Any]) -> list[str]:
        vin = message.entities.get("vin", "this VIN")
        return [
            f"Is {vin} showing a repeat issue?",
            f"What is the latest fault code for {vin}?",
            "Which part availability should be checked next?",
        ]

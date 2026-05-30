from __future__ import annotations
from typing import Any
from agents.base import BaseAgent
from services.a2a import A2AMessage
from services.mcp_bridge import mcp_bridge
from observability.langsmith_tracing import trace_agent


class WarrantyAgent(BaseAgent):
    name = "Warranty Agent"

    @trace_agent("warranty_agent_run", run_type="chain", tags=["specialist-agent"])
    def handle(self, message: A2AMessage) -> dict[str, Any]:
        claim_id = message.entities.get("claim_id")
        if not claim_id:
            evidence = {"found": False, "message": "Please provide a warranty claim ID such as WC1001."}
        else:
            evidence = mcp_bridge.call_tool_sync("get_warranty_claim_details", {"claim_id": claim_id})
        return self.build_response(message, evidence)

    def suggested_questions(self, message: A2AMessage, evidence: dict[str, Any]) -> list[str]:
        claim_id = message.entities.get("claim_id", "this claim")
        return [
            f"What documents are missing for {claim_id}?",
            f"Can {claim_id} be resubmitted?",
            "Is there a repeat repair pattern for the same VIN?",
        ]

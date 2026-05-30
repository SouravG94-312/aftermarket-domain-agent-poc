from __future__ import annotations
from typing import Any
from agents.base import BaseAgent
from services.a2a import A2AMessage
from services.mcp_bridge import mcp_bridge
from observability.langsmith_tracing import trace_agent


class DeepReasoningAgent(BaseAgent):
    name = "Deep Reasoning Agent"

    @trace_agent("deep_reasoning_agent_run", run_type="chain", tags=["specialist-agent"])
    def handle(self, message: A2AMessage) -> dict[str, Any]:
        # Additive behavior: when the Supervisor already collected evidence from
        # multiple specialist agents, synthesize that evidence directly instead
        # of performing another MCP lookup. Existing context-pack behavior is
        # preserved for dealer/VIN/claim/part/market-only reasoning questions.
        if isinstance(message.payload, dict) and message.payload.get("evidence_bundle"):
            evidence = message.payload["evidence_bundle"]
        else:
            entity_type, entity_id = self._resolve_entity(message)
            if not entity_type or not entity_id:
                evidence = {"found": False, "message": "Please provide a dealer ID, VIN, claim ID, market, or part number for deep reasoning."}
            else:
                evidence = mcp_bridge.call_tool_sync(
                    "generate_aftermarket_context_pack",
                    {"entity_type": entity_type, "entity_id": entity_id},
                )
        return self.build_response(message, evidence)

    def _resolve_entity(self, message: A2AMessage) -> tuple[str | None, str | None]:
        e = message.entities
        if e.get("dealer_id"):
            return "dealer", e["dealer_id"]
        if e.get("vin"):
            return "vin", e["vin"]
        if e.get("claim_id"):
            return "claim", e["claim_id"]
        if e.get("part_number"):
            return "part", e["part_number"]
        if e.get("market_code"):
            return "market", e["market_code"]
        return None, None

    def suggested_questions(self, message: A2AMessage, evidence: dict[str, Any]) -> list[str]:
        return [
            "What is the likely root cause?",
            "What is the business impact?",
            "What should the supervisor recommend next?",
        ]

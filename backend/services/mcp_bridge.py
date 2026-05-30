from __future__ import annotations

import asyncio
import os
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from services.config import settings
from observability.langsmith_tracing import trace_agent, safe_trace_payload


MOCK_RESPONSES: dict[str, dict[str, Any]] = {
    "get_warranty_claim_details": {
        "found": True,
        "claim": {
            "claim_id": "WC1001", "claim_status": "Rejected", "dealer_id": "DLR003",
            "dealer_name": "Berlin Trucks Center", "vin": "VINDEF000123",
            "rejection_reason": "Missing diagnostic log and late submission",
            "missing_documents": "Diagnostic log, technician notes",
            "claim_risk_level": "High", "recommended_claim_action": "Collect missing documents and resubmit with technical justification."
        },
        "summary": {"status": "Rejected", "risk_level": "High", "recommended_action": "Resubmit with evidence"}
    },
    "get_vehicle_service_history": {
        "found": True,
        "vin": "VINDEF000123",
        "summary": {"total_service_events": 4, "distinct_fault_codes": 2, "latest_mileage_km": 132400, "symptoms_observed": "Power loss, warning lamp"},
        "recent_events": [
            {"repair_order_id": "RO2001", "fault_code": "FC-PWR-101", "symptom": "Power loss", "component": "Powertrain", "service_priority": "Priority 1"},
            {"repair_order_id": "RO1984", "fault_code": "FC-PWR-101", "symptom": "Power loss", "component": "Powertrain", "service_priority": "Priority 2"}
        ],
        "analysis": {"repeat_issue_indicator": True, "recommended_next_step": "Escalate due to repeat fault pattern."}
    },
    "check_part_availability": {
        "found": True,
        "part_number": "P001",
        "market_code": "DE",
        "summary": {"total_available_qty": 14, "total_backorder_qty": 6, "availability_status": "Limited", "alternate_part_number": "P001-A", "recommended_parts_action": "Use alternate part or transfer from best-stock dealer."},
        "locations": [{"dealer_id": "DLR003", "available_qty": 8, "lead_time_days": 2}, {"dealer_id": "DLR007", "available_qty": 6, "lead_time_days": 4}]
    },
    "generate_aftermarket_context_pack": {
        "found": True,
        "entity_type": "dealer",
        "entity_id": "DLR003",
        "dealer_360": {"dealer_id": "DLR003", "market_name": "Germany", "revenue_eur": 594000, "customer_satisfaction_score": 3.8, "warranty_claim_rejection_rate": 0.31, "eligible_flag": False},
        "recent_warranty_performance": [{"claim_month": "2026-04", "total_claims": 22, "rejected_claims": 7}],
        "recent_bonus_records": [{"bonus_period": "2026-Q1", "eligible_flag": False, "failed_hurdle": "Customer Satisfaction"}],
        "recommended_reasoning_focus": ["Warranty rejection rate is high.", "Customer satisfaction is below threshold.", "Bonus eligibility is blocked or at risk."]
    }
}


class MCPBridge:
    """Calls the local MCP server over stdio.

    In MOCK_MCP=true mode, returns deterministic mock responses so frontend/backend
    can be tested without Databricks or a running MCP server.
    """

    @trace_agent("mcp_tool_call_async", run_type="tool", tags=["mcp-tool"] )
    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = safe_trace_payload(arguments or {})
        if settings.mock_mcp:
            return safe_trace_payload(MOCK_RESPONSES.get(tool_name, {"found": False, "message": f"No mock for {tool_name}", "arguments": arguments}))

        if not settings.mcp_app_path.exists():
            raise FileNotFoundError(f"MCP server app.py not found at {settings.mcp_app_path}")

        child_env = os.environ.copy()
        child_env["MCP_TRANSPORT"] = "stdio"
        child_env["PYTHONPATH"] = str(settings.mcp_server_dir)

        server_params = StdioServerParameters(
            command="python",
            args=["app.py"],
            cwd=str(settings.mcp_server_dir),
            env=child_env,
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                return safe_trace_payload(self._extract_result(result))

    @trace_agent("mcp_tool_call", run_type="tool", tags=["mcp-tool-sync"] )
    def call_tool_sync(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return asyncio.run(self.call_tool(tool_name, arguments))

    @staticmethod
    def _extract_result(result: Any) -> dict[str, Any]:
        # MCP SDK versions represent tool results differently.
        structured = getattr(result, "structuredContent", None) or getattr(result, "structured_content", None)
        if isinstance(structured, dict):
            return structured

        content = getattr(result, "content", None)
        if content:
            first = content[0]
            text = getattr(first, "text", None)
            if text:
                import json
                try:
                    return json.loads(text)
                except Exception:
                    return {"text": text}
            if isinstance(first, dict):
                return first

        if isinstance(result, dict):
            return result
        return {"raw_result": str(result)}


mcp_bridge = MCPBridge()

from __future__ import annotations

import json
from typing import Any

from services.config import settings
from observability.langsmith_tracing import trace_agent, safe_trace_payload


class ReasoningService:
    @trace_agent("reason_over_evidence", run_type="chain", tags=["reasoning"])
    def reason(self, *, agent_name: str, user_query: str, evidence: dict[str, Any], memory: list[dict[str, Any]]) -> str:
        if settings.openai_api_key and settings.openai_api_key != "your-openai-api-key-here":
            try:
                return self._openai_reason(agent_name, user_query, evidence, memory)
            except Exception as exc:
                return self._fallback_reason(agent_name, user_query, evidence, memory, error=str(exc))
        return self._fallback_reason(agent_name, user_query, evidence, memory)

    @trace_agent("deep_reasoning_with_gpt_5_5", run_type="llm", tags=["openai"] )
    def _openai_reason(self, agent_name: str, user_query: str, evidence: dict[str, Any], memory: list[dict[str, Any]]) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        system = f"""You are {agent_name}, an Automotive Aftermarket specialist agent.
Use only the provided evidence. Be concise, business-friendly, and actionable.
Structure the answer as: Answer, Evidence, Recommended Next Action.
If evidence is incomplete, say what is missing."""
        prompt = {
            "user_query": user_query,
            "recent_conversation": safe_trace_payload(memory[-6:]),
            "evidence": safe_trace_payload(evidence),
        }
        response = client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(prompt, default=str)},
            ],
        )
        text = getattr(response, "output_text", None)
        if text:
            return text
        return str(response)

    @trace_agent("fallback_reasoning", run_type="chain", tags=["reasoning-fallback"] )
    def _fallback_reason(self, agent_name: str, user_query: str, evidence: dict[str, Any], memory: list[dict[str, Any]], error: str | None = None) -> str:
        lines = [f"{agent_name} response for: {user_query}"]
        if error:
            lines.append(f"LLM fallback used because OpenAI reasoning failed: {error}")
        if not evidence:
            return "No evidence was returned for this question. Please provide a claim ID, VIN, dealer ID, or part number."

        if "agent_evidence" in evidence and isinstance(evidence["agent_evidence"], dict):
            lines.append("\nMulti-agent evidence summary:")
            agent_evidence = evidence.get("agent_evidence", {})
            warranty = agent_evidence.get("warranty", {}).get("evidence", {})
            service = agent_evidence.get("service", {}).get("evidence", {})
            parts = agent_evidence.get("parts", {}).get("evidence", {})

            if warranty.get("claim"):
                claim = warranty["claim"]
                lines.append(f"- Warranty: claim {claim.get('claim_id')} is {claim.get('claim_status')} with risk {claim.get('claim_risk_level')}.")
                if claim.get("rejection_reason"):
                    lines.append(f"- Warranty rejection reason: {claim.get('rejection_reason')}.")
            if service:
                analysis = service.get("analysis", {})
                summary = service.get("summary", {})
                if analysis.get("repeat_issue_indicator") is True:
                    lines.append("- Service: repeat issue indicator is TRUE based on service history.")
                elif analysis:
                    lines.append("- Service: service history was retrieved; review returned repair events for repeat pattern.")
                if summary.get("total_service_events") is not None:
                    lines.append(f"- Service events found: {summary.get('total_service_events')}.")
            if parts.get("summary"):
                part_summary = parts["summary"]
                lines.append(f"- Parts: availability status is {part_summary.get('availability_status')} with available qty {part_summary.get('total_available_qty')}.")

            if evidence.get("recommended_reasoning_focus"):
                lines.append("\nReasoning focus:")
                for item in evidence.get("recommended_reasoning_focus", []):
                    lines.append(f"- {item}")

            lines.append("\nRecommended next action:")
            if warranty and service:
                lines.append("- Compare claim symptom/component/fault evidence with prior VIN repair events before resubmission.")
                lines.append("- Attach diagnostic logs, technician notes, and repeat-repair justification if the same fault pattern is confirmed.")
            elif warranty:
                lines.append("- Resolve missing claim evidence and resubmit with technical justification if policy allows.")
            elif service:
                lines.append("- Escalate to technical support if repeat service pattern is confirmed.")
            elif parts:
                lines.append("- Use alternate/reman/transfer option if stock is limited.")
        elif "summary" in evidence and isinstance(evidence["summary"], dict):
            lines.append("\nKey summary:")
            for k, v in evidence["summary"].items():
                lines.append(f"- {k}: {v}")
        elif "recommended_reasoning_focus" in evidence:
            lines.append("\nReasoning focus:")
            for item in evidence.get("recommended_reasoning_focus", []):
                lines.append(f"- {item}")
        else:
            lines.append("\nEvidence returned successfully. Review the table/details for full context.")

        if evidence.get("found") is False:
            lines.append(f"\nNote: {evidence.get('message', 'No matching record was found.')}")
        return "\n".join(lines)


reasoning_service = ReasoningService()

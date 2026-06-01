from __future__ import annotations
import re
from typing import Any

from agents.warranty_agent import WarrantyAgent
from agents.service_agent import ServiceAgent
from agents.parts_agent import PartsAgent
from agents.deep_reasoning_agent import DeepReasoningAgent
from agents.analytics_agent import AnalyticsAgent
from services.a2a import A2AMessage
from services.entity_extractor import extract_entities
from services.memory import memory
from observability.langsmith_tracing import trace_agent, make_flow_step, safe_trace_payload


class SupervisorAgent:
    name = "Supervisor Agent"

    def __init__(self) -> None:
        self.agents = {
            "warranty": WarrantyAgent(),
            "service": ServiceAgent(),
            "parts": PartsAgent(),
            "analytics": AnalyticsAgent(),
            "deep_reasoning": DeepReasoningAgent(),
        }

    @trace_agent("supervisor_chat", run_type="chain", tags=["supervisor"])
    def chat(self, question: str, session_id: str | None = None) -> dict[str, Any]:
        """Main chat entrypoint.

        Enhancement in this version:
        - The supervisor is now a planner, not only a single-agent router.
        - Existing single-agent routing behavior is preserved for simple questions.
        - Multi-evidence questions trigger multiple specialist agents and a final
          deep-reasoning synthesis step.
        """
        state = memory.get_or_create(session_id)
        flow = [make_flow_step(1, "user", self.name, "received_query", question)]

        entities = extract_entities(question, state.last_entities)
        direct_entities = extract_entities(question, {})
        flow.append(make_flow_step(2, self.name, "entity_extractor", "extract_entities", str(entities)))

        plan = self.plan(question, entities, state.last_agent, direct_entities=direct_entities)
        execution_steps = plan.get("execution_steps", [])
        primary_agent_key = plan.get("primary_agent", "deep_reasoning")
        flow.append(
            make_flow_step(
                3,
                self.name,
                "multi_agent_planner",
                "create_execution_plan",
                f"agents={plan.get('required_agents', [])}; reason={plan.get('routing_reason')}",
            )
        )

        memory.add_message(state.session_id, "user", question, {"entities": entities, "plan": safe_trace_payload(plan)})

        agent_results: dict[str, Any] = {}
        step_no = 4

        # Execute all non-synthesis specialist steps first.
        for step in execution_steps:
            agent_key = step.get("agent")
            if agent_key == "deep_reasoning":
                continue
            agent = self.agents[agent_key]
            task = step.get("task", "specialist_lookup")

            message = A2AMessage.create(
                from_agent=self.name,
                to_agent=agent.name,
                task=task,
                user_query=question,
                session_id=state.session_id,
                entities=entities,
                memory=memory.recent_messages(state.session_id, limit=8),
                payload={
                    "routing_reason": step.get("reason", "Evidence required by supervisor plan."),
                    "plan_id": plan.get("plan_id"),
                    "execution_step": safe_trace_payload(step),
                },
            )

            flow.append(make_flow_step(step_no, self.name, agent.name, "a2a_send_message", message.message_id))
            step_no += 1
            result = agent.handle(message)
            agent_results[agent_key] = result
            flow.append(make_flow_step(step_no, agent.name, "custom_mcp_server", "mcp_tool_call", step.get("tool", task)))
            step_no += 1

        # Execute Deep Reasoning in the correct mode:
        # 1) If specialist agents already produced evidence, send an evidence_bundle
        #    for cross-agent synthesis.
        # 2) If Deep Reasoning is the only required agent, DO NOT send an empty
        #    evidence_bundle. Let DeepReasoningAgent call the MCP tool
        #    generate_aftermarket_context_pack(entity_type, entity_id).
        #
        # This fixes the dealer 360 issue where the supervisor previously created
        # an empty evidence bundle for dealer-only questions and therefore skipped
        # the MCP context-pack lookup.
        if "deep_reasoning" in plan.get("required_agents", []):
            deep_agent = self.agents["deep_reasoning"]

            deep_step = next((s for s in execution_steps if s.get("agent") == "deep_reasoning"), {})
            has_specialist_evidence = bool(agent_results)
            is_context_pack_lookup = deep_step.get("tool") == "generate_aftermarket_context_pack"

            if has_specialist_evidence:
                task = "multi_agent_evidence_synthesis"
                payload = {
                    "routing_reason": "Final answer requires synthesis across specialist agent evidence.",
                    "plan_id": plan.get("plan_id"),
                    "evidence_bundle": self._build_evidence_bundle(question, entities, plan, agent_results),
                }
                flow_detail = "combined warranty/service/parts/context evidence"
                flow_action = "synthesize_multi_agent_evidence"
            else:
                task = deep_step.get("task", "aftermarket_context_reasoning")
                payload = {
                    "routing_reason": deep_step.get("reason", "Context-pack lookup required by supervisor plan."),
                    "plan_id": plan.get("plan_id"),
                    "execution_step": safe_trace_payload(deep_step),
                }
                flow_detail = deep_step.get("tool", "generate_aftermarket_context_pack") if is_context_pack_lookup else task
                flow_action = "mcp_context_pack_lookup" if is_context_pack_lookup else "deep_reasoning_lookup"

            synthesis_message = A2AMessage.create(
                from_agent=self.name,
                to_agent=deep_agent.name,
                task=task,
                user_query=question,
                session_id=state.session_id,
                entities=entities,
                memory=memory.recent_messages(state.session_id, limit=8),
                payload=payload,
            )
            flow.append(make_flow_step(step_no, self.name, deep_agent.name, "a2a_send_message", synthesis_message.message_id))
            step_no += 1
            deep_result = deep_agent.handle(synthesis_message)
            agent_results["deep_reasoning"] = deep_result
            flow.append(make_flow_step(step_no, deep_agent.name, "custom_mcp_server_or_reasoner", flow_action, flow_detail))
            step_no += 1

        # Fallback safety: if the plan somehow produced no result, preserve old route behavior.
        if not agent_results:
            selected_agent_key, task = self.route(question, entities, state.last_agent)
            selected_agent = self.agents[selected_agent_key]
            message = A2AMessage.create(
                from_agent=self.name,
                to_agent=selected_agent.name,
                task=task,
                user_query=question,
                session_id=state.session_id,
                entities=entities,
                memory=memory.recent_messages(state.session_id, limit=8),
                payload={"routing_reason": "Fallback to legacy single-agent route."},
            )
            flow.append(make_flow_step(step_no, self.name, selected_agent.name, "a2a_send_message", message.message_id))
            agent_results[selected_agent_key] = selected_agent.handle(message)
            primary_agent_key = selected_agent_key

        final_key = "deep_reasoning" if "deep_reasoning" in agent_results else primary_agent_key
        final_result = agent_results.get(final_key) or next(iter(agent_results.values()))
        final_result = self._enrich_final_result(final_result, agent_results, plan)

        memory.add_message(state.session_id, "assistant", final_result.get("summary", ""), {"agent": final_result.get("agent"), "plan": safe_trace_payload(plan)})
        memory.update_entities(state.session_id, entities)
        state.last_agent = final_key

        flow.append(make_flow_step(step_no, self.name, "user", "final_response", final_result.get("agent", "multi_agent")))
        return self._to_chat_response(state.session_id, question, final_key, final_result, flow, plan, agent_results)

    @trace_agent("supervisor_plan", run_type="chain", tags=["routing", "planner"])
    def plan(self, question: str, entities: dict[str, str], last_agent: str | None = None, direct_entities: dict[str, str] | None = None) -> dict[str, Any]:
        """Create a multi-agent execution plan based on required evidence.

        `entities` includes inherited multi-turn context. `direct_entities` includes
        only entities explicitly present in the current user message. Planning uses
        direct entities first so an old claim/VIN does not accidentally trigger
        unrelated agents for a new part/dealer question.
        """
        q = question.lower()
        planning_entities = direct_entities or entities
        required: list[str] = []
        steps: list[dict[str, Any]] = []

        def add(agent: str, task: str, tool: str | None, reason: str) -> None:
            if agent not in required:
                required.append(agent)
                steps.append({"agent": agent, "task": task, "tool": tool, "reason": reason})

        analytics_intent = self._is_analytics_question(q, planning_entities)
        claim_intent = bool(planning_entities.get("claim_id")) or any(k in q for k in ["warranty", "claim", "reject", "resubmit", "coverage"])
        service_intent = bool(planning_entities.get("vin")) or any(k in q for k in ["vin", "fault", "symptom", "repair", "service history", "troubleshoot", "repeat repair", "same issue"])
        # Keep deterministic Parts Agent for specific part/inventory lookups only.
        # Broad analytical questions like "parts revenue by market" must go to Analytics Agent.
        parts_intent = bool(planning_entities.get("part_number")) or any(k in q for k in ["stock", "inventory", "availability", "reman", "alternate", "backorder"])
        dealer_reasoning_intent = bool(planning_entities.get("dealer_id")) or any(k in q for k in ["360", "dealer", "underperform", "root cause", "rca", "bonus", "performance"])
        reasoning_intent = any(k in q for k in [
            "why", "reason", "root cause", "rca", "risk", "recommend", "next action", "summary", "360", "compare", "impact", "repeat", "same issue", "tell me if", "analysis", "looks like"
        ])

        if analytics_intent:
            add("analytics", "databricks_genie_analytics", "databricks_genie_mcp", "Analytical aggregation/ranking/trend question requires Databricks Genie.")
        if claim_intent and not analytics_intent:
            add("warranty", "warranty_claim_lookup", "get_warranty_claim_details", "Claim or warranty evidence is required.")
        if service_intent and not analytics_intent:
            add("service", "vehicle_service_history_lookup", "get_vehicle_service_history", "VIN/service history evidence is required.")
        if parts_intent and not analytics_intent:
            add("parts", "part_availability_lookup", "check_part_availability", "Parts availability evidence is required.")
        if dealer_reasoning_intent and not (claim_intent or service_intent or parts_intent or analytics_intent):
            add("deep_reasoning", "aftermarket_context_reasoning", "generate_aftermarket_context_pack", "Dealer/market/context reasoning is required.")

        # Multi-agent synthesis is required when more than one specialist evidence source
        # is needed. For single-specialist questions, preserve the existing behavior: the
        # specialist agent performs its own reasoning over its MCP evidence.
        if len([a for a in required if a != "deep_reasoning"]) > 1:
            if "deep_reasoning" not in required:
                required.append("deep_reasoning")
                steps.append({"agent": "deep_reasoning", "task": "multi_agent_evidence_synthesis", "tool": None, "reason": "Final response requires reasoning across multiple evidence sources."})

        # Follow-up support: if no explicit evidence requirement, continue with previous agent.
        if not required and last_agent and any(k in q for k in ["why", "what about", "next", "explain", "more", "same", "show evidence"]):
            add(last_agent, "multi_turn_follow_up", None, "Follow-up question inherits previous agent context.")
            if reasoning_intent and last_agent != "deep_reasoning":
                add("deep_reasoning", "multi_turn_follow_up_synthesis", None, "Follow-up requires synthesis.")

        if not required:
            add("deep_reasoning", "general_aftermarket_reasoning", "generate_aftermarket_context_pack", "Default to deep reasoning for general aftermarket questions.")

        primary = "deep_reasoning" if "deep_reasoning" in required else required[0]
        return {
            "plan_id": f"plan-{abs(hash((question, tuple(sorted(entities.items()))))) % 1000000}",
            "query_type": "multi_agent_analysis" if len(required) > 1 else "single_agent_lookup",
            "entities": entities,
            "direct_entities": planning_entities,
            "primary_agent": primary,
            "required_agents": required,
            "execution_steps": steps,
            "routing_reason": "; ".join([s["reason"] for s in steps]),
        }

    @trace_agent("supervisor_route", run_type="chain", tags=["routing"])
    def route(self, question: str, entities: dict[str, str], last_agent: str | None = None) -> tuple[str, str]:
        """Legacy single-agent router retained for compatibility and fallback."""
        q = question.lower()
        if self._is_analytics_question(q, entities):
            return "analytics", "databricks_genie_analytics"
        if entities.get("claim_id") or any(k in q for k in ["warranty", "claim", "reject", "resubmit", "coverage"]):
            return "warranty", "warranty_claim_lookup"
        if entities.get("vin") or any(k in q for k in ["vin", "fault", "symptom", "repair", "service history", "troubleshoot"]):
            return "service", "vehicle_service_history_lookup"
        if entities.get("part_number") or any(k in q for k in ["part", "stock", "inventory", "availability", "reman", "alternate"]):
            return "parts", "part_availability_lookup"
        if entities.get("dealer_id") or any(k in q for k in ["360", "dealer", "underperform", "root cause", "rca", "bonus", "performance"]):
            return "deep_reasoning", "aftermarket_context_reasoning"
        if last_agent and any(k in q for k in ["why", "what about", "next", "explain", "more", "same", "show evidence"]):
            return last_agent, "multi_turn_follow_up"
        return "deep_reasoning", "general_aftermarket_reasoning"


    def _is_analytics_question(self, q: str, entities: dict[str, str] | None = None) -> bool:
        """Return True for aggregation/comparison/trend/ranking questions.

        Analytics questions should be answered by Databricks Genie, not by
        entity-specific operational MCP tools. Specific operational lookups still
        remain with Warranty/Service/Parts/Deep Reasoning agents.

        Important routing rule:
        - "Is part P001 available in Germany?" => Parts Agent.
        - "Which parts have the highest backorder quantity?" => Analytics Agent.
        """
        entities = entities or {}

        comparison_or_aggregation_keywords = [
            "top", "bottom", "highest", "lowest", "rank", "ranking", "leader", "leaders",
            "compare", "comparison", "trend", "monthly", "over time", "month over month",
            "by market", "by dealer", "by part", "by parts", "by part group", "by component",
            "which parts", "which dealers", "which markets", "how many", "total", "average",
            "sum", "count", "distribution", "breakdown",
        ]

        metric_keywords = [
            "revenue", "sales", "units sold", "quantity", "qty", "available quantity",
            "available qty", "backorder", "backorder quantity", "backorder qty", "stock",
            "customer satisfaction", "csat", "dims", "bonus payout", "eligibility",
            "warranty rejection rate", "claim rejection rate", "repair order", "vehicle off-road",
            "cycle time", "kpi", "performance",
        ]

        subject_keywords = [
            "market", "markets", "dealer", "dealers", "part", "parts", "part group",
            "part groups", "component", "components", "kpi", "bonus", "warranty",
            "inventory", "stock", "backorder", "revenue", "sales",
        ]

        def has_phrase(phrases: list[str]) -> bool:
            for phrase in phrases:
                # Single-word phrases should match as whole words, so "sum" does not
                # accidentally match "summary" in dealer 360 questions. Multi-word
                # phrases are searched as natural-language substrings.
                if " " in phrase:
                    if phrase in q:
                        return True
                elif re.search(rf"\b{re.escape(phrase)}\b", q):
                    return True
            return False

        has_analytics_shape = has_phrase(comparison_or_aggregation_keywords)
        has_metric_or_subject = has_phrase(metric_keywords) or has_phrase(subject_keywords)

        if not (has_analytics_shape and has_metric_or_subject):
            return False

        # Specific operational entity lookups should stay with deterministic tools
        # unless the question explicitly asks for comparison, trend, ranking, or aggregation.
        has_specific_operational_entity = bool(
            entities.get("claim_id") or entities.get("vin") or entities.get("part_number")
        )
        if has_specific_operational_entity:
            explicit_analytics = has_phrase(comparison_or_aggregation_keywords)
            return explicit_analytics

        return True

    def _build_evidence_bundle(self, question: str, entities: dict[str, str], plan: dict[str, Any], agent_results: dict[str, Any]) -> dict[str, Any]:
        return safe_trace_payload({
            "found": bool(agent_results),
            "question": question,
            "entities": entities,
            "plan": plan,
            "agent_evidence": {
                key: {
                    "agent": result.get("agent"),
                    "evidence": result.get("evidence"),
                    "summary": result.get("summary"),
                    "table": result.get("table"),
                }
                for key, result in agent_results.items()
            },
            "recommended_reasoning_focus": self._derive_reasoning_focus(agent_results),
        })

    def _derive_reasoning_focus(self, agent_results: dict[str, Any]) -> list[str]:
        focus: list[str] = []
        warranty = (agent_results.get("warranty") or {}).get("evidence", {})
        service = (agent_results.get("service") or {}).get("evidence", {})
        parts = (agent_results.get("parts") or {}).get("evidence", {})
        if warranty:
            claim = warranty.get("claim", {})
            if claim.get("claim_status"):
                focus.append(f"Warranty claim status is {claim.get('claim_status')} with risk {claim.get('claim_risk_level')}.")
            if claim.get("rejection_reason"):
                focus.append(f"Warranty rejection reason: {claim.get('rejection_reason')}.")
        if service:
            analysis = service.get("analysis", {})
            if analysis.get("repeat_issue_indicator") is True:
                focus.append("Service history indicates a repeat issue pattern.")
            elif analysis:
                focus.append("Service history should be reviewed for repeat issue evidence.")
        if parts:
            summary = parts.get("summary", {})
            if summary.get("availability_status"):
                focus.append(f"Parts availability status is {summary.get('availability_status')}.")
        if not focus:
            focus.append("Synthesize all available specialist evidence and highlight missing evidence if any.")
        return focus

    def _enrich_final_result(self, final_result: dict[str, Any], agent_results: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        enriched = dict(final_result)
        enriched["multi_agent_plan"] = safe_trace_payload(plan)
        enriched["agent_results"] = safe_trace_payload(agent_results)
        final_rows = final_result.get("table", {}).get("rows", [])
        # Preserve native single-agent tabular output exactly as returned by that agent.
        # For multi-agent synthesis, combine a small evidence table from each specialist.
        output_rows = final_rows if len(agent_results) <= 1 else (self._combined_rows(agent_results) or final_rows)
        enriched["table"] = {
            "rows": output_rows,
            "sql": final_result.get("table", {}).get("sql") if len(agent_results) <= 1 else None,
            "type": "multi_agent_evidence" if len(agent_results) > 1 else final_result.get("table", {}).get("type", "mcp_tool_result"),
        }
        enriched["suggested_questions"] = self._combined_suggested_questions(agent_results, final_result)
        return enriched

    def _combined_rows(self, agent_results: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for key, result in agent_results.items():
            if key == "deep_reasoning":
                continue
            for row in (result.get("table", {}) or {}).get("rows", [])[:5]:
                if isinstance(row, dict):
                    merged = {"source_agent": result.get("agent", key)}
                    merged.update(row)
                    rows.append(merged)
        return rows

    def _combined_suggested_questions(self, agent_results: dict[str, Any], final_result: dict[str, Any]) -> list[str]:
        questions: list[str] = []
        for result in agent_results.values():
            for q in result.get("suggested_questions", []):
                if q not in questions:
                    questions.append(q)
        for q in final_result.get("suggested_questions", []):
            if q not in questions:
                questions.append(q)
        return questions[:5]

    @trace_agent("final_response_mapping", run_type="chain", tags=["response"] )
    def _to_chat_response(
        self,
        session_id: str,
        question: str,
        agent_key: str,
        agent_result: dict[str, Any],
        agent_flow: list[dict[str, Any]] | None = None,
        plan: dict[str, Any] | None = None,
        agent_results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        evidence = agent_result.get("evidence", {})
        rows = agent_result.get("table", {}).get("rows") or []
        chart = agent_result.get("chart") or self._maybe_chart(agent_key, rows)
        trace = {
            "session_id": session_id,
            "selected_agent": agent_result.get("agent"),
            "selected_agents": (plan or {}).get("required_agents", [agent_key]),
            "a2a": agent_result.get("a2a"),
            "evidence_keys": list(evidence.keys()) if isinstance(evidence, dict) else [],
            "agent_flow": agent_flow or [],
            "multi_agent_plan": safe_trace_payload(plan or {}),
            "agent_result_keys": list((agent_results or {}).keys()),
        }
        workflow_agents = " -> ".join((plan or {}).get("required_agents", [agent_result.get("agent", agent_key)]))
        return {
            "session_id": session_id,
            "summary": agent_result.get("summary"),
            "reasoning": agent_result.get("summary"),
            "table": {"rows": rows, "sql": None, "type": agent_result.get("table", {}).get("type", "mcp_tool_result")},
            "chart": chart,
            "suggested_questions": agent_result.get("suggested_questions", []),
            "trace": trace,
            "agent_flow": agent_flow or [],
            "workflow": f"Supervisor -> A2A Planner -> {workflow_agents} -> MCP/Reasoning -> Databricks",
        }

    def _maybe_chart(self, agent_key: str, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not rows:
            return None
        if agent_key == "analytics":
            return None
        if agent_key == "parts" and "available_qty" in rows[0]:
            return {"chart_type": "bar", "title": "Available Quantity by Dealer", "x": "dealer_id", "y": ["available_qty"], "series": None, "data": rows, "notes": "Inventory data returned by Parts Agent."}
        if agent_key == "service" and "repair_order_id" in rows[0]:
            return {"chart_type": "bar", "title": "Repair Cost / Event View", "x": "repair_order_id", "y": ["repair_cost_eur"], "series": None, "data": rows, "notes": "Recent service events returned by Service Agent."}
        if agent_key == "deep_reasoning" and rows and "claim_month" in rows[0]:
            return {"chart_type": "bar", "title": "Recent Warranty Claims", "x": "claim_month", "y": ["total_claims", "rejected_claims"], "series": None, "data": rows, "notes": "Context pack trend."}
        return None


supervisor_agent = SupervisorAgent()

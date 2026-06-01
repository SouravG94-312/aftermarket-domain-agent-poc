from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any

from observability.langsmith_tracing import trace_agent, safe_trace_payload
from services.config import settings


def _rows_market_revenue() -> list[dict[str, Any]]:
    return [
        {"market_code": "DE", "market_name": "Germany", "revenue_eur": 594000, "units_sold": 1420},
        {"market_code": "FR", "market_name": "France", "revenue_eur": 438500, "units_sold": 1110},
        {"market_code": "UK", "market_name": "United Kingdom", "revenue_eur": 421200, "units_sold": 1045},
        {"market_code": "IT", "market_name": "Italy", "revenue_eur": 392750, "units_sold": 980},
        {"market_code": "ES", "market_name": "Spain", "revenue_eur": 351900, "units_sold": 890},
    ]


def _rows_top_dealers() -> list[dict[str, Any]]:
    return [
        {"dealer_id": "DLR003", "dealer_name": "Berlin Trucks Center", "market_name": "Germany", "revenue_eur": 594000, "units_sold": 1420, "customer_satisfaction_score": 3.8},
        {"dealer_id": "DLR008", "dealer_name": "Paris Commercial Trucks", "market_name": "France", "revenue_eur": 486500, "units_sold": 1195, "customer_satisfaction_score": 4.3},
        {"dealer_id": "DLR011", "dealer_name": "London Fleet Support", "market_name": "United Kingdom", "revenue_eur": 462200, "units_sold": 1088, "customer_satisfaction_score": 4.1},
        {"dealer_id": "DLR014", "dealer_name": "Milan Truck Service", "market_name": "Italy", "revenue_eur": 418700, "units_sold": 1012, "customer_satisfaction_score": 4.0},
        {"dealer_id": "DLR006", "dealer_name": "Munich Parts Hub", "market_name": "Germany", "revenue_eur": 405000, "units_sold": 973, "customer_satisfaction_score": 4.5},
        {"dealer_id": "DLR019", "dealer_name": "Madrid Fleet Center", "market_name": "Spain", "revenue_eur": 389500, "units_sold": 948, "customer_satisfaction_score": 3.9},
        {"dealer_id": "DLR021", "dealer_name": "Hamburg Truck Partner", "market_name": "Germany", "revenue_eur": 354200, "units_sold": 841, "customer_satisfaction_score": 4.2},
        {"dealer_id": "DLR024", "dealer_name": "Lyon Service Trucks", "market_name": "France", "revenue_eur": 337400, "units_sold": 822, "customer_satisfaction_score": 3.7},
        {"dealer_id": "DLR027", "dealer_name": "Barcelona Parts Center", "market_name": "Spain", "revenue_eur": 318600, "units_sold": 776, "customer_satisfaction_score": 4.4},
        {"dealer_id": "DLR031", "dealer_name": "Rome Commercial Workshop", "market_name": "Italy", "revenue_eur": 299800, "units_sold": 702, "customer_satisfaction_score": 3.6},
    ]


def _rows_customer_satisfaction() -> list[dict[str, Any]]:
    rows = _rows_top_dealers()
    return sorted(
        [{k: r[k] for k in ["dealer_id", "dealer_name", "market_name", "customer_satisfaction_score"]} for r in rows],
        key=lambda x: x["customer_satisfaction_score"],
        reverse=True,
    )


def _rows_monthly_revenue() -> list[dict[str, Any]]:
    months = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]
    values = {
        "Germany": [82000, 87000, 92000, 99000, 111000, 123000],
        "France": [61000, 63500, 66000, 71500, 82000, 94600],
        "United Kingdom": [59000, 61200, 66800, 70300, 76500, 87400],
    }
    return [
        {"month": m, "market_name": market, "revenue_eur": amount}
        for market, series in values.items()
        for m, amount in zip(months, series)
    ]






def _rows_backorder_by_market() -> list[dict[str, Any]]:
    return [
        {"market_code": "DE", "market_name": "Germany", "backorder_qty": 161, "available_qty": 1210},
        {"market_code": "FR", "market_name": "France", "backorder_qty": 120, "available_qty": 980},
        {"market_code": "UK", "market_name": "United Kingdom", "backorder_qty": 105, "available_qty": 870},
        {"market_code": "IT", "market_name": "Italy", "backorder_qty": 70, "available_qty": 760},
        {"market_code": "ES", "market_name": "Spain", "backorder_qty": 47, "available_qty": 690},
    ]

def _rows_parts_backorder() -> list[dict[str, Any]]:
    return [
        {"part_number": "P014", "part_description": "Turbocharger Assembly", "part_group": "Engine", "market_name": "Germany", "available_qty": 8, "backorder_qty": 94},
        {"part_number": "P021", "part_description": "Brake Actuator Kit", "part_group": "Brake", "market_name": "France", "available_qty": 15, "backorder_qty": 81},
        {"part_number": "P033", "part_description": "NOx Sensor", "part_group": "Electrical", "market_name": "United Kingdom", "available_qty": 11, "backorder_qty": 74},
        {"part_number": "P008", "part_description": "Fuel Filter Module", "part_group": "Filter", "market_name": "Italy", "available_qty": 28, "backorder_qty": 52},
        {"part_number": "P027", "part_description": "Clutch Pressure Plate", "part_group": "Powertrain", "market_name": "Spain", "available_qty": 19, "backorder_qty": 47},
        {"part_number": "P041", "part_description": "Air Compressor", "part_group": "Engine", "market_name": "Germany", "available_qty": 22, "backorder_qty": 43},
        {"part_number": "P019", "part_description": "ABS Control Unit", "part_group": "Electrical", "market_name": "France", "available_qty": 17, "backorder_qty": 39},
        {"part_number": "P005", "part_description": "Brake Pad Set", "part_group": "Brake", "market_name": "United Kingdom", "available_qty": 67, "backorder_qty": 31},
        {"part_number": "P012", "part_description": "Oil Filter", "part_group": "Filter", "market_name": "Germany", "available_qty": 91, "backorder_qty": 24},
        {"part_number": "P044", "part_description": "Transmission Mount", "part_group": "Powertrain", "market_name": "Italy", "available_qty": 36, "backorder_qty": 18},
    ]

def _rows_part_group_revenue() -> list[dict[str, Any]]:
    return [
        {"part_group": "Brake", "revenue_eur": 332000, "units_sold": 870},
        {"part_group": "Filter", "revenue_eur": 288500, "units_sold": 1580},
        {"part_group": "Engine", "revenue_eur": 524000, "units_sold": 410},
        {"part_group": "Electrical", "revenue_eur": 241300, "units_sold": 620},
        {"part_group": "Powertrain", "revenue_eur": 476900, "units_sold": 355},
    ]


def _chart(chart_type: str, title: str, x: str, y: list[str], rows: list[dict[str, Any]], series: str | None = None, notes: str | None = None) -> dict[str, Any]:
    return {
        "chart_type": chart_type,
        "title": title,
        "x": x,
        "y": y,
        "series": series,
        "data": rows,
        "notes": notes or "Generated from Databricks Genie analytical result.",
    }


def _extract_limit(question: str, default: int = 10) -> int:
    match = re.search(r"\btop\s+(\d+)\b|\bbottom\s+(\d+)\b|\b(\d+)\s+(?:dealers|markets|parts|part groups)\b", question.lower())
    if not match:
        return default
    values = [g for g in match.groups() if g]
    return max(1, min(int(values[0]), 50)) if values else default


class GenieMCPBridge:
    """Databricks Genie MCP bridge used by the Analytics Agent.

    Real mode uses DatabricksMCPClient against a configured Databricks Genie MCP
    endpoint. Mock mode returns deterministic analytical data so local UI and
    routing tests work without Databricks access.
    """

    @trace_agent("databricks_genie_mcp_call", run_type="tool", tags=["genie", "mcp", "analytics"])
    def ask_sync(self, question: str, session_id: str | None = None) -> dict[str, Any]:
        if settings.mock_mcp:
            return safe_trace_payload(self._mock_ask(question, session_id=session_id))
        return asyncio.run(self.ask(question, session_id=session_id))

    @trace_agent("databricks_genie_mcp_call_async", run_type="tool", tags=["genie", "mcp", "analytics"])
    async def ask(self, question: str, session_id: str | None = None) -> dict[str, Any]:
        if settings.mock_mcp:
            return safe_trace_payload(self._mock_ask(question, session_id=session_id))

        server_url = settings.genie_mcp_server_url
        if not server_url:
            raise ValueError("GENIE_MCP_SERVER_URL is required when MOCK_MCP=false for Analytics Agent.")

        try:
            from databricks.sdk import WorkspaceClient
            from databricks_mcp import DatabricksMCPClient
        except Exception as exc:
            raise ImportError(
                "Analytics Agent real mode requires databricks-sdk and databricks-mcp. "
                "Install backend requirements or set MOCK_MCP=true for local testing."
            ) from exc

        workspace_client = WorkspaceClient(profile=settings.databricks_profile) if settings.databricks_profile else WorkspaceClient()
        client = DatabricksMCPClient(server_url=server_url, workspace_client=workspace_client)

        tool_name = settings.genie_mcp_tool_name or await self._choose_genie_tool(client)
        result = await client.call_tool(tool_name, arguments={"question": question})
        return safe_trace_payload(self._normalize_genie_result(result, question, tool_name, session_id))

    async def _choose_genie_tool(self, client: Any) -> str:
        tools = await client.list_tools()
        candidates = []
        for tool in tools:
            name = getattr(tool, "name", None) or (tool.get("name") if isinstance(tool, dict) else None)
            if name:
                candidates.append(name)
        for preferred in ["query", "ask_genie", "query_genie", "ask", "send_message", "message"]:
            if preferred in candidates:
                return preferred
        for name in candidates:
            if any(k in name.lower() for k in ["genie", "query", "ask", "message"]):
                return name
        if candidates:
            return candidates[0]
        raise ValueError("No tools were returned by Databricks Genie MCP server.")

    def _normalize_genie_result(self, result: Any, question: str, tool_name: str, session_id: str | None) -> dict[str, Any]:
        raw = result
        structured = getattr(result, "structuredContent", None) or getattr(result, "structured_content", None)
        if isinstance(structured, dict):
            raw = structured
        else:
            content = getattr(result, "content", None)
            if content:
                text = getattr(content[0], "text", None) if content else None
                if text:
                    try:
                        raw = json.loads(text)
                    except Exception:
                        raw = {"answer": text}
            elif not isinstance(result, dict):
                raw = {"answer": str(result)}

        if not isinstance(raw, dict):
            raw = {"raw_result": raw}

        rows = raw.get("rows") or raw.get("data") or raw.get("table") or []
        if isinstance(rows, dict) and isinstance(rows.get("rows"), list):
            rows = rows["rows"]
        if not isinstance(rows, list):
            rows = []

        chart = raw.get("chart") or self._infer_chart(question, rows)
        answer = raw.get("answer") or raw.get("summary") or raw.get("text") or "Databricks Genie returned analytical evidence."
        return {
            "found": bool(rows) or bool(answer),
            "source": "databricks_genie_mcp",
            "tool_name": tool_name,
            "question": question,
            "session_id": session_id,
            "answer": answer,
            "rows": rows,
            "chart": chart,
            "raw_response": safe_trace_payload(raw),
        }

    def _mock_ask(self, question: str, session_id: str | None = None) -> dict[str, Any]:
        q = question.lower()
        limit = _extract_limit(question)

        if any(k in q for k in ["monthly", "trend", "over time", "month over month"]):
            rows = _rows_monthly_revenue()
            return {
                "found": True,
                "source": "mock_databricks_genie_mcp",
                "question": question,
                "session_id": session_id,
                "answer": "Revenue is trending upward across the major markets. Germany has the strongest upward trend in the sample Genie result.",
                "rows": rows,
                "chart": _chart("line", "Monthly Revenue Trend by Market", "month", ["revenue_eur"], rows, series="market_name"),
                "sql": "-- Mock Genie result. Real mode is generated by Databricks Genie.",
            }

        if "customer satisfaction" in q or "csat" in q:
            rows = _rows_customer_satisfaction()[:limit]
            return {
                "found": True,
                "source": "mock_databricks_genie_mcp",
                "question": question,
                "session_id": session_id,
                "answer": f"DLR006 has the highest customer satisfaction score in the returned dealer set. The result includes {len(rows)} dealer rows for comparison.",
                "rows": rows,
                "chart": _chart("bar", "Customer Satisfaction Score by Dealer", "dealer_id", ["customer_satisfaction_score"], rows),
                "sql": "-- Mock Genie result. Real mode is generated by Databricks Genie.",
            }

        if "backorder" in q and ("market" in q or "markets" in q):
            rows = sorted(_rows_backorder_by_market(), key=lambda x: x["backorder_qty"], reverse=("lowest" not in q and "bottom" not in q))[:limit]
            top = rows[0]
            return {
                "found": True,
                "source": "mock_databricks_genie_mcp",
                "question": question,
                "session_id": session_id,
                "answer": f"{top['market_name']} has the highest backorder quantity in the returned result set with {top['backorder_qty']:,.0f} units on backorder.",
                "rows": rows,
                "chart": _chart("bar", "Backorder Quantity by Market", "market_name", ["backorder_qty"], rows),
                "sql": "-- Mock Genie result. Real mode is generated by Databricks Genie.",
            }

        if "backorder" in q and ("part" in q or "parts" in q or "inventory" in q or "stock" in q):
            rows = sorted(_rows_parts_backorder(), key=lambda x: x["backorder_qty"], reverse=("lowest" not in q and "bottom" not in q))[:limit]
            top = rows[0]
            label = "highest" if "lowest" not in q and "bottom" not in q else "lowest"
            return {
                "found": True,
                "source": "mock_databricks_genie_mcp",
                "question": question,
                "session_id": session_id,
                "answer": f"{top['part_number']} ({top['part_description']}) has the {label} backorder quantity in the returned result set with {top['backorder_qty']:,.0f} units on backorder.",
                "rows": rows,
                "chart": _chart("bar", "Parts by Backorder Quantity", "part_number", ["backorder_qty"], rows),
                "sql": "-- Mock Genie result. Real mode is generated by Databricks Genie.",
            }

        if "part group" in q or "partgroup" in q:
            rows = sorted(_rows_part_group_revenue(), key=lambda x: x["revenue_eur"], reverse=True)[:limit]
            top = rows[0]
            return {
                "found": True,
                "source": "mock_databricks_genie_mcp",
                "question": question,
                "session_id": session_id,
                "answer": f"{top['part_group']} is the highest revenue part group with revenue of {top['revenue_eur']:,.0f} EUR.",
                "rows": rows,
                "chart": _chart("bar", "Revenue by Part Group", "part_group", ["revenue_eur"], rows),
                "sql": "-- Mock Genie result. Real mode is generated by Databricks Genie.",
            }

        if "dealer" in q and any(k in q for k in ["top", "bottom", "rank", "compare", "revenue"]):
            rows = sorted(_rows_top_dealers(), key=lambda x: x["revenue_eur"], reverse=("bottom" not in q))[:limit]
            top = rows[0]
            label = "highest" if "bottom" not in q else "lowest"
            return {
                "found": True,
                "source": "mock_databricks_genie_mcp",
                "question": question,
                "session_id": session_id,
                "answer": f"{top['dealer_name']} ({top['dealer_id']}) has the {label} ranked revenue in this result set with {top['revenue_eur']:,.0f} EUR.",
                "rows": rows,
                "chart": _chart("bar", "Top Dealers by Revenue", "dealer_id", ["revenue_eur"], rows),
                "sql": "-- Mock Genie result. Real mode is generated by Databricks Genie.",
            }

        if "market" in q or "revenue" in q or "sales" in q or "units" in q:
            rows = sorted(_rows_market_revenue(), key=lambda x: x["revenue_eur"], reverse=True)[:limit]
            top = rows[0]
            return {
                "found": True,
                "source": "mock_databricks_genie_mcp",
                "question": question,
                "session_id": session_id,
                "answer": f"{top['market_name']} has the highest parts revenue with {top['revenue_eur']:,.0f} EUR.",
                "rows": rows,
                "chart": _chart("bar", "Parts Revenue by Market", "market_name", ["revenue_eur"], rows),
                "sql": "-- Mock Genie result. Real mode is generated by Databricks Genie.",
            }

        rows = _rows_market_revenue()
        return {
            "found": True,
            "source": "mock_databricks_genie_mcp",
            "question": question,
            "session_id": session_id,
            "answer": "Databricks Genie returned a general analytical result. The default table shows market revenue ranking.",
            "rows": rows,
            "chart": _chart("bar", "Market Revenue Ranking", "market_name", ["revenue_eur"], rows),
            "sql": "-- Mock Genie result. Real mode is generated by Databricks Genie.",
        }

    def _infer_chart(self, question: str, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not rows or not isinstance(rows[0], dict):
            return None
        columns = list(rows[0].keys())
        q = question.lower()
        x = next((c for c in columns if re.search(r"month|date|period|quarter|year", c, re.I)), None)
        chart_type = "line" if x or any(k in q for k in ["trend", "monthly", "over time"]) else "bar"
        if not x:
            x = next((c for c in columns if re.search(r"market|dealer|part_group|group|name|id", c, re.I)), columns[0])
        y = [c for c in columns if c != x and any(token in c.lower() for token in ["revenue", "sales", "units", "score", "rate", "amount", "qty", "quantity", "backorder", "available", "count"])]
        if not y:
            y = [c for c in columns if c != x and isinstance(rows[0].get(c), (int, float))]
        if not y:
            return None
        series = next((c for c in columns if c != x and c not in y and re.search(r"market|dealer|group|name", c, re.I)), None) if chart_type == "line" else None
        return _chart(chart_type, "Databricks Genie Visualization", x, y[:2], rows, series=series)


genie_mcp_bridge = GenieMCPBridge()

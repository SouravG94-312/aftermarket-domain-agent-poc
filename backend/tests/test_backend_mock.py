import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ["MOCK_MCP"] = "true"

from app import create_app


def run_basic_routing_test():
    app = create_app()
    client = app.test_client()

    cases = [
        ("Why was claim WC1001 rejected?", "Warranty Agent"),
        ("Has VINDEF000123 had the same issue before?", "Service Agent"),
        ("Is part P001 available in Germany?", "Parts Agent"),
        ("Give me a 360 summary of dealer DLR003.", "Deep Reasoning Agent"),
    ]
    session_id = None
    for question, expected_agent in cases:
        response = client.post("/api/v1/chat", json={"question": question, "session_id": session_id})
        assert response.status_code == 200, response.text
        data = response.get_json()
        session_id = data["session_id"]
        assert data["summary"]
        assert data["trace"]["selected_agent"] == expected_agent, data["trace"]
        print(question, "->", data["trace"]["selected_agent"])
    print("Basic routing test passed.")


def run_dealer_360_context_pack_test():
    app = create_app()
    client = app.test_client()
    question = "Give me a 360 summary of dealer DLR003."
    response = client.post("/api/v1/chat", json={"question": question})
    assert response.status_code == 200, response.text
    data = response.get_json()
    assert data["trace"]["selected_agent"] == "Deep Reasoning Agent", data["trace"]
    assert data["trace"].get("selected_agents") == ["deep_reasoning"], data["trace"]
    assert data["trace"].get("agent_result_keys") == ["deep_reasoning"], data["trace"]
    assert data["table"]["rows"], "Dealer 360 should return a table row from the MCP context pack."
    assert data["table"]["rows"][0].get("dealer_id") == "DLR003", data["table"]["rows"]
    assert any(step.get("action") == "mcp_context_pack_lookup" for step in data.get("agent_flow", [])), data.get("agent_flow")
    assert "DLR003" in data["summary"] or "dealer" in data["summary"].lower(), data["summary"]
    print("Dealer 360 context-pack test passed.")


def run_multi_agent_planning_test():
    app = create_app()
    client = app.test_client()
    question = "Claim WC1001 is related to VINDEF000123. Check the claim status and service history, then tell me if this looks like a repeat repair issue."
    response = client.post("/api/v1/chat", json={"question": question})
    assert response.status_code == 200, response.text
    data = response.get_json()
    selected_agents = data["trace"].get("selected_agents", [])
    assert "warranty" in selected_agents, selected_agents
    assert "service" in selected_agents, selected_agents
    assert "deep_reasoning" in selected_agents, selected_agents
    assert "warranty" in data["trace"].get("agent_result_keys", []), data["trace"]
    assert "service" in data["trace"].get("agent_result_keys", []), data["trace"]
    assert "deep_reasoning" in data["trace"].get("agent_result_keys", []), data["trace"]
    assert len(data.get("agent_flow", [])) >= 7
    assert "repeat" in data["summary"].lower() or "service" in data["summary"].lower(), data["summary"]
    print("Multi-agent planning test passed:", selected_agents)


def run_analytics_agent_test():
    app = create_app()
    client = app.test_client()
    cases = [
        "Which market has the highest parts revenue?",
        "Show top 10 dealers by revenue.",
        "Compare customer satisfaction score by dealer.",
        "Show monthly revenue trend across all markets.",
        "Which parts have the highest backorder quantity?",
        "Compare backorder quantity by market.",
    ]
    for question in cases:
        response = client.post("/api/v1/chat", json={"question": question})
        assert response.status_code == 200, response.text
        data = response.get_json()
        assert data["trace"]["selected_agent"] == "Analytics Agent", data["trace"]
        assert "analytics" in data["trace"].get("selected_agents", []), data["trace"]
        assert data["table"]["rows"], f"Analytics question returned no rows: {question}"
        assert data.get("chart") and data["chart"].get("data"), f"Analytics question returned no chart: {question}"
        assert any(step.get("to") == "Analytics Agent" for step in data.get("agent_flow", [])), data.get("agent_flow")
        print(question, "->", data["trace"]["selected_agent"], data["chart"].get("chart_type"))
    print("Analytics Agent test passed.")


def run_analytics_vs_operational_parts_routing_test():
    app = create_app()
    client = app.test_client()

    analytics_question = "Which parts have the highest backorder quantity?"
    response = client.post("/api/v1/chat", json={"question": analytics_question})
    assert response.status_code == 200, response.text
    data = response.get_json()
    assert data["trace"]["selected_agent"] == "Analytics Agent", data["trace"]
    assert "analytics" in data["trace"].get("selected_agents", []), data["trace"]
    assert data["table"]["rows"], data
    assert "backorder" in data["chart"].get("y", [""])[0].lower(), data["chart"]

    operational_question = "Is part P001 available in Germany?"
    response = client.post("/api/v1/chat", json={"question": operational_question})
    assert response.status_code == 200, response.text
    data = response.get_json()
    assert data["trace"]["selected_agent"] == "Parts Agent", data["trace"]
    assert "parts" in data["trace"].get("selected_agents", []), data["trace"]
    print("Analytics vs operational Parts routing test passed.")


if __name__ == "__main__":
    run_basic_routing_test()
    run_dealer_360_context_pack_test()
    run_multi_agent_planning_test()
    run_analytics_agent_test()
    run_analytics_vs_operational_parts_routing_test()

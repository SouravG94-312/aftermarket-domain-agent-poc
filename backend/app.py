from __future__ import annotations

from flask import Flask, jsonify, request
from flask_cors import CORS

from agents.supervisor_agent import supervisor_agent
from agents.warranty_agent import WarrantyAgent
from agents.service_agent import ServiceAgent
from agents.parts_agent import PartsAgent
from agents.deep_reasoning_agent import DeepReasoningAgent
from services.a2a import A2AMessage
from services.config import settings
from services.mcp_bridge import mcp_bridge
from observability.langsmith_tracing import trace_agent


@trace_agent("chat_request", run_type="chain", tags=["flask-api"] )
def traced_chat_request(question: str, session_id: str | None = None) -> dict:
    return supervisor_agent.chat(question=question, session_id=session_id)


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, supports_credentials=True)

    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok",
            "service": "aftermarket-agent-cluster-backend",
            "mock_mcp": settings.mock_mcp,
            "openai_model": settings.openai_model,
            "mcp_server_dir": str(settings.mcp_server_dir),
            "langsmith_tracing": settings.langsmith_tracing,
            "langsmith_project": settings.langsmith_project,
        })

    @app.post("/api/v1/chat")
    def chat():
        payload = request.get_json(force=True) or {}
        question = (payload.get("question") or payload.get("message") or "").strip()
        session_id = payload.get("session_id") or payload.get("conversation_id")
        if not question:
            return jsonify({"error": "question is required"}), 400
        result = traced_chat_request(question=question, session_id=session_id)
        return jsonify(result)

    @app.post("/api/v1/mcp/call")
    def call_mcp_tool():
        payload = request.get_json(force=True) or {}
        tool_name = payload.get("tool_name")
        arguments = payload.get("arguments") or {}
        if not tool_name:
            return jsonify({"error": "tool_name is required"}), 400
        result = mcp_bridge.call_tool_sync(tool_name, arguments)
        return jsonify(result)

    @app.post("/api/v1/a2a/<agent_key>")
    def a2a_agent(agent_key: str):
        agent_map = {
            "warranty": WarrantyAgent(),
            "service": ServiceAgent(),
            "parts": PartsAgent(),
            "deep_reasoning": DeepReasoningAgent(),
        }
        agent = agent_map.get(agent_key)
        if not agent:
            return jsonify({"error": f"Unknown agent '{agent_key}'"}), 404
        payload = request.get_json(force=True) or {}
        message = A2AMessage(
            protocol=payload.get("protocol", "a2a-local-json-v1"),
            message_id=payload.get("message_id", "manual"),
            from_agent=payload.get("from_agent", "external_client"),
            to_agent=payload.get("to_agent", agent.name),
            task=payload.get("task", "manual_a2a_task"),
            user_query=payload.get("user_query", ""),
            session_id=payload.get("session_id", "manual-session"),
            entities=payload.get("entities", {}),
            memory=payload.get("memory", []),
            payload=payload.get("payload", {}),
        )
        return jsonify(agent.handle(message))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=settings.backend_host, port=settings.backend_port, debug=True)

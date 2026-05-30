from __future__ import annotations

import os
from pathlib import Path
from functools import wraps
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

try:
    from dotenv import load_dotenv
    BACKEND_ROOT = Path(__file__).resolve().parents[1]
    REPO_ROOT = BACKEND_ROOT.parent
    load_dotenv(BACKEND_ROOT / ".env")
    load_dotenv(REPO_ROOT / ".env")
except Exception:
    pass

try:
    from langsmith import traceable as _langsmith_traceable
except Exception:  # LangSmith is optional at import/runtime.
    _langsmith_traceable = None


def langsmith_enabled() -> bool:
    return os.getenv("LANGSMITH_TRACING", os.getenv("LANGCHAIN_TRACING_V2", "false")).strip().lower() in {"1", "true", "yes", "y"}


def safe_trace_payload(payload: Any, max_string_length: int = 4000) -> Any:
    """Redact secrets and trim oversized values before sending data to traces or UI."""
    blocked_keys = {
        "api_key",
        "token",
        "secret",
        "password",
        "authorization",
        "databricks_token",
        "openai_api_key",
        "langsmith_api_key",
        "client_secret",
    }

    if isinstance(payload, dict):
        cleaned: dict[str, Any] = {}
        for key, value in payload.items():
            key_str = str(key)
            if key_str.lower() in blocked_keys or any(blocked in key_str.lower() for blocked in blocked_keys):
                cleaned[key_str] = "***REDACTED***"
            else:
                cleaned[key_str] = safe_trace_payload(value, max_string_length=max_string_length)
        return cleaned

    if isinstance(payload, list):
        return [safe_trace_payload(item, max_string_length=max_string_length) for item in payload]

    if isinstance(payload, tuple):
        return tuple(safe_trace_payload(item, max_string_length=max_string_length) for item in payload)

    if isinstance(payload, str) and len(payload) > max_string_length:
        return payload[:max_string_length] + "...[truncated]"

    return payload


def trace_agent(name: str, run_type: str = "chain", tags: list[str] | None = None) -> Callable[[F], F]:
    """Optional LangSmith trace decorator.

    If LangSmith is not installed or LANGSMITH_TRACING is not true, this returns a no-op wrapper.
    This keeps local development and mock tests working without any LangSmith dependency.
    """
    base_tags = ["aftermarket-agent-cluster", "mcp", "a2a"]
    all_tags = base_tags + (tags or [])

    def decorator(func: F) -> F:
        if _langsmith_traceable is not None and langsmith_enabled():
            return _langsmith_traceable(name=name, run_type=run_type, tags=all_tags)(func)  # type: ignore[return-value]

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def make_flow_step(step: int, from_agent: str, to_agent: str, action: str, detail: str | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {
        "step": step,
        "from": from_agent,
        "to": to_agent,
        "action": action,
    }
    if detail:
        item["detail"] = detail
    return item

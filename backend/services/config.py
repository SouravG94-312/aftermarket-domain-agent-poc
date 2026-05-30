from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
load_dotenv(BACKEND_ROOT / ".env")
load_dotenv(REPO_ROOT / ".env")


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "y"}


@dataclass(frozen=True)
class Settings:
    backend_host: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    backend_port: int = int(os.getenv("BACKEND_PORT", "5000"))
    mock_mcp: bool = _bool("MOCK_MCP", False)
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.5")
    mcp_server_dir: Path = (BACKEND_ROOT / os.getenv("MCP_SERVER_DIR", "../mcp_server")).resolve()
    langsmith_tracing: bool = _bool("LANGSMITH_TRACING", False)
    langsmith_project: str | None = os.getenv("LANGSMITH_PROJECT")

    @property
    def mcp_app_path(self) -> Path:
        return self.mcp_server_dir / "app.py"


settings = Settings()

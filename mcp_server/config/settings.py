from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

@dataclass(frozen=True)
class Settings:
    catalog: str = os.getenv("CATALOG", "main")
    schema: str = os.getenv("SCHEMA", "aftermarket_agent_poc")
    databricks_server_hostname: str | None = os.getenv("DATABRICKS_SERVER_HOSTNAME")
    databricks_http_path: str | None = os.getenv("DATABRICKS_HTTP_PATH")
    databricks_token: str | None = os.getenv("DATABRICKS_TOKEN")
    mcp_transport: str = os.getenv("MCP_TRANSPORT", "stdio")
    mcp_host: str = os.getenv("MCP_HOST", "127.0.0.1")
    mcp_port: int = int(os.getenv("MCP_PORT", "8000"))

    @property
    def fq_schema(self) -> str:
        return f"{self.catalog}.{self.schema}"

    def validate_for_sql(self) -> None:
        missing = []
        if not self.databricks_server_hostname:
            missing.append("DATABRICKS_SERVER_HOSTNAME")
        if not self.databricks_http_path:
            missing.append("DATABRICKS_HTTP_PATH")
        if not self.databricks_token:
            missing.append("DATABRICKS_TOKEN")
        if missing:
            raise ValueError("Missing env vars: " + ", ".join(missing))

settings = Settings()

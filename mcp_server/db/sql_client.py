from __future__ import annotations
from contextlib import contextmanager
from typing import Any
from databricks import sql
from config.settings import settings
from db.json_utils import rows_to_json

class DatabricksSQLClient:
    def __init__(self):
        settings.validate_for_sql()
        self.server_hostname = settings.databricks_server_hostname
        self.http_path = settings.databricks_http_path
        self.access_token = settings.databricks_token

    def _connection_args(self) -> dict[str, Any]:
        return {
            "server_hostname": str(self.server_hostname).replace("https://", "").rstrip("/"),
            "http_path": self.http_path,
            "access_token": self.access_token,
        }

    @contextmanager
    def connect(self):
        conn = sql.connect(**self._connection_args())
        try:
            yield conn
        finally:
            conn.close()

    def query(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, parameters or None)
                columns = [c[0] for c in cur.description] if cur.description else []
                rows = cur.fetchall()
        return rows_to_json([dict(zip(columns, row)) for row in rows])

    def query_one(self, query: str, parameters: dict[str, Any] | None = None) -> dict | None:
        rows = self.query(query, parameters)
        return rows[0] if rows else None

    def ping(self) -> dict:
        return {"status": "ok", "result": self.query_one("SELECT current_date() AS current_date, current_user() AS current_user")}

sql_client = DatabricksSQLClient()

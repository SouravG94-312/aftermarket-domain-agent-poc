# Local Testing Steps

1. `python -m pip install -r requirements.txt`
2. `copy .env.example .env`
3. Update `.env` with SQL warehouse hostname, HTTP path, and PAT.
4. `python tests/test_sql_connection.py`
5. `python tests/test_tools_local.py`
6. `python scripts/smoke_test_stdio_client.py`

For MCP Inspector:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_http_server.ps1
```

Use URL:

```text
http://127.0.0.1:8000/mcp
```

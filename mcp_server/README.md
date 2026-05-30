# MCP Aftermarket Custom Tools - Local Final

This version hosts the custom MCP server locally and queries Databricks SQL Warehouse.

## Architecture

```text
Local Agent / VS Code
   -> Local FastMCP Server
   -> Databricks SQL Warehouse
   -> Unity Catalog Views / Delta Tables
```

## Tools

- `health_check(include_sql_ping=False)`
- `get_warranty_claim_details(claim_id)`
- `get_vehicle_service_history(vin, limit=10)`
- `check_part_availability(part_number, market_code=None, limit=10)`
- `generate_aftermarket_context_pack(entity_type, entity_id)`

## Setup

```powershell
python -m pip install -r requirements.txt
copy .env.example .env
```

Update `.env` with:

```env
DATABRICKS_SERVER_HOSTNAME=
DATABRICKS_HTTP_PATH=
DATABRICKS_TOKEN=
```

Use only PAT-based local auth here. Do not mix with `DATABRICKS_CLIENT_ID` / `DATABRICKS_CLIENT_SECRET`.

## Test

```powershell
python tests/test_sql_connection.py
python tests/test_tools_local.py
python scripts/smoke_test_stdio_client.py
```

## MCP Inspector

Terminal 1:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_http_server.ps1
```

Terminal 2:

```powershell
npx @modelcontextprotocol/inspector
```

Use:

```text
Transport: Streamable HTTP
URL: http://127.0.0.1:8000/mcp
Authentication: None
```

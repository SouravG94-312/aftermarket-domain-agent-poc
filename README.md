# Automotive Aftermarket Agent Cluster PoC

This codebase implements a local chatbot with:

- Warranty Agent connected to a custom MCP server
- Service Agent connected to a custom MCP server
- Parts Agent connected to a custom MCP server
- Supervisor Agent with routing logic
- Local A2A-style protocol between Supervisor and specialist agents
- GPT-5.5 reasoning over MCP context packs using the OpenAI API
- Conversation memory for multi-turn follow-up
- React + Vite frontend based on the provided UI codebase
- Flask backend that can run locally
- Local MCP server that accesses Databricks SQL Warehouse and Unity Catalog views

## 1. Architecture

```text
React UI
  |
  | /api/v1/chat
  v
Flask Backend
  |
  v
Supervisor Agent
  |
  | A2A local JSON message
  |------------------------------
  |              |              |
Warranty Agent  Service Agent  Parts Agent
  |              |              |
  ------------ Custom MCP Bridge ------------
                  |
                  v
        Local MCP Server over stdio
                  |
                  v
       Databricks SQL Warehouse
                  |
                  v
       Unity Catalog Views / Delta Tables
```

## 2. Folder Structure

```text
aftermarket-agent-cluster-poc/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── agents/
│   ├── services/
│   └── tests/
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│
├── mcp_server/
│   ├── app.py
│   ├── config/
│   ├── db/
│   └── tools/
│
└── README.md
```

## 3. Prerequisites

Install:

- Python 3.10+
- Node.js 18+
- Databricks SQL Warehouse access
- Databricks PAT token for local testing
- OpenAI API key for GPT-5.5 reasoning

The solution also works in mock mode without Databricks/OpenAI for UI and routing testing.

## 4. Backend Setup

Open PowerShell from the project root.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
```

Update `backend/.env`:

```env
BACKEND_HOST=127.0.0.1
BACKEND_PORT=5000
MOCK_MCP=false

MCP_SERVER_DIR=../mcp_server

OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-5.5

CATALOG=main
SCHEMA=aftermarket_agent_poc
DATABRICKS_SERVER_HOSTNAME=dbc-xxxx.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/xxxxxxxxxxxxxxxx
DATABRICKS_TOKEN=your-databricks-pat
```

### Important security note

Do not commit `.env` to GitHub. It contains secrets. Only commit `.env.example`.

## 5. Run Backend

From `backend/`:

```powershell
$env:PYTHONPATH="."
python app.py
```

Health check:

```text
http://127.0.0.1:5000/health
```

## 6. Mock Mode for Local UI Testing

Use mock mode when you want to test the full chatbot without Databricks or OpenAI.

```powershell
cd backend
$env:PYTHONPATH="."
$env:MOCK_MCP="true"
python app.py
```

Or update `backend/.env`:

```env
MOCK_MCP=true
```

## 7. Frontend Setup

Open a second terminal from the project root.

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

The Vite dev server proxies `/api` calls to:

```text
http://127.0.0.1:5000
```

## 8. Local Test Commands

### Backend mock test

```powershell
cd backend
$env:PYTHONPATH="."
$env:MOCK_MCP="true"
python tests/test_backend_mock.py
```

Expected routing:

```text
Why was claim WC1001 rejected? -> Warranty Agent
Has VINDEF000123 had the same issue before? -> Service Agent
Is part P001 available in Germany? -> Parts Agent
Give me a 360 summary of dealer DLR003. -> Deep Reasoning Agent
```

### MCP server direct tests

```powershell
cd mcp_server
$env:PYTHONPATH="."
python tests/test_sql_connection.py
python tests/test_tools_local.py
```

## 9. API Examples

### Chat API

```powershell
curl -X POST http://127.0.0.1:5000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d '{"question":"Why was claim WC1001 rejected?","session_id":"demo-session"}'
```

### Direct MCP bridge API

```powershell
curl -X POST http://127.0.0.1:5000/api/v1/mcp/call `
  -H "Content-Type: application/json" `
  -d '{"tool_name":"get_warranty_claim_details","arguments":{"claim_id":"WC1001"}}'
```

### A2A endpoint example

```powershell
curl -X POST http://127.0.0.1:5000/api/v1/a2a/warranty `
  -H "Content-Type: application/json" `
  -d '{"from_agent":"Supervisor Agent","to_agent":"Warranty Agent","task":"warranty_claim_lookup","user_query":"Why was claim WC1001 rejected?","session_id":"demo-session","entities":{"claim_id":"WC1001"},"memory":[],"payload":{}}'
```

## 10. Demo Questions

Use these in the UI:

```text
Why was claim WC1001 rejected?
Has VINDEF000123 had the same issue before?
Is part P001 available in Germany?
Give me a 360 summary of dealer DLR003.
What should be the next action?
Show the evidence used for this answer.
```

The last two questions validate multi-turn memory and follow-up routing.

## 11. How Routing Works

The Supervisor Agent extracts entities from the user query:

- `WC1001` -> claim ID -> Warranty Agent
- `VINDEF000123` -> VIN -> Service Agent
- `P001` -> part number -> Parts Agent
- `DLR003` -> dealer ID -> Deep Reasoning Agent

It then creates an A2A message envelope:

```json
{
  "protocol": "a2a-local-json-v1",
  "from_agent": "Supervisor Agent",
  "to_agent": "Warranty Agent",
  "task": "warranty_claim_lookup",
  "user_query": "Why was claim WC1001 rejected?",
  "entities": {"claim_id": "WC1001"},
  "memory": []
}
```

The specialist agent calls the custom MCP server, receives Databricks-backed evidence, and passes it to GPT-5.5 for reasoning.

## 12. GPT-5.5 Reasoning

Reasoning is handled in:

```text
backend/services/reasoning.py
```

It uses:

```env
OPENAI_MODEL=gpt-5.5
```

If `OPENAI_API_KEY` is missing or the OpenAI call fails, the backend returns deterministic fallback reasoning so the UI continues to work.

## 13. Conversation Memory

Conversation memory is implemented in:

```text
backend/services/memory.py
```

The frontend generates a session ID and passes it in every `/api/v1/chat` request.

The backend stores:

- user messages
- assistant messages
- selected agent
- extracted entities
- last agent for follow-up routing

This enables questions like:

```text
Why was claim WC1001 rejected?
What should be the next action?
```

The second question can inherit the previous claim context.

## 14. MCP Server

The MCP server is included in:

```text
mcp_server/
```

It exposes:

- `health_check`
- `get_warranty_claim_details`
- `get_vehicle_service_history`
- `check_part_availability`
- `generate_aftermarket_context_pack`

The backend calls the MCP server through stdio using the MCP Python client.

## 15. Required Databricks Views

The MCP server expects these Unity Catalog views:

```text
main.aftermarket_agent_poc.vw_warranty_claim_intelligence
main.aftermarket_agent_poc.vw_service_repair_order_intelligence
main.aftermarket_agent_poc.vw_vehicle_service_history_summary
main.aftermarket_agent_poc.vw_parts_availability_intelligence
main.aftermarket_agent_poc.vw_dealer_360_summary
main.aftermarket_agent_poc.vw_warranty_performance_summary
main.aftermarket_agent_poc.vw_sales_market_partgroup_trend
main.aftermarket_agent_poc.vw_bonus_eligibility_intelligence
```

## 16. Troubleshooting

### `ModuleNotFoundError`

Run:

```powershell
$env:PYTHONPATH="."
```

### Databricks connector import issue

```powershell
python -m pip uninstall -y databricks databricks-sql-connector
python -m pip install --upgrade databricks-sql-connector databricks-sdk
```

### UI cannot call backend

Confirm backend is running:

```text
http://127.0.0.1:5000/health
```

Confirm frontend proxy exists in `frontend/vite.config.ts`.

### No OpenAI key

Set `OPENAI_API_KEY`, or use fallback mode. The app will still work without OpenAI, but answers will be less polished.

### Need to test without Databricks

Use:

```powershell
$env:MOCK_MCP="true"
python app.py
```

## 17. Production Extension

For production, the local MCP server can be moved to:

- Databricks Apps
- Azure App Service
- Container Apps
- Kubernetes

Recommended production changes:

- OAuth instead of PAT
- Persistent conversation memory
- Central logging and tracing
- LangSmith or OpenTelemetry observability
- Databricks secrets instead of `.env`
- Proper A2A transport over HTTP/SSE or official A2A runtime

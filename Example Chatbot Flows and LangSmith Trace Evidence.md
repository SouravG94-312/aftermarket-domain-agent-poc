# Example Chatbot Agent Workflows and Trace Evidence

This section captures representative chatbot conversations to demonstrate how the Supervisor Agent routes user queries to the right domain agents, invokes MCP/Genie tools, and synthesizes the final response.

Each example includes the input question, agent workflow, output evidence, and LangSmith trace screenshots to show end-to-end observability of routing, tool calls, reasoning, and response generation.

---

### Scenario 1: Warranty Claim Rejection Analysis

#### Input Question

```text
Why was claim WC1001 rejected?
```

#### Expected Workflow

```text
User
  ↓
React Chat UI
  ↓
Flask Backend API
  ↓
Supervisor Agent
  ↓
Entity Extraction
  - claim_id = WC1001
  ↓
Routing Decision
  - selected_agent = Warranty Agent
  ↓
A2A Message
  - Supervisor Agent → Warranty Agent
  ↓
Warranty Agent
  ↓
MCP Tool Call
  - get_warranty_claim_details({"claim_id": "WC1001"})
  ↓
Custom MCP Server
  ↓
Databricks SQL Warehouse
  ↓
vw_warranty_claim_intelligence
  ↓
Warranty Agent Response
  ↓
Final Response Mapping
  ↓
UI Output
```

#### Agent Flow
<img width="1195" height="520" alt="image" src="https://github.com/user-attachments/assets/6bc77891-c2a0-4d46-8df7-4406e1d519b4" />

#### UI Output Screenshot

<img width="1835" height="807" alt="image" src="https://github.com/user-attachments/assets/28aaffdf-add9-4201-acd0-696084a36038" />


#### LangSmith Monitoring and Trace Screenshot

<img width="1582" height="975" alt="image" src="https://github.com/user-attachments/assets/98a1d2da-fd08-4855-b843-3f023c1d9743" />

---

### Scenario 2: VIN Service History and Repeat Repair Analysis

#### Input Question

```text
Has VINDEF000123 had the same issue before?
```

#### Expected Workflow

```text
User
  ↓
Supervisor Agent
  ↓
Entity Extraction
  - vin = VINDEF000123
  ↓
Routing Decision
  - selected_agent = Service Agent
  ↓
A2A Message
  - Supervisor Agent → Service Agent
  ↓
Service Agent
  ↓
MCP Tool Call
  - get_vehicle_service_history({"vin": "VINDEF000123", "limit": 5})
  ↓
Databricks SQL Warehouse
  ↓
vw_vehicle_service_history_summary
vw_service_repair_order_intelligence
  ↓
Service Agent Response
  ↓
Reasoning over service evidence
  ↓
UI Output
```

#### Agent Flow
<img width="1121" height="492" alt="image" src="https://github.com/user-attachments/assets/bc9a51d3-d130-46c4-b94a-d1b5333de3b8" />


#### UI Output Screenshot
Scenario 2 - Service History UI Output
<img width="1842" height="955" alt="image" src="https://github.com/user-attachments/assets/a40ab7ee-a077-4783-a4a8-4c356962a75d" />

#### LangSmith Monitoring and Trace Screenshot
<img width="1586" height="936" alt="image" src="https://github.com/user-attachments/assets/85a029b8-b5c1-487e-84a5-af123874aa42" />

---

### Scenario 3: Multi-Agent Claim + Service Repeat Repair Investigation

#### Input Question

```text
Claim WC1001 is related to VINDEF000123. Check the claim status and service history, then tell me if this looks like a repeat repair issue.
```

#### Expected Workflow

```text
User
  ↓
Supervisor Agent
  ↓
Entity Extraction
  - claim_id = WC1001
  - vin = VINDEF000123
  - intent = repeat_repair_analysis
  ↓
Multi-Agent Planning
  - required_agents = Warranty Agent, Service Agent, Deep Reasoning Agent
  ↓
A2A Message 1
  - Supervisor Agent → Warranty Agent
  ↓
Warranty Agent
  ↓
MCP Tool Call
  - get_warranty_claim_details({"claim_id": "WC1001"})
  ↓
A2A Message 2
  - Supervisor Agent → Service Agent
  ↓
Service Agent
  ↓
MCP Tool Call
  - get_vehicle_service_history({"vin": "VINDEF000123", "limit": 10})
  ↓
Evidence Bundle
  - warranty evidence
  - service history evidence
  ↓
A2A Message 3
  - Supervisor Agent → Deep Reasoning Agent
  ↓
GPT-5.5 Reasoning / Fallback Reasoning
  ↓
Final Synthesized Answer
```

#### Actual Agent Flow
<img width="996" height="712" alt="image" src="https://github.com/user-attachments/assets/252b84e0-c72f-42af-9461-bffe5bd14d7b" />

---
#### UI Output Screenshot
<img width="1831" height="1072" alt="image" src="https://github.com/user-attachments/assets/66ad409f-ff2d-4d49-bc5e-77db9ce32644" />

#### LangSmith Monitoring and Trace Screenshot- Scenario 4 - LangSmith Multi-Agent Trace

Expected LangSmith trace structure:

```text
chat_request
 └── supervisor_chat
     ├── memory_get_or_create
     ├── entity_extraction
     ├── supervisor_route
     ├── supervisor_plan
     ├── a2a_create_message → Warranty Agent
     ├── warranty_agent_run
     │   └── mcp_tool_call
     │       └── mcp_tool_call_async
     ├── a2a_create_message → Service Agent
     ├── service_agent_run
     │   └── mcp_tool_call
     │       └── mcp_tool_call_async
     ├── a2a_create_message → Deep Reasoning Agent
     ├── deep_reasoning_agent_run
     │   ├── specialist_agent_build_response
     │   └── reason_over_evidence
     │       └── deep_reasoning_with_gpt_5_5
     ├── memory_add_message
     ├── memory_update_entities
     └── final_response_mapping
```
<img width="1643" height="977" alt="image" src="https://github.com/user-attachments/assets/88d48d94-9cb5-4199-a14a-5b308b6e2619" />

---

### Scenario 4: Dealer 360 Deep Reasoning and Follow-Up Memory

#### Input Question

```text
Give me a 360 summary of dealer DLR003.
```

#### Expected Workflow

```text
User
  ↓
Supervisor Agent
  ↓
Entity Extraction
  - dealer_id = DLR003
  ↓
Routing Decision
  - selected_agent = Deep Reasoning Agent
  ↓
A2A Message
  - Supervisor Agent → Deep Reasoning Agent
  ↓
Deep Reasoning Agent
  ↓
MCP Tool Call
  - generate_aftermarket_context_pack({"entity_type": "dealer", "entity_id": "DLR003"})
  ↓
Databricks SQL Warehouse
  ↓
Dealer 360 / warranty / bonus / sales views
  ↓
GPT-5.5 Reasoning / Fallback Reasoning
  ↓
Final Dealer Summary
```

#### Agent Flow
<img width="747" height="337" alt="image" src="https://github.com/user-attachments/assets/0f7dd168-d3ca-4aba-96d4-a5e2a6172000" />


#### UI Output Screenshot: Scenario 5 - Dealer 360 UI Output

<img width="773" height="1018" alt="image" src="https://github.com/user-attachments/assets/adee1fac-7458-439d-b63b-ba73ccbfc6f6" />

#### LangSmith Monitoring and Trace Screenshot

Expected LangSmith trace structure:

```text
chat_request
 └── supervisor_chat
     ├── memory_get_or_create
     ├── entity_extraction
     ├── supervisor_route
     ├── a2a_create_message
     ├── deep_reasoning_agent_run
     │   ├── mcp_tool_call
     │   │   └── mcp_tool_call_async
     │   ├── specialist_agent_build_response
     │   └── reason_over_evidence
     │       └── deep_reasoning_with_gpt_5_5
     ├── memory_add_message
     ├── memory_update_entities
     └── final_response_mapping
```
<img width="1443" height="980" alt="image" src="https://github.com/user-attachments/assets/6f3dddea-660e-4a16-99e4-9f4ecbc67d7b" />

---
### Scenario 5: Testing A2A Protocol Test Scenarios

#### Input Question
**Warranty + Service Agent**

```text

Claim WC1001 is related to VINDEF000123. Check the claim status and service history, then tell me if this looks like a repeat repair issue.

Expected flow:
Supervisor → Warranty Agent
Supervisor → Service Agent
Supervisor → Final synthesized answer
```

#### Agent Flow
<img width="931" height="660" alt="image" src="https://github.com/user-attachments/assets/be55c752-8752-496f-87ac-98278c71dc5b" />

#### UI Output Screenshot
<img width="1012" height="1013" alt="image" src="https://github.com/user-attachments/assets/43cd4030-a4b8-4671-bce4-4aa235308630" />

---
### Scenario 6: Testing Analytics & Deep Reasoning Agent 

#### Input Question

```text
Show revenue comparison between Germany, France, Italy, Spain, and UK.
```

#### Agent Flow
<img width="1150" height="513" alt="image" src="https://github.com/user-attachments/assets/25109cac-65ea-4376-8a10-2c39645b6314" />


#### UI Output Screenshot
<img width="1852" height="1035" alt="image" src="https://github.com/user-attachments/assets/97fb58f5-d8d7-4d9d-a6d0-2a1faaf4ba9e" />


### Scenario 6.1: Testing Analytics & Deep Reasoning Agent 

#### Input Question

```text
Which parts have the highest backorder quantity?
```

#### Agent Flow
<img width="742" height="341" alt="image" src="https://github.com/user-attachments/assets/5fbba708-e75a-421c-a0df-4e50bddfc7a2" />


#### UI Output Screenshot
<img width="911" height="1022" alt="image" src="https://github.com/user-attachments/assets/77b56e57-14ff-4f43-9735-0a355aaf4b9d" />

### Scenario 6.2: Testing Analytics & Deep Reasoning Agent 

#### Input Question

```text
Show monthly sales trend for part group Brake.!
```

#### Agent Flow
<img width="525" height="452" alt="image" src="https://github.com/user-attachments/assets/9c05f64b-3c38-4529-b732-2bf51a0392cb" />


#### UI Output Screenshot
<img width="857" height="1027" alt="image" src="https://github.com/user-attachments/assets/e34ae6ba-5efe-479c-9338-aaeb3df2a14d" />




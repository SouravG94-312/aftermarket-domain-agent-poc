# Example Chatbot Flows and LangSmith Trace Evidence

This section can be used to document demo evidence for the chatbot, including input questions, workflow steps, UI output screenshots, and LangSmith tracing screenshots.

> Screenshot placeholders are intentionally included so you can add images after running each scenario in your local environment and LangSmith project.

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

#### Expected Agent Flow

```text
1. User → Supervisor Agent: received warranty claim question
2. Supervisor Agent → Entity Extraction: extracted claim_id = WC1001
3. Supervisor Agent → Warranty Agent: routed through A2A message
4. Warranty Agent → MCP Server: called get_warranty_claim_details
5. MCP Server → Databricks: queried warranty claim view
6. Warranty Agent → Supervisor Agent: returned claim evidence
7. Supervisor Agent → User: final explanation
```

#### Expected Output

The chatbot should explain:

- Current claim status
- Rejection reason
- Missing documents
- Claim risk level
- Recommended next action

Example answer pattern:

```text
Claim WC1001 is currently rejected and marked high risk.
The rejection reason is missing diagnostic log and late submission.
The missing documents include diagnostic log and technician notes.
Recommended next action is to collect the missing documents and resubmit with technical justification.
```

#### UI Output Screenshot

Add screenshot here:

```markdown
![Scenario 1 - Warranty Claim UI Output](./docs/screenshots/scenario_1_warranty_claim_ui.png)
```

#### LangSmith Monitoring and Trace Screenshot

Expected LangSmith trace structure:

```text
chat_request
 └── supervisor_chat
     ├── memory_get_or_create
     ├── entity_extraction
     ├── supervisor_route
     ├── a2a_create_message
     ├── warranty_agent_run
     │   └── mcp_tool_call
     │       └── mcp_tool_call_async
     ├── specialist_agent_build_response
     ├── reason_over_evidence
     ├── memory_add_message
     ├── memory_update_entities
     └── final_response_mapping
```

Add screenshot here:

```markdown
![Scenario 1 - LangSmith Warranty Trace](./docs/screenshots/scenario_1_warranty_langsmith_trace.png)
```

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

#### Expected Agent Flow

```text
1. User → Supervisor Agent: received VIN repeat issue question
2. Supervisor Agent → Entity Extraction: extracted vin = VINDEF000123
3. Supervisor Agent → Service Agent: routed through A2A message
4. Service Agent → MCP Server: called get_vehicle_service_history
5. MCP Server → Databricks: queried service summary and repair order views
6. Service Agent → Supervisor Agent: returned service evidence
7. Supervisor Agent → User: repeat repair assessment
```

#### Expected Output

The chatbot should explain:

- Number of service events
- Latest fault code or symptom
- Whether the same fault/symptom appears repeatedly
- Whether technical escalation is recommended
- Technician-friendly next step

Example answer pattern:

```text
VINDEF000123 shows multiple service events. Based on the available service history, there is a repeat issue indicator because similar symptoms or fault codes appear across prior repair orders.
Recommended next step is to compare the latest repair event with prior repair orders and escalate to technical support if the same component or fault code is recurring.
```

#### UI Output Screenshot

Add screenshot here:

```markdown
![Scenario 2 - Service History UI Output](./docs/screenshots/scenario_2_service_history_ui.png)
```

#### LangSmith Monitoring and Trace Screenshot

Expected LangSmith trace structure:

```text
chat_request
 └── supervisor_chat
     ├── memory_get_or_create
     ├── entity_extraction
     ├── supervisor_route
     ├── a2a_create_message
     ├── service_agent_run
     │   └── mcp_tool_call
     │       └── mcp_tool_call_async
     ├── specialist_agent_build_response
     ├── reason_over_evidence
     ├── memory_add_message
     ├── memory_update_entities
     └── final_response_mapping
```

Add screenshot here:

```markdown
![Scenario 2 - LangSmith Service Trace](./docs/screenshots/scenario_2_service_langsmith_trace.png)
```

---

### Scenario 3: Parts Availability and Alternate Option Analysis

#### Input Question

```text
Is part P001 available in Germany?
```

#### Expected Workflow

```text
User
  ↓
Supervisor Agent
  ↓
Entity Extraction
  - part_number = P001
  - market_code = DE
  ↓
Routing Decision
  - selected_agent = Parts Agent
  ↓
A2A Message
  - Supervisor Agent → Parts Agent
  ↓
Parts Agent
  ↓
MCP Tool Call
  - check_part_availability({"part_number": "P001", "market_code": "DE", "limit": 10})
  ↓
Databricks SQL Warehouse
  ↓
vw_parts_availability_intelligence
  ↓
Parts Agent Response
  ↓
UI Output
```

#### Expected Agent Flow

```text
1. User → Supervisor Agent: received part availability question
2. Supervisor Agent → Entity Extraction: extracted part_number = P001 and market_code = DE
3. Supervisor Agent → Parts Agent: routed through A2A message
4. Parts Agent → MCP Server: called check_part_availability
5. MCP Server → Databricks: queried parts availability view
6. Parts Agent → Supervisor Agent: returned inventory evidence
7. Supervisor Agent → User: availability and next action response
```

#### Expected Output

The chatbot should explain:

- Whether the part is available
- Available quantity
- Backorder quantity
- Best dealer/location
- Alternate part number
- Reman part number
- End-of-chain part number
- Recommended action

Example answer pattern:

```text
Part P001 is available in Germany. The best available dealer location is shown in the inventory result.
If availability is limited, the dealer should check alternate, remanufactured, or end-of-chain replacement options before escalating.
```

#### UI Output Screenshot

Add screenshot here:

```markdown
![Scenario 3 - Parts Availability UI Output](./docs/screenshots/scenario_3_parts_availability_ui.png)
```

#### LangSmith Monitoring and Trace Screenshot

Expected LangSmith trace structure:

```text
chat_request
 └── supervisor_chat
     ├── memory_get_or_create
     ├── entity_extraction
     ├── supervisor_route
     ├── a2a_create_message
     ├── parts_agent_run
     │   └── mcp_tool_call
     │       └── mcp_tool_call_async
     ├── specialist_agent_build_response
     ├── reason_over_evidence
     ├── memory_add_message
     ├── memory_update_entities
     └── final_response_mapping
```

Add screenshot here:

```markdown
![Scenario 3 - LangSmith Parts Trace](./docs/screenshots/scenario_3_parts_langsmith_trace.png)
```

---

### Scenario 4: Multi-Agent Claim + Service Repeat Repair Investigation

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

#### Expected Agent Flow

```text
1. User → Supervisor Agent: received multi-evidence repeat repair question
2. Supervisor Agent → Entity Extraction: extracted claim_id and vin
3. Supervisor Agent → Multi-Agent Planner: created execution plan
4. Supervisor Agent → Warranty Agent: requested claim evidence
5. Warranty Agent → MCP Server: called get_warranty_claim_details
6. Supervisor Agent → Service Agent: requested service history evidence
7. Service Agent → MCP Server: called get_vehicle_service_history
8. Supervisor Agent → Deep Reasoning Agent: sent combined evidence bundle
9. Deep Reasoning Agent → GPT-5.5: reasoned over claim and service evidence
10. Supervisor Agent → User: final repeat repair assessment
```

#### Expected Output

The chatbot should explain:

- Claim status and risk
- Relevant service history for the VIN
- Whether the evidence indicates a repeat repair pattern
- What evidence is missing, if any
- Recommended next action for claim and service teams

Example answer pattern:

```text
Claim WC1001 is currently rejected and marked high risk.
The claim evidence shows missing diagnostic log and late submission.

The service history for VINDEF000123 should be reviewed to identify whether the same fault code, symptom, component, labor operation, or part replacement appears across multiple repair events.

Based on the combined warranty and service evidence, this does / does not look like a repeat repair issue because ...

Recommended next action:
1. Attach missing diagnostic log and technician notes.
2. Compare the latest repair event with previous events for the same VIN.
3. If the same component or fault code is recurring, escalate to technical support before claim resubmission.
```

#### UI Output Screenshot

Add screenshot here:

```markdown
![Scenario 4 - Multi-Agent Repeat Repair UI Output](./docs/screenshots/scenario_4_multi_agent_repeat_repair_ui.png)
```

#### LangSmith Monitoring and Trace Screenshot

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

Add screenshot here:

```markdown
![Scenario 4 - LangSmith Multi-Agent Trace](./docs/screenshots/scenario_4_multi_agent_langsmith_trace.png)
```

---

### Scenario 5: Dealer 360 Deep Reasoning and Follow-Up Memory

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

#### Expected Agent Flow

```text
1. User → Supervisor Agent: received dealer 360 question
2. Supervisor Agent → Entity Extraction: extracted dealer_id = DLR003
3. Supervisor Agent → Deep Reasoning Agent: requested dealer context pack and synthesis
4. Deep Reasoning Agent → MCP Server: called generate_aftermarket_context_pack
5. MCP Server → Databricks: queried dealer 360, warranty, bonus, and sales views
6. Deep Reasoning Agent → GPT-5.5: synthesized summary and risks
7. Supervisor Agent → User: final dealer 360 summary
```

#### Expected Output

The chatbot should explain:

- Dealer performance summary
- Warranty risk
- Bonus eligibility status
- Customer satisfaction or DIMS compliance risk
- Top recommended actions

Example answer pattern:

```text
Dealer DLR003 shows a combination of commercial performance and operational risk.
The main risk areas are warranty rejection rate, bonus eligibility, and service process compliance.

Recommended actions:
1. Reduce warranty rejection drivers by improving document completeness.
2. Review service history and repeat repair patterns.
3. Improve KPI gaps impacting bonus eligibility.
```

#### Follow-Up Input Question

```text
What are the top 3 actions for this dealer?
```

#### Expected Follow-Up Workflow

```text
User follow-up
  ↓
Conversation Memory
  - previous dealer_id = DLR003
  ↓
Supervisor Agent
  ↓
Deep Reasoning Agent
  ↓
Final action-oriented answer
```

#### UI Output Screenshot

Add screenshot here:

```markdown
![Scenario 5 - Dealer 360 UI Output](./docs/screenshots/scenario_5_dealer_360_ui.png)
```

#### Follow-Up UI Output Screenshot

Add screenshot here:

```markdown
![Scenario 5 - Dealer 360 Follow-Up UI Output](./docs/screenshots/scenario_5_dealer_360_followup_ui.png)
```

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

Add screenshot here:

```markdown
![Scenario 5 - LangSmith Dealer Trace](./docs/screenshots/scenario_5_dealer_360_langsmith_trace.png)
```

---

### Recommended Screenshot Folder Structure

Create this folder in the repository:

```text
docs/
└── screenshots/
    ├── scenario_1_warranty_claim_ui.png
    ├── scenario_1_warranty_langsmith_trace.png
    ├── scenario_2_service_history_ui.png
    ├── scenario_2_service_langsmith_trace.png
    ├── scenario_3_parts_availability_ui.png
    ├── scenario_3_parts_langsmith_trace.png
    ├── scenario_4_multi_agent_repeat_repair_ui.png
    ├── scenario_4_multi_agent_langsmith_trace.png
    ├── scenario_5_dealer_360_ui.png
    ├── scenario_5_dealer_360_followup_ui.png
    └── scenario_5_dealer_360_langsmith_trace.png
```

### How to Capture Screenshots

#### UI screenshot

1. Run backend and frontend.
2. Open the chatbot UI.
3. Ask the scenario question.
4. Capture the answer area, table view, and agent communication flow panel.
5. Save the image under `docs/screenshots/`.

#### LangSmith screenshot

1. Enable LangSmith tracing.
2. Ask the scenario question.
3. Open the LangSmith project.
4. Open the latest `chat_request` trace.
5. Expand the waterfall view.
6. Capture the trace showing Supervisor, A2A, specialist agent, MCP tool, and reasoning calls.
7. Save the image under `docs/screenshots/`.

### Recommended Demo Evidence Checklist

Use this checklist before presenting the PoC:

```text
[ ] Scenario 1 UI screenshot captured
[ ] Scenario 1 LangSmith trace screenshot captured
[ ] Scenario 2 UI screenshot captured
[ ] Scenario 2 LangSmith trace screenshot captured
[ ] Scenario 3 UI screenshot captured
[ ] Scenario 3 LangSmith trace screenshot captured
[ ] Scenario 4 UI screenshot captured
[ ] Scenario 4 LangSmith multi-agent trace screenshot captured
[ ] Scenario 5 UI screenshot captured
[ ] Scenario 5 follow-up memory screenshot captured
[ ] Scenario 5 LangSmith trace screenshot captured
```


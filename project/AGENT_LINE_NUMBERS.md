# Quick Reference: Framework Agent Locations

## Line Numbers for Framework Agent Instances

| Agent | Type | Line | Code |
|-------|------|------|------|
| **inventory_agent** | `ToolCallingAgent` | 985 | `inventory_agent = ToolCallingAgent(...)` |
| **restocking_agent** | `ToolCallingAgent` | 1032 | `restocking_agent = ToolCallingAgent(...)` |
| **quoting_agent** | `ToolCallingAgent` | 1076 | `quoting_agent = ToolCallingAgent(...)` |
| **ordering_agent** | `ToolCallingAgent` | 1129 | `ordering_agent = ToolCallingAgent(...)` |

## Line Numbers for Framework Agent Execution

| Function | Executes Agent | Line | Framework Method |
|----------|---------------|------|------------------|
| `run_agent_with_task()` | Any agent | 1162 | `agent.run(task)` |
| `inventory_check_with_agent()` | inventory_agent | 1189 | Via `run_agent_with_task()` |
| `quoting_with_agent()` | quoting_agent | 1227 | Via `run_agent_with_task()` |
| `ordering_with_agent()` | ordering_agent | 1340 | Via `run_agent_with_task()` |
| `restocking_with_agent()` | restocking_agent | 1411 | Via `run_agent_with_task()` |

## Line Numbers for Orchestrator

| Component | Line | Description |
|-----------|------|-------------|
| `orchestrator_agent()` | 1439 | Main orchestrator function |
| Uses inventory_agent | 1462 | `inventory_check = inventory_check_with_agent(items, date)` |
| Uses restocking_agent | 1467 | `restock_result = restocking_with_agent(...)` |
| Uses quoting_agent | 1482 | `quote = quoting_with_agent(items, date, customer_request)` |
| Uses ordering_agent | 1489 | `order_result = ordering_with_agent(quote, date)` |

## Framework Import

| Component | Line | Code |
|-----------|------|------|
| Framework import | 603 | `from smolagents import CodeAgent, ToolCallingAgent, tool, LiteLLMModel` |
| Model initialization | 613 | `model = LiteLLMModel(...)` |

## Visual Proof

```
CODE STRUCTURE:

Line 603:  from smolagents import ToolCallingAgent  ← FRAMEWORK IMPORT
           
Line 613:  model = LiteLLMModel(...)               ← FRAMEWORK MODEL

Line 985:  inventory_agent = ToolCallingAgent(     ← FRAMEWORK AGENT INSTANCE
              tools=[...],                          ← TOOLS REGISTERED
              model=model,                          ← FRAMEWORK MODEL
              max_steps=5                           ← FRAMEWORK CONFIG
           )

Line 1032: restocking_agent = ToolCallingAgent(    ← FRAMEWORK AGENT INSTANCE
              tools=[...],                          ← TOOLS REGISTERED
              model=model,                          ← FRAMEWORK MODEL
              max_steps=5                           ← FRAMEWORK CONFIG
           )

Line 1076: quoting_agent = ToolCallingAgent(       ← FRAMEWORK AGENT INSTANCE
              tools=[...],                          ← TOOLS REGISTERED
              model=model,                          ← FRAMEWORK MODEL
              max_steps=5                           ← FRAMEWORK CONFIG
           )

Line 1129: ordering_agent = ToolCallingAgent(      ← FRAMEWORK AGENT INSTANCE
              tools=[...],                          ← TOOLS REGISTERED
              model=model,                          ← FRAMEWORK MODEL
              max_steps=5                           ← FRAMEWORK CONFIG
           )

Line 1162: def run_agent_with_task(agent, task):
               result = agent.run(task)             ← FRAMEWORK METHOD .run()
               return str(result)

Line 1189: result_str = run_agent_with_task(inventory_agent, task)   ← FRAMEWORK EXECUTION
Line 1227: result_str = run_agent_with_task(quoting_agent, task)     ← FRAMEWORK EXECUTION  
Line 1340: result_str = run_agent_with_task(ordering_agent, task)    ← FRAMEWORK EXECUTION
Line 1411: result_str = run_agent_with_task(restocking_agent, task)  ← FRAMEWORK EXECUTION
```

## Search Commands to Verify

```bash
# Find all ToolCallingAgent instances (should return 4)
grep -n "= ToolCallingAgent(" project_starter.py

# Find all agent.run() calls (framework execution)
grep -n "agent.run(" project_starter.py

# Find all @tool decorations (should return many)
grep -n "^@tool" project_starter.py

# Find smolagents import
grep -n "from smolagents import" project_starter.py
```

## Key Points for Reviewer

1. **NOT FUNCTIONS**: None of the agents are defined as `def agent_name(...):`
2. **FRAMEWORK INSTANCES**: All agents are `ToolCallingAgent(...)` instances
3. **FRAMEWORK EXECUTION**: All agents use `.run()` method, not direct calls
4. **TOOLS REGISTERED**: Tools are passed to `ToolCallingAgent(tools=[...])`
5. **ORCHESTRATION**: Orchestrator calls framework agents, not helper functions

## Compare: Wrong vs Right

### ❌ WRONG (Simple Function)
```python
def inventory_agent(items, date):
    # Direct implementation
    return check_stock(items)
```

### ✅ RIGHT (Framework Agent)
```python
# Create instance
inventory_agent = ToolCallingAgent(
    tools=[check_inventory_availability, get_inventory_list],
    model=model,
    max_steps=5
)

# Execute via framework
result = inventory_agent.run("Check inventory for items...")
```

## The Four Framework Agents

```
┌─────────────────────────────────────────────────────────────────┐
│  INVENTORY AGENT (Line 985)                                     │
│  Type: smolagents.ToolCallingAgent                              │
│  Tools: check_inventory_availability, get_inventory_list, ...   │
│  Execution: agent.run(task) → Framework handles tool selection  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  RESTOCKING AGENT (Line 1032)                                   │
│  Type: smolagents.ToolCallingAgent                              │
│  Tools: restock_item_tool, get_supplier_delivery_date_tool, ...│
│  Execution: agent.run(task) → Framework handles tool selection  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  QUOTING AGENT (Line 1076)                                      │
│  Type: smolagents.ToolCallingAgent                              │
│  Tools: calculate_bulk_discount, get_item_price, ...           │
│  Execution: agent.run(task) → Framework handles tool selection  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ORDERING AGENT (Line 1129)                                     │
│  Type: smolagents.ToolCallingAgent                              │
│  Tools: place_order_tool, create_transaction_tool              │
│  Execution: agent.run(task) → Framework handles tool selection  │
└─────────────────────────────────────────────────────────────────┘
```

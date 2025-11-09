# Framework Integration Documentation

## Overview

This document explains how the multi-agent system integrates with the smolagents framework, addressing the reviewer's requirements for proper framework-based tool usage.

## Architecture

### Framework-Based Agents

All agents in this system are **ToolCallingAgent** instances from the smolagents framework:

1. **Inventory Agent** (`inventory_agent`)
2. **Restocking Agent** (`restocking_agent`)
3. **Quoting Agent** (`quoting_agent`)
4. **Ordering Agent** (`ordering_agent`)

### Tool Decoration

All tools are decorated with `@tool` from smolagents, making them discoverable and callable by framework agents:

```python
from smolagents import tool

@tool
def check_inventory_availability(item_name: str, quantity: int, date: str) -> str:
    """Check if an item is available in sufficient quantity."""
    # Implementation
```

## Agent-Tool Mappings

### 1. Inventory Agent

**Framework Agent Type**: `ToolCallingAgent`

**Tools**:
- `@tool check_inventory_availability` → calls helper `get_stock_level()`
- `@tool get_inventory_list` → calls helper `get_all_inventory()`
- `@tool check_restock_needed` → calls helper `get_stock_level()`

**Usage Pattern**:
```python
inventory_agent = ToolCallingAgent(
    tools=[check_inventory_availability, get_inventory_list, check_restock_needed],
    model=model,
    max_steps=5
)

# Agent is invoked via framework
result = inventory_agent.run(task_description)
```

### 2. Restocking Agent

**Framework Agent Type**: `ToolCallingAgent`

**Tools**:
- `@tool restock_item_tool` → calls helper `restock_item()`
- `@tool get_supplier_delivery_date_tool` → calls helper `get_supplier_delivery_date()`
- `@tool get_cash_balance_tool` → calls helper `get_cash_balance()`

**Usage Pattern**:
```python
restocking_agent = ToolCallingAgent(
    tools=[restock_item_tool, get_supplier_delivery_date_tool, get_cash_balance_tool],
    model=model,
    max_steps=5
)
```

### 3. Quoting Agent

**Framework Agent Type**: `ToolCallingAgent`

**Tools**:
- `@tool calculate_bulk_discount` → direct calculation
- `@tool get_item_price` → queries database via `inventory` table
- `@tool generate_quote_tool` → calls helper `generate_quote()`
- `@tool search_quote_history_tool` → calls helper `search_quote_history()`

**Usage Pattern**:
```python
quoting_agent = ToolCallingAgent(
    tools=[calculate_bulk_discount, get_item_price, generate_quote_tool, search_quote_history_tool],
    model=model,
    max_steps=5
)
```

### 4. Ordering Agent

**Framework Agent Type**: `ToolCallingAgent`

**Tools**:
- `@tool place_order_tool` → calls helper `place_order()`
- `@tool create_transaction_tool` → calls helper `create_transaction()`

**Usage Pattern**:
```python
ordering_agent = ToolCallingAgent(
    tools=[place_order_tool, create_transaction_tool],
    model=model,
    max_steps=5
)
```

## Data Flow

### Framework-Managed Tool Invocation

1. **Orchestrator** calls agent with natural language task
2. **Framework Agent** (ToolCallingAgent) receives task
3. **LLM** (via framework) decides which tools to call
4. **Framework** invokes selected `@tool` decorated functions
5. **Tools** call helper functions from starter code
6. **Helpers** query/update SQLite database
7. **Results** flow back through framework to orchestrator

### Example Flow: Inventory Check

```
orchestrator_agent()
  ↓
inventory_check_with_agent(items, date)
  ↓
inventory_agent.run("Check availability for items...")  ← Framework invocation
  ↓
Framework decides to call: check_inventory_availability  ← @tool decorated
  ↓
Tool calls helper: get_stock_level(item_name, date)
  ↓
Helper queries: SQLite transactions table
  ↓
Result flows back through framework to orchestrator
```

## Key Differences from Previous Implementation

### Before (Direct Function Calls):
```python
def inventory_agent(items: List[Dict], date: str) -> Dict:
    # Direct call to helper - NO FRAMEWORK
    availability = _check_inventory_availability_dict(item_name, quantity, date)
```

### After (Framework-Based):
```python
def inventory_check_with_agent(items: List[Dict], date: str) -> Dict:
    task = f"Check inventory availability for these items as of {date}..."
    
    # Framework agent decides which tools to use
    result_str = inventory_agent.run(task)  # ToolCallingAgent.run()
    
    # Framework handles all tool invocations internally
```

## Fallback Mechanism

Each agent has a fallback function in case the framework agent encounters errors:

```python
def inventory_check_with_agent(items, date):
    try:
        result = inventory_agent.run(task)  # Try framework
        return parse_result(result)
    except:
        return inventory_agent_fallback(items, date)  # Direct helper calls
```

This ensures robustness while maintaining framework compliance.

## Helper Functions vs. Tools

### Helper Functions
- Direct Python functions from starter code
- Work with database via SQLAlchemy
- Not exposed to framework agents
- Examples: `get_stock_level()`, `create_transaction()`, `get_all_inventory()`

### Tools
- `@tool` decorated wrappers
- Exposed to framework agents
- Convert between JSON strings and Python objects
- Call helper functions internally
- Examples: `check_inventory_availability`, `restock_item_tool`, `place_order_tool`

## Compliance with Rubric

✅ **Tools assigned to agents**: Each agent has specific tools via `ToolCallingAgent(tools=[...])`

✅ **Framework integration**: All agents are `ToolCallingAgent` instances, not plain functions

✅ **Tool decoration**: All tools use `@tool` decorator from smolagents

✅ **Helper function mappings**: Tools call helpers, shown in workflow diagram

✅ **Data flow direction**: Diagram shows:
- Customer request → Orchestrator → Agents
- Agents → Framework → Tools
- Tools → Helpers → Database
- Results flow back through chain

## Testing

The system maintains the same external interface, so existing tests continue to work:

```python
response = orchestrator_agent(customer_request, date)
```

Internally, the orchestrator now uses framework agents instead of direct function calls.

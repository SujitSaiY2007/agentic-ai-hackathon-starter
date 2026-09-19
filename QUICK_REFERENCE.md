# Agno Hackathon Quick Reference

## Agent (Default Model)
```python
Agent(model=openrouter())
```

## Agent (Specific OpenRouter Model)
```python
# Pass any model string or preset from MODELS
Agent(model=openrouter("anthropic/claude-3.5-sonnet"))
Agent(model=openrouter(MODELS.DEEPSEEK_R1))
Agent(model=openrouter(MODELS.LLAMA_3_3_70B))
```

## Agent with Fallback Routing (Auto-Failover)
```python
# Automatically tries fallback models if the primary is rate-limited or down
Agent(
    model=openrouter(
        id="anthropic/claude-3.5-sonnet",
        fallback_models=["openai/gpt-4o", "deepseek/deepseek-chat"],
    )
)
```

## Tool
```python
def my_tool(x: str) -> str:
    """Describe what this tool does."""
    return x

Agent(tools=[my_tool])
```

## Structured output
```python
class Result(BaseModel):
    answer: str

Agent(output_schema=Result)
```

## RAG
```python
knowledge = Knowledge(vector_db=ChromaDb(...))
knowledge.insert(path="data/file.pdf")
Agent(knowledge=knowledge, search_knowledge=True)
```

## Storage / history
```python
Agent(
    db=SqliteDb(db_file="tmp/agent.db"),
    add_history_to_context=True,
)
```

## Memory
```python
Agent(
    db=SqliteDb(db_file="tmp/agent.db"),
    update_memory_on_run=True,
)
```

## Team
```python
Team(members=[agent1, agent2], model=openrouter())
```

## Workflow
```python
Workflow(steps=[agent1, agent2])
```

## Guardrails
```python
Agent(pre_hooks=[PIIDetectionGuardrail(), PromptInjectionGuardrail()])
```

## HITL
```python
@tool(requires_confirmation=True)
def sensitive_tool(...): ...
```

## MCP
```python
MCPTools(transport="streamable-http", url="...")
```

## AgentOS
```python
agent_os = AgentOS(agents=[agent], db=db)
app = agent_os.get_app()
agent_os.serve(app="app:app")
```

## Decision rule

```text
One agent + tools       → default
RAG                     → proprietary/document knowledge needed
Structured output       → machine-readable result needed
Memory                  → user preferences/facts across sessions
Workflow                → fixed process
Team                    → dynamic collaboration
MCP                     → existing MCP server
HITL                    → risky external side effect
Guardrails              → untrusted/risky input
AgentOS                 → expose runtime/API/UI
```

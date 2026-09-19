# Agentic AI Hackathon Starter — Python + Agno + OpenRouter

A reusable, hackathon-oriented Agno starter project. The goal is to learn and reuse small building blocks instead of searching documentation during the event.

## Stack

- Python 3.12
- uv
- Agno 3.x
- OpenRouter (supporting GPT-4o-mini, Claude 3.5 Sonnet, Llama 3.3, DeepSeek, etc.)
- SQLite for local persistence
- ChromaDB for local RAG
- Pydantic for structured outputs
- AgentOS for the runtime/API
- Optional MCP support

## Project map

```text
agentic_ai_hackathon_starter/
├── app.py                     # Minimal AgentOS server
├── run_demo.py                # Run individual learning modules
├── config.py                  # .env loading + OpenRouter configuration
├── pyproject.toml
├── .env.example
├── .gitignore
├── data/
│   └── knowledge.md           # Tiny local RAG dataset
├── demos/
│   ├── 01_basic_agent.py
│   ├── 02_tools.py
│   ├── 03_structured_output.py
│   ├── 04_rag.py
│   ├── 05_memory_and_storage.py
│   ├── 06_workflow.py
│   ├── 07_team.py
│   ├── 08_guardrails.py
│   ├── 09_hitl.py
│   ├── 10_mcp.py
│   └── 11_eval.py
└── tmp/                      # local DB/vector data; ignored by Git
```

## One-time setup in Antigravity

Open this folder as the workspace in Antigravity, then open a PowerShell terminal in the project root.

### 1. Check Python

```powershell
python --version
```

You want Python 3.12.x.

### 2. Check uv

```powershell
uv --version
```

If it is not installed, install uv using the official installer before continuing.

### 3. Create the environment

```powershell
uv venv --python 3.12
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install the starter

```powershell
uv sync
```

This installs the pinned project dependencies from `pyproject.toml`.

### 5. Create `.env`

Copy `.env.example` to `.env` and put your OpenRouter API key in it.

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
# Optional model override (defaults to openai/gpt-4o-mini)
OPENROUTER_MODEL=openai/gpt-4o-mini
```

## First run

The safest first run is the plain agent:

```powershell
uv run python run_demo.py basic
```

Then try the modules in this order:

```powershell
uv run python run_demo.py tools
uv run python run_demo.py structured
uv run python run_demo.py rag
uv run python run_demo.py memory
uv run python run_demo.py workflow
uv run python run_demo.py team
uv run python run_demo.py guardrails
uv run python run_demo.py hitl
uv run python run_demo.py mcp
uv run python run_demo.py eval
```

Some modules intentionally require an external MCP server or additional runtime services. The code is included as a reference pattern, but the basic, tools, structured, RAG, workflow and team modules are the core learning path.

## Start AgentOS

```powershell
uv run python app.py
```

Then open:

- Health: http://localhost:7777/health
- API docs: http://localhost:7777/docs
- Info: http://localhost:7777/info

The Agno Agent UI can be connected to `http://localhost:7777` when you have the UI available.

## Hackathon rule of thumb

Start with:

```text
Agent
  + Tools
  + RAG (only if required)
  + Structured Output
  + SQLite persistence
```

Then add only what the problem needs:

```text
Workflow → fixed process
Team     → dynamic multi-agent collaboration
MCP      → existing external MCP integration
HITL     → sensitive/irreversible action
Guardrail→ risky/untrusted input
```

Do not build a multi-agent architecture just because the event is called an Agentic AI Hackathon.

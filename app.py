"""Minimal AgentOS runtime.

Start with:
    uv run python app.py
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.os import AgentOS

from config import DB_PATH
from model import MODELS, openrouter

db = SqliteDb(db_file=DB_PATH)

# 1. General Fast Assistant (uses default OPENROUTER_MODEL or gpt-4o-mini)
general_agent = Agent(
    id="general-assistant",
    name="General Assistant (Fast)",
    model=openrouter(),
    db=db,
    add_history_to_context=True,
    num_history_runs=5,
    markdown=True,
    instructions=[
        "You are a fast, practical hackathon assistant.",
        "Prefer concise, implementation-ready answers.",
    ],
)

# 2. Deep Reasoning Agent (powered by DeepSeek R1 / o3-mini)
reasoning_agent = Agent(
    id="reasoning-assistant",
    name="Deep Reasoning Assistant",
    model=openrouter(
        id=MODELS.DEEPSEEK_R1,
        fallback_models=[MODELS.O3_MINI, MODELS.GPT_4O_MINI],
    ),
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
    markdown=True,
    instructions=[
        "You are an expert analytical reasoner and problem solver.",
        "Break complex algorithmic and architectural problems down step-by-step.",
    ],
)

# 3. Claude Intelligence Agent (powered by Claude 3.5/3.7 Sonnet)
claude_agent = Agent(
    id="claude-assistant",
    name="Claude Intelligence Assistant",
    model=openrouter(
        id=MODELS.CLAUDE_3_5_SONNET,
        fallback_models=[MODELS.GPT_4O],
    ),
    db=db,
    add_history_to_context=True,
    num_history_runs=5,
    markdown=True,
    instructions=[
        "You are a high-capability architectural planner and writer.",
        "Produce detailed, elegant, production-grade agent architectures.",
    ],
)

agent_os = AgentOS(
    agents=[general_agent, reasoning_agent, claude_agent],
    db=db,
    tracing=True,
)

app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="app:app", host="127.0.0.1", port=7777, reload=True)

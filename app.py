"""Minimal AgentOS runtime.

Start with:
    uv run python app.py
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.os import AgentOS

from config import DB_PATH
from model import gemini


db = SqliteDb(db_file=DB_PATH)

hackathon_agent = Agent(
    id="hackathon-assistant",
    name="Hackathon Assistant",
    model=gemini(),
    db=db,
    add_history_to_context=True,
    num_history_runs=5,
    markdown=True,
    instructions=[
        "You are a practical Agentic AI hackathon assistant.",
        "Prefer concise, implementation-ready answers.",
        "Never invent tool results or citations.",
    ],
)

agent_os = AgentOS(
    agents=[hackathon_agent],
    db=db,
    tracing=True,
)

app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="app:app", host="127.0.0.1", port=7777, reload=True)

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from config import DB_PATH
from model import openrouter


def run() -> None:
    db = SqliteDb(db_file=DB_PATH)

    agent = Agent(
        name="Persistent Agent",
        model=openrouter(),
        db=db,
        add_history_to_context=True,
        num_history_runs=5,
        update_memory_on_run=True,
        markdown=True,
        instructions="Remember useful user preferences; do not store secrets.",
    )

    user_id = "demo-user"
    session_id = "memory-demo"

    agent.print_response(
        "I prefer concise technical explanations and I am preparing for an AI hackathon.",
        user_id=user_id,
        session_id=session_id,
    )
    agent.print_response(
        "What style of explanations do I prefer?",
        user_id=user_id,
        session_id=session_id,
    )

    print("\nStored user memories:")
    print(agent.get_user_memories(user_id=user_id))

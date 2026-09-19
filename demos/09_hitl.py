from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.tools import tool

from config import DB_PATH
from model import gemini


@tool(requires_confirmation=True)
def publish_demo(text: str) -> str:
    """Simulate publishing text to an external system."""
    return f"PUBLISHED: {text}"


def run() -> None:
    agent = Agent(
        name="Human Approval Agent",
        model=gemini(),
        tools=[publish_demo],
        db=SqliteDb(db_file=DB_PATH),
        markdown=True,
    )

    response = agent.run("Draft and publish a two-line hackathon announcement.")

    for requirement in response.active_requirements or []:
        if requirement.needs_confirmation:
            print("\nTool approval required:")
            print(requirement.tool_execution.tool_name)
            print(requirement.tool_execution.tool_args)
            choice = input("Approve? [y/N]: ").strip().lower()
            if choice == "y":
                requirement.confirm()
            else:
                requirement.reject()

    if response.active_requirements:
        response = agent.continue_run(
            run_id=response.run_id,
            requirements=response.requirements,
        )

    print(response.content)

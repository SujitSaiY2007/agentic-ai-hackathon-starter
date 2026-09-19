from agno.agent import Agent
from agno.workflow import Workflow

from model import gemini


def run() -> None:
    researcher = Agent(
        name="Researcher",
        model=gemini(),
        instructions="Identify the key technical requirements for the requested project.",
    )

    writer = Agent(
        name="Planner",
        model=gemini(),
        instructions="Turn the research into a concise implementation plan.",
    )

    workflow = Workflow(
        name="Hackathon Planning Workflow",
        steps=[researcher, writer],
    )

    workflow.print_response(
        "Plan a small agent that answers questions over a college event rulebook and drafts responses.",
        markdown=True,
    )

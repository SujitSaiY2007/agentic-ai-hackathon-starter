from agno.agent import Agent
from agno.team import Team

from model import gemini


def run() -> None:
    researcher = Agent(
        name="Researcher",
        model=gemini(),
        role="Research the problem and identify relevant information.",
    )
    architect = Agent(
        name="Architect",
        model=gemini(),
        role="Design the smallest technical architecture that solves the problem.",
    )

    team = Team(
        name="Hackathon Architecture Team",
        model=gemini(),
        members=[researcher, architect],
        instructions=[
            "Coordinate the members and produce one implementation plan.",
            "Avoid unnecessary agents and infrastructure.",
        ],
        markdown=True,
    )

    team.print_response(
        "Design a hackathon architecture for a document-grounded student support assistant.",
        stream=True,
    )

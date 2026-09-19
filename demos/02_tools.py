from agno.agent import Agent
from agno.tools.websearch import WebSearchTools

from model import openrouter


def get_hackathon_advice(topic: str) -> str:
    """Return deterministic advice for a hackathon topic."""
    return f"For {topic}, start with the smallest working agent, then add only required tools."


def run() -> None:
    agent = Agent(
        name="Tool Agent",
        model=openrouter(),
        tools=[get_hackathon_advice, WebSearchTools()],
        markdown=True,
        instructions=[
            "Use get_hackathon_advice for general architecture advice.",
            "Use web search when the user explicitly asks for current information.",
        ],
    )
    agent.print_response("What should I focus on when building an Agentic AI hackathon project?")

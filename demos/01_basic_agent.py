from agno.agent import Agent

from model import openrouter


def run() -> None:
    agent = Agent(
        name="Basic Agent",
        model=openrouter(),
        markdown=True,
        instructions="Answer clearly and explain your reasoning at a high level without hidden chain-of-thought.",
    )
    agent.print_response("Explain what an AI agent is in three simple points.")

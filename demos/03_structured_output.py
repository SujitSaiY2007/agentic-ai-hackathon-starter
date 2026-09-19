from pydantic import BaseModel, Field
from agno.agent import Agent

from model import gemini


class HackathonPlan(BaseModel):
    problem: str = Field(description="The problem being solved")
    agent_role: str = Field(description="The main role of the AI agent")
    tools: list[str] = Field(description="Tools the agent needs")
    rag_needed: bool = Field(description="Whether RAG is necessary")
    next_step: str = Field(description="The first implementation step")


def run() -> None:
    agent = Agent(
        name="Structured Planner",
        model=gemini(),
        output_schema=HackathonPlan,
        instructions="Design a minimal architecture. Do not add components without a reason.",
    )
    result = agent.run(
        "We need an agent that answers questions about a college event rulebook and can draft an email."
    )
    print(result.content)

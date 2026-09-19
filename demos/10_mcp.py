"""MCP pattern.

Set MCP_SERVER_URL in .env before running this demo.
The endpoint must be a reachable MCP Streamable HTTP server.
"""

import asyncio
import os

from agno.agent import Agent
from agno.tools.mcp import MCPTools

from config import require_openrouter_key
from model import openrouter


def run_async() -> None:
    require_openrouter_key()
    url = os.getenv("MCP_SERVER_URL")
    if not url:
        raise RuntimeError(
            "Set MCP_SERVER_URL in .env before running the MCP demo."
        )

    async def _run() -> None:
        tools = MCPTools(transport="streamable-http", url=url)
        async with tools:
            agent = Agent(
                name="MCP Agent",
                model=openrouter(),
                tools=[tools],
                markdown=True,
            )
            await agent.aprint_response("Describe the tools available through the connected MCP server.")

    asyncio.run(_run())


def run() -> None:
    run_async()

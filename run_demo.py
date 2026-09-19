from __future__ import annotations

import importlib
import sys

ALIASES = {
    "basic": "demos.01_basic_agent",
    "tools": "demos.02_tools",
    "structured": "demos.03_structured_output",
    "rag": "demos.04_rag",
    "memory": "demos.05_memory_and_storage",
    "workflow": "demos.06_workflow",
    "team": "demos.07_team",
    "guardrails": "demos.08_guardrails",
    "hitl": "demos.09_hitl",
    "mcp": "demos.10_mcp",
    "eval": "demos.11_eval",
}


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ALIASES:
        print("Usage: uv run python run_demo.py <demo>")
        print("Available:", ", ".join(ALIASES))
        raise SystemExit(2)

    module = importlib.import_module(ALIASES[sys.argv[1]])
    module.run()


if __name__ == "__main__":
    main()

"""Flattener script: bundles modular agent/ files into a standalone single-file submission.

Usage:
    uv run python flatten_agent.py
Output:
    standalone_submission.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    agent_dir = root / "agent"
    output_file = root / "standalone_submission.py"

    order = [
        "emissions.py",
        "belief.py",
        "predictor.py",
        "stopping.py",
        "scheduler.py",
        "rerouter.py",
        "explanations.py",
        "act_agent.py",
    ]

    header = '''"""Standalone Adaptive Commitment Timing (ACT) Agent for MM26AI02.

Keep the Cluster Alive: Detect, Reroute, Recover.
Auto-generated standalone bundle for submission.
"""

from __future__ import annotations

import math
from typing import Any

try:
    from agent_interface import BaseAgent
except ImportError:
    from abc import ABC, abstractmethod

    class BaseAgent(ABC):
        def __init__(self, n_nodes: int, node_capacity: int):
            self.n_nodes = n_nodes
            self.node_capacity = node_capacity

        @abstractmethod
        def reset(self) -> None:
            raise NotImplementedError

        @abstractmethod
        def act(self, obs: dict) -> dict:
            raise NotImplementedError

        @abstractmethod
        def update(self, obs: dict, reward: float, done: bool, info: dict) -> None:
            raise NotImplementedError

'''

    combined_body = []

    for fname in order:
        fpath = agent_dir / fname
        content = fpath.read_text(encoding="utf-8")

        # Strip headers and internal agent imports
        lines = content.splitlines()
        filtered_lines = []
        for line in lines:
            if line.startswith("from agent.") or line.startswith("import agent."):
                continue
            if line.startswith("from agent_interface import BaseAgent"):
                continue
            if line.startswith("from __future__ import annotations"):
                continue
            if line.startswith("import math") or line.startswith("from typing import Any"):
                continue
            filtered_lines.append(line)

        combined_body.append(f"\n# --- BEGIN {fname} ---\n")
        combined_body.append("\n".join(filtered_lines))
        combined_body.append(f"\n# --- END {fname} ---\n")

    footer = '''
# Canonical alias for evaluation harness
class MyAgent(ACTAgent):
    pass

__all__ = ["MyAgent", "ACTAgent"]
'''

    full_text = header + "".join(combined_body) + footer
    output_file.write_text(full_text, encoding="utf-8")
    print(f"Successfully generated standalone submission: {output_file} ({output_file.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

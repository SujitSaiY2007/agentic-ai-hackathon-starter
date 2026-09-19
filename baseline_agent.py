"""A plain round-robin load balancer with NO health awareness.

It assigns every pending task to the least-loaded node in simple rotation,
and never reroutes anything once assigned -- it has no concept of "this node might be down."

This file is a reference/baseline, demonstrating the failure mode to solve.
"""

from agent_interface import BaseAgent


class RoundRobinNoHealthCheck(BaseAgent):
    def __init__(self, n_nodes: int, node_capacity: int):
        super().__init__(n_nodes, node_capacity)
        self._next_node = 0

    def reset(self) -> None:
        self._next_node = 0

    def act(self, obs: dict) -> dict:
        actions = {}
        for task in obs["tasks"]:
            if task["node"] is None:  # only ever assigns NEW/pending tasks
                actions[task["task_id"]] = self._next_node
                self._next_node = (self._next_node + 1) % self.n_nodes
        return actions

    def update(self, obs: dict, reward: float, done: bool, info: dict) -> None:
        pass  # no learning, no health tracking at all -- that's the point

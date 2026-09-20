"""Bayesian 3-state Hidden Markov Model (HMM) filter for node health perception."""

from __future__ import annotations

from typing import Any
from agent.emissions import EmissionModel


class BayesianHealthFilter:
    """Maintains probabilistic belief b_j = [P(H), P(D), P(X)] for each cluster node.

    Fuses:
    1. Multi-signal raw telemetry (heartbeat, latency, error rate).
    2. Execution sensor: task progress vs stall behavior.
    3. Persistence-biased Markov state transitions.
    """

    def __init__(
        self,
        n_nodes: int,
        transition_matrix: list[list[float]] | None = None,
    ):
        self.n_nodes = n_nodes
        self.emission_model = EmissionModel()

        # Structurally constrained, persistence-biased transition matrix:
        # Rows: from state s; Cols: to state s'
        # States: 0: HEALTHY, 1: DEGRADED, 2: DOWN
        if transition_matrix is not None:
            self.P = transition_matrix
        else:
            self.P = [
                [0.985, 0.012, 0.003],  # From HEALTHY
                [0.05, 0.85, 0.10],     # From DEGRADED
                [0.02, 0.03, 0.95],     # From DOWN
            ]

        # Belief vectors: b[j] = [P(H), P(D), P(X)]
        self.beliefs: list[list[float]] = [[1.0, 0.0, 0.0] for _ in range(n_nodes)]

        # History tracking for task progress sensor
        self._prev_task_nodes: dict[int, int] = {}
        self._prev_task_durations: dict[int, float] = {}

    def reset(self) -> None:
        """Reset beliefs to initial healthy state."""
        self.beliefs = [[0.985, 0.012, 0.003] for _ in range(self.n_nodes)]
        self._prev_task_nodes.clear()
        self._prev_task_durations.clear()

    def update(
        self,
        nodes_obs: list[dict[str, Any]],
        current_tasks_obs: list[dict[str, Any]],
    ) -> list[list[float]]:
        """Perform a full Bayesian predict-and-update step across all nodes.

        Returns updated beliefs [[P(H), P(D), P(X)], ...].
        """
        # 1. Evaluate task execution progress/stall sensor per node
        node_stalls = [0] * self.n_nodes
        node_progresses = [0] * self.n_nodes

        current_task_map = {t["task_id"]: t for t in current_tasks_obs}

        for task_id, prev_node in self._prev_task_nodes.items():
            if prev_node is not None and 0 <= prev_node < self.n_nodes:
                prev_dur = self._prev_task_durations.get(task_id)
                curr_task = current_task_map.get(task_id)

                if curr_task is not None and prev_dur is not None:
                    # If task remained on the same node
                    if curr_task.get("node") == prev_node:
                        curr_dur = curr_task.get("duration_remaining", curr_task.get("duration", prev_dur))
                        if curr_dur < prev_dur:
                            node_progresses[prev_node] += 1
                        else:
                            node_stalls[prev_node] += 1

        # 2. Update each node's belief
        for j, node_data in enumerate(nodes_obs):
            # Prior step: b_bar = b(t-1) * P
            prev_b = self.beliefs[j]
            prior = [0.0, 0.0, 0.0]
            for s_next in range(3):
                prior[s_next] = sum(prev_b[s_prev] * self.P[s_prev][s_next] for s_prev in range(3))

            # Measurement likelihood from raw telemetry
            l_telemetry = self.emission_model.compute_telemetry_likelihood(
                heartbeat_ok=node_data.get("heartbeat_ok"),
                latency_ms=node_data.get("latency_ms"),
                error_rate=node_data.get("error_rate"),
            )

            # Measurement likelihood from task progress sensor
            l_progress = self.emission_model.compute_progress_likelihood(
                stalled_count=node_stalls[j],
                progressed_count=node_progresses[j],
            )

            # Combined posterior: b(s) propto prior(s) * L_tel(s) * L_prog(s)
            posterior = [0.0, 0.0, 0.0]
            for s in range(3):
                posterior[s] = prior[s] * l_telemetry[s] * l_progress[s]

            total = sum(posterior)
            if total > 0:
                self.beliefs[j] = [p / total for p in posterior]
            else:
                self.beliefs[j] = prior

        # 3. Update task cache for the next step
        self._prev_task_nodes = {
            t["task_id"]: t["node"] for t in current_tasks_obs if t.get("node") is not None
        }
        self._prev_task_durations = {
            t["task_id"]: t.get("duration_remaining", t.get("duration", 0)) for t in current_tasks_obs
        }

        return self.beliefs

    def get_belief(self, node_id: int) -> list[float]:
        """Return [P(H), P(D), P(X)] for a specific node."""
        if 0 <= node_id < self.n_nodes:
            return self.beliefs[node_id]
        return [0.33, 0.33, 0.34]

    def get_expected_progress_rate(self, node_id: int) -> float:
        """Expected work progress units per step on node_id:

        Healthy: 1.0
        Degraded: 0.25 (expected: -0.5 w.p. 0.5)
        Down: 0.0
        """
        b = self.get_belief(node_id)
        return round(b[0] * 1.0 + b[1] * 0.25 + b[2] * 0.0, 4)

    def get_health_state_label(self, node_id: int) -> str:
        """Categorical state based on maximum posterior probability."""
        b = self.get_belief(node_id)
        max_idx = b.index(max(b))
        return {0: "HEALTHY", 1: "DEGRADED", 2: "DOWN"}[max_idx]

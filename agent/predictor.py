"""Predictive engine for task completion probabilities and Q-value calculations."""

from __future__ import annotations

import math
from typing import Any
from agent.belief import BayesianHealthFilter


def sigmoid(x: float) -> float:
    """Standard numerically stable sigmoid."""
    if x >= 15.0:
        return 1.0
    if x <= -15.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


class ValuePredictor:
    """Calculates Q(k, j), the expected value of task k on node j,

    accounting for:
    - Node health belief [P(H), P(D), P(X)]
    - Remaining duration vs deadline slack
    - Cold restart progress reset penalty
    - Queue congestion and capacity constraints
    """

    def __init__(self, filter: BayesianHealthFilter, node_capacity: int):
        self.filter = filter
        self.node_capacity = node_capacity

    def compute_q_value(
        self,
        task: dict[str, Any],
        node_id: int,
        current_step: int,
        current_node_queues: list[int],
        eval_as_reroute: bool = False,
        apply_congestion_tie_break: bool = False,
        is_already_on_node: bool = False,
    ) -> float:
        """Compute expected return Q(k, j) in [-1.0, 1.0].

        If eval_as_reroute is True, the task suffers cold-restart penalty:
        duration resets to original_duration.
        If is_already_on_node is True, the task already holds a slot on node_id.
        """
        # 1. Check capacity constraint (only if adding a new task to node_id)
        if not is_already_on_node and current_node_queues[node_id] >= self.node_capacity:
            return -999.0  # Infeasible due to capacity

        duration = task.get("original_duration", task["duration"]) if eval_as_reroute else task["duration"]
        deadline = task["deadline"]
        time_available = deadline - current_step

        # Hopeless task check: even at 100% health, cannot finish
        if time_available < duration:
            return -1.0  # Inevitable deadline miss

        # Expected progress rate on node_id:
        # Healthy: 1.0, Degraded: 0.40, Down: 0.0
        rate = self.filter.get_expected_progress_rate(node_id)
        belief = self.filter.get_belief(node_id)
        p_down = belief[2]

        # If node is down with high confidence, completion is practically impossible
        if p_down > 0.80 or rate < 0.10:
            return -1.0

        # Expected completion time
        # Small variance parameter based on duration
        expected_steps = duration / max(0.08, rate)
        slack = time_available - expected_steps

        # Probability of meeting deadline under stochastic execution
        scale = max(1.2, math.sqrt(duration))
        p_complete = sigmoid(slack / scale)

        # Expected payoff:
        # +1.0 for completion, -1.0 for deadline miss
        expected_payoff = p_complete * 1.0 + (1.0 - p_complete) * (-1.0)

        # Congestion tie-breaker is ONLY used when comparing nodes for initial pending placement
        if apply_congestion_tie_break:
            q_len = current_node_queues[node_id]
            congestion_penalty = 0.01 * (q_len / max(1, self.node_capacity))
            return round(expected_payoff - congestion_penalty, 4)

        return round(expected_payoff, 4)

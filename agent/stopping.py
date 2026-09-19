"""Optimal stopping and continuation valuation for pending and running tasks."""

from __future__ import annotations

from typing import Any
from agent.predictor import ValuePredictor

# Real environment cost for holding a pending task unassigned per step
C_HOLD = 0.01


class OptimalStoppingEngine:
    """Implements finite-horizon optimal stopping decisions:

    1. Pending tasks: COMMIT vs HOLD
       C_k(t) = max_j Q_kj(t)
       H_k(t) = -0.01 + E[V_k(t+1)]
       A_k(t) = C_k(t) - H_k(t)
       Decision: COMMIT if A_k > 0, else HOLD.

    2. Running tasks: STAY vs REROUTE
       Q_stay(t) = Q(k, c_k, current_duration)
       Q_reroute(t) = max_{j != c_k} Q(k, j, original_duration)
       Decision: REROUTE if Q_reroute > Q_stay, else STAY (no arbitrary epsilon).
    """

    def __init__(self, predictor: ValuePredictor, n_nodes: int):
        self.predictor = predictor
        self.n_nodes = n_nodes

    def evaluate_pending_task(
        self,
        task: dict[str, Any],
        current_step: int,
        current_node_queues: list[int],
    ) -> tuple[float, int | None, float, float, float]:
        """Evaluate optimal stopping for a pending task.

        Returns:
            (stopping_advantage A_k, best_node, best_q, continuation_value H_k, delta_scarcity)
        """
        q_values: list[tuple[int, float]] = []

        for j in range(self.n_nodes):
            q_val = self.predictor.compute_q_value(
                task=task,
                node_id=j,
                current_step=current_step,
                current_node_queues=current_node_queues,
                eval_as_reroute=False,
                apply_congestion_tie_break=True,
            )
            q_values.append((j, q_val))

        # Sort candidate nodes by Q-value descending
        q_values.sort(key=lambda x: x[1], reverse=True)

        best_node, c_k = q_values[0]
        second_node, second_q = q_values[1] if len(q_values) > 1 else (None, -1.0)

        # Alternative scarcity: gap between 1st and 2nd best node
        # High delta means few alternatives (opportunity cost is high)
        delta_k = max(0.0, c_k - max(-1.0, second_q))

        # Continuation value H_k(t): holding for 1 step costs -0.01
        # at step t+1, available time is reduced by 1
        q_next_values = [
            self.predictor.compute_q_value(
                task=task,
                node_id=j,
                current_step=current_step + 1,
                current_node_queues=current_node_queues,
                eval_as_reroute=False,
                apply_congestion_tie_break=True,
            )
            for j in range(self.n_nodes)
        ]
        best_q_next = max(q_next_values) if q_next_values else -1.0
        h_k = -C_HOLD + best_q_next

        # Stopping advantage: A_k = C_k - H_k
        # If A_k > 0, committing now is better than holding
        a_k = c_k - h_k

        return a_k, best_node, c_k, h_k, delta_k

    def evaluate_running_task(
        self,
        task: dict[str, Any],
        current_node: int,
        current_step: int,
        current_node_queues: list[int],
    ) -> tuple[bool, int | None, float, float]:
        """Evaluate STAY vs REROUTE for a running task.

        Returns:
            (should_reroute, best_target_node, q_stay, q_reroute)
        """
        # 1. Expected value of staying on current node (task already holds its slot!)
        q_stay = self.predictor.compute_q_value(
            task=task,
            node_id=current_node,
            current_step=current_step,
            current_node_queues=current_node_queues,
            eval_as_reroute=False,
            apply_congestion_tie_break=False,
            is_already_on_node=True,
        )

        # 2. Expected value of rerouting to an alternative node (resets to original_duration)
        best_target = None
        best_q_reroute = -999.0

        for j in range(self.n_nodes):
            if j == current_node:
                continue

            q_candidate = self.predictor.compute_q_value(
                task=task,
                node_id=j,
                current_step=current_step,
                current_node_queues=current_node_queues,
                eval_as_reroute=True,  # Cold restart penalty applied here
                apply_congestion_tie_break=False,
                is_already_on_node=False,
            )

            if q_candidate > best_q_reroute:
                best_q_reroute = q_candidate
                best_target = j

        # Reroute decision: purely economic comparison
        # Q_reroute > Q_stay (no arbitrary epsilon)
        should_reroute = (best_target is not None) and (best_q_reroute > q_stay) and (best_q_reroute > -1.0)

        return should_reroute, best_target, q_stay, best_q_reroute

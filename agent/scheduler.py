"""Capacity-aware cluster scheduler using Stopping Advantage and Alternative Scarcity."""

from __future__ import annotations

from typing import Any
from agent.stopping import OptimalStoppingEngine


class ClusterScheduler:
    """Schedules pending tasks by resolving capacity contention using:

    1. Stopping Advantage: A_k = C_k - H_k
    2. Alternative Scarcity: Delta_k = Q_j1 - Q_j2
    3. Priority_k = A_k * (1.0 + Delta_k)
    4. HOLD option competing directly: max(Q_0, ..., Q_N, H_k)
    """

    def __init__(self, stopping_engine: OptimalStoppingEngine, n_nodes: int, node_capacity: int):
        self.stopping_engine = stopping_engine
        self.n_nodes = n_nodes
        self.node_capacity = node_capacity

    def schedule_pending_tasks(
        self,
        pending_tasks: list[dict[str, Any]],
        current_step: int,
        current_node_queues: list[int],
    ) -> tuple[dict[int, int], list[dict[str, Any]]]:
        """Schedule pending tasks into available node capacity.

        Returns:
            (commit_actions: {task_id: target_node}, explanations: list[dict])
        """
        commit_actions: dict[int, int] = {}
        explanations: list[dict[str, Any]] = []

        candidates = []

        # 1. Evaluate each pending task
        for task in pending_tasks:
            task_id = task["task_id"]
            a_k, best_node, c_k, h_k, delta_k = self.stopping_engine.evaluate_pending_task(
                task=task,
                current_step=current_step,
                current_node_queues=current_node_queues,
            )

            if a_k > 0 and best_node is not None and c_k > -1.0:
                # Opportunity cost weighting: emphasize tasks with few alternatives
                priority = a_k * (1.0 + delta_k)
                candidates.append({
                    "task": task,
                    "task_id": task_id,
                    "priority": priority,
                    "a_k": a_k,
                    "best_node": best_node,
                    "c_k": c_k,
                    "h_k": h_k,
                    "delta_k": delta_k,
                })
            else:
                # Decision: HOLD
                explanations.append({
                    "task_id": task_id,
                    "action": "HOLD",
                    "c_k": c_k,
                    "h_k": h_k,
                    "a_k": a_k,
                    "reason": f"A_k ({a_k:.3f}) <= 0: Holding unassigned is better than committing",
                })

        # 2. Sort candidates by Priority descending
        candidates.sort(key=lambda c: c["priority"], reverse=True)

        # 3. Allocate capacity greedily
        for cand in candidates:
            task = cand["task"]
            task_id = cand["task_id"]
            best_node = cand["best_node"]

            # Try best node first
            if current_node_queues[best_node] < self.node_capacity:
                commit_actions[task_id] = best_node
                current_node_queues[best_node] += 1
                explanations.append({
                    "task_id": task_id,
                    "action": "COMMIT",
                    "node": best_node,
                    "priority": cand["priority"],
                    "a_k": cand["a_k"],
                    "c_k": cand["c_k"],
                    "h_k": cand["h_k"],
                    "reason": f"Committed to best node {best_node} (Priority {cand['priority']:.3f}, A_k {cand['a_k']:.3f})",
                })
            else:
                # Best node is full: re-evaluate feasible alternative nodes
                assigned = False
                for alt_node in range(self.n_nodes):
                    if alt_node == best_node:
                        continue
                    if current_node_queues[alt_node] < self.node_capacity:
                        alt_q = self.stopping_engine.predictor.compute_q_value(
                            task=task,
                            node_id=alt_node,
                            current_step=current_step,
                            current_node_queues=current_node_queues,
                        )
                        # Check if alternative node still beats holding
                        if alt_q > cand["h_k"] and alt_q > -1.0:
                            commit_actions[task_id] = alt_node
                            current_node_queues[alt_node] += 1
                            assigned = True
                            explanations.append({
                                "task_id": task_id,
                                "action": "COMMIT_FALLBACK",
                                "node": alt_node,
                                "a_k": alt_q - cand["h_k"],
                                "reason": f"Committed to fallback node {alt_node} as best node {best_node} was full",
                            })
                            break

                if not assigned:
                    explanations.append({
                        "task_id": task_id,
                        "action": "HOLD_CONGESTED",
                        "best_node": best_node,
                        "reason": f"All viable nodes saturated; holding for next tick",
                    })

        return commit_actions, explanations

"""Rerouting manager for running tasks with economic churn suppression."""

from __future__ import annotations

from typing import Any
from agent.stopping import OptimalStoppingEngine


class ReroutingManager:
    """Manages STAY vs REROUTE decisions for currently running tasks.

    Uses economic comparison: Q_reroute > Q_stay.
    Cold-restart progress loss provides the natural hysteresis barrier.
    """

    def __init__(self, stopping_engine: OptimalStoppingEngine, node_capacity: int):
        self.stopping_engine = stopping_engine
        self.node_capacity = node_capacity

    def plan_reroutes(
        self,
        running_tasks: list[dict[str, Any]],
        current_step: int,
        current_node_queues: list[int],
    ) -> tuple[dict[int, int], list[dict[str, Any]]]:
        """Evaluate running tasks and generate reroute actions.

        Returns:
            (reroute_actions: {task_id: target_node}, explanations: list[dict])
        """
        reroute_actions: dict[int, int] = {}
        explanations: list[dict[str, Any]] = []

        # Sort running tasks by urgency (tightest slack first)
        sorted_tasks = sorted(
            running_tasks,
            key=lambda t: t["deadline"] - current_step - t["duration"]
        )

        for task in sorted_tasks:
            task_id = task["task_id"]
            curr_node = task["node"]
            if curr_node is None:
                continue

            should_reroute, best_target, q_stay, q_reroute = (
                self.stopping_engine.evaluate_running_task(
                    task=task,
                    current_node=curr_node,
                    current_step=current_step,
                    current_node_queues=current_node_queues,
                )
            )

            if should_reroute and best_target is not None:
                # Check if target node has available capacity
                if current_node_queues[best_target] < self.node_capacity:
                    reroute_actions[task_id] = best_target
                    current_node_queues[curr_node] -= 1
                    current_node_queues[best_target] += 1

                    explanations.append({
                        "task_id": task_id,
                        "action": "REROUTE",
                        "from_node": curr_node,
                        "to_node": best_target,
                        "q_stay": q_stay,
                        "q_reroute": q_reroute,
                        "lost_progress": task.get("original_duration", task["duration"]) - task["duration"],
                        "reason": f"Q_reroute ({q_reroute:.3f}) > Q_stay ({q_stay:.3f}) on node {curr_node}",
                    })
                else:
                    explanations.append({
                        "task_id": task_id,
                        "action": "STAY_BLOCKED",
                        "from_node": curr_node,
                        "target_node": best_target,
                        "reason": f"Target node {best_target} at full capacity",
                    })
            else:
                explanations.append({
                    "task_id": task_id,
                    "action": "STAY",
                    "node": curr_node,
                    "q_stay": q_stay,
                    "q_reroute": q_reroute,
                    "reason": f"Q_stay ({q_stay:.3f}) >= Q_reroute ({q_reroute:.3f})",
                })

        return reroute_actions, explanations

"""Simulated cluster environment for MM26AI02: Keep the Cluster Alive.

Simulates a cluster of worker nodes processing a continuous stream of tasks with deadlines.
Nodes independently experience unannounced degradation or failure governed by a Markov process.
"""

from __future__ import annotations

from typing import Any
import numpy as np


class ClusterEnv:
    def __init__(
        self,
        n_nodes: int = 6,
        node_capacity: int = 4,
        arrival_rate: float = 2.0,
        duration_range: tuple[int, int] = (3, 8),
        slack_range: tuple[int, int] = (4, 10),
        episode_length: int = 400,
        seed: int | None = None,
        expose_health: bool = False,
    ):
        self.n_nodes = n_nodes
        self.node_capacity = node_capacity
        self.arrival_rate = arrival_rate
        self.duration_range = duration_range
        self.slack_range = slack_range
        self.episode_length = episode_length
        self.seed = seed
        self.expose_health = expose_health

        self._rng = np.random.default_rng(seed)
        self.current_step = 0
        self._next_task_id = 1

        # Node states: 0: HEALTHY, 1: DEGRADED, 2: DOWN
        self._node_states: list[int] = [0] * self.n_nodes
        self._tasks: dict[int, dict[str, Any]] = {}

        # Episode statistics
        self.completed_count = 0
        self.failed_count = 0
        self.total_tasks_created = 0
        self.churn_count = 0

    def reset(self) -> dict[str, Any]:
        """Reset the environment to the beginning of an episode."""
        if self.seed is not None:
            self._rng = np.random.default_rng(self.seed)
        self.current_step = 0
        self._next_task_id = 1
        self._node_states = [0] * self.n_nodes
        self._tasks.clear()

        self.completed_count = 0
        self.failed_count = 0
        self.total_tasks_created = 0
        self.churn_count = 0

        # Generate initial arrivals
        self._spawn_tasks()
        return self._get_obs()

    def _spawn_tasks(self) -> None:
        """Spawn new arriving tasks based on Poisson arrival."""
        num_new = int(self._rng.poisson(self.arrival_rate))
        if num_new == 0 and self._rng.random() < 0.2:
            num_new = 1

        for _ in range(num_new):
            duration = int(self._rng.integers(self.duration_range[0], self.duration_range[1] + 1))
            slack = int(self._rng.integers(self.slack_range[0], self.slack_range[1] + 1))
            deadline = self.current_step + duration + slack
            task_id = self._next_task_id
            self._next_task_id += 1

            self._tasks[task_id] = {
                "task_id": task_id,
                "node": None,
                "duration_remaining": float(duration),
                "original_duration": float(duration),
                "deadline": deadline,
                "is_new": True,
            }
            self.total_tasks_created += 1

    def _update_node_states(self) -> list[int]:
        """Evolve hidden node states as a Markov chain."""
        failed_this_step = []
        for i in range(self.n_nodes):
            current_state = self._node_states[i]
            r = self._rng.random()

            if current_state == 0:  # HEALTHY
                # Transition: [.985, .012, .003]
                if r < 0.012:
                    self._node_states[i] = 1  # DEGRADED
                    failed_this_step.append(i)
                elif r < 0.015:  # 0.012 + 0.003
                    self._node_states[i] = 2  # DOWN
                    failed_this_step.append(i)
            elif current_state == 1:  # DEGRADED
                # Degraded recovery and failure
                if r < 0.05:
                    self._node_states[i] = 0  # Recovered to HEALTHY
                elif r < 0.15:
                    self._node_states[i] = 2  # Failed to DOWN
                    failed_this_step.append(i)
            elif current_state == 2:  # DOWN
                # Down recovery: 0.02 to Healthy, 0.03 to Degraded
                if r < 0.02:
                    self._node_states[i] = 0  # Recovered to HEALTHY
                elif r < 0.05:  # 0.02 + 0.03
                    self._node_states[i] = 1  # Recovered to DEGRADED

        return failed_this_step

    def _get_obs(self) -> dict[str, Any]:
        """Generate noisy telemetry and active task list."""
        node_queues = [0] * self.n_nodes
        for t in self._tasks.values():
            if t["node"] is not None and 0 <= t["node"] < self.n_nodes:
                node_queues[t["node"]] += 1

        nodes_telemetry = []
        for i in range(self.n_nodes):
            state = self._node_states[i]
            # Noisy telemetry based on true state
            if state == 0:  # HEALTHY
                hb = bool(self._rng.random() < 0.98)
                lat = float(max(5.0, self._rng.normal(12.0, 3.0)))
                err = float(max(0.0, min(1.0, self._rng.uniform(0.0, 0.02))))
            elif state == 1:  # DEGRADED
                hb = bool(self._rng.random() < 0.75)
                lat = float(max(50.0, self._rng.normal(180.0, 35.0)))
                err = float(max(0.0, min(1.0, self._rng.uniform(0.25, 0.55))))
            else:  # DOWN
                hb = bool(self._rng.random() < 0.05)
                lat = float(max(300.0, self._rng.normal(650.0, 80.0)))
                err = float(max(0.0, min(1.0, self._rng.uniform(0.85, 1.0))))

            nodes_telemetry.append({
                "node_id": i,
                "heartbeat_ok": hb,
                "latency_ms": round(lat, 2),
                "error_rate": round(err, 3),
                "queue_len": node_queues[i],
                "capacity": self.node_capacity,
            })

        tasks_obs = [
            {
                "task_id": t["task_id"],
                "node": t["node"],
                "duration_remaining": t["duration_remaining"],
                "deadline": t["deadline"],
                "is_new": t.get("is_new", False),
            }
            for t in self._tasks.values()
        ]

        return {"nodes": nodes_telemetry, "tasks": tasks_obs}

    def step(self, actions: dict[int, int]) -> tuple[dict[str, Any], float, bool, dict[str, Any]]:
        """Apply actions, evolve environment, and return (obs, reward, done, info)."""
        self.current_step += 1

        # Track node queues before applying actions
        current_node_queues = [0] * self.n_nodes
        for t in self._tasks.values():
            if t["node"] is not None:
                current_node_queues[t["node"]] += 1

        # 1. Apply actions with capacity and cold-restart constraints
        for task_id, target_node in actions.items():
            if task_id not in self._tasks:
                continue
            if not (0 <= target_node < self.n_nodes):
                continue

            task = self._tasks[task_id]
            current_node = task["node"]

            # Same node assignment is a no-op
            if current_node == target_node:
                continue

            # Check capacity on target node
            if current_node_queues[target_node] >= self.node_capacity:
                # Silently reject over-capacity assignment
                continue

            # If reassigning from another node -> COLD RESTART
            if current_node is not None:
                task["duration_remaining"] = task["original_duration"]
                current_node_queues[current_node] -= 1
                self.churn_count += 1

            task["node"] = target_node
            current_node_queues[target_node] += 1

        # 2. Evolve hidden states
        failed_this_step = self._update_node_states()

        # 3. Process tasks on nodes & calculate rewards
        completed_ids = []
        expired_ids = []
        reward = 0.0

        for task_id, task in list(self._tasks.items()):
            node_id = task["node"]

            # Unassigned tasks incur holding cost of -0.01 per step
            if node_id is None:
                reward -= 0.01
            elif 0 <= node_id < self.n_nodes:
                state = self._node_states[node_id]
                # Progress depends on node state:
                # HEALTHY: -1.0 deterministic
                # DEGRADED: -0.5 with probability 0.5 (expected -0.25/step)
                # DOWN: 0.0 progress
                if state == 0:  # HEALTHY
                    task["duration_remaining"] -= 1.0
                elif state == 1:  # DEGRADED
                    if self._rng.random() < 0.5:
                        task["duration_remaining"] -= 0.5

            # After first step, task is no longer new
            task["is_new"] = False

            # Check completion
            if task["duration_remaining"] <= 0.0:
                completed_ids.append(task_id)
                self.completed_count += 1
                reward += 1.0
            # Check deadline expiry
            elif self.current_step >= task["deadline"]:
                expired_ids.append(task_id)
                self.failed_count += 1
                reward -= 1.0  # Real deadline-miss penalty is -1.0

        # Remove finished tasks
        for task_id in completed_ids + expired_ids:
            self._tasks.pop(task_id, None)

        # 4. Spawn new arriving tasks
        if self.current_step < self.episode_length:
            self._spawn_tasks()

        done = self.current_step >= self.episode_length
        obs = self._get_obs()

        state_names = {0: "HEALTHY", 1: "DEGRADED", 2: "DOWN"}
        info = {
            "failed_this_step": failed_this_step,
            "completed_this_step": len(completed_ids),
            "expired_this_step": len(expired_ids),
        }
        if self.expose_health:
            info["node_true_states"] = {i: state_names[s] for i, s in enumerate(self._node_states)}

        return obs, reward, done, info

    def get_episode_log(self) -> dict[str, Any]:
        """Return cumulative statistics for the current episode."""
        return {
            "completed_count": self.completed_count,
            "failed_count": self.failed_count,
            "total_tasks": self.total_tasks_created,
            "churn_count": self.churn_count,
            "completion_rate": (
                round(self.completed_count / max(1, self.completed_count + self.failed_count), 3)
            ),
        }

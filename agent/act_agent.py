"""Integrated Adaptive Commitment Timing (ACT) Agent for MM26AI02."""

from __future__ import annotations

from typing import Any
from agent_interface import BaseAgent
from agent.belief import BayesianHealthFilter
from agent.predictor import ValuePredictor
from agent.stopping import OptimalStoppingEngine
from agent.scheduler import ClusterScheduler
from agent.rerouter import ReroutingManager
from agent.explanations import ExplanationEngine


class ACTAgent(BaseAgent):
    """Adaptive Commitment Timing (ACT) Cluster Scheduling Agent.

    Decomposes the cluster management problem into:
    1. Bayesian 3-state HMM health filter fusing telemetry and execution progress stalls.
    2. Predictive engine for completion probabilities and Q(k, j) values.
    3. Optimal stopping with dual continuation semantics:
       - Pending tasks: COMMIT vs HOLD (-0.01 holding penalty per step).
       - Running tasks: STAY vs REROUTE (progress loss provides natural hysteresis).
    4. Capacity contention resolution via Stopping Advantage (A_k) and Alternative Scarcity (Delta_k).
    5. Diagnostic explanations for full transparency and interpretability.
    """

    def __init__(self, n_nodes: int, node_capacity: int):
        super().__init__(n_nodes, node_capacity)
        self.current_step = 0

        # Subsystems
        self.filter = BayesianHealthFilter(n_nodes)
        self.predictor = ValuePredictor(self.filter, node_capacity)
        self.stopping_engine = OptimalStoppingEngine(self.predictor, n_nodes)
        self.scheduler = ClusterScheduler(self.stopping_engine, n_nodes, node_capacity)
        self.rerouter = ReroutingManager(self.stopping_engine, node_capacity)
        self.explanations = ExplanationEngine()

        # Task metadata tracking
        self.task_original_durations: dict[int, int] = {}
        self.task_first_seen_step: dict[int, int] = {}
        self.prev_node_states: list[str] = ["HEALTHY"] * n_nodes

    def reset(self) -> None:
        """Reset per-episode state."""
        self.current_step = 0
        self.filter.reset()
        self.explanations.reset()
        self.task_original_durations.clear()
        self.task_first_seen_step.clear()
        self.prev_node_states = ["HEALTHY"] * self.n_nodes

    def act(self, obs: dict[str, Any]) -> dict[int, int]:
        """Generate cluster actions: {task_id: target_node_id}."""
        nodes_obs = obs.get("nodes", [])
        tasks_obs = obs.get("tasks", [])

        # 1. Maintain task original durations for accurate cold-restart penalty calculation
        for t in tasks_obs:
            tid = t["task_id"]
            if tid not in self.task_original_durations:
                self.task_original_durations[tid] = t["duration"]
                self.task_first_seen_step[tid] = self.current_step
            t["original_duration"] = self.task_original_durations[tid]

        # 2. Update Bayesian belief filter with telemetry and execution progress
        self.filter.update(nodes_obs, tasks_obs)

        # 3. Log state transitions for interpretability
        for j, node_data in enumerate(nodes_obs):
            curr_state = self.filter.get_health_state_label(j)
            prev_state = self.prev_node_states[j]
            if curr_state != prev_state:
                self.explanations.record_transition(
                    step=self.current_step,
                    node_id=j,
                    prev_state=prev_state,
                    new_state=curr_state,
                    belief=self.filter.get_belief(j),
                    telemetry=node_data,
                )
                self.prev_node_states[j] = curr_state

        # 4. Partition tasks into running and pending
        running_tasks = [t for t in tasks_obs if t.get("node") is not None]
        pending_tasks = [t for t in tasks_obs if t.get("node") is None]

        # 5. Compute current node queues
        current_node_queues = [0] * self.n_nodes
        for t in running_tasks:
            node_id = t["node"]
            if 0 <= node_id < self.n_nodes:
                current_node_queues[node_id] += 1

        # 6. Evaluate running tasks: STAY vs REROUTE
        reroute_actions, reroute_expl = self.rerouter.plan_reroutes(
            running_tasks=running_tasks,
            current_step=self.current_step,
            current_node_queues=current_node_queues,
        )

        for expl in reroute_expl:
            self.explanations.record_decision(
                step=self.current_step,
                decision_type=expl.get("action", "REROUTE"),
                task_id=expl["task_id"],
                details=expl,
            )

        # 7. Evaluate pending tasks: COMMIT vs HOLD (capacity contention resolution)
        commit_actions, sched_expl = self.scheduler.schedule_pending_tasks(
            pending_tasks=pending_tasks,
            current_step=self.current_step,
            current_node_queues=current_node_queues,
        )

        for expl in sched_expl:
            self.explanations.record_decision(
                step=self.current_step,
                decision_type=expl.get("action", "COMMIT"),
                task_id=expl["task_id"],
                details=expl,
            )

        # 8. Merge and return actions
        actions = {**reroute_actions, **commit_actions}
        return actions

    def update(self, obs: dict[str, Any], reward: float, done: bool, info: dict[str, Any]) -> None:
        """Receive post-step environment feedback."""
        self.current_step += 1

    @property
    def health_scores(self) -> list[float]:
        """Expected health scores for UI/monitoring: P(H) + 0.5 * P(D)."""
        return [
            round(b[0] * 1.0 + b[1] * 0.50, 4)
            for b in self.filter.beliefs
        ]

    @property
    def node_states(self) -> list[str]:
        """Current categorical health states for UI/monitoring."""
        return [
            self.filter.get_health_state_label(i)
            for i in range(self.n_nodes)
        ]

    def get_diagnostic_logs(self) -> list[dict[str, Any]]:
        """Expose diagnostic logs for UI dashboard or evaluation inspection."""
        return self.explanations.get_recent_logs(100)

    def get_diagnostic_report(self) -> list[dict[str, Any]]:
        """Alias for get_diagnostic_logs for backwards compatibility with app.py."""
        return self.get_diagnostic_logs()

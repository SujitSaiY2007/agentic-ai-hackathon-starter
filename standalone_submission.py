"""Standalone Adaptive Commitment Timing (ACT) Agent for MM26AI02.

Keep the Cluster Alive: Detect, Reroute, Recover.
Auto-generated standalone bundle for submission.
"""

from __future__ import annotations

import math
from typing import Any
from agent_interface import BaseAgent


# --- BEGIN emissions.py ---
"""Emission probability and likelihood calculations for cluster telemetry and execution sensors."""



# Numerical floor for likelihoods to prevent zero-probability collapse
EPSILON = 1e-6


def gaussian_pdf(x: float, mean: float, std: float) -> float:
    """Compute Gaussian probability density with floor protection."""
    if std <= 0:
        return 1.0 if abs(x - mean) < 1e-3 else EPSILON
    var = std * std
    denom = math.sqrt(2.0 * math.pi * var)
    diff = x - mean
    exponent = math.exp(-(diff * diff) / (2.0 * var))
    return max(EPSILON, exponent / denom)


class EmissionModel:
    """Computes likelihood P(Y_j | S_j) for hidden states:

    0: HEALTHY (H)
    1: DEGRADED (D)
    2: DOWN (X)
    """

    def __init__(self):
        # Heartbeat emission probabilities P(hb=1 | state)
        self.p_hb = {
            0: 0.98,  # H
            1: 0.75,  # D
            2: 0.05,  # X
        }

        # Latency parameters (mean, std)
        self.lat_params = {
            0: (12.0, 3.0),   # H
            1: (180.0, 35.0), # D
            2: (650.0, 80.0), # X
        }

        # Error rate parameters (mean, std) - smooth Gaussian to avoid boundary zero-collapse
        self.err_params = {
            0: (0.01, 0.04),  # H
            1: (0.40, 0.12),  # D
            2: (0.92, 0.10),  # X
        }

    def compute_telemetry_likelihood(
        self,
        heartbeat_ok: bool | None,
        latency_ms: float | None,
        error_rate: float | None,
    ) -> list[float]:
        """Compute [P(Y | H), P(Y | D), P(Y | X)] for raw node telemetry."""
        likelihoods = [1.0, 1.0, 1.0]

        # 1. Heartbeat likelihood
        if heartbeat_ok is not None:
            for s in (0, 1, 2):
                p1 = self.p_hb[s]
                likelihoods[s] *= p1 if heartbeat_ok else (1.0 - p1)

        # 2. Latency likelihood
        if latency_ms is None:
            # Special DOWN handling: latency is None is a near-perfect signal of DOWN,
            # but maintain a small non-zero probability for H/D to avoid brittle 100% collapse.
            likelihoods[0] *= 0.0005
            likelihoods[1] *= 0.01
            likelihoods[2] *= 0.98
        else:
            for s in (0, 1, 2):
                mean, std = self.lat_params[s]
                likelihoods[s] *= gaussian_pdf(latency_ms, mean, std)

        # 3. Error rate likelihood
        if error_rate is not None:
            for s in (0, 1, 2):
                mean, std = self.err_params[s]
                likelihoods[s] *= gaussian_pdf(error_rate, mean, std)

        return likelihoods

    def compute_progress_likelihood(
        self,
        stalled_count: int,
        progressed_count: int,
    ) -> list[float]:
        """Compute [P(progress | H), P(progress | D), P(progress | X)] based on observed task execution.

        - HEALTHY: deterministic progress (progress rate 1.0)
        - DEGRADED: stochastic partial progress (~0.40 rate)
        - DOWN: zero progress (stalls 100%)
        """
        if stalled_count == 0 and progressed_count == 0:
            return [1.0, 1.0, 1.0]

        # Per-task progress likelihoods
        # P(progress | state)
        p_prog = {
            0: 0.999,  # H
            1: 0.40,   # D
            2: 0.001,  # X
        }

        # P(stall | state)
        p_stall = {
            0: 0.001,  # H
            1: 0.60,   # D
            2: 0.999,  # X
        }

        likelihoods = [1.0, 1.0, 1.0]
        for s in (0, 1, 2):
            prog_l = (p_prog[s] ** progressed_count) if progressed_count > 0 else 1.0
            stall_l = (p_stall[s] ** stalled_count) if stalled_count > 0 else 1.0
            likelihoods[s] *= max(EPSILON, prog_l * stall_l)

        return likelihoods
# --- END emissions.py ---

# --- BEGIN belief.py ---
"""Bayesian 3-state Hidden Markov Model (HMM) filter for node health perception."""




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
                [0.97, 0.02, 0.01],  # From HEALTHY
                [0.08, 0.82, 0.10],  # From DEGRADED
                [0.07, 0.05, 0.88],  # From DOWN
            ]

        # Belief vectors: b[j] = [P(H), P(D), P(X)]
        self.beliefs: list[list[float]] = [[1.0, 0.0, 0.0] for _ in range(n_nodes)]

        # History tracking for task progress sensor
        self._prev_task_nodes: dict[int, int] = {}
        self._prev_task_durations: dict[int, int] = {}

    def reset(self) -> None:
        """Reset beliefs to initial healthy state."""
        self.beliefs = [[0.98, 0.015, 0.005] for _ in range(self.n_nodes)]
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
                        curr_dur = curr_task.get("duration", prev_dur)
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
            t["task_id"]: t["duration"] for t in current_tasks_obs
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
        Degraded: 0.40
        Down: 0.0
        """
        b = self.get_belief(node_id)
        return round(b[0] * 1.0 + b[1] * 0.40 + b[2] * 0.0, 4)

    def get_health_state_label(self, node_id: int) -> str:
        """Categorical state based on maximum posterior probability."""
        b = self.get_belief(node_id)
        max_idx = b.index(max(b))
        return {0: "HEALTHY", 1: "DEGRADED", 2: "DOWN"}[max_idx]
# --- END belief.py ---

# --- BEGIN predictor.py ---
"""Predictive engine for task completion probabilities and Q-value calculations."""




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
# --- END predictor.py ---

# --- BEGIN stopping.py ---
"""Optimal stopping and continuation valuation for pending and running tasks."""



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
# --- END stopping.py ---

# --- BEGIN scheduler.py ---
"""Capacity-aware cluster scheduler using Stopping Advantage and Alternative Scarcity."""




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
# --- END scheduler.py ---

# --- BEGIN rerouter.py ---
"""Rerouting manager for running tasks with economic churn suppression."""




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
# --- END rerouter.py ---

# --- BEGIN explanations.py ---
"""Diagnostic explanation and interpretability engine for cluster scheduling decisions."""




class ExplanationEngine:
    """Collects and formats structured diagnostic events for:

    - Health state transitions with posterior probabilities
    - Optimal stopping decisions (COMMIT vs HOLD)
    - Rerouting decisions (STAY vs REROUTE)
    """

    def __init__(self, max_history: int = 500):
        self.max_history = max_history
        self.diagnostic_logs: list[dict[str, Any]] = []

    def reset(self) -> None:
        """Clear logs at the start of each episode."""
        self.diagnostic_logs.clear()

    def record_transition(
        self,
        step: int,
        node_id: int,
        prev_state: str,
        new_state: str,
        belief: list[float],
        telemetry: dict[str, Any],
    ) -> None:
        """Record a node health state change."""
        log_entry = {
            "type": "NODE_TRANSITION",
            "step": step,
            "node_id": node_id,
            "prev_state": prev_state,
            "new_state": new_state,
            "belief": {
                "P_healthy": round(belief[0], 4),
                "P_degraded": round(belief[1], 4),
                "P_down": round(belief[2], 4),
            },
            "telemetry": {
                "heartbeat": telemetry.get("heartbeat_ok"),
                "latency_ms": telemetry.get("latency_ms"),
                "error_rate": telemetry.get("error_rate"),
                "queue_len": telemetry.get("queue_len"),
            },
            "summary": (
                f"[t={step:03d}] Node {node_id}: {prev_state} -> {new_state} "
                f"(P(X)={belief[2]:.2f}, lat={telemetry.get('latency_ms')}ms, "
                f"err={telemetry.get('error_rate')})"
            ),
        }
        self._add_entry(log_entry)

    def record_decision(
        self,
        step: int,
        decision_type: str,  # "COMMIT", "HOLD", "REROUTE", "STAY"
        task_id: int,
        details: dict[str, Any],
    ) -> None:
        """Record a scheduling or routing decision."""
        log_entry = {
            "type": f"DECISION_{decision_type}",
            "step": step,
            "task_id": task_id,
            "details": details,
        }
        self._add_entry(log_entry)

    def _add_entry(self, entry: dict[str, Any]) -> None:
        self.diagnostic_logs.append(entry)
        if len(self.diagnostic_logs) > self.max_history:
            self.diagnostic_logs.pop(0)

    def get_recent_logs(self, n: int = 50) -> list[dict[str, Any]]:
        """Return the most recent n diagnostic logs."""
        return self.diagnostic_logs[-n:]
# --- END explanations.py ---

# --- BEGIN act_agent.py ---
"""Integrated Adaptive Commitment Timing (ACT) Agent for MM26AI02."""




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
# --- END act_agent.py ---

# Canonical alias for evaluation harness
class MyAgent(ACTAgent):
    pass

__all__ = ["MyAgent", "ACTAgent"]

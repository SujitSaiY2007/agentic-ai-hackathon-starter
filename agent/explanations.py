"""Diagnostic explanation and interpretability engine for cluster scheduling decisions."""

from __future__ import annotations

from typing import Any


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

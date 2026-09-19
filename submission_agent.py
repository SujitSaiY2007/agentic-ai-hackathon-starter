"""Adaptive Commitment Timing (ACT) Agent for MM26AI02.

Problem Statement: Keep the Cluster Alive: Detect, Reroute, Recover.

Architecture:
1. Bayesian 3-State HMM Health Filter (P(H), P(D), P(X)) with execution progress stall sensing.
2. Predictive Horizon Engine for task completion probabilities and Q(k, j).
3. Optimal Stopping Engine:
   - Pending: COMMIT vs HOLD with actual c_hold = 0.01 per-step cost.
   - Running: STAY vs REROUTE with economic cold-restart progress loss barrier.
4. Capacity Contention Resolution via Stopping Advantage (A_k) and Alternative Scarcity (Delta_k).
5. Diagnostic Interpretability Engine.
"""

from __future__ import annotations

from agent.act_agent import ACTAgent


class MyAgent(ACTAgent):
    """Canonical competition entry point aliasing ACTAgent."""
    pass


__all__ = ["MyAgent", "ACTAgent"]

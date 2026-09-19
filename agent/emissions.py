"""Emission probability and likelihood calculations for cluster telemetry and execution sensors."""

from __future__ import annotations

import math
from typing import Any

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

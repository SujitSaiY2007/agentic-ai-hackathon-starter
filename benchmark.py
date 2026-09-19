"""Comprehensive benchmark suite for MM26AI02.

Evaluates MyAgent (Adaptive Tri-Guard) vs RoundRobinNoHealthCheck baseline
across multiple random evaluation seeds and prints full comparison metrics.
"""

from __future__ import annotations

import time
from typing import Any

from baseline_agent import RoundRobinNoHealthCheck
from sandbox_env import make_sandbox_env
from submission_agent import MyAgent


def run_episode(agent, seed: int, debug: bool = False) -> dict[str, Any]:
    env = make_sandbox_env(seed=seed, debug=debug)
    obs = env.reset()
    agent.reset()

    start_time = time.perf_counter()
    unhealthy_traffic_count = 0

    for t in range(env.episode_length):
        actions = agent.act(obs)
        obs, reward, done, info = env.step(actions)
        agent.update(obs, reward, done, info)

        # Track if agent sent traffic to true DOWN nodes
        if debug and "node_true_states" in info:
            for target_node in actions.values():
                if info["node_true_states"].get(target_node) == "DOWN":
                    unhealthy_traffic_count += 1

        if done:
            break

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    log = env.get_episode_log()

    return {
        "seed": seed,
        "completed": log["completed_count"],
        "failed": log["failed_count"],
        "total": log["total_tasks"],
        "completion_rate": log["completion_rate"],
        "churn": log["churn_count"],
        "unhealthy_traffic": unhealthy_traffic_count,
        "elapsed_ms": round(elapsed_ms, 2),
    }


def main() -> None:
    test_seeds = [1, 3, 7, 42, 99]

    print("=" * 80)
    print("MM26AI02 BENCHMARK: Adaptive Tri-Guard vs Round-Robin Baseline")
    print("=" * 80)
    print(f"Running across {len(test_seeds)} seeds: {test_seeds}\n")

    baseline_results = []
    adaptive_results = []

    for s in test_seeds:
        # Run Baseline
        b_agent = RoundRobinNoHealthCheck(n_nodes=6, node_capacity=4)
        b_res = run_episode(b_agent, seed=s, debug=True)
        baseline_results.append(b_res)

        # Run Our Adaptive Agent
        a_agent = MyAgent(n_nodes=6, node_capacity=4)
        a_res = run_episode(a_agent, seed=s, debug=True)
        adaptive_results.append(a_res)

    print("-" * 80)
    print(f"{'Seed':<6} | {'Baseline Completed':<20} | {'Adaptive Completed':<20} | {'Gain':<10}")
    print("-" * 80)

    total_b_comp = sum(r["completed"] for r in baseline_results)
    total_a_comp = sum(r["completed"] for r in adaptive_results)
    total_b_fail = sum(r["failed"] for r in baseline_results)
    total_a_fail = sum(r["failed"] for r in adaptive_results)
    total_b_churn = sum(r["churn"] for r in baseline_results)
    total_a_churn = sum(r["churn"] for r in adaptive_results)
    total_b_bad_traffic = sum(r["unhealthy_traffic"] for r in baseline_results)
    total_a_bad_traffic = sum(r["unhealthy_traffic"] for r in adaptive_results)
    avg_a_time = sum(r["elapsed_ms"] for r in adaptive_results) / len(adaptive_results)

    for b, a in zip(baseline_results, adaptive_results):
        gain = a["completed"] - b["completed"]
        print(
            f"{b['seed']:<6} | "
            f"{b['completed']:>4} / {b['total']} ({b['completion_rate']*100:.1f}%)     | "
            f"{a['completed']:>4} / {a['total']} ({a['completion_rate']*100:.1f}%)     | "
            f"+{gain} tasks"
        )

    print("-" * 80)
    print("\n[+] CUMULATIVE METRICS SUMMARY:")
    print(f"  * Baseline Total Completed: {total_b_comp} (Failed: {total_b_fail})")
    print(f"  * Adaptive Total Completed: {total_a_comp} (Failed: {total_a_fail})")
    print(f"  * Net Task Salvage Gain:   +{total_a_comp - total_b_comp} completed tasks (+{((total_a_comp - total_b_comp)/max(1, total_b_comp))*100:.1f}%)")
    print(f"  * Traffic Sent to Dead Nodes: Baseline={total_b_bad_traffic} vs Adaptive={total_a_bad_traffic} (-{((total_b_bad_traffic - total_a_bad_traffic)/max(1, total_b_bad_traffic))*100:.1f}%)")
    print(f"  * Total Churn (Reroutes):   Baseline={total_b_churn} vs Adaptive={total_a_churn}")
    print(f"  * Average Compute Time:     {avg_a_time:.1f} ms per 400-step episode (~{avg_a_time/400:.3f} ms/step)")
    print("=" * 80)


if __name__ == "__main__":
    main()

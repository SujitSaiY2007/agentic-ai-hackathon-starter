"""Verification test for Interpretability and AI Root Cause Analysis (RCA) reporting."""

from __future__ import annotations

from sandbox_env import make_sandbox_env
from submission_agent import MyAgent
from app import build_sre_rca_report


def main() -> None:
    print("=" * 80)
    print("INTERPRETABILITY & AI ROOT-CAUSE ANALYSIS (RCA) TEST")
    print("=" * 80)

    # 1. Run simulation directly to generate diagnostic logs
    print("[1/3] Running simulation episode with MyAgent (seed=3)...")
    env = make_sandbox_env(seed=3, debug=True)
    agent = MyAgent(n_nodes=env.n_nodes, node_capacity=env.node_capacity)

    obs = env.reset()
    agent.reset()

    for t in range(env.episode_length):
        actions = agent.act(obs)
        obs, reward, done, info = env.step(actions)
        agent.update(obs, reward, done, info)
        if done:
            break

    log = env.get_episode_log()
    diagnostics = agent.get_diagnostic_report()

    print(f"      Episode finished: {log['completed_count']} completed, "
          f"{log['failed_count']} failed, "
          f"{len(diagnostics)} diagnostic events recorded.")

    # 2. Verify structured diagnostic events
    print("[2/3] Inspecting diagnostic event schema & types...")
    event_types = {d.get("type") for d in diagnostics}
    print(f"      Recorded event types: {event_types}")

    transitions = [d for d in diagnostics if d.get("type") == "NODE_TRANSITION"]
    commits = [d for d in diagnostics if "COMMIT" in d.get("details", {}).get("action", "")]
    holds = [d for d in diagnostics if "HOLD" in d.get("details", {}).get("action", "")]
    reroutes = [d for d in diagnostics if "REROUTE" in d.get("details", {}).get("action", "")]

    print(f"      - Transitions: {len(transitions)}")
    print(f"      - Commits: {len(commits)}")
    print(f"      - Holds: {len(holds)}")
    print(f"      - Reroutes: {len(reroutes)}")

    # 3. Generate SRE Root Cause Analysis Report
    print("[3/3] Generating Executive SRE Root Cause Analysis (RCA) Report:")
    print("-" * 80)
    report = build_sre_rca_report(diagnostics)
    print(report)
    print("-" * 80)

    assert len(report) > 100, "Report too short"
    assert "Incident Timeline" in report, "Missing timeline section"
    assert "Adaptive Commitment Timing" in report, "Missing ACT section"
    assert "Reliability & Impact Assessment" in report, "Missing impact section"

    print("\n[SUCCESS] Step 3: Interpretability & AI Root-Cause Analysis verified successfully!")


if __name__ == "__main__":
    main()

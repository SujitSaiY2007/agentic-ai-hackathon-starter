"""SANDBOX environment factory for MM26AI02.

Usage:
    from sandbox_env import make_sandbox_env
    env = make_sandbox_env(seed=0, debug=True)
    obs = env.reset()
    obs, reward, done, info = env.step({101: 2, 104: 0})
"""

from env.cluster_env import ClusterEnv

N_NODES = 6
NODE_CAPACITY = 4
EPISODE_LENGTH = 400


def make_sandbox_env(seed: int = None, debug: bool = False) -> ClusterEnv:
    """
    debug=True exposes info['node_true_states'] and info['failed_this_step']
    so you can plot/verify your detector against ground truth.
    """
    return ClusterEnv(
        n_nodes=N_NODES,
        node_capacity=NODE_CAPACITY,
        arrival_rate=2.0,
        duration_range=(3, 8),
        slack_range=(4, 10),
        episode_length=EPISODE_LENGTH,
        seed=seed,
        expose_health=debug,
    )

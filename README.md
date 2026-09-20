# Problem Statement MM26AI02: Keep the Cluster Alive
## Autonomous Fault-Tolerant Cluster Scheduling Agent
### Solution: Adaptive Commitment Timing (ACT) • Team MM26AI02

---

## 1. Executive Summary & Submission Details
* **Track**: Agentic AI
* **Problem Statement ID**: MM26AI02
* **Title**: *Keep the Cluster Alive: Detect, Reroute, Recover*
* **Submission Class**: `MyAgent(BaseAgent)` located in `submission_agent.py` and `standalone_submission.py`.
* **Zero-Dependency Bundle**: `standalone_submission.py` (35.6 KB, pure Python standard library, execution time ~0.23 ms/step).

---

## 2. Detection Approach: What Signals We Use to Detect Change
Nodes experience unannounced Markov transitions between three hidden states: `HEALTHY (0)`, `DEGRADED (1)`, and `DOWN (2)`. Rather than relying on fragile hardcoded thresholds, `MyAgent` maintains a continuous **Bayesian 3-State Hidden Markov Model (HMM) posterior belief distribution**:

$$\mathbf{b}_j(t) = \begin{bmatrix} P(S_j(t) = \text{HEALTHY}) \\ P(S_j(t) = \text{DEGRADED}) \\ P(S_j(t) = \text{DOWN}) \end{bmatrix} \in \Delta^2$$

We fuse four multi-modal signals at every simulation step:
1. **Heartbeat Likelihood**: Bernoulli likelihood ($0.98$ for $H$, $0.75$ for $D$, $0.05$ for $X$).
2. **Latency Likelihood**: Gaussian density centered on operational baselines; automatically detects `None` or extreme spikes ($> 500\text{ ms}$) as near-certain DOWN events.
3. **Error Rate Likelihood**: Density functions tracking error surges ($H: 0.01$, $D: 0.40$, $X: 0.92$).
4. **Active Task Execution Sensing ($\Delta d$)**: The tasks themselves act as sensors. If an active task makes normal progress ($\Delta d = 1$), the node is confirmed healthy. If an active task makes zero progress ($\Delta d = 0$ stall), the likelihood of the node being DOWN multiplies exponentially in real time, detecting failures before network heartbeats even time out.

---

## 3. Adaptation Approach: How We Adapt Once Change Is Suspected
Once node degradation or failure is suspected, our **Adaptive Commitment Timing (ACT)** engine formulates scheduling as an **approximate finite-horizon optimal-stopping problem**:

### A. Pending / Unassigned Tasks (COMMIT vs. HOLD)
* Evaluates the **Stopping Advantage**: $A_k(t) = C_k(t) - H_k(t)$, where $C_k$ is the maximum expected payoff on available nodes and $H_k = -0.01 + \mathbb{E}[V_k(t+1)]$ is the continuation value of waiting in the buffer.
* **Strategic Hold**: If available nodes are degraded or saturated, the task patiently **holds in the buffer** (paying $-0.01$/step) rather than gambling on a sick node. As deadline slack decays, the advantage turns positive, forcing commitment before it's too late.

### B. Running In-Flight Tasks (STAY vs. REROUTE)
* Rerouting an in-flight task wipes completed progress back to the original duration (Cold Restart: $d \leftarrow d_{\text{orig}}$).
* The lost progress ($d_{\text{orig}} - d$) serves as an **automatic economic barrier against churn**.
* A task is **only rerouted if $Q^{\text{reroute}} > Q^{\text{stay}}$**. Tasks on healthy or mildly degraded nodes stay put to protect work, while tasks trapped on confirmed dead nodes ($Q^{\text{stay}} \to -1.0$) are decisively rescued.

### C. Capacity Contention & Opportunity Cost
* With a strict limit of 4 tasks per node (`node_capacity = 4`), assigning to a full node causes **silent rejection**.
* We resolve contention using **Opportunity Cost** ($\Delta_k = Q_{j_1} - Q_{j_2}$). Tasks with the fewest safe alternative nodes receive capacity priority, eliminating silent rejections.

---

## 4. (Bonus) Interpretability & Diagnostic Audit Logs
Every state transition and routing decision logs its exact mathematical rationale for real-time SRE auditing:
```text
[Step 184] NODE_TRANSITION — Node 1 -> DOWN: P(X)=1.00, P(D)=0.00, P(H)=0.00. Latency=733.0ms, Error=94.9%, Heartbeat=LOST.
[Step 185] TASK_REROUTE    — Task #41 migrated: Node 1 -> Node 2. (Q_reroute 0.888 > Q_stay -1.000, avoiding dead freeze).
[Step 186] TASK_HOLD       — Task #45 HELD in buffer (Slack: 8s, A_k <= 0, holding fee -$0.01 paid to await healthy capacity).
```

---

## 5. Benchmark Performance (2,000 Total Steps Across Seeds 1, 3, 7, 42, 99)
* **Task Completion Rate**: **98.1%** vs. 86.1% baseline (**+13.2% net gain**, +471 tasks salvaged).
* **Missed Deadlines**: **79** vs. 577 baseline (**86.3% reduction**).
* **Dead-Node Traffic**: **102** vs. 644 baseline (**84.2% reduction**).
* **Execution Latency**: **~0.23 ms per step** (well below the 1.0 ms real-time evaluation limit).

---

## 6. How to Run & Verify

### Run Compliance Verification:
```bash
python verify_submission.py
```

### Run 5-Seed Benchmark:
```bash
python benchmark.py
```

### Launch Interactive SRE Observability Dashboard:
```bash
uv run python app.py
# Open http://localhost:7777 in your browser
```

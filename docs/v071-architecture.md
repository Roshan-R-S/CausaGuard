# CausaGuard v0.7.1: System Architecture and Generative Specification

**Status:** Technical Architecture Document, CausaGuard PhD Research Programme
**Date:** 6 November 2026
**Scope:** Architecture Specification for Isolated CausaGuard v0.7.1 Engine
**Referenced Evidence:**

- [src_v07_1/causaguard_v07_1/](../src_v07_1/causaguard_v07_1/)
- [docs/v071-engineering-implementation-report.md](../docs/v071-engineering-implementation-report.md)
- [research/methodology/v07-escalation-remediation-design.md](../research/methodology/v07-escalation-remediation-design.md)
- [research/reviews/v07-methodological-gate-resolution.md](../research/reviews/v07-methodological-gate-resolution.md)

---

## 1. Architectural Overview & Design Principles

CausaGuard v0.7.1 provides an isolated, reproducible benchmark for evaluating sequential causal decision algorithms under uncertainty, operational risk limits, and authentic workflow disruption penalties.

The v0.7.1 architecture is structured around five core pillars:

1. **Generative Causal DAG Environments:** Synthetic enterprise workflow simulators (Customer Support and Data Engineering) with latent state spaces, fallible observational alarms, and asymmetric operational hazards.
2. **Decomposed Human-Intervention Engine:** A realistic multi-attribute escalation model that captures human labor engagement fees, queuing delay distributions, capacity bounds, specialist error rates, and downstream workflow value degradation.
3. **Action-Space Symmetry:** A strict comparator protocol where all practical policies operate under identical public observations, feasible actions, tool operation budgets, and safety constraints.
4. **Counterfactual Paired Evaluation:** Exact potential-outcome evaluation using deterministic exogenous random tapes, guaranteeing that all policies encounter identical latent case draws and background conditions.
5. **Policy-Order Invariance:** Isolated, policy-specific queue states that guarantee the evaluation order of policies does not alter empirical metrics.

```
+--------------------------------------------------------------------------------------------------+
|                                    CausaGuard v0.7.1 ARCHITECTURE                                 |
+--------------------------------------------------------------------------------------------------+
|                                                                                                  |
|   +--------------------------+       +--------------------------+                                |
|   |   Customer Support (CS)  |       |   Data Engineering (DE)  |                                |
|   |   - Clean / Stale / Fraud|       |   - Schema / Content /   |                                |
|   |   - Friction & Churn     |       |     Transient Node Crash |                                |
|   +------------+-------------+       +------------+-------------+                                |
|                |                                  |                                              |
|                v                                  v                                              |
|   +-------------------------------------------------------------+                                |
|   |               Exogenous Random Generation Engine             |                                |
|   |   - Deterministic SeedSequence [Seed, Profile, CaseIndex]   |                                |
|   |   - 12 Exogenous Uniform Draws per Case                     |                                |
|   +------------------------------+------------------------------+                                |
|                                  |                                                               |
|                                  v                                                               |
|   +-------------------------------------------------------------+                                |
|   |          Symmetric 8-Policy Benchmark Comparison Suite       |                                |
|   |   - cost_rule_v07_1 (Analytical Bayesian VOI Candidate)     |                                |
|   |   - always_escalate / always_recovery / budget_aware_rec    |                                |
|   |   - escalation_aware_deterministic_thresh (Calibrated)      |                                |
|   |   - cost_sensitive_symmetric_heuristic (Full Heuristic)     |                                |
|   |   - fixed_verify_repair_macro (Historical Macro)            |                                |
|   |   - oracle (Diagnostic Reference Ground Truth)              |                                |
|   +------------------------------+------------------------------+                                |
|                                  |                                                               |
|                                  v                                                               |
|   +-------------------------------------------------------------+                                |
|   |          Decomposed Multi-Attribute Escalation Engine        |                                |
|   |   - Labor Fees ($0.45 CS, $0.75 DE)                         |                                |
|   |   - Queue Latency ($0.75h CS, $1.20h DE + Queue Scaling)    |                                |
|   |   - Capacity Limit (150/cluster -> Queue Drop Rejection)    |                                |
|   |   - Human Error (5-15% -> Residual Harm Risk)               |                                |
|   |   - Workflow Degradation (0.80*V CS, 0.75*V DE Net Value)   |                                |
|   +------------------------------+------------------------------+                                |
|                                  |                                                               |
|                                  v                                                               |
|   +-------------------------------------------------------------+                                |
|   |             Counterfactual Multi-Policy Runner               |                                |
|   |   - Independent QueueState Clones per Policy                |                                |
|   |   - Strict Policy-Order Invariance                          |                                |
|   |   - Paired Student-t & Clustered Bootstrap Contrast Engine   |                                |
|   +-------------------------------------------------------------+                                |
+--------------------------------------------------------------------------------------------------+
```

---

## 2. Domain Generative Causal Models

### 2.1 Customer Support Record-Resolution Domain ([`domain_cs.py`](../src_v07_1/causaguard_v07_1/domain_cs.py))

Models enterprise customer record resolution where tickets may contain stale customer data or deliberate account takeover fraud:

- **State Space ($\mathcal{S}_{\text{cs}}$):** $S \in \{\text{clean}, \text{stale}, \text{fraud}\}$.
- **Public Covariates ($X_{\text{cs}}$):**
  - `ticket_age_hours` $\in [0, 96]$
  - `queue_load` $\sim \text{Beta}(2, 4)$
  - `conflict_alarm` $\in [0, 1]$ (Observable sensor score: high for fraud/stale, low for clean)
  - `source_reliability` $\in [0.35, 1.0]$
  - `value` $\sim \mathcal{U}(0.80, 1.50)$
  - `harm` $\sim \mathcal{U}(2.00, 6.00)$
  - `budget` $B \in \{1, 2\}$
- **Action Space ($\mathcal{A}_{\text{cs}}$):**
  - `proceed`: Consumes $1$ tool op. Safe on clean; silent failure on stale; causes catastrophic operational harm ($-H$) on fraud.
  - `verify`: Consumes $1$ tool op. Non-terminal consistency check. Generates fallible binary evidence flag with quoted/actual error rates.
  - `retry`: Consumes $1$ tool op. Authoritative database re-query. Cures stale record with probability $\rho_{\text{cs}} = \text{clip}(0.35 + 0.45 \cdot \text{Rel} - 0.20 \cdot \text{Load}, 0.10, 0.95)$. On clean tickets, causes customer friction ($p_{\text{fric}} = 0.15 + 0.35 \cdot \text{Load}$) resulting in ticket abandonment ($25\%$) or satisfaction discount ($10–40\%$). Cannot cure fraud.
  - `escalate`: Consumes $0$ tool ops. Routes ticket to human specialist via [`escalation.py`](../src_v07_1/causaguard_v07_1/escalation.py).

### 2.2 Data Engineering Pipeline Domain ([`domain_de.py`](../src_v07_1/causaguard_v07_1/domain_de.py))

Models automated batch transformation pipelines subject to multi-channel data defects:

- **State Space ($\mathcal{S}_{\text{de}}$):** Multivariate Bernoulli failure indicators $F = (F_s, F_c, F_t)$:
  - $F_s$ (Schema Drift): Structural upstream table modification ($P(F_s) \approx 0.02 + 0.35 \cdot \text{Load}$).
  - $F_c$ (Content Corruption): Malformed rows, encoding errors ($P(F_c) \approx 0.03 + 0.25 \cdot \text{Age} + 0.25 \cdot (1 - \text{Qual})$).
  - $F_t$ (Transient Noise): Hardware node crashes, network partition ($P(F_t) \approx 0.01 + 0.08 \cdot \text{Load}$).
- **Action Space ($\mathcal{A}_{\text{de}}$):**
  - `proceed`: Consumes $1$ tool op. If $F_s$ or $F_c$ present, corrupted data enters production analytics, triggering operational harm ($-H$).
  - `verify`: Consumes $1$ tool op. Non-terminal schema audit and sample row check. Generates `schema_valid` and continuous `sample_pass_rate`.
  - `restore`: Consumes $1$ tool op. Checkpoint snapshot rollback. Recovers degraded fallback output ($v_{\text{fallback}} = 0.45 \times V$). If structural schema drift ($F_s$) is present, persistent incompatibility occurs with probability $80\%$, collapsing value to $0.10 \times V$.
  - `escalate`: Consumes $0$ tool ops. Pages on-call data engineer via [`escalation.py`](../src_v07_1/causaguard_v07_1/escalation.py).

---

## 3. Decomposed Human Escalation Engine ([`escalation.py`](../src_v07_1/causaguard_v07_1/escalation.py))

Human escalation is modeled as a 7-attribute generative state machine:

### 3.1 Mathematical Formulation

1. **Labor Cost:**
   $$C_{\text{labor}} = C_{\text{base}} + \beta_{\text{labor}} \cdot \text{Load}$$
   ($C_{\text{base}} = \$0.45$ CS, $\$0.75$ DE; $\beta_{\text{labor}} = \$0.20$ CS, $\$0.30$ DE).
2. **Queuing Latency:**
   $$L_{\text{queue}} = L_0 + \beta_{\text{queue}} \cdot \text{Load} + \eta_{\text{jitter}}$$
   ($L_0 = 0.75\text{h}$ CS, $1.20\text{h}$ DE; $\beta_{\text{queue}} = 1.20$ CS, $1.50$ DE). If $L > \text{Deadline}$, the task is marked late with zero value.
3. **Capacity Constraints & Queue Drops:**
   Cluster-level capacity is bounded by $\mathcal{K}_{\text{limit}} = 150$. If cumulative escalations exceed $\mathcal{K}_{\text{limit}}$, subsequent requests suffer **queue drop** ($\text{Reason} = \text{"human\_queue\_capacity\_exhausted"}$, $\text{Utility} = -\text{Cost}$).
4. **Specialist Error Rate:**
   $$P(\text{Error}) = P_{\text{error\_base}} + \beta_{\text{error}} \cdot \text{Load}$$
   ($P_{\text{error\_base}} = 0.05$). Under error, human fails to resolve defect. If defect was hazardous, latent harm risk triggers with probability $50–60\%$ ($H_{\text{error}} = \$3.50$ CS, $\$4.00$ DE).
5. **Conditional Salvage:**
   Under successful review, human fixes defect with category-specific probability:
   - CS: Fraud $0.60$, Stale $0.80$, Clean $0.95$
   - DE: Schema $0.75$, Content $0.80$, Transient $0.85$, Clean $1.00$
6. **Workflow Value Discount:**
   Successful human resolution awards discounted completion value:
   $$V_{\text{net}} = \gamma_{\text{workflow}} \cdot V$$
   ($\gamma_{\text{workflow}} = 0.80$ CS, $0.75$ DE).

---

## 4. Symmetric Policy Suite & Decision Architecture ([`policy_v07_1.py`](../src_v07_1/causaguard_v07_1/policy_v07_1.py))

### 4.1 Comparator Matrix

| Policy Name                             | Action Set at Step 1                   | Action Set at Step 2           | Decision Mechanism                                                       | Confirmatory Status       |
| --------------------------------------- | -------------------------------------- | ------------------------------ | ------------------------------------------------------------------------ | ------------------------- |
| `cost_rule_v07_1`                       | `{proceed, verify, recover, escalate}` | `{proceed, recover, escalate}` | Bayesian VOI Optimization                                                | **Candidate**             |
| `always_escalate`                       | `{escalate}`                           | N/A                            | Fixed Policy                                                             | **Primary Baseline**      |
| `always_recovery`                       | `{retry}` (CS) / `{restore}` (DE)      | N/A                            | Fixed Policy                                                             | **Primary Baseline**      |
| `cost_sensitive_symmetric_heuristic`    | `{proceed, verify, recover, escalate}` | `{proceed, recover, escalate}` | Symmetric Cost-Benefit Heuristic                                         | **Primary Baseline**      |
| `budget_aware_direct_recovery`          | `{proceed, recover}`                   | N/A                            | Heuristic Direct Recovery                                                | Secondary Baseline        |
| `escalation_aware_deterministic_thresh` | `{proceed, recover, escalate}`         | `{proceed, recover, escalate}` | Calibrated Threshold ($\tau_{\text{low}}=0.15, \tau_{\text{high}}=0.65$) | Secondary Baseline        |
| `fixed_verify_repair_macro`             | `{verify}`                             | `{proceed, recover}`           | Fixed Inspection-First Macro                                             | Historical Benchmark      |
| `oracle`                                | `{proceed, recover, escalate}`         | N/A                            | Ground-Truth Optimal                                                     | Diagnostic Reference Only |

### 4.2 Analytical Bayesian VOI Derivation

At Step 1, with observation $X$ and budget $B$:

1. Compute posterior defect probability $p_0 = P(\text{Defect} \mid X)$.
2. Evaluate expected utilities for terminal actions:
   $$U(\text{proceed}) = \begin{cases} V \cdot a_0 \cdot (1 - p_0) - H \cdot a_0 \cdot p_0 - C_{\text{apply}} - C_{\text{time}} L_0 & \text{if } p_0 \le 0.050 \\ -\infty & \text{if } p_0 > 0.050 \end{cases}$$
   $$U(\text{recover}) = V_{\text{rec}} \cdot a_0 - C_{\text{rec}} - C_{\text{time}} L_{\text{rec}}$$
   $$U(\text{escalate}) = \gamma_{\text{workflow}} V \cdot a_h \cdot (1 - P_{\text{err}}) P_{\text{salv}} - C_{\text{labor}} - C_{\text{time}} L_h - \text{Risk}_{\text{esc}}$$
3. If $B = 1$, prune `verify` (strictly dominated); return $\arg\max_{a \in \{\text{proc}, \text{rec}, \text{esc}\}} U(a)$.
4. If $B = 2$, compute Value of Information:
   $$U(\text{verify}) = \sum_{y \in \{0, 1\}} P(Y=y \mid X) \cdot \max_{a \in \mathcal{A}_{\text{term}}} U(a \mid X, Y=y) - C_{\text{verify}}$$
   If $U(\text{verify}) > \max(U(\text{proc}), U(\text{rec}), U(\text{esc}))$, select `verify`, else select best terminal action.

---

## 5. Counterfactual Study Runner & Order Invariance ([`study_v07_1.py`](../src_v07_1/causaguard_v07_1/study_v07_1.py))

### 5.1 The `QueueState` Isolation Mechanism

To prevent policies from interfering with each other's queue capacity:

```python
# study_v07_1.py lines 170-176
queue_states = {name: QueueState(capacity_limit=capacity_limit) for name in policies}

for case in cases:
    for name, policy in policies.items():
        ep = run_episode_v07_1(
            case=case,
            policy=policy,
            queue_state=queue_states[name],
            **step_kwargs,
        )
```

Each policy updates only its own `QueueState`.

### 5.2 Formal Policy-Order Invariance Guarantee

Because:

1. Cases in a cluster are deterministic pure data objects with fixed random draw tapes;
2. Policies receive immutable observation slices;
3. Queue states are maintained in separate, non-overlapping instances;
   The execution of Policy $A$ is a mathematical pure function of $(\text{Cases}, \text{Policy } A, \text{QueueState}_A)$, completely independent of the execution sequence or existence of Policy $B$.
   Formally:
   $$\mathcal{M}(\text{Policy } A \mid \text{Order } [A, B]) \equiv \mathcal{M}(\text{Policy } A \mid \text{Order } [B, A])$$
   Verified by unit test [`test_strict_policy_order_invariance`](../tests_v07_1/test_study_v07_1.py#L35).

---

## 6. Seed Namespace & Boundary Protection Architecture

```
========================================================================================
                      CausaGuard v0.7.1 SEED NAMESPACE MAP
========================================================================================
  SEED BLOCK               SCOPE / PURPOSE               STATUS / ACCESS RULE
  --------------------------------------------------------------------------------------
  60001001 – 60001010      v0.6 Exploratory Variance     Historical Archived
  60010001 – 60020064      v0.6 Development Confirmatory Historical Sealed (Master Protocol)
  60030001 – 60040064      v0.6 Final Confirmatory       PERMANENTLY QUARANTINED
  --------------------------------------------------------------------------------------
  70001001 – 70001016      v0.7 Exploratory Calibration  Historical Archived (Package 6D)
  70002001 – 70002016      v0.7.1 Fresh Calibration      AUTHORIZED FOR PACKAGE 6F-C
  70002017 – 70009999      Safety Buffer Zone            RESERVED BUFFER
  --------------------------------------------------------------------------------------
  70010001 – 70010160      CS Confirmatory Development   PROHIBITED (Pre-Freeze)
  70020001 – 70020084      DE Confirmatory Development   PROHIBITED (Pre-Freeze)
  70020085 – 70049999      Safety Buffer Zone            RESERVED BUFFER
  --------------------------------------------------------------------------------------
  70050001 – 70050160      CS Confirmatory Final         STRICT QUARANTINE
  70060001 – 70060084      DE Confirmatory Final         STRICT QUARANTINE
========================================================================================
```

The seed boundaries are strictly protected by assertions in [`test_identity_preservation_v07_1.py`](../tests_v07_1/test_identity_preservation_v07_1.py#L42), guaranteeing that fresh exploratory calibration will never contaminate prospective development or final confirmatory evaluation samples.

---

_Authored on behalf of the System Architecture Team,_
**CausaGuard PhD Programme**
6 November 2026

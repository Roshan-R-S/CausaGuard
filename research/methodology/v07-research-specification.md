# CausaGuard v0.7: Scientific Research Specification

**Status:** Official Scientific Specification  
**Version:** `0.7.0-draft`  
**Date:** 5 November 2026  
**Parent Document:** [`research/reviews/v06-methodological-remediation-plan.md`](../reviews/v06-methodological-remediation-plan.md)  
**Historical Dependencies:** Sealed v0.6 Protocol (`c0f217ca...`) and Historical v0.5.2 Freeze (`053dea36...`) strictly preserved  

---

## 1. Scientific Motivation & Revised Research Objectives

### 1.1 The Scientific Problem: Intervention Trade-offs in Tool-Using Agents
Autonomous software agents operating in production environments (customer operations, data transformation pipelines) must decide when to accept unverified outputs, when to invoke fallible inspection tools, when to initiate automated recovery, and when to escalate to human operators.

In primary literature (arXiv:2602.03338, *Accurate Failure Prediction Does Not Imply Effective Failure Prevention*), the **Intervention Paradox** establishes that automated interventions frequently degrade net system utility:
1. Interventions are triggered on false alarms or benign cases, disrupting healthy task completion.
2. Automated recovery mechanisms can cause secondary operational friction, queue latency, and SLA timeouts.
3. Fallible verifiers incur substantial inspection costs without eliminating underlying uncertainty.

### 1.2 Lessons from CausaGuard v0.6
The independent review of CausaGuard v0.6 ([`research/reviews/v06-independent-scientific-review.md`](../reviews/v06-independent-scientific-review.md)) proved that while the candidate policy (`cost_rule`) achieved massive utility gains over legacy baselines, this was an artifact of:
- **Structural baseline restriction:** Deterministic baselines were forced to verify first and prohibited from initiating direct recovery at Step 1, whereas `cost_rule` was unconstrained.
- **Absence of disruption in Customer Support:** Retrying clean records was modeled as completely harmless, making universal re-querying artificially optimal.
- **Dominated escalation:** Escalation incurred cost with zero completion reward, rendering it economically dead ($0.0\%$ burden).

### 1.3 Revised Core Research Question for CausaGuard v0.7
> **In high-stakes, tool-using agent workflows where interventions disrupt benign executions, does an analytical Bayesian Value-of-Information (VOI) decision policy achieve superior net economic utility over strong, fair direct-recovery and threshold heuristics, while strictly satisfying decoupled operational safety and runtime authorization constraints?**

### 1.4 Primary Falsifiable Hypotheses

Let $U(\pi)$ denote net economic utility per assigned task:
$$U(\pi) = \text{value} \cdot \text{completed} - \text{harm} \cdot \text{unsafe} - \text{operational\_costs}$$

#### Hypothesis 1 (Customer Support Direct-Recovery Margin):
$$H_1^{(\text{CS})}: \mathbb{E}\left[U(\pi_{\text{VOI}}) - U(\pi_{\text{always\_retry}})\right] > \Delta_{\text{util}} = +0.015$$
- *Null Hypothesis $H_0^{(\text{CS})}$:* $\mathbb{E}[U(\pi_{\text{VOI}}) - U(\pi_{\text{always\_retry}})] \le +0.015$.
- *Scientific Meaning:* If the null is not rejected, analytical Bayesian VOI fails to provide a meaningful advantage over simple universal recovery, establishing that the complexity of Bayesian inspection planning is unjustified in this domain.

#### Hypothesis 2 (Data Engineering Direct-Recovery Margin):
$$H_1^{(\text{DE})}: \mathbb{E}\left[U(\pi_{\text{VOI}}) - U(\pi_{\text{always\_restore}})\right] > \Delta_{\text{util}} = +0.015$$
- *Null Hypothesis $H_0^{(\text{DE})}$:* $\mathbb{E}[U(\pi_{\text{VOI}}) - U(\pi_{\text{always\_restore}})] \le +0.015$.
- *Scientific Meaning:* If the null is not rejected, rolling back every suspicious batch is as effective as computing sequential Bayesian VOI.

#### Hypothesis 3 (Heuristic Threshold Dominance):
$$H_1^{(\text{Heuristic})}: \min_{d \in \{\text{CS}, \text{DE}\}} \mathbb{E}\left[U(\pi_{\text{VOI}}) - U(\pi_{\text{threshold\_recovery}})\right] > \Delta_{\text{util}} = +0.015$$
- *Null Hypothesis $H_0^{(\text{Heuristic})}$:* Analytical VOI does not significantly outperform calibrated deterministic threshold heuristics under matched action spaces.

#### Safety and Authorization Joint Constraints:
In addition to utility, the candidate policy must simultaneously satisfy:
1. Operational Risk Gate: $\hat{R}_{\text{upper}}(\pi_{\text{VOI}}) \le \tau_{\text{safe}} = 0.050$.
2. Pairwise Excess Risk Gate: $\max_{j} \widehat{\Delta R}_{\text{upper}, j} \le \tau_{\text{excess}} = +0.005$.
3. Authorization Gate: Zero runtime permission violations across all evaluated episodes.

---

## 2. Fair Comparator Architecture (The 9-Policy Suite)

To prevent the structural asymmetry that invalidated v0.6, all eligible policies in v0.7 operate under **strictly identical information sets, identical operation budgets ($B \in \{1, 2\}$), and identical feasible action sets at Step 1**:
$$\mathcal{A}_{\text{step1}} = \{\text{proceed}, \text{verify}, \text{recovery}, \text{escalate}\}$$
where $\text{recovery} = \text{retry}$ in Customer Support, and $\text{restore}$ in Data Engineering.

```
+---------------------------------------------------------------------------------------+
|                                    POLICY TAXONOMY                                    |
+------------------------------------+--------------------------------------------------+
| Reference Baselines                | 1. rules_proceed (Unconditional execution)       |
|                                    | 2. always_escalate (Risk-free human deferral)    |
|                                    | 3. always_verify_then_proceed (Blind inspect)   |
+------------------------------------+--------------------------------------------------+
| Historical Comparator              | 4. fixed_verify_repair_macro (Legacy v0.5 macro) |
+------------------------------------+--------------------------------------------------+
| Strong Direct-Recovery Baselines   | 5. always_retry / always_restore (Universal rec) |
| (Resolving C-01)                   | 6. budget_aware_direct_recovery (B=1 prune)     |
|                                    | 7. cost_sensitive_threshold_recovery (Heuristic) |
+------------------------------------+--------------------------------------------------+
| Candidate & Diagnostic             | 8. cost_rule_v07 (Analytical Bayesian VOI)       |
|                                    | 9. oracle (Diagnostic upper bound, privileged)  |
+------------------------------------+--------------------------------------------------+
```

### 2.1 Detailed Policy Specifications

1. **`rules_proceed` (Blind Proceed):**  
   - Step 1: Selects `proceed` unconditionally. Post-verify: selects `proceed` if budget remains, else `escalate`.
2. **`always_escalate` (Universal Human Deferral):**  
   - Selects `escalate` unconditionally at all steps (0 operations consumed).
3. **`always_verify_then_proceed` (Blind Inspection):**  
   - Step 1: Selects `verify`. Post-verify: selects `proceed` if feasible ($b_{\text{rem}} \ge 1$), else falls back to `escalate`.
4. **`fixed_verify_repair_macro` (Historical Legacy Baseline):**  
   - At $B=1$: proceeds if alarm $\le 0.50$, else escalates.
   - At $B=2$: calls `verify`. If flagged, calls recovery; else proceeds. (Replicates historical v0.5/v0.6 macro).
5. **`always_retry` [CS] / `always_restore` [DE] (Universal Direct Recovery):**  
   - Step 1: Unconditionally selects `recovery` (bypassing `verify`).
   - *Role:* Primary comparator for Hypothesis 1 and 2. Tests whether universal recovery dominates inspection.
6. **`budget_aware_direct_recovery`:**  
   - At $B=1$: selects `recovery` directly (recognizing that `verify` is strictly dominated when $B=1$).
   - At $B=2$: if alarm signal $> 0.50$, selects `recovery` directly; else calls `verify` and recovers if flagged.
7. **`cost_sensitive_threshold_recovery` (Tuned Deterministic Heuristic):**  
   - Uses observable cost ratios and alarm signals:
     $$\pi_{\text{thresh}}(X) = \begin{cases}
     \text{proceed} & \text{if } \text{alarm} \le \tau_{\text{alarm}} \land \text{age} \le \tau_{\text{age}} \\
     \text{recovery} & \text{if } \text{alarm} > \tau_{\text{alarm}} \land C_{\text{rec}} \le C_{\text{ver}} \\
     \text{verify} & \text{if } \text{alarm} > \tau_{\text{alarm}} \land C_{\text{rec}} > C_{\text{ver}} \land B \ge 2 \\
     \text{escalate} & \text{otherwise}
     \end{cases}$$
   - Thresholds $\tau_{\text{alarm}}, \tau_{\text{age}}$ are prespecified during exploratory calibration.
8. **`cost_rule_v07` (Candidate Analytical Bayesian VOI):**  
   - Consumes only public covariates $X$, budget $B$, and evidence $E$.
   - Evaluates closed-form expected utility for all feasible actions in $\mathcal{A}_{\text{step1}}$ and $\mathcal{A}_{\text{step2}}$.
   - Prunes `verify` at $B=1$ (strictly dominated).
   - Enforces operational safety constraint $P(\text{Unsafe}) \le 0.050$.
9. **`oracle` (Diagnostic Upper Bound):**  
   - Privileged policy selecting the argmax over realized potential outcomes. Diagnostic reference only.

---

## 3. Customer Support Domain Redesign (v0.7)

### 3.1 Latent State Space and Generative Model
Each episode is characterized by public covariates $X$ and latent state $Y \in \{\text{clean}, \text{stale}, \text{fraud}\}$:
- `ticket_age_hours` $\in [0.0, 96.0]$
- `queue_load` $\in [0.0, 1.0]$ ($\sim \text{Beta}(2, 4)$)
- `source_reliability` $\in [0.35, 1.0]$
- `conflict_alarm` $\in [0.0, 1.0]$
- Latent staleness: $P(\text{stale}) = \text{clip}(0.04 + 0.28 \cdot (\text{age}/72) + 0.18 \cdot \text{load}, 0.01, 0.90)$
- Latent fraud: Conditioned on staleness and conflict alarm:
  $$P(\text{fraud} \mid \text{stale}) = 0.15 + 0.50 \cdot (\text{conflict\_alarm}^2)$$
  $$P(\text{fraud} \mid \neg\text{stale}) = 0.02 + 0.10 \cdot (\text{conflict\_alarm}^2)$$
- True defect indicator: $\text{defect} = \mathbb{I}(Y \in \{\text{stale}, \text{fraud}\})$.

### 3.2 Action Mechanics and Realistic Disruption

#### 1. Action `proceed`:
- Execution latency: $L = t_{\text{curr}} + 0.10$. Late if $L > \text{deadline}$.
- Upstream availability: $U_0 \ge \text{source\_outage}$.
- Outcome: Completed if available and not late. Unsafe if completed and $\text{defect} = \text{True}$.
- Net Utility: $U = V \cdot \text{completed} - H \cdot \text{unsafe} - C_{\text{apply}} - c_{\text{time}} \cdot L$.

#### 2. Action `verify` (Consistency Check, Non-Terminal, 1 Op):
- Latency: $L = t_{\text{curr}} + \text{obs\_delay} + 0.20$.
- Cost: $C_{\text{verify}} \in [0.06, 0.50] \times \text{cost\_multiplier}$.
- Fallible signal: Flagged with quoted $FP \in [0.015, 0.095]$ and $FN \in [0.025, 0.245]$.

#### 3. Action `retry` (Authoritative Re-Query Recovery, Terminal, 1 Op):
- **Recovery Uncertainty:** Authoritative re-fetch cures staleness with probability:
  $$\rho_{\text{cs}} = \text{clip}(0.35 + 0.45 \cdot \text{source\_reliability} - 0.20 \cdot \text{queue\_load}, 0.10, 0.95)$$
- **Fraud Incurable by Re-Query:** If $Y = \text{fraud}$, re-querying external customer tables **cannot cure fraudulent identity** $\implies \text{completed} = 0, \text{unsafe} = 0$.
- **Disruption on Benign Cases ($Y = \text{clean}$):**  
  Re-querying an already-clean ticket triggers secondary verification friction:
  $$P(\text{friction} \mid Y = \text{clean}) = \text{clip}(0.15 + 0.35 \cdot \text{queue\_load}, 0.05, 0.70)$$
  - Customer abandonment: With probability $P(\text{abandon}) = 0.25$, customer drops session $\implies \text{completed} = 0$.
  - Completion friction discount: If completed, customer satisfaction penalty discounts value:
    $$V_{\text{clean\_retry}} = V \cdot \left(1.0 - \text{clip}\left(0.10 + 0.20 \cdot \frac{L}{\text{deadline}}, 0.10, 0.40\right)\right)$$
- *Scientific Status of Assumptions:* The friction probability $P(\text{friction})$, abandonment rate ($25\%$), and discount ($10\%-40\%$) are **model assumptions**. Section 5 specifies sensitivity intervals.

#### 4. Action `escalate` (Human Specialist Review, Terminal, 0 Ops):
- Latency: $L = t_{\text{curr}} + 0.50 + 1.20 \cdot \text{queue\_load}$.
- Operational Cost: $C_{\text{esc}} \in [0.20, 0.45] \times \text{cost\_multiplier}$.
- Human Availability: $P(\text{available}) = \text{clip}(1.0 - 0.30 \cdot \text{queue\_load}, 0.50, 0.98)$. If saturated, ticket times out.
- **Conditional Human Salvage Probabilities:**
  - On Fraud ($Y = \text{fraud}$): $P(\text{salvage} \mid \text{fraud}) = 0.70$. If salvaged: fraudulent attempt blocked, resolution completed safely $\implies \text{completed} = 1, \text{unsafe} = 0, V_{\text{net}} = V$.
  - On Stale ($Y = \text{stale}$): $P(\text{salvage} \mid \text{stale}) = 0.85 \implies \text{completed} = 1, \text{unsafe} = 0, V_{\text{net}} = V$.
  - On Clean ($Y = \text{clean}$): $P(\text{salvage} \mid \text{clean}) = 0.95 \implies \text{completed} = 1, \text{unsafe} = 0, V_{\text{net}} = V$.
- *Scientific Status of Assumptions:* The $70\%$ fraud salvage probability is an **explicit model assumption requiring sensitivity analysis**.

---

## 4. Data Engineering Domain Redesign (v0.7)

### 4.1 Multivariate Failure Modes
Data Engineering models four distinct, realistic pipeline hazards:
1. $F_{\text{schema}}$: Upstream schema migration / column type mismatch ($P \approx 0.02 - 0.45$).
2. $F_{\text{content}}$: Numerical corruption / null-byte contamination ($P \approx 0.10 - 0.70$).
3. $F_{\text{metalag}}$: Upstream replication lag ($P \approx 0.05 - 0.45$).
4. $F_{\text{transient}}$: Undetectable worker node OOM / deadlock ($P \approx 0.01 - 0.05$).

### 4.2 Distinguishing Rollback from Structural Repair

#### 1. Action `proceed`:
- Commits transformation. If hazard present ($F_{\text{schema}} \lor F_{\text{content}} \lor F_{\text{transient}}$), causes disaster harm $H \in [2.50, 7.00]$ (mean $\$4.50$).

#### 2. Action `verify` (Schema + Content Sample Check, Non-Terminal, 1 Op):
- Tests schema validation and sample pass rate. Transient hazard $F_{\text{transient}}$ is unobservable by verification.

#### 3. Action `restore` (Checkpoint Rollback Recovery, Terminal, 1 Op):
- Rollback restores partition to clean prior snapshot ($F_{\text{content}} = 0, F_{\text{transient}} = 0$).
- **Efficacy Conditioned on Hazard Type:**
  - If $F_{\text{schema}} = 0$: Rollback succeeds safely $\implies \text{completed} = 1, \text{unsafe} = 0$, awards fallback utility $V_{\text{fallback}} = 0.45 V$.
  - If $F_{\text{schema}} = 1$ (Structural Schema Drift): Upstream schema is permanently altered. Rolling back to old snapshot **does not repair transformation code**.
    $$P(\text{persistent\_schema\_incompatibility}) = 0.80$$
    Pipeline restarts and crashes immediately $\implies V_{\text{fallback}} = 0.10 V$ (heavily degraded fallback).

#### 4. Action `escalate` (Data Engineer Intervention, Terminal, 0 Ops):
- Latency: $L = t_{\text{curr}} + 0.60 + 1.50 \cdot \text{pipeline\_load}$. Cost: $C_{\text{esc}} \in [0.25, 0.55]$.
- Human Engineer Salvage:
  - On Schema Drift ($F_{\text{schema}} = 1$): Engineer updates transformation DDL mapping with probability:
    $$P(\text{engineer\_fix} \mid \text{schema}) = 0.85$$
    If fixed: achieves full transformation completion $\implies \text{completed} = 1, \text{unsafe} = 0, \text{value} = V$.
  - On Content / Transient ($F_{\text{content}} = 1 \lor F_{\text{transient}} = 1$): Engineer identifies bad batch or restarts cluster with probability $0.90 \implies \text{completed} = 1, \text{value} = V$.
- *Scientific Status of Assumptions:* The $85\%$ engineer resolution rate and $80\%$ schema persistence rate are **explicit model assumptions requiring sensitivity analysis**.

---

## 5. Inventory of Parametric Assumptions & Sensitivity Protocol

To maintain scientific integrity, all parametric assumptions introduced in v0.7 are documented below with their provisional planning values, plausible sensitivity ranges, and required calibration protocols:

| Parameter Description | Symbolic Name | v0.7 Planning Value | Sensitivity Test Range | Empirical Calibration Requirement |
|---|---|---|---|---|
| **CS Clean Retry Friction Probability** | $P(\text{fric} \mid \text{clean})$ | $0.15 + 0.35 \cdot \text{load}$ | $[0.05, 0.80]$ | Measure user re-authentication drop-off in CRM logs |
| **CS Customer Abandonment Rate** | $P(\text{abandon})$ | $0.25$ ($25\%$) | $[0.10, 0.45]$ | Analyze session drop rate under 2FA step-up prompts |
| **CS Clean Retry Value Discount** | $D_{\text{friction}}$ | $10\% - 40\%$ | $[0\%, 50\%]$ | Customer CSAT survey degradation after delay |
| **CS Human Fraud Salvage Probability** | $P(\text{salvage} \mid \text{fraud})$ | $0.70$ ($70\%$) | $[0.40, 0.90]$ | Historical fraud review desk resolution rates |
| **DE Rollback Fallback Value Ratio** | $V_{\text{fallback}} / V$ | $0.45$ ($45\%$) | $[0.20, 0.60]$ | Downstream business value of stale snapshot data |
| **DE Schema Drift Persistent Failure**| $P(\text{fail} \mid \text{schema})$ | $0.80$ ($80\%$) | $[0.50, 0.95]$ | Frequency of schema errors resolving without DDL fix |
| **DE Engineer Schema Fix Probability** | $P(\text{fix} \mid \text{schema})$ | $0.85$ ($85\%$) | $[0.60, 0.95]$ | On-call engineer runbook mean-time-to-resolution |

> [!IMPORTANT]
> **Mandatory Sensitivity Analysis Protocol:**
> During exploratory calibration, a multi-parameter sensitivity grid must be simulated across the defined ranges. If analytical VOI superiority over `always_retry` holds only within a narrow parameter band (e.g. only when friction $> 35\%$), the study must report this as a **conditional finding**, not a universal property of agent intervention.

---

## 6. Seed Namespace Partitioning & Isolation

All CausaGuard v0.7 runs are strictly isolated from historical v0.5 and v0.6 seeds:

```
+---------------------------------------------------------------------------------------+
|                              v0.7 SEED PARTITIONING MATRIX                            |
+-----------------------------------+-------------------+-------------+-----------------+
| Namespace                         | Seed Allocation   | Clusters(K) | Cases/Clust(N)  |
+-----------------------------------+-------------------+-------------+-----------------+
| v0.6 Final Seeds (QUARANTINED)    | 60030001-60040064 | 64          | 250 (SEALED)    |
| v0.7 Exploratory Calibration      | 70001001-70001016 | 16          | 250             |
| v0.7 CS Development Evaluation    | 70010001-70010064 | 64          | 250             |
| v0.7 DE Development Evaluation    | 70020001-70020064 | 64          | 250             |
| v0.7 CS Final Evaluation (LOCKED) | 70030001-70030064 | 64          | 250 (RESERVED)  |
| v0.7 DE Final Evaluation (LOCKED) | 70040001-70040064 | 64          | 250 (RESERVED)  |
+-----------------------------------+-------------------+-------------+-----------------+
```

- **Quarantine Guarantee:** v0.6 reserved final seeds (`60030001–60040064`) remain in permanent cold storage.
- **Reservation Guarantee:** v0.7 final seeds (`70030001–70040064`) will **never be generated, touched, or evaluated** during development or calibration.

---

## 7. Status of v0.6 Historical Results

The results in [`artifacts_v06/dev_eval/dev_evaluation_summary.json`](../../artifacts_v06/dev_eval/dev_evaluation_summary.json) remain **valid descriptive findings** for the historical v0.6 generative model and asymmetric baseline suite. They are permanently archived and will not be overwritten, altered, or claimed as evidence for v0.7 hypotheses.


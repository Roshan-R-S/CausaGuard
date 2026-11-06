# CausaGuard v0.7: Scientific Escalation Remediation Design and Benchmark Specification

**Status:** Official Methodological Remediation Design Document, CausaGuard PhD Research Programme  
**Date:** 6 November 2026  
**Scope:** Engineering Package 6F-A — Scientific Remediation Decision, Human Escalation Model, and Prospective Redesign  
**Referenced Evidence:**
- [research/reviews/v07-independent-scientific-review.md](file:///d:/causaguard/research/reviews/v07-independent-scientific-review.md)
- [research/methodology/v07-protocol-freeze-readiness.md](file:///d:/causaguard/research/methodology/v07-protocol-freeze-readiness.md)
- [docs/v07-exploratory-calibration-report.md](file:///d:/causaguard/docs/v07-exploratory-calibration-report.md)
- [artifacts_v07/exploratory/exploratory_summary.json](file:///d:/causaguard/artifacts_v07/exploratory/exploratory_summary.json)
- [research/methodology/v07-research-specification.md](file:///d:/causaguard/research/methodology/v07-research-specification.md)
- [research/methodology/v07-statistical-analysis-plan.md](file:///d:/causaguard/research/methodology/v07-statistical-analysis-plan.md)
- [research/methodology/v07-power-erratum.md](file:///d:/causaguard/research/methodology/v07-power-erratum.md)
- [src_v07/causaguard_v07/policy_v07.py](file:///d:/causaguard/src_v07/causaguard_v07/policy_v07.py)
- [src_v07/causaguard_v07/domain_cs.py](file:///d:/causaguard/src_v07/causaguard_v07/domain_cs.py)
- [src_v07/causaguard_v07/domain_de.py](file:///d:/causaguard/src_v07/causaguard_v07/domain_de.py)
- [src_v07/causaguard_v07/study_v07.py](file:///d:/causaguard/src_v07/causaguard_v07/study_v07.py)

**Strict Scientific & Repository Boundaries:** Documentation-only specification. Zero code modifications, zero simulations, zero benchmark executions, zero tests. Historical v0.5.2 and sealed v0.6 artifacts and cryptographic seals remain preserved and byte-identical. Quarantined v0.6 seeds (`60030001–60040064`), v0.7 development seeds (`70010001–70020064`), and reserved final seeds (`70030001–70040064`) remain strictly untouched.

---

## 1. Executive Summary & Purpose

This document provides the formal scientific remediation blueprint for CausaGuard v0.7. Following the independent review in Package 6E, which issued a **NO-GO on protocol freezing** and a **STRICT HOLD on confirmatory evaluation**, this redesign addresses the fundamental methodological, decision-theoretic, and baseline defects discovered during exploratory calibration:

1. **Reconciliation of Scientific Findings:** Explaining why naive escalation (`always_escalate`) defeated the Bayesian Value of Information (VOI) candidate policy (`cost_rule_v07`) in Data Engineering, and why the candidate policy collapsed into an escalation monoculture ($77–88\%$ escalation).
2. **Procedural Review Audit:** Documenting the post-hoc threshold heuristic discovery (`if conflict_alarm > 0.30: escalate else proceed`) and establishing the research boundaries of that observation.
3. **Principled Human-Intervention Model:** Formulating a realistic, multi-attribute generative escalation model that replaces the "free-lunch" escalation mechanics with explicit labor costs, queuing delay distributions, capacity bounds, and downstream workflow value degradation.
4. **Symmetric Comparator Suite:** Eliminating the strawman baseline defect by specifying a balanced 8-policy benchmark suite where all comparators operate under identical information sets, feasible action spaces, safety constraints, and budgets.
5. **Orthogonal Scientific Design:** Ensuring the benchmark can decisively distinguish between verification value, recovery value, human escalation value, and benign workflow disruption, treating all four outcomes (VOI wins, heuristic wins, escalation wins, recovery wins) as valid, publishable scientific regimes.
6. **Isolation Architecture:** Specifying the implementation strategy for Package 6F-B, isolating the remediated benchmark as **CausaGuard v0.7.1** to ensure total preservation of historical v0.7 exploratory data.

---

## 2. Scientific Diagnosis of Exploratory Failures

### 2.1 The Data Engineering Inversion: Why `always_escalate` Defeated Analytical VOI

In the exploratory calibration of v0.7 ([`docs/v07-exploratory-calibration-report.md`](file:///d:/causaguard/docs/v07-exploratory-calibration-report.md)), the candidate policy `cost_rule_v07` was outperformed by the zero-intelligence baseline `always_escalate`:
- `always_escalate` Mean Utility: $\mathbf{+0.4188}$ ($S = 0.0275$)
- `cost_rule_v07` Mean Utility: $\mathbf{+0.4033}$ ($S = 0.0317$)
- **Paired Mean Difference ($\bar{D}$):** $\mathbf{-0.0155}$ ($S_D = 0.0142, t_{15} = -4.37, p = 0.00028$)

The candidate policy was strictly inferior in 14 out of 16 clusters. The mathematical mechanism underlying this inversion is rooted in the asymmetric economic payoffs between automated recovery and human escalation in [`domain_de.py`](file:///d:/causaguard/src_v07/causaguard_v07/domain_de.py):

```
========================================================================================
                 DATA ENGINEERING: AUTOMATED RECOVERY VS. HUMAN ESCALATION
========================================================================================
  ATTRIBUTE                        AUTOMATED CHECKPOINT RESTORE      HUMAN DATA ENGINEER ESCALATION
  --------------------------------------------------------------------------------------
  1. Operation Budget Cost:        Consumes B = 1 operation         Consumes B = 0 operations
  2. Latency Added:                0.20h + Load + Jitter (0.15h)     0.60h + 1.50 * Load
  3. Direct Dollar Cost:           restore_cost ($0.08)              escalation_cost ($0.30)
  4. Operational Harm Risk:        Vulnerable to H_transient         Completely eliminated (H = 0)
  5. Recovery Success Rate:        100% on transient/content         85% on schema, 90% on content
                                   20% on structural schema drift   100% on clean cases
  6. Completion Value Awarded:     0.45 * V (Fallback degradation)   1.00 * V (FULL COMPLETION VALUE)
                                   0.10 * V (Persistent schema drift)
========================================================================================
```

Whenever `cost_rule_v07` attempts autonomous recovery or verification ($17\%$ of DE cases):
1. **The Fallback Value Penalty:** Autonomous restore permanently degrades pipeline output to fallback status, recovering only $45\%$ of value ($0.45 \times V$). If schema drift is present, recovery succeeds in only $20\%$ of cases, collapsing value to $10\%$ ($0.10 \times V$).
2. **The Verification Inspection Tax:** Paying $\$0.08$ for verification plus observation delay adds cost without eliminating unobservable downstream transient hazards ($p_t$).
3. **The Escalation Advantage:** In contrast, escalating directly to an engineer guarantees that if the engineer fixes the issue ($85–90\%$ probability), the pipeline awards **$100\%$ full net completion value ($1.0 \times V$)** with **zero operational harm risk ($H = 0$)** and **zero operations consumed ($B = 0$)**.

Because human engineers salvage full value while automated restore incurs severe value haircuts, the expected utility of autonomous actions is structurally depressed. The candidate policy's attempts to act autonomously dragged its expected utility down from $+0.4188$ to $+0.4033$.

### 2.2 Why Did the Candidate Policy Collapse into an Escalation Monoculture?

Action distribution tracking across 8,000 exploratory cases confirmed that `cost_rule_v07` escalated in **$77.2\%$ of CS cases** and **$87.9\%$ of DE cases**, verifying in only $5.6\%$ (CS) and $13.4\%$ (DE).

This behavior was driven by five interacting simulator properties:

1. **Rational Policy Behavior Under Distorted Payoffs:**  
   The Bayesian VOI engine in [`CostRulePolicyV07`](file:///d:/causaguard/src_v07/causaguard_v07/policy_v07.py#L248-L520) is not computationally flawed. It computes closed-form expected utilities:
   $$U(\text{escalate}) = V \cdot a_{\text{human}} \cdot p_{\text{salvage}} - C_{\text{escalate}} - C_{\text{time}} \cdot L_{\text{escalate}}$$
   Given that $p_{\text{salvage}} \in [0.70, 0.95]$ and $V_{\text{salvage}} = 1.0 \times V$, $U(\text{escalate})$ is consistently positive ($\approx +0.40$ to $+0.55$).
2. **Unrealistically Generous Human Salvage Assumptions:**  
   In both domains, human specialists fix defects with near-perfect reliability ($70\%$ on fraud, $85\%$ on stale, $85\%$ on schema, $90\%$ on content, and $95–100\%$ on clean cases). The simulator assumed human intervention is essentially infallible and non-destructive.
3. **Underestimated Escalation Cost and Friction:**  
   The escalation fee was set to only $\$0.25$ in CS and $\$0.30$ in DE. In enterprise settings, routing a ticket to a tier-2 human specialist or waking an on-call data engineer costs an order of magnitude more than an automated API query.
4. **Complete Absence of Human Capacity Constraints:**  
   The simulator modeled human specialists as having infinite bandwidth. Queue load increased latency linearly, but there was no queue drop probability, no backlog saturation threshold, no availability cliff, and no operational ceiling.
5. **Static Tool Blindness to Dynamic Hazards:**  
   Verification tools only audited static attributes (credential validity, column counts). They could not detect transient execution hazards ($p_{\text{transient}}$). Because the safety constraint enforced $P(\text{Harm}) \le 0.050$, and prior hazards frequently exceeded $0.10$, automated proceed was pruned. With recovery heavily penalized by fallback discounts, escalation was the only viable path.

### 2.3 Investigation of the Post-Hoc Threshold Discovery & Procedural Deviation Audit

During the Package 6E review, a diagnostic probe tested a simple deterministic threshold rule:
```python
# Post-hoc exploratory heuristic probe
if observation.conflict_alarm > 0.30:
    action = "escalate"
else:
    action = "proceed"
```
When evaluated against the Customer Support exploratory cases, this rule achieved a mean cluster utility of **$\mathbf{+0.6155}$**, outperforming `cost_rule_v07` ($+0.5199$) by **$+0.0956$ utility**.

#### Procedural Deviation Audit:
1. **Origin and Scope:** This calculation was executed as an inline diagnostic probe to investigate why the prespecified heuristic baseline `cost_sensitive_threshold_recovery` performed poorly ($+0.2967$).
2. **Data and Artifact Integrity:** The probe was executed entirely in memory against the already-generated exploratory cases. **Zero files were modified, zero raw telemetry files were altered, zero seed ranges were violated, and zero cryptographic seals were touched.**
3. **Scientific Classification:** This 2-line heuristic must be classified strictly as a **post-hoc exploratory discovery**, **NOT** an independently validated primary comparator. Claiming that this specific rule "disproves" VOI would commit the exact data-dredging fallacy that confirmatory protocols exist to prevent.
4. **Methodological Significance:** The significance of this discovery is not the specific threshold value ($0.30$), but the structural revelation that **`cost_sensitive_threshold_recovery` was artificially crippled**. In [`policy_v07.py`](file:///d:/causaguard/src_v07/causaguard_v07/policy_v07.py#L218-L235), `cost_sensitive_threshold_recovery` was hardcoded never to escalate at Step 1! The apparent superiority of `cost_rule_v07` over the heuristic was a spurious artifact of comparing an unconstrained policy against an artificially restricted baseline.

---

## 3. Principled Human-Intervention Generative Model

To resolve the escalation monoculture, the generative simulator must model human escalation with realistic operational friction, capacity constraints, labor costs, and workflow degradation.

### 3.1 Decomposed Multi-Attribute Escalation Architecture

Human intervention must not be represented as a static fee with guaranteed completion. We specify an explicit 7-component decomposition:

$$\mathcal{M}_{\text{escalate}} = \langle C_{\text{labor}}, \; L_{\text{queue}}, \; \mathcal{K}_{\text{capacity}}, \; P_{\text{salvage}}, \; P_{\text{error}}, \; \mathcal{H}_{\text{human}}, \; \gamma_{\text{workflow}} \rangle$$

```
                                  +-----------------------+
                                  |   Escalate Action     |
                                  +-----------+-----------+
                                              |
                         +--------------------+--------------------+
                         |                                         |
               [Capacity & Availability]                 [Labor Cost & Latency]
                         |                                         |
               Queue Load > Threshold?                   Base Fee + Queue Delay
                         |                                         |
             +-----------+-----------+                             |
             |                       |                             |
      (Backlog Drop)          (Accepted)                           |
         Fail Case                   |                             |
                                     +--------------+--------------+
                                                    |
                                          [Specialist Review]
                                                    |
                                    +---------------+---------------+
                                    |                               |
                              (Human Error)                  (Salvage Attempt)
                             Unsafe or Fail                         |
                                                    +---------------+---------------+
                                                    |                               |
                                               (Unsalvageable)                 (Salvaged)
                                                  Fail Case                         |
                                                                        [Workflow Value Discount]
                                                                        V_net = gamma * V - Costs
```

#### 1. Labor Handling Cost ($C_{\text{labor}}$):
Human specialist time is expensive relative to automated compute:
- **Customer Support:** Base human handling fee $C_{\text{human\_base}} = \$0.45$ (escalates with queue congestion).
- **Data Engineering:** On-call data engineer engagement fee $C_{\text{engineer\_base}} = \$0.75$.

#### 2. Queuing Delay Distribution ($L_{\text{queue}}$):
Human review is not instantaneous. Latency follows a shifted log-normal or exponential queue distribution:
$$L_{\text{queue}} = L_0 + \beta \cdot \text{Load} + \eta_{\text{wait}}, \quad \eta_{\text{wait}} \sim \text{Exponential}(\lambda_{\text{queue}})$$
Where $L_0 = 0.75\text{h}$ in CS, $1.20\text{h}$ in DE. If $L_{\text{queue}} > \text{Deadline}$, the task is marked **late** and incurs contractual penalties.

#### 3. Availability and Capacity Saturation ($\mathcal{K}_{\text{capacity}}$):
Human teams have finite concurrency limits. If cumulative escalation volume in a cluster or operational window exceeds capacity, subsequent escalations suffer **queue drop / rejection**:
$$P(\text{Available} \mid \text{Load}) = \max\left(0.10, \; 1.0 - \kappa_1 \cdot \text{Load} - \kappa_2 \cdot (\text{ClusterEscalationRate})^2 \right)$$
Rejected escalations result in immediate ticket abandonment or pipeline failure ($\text{Utility} = -\text{Cost}$).

#### 4. Realistic Salvage Probability by Fault Category ($P_{\text{salvage}}$):
Human specialists cannot magically cure all defects:
- Fraudulent intent (CS): $P(\text{Salvage} \mid \text{Fraud}) = 0.60$ (was $0.70$).
- Stale data / out-of-sync (CS): $P(\text{Salvage} \mid \text{Stale}) = 0.80$ (was $0.85$).
- Structural schema drift (DE): $P(\text{Salvage} \mid \text{Schema}) = 0.75$ (was $0.85$).
- Corrupted content (DE): $P(\text{Salvage} \mid \text{Content}) = 0.80$ (was $0.90$).
- Transient cluster failure (DE): $P(\text{Salvage} \mid \text{Transient}) = 0.85$ (was $1.00$).

#### 5. Specialist Error Rate & Unsuccessful Intervention ($P_{\text{error}}$):
Humans make mistakes under cognitive load:
$$P(\text{Human Error}) = 0.05 + 0.10 \cdot \text{Load}$$
An error results in misclassification, failed resolution, or invalid data patching.

#### 6. Operational Risk of Human Intervention ($\mathcal{H}_{\text{human}}$):
Human intervention is not zero-risk. While specialist intervention reduces direct catastrophic harm, manual database patching, table drops, or credential overrides introduce latent operational risk ($P(\text{Unsafe}) \approx 0.005$ to $0.010$).

#### 7. Downstream Workflow Value Degradation ($\gamma_{\text{workflow}}$):
When a task is escalated to a human, the business value realized is discounted due to human handling delay, customer dissatisfaction, and downstream batch pipeline synchronization loss:
$$V_{\text{escalate}} = \gamma_{\text{workflow}} \cdot V$$

### 3.2 Evaluation of the Proposal to Force Escalation to Consume One Automated Operation

In Package 6E, it was proposed that escalation consume $B = 1$ operation. We evaluate this proposal from first principles:

```
========================================================================================
             EVALUATION: CONSUMING AUTOMATED BUDGET (B = 1) FOR ESCALATION
========================================================================================
  ARGUMENT FOR B = 1:
    - In a discrete finite-horizon decision process, every action transition consumes a 
      decision epoch. Allowing escalation at B=0 allows the agent to treat escalation as 
      a cost-free 'bonus' move after exhausting all automated attempts.
    - Setting B_escalate = 1 prevents the policy from attempting risky actions at B=1 and 
      then falling back to escalation for free at B=0.

  ARGUMENT AGAINST B = 1 (CONCEPTUAL CLARITY):
    - B specifically represents the AUTOMATED TOOL EXECUTION BUDGET (number of API calls, 
      queries, or automated scripts permitted by policy).
    - Human escalation is an EXIT from the automated loop. Penalizing an exit transition 
      using automated compute credits conflates machine compute limits with organizational 
      routing boundaries.
    - If B=1, an agent that executes 'verify' (consuming 1 op) would have B_rem = 0, and 
      would be FORBIDDEN from escalating to a human! This would force the agent to either 
      proceed blindly or fail, creating an absurd operational rule where gathering 
      information makes human escalation illegal!

  SCIENTIFIC RESOLUTION:
    - REJECT the crude B_escalate = 1 rule for post-verification states.
    - ADOPT a Macro-Decision Budget framework: The policy has a maximum horizon of 2 steps.
    - Enforce EXPLICIT HUMAN RESOURCE CONSTRAINTS (higher dollar cost, capacity limits, 
      and workflow value discounts) rather than an artificial tool-budget kludge.
========================================================================================
```

### 3.3 Evaluation of Salvage Value Multipliers ($\gamma_{\text{CS}} = 0.80, \gamma_{\text{DE}} = 0.75$)

The suggested multipliers ($\gamma_{\text{CS}} = 0.80, \gamma_{\text{DE}} = 0.75$) proposed in Package 6E were **exploratory hypotheses**, not empirically validated constants.

#### Domain-Specific Justifications:
1. **Customer Support ($\gamma_{\text{CS}} \in [0.70, 0.85]$):**  
   When a customer issue is escalated to tier-2 human agents, resolution takes hours instead of seconds. Industry data shows significant satisfaction degradation, increased ticket abandonment, and customer compensation (goodwill credits, partial fee waivers). A value retention factor of $\gamma_{\text{CS}} = 0.80$ reflects a $20\%$ value haircut from delayed resolution.
2. **Data Engineering ($\gamma_{\text{DE}} \in [0.65, 0.80]$):**  
   In production data pipelines, an incident escalated to an on-call engineer requires triage, root-cause analysis, and manual backfilling. Downstream BI dashboards and real-time ML feature stores miss SLA windows. Data consumers operate on stale data or fallback caches. A value retention factor of $\gamma_{\text{DE}} = 0.75$ reflects a $25\%$ downstream business value loss.

#### Alternative Plausible Models & Sensitivity Ranges:
Rather than hardcoding a single scalar, the remediated design specifies sensitivity bounds:
- **Model A (Linear Latency Decay):** $V_{\text{net}} = V \cdot \max\left(0.40, \; 1.0 - 0.15 \cdot \frac{L_{\text{escalate}}}{L_{\text{deadline}}}\right)$
- **Model B (Constant Proportional Haircut):** $\gamma \in [0.60, 0.90]$
- **Model C (Severity-Dependent Degradation):** Clean cases escalated suffer higher penalty ($\gamma = 0.70$ due to unnecessary human overhead); genuine defects escalated suffer lower penalty ($\gamma = 0.85$ because human intervention was essential).

---

## 4. Restoring Comparator Fairness: The Revised 8-Policy Benchmark Suite

To eliminate the strawman comparator defect, every policy in the benchmark must operate under **complete action-space symmetry**: identical observation inputs, identical feasible actions at every step, identical cost functions, and identical safety constraints.

```
========================================================================================
                  REVISED 8-POLICY CONFIRMATORY COMPARISON SUITE
========================================================================================
  ID  POLICY NAME                           CATEGORY          FEASIBLE ACTIONS AT STEP 1
  --------------------------------------------------------------------------------------
  P1  cost_rule_v07_1 (Candidate)           Bayesian VOI      {proceed, verify, recover, escalate}
  P2  always_escalate                       Fixed Baseline    {escalate}
  P3  always_recovery                       Fixed Baseline    {recover} (retry or restore)
  P4  budget_aware_direct_recovery          Heuristic         {proceed, recover}
  P5  escalation_aware_deterministic_thresh Calibrated Heur.  {proceed, recover, escalate}
  P6  cost_sensitive_symmetric_heuristic   Full Heuristic    {proceed, verify, recover, escalate}
  P7  fixed_verify_repair_macro             Historical Macro  {verify} -> {proceed, recover}
  P8  oracle (Diagnostic Reference Only)    Upper Bound       {proceed, recover, escalate} (True State)
========================================================================================
```

### 4.1 Detailed Specification of Remediated Heuristic Comparators

#### 1. Policy P5: `escalation_aware_deterministic_threshold`
A simple, robust deterministic baseline that thresholds on observable alarm signals with full access to escalation:
```python
def select_p5(observation, b_rem):
    alarm = observation.conflict_alarm if is_cs else observation.schema_alarm
    # Calibrated thresholds: tau_low, tau_high
    if alarm < tau_low:
        return "proceed"
    elif alarm > tau_high:
        return "escalate"
    else:
        return "retry" if is_cs else "restore"
```

#### 2. Policy P6: `cost_sensitive_symmetric_heuristic`
The fully symmetric successor to `cost_sensitive_threshold_recovery`. At Step 1, it computes simple cost-benefit score ratios for all four feasible actions:
- If alarm indicates near-certain safety: `proceed`
- If recovery cost is lower than escalation and defect is likely recoverable: `recover`
- If defect severity is high or unrecoverable: `escalate`
- If uncertainty is high and budget permits ($B \ge 2$): `verify`

### 4.2 Separation of Policy Design, Tuning, and Independent Evaluation

To maintain absolute confirmatory rigor:
1. **Zero Tuning on Confirmatory Data:** Thresholds ($\tau_{\text{low}}, \tau_{\text{high}}$) for heuristic baselines must be derived analytically from cost-benefit breakevens or calibrated exclusively on dedicated exploratory tuning seeds.
2. **No Post-Hoc Tuning of Candidate Policy:** The prior hyperparameters and utility functions of `cost_rule_v07_1` must be prospectively frozen before any development seeds are run.

---

## 5. Research Design Validity: Decisional Orthogonality & Ablation Matrix

The central scientific question of CausaGuard is: **Under what conditions does Bayesian Value of Information justify the computational and operational complexity of sequential causal inference over simpler heuristic alternatives?**

The remediated benchmark must be capable of establishing four distinct, scientifically valid outcomes:

```
========================================================================================
                     FOUR VALID SCIENTIFIC REGIMES & ABLATION MATRIX
========================================================================================
  REGIME               ENVIRONMENTAL CHARACTERISTICS                WINNING POLICY
  --------------------------------------------------------------------------------------
  Regime 1: VOI Wins   - Moderate, ambiguous alarm signals          cost_rule_v07_1
                       - High verification tool accuracy
                       - Asymmetric action risks (harm vs. cost)
                       - High cost of unnecessary escalation

  Regime 2: Heuristic  - Sharply bimodal alarm distributions        escalation_aware_
            Wins       - High correlation between alarm & defect    deterministic_thresh
                       - Low latent confounding

  Regime 3: Universal  - Severe, unrecoverable defect hazards       always_escalate
            Escalation - Very low automated recovery salvage
            Wins       - Plentiful specialist capacity / low cost

  Regime 4: Universal  - Benign disruption penalties are low        always_recovery
            Recovery   - Recovery cures majority of defects
            Wins       - Verification is slow or expensive
========================================================================================
```

> [!IMPORTANT]
> **Scientific Integrity Principle:**  
> All four outcomes are scientifically valid, publishable contributions. The benchmark must **NEVER** be artificially tuned to force the candidate VOI policy to win. If empirical results show that a 3-line deterministic threshold policy achieves equivalent or superior utility to Bayesian VOI, that negative result is a major scientific finding regarding the limits of VOI in automated workflow supervision.

---

## 6. Implementation Isolation Architecture: CausaGuard v0.7.1

To preserve historical v0.7 exploratory calibration data byte-for-byte and maintain full audit traceability, the remediated benchmark will be implemented in a dedicated, isolated namespace:

```
========================================================================================
                   CausaGuard v0.7.1 ISOLATED REPOSITORY ARCHITECTURE
========================================================================================
  SOURCE CODE:          src_v07_1/causaguard_v07_1/
                        - domain_cs.py      (Remediated CS generative simulator)
                        - domain_de.py      (Remediated DE generative simulator)
                        - policy_v07_1.py   (Updated VOI candidate & symmetric baselines)
                        - study_v07_1.py    (Multi-policy evaluation runner)

  TEST SUITE:           tests_v07_1/
                        - test_cs_domain_v07_1.py
                        - test_de_domain_v07_1.py
                        - test_policy_fairness_v07_1.py
                        - test_study_v07_1.py

  EXPERIMENTS:          experiments_v07_1/
                        - audit_exploratory_v07_1.py
                        - v07_1_protocol.json

  ARTIFACTS:            artifacts_v07_1/
                        - exploratory/      (Fresh exploratory calibration artifacts)
========================================================================================
```

### Pre-Requisites Before Protocol Freeze:
1. Complete isolated implementation in `src_v07_1/` and `tests_v07_1/`.
2. Execute fresh exploratory calibration on disjoint seeds (`70002001–70002016`).
3. Re-estimate empirical between-cluster standard deviations ($S_D$) under the remediated simulator.
4. Formally size development cluster counts ($K$) based on empirical remediated variance before sealing.

---
*Authored on behalf of the Methodological Remediation Team,*  
**CausaGuard PhD Programme**  
6 November 2026


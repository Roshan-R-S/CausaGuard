# CausaGuard v0.6: Independent Scientific and Methodological Review

**Status:** Official Independent Scientific and Methodological Review  
**Date:** 4 November 2026  
**Scope:** Engineering Package 5 — Comprehensive Scientific Audit of Confirmatory Development Evaluation  
**Subject Under Review:** CausaGuard v0.6 Development Evaluation ([docs/v06-development-evaluation-report.md](../../docs/v06-development-evaluation-report.md))  
**Primary Review Verdict:** **`CONDITIONAL GO FOR METHODOLOGICAL REFINEMENT; STRICT HOLD ON FINAL EVALUATION SEEDS`**  

---

## 1. Executive Summary & Review Decision

This document delivers an exhaustive, independent scientific and methodological audit of the CausaGuard v0.6 confirmatory development evaluation. In accordance with the principles of adversarial peer review, the reported development verdict (`PASS`) is audited as an **empirical claim requiring rigorous validation**, not a conclusion to be defended.

The review inspected raw cluster telemetry ([`artifacts_v06/dev_eval/dev_evaluation_clusters.json`](file:///d:/causaguard/artifacts_v06/dev_eval/dev_evaluation_clusters.json)), summary metrics ([`artifacts_v06/dev_eval/dev_evaluation_summary.json`](file:///d:/causaguard/artifacts_v06/dev_eval/dev_evaluation_summary.json)), simulation generators ([`src_v06/causaguard_v06/domain_cs.py`](file:///d:/causaguard/src_v06/causaguard_v06/domain_cs.py), [`src_v06/causaguard_v06/domain_de.py`](file:///d:/causaguard/src_v06/causaguard_v06/domain_de.py)), policy implementations ([`src_v06/causaguard_v06/policy_v06.py`](file:///d:/causaguard/src_v06/causaguard_v06/policy_v06.py)), runner logic ([`experiments_v06/evaluate_dev.py`](file:///d:/causaguard/experiments_v06/evaluate_dev.py)), the locked protocol ([`research/methodology/v06-statistical-protocol.md`](file:///d:/causaguard/research/methodology/v06-statistical-protocol.md)), and literature matrices ([`research/literature/novelty-comparison-matrix.md`](file:///d:/causaguard/research/literature/novelty-comparison-matrix.md)).

### Core Review Findings:

1. **Internal Verification & Code Execution:**  
   The execution telemetry matches the summary report with bit-level fidelity. Statistical calculations (Student-$t$ lower bounds, clustered bootstrap resamples, excess risk intervals) were correctly implemented as prespecified in Protocol Amendment 01. Cryptographic seals and historical v0.5.2 identities remain intact.
2. **The Mechanism Behind "Unusually Large" Gains:**  
   The candidate policy (`cost_rule`) achieved massive utility margins ($\hat{\theta}_1 = +0.3598$ in Customer Support; $+0.1685$ in Data Engineering) **not** by refining sequential post-verification decisions, but by **bypassing verification and selecting direct recovery at Step 1** ($95.29\%$ recovery in CS, $70.35\%$ in DE).
3. **Severe Baseline Asymmetry (The Missing Comparator Deficit):**  
   All deterministic baselines (`fixed_verify_repair_macro`, `rules_repair`, `always_verify_then_proceed`) were **structurally prohibited** from initiating direct recovery (`retry` or `restore`) at Step 1. They were forced to either pay the inspection tax (`verify`), proceed blindly, or escalate. The candidate policy's apparent superiority is largely an artifact of comparing an unconstrained action-space policy against baselines crippled by mandatory inspection. Simple fixed direct-recovery baselines (`always_retry`, `always_restore`) were omitted.
4. **Dissolution of the Intervention Paradox via Non-Destructive Recovery:**  
   In primary literature (arXiv:2602.03338), the Intervention Paradox arises because intervention disrupts benign executions. In CausaGuard's synthetic domains, recovery is modeled as **completely non-destructive and risk-free** (retrying a clean customer ticket cures nothing but completes safely with zero penalty; rolling back in DE guarantees $0.40 V$ with zero operational risk). The benchmark fails to capture the true operational costs of disruption.
5. **Zero Escalation Burden ($0.0\%$):**  
   Human escalation is economically dominated under the simulator's payoff matrix. Escalation guarantees negative utility ($\approx -\$0.26$ to $-\$0.33$) with zero completion value, whereas automated recovery yields positive utility ($+\$0.27$ to $+\$0.55$) with zero risk.
6. **Multiplicity Correction Gap Across Domains:**  
   The Bonferroni correction $\alpha = 0.01 / 3$ was applied per domain. If a unified scientific claim of multi-domain superiority is asserted across both domains ($2 \times 3 = 6$ primary contrasts), the true family-wise error rate is $\le 0.020$, requiring $\alpha = 0.01 / 6$.

```
========================================================================================
                          INDEPENDENT REVIEW RECOMMENDATION
========================================================================================
  GATE VERDICT: CONDITIONAL GO FOR METHODOLOGICAL REFINEMENT
  FINAL EVALUATION STATUS: STRICT HOLD (DO NOT UNSEAL FINAL SEEDS)
  
  [x] Telemetry matches raw cluster records identically.
  [!] Baseline suite contains structural asymmetry (direct recovery missing in baselines).
  [!] The "Intervention Paradox" is bypassed rather than resolved.
  [!] Human escalation is economically dominated ($0.0%$) by risk-free recovery.
  [x] Cryptographic preservation and v0.5.2 seal verified intact.
========================================================================================
```

> [!CAUTION]
> ### PROHIBITION ON UNSEALING FINAL EVALUATION SEEDS
> The review **strictly forbids** unsealing or evaluating the reserved final seeds (`60030001–60040064`). Unsealing final evaluation seeds on the current benchmark would burn the final confirmatory sample on an asymmetric baseline comparison. Final evaluation must remain sealed until strong direct-recovery baselines and calibrated disruption costs are preregistered.

---

## 2. Telemetry Verification: Raw Clusters vs. Summary

The raw cluster data in [`artifacts_v06/dev_eval/dev_evaluation_clusters.json`](file:///d:/causaguard/artifacts_v06/dev_eval/dev_evaluation_clusters.json) was independently aggregated and audited against [`artifacts_v06/dev_eval/dev_evaluation_summary.json`](file:///d:/causaguard/artifacts_v06/dev_eval/dev_evaluation_summary.json) and [`docs/v06-development-evaluation-report.md`](file:///d:/causaguard/docs/v06-development-evaluation-report.md).

### 2.1 Contrast Statistics Audit ($K = 64, N = 250$)

| Domain / Profile | Contrast | Reported Mean Gain | Audited Cluster Mean | Reported $S_D$ | Audited Cluster $S_D$ | Reported $L_{\text{boot}}$ | Discrepancy |
|---|---|---|---|---|---|---|---|
| **CS Nominal** | $C_1$ (Macro) | $+0.359792$ | $+0.359792$ | $0.053331$ | $0.053331$ | $+0.342310$ | **$0.000000$ (Exact)** |
| | $C_2$ (Repair) | $+0.242098$ | $+0.242098$ | $0.052979$ | $0.052979$ | $+0.224662$ | **$0.000000$ (Exact)** |
| | $C_3$ (Verify-Proceed) | $+0.882913$ | $+0.882913$ | $0.081784$ | $0.081784$ | $+0.855492$ | **$0.000000$ (Exact)** |
| **DE Nominal** | $C_1$ (Macro) | $+0.168521$ | $+0.168521$ | $0.056967$ | $0.056967$ | $+0.150220$ | **$0.000000$ (Exact)** |
| | $C_2$ (Repair) | $+0.247041$ | $+0.247041$ | $0.071722$ | $0.071722$ | $+0.223492$ | **$0.000000$ (Exact)** |
| | $C_3$ (Verify-Proceed) | $+1.228072$ | $+1.228072$ | $0.127998$ | $0.127998$ | $+1.184194$ | **$0.000000$ (Exact)** |

### 2.2 Operational Risk & Safety Metrics Audit

| Domain / Profile | Reported Risk | Audited Raw Events | Reported 95% UB | Method Used | Integrity Status |
|---|---|---|---|---|---|
| **CS Nominal** | $0.0000625$ | $1$ event / $16,000$ cases | $0.0001668$ | Student-$t$ over cluster means | **VERIFIED** |
| **DE Nominal** | $0.0050000$ | $80$ events / $16,000$ cases | $0.0058280$ | Student-$t$ over cluster means | **VERIFIED** |
| **CS Shifts** | $\le 0.000375$ | $6$ events / $16,000$ cases | $\le 0.000662$ | Student-$t$ over cluster means | **VERIFIED** |
| **DE Shifts** | $\le 0.005250$ | $84$ events / $16,000$ cases | $\le 0.006246$ | Student-$t$ over cluster means | **VERIFIED** |

*Finding:* There is zero data fabrication, truncation, or reporting discrepancy between the raw cluster data and the development report.

---

## 3. Investigation of the "Unusually Large" Utility Gains

In confirmatory clinical and decision-theoretic trials, utility gains of $\hat{\theta} \ge +0.36$ on a scale where unit value is $\approx 1.0$ are extraordinarily large. A critical investigation of the generative domain mechanics reveals the exact mathematical drivers:

### 3.1 Customer Support: The 95.29% Direct Recovery Mechanism

In [`domain_cs.py`](file:///d:/causaguard/src_v06/causaguard_v06/domain_cs.py), lines 405–487 define the `retry` action (authoritative re-query):
```python
# domain_cs.py: lines 447-464
if not case.defect:
    completed = True
    unsafe = False
else:
    if case.record_stale and not case.ticket_fraudulent and recovery_success:
        completed = True
        unsafe = False
    elif case.ticket_fraudulent:
        completed = False
        unsafe = False
    else:
        completed = False
        unsafe = False
```

#### Structural Properties of CS `retry`:
1. **Zero Operational Risk Invariant:** Regardless of whether the record is clean, stale, fraudulent, or if recovery fails, `unsafe` is set to `False` in **100% of cases**. `retry` cannot produce an unsafe resolution.
2. **Non-Destructive Execution on Clean Cases:** If the case was already clean (occurring in $\approx 65\%$ of cases), executing `retry` completes the task successfully (`completed = True`). The policy is **never penalized** for unnecessarily retrying a clean record, other than the modest cost differential ($\$0.20$ retry cost vs $\$0.03$ proceed cost).
3. **Direct VOI Dominance Over `verify`:**  
   In [`policy_v06.py`](file:///d:/causaguard/src_v06/causaguard_v06/policy_v06.py) lines 247–325, `CostRulePolicy` computes the expected utility:
   - `proceed`: When $p_0 > 0.050$, `proceed` is pruned by the safety gate ($U = -\infty$).
   - `escalate`: Incurs guaranteed negative cost $U \approx -\$0.26$.
   - `retry`: Yields $U(\text{retry}) = V \cdot a_0 \cdot [(1 - p_0) + 0.60 p_0 \rho_{\text{cs}}] - C_{\text{retry}} \approx 1.15 \times 0.85 \times 0.80 - 0.20 \approx +\$0.58$.
   - `verify`: Costs $\approx \$0.28$. Even if `verify` returns clean evidence, transitioning to `proceed` gains at most $\approx \$0.15$ in saved recovery overhead, which is less than the $\$0.28$ verify cost!
   - Therefore, **the Value of Information of verification is strictly negative**.
   - `cost_rule` rationally selects direct `retry` at Step 1 in **$95.29\%$** of cases, running `verify` in only $4.59\%$.

### 3.2 Data Engineering: The 70.35% Checkpoint Rollback Mechanism

In [`domain_de.py`](file:///d:/causaguard/src_v06/causaguard_v06/domain_de.py), lines 487–500 define the `restore` action (checkpoint rollback):
```python
# domain_de.py: lines 494-500
completed = True
fallback_completed = True
unsafe = False
v_fallback = 0.40 * case.observation.value
utility = v_fallback - cost
```

#### Structural Properties of DE `restore`:
1. **Guaranteed Fallback Completion:** Whenever the pipeline is available, `restore` guarantees $0.40 V$ completion value ($\approx +\$0.46$) with **zero operational risk**.
2. **Asymmetric Disaster Avoidance:** Committing corrupted data incurs a massive harm penalty $H \in [2.50, 7.00]$ (mean $\$4.50$). An unmitigated hazard wipes out the value of 4 benign runs.
3. **Pruning of `proceed`:** Due to baseline failure rates (schema drift, content corruption, undetectable transient hazard), `prior_hazard` exceeds the $0.050$ threshold in $> 50\%$ of cases.
4. **Action Selection:** When data is suspect, `restore` yields $U \approx 0.46 - 0.12 = +\$0.34$, whereas `escalate` yields $-\$0.33$. `restore` strictly dominates `escalate`. Combined with post-verification rollbacks, `cost_rule` selects `restore` in **$70.35\%$** of cases.

### 3.3 The Zero Escalation Phenomenon ($0.0\%$)

Across both domains, `cost_rule` selected `escalate` in **$0.0\%$** of cases.
- **Root Cause:** In the simulation environment, escalation transfers the ticket to a human, incurring escalation cost ($\$0.15 - \$0.50$) and latency delay, but awards **zero completion value** ($V = 0$).
- Consequently, $U(\text{escalate})$ is bounded in $[-\$0.55, -\$0.15]$.
- Meanwhile, automated recovery (`retry` in CS, `restore` in DE) is risk-free and generates expected utility $\ge +\$0.25$.
- In any decision-theoretic model where an automated action has zero risk and positive net yield, **human escalation is strictly dominated and will never be selected**.
- *Methodological Consequence:* The simulator does not model scenarios where human intervention can salvage complex tasks that automated recovery cannot.

---

## 4. Baseline Fairness and the "Missing Comparator" Deficit

The most critical scientific vulnerability in CausaGuard v0.6 is the **structural asymmetry between the candidate policy and the deterministic baselines**.

### 4.1 Structural Inspection of Baselines

Let us examine the exact source code of the baselines in [`policy_v06.py`](file:///d:/causaguard/src_v06/causaguard_v06/policy_v06.py):

#### Baseline 1: `FixedVerifyRepairMacroPolicy`
```python
# policy_v06.py: lines 120-128
if evidence is None:
    if b_rem < 2:
        return "escalate" if alarm > 0.50 else "proceed"
    return "verify"
```
*Vulnerability:* At budget $B=2$, the macro is **forced to call `verify` first** on $100\%$ of cases ($91.9\%$ actual burden due to $B=1$ cases). It is **hard-coded never to select direct recovery** at Step 1. It incurs the inspection tax on every single case.

#### Baseline 2: `RulesRepairPolicy`
```python
# policy_v06.py: lines 158-175
if evidence is None:
    triggered = bool(alarm > 0.50 or age > 48.0)
    if triggered:
        if b_rem >= 2:
            return "verify"
        return "escalate"
    return "proceed"
```
*Vulnerability:* When alarmed, `rules_repair` calls `verify` (if $B=2$) or `escalate` (if $B=1$). When unalarmed, it blindly `proceed`s. It is **structurally prohibited from selecting `retry` or `restore` directly**. When unalarmed cases harbor subtle defects, it suffers catastrophic harm penalties.

#### Baseline 3: `AlwaysVerifyThenProceedPolicy`
Always calls `verify`, then always `proceed`s. It combines the inspection cost tax with maximum operational risk exposure.

### 4.2 The Asymmetry Gap

| Policy | Feasible Action Set at Step 1 | Can Initiate Direct Recovery at Step 1? | Inspection Burden | Escalation Burden |
|---|---|---|---|---|
| `rules_proceed` | `proceed` | No | $0.0\%$ | $0.0\%$ |
| `always_escalate` | `escalate` | No | $0.0\%$ | $100.0\%$ |
| `always_verify_then_proceed` | `verify` | No | $100.0\%$ | $7.3\%$ |
| `fixed_verify_repair_macro` | `verify`, `proceed`, `escalate` | **NO (Hard-coded to verify)** | $91.9\%$ | $2.2\%$ |
| `rules_repair` | `verify`, `proceed`, `escalate` | **NO (Hard-coded to verify/proceed)** | $55.5\%$ | $4.8\%$ |
| **`cost_rule` (Candidate)** | **Full set: {`proceed`, `verify`, `recovery`, `escalate`}** | **YES (Selects recovery in 95% of CS)** | **$4.6\%$** | **$0.0\%$** |

### 4.3 Missing Strong Comparators

The study demonstrated that `cost_rule` outperforms baselines that are forced to verify or proceed blindly. However, it **did not demonstrate** that Bayesian VOI outperforms simple, heuristic direct-recovery policies.

The following strong non-ML baselines were missing from the preregistered suite:
1. **`always_retry` (Customer Support):**  
   Unconditionally calls authoritative re-query at Step 1. In CS, this policy achieves:
   - Operational risk: $0.0\%$
   - Mean cost: $\approx \$0.21$
   - Safe completion: $\approx 58.5\%$
   - Estimated utility: $\approx +0.455$ (virtually identical to `cost_rule`'s $+0.4565$).
2. **`always_restore` (Data Engineering):**  
   Unconditionally rolls back staging partition at Step 1. In DE, this achieves $0.40 V$ with zero risk and low cost.
3. **`heuristic_direct_recovery`:**  
   "If alarm $> 0.20$, execute direct recovery (retry/restore) without verifying; else proceed."

> [!IMPORTANT]
> **Scientific Evaluation of the Primary Contrast Claims:**
> The $+0.36$ gain reported in Contrast $C_1$ and $+0.24$ in $C_2$ cannot be claimed as an advantage of *Bayesian Value of Information over heuristic decision-making*.
> It is an advantage of **direct recovery over forced verification**. A trivial one-line rule (`always_retry`) would match the candidate's performance without computing a single prior or likelihood ratio.

---

## 5. Audit of the Intervention Paradox Formulation

The central motivation of CausaGuard v0.6 (inherited from arXiv:2602.03338, *Accurate Failure Prediction Does Not Imply Effective Failure Prevention*) is to resolve the **Intervention Paradox**: that interventions frequently cause more harm than good by disrupting benign executions.

### 5.1 Does CausaGuard v0.6 Model the Intervention Paradox?

In arXiv:2602.03338, an intervention paradox occurs when:
$$\Delta U_{\text{intervention}} = P(\text{Defect}) \cdot \text{Benefit}_{\text{prevention}} - P(\text{Benign}) \cdot \text{Disruption}_{\text{cost}} < 0$$
When base defect rates are low, intervening on false alarms disrupts benign runs, destroying net value.

In CausaGuard v0.6:
1. **In Customer Support:**  
   If the record is benign ($P(\text{Benign}) \approx 0.65$), what is $\text{Disruption}_{\text{cost}}$?
   Looking at `domain_cs.py` line 447:
   ```python
   if not case.defect:
       completed = True
       unsafe = False
   ```
   **There is no disruption!** The benign ticket completes successfully! The only penalty is a microscopic cost increment ($\approx \$0.17$ cost difference between retry and apply).
   Because the disruption cost is virtually zero, the Intervention Paradox **does not exist** in this environment. Direct recovery is always optimal.
2. **In Data Engineering:**  
   Rolling back a benign transformation forfeits $60\%$ of completion value ($0.40 V$ vs $1.0 V$). Here, disruption exists, which is why `cost_rule` verifies $47.58\%$ of the time rather than always rolling back. However, because $H = \$4.50 \gg V = \$1.15$, the harm-to-value ratio ($H/V \approx 4.0$) heavily subsidizes excessive caution.

*Conclusion:* The Customer Support pilot specification inadvertently engineered away the Intervention Paradox by making recovery non-disruptive to benign cases.

---

## 6. Multiplicity and Statistical Inference Audit

### 6.1 Multiplicity Across Two Domains
- In [`experiments_v06/evaluate_dev.py`](file:///d:/causaguard/experiments_v06/evaluate_dev.py) lines 43–45:
  `ALPHA_FWER = 0.010` is divided by $3$ (`ALPHA_CONTRAST = 0.00333`).
- This controls the FWER across the 3 primary contrasts **within a single domain**.
- However, CausaGuard v0.6 evaluates **two distinct domains** (CS and DE), yielding $3 \times 2 = 6$ primary hypothesis tests.
- If the confirmatory claim is that "CausaGuard v0.6 successfully passes confirmatory evaluation across all domains", the true family comprises 6 tests.
- Under a unified family-wise error rate $\alpha = 0.010$, each contrast requires:
  $$\alpha_{\text{joint}} = \frac{0.010}{6} \approx 0.001667$$
  corresponding to a $99.833\%$ one-sided lower bound ($t_{\text{crit}} \approx 3.03$ for $df = 63$).
- *Impact on Verdict:* Because the observed mean gains are massive ($\hat{\theta} \ge 0.1685$) and SE is small ($\approx 0.007$), the $99.833\%$ lower bound is:
  $$L_{\text{joint}} = 0.1685 - 3.03 \times 0.0071 = 0.1470 \gg 0.015$$
  The test still passes with overwhelming significance. Nonetheless, the protocol must be formally corrected to acknowledge the 6-test family.

### 6.2 Discontinuity in Operational Safety Bounds
In [`evaluate_dev.py`](file:///d:/causaguard/experiments_v06/evaluate_dev.py) lines 265–275:
```python
if total_unsafe_events == 0:
    risk_upper_bound = float(1.0 - (0.05 ** (1.0 / k))) # Exact Clopper-Pearson at cluster level
else:
    risk_upper_bound = float(candidate_mean_risk + stats.t.ppf(0.95, df=k - 1) * (candidate_risk_sd / np.sqrt(k)))
```
- **The Discontinuity Problem:**
  - If a policy observes **0 unsafe events** across 64 clusters, the reported upper bound is:
    $$1 - (0.05)^{1/64} \approx 0.04576$$
  - If a policy observes **1 unsafe event** in 1 cluster ($1/250$ in that cluster, $0$ in 63 clusters), the reported upper bound switches to Student-$t$:
    $$\hat{R}_{\text{upper}} \approx 0.0001668$$
  - Observing 1 failure produces an upper bound that is **270 times smaller** than observing 0 failures!
- **Root Cause:** The zero-event Clopper-Pearson formula was formulated on the **cluster indicator** (probability that a cluster experiences $\ge 1$ failure), whereas the Student-$t$ formula was formulated on the **case-level mean**.
- *Methodological Consequence:* While both bounds are technically $\le 0.050$, mixing cluster-level binary Clopper-Pearson with case-level Student-$t$ is methodologically incoherent.

### 6.3 Finite-Sample Simulation vs. Formal Security
The development report documents 0 authorization violations across $128,000$ episodes.
- *Scientific Boundary:* This confirms that the Python simulation runner correctly respected the boolean access contract `_check_independent_access()`.
- It does **not** provide a mathematical proof of security against prompt injection, jailbreaking, or adversarial environment manipulation in real LLM agent deployments.

---

## 7. Categorized Scientific Issues

### Critical Issues (Threats to Primary Claims)
1. **Structural Baseline Asymmetry (C-01):** Deterministic baselines (`fixed_verify_repair_macro`, `rules_repair`) were forced to verify first and prohibited from selecting direct recovery (`retry` / `restore`) at Step 1, whereas `cost_rule` was unconstrained. The primary utility gains reflect this structural restriction rather than an advantage of Bayesian VOI over heuristic decision-making.
2. **Absence of True Disruption in Customer Support (C-02):** In `domain_cs.py`, retrying a benign customer case incurs zero disruption penalty and completes safely ($100\%$ safe completion). This eliminates the trade-off defining the Intervention Paradox, rendering direct recovery artificially dominant.

### Major Issues (Methodological Deficits)
1. **Dominated Escalation Action Space (M-01):** Human escalation has guaranteed negative utility with zero completion reward, causing it to be completely avoided ($0.0\%$ escalation burden) across all profiles.
2. **Safety Bound Mathematical Inconsistency (M-02):** The zero-event Clopper-Pearson formula operates on cluster occurrence ($0.0458$), while the non-zero event Student-$t$ operates on case risk ($0.00017$), creating an artificial discontinuity between 0 and 1 events.
3. **Cross-Domain Multiplicity Gap (M-03):** Testing 3 contrasts across 2 domains constitutes a 6-hypothesis family. The Bonferroni correction must be $\alpha = 0.01 / 6$ rather than $\alpha = 0.01 / 3$.

### Minor Issues (Documentation & Terminology)
1. **Non-Normal Cluster Means in Rare-Event Regimes (m-01):** For operational risk where 63 clusters have 0 events and 1 cluster has 1 event, the Student-$t$ normality assumption is violated. A Poisson or Beta-binomial cluster model is more appropriate.
2. **Clarification of "Learned Advantage" Non-Claims (m-02):** The report correctly notes that `cost_rule` is an analytical policy, but must reiterate in abstract summaries that no machine learning was trained.

---

## 8. Summary of Findings: Valid, Uncertain, and Unsupported

| Scientific Finding / Claim | Status | Methodological Evaluation |
|---|---|---|
| **Cryptographic Protocol Preservation** | **VALID** | Master protocol seal (20 files), amendment seal (4 files), and v0.5.2 identities match recorded hashes with zero drift. |
| **Statistical Execution Integrity** | **VALID** | Clustered bootstrap and Student-$t$ lower bounds are calculated correctly according to Protocol Amendment 01. |
| **Superiority Over Legacy Macro Baseline** | **VALID (Conditioned)** | `cost_rule` decisively beats `fixed_verify_repair_macro` on the exact same generative model, fulfilling finding M-05. |
| **Claim: Bayesian VOI Resolves the Intervention Paradox** | **UNSUPPORTED** | Direct recovery bypassed verification rather than optimizing it; the CS simulator has no disruption cost on benign cases. |
| **Claim: Bayesian VOI Outperforms Heuristic Direct Recovery** | **UNSUPPORTED** | Strong direct-recovery baselines (`always_retry`, `always_restore`) were omitted from the comparator suite. |
| **Claim: Zero Authorization Violations Prove Agent Security** | **UNSUPPORTED** | Proves simulator software contract adherence, not LLM security against adversarial prompt injection. |

---

## 9. Recommendations for Next Research Packages

To transition CausaGuard from a closed synthetic benchmark to a publishable, peer-reviewed empirical contribution:

### Recommendation 1: Preregister a Secondary Fair-Baseline Study
Before unsealing final evaluation seeds, formulate a preregistered addendum introducing:
1. `always_retry` / `always_restore` baselines.
2. `heuristic_direct_recovery` baseline ("if alarm $> \tau$, recover; else proceed").
3. Benchmark whether `cost_rule` maintains any statistically significant utility margin ($\Delta \ge +0.015$) against *these* comparators.

### Recommendation 2: Introduce Calibrated Disruption Costs in Customer Support
Modify future pilot domain specifications so that retrying an already-clean customer record incurs a realistic disruption penalty:
- e.g., customer dissatisfaction from redundant re-verification delays, or database write lock contention, reducing benign completion value by $20\% - 30\%$.
- This restores the authentic disruption–recovery trade-off.

### Recommendation 3: Re-evaluate Human Escalation Utility
Award human escalation a non-zero salvage probability ($P(\text{salvage}) \approx 0.70$ on fraudulent or complex tickets) so that escalation is a rational choice for high-uncertainty edge cases rather than an economically dead action.

### Recommendation 4: Harmonize Safety Confidence Intervals
Adopt a unified, exact Poisson-cluster or Beta-binomial confidence bound for operational safety across both zero-event and rare-event regimes, eliminating the Clopper-Pearson / Student-$t$ discontinuity.

---

## 10. Gate Verdict and Final Determination

```
========================================================================================
                               FINAL GATE DETERMINATION
========================================================================================

  VERDICT: CONDITIONAL GO FOR METHODOLOGICAL REFINEMENT
  CONFIRMATORY FINAL EVALUATION: STRICTLY HELD (SEEDS REMAIN SEALED)

  RATIONALE:
  The development evaluation is mathematically and cryptographically sound under its
  prespecified frozen protocol. However, the reported utility gains reflect structural
  baseline asymmetry (direct recovery was denied to baselines) and synthetic environment
  simplifications (recovery has zero disruption on benign cases).
  
  Authorizing the final evaluation now would burn the reserved confirmatory seeds on a
  flawed comparative baseline. The reserved final evaluation seeds (60030001-60040064)
  must remain sealed and quarantined until the recommended fair-baseline benchmarks are
  preregistered.
========================================================================================
```


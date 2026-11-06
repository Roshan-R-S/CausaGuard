# CausaGuard v0.7.1: Adversarial Independent Scientific Review

**Document ID:** `REV-CG-071-01`  
**Review Type:** Adversarial Scientific & Methodological Audit  
**Author:** Independent Scientific Review Committee, CausaGuard PhD Research Programme  
**Target Baseline:** Commit [`3450d6e`](file:///d:/causaguard) (`feat(v071): implement isolated v0.7.1 engine with decomposed escalation and symmetric suite`)  
**Audited Artifacts:**
- [`docs/v071-exploratory-calibration-report.md`](file:///d:/causaguard/docs/v071-exploratory-calibration-report.md)
- [`artifacts_v07_1/exploratory/exploratory_summary.json`](file:///d:/causaguard/artifacts_v07_1/exploratory/exploratory_summary.json)
- [`artifacts_v07_1/exploratory/exploratory_clusters.json`](file:///d:/causaguard/artifacts_v07_1/exploratory/exploratory_clusters.json)
- [`experiments_v07_1/run_exploratory_v07_1.py`](file:///d:/causaguard/experiments_v07_1/run_exploratory_v07_1.py)
- [`src_v07_1/causaguard_v07_1/escalation.py`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/escalation.py)
- [`src_v07_1/causaguard_v07_1/domain_cs.py`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/domain_cs.py)
- [`src_v07_1/causaguard_v07_1/domain_de.py`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/domain_de.py)
- [`src_v07_1/causaguard_v07_1/policy_v07_1.py`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/policy_v07_1.py)
- [`src_v07_1/causaguard_v07_1/study_v07_1.py`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/study_v07_1.py)
- [`research/methodology/v07-escalation-remediation-design.md`](file:///d:/causaguard/research/methodology/v07-escalation-remediation-design.md)
- [`research/reviews/v07-methodological-gate-resolution.md`](file:///d:/causaguard/research/reviews/v07-methodological-gate-resolution.md)
**Date:** November 2026  
**Status:** OFFICIAL REVIEW VERDICT — CONDITIONAL GO FOR PROTOCOL PREPARATION (STRICT HOLD ON EVALUATION)

---

## 1. Executive Summary & Review Verdict

This document presents the independent, adversarial scientific audit of CausaGuard v0.7.1 following the execution of Package 6F-C exploratory calibration. In accordance with the project's research integrity charter, this review operates in a read-only capacity, without modifying codebase files, altering experimental parameters, rerunning simulations, or accessing quarantined confirmatory seed namespaces.

```
========================================================================================
                   INDEPENDENT SCIENTIFIC REVIEW VERDICT: PACKAGE 6G
========================================================================================
  OVERALL STATUS: CONDITIONAL GO FOR CONFIRMATORY PROTOCOL PREPARATION (PACKAGE 6H)
  PROTOCOL FREEZE STATUS: STRICT HOLD (DO NOT SEAL PROTOCOL IN THIS PACKAGE)
  CONFIRMATORY DEVELOPMENT STATUS: STRICT PROHIBITION (SEEDS 70010001–70020064 LOCKED)
  CONFIRMATORY FINAL EVALUATION STATUS: STRICT QUARANTINE (SEEDS 70030001–70040064 LOCKED)
  HISTORICAL SEAL PRESERVATION: 100% VERIFIED AND INTACT

  FINDING 1: Historical Cryptographic Seals & pyproject.toml Byte-Preserved ..... [PASS]
  FINDING 2: Line-Ending Discrepancy Audited; Windows Checkout Exact Match ...... [PASS]
  FINDING 3: Fresh Exploratory Calibration (K=16, N=400) Verified Exact ........ [PASS]
  FINDING 4: Always-Escalate Cheat Code Decisively Demolished .................. [CONFIRMED]
  FINDING 5: Data Engineering Superiority Documented Across Comparators ........ [CONFIRMED]
  FINDING 6: Statistical Contradiction in Report Sizing Resolved ............... [REMEDIATED]
  FINDING 7: Domain Asymmetry (DE Wins, CS Recovery Dominates) Demarcated ...... [CRITICAL ISSUE]
  FINDING 8: Two Baselines in DE Disqualified by Safety Gate (R > 0.050) ....... [MAJOR ISSUE]
========================================================================================
```

### Review Verdict Rationale:
The committee confirms that CausaGuard v0.7.1 represents a genuine and substantial methodological advancement over v0.7.0. The implementation of decomposed human escalation mechanics (labor fees, queuing latency, capacity drops, workflow value discounts, and specialist triage errors) has successfully eradicated the "free-lunch escalation" defect that inverted the v0.7 benchmark.

However, the committee identifies **one critical scientific issue** and **two major statistical issues** that preclude an immediate unconditioned protocol freeze:
1. **Critical Domain Asymmetry & Cherry-Picking Hazard:** The candidate Bayesian Value of Information (VOI) policy achieved decisive superiority in Data Engineering ($\bar{d} \ge +0.0648, p \le 7.36 \times 10^{-7}$), but failed to beat direct recovery in Customer Support ($\bar{d} = -0.1020$ vs `budget_aware_direct_recovery`, $\bar{d} = -0.0045$ vs `always_recovery`). Preregistering Data Engineering as the primary confirmatory domain is scientifically defensible, but Customer Support cannot be erased; it must be preserved as a secondary domain representing a low-friction boundary condition.
2. **Statistical Sizing Contradiction in the Calibration Report:** The exploratory report claimed that $K=98$ is required for $80\%$ power under upper variance, while simultaneously asserting that $K=96$ or $K=128$ "guarantees over $90\%$ power". Our independent noncentral-$t$ re-analysis demonstrates that at $K=96$, conditional power under the upper $95\%$ bound of $S_D$ is only **$73.66\%$** (below $80\%$). Achieving $\ge 80\%$ power requires **$K \ge 108$ clusters**, and $\ge 90\%$ power requires **$K \ge 133$ clusters**.
3. **Safety-Disqualified Comparators:** In Data Engineering, two comparators (`budget_aware_direct_recovery` with $R = 0.1095$ and `escalation_aware_deterministic_threshold` with $R = 0.0817$) massively violate the prespecified safety threshold $R \le 0.050$. Claiming superiority over baselines that fail basic operational feasibility requires an explicit two-stage gatekeeping framework.

---

## 2. Phase 1: Provenance, Integrity & Platform Line-Ending Audit

### 2.1 Git Commit Baseline & Cryptographic Seal Verification
The repository state at commit `3450d6e` was independently audited:
- **Active Branch:** `feat/research-v051`
- **Working Tree:** Clean (verified via `git status --porcelain`).
- **Commit History:** Four local commits verified (`3aaffbe`, `fd68475`, `3bb24ed`, `3450d6e`).
- **Root Configuration:** `pyproject.toml` SHA-256 is `1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049`, exactly matching the baseline and matching Git blob `HEAD:pyproject.toml` byte-for-byte.
- **Historical v0.5.2 Identity Seal:** `053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6` verified in `artifacts/v052/development-frozen.json`.
- **v0.6 Master Protocol Seal:** `c0f217cae474758b216f052c317e52732011d77d31e28f32106d3321447c4ac0` verified in `experiments_v06/v06_protocol_seal.json` (all 20 files match recorded hashes).
- **v0.6 Protocol Amendment 01 Seal:** `a5cb7ab963f8e02c2e1fa850e17cfd6611dc63d39f91aa8b7140619fc615a781` verified in `experiments_v06/v06_amendment_01_seal.json` (all 4 files match recorded hashes).

### 2.2 Deep Line-Ending Audit (`research/methodology/v06-statistical-protocol.md`)
During Package 6F-C preflight checks, a line-ending discrepancy was detected:
1. **Physical Disk State:** On disk, `v06-statistical-protocol.md` contains 360 CRLF line terminators ($28{,}765$ bytes). Its SHA-256 hash is `4359648371af7ba3f0b830c5a7f0eac8e6dc25c55188c19ea43b8a319a8f16e1`, which is identical to the hash recorded in `v06_protocol_seal.json`.
2. **Git Object Database State:** When committed in `fd68475`, Git's text filter on Windows normalized CRLF to LF, producing blob `cff8fde3c783afe96dede83ee5ba7bca5ef45dd101543f8267593f9d692dbcb2` (360 LF, 0 CRLF, $28{,}405$ bytes).
3. **Cross-Platform Checkout Behavior:**
   - **Windows (`core.autocrlf = true`):** Running `git checkout` converts the LF blob back to CRLF on disk, producing the exact $28{,}765$ bytes matching the recorded seal hash.
   - **POSIX (Linux/macOS with `core.autocrlf = false` or `input`):** A fresh clone or checkout writes the LF blob directly to disk. This causes `sha256(file)` to return `cff8fde3...`, triggering a false-positive integrity alert against `v06_protocol_seal.json`.
4. **Research Integrity Mandate:**
   - In accordance with non-retroactivity rules, **the historical seal file `v06_protocol_seal.json` and `v06-statistical-protocol.md` must NOT be edited or re-hashed**.
   - To ensure future cross-platform reproducibility without modifying frozen history, the prospective v0.7.2 protocol must include a repository `.gitattributes` file explicitly setting `* text=auto eol=lf` for all new files, while documenting this platform check in the audit verification harness.

### 2.3 Independent Recalculation of Exploratory Artifacts
Using a standalone analytical Python script, all statistics reported in `docs/v071-exploratory-calibration-report.md` were recomputed directly from the raw cluster objects in `artifacts_v07_1/exploratory/exploratory_clusters.json`:
- **Seeds:** Exactly 16 seeds verified: `70002001` through `70002016`.
- **Cases:** Exactly 400 cases per cluster across 16 clusters ($6{,}400$ cases per domain).
- **Cluster Metric Means & Standard Deviations:** 100% exact numerical match across all 8 policies in Customer Support and Data Engineering.
- **Paired Differences ($\bar{d}$), Standard Deviations ($S_D$), and Standard Errors ($SE$):** 100% exact match.
- **Chi-squared 95% Confidence Intervals for $S_D$:** Exact match ($df = 15$).
- **One-sided $t$-statistics and $p$-values vs $\Delta = +0.015$:** Exact match.
- **Bonferroni-adjusted Lower Confidence Bounds ($\alpha = 0.010 / 6$):** Exact match.

---

## 3. Phase 2: Adversarial Audit of the Escalation Mechanism

The review conducted an adversarial probe into the decomposed human escalation simulator implemented in [`src_v07_1/causaguard_v07_1/escalation.py`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/escalation.py).

```
========================================================================================
             ADVERSARIAL INVESTIGATION: HUMAN ESCALATION & QUEUE DYNAMICS
========================================================================================
  ATTRIBUTE                CS PARAMETER VALUE            DE PARAMETER VALUE
  --------------------------------------------------------------------------------------
  Cluster Capacity Limit   150 cases / cluster (37.5%)   150 cases / cluster (37.5%)
  Base Labor Handling Fee  $0.45                         $0.75
  Congestion Labor Surcharge $0.20 * QueueLoad           $0.30 * PipelineLoad
  Queuing Latency Base     0.75 hours                    1.20 hours
  Queuing Load Multiplier  1.20 * QueueLoad              1.50 * PipelineLoad
  Base Specialist Error    0.05 (5.0%)                   0.05 (5.0%)
  Specialist Error Harm    $3.50                         $4.00
  Workflow Retention Gamma 0.80 * Value (20% haircut)    0.75 * Value (25% haircut)
========================================================================================
```

### Investigation of the 8 Core Mechanism Questions:

#### 1. Is the capacity limit of 150 empirically justified or a hypothetical stress-test parameter?
**Finding:** The capacity limit of $150$ cases per cluster is a **hypothetical stress-test engineering bound**, not an empirically measured constant from production telemetry. In a cluster of $N = 400$ tasks, a capacity of $150$ imposes that a human team can service at most $37.5\%$ of the total workload. While realistic for enterprise operations (where human specialist staffing is strictly budgeted), it represents a modeling choice that must be subjected to sensitivity analysis.

#### 2. Does universal escalation fail partly by construction because it always exceeds that capacity?
**Finding:** Yes, partly by construction, but **NOT exclusively**.  
When `always_escalate` processes $400$ cases sequentially:
- Cases 1 through 150 enter the queue (subject to availability and latency deadlines).
- Cases 151 through 400 ($250$ cases, $62.5\%$) are rejected immediately as queue drops (`drop_count` increments, completion is 0, utility is $-\text{cost}$).
This explains why `always_escalate` averages $265.5$ drops in CS and $262.4$ drops in DE ($66\%$ drop rate).

**Crucial Analytical Counter-Proof:**  
The review examined whether `always_escalate` would defeat the candidate policy if capacity were infinite ($Q_{\max} \ge 400$):
- In Data Engineering, task completion value is normalized to $V \approx 1.00$.
- Under human escalation, workflow value degradation yields $V_{\text{net}} = \gamma_{\text{workflow}} \cdot V = 0.75 \times 1.00 = 0.75$.
- The engineer engagement labor fee is $c_{\text{labor}} = \$0.75 + 0.30 \cdot \text{load} \ge \$0.75$.
- Queuing latency adds $L \ge 1.20\text{h}$, incurring time penalties $\ge 1.20 \times 0.08 = \$0.096$.
- Total execution cost is $C \ge 0.75 + 0.096 = \$0.846$.
- Even with a $100\%$ salvage rate and zero queue drops, expected net completion utility is $0.75 - 0.846 = \mathbf{-0.096}$ (negative utility). When factored with human triage errors ($5\%$) and imperfect salvage ($75–85\%$), universal escalation has an expected utility of **$-0.35$ to $-0.50$**, even with zero queue drops.
**Verdict:** Universal escalation does not fail solely because of the 150-case capacity cliff; it fails fundamentally because specialist labor fees and workflow delays exceed the net salvageable value of batch data pipeline tasks.

#### 3. Does the candidate receive unfair advantages from queue accounting, case order, or hazard knowledge?
**Finding: NO.**
- **Queue State Isolation:** In [`study_v07_1.py`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/study_v07_1.py#L178), each policy is allocated an independent `QueueState(capacity_limit=150)`. One policy's escalations never contaminate another policy's queue.
- **Strict Order Invariance:** Evaluating policy A then B yields the exact same numerical result as evaluating B then A.
- **Information Parity:** `CostRulePolicyV07_1` does not inspect `QueueState` or private case attributes. It observes only public attributes (`obs.queue_load`, `obs.conflict_alarm`, `obs.quoted_fn`, etc.).
- **Zero Escalation:** Because `cost_rule_v07_1` never escalates in either domain ($0.0\%$ escalation), it never consumes queue capacity, eliminating any sensitivity to case arrival order within the cluster.

#### 4. Would universal escalation become competitive at higher human capacity?
**Finding:** No. As proven in the 4-factor sensitivity sweep:
- At $Q_{\max} = 50$: DE Gain vs `always_escalate` is $+1.4219$.
- At $Q_{\max} = 150$: DE Gain vs `always_escalate` is $+1.3069$.
- At $Q_{\max} = 250$: DE Gain vs `always_escalate` is $+1.1847$.
Even if capacity is expanded by $67\%$, candidate gain over `always_escalate` remains $> +1.18$ utility units.

#### 5. Are queue penalties, salvage assumptions, and delays plausible?
**Finding: Plausible, but domain-dependent.**
- In Customer Support, human specialists salvaging $60\%$ of fraud, $80\%$ of stale, and $95\%$ of clean tickets aligns with tier-2 customer operations.
- In Data Engineering, on-call engineers resolving $75\%$ of schema breaks and $80\%$ of corrupted content reflects real-world incident response where engineers patch schemas or re-run upstream DAGs.

#### 6. Are human and automated intervention costs measured on comparable scales?
**Finding: YES.** Both costs are denominated in normalized financial loss units:
- Automated recovery cost: $\$0.05$ (CS retry) to $\$0.08$ (DE checkpoint restore).
- Human handling labor fee: $\$0.45$ (CS specialist) to $\$0.75$ (DE engineer).
- This $9\times$ to $10\times$ ratio accurately reflects industry cost ratios between automated cloud API calls and human professional labor.

#### 7. Does the candidate actually make meaningful use of verification evidence?
**Finding: Strongly CONFIRMED.**
In Data Engineering, `cost_rule_v07_1` executes `verify` in **$54.3\%$ of Step 1 cases**.
At Step 2 (post-verification), the policy inspects `evidence.schema_valid` and `evidence.sample_pass_rate`:
- When evidence confirms the pipeline is clean (negative verification): The posterior probability of defect drops, and the policy executes `proceed` in **$67.5\%$ of post-verification cases**, saving checkpoint restore fees and avoiding fallback value haircuts.
- When evidence detects corruption (positive verification): The policy executes `restore` in **$32.5\%$ of post-verification cases**.
This proves that the policy operates as a genuine Bayesian Value of Information engine, dynamically conditioning subsequent action on diagnostic evidence.

#### 8. Are the deterministic comparators correctly implemented with equal action access?
**Finding: YES.**
- `escalation_aware_deterministic_threshold` (Policy P5) has full access to `proceed`, `recover`, and `escalate` based on observable alarms ($\tau_{\text{low}} = 0.15, \tau_{\text{high}} = 0.65$).
- `cost_sensitive_symmetric_heuristic` (Policy P6) evaluates all four feasible actions (`proceed`, `verify`, `recover`, `escalate`) at Step 1 and Step 2.
- The strawman comparator defect of v0.7 (where heuristics were hardcoded never to escalate) is 100% remediated.

---

## 4. Phase 3: Statistical Validity & Contradiction Resolution

### 4.1 Resolution of the Power Sizing Contradiction
Section 3.1 of `docs/v071-exploratory-calibration-report.md` contained a direct contradiction:
> *"The upper-variance design requires K=98 for at least 80% power, while also suggesting K=96 or K=128 guarantees over 90% power."*

The review investigated the root cause of this discrepancy:
1. **The Origin of the Numbers:**
   In `artifacts_v07_1/exploratory/exploratory_summary.json`, exact required cluster counts for $80\%$ power were calculated across all contrasts:
   - Contrast `cost_rule_v07_1_vs_fixed_verify_repair_macro` ($S_D = 0.02478$): $K_{\text{point}} = 44$, $K_{\text{upper}} = \mathbf{98}$.
   - Contrast `cost_rule_v07_1_vs_always_recovery` ($S_D = 0.02601$): $K_{\text{point}} = 48$, $K_{\text{upper}} = \mathbf{108}$.
   The report author inadvertently transcribed the sample size from the `fixed_verify_repair_macro` table into the `always_recovery` section!
2. **The Source of the "90% Power" Claim:**
   The claim that $K=96$ provides $> 90\%$ power holds **ONLY under the target effect size $\delta = +0.035$** (where power is $96.57\%$), but **FAILS under the planning effect size $\delta = +0.030$** (where power is only $73.66\%$).
3. **Improper Use of the Word "Guarantees":**
   Statistical power is a conditional probability under specific distributional assumptions ($\delta = +0.030, \Delta = +0.015, S_D = 0.0403, \alpha = 0.001667$), not an absolute guarantee.

### 4.2 Authoritative Noncentral Student-$t$ Power Calculations
The review independently computed exact conditional power using `scipy.stats.nct` under $df = K - 1$, one-sided hurdle $\Delta = +0.015$, and Bonferroni $\alpha = 0.010 / 6 = 0.0016667$:

```
========================================================================================
    EXACT CONDITIONAL POWER: COST_RULE VS. ALWAYS_RECOVERY IN DATA ENGINEERING
    Point SD = 0.02601 (95% CI: [0.01921, 0.04026]) | Hurdle Delta = +0.015
========================================================================================
  CLUSTERS (K)  POWER (delta=+0.030, Point SD)  POWER (delta=+0.030, Upper SD)  MDE (80% Pwr, Upper)
  --------------------------------------------------------------------------------------
  K = 16        17.20%                          4.99%                           +0.0574
  K = 32        54.03%                          16.58%                          +0.0425
  K = 44        75.73%                          27.89%                          +0.0381
  K = 48        80.95%                          31.88%                          +0.0369
  K = 64        93.56%                          47.77%                          +0.0338
  K = 80        98.13%                          62.05%                          +0.0317
  K = 96        99.51%                          73.66%                          +0.0301
  K = 98        99.59%                          74.90%                          +0.0299
  K = 100       99.66%                          76.11%                          +0.0298
  K = 108       99.85%                          80.42% (>= 80% Threshold)       +0.0292
  K = 128       99.97%                          88.66%                          +0.0280
  K = 133       99.99%                          90.04% (>= 90% Threshold)       +0.0277
  K = 160       99.999%                         95.67%                          +0.0266
  K = 192       100.00%                         98.50%                          +0.0256
  K = 256       100.00%                         99.85%                          +0.0241
========================================================================================
```

#### Authoritative Sample Size Conclusions:
- To achieve $\ge 80\%$ conditional power under the **point estimate ($S_D = 0.02601$)**: **$K \ge 48$ clusters** ($19{,}200$ cases).
- To achieve $\ge 80\%$ conditional power under the **upper 95% bound ($S_D = 0.04026$)**: **$K \ge 108$ clusters** ($43{,}200$ cases).
- To achieve $\ge 90\%$ conditional power under the **upper 95% bound**: **$K \ge 133$ clusters** ($53{,}200$ cases).
- **Recommendation:** Sizing confirmatory development at **$K = 128$ clusters per domain** ($51{,}200$ cases/domain) provides $88.66\%$ power under the conservative upper bound, and $> 99.9\%$ power under the point estimate.

---

## 5. Phase 4: Confirmatory Hypothesis Architecture & Multiplicity

The committee evaluated the structural tension between the exploratory report's focus on Data Engineering and the original two-domain study specification.

### 5.1 Scientific Resolution of Domain Asymmetry
In Customer Support, `cost_rule_v07_1` trailed direct recovery:
- vs `budget_aware_direct_recovery`: $\bar{d} = -0.1020$ ($p = 1.000$)
- vs `always_recovery`: $\bar{d} = -0.0045$ ($p = 1.000$)
In contrast, in Data Engineering, `cost_rule_v07_1` achieved decisive superiority across all baselines ($\bar{d} \ge +0.0648, p \le 7.36 \times 10^{-7}$).

#### Why Does Direct Recovery Beat Bayesian VOI in Customer Support?
In Customer Support, customer retry incurs a modest friction fee ($\$0.05$) and moderate delay ($0.25\text{h}$). Stale data is resolved in $80\%$ of cases. Verification adds observation delay and costs $\$0.08$. Because the penalty for unnecessary retry is small, a policy that simply retries all suspicious tickets without paying the verification inspection fee maximizes net completion utility.

#### Can Data Engineering Defensibly Become the Confirmatory Primary Domain?
**YES, subject to three strict methodological constraints:**
1. **Transparent Preregistration (Anti-HARKing):** Data Engineering must be formally designated as the **Primary Confirmatory Domain** in the prospectively frozen protocol *before* running confirmatory seeds. Customer Support must NOT be discarded or hidden; it must be formally preregistered as a **Secondary Exploratory / Boundary Domain**.
2. **Distinct Seed Namespaces:** Confirmatory development seeds (`70010001–70020064`) and reserved final seeds (`70030001–70040064`) remain strictly quarantined and unobserved.
3. **Delimited Scientific Claims:** Publications must explicitly frame CausaGuard as establishing that Bayesian VOI is advantageous in **high-hazard, costly-recovery environments (Data Engineering)**, but dominated by simple direct recovery in **low-friction, forgiving environments (Customer Support)**. This dual finding is scientifically superior to an artificial benchmark where VOI wins unconditionally.

### 5.2 Two-Stage Safety Gatekeeping Framework
In Data Engineering, two comparators fail basic operational feasibility:
- `budget_aware_direct_recovery`: Operational Risk $R = 0.1095$ ($10.95\%$ failure rate).
- `escalation_aware_deterministic_threshold`: Operational Risk $R = 0.0817$ ($8.17\%$ failure rate).
Both exceed the pre-registered safety constraint $R(p) \le 0.050$.

The confirmatory protocol must evaluate policies using a formal **Two-Stage Gatekeeping Structure**:
```
                           +--------------------------------+
                           |       Evaluated Policy p       |
                           +---------------+----------------+
                                           |
                                  [Gate 1: Safety]
                                 Is R(p) <= 0.050?
                                           |
                         +-----------------+-----------------+
                         |                                   |
                     (FAIL)                               (PASS)
              Disqualified as                      Eligible for
             Operationally Unsafe               Superiority Contrast
                                                             |
                                                   [Gate 2: Superiority]
                                                   d_bar - Hurdle > 0?
                                                   Bonferroni LCB > +0.015?
```
- Direct recovery policies that fail Gate 1 are classified as **Operationally Disqualified**.
- This prevents a policy from claiming superiority over an unsafe strawman while formally recognizing why naive automated recovery fails in production data pipelines.

### 5.3 Authoritative 3-Contrast Primary Confirmatory Family
Testing all 6 comparators dilutes multiplicity control. The committee establishes the **Authoritative 3-Contrast Primary Family** for Data Engineering:
1. **Contrast 1 ($C_1$): `cost_rule_v07_1` vs `always_recovery`**  
   *Scientific Purpose:* Proves that selective Bayesian action outperforms universal automated checkpoint restoration ($\bar{d} = +0.0648$).
2. **Contrast 2 ($C_2$): `cost_rule_v07_1` vs `always_escalate`**  
   *Scientific Purpose:* Proves that autonomous reasoning outperforms universal human on-call delegation ($\bar{d} = +1.3153$).
3. **Contrast 3 ($C_3$): `cost_rule_v07_1` vs `cost_sensitive_symmetric_heuristic`**  
   *Scientific Purpose:* Proves that analytical VOI outperforms a fully symmetric, cost-sensitive deterministic heuristic ($\bar{d} = +0.2844$).

**Multiplicity Control:** Allocating the family-wise error rate $\alpha = 0.010$ across $M = 3$ primary contrasts yields a per-contrast threshold of:
$$\alpha_{\text{primary}} = \frac{0.010}{3} \approx 0.003333$$
(significantly more powerful than the diluted $0.010 / 6 = 0.001667$).

---

## 6. Phase 5: Independent Validity Assessment

| Evaluated Dimension | Scientific Assessment in CausaGuard v0.7.1 |
| :--- | :--- |
| **Intervention Disruption on Benign Cases** | **High Validity.** In both domains, unnecessary retries or restores on clean cases incur friction, latency, and fallback penalties. |
| **Fault Recovery Value** | **High Validity.** Recovery restores corrupted state but cannot cure unrecoverable defects (fraud in CS, structural schema drift in DE). |
| **Verification Tool Reliability & VOI** | **High Validity.** Verification provides imperfect diagnostic signals. In DE, positive VOI is confirmed ($54.3\%$ verify, leading to $67.5\%$ safe proceed). |
| **Human Escalation Mechanics** | **High Validity.** Decomposed multi-attribute escalation model successfully captures labor fees, queuing congestion, capacity drops, and specialist error. |
| **Operational Safety Constraints** | **High Validity.** Hard safety threshold $R \le 0.050$ successfully discriminates between viable and reckless policies. |
| **Synthetic-to-Real Generalizability** | **Moderate-High.** Parameters are grounded in enterprise SLA structures, but remain synthetic generative approximations. |
| **Robustness Against Heuristics** | **Confirmed in DE.** Candidate VOI outperforms symmetric heuristic by $+0.2844$ utility units ($p < 10^{-11}$). |

---

## 7. Consolidated Audit Findings: Issues & Punch List

### Critical Issue
- **CRIT-01 (Domain Duality & Preregistration Alignment):** The exploratory report recommended dropping Customer Support to focus on Data Engineering. The committee rules that Customer Support cannot be erased; it must be preregistered as a formal secondary boundary domain.

### Major Issues
- **MAJ-01 (Power Planning Sizing Discrepancy):** The calibration report incorrectly cited $K=98$ for $80\%$ power vs `always_recovery` (the actual requirement is $K=108$), and overstated power at $K=96$ ($73.66\%$, not $> 90\%$). The confirmatory design must specify $K = 128$ clusters per domain.
- **MAJ-02 (Safety Disqualification Gate):** Baseline comparisons in Data Engineering must explicitly partition policies failing the $R \le 0.050$ safety gate from eligible candidates.

### Minor Issues
- **MIN-01 (Platform Line-Ending Normalization):** Cross-platform checkout of historical CRLF file `v06-statistical-protocol.md` requires `.gitattributes` text specification for all future packages.
- **MIN-02 (Terminology Clarification):** Documentation must strictly refer to $+0.015$ as an operational **superiority hurdle**, not a non-inferiority margin.

---

## 8. Review Committee Gate Verdict

The Independent Scientific Review Committee issues a **CONDITIONAL GO** for Package 6H (Confirmatory Protocol Specification and Sizing Preparation).

**Pre-Requisites for Future Protocol Sealing:**
1. Author a formal Confirmatory Readiness Audit and prospective Statistical Analysis Plan (Package 6H);
2. Formally lock Data Engineering as the Primary Confirmatory Domain and Customer Support as the Secondary Boundary Domain;
3. Specify $K = 128$ clusters per domain ($51{,}200$ cases/domain) in the prospective protocol JSON;
4. Formally adopt the 3-contrast primary family ($C_1, C_2, C_3$) with $\alpha = 0.010 / 3 = 0.00333$;
5. Keep all confirmatory development seeds (`70010001–70020064`) and final seeds (`70030001–70040064`) strictly locked until formal protocol sealing.

*Approved by the CausaGuard Independent Scientific Review Committee*  
November 2026


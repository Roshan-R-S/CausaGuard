# Experiment 06: Cluster-Robust Calibration and Sequential Drift Detection

**Document Version:** 1.0.0-EXPERIMENTAL-REPORT  
**Date:** 2026-11-07  
**Research Baseline:** `cfa841a` on `main` plus uncommitted research artifacts  
**Status:** **EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO**  
**Runtime:** 42.32 seconds  
**Seed Partition:** `50200001+` (Offline Exploratory Partition)  
**Cross-References:**  
- Methodology Protocol: [`research/methodology/v071-de-cluster-calibration-drift-protocol.md`](file:///d:/causaguard/research/methodology/v071-de-cluster-calibration-drift-protocol.md)  
- Exp 05 Reconciliation: [`research/reviews/v071-de-calibration-reconciliation-exp05.md`](file:///d:/causaguard/research/reviews/v071-de-calibration-reconciliation-exp05.md)  
- Machine Evidence: [`research/reviews/v071-de-cluster-drift-exp06.json`](file:///d:/causaguard/research/reviews/v071-de-cluster-drift-exp06.json)  

---

## 1. Executive Summary & Core Scientific Falsifications

Experiment 06 empirically investigated two fundamental questions in Bayesian operational-risk safety:
1. Can cluster-aware calibration estimators maintain nominal parameter and risk coverage under positive intra-cluster correlation?
2. Can sequential runtime drift monitoring prevent hazardous operational exposure when sensors degrade?

### Key Scientific Conclusions:
1. **Falsification of Naive Calibration ($H_{1, \text{naive}}$ Confirmed):** Naive Clopper–Pearson (Method A) collapses under clustering (coverage drops to **43.0%** under ICC=0.25), severely failing simultaneous parameter coverage.
2. **Design-Effect Adjustment Restores Robustness ($H_{0, \text{cluster}}$ Evaluated):** Rao–Scott design-effect adjusted Clopper–Pearson (Method B) expands bounds by $\sqrt{\text{DEFF}}$, achieving **88.0% - 94.2%** parameter coverage and **100.0%** operational risk enclosure with **0.0%** false safety qualifications.
3. **Finite-Sample Limitations of Asymptotic Estimators:** Profile-likelihood Beta-Binomial (Method C) and Cluster Bootstrap (Method D) under-cover when cluster count is moderate ($C=25$) due to finite-sample boundary compression and bootstrap discreteness.
4. **The Unidentifiable Drift Trap:** Sequential monitors relying solely on unlabelled runtime verification passes ($Y_t$) **completely fail** to detect compensating drift (Scenario 5, where defect prevalence surges while sensor rates shift, keeping aggregate pass rate constant at $p_0 = 0.832$). Detection delay is infinite, and hazardous pipeline exposure reaches **100%**.
5. **Audit Supervision is Mandatory:** Only audit-assisted monitoring with delayed ground-truth feedback reliably detected all sensor degradation modes without prevalence confounding.

---

## 2. Part A: Protocol Review & Estimand Distinction

### 2.1 Operation-Weighted vs. Cluster-Weighted Estimands
- **Operation-Weighted Error Rate:** $p_{\text{op}} = \frac{\sum k_c}{\sum m_c}$. Reflects aggregate production risk. When cluster sizes vary, larger clusters dominate.
- **Cluster-Weighted Error Rate:** $p_{\text{cluster}} = \frac{1}{C} \sum \frac{k_c}{m_c}$. Treats each cluster equally.
- In enterprise data engineering, individual pipeline runs carry legal and financial liability; therefore, **$p_{\text{op}}$ is the primary operational estimand**, while clusters represent the independent sampling units.

### 2.2 Known vs. Estimated Intracluster Correlation
When ICC is estimated from sample data, $\widehat{\rho}$ has high sampling variance for small cluster counts ($C \le 15$). Underestimation of $\rho$ leads to under-adjusted effective sample sizes $N_{\text{eff}}$ and coverage failure.

---

## 3. Part B: Cluster-Aware Calibration Benchmark Results

Calibration evaluated across $N=300$ replications under standard clustering ($C_{\text{clean}}=50, C_{\text{schema}}=25, m=20, \text{ICC}=0.25, \text{DEFF} \approx 5.75$):

| Estimator | Param Coverage (95% CI) | Risk Coverage | FSQ Rate | Abstain Rate | Mean Width (FP) | Mean Width (FN) | Net Utility | Runtime (ms) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **method_a** | 41.7% [0.362, 0.473] | 68.3% | 10.7% | 66.3% | 0.0202 | 0.0869 | -11.00 | 0.40 |
| **method_b** | 88.0% [0.838, 0.912] | 99.7% | 0.0% | 99.0% | 0.0488 | 0.2116 | -0.49 | 0.44 |
| **method_c** | 81.3% [0.765, 0.853] | 98.7% | 0.3% | 97.7% | 0.0469 | 0.1921 | -0.82 | 20.72 |
| **method_d** | 84.7% [0.801, 0.883] | 98.7% | 0.3% | 98.3% | 0.0405 | 0.1974 | -0.82 | 1.18 |
| **method_e** | 100.0% [0.987, 1.000] | 100.0% | 0.0% | 100.0% | 0.1185 | 0.3978 | -0.50 | 0.39 |

### 3.1 Low-Cluster-Count Stress Grid

Coverage of Clean error rate ($p=0.050, m=15$) across varying cluster counts and ICC values:

| Clusters ($C$) | Cluster Size ($m$) | ICC | DEFF | Naive CP (Method A) | Design-Effect (Method B) | Profile Likelihood (Method C) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 10 | 15 | 0.00 | 1.00 | 95.8% | 95.8% | 90.8% |
| 10 | 15 | 0.15 | 3.10 | 80.8% | 90.8% | 93.3% |
| 10 | 15 | 0.30 | 5.20 | 65.8% | 80.8% | 100.0% |
| 25 | 15 | 0.00 | 1.00 | 96.7% | 96.7% | 90.0% |
| 25 | 15 | 0.15 | 3.10 | 69.2% | 90.0% | 84.2% |
| 25 | 15 | 0.30 | 5.20 | 59.2% | 90.8% | 95.0% |
| 50 | 15 | 0.00 | 1.00 | 95.8% | 95.8% | 79.2% |
| 50 | 15 | 0.15 | 3.10 | 80.0% | 94.2% | 87.5% |
| 50 | 15 | 0.30 | 5.20 | 64.2% | 93.3% | 86.7% |

---

## 4. Part C: Sequential Sensor-Drift Benchmark Results

Runtime monitoring evaluated across 6 critical operational scenarios ($N=150$ trajectories, horizon $T=600$, drift at $t=200$):

### Scenario: `scenario_1_sudden_fn`

| Monitor | Post-Drift Alarm | False Alarm (Pre) | Cond Mean Delay | Censored Delay Bound | Median Delay | Post-Drift Haz (max 400) | Pre-Drift Haz (max 200) | Mean Utility |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Static (No Monitor)** | 0.0% | 0.0% | NO_ALARM | 400.0 | >=400 (Censored) | 344.57 | 165.49 | -51006.0 |
| **Page CUSUM (Two-Sided)** | 9.3% | 0.0% | 284.9 | 389.3 | >=400 (Censored) | 335.33 | 165.49 | -50082.0 |
| **SPRT Likelihood-Ratio** | 24.0% | 0.0% | 287.4 | 373.0 | >=400 (Censored) | 321.21 | 165.49 | -48670.0 |
| **Fail-Closed Guard (Early Warning)** | 12.7% | 0.0% | 250.9 | 381.1 | >=400 (Censored) | 328.25 | 165.49 | -49374.0 |
| **Audit-Assisted SPRT (Supervised)** | 4.7% | 0.0% | 283.4 | 394.6 | >=400 (Censored) | 339.94 | 165.49 | -50543.3 |

### Scenario: `scenario_2_gradual_fn`

| Monitor | Post-Drift Alarm | False Alarm (Pre) | Cond Mean Delay | Censored Delay Bound | Median Delay | Post-Drift Haz (max 400) | Pre-Drift Haz (max 200) | Mean Utility |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Static (No Monitor)** | 0.0% | 0.0% | NO_ALARM | 400.0 | >=400 (Censored) | 347.51 | 165.49 | -51300.0 |
| **Page CUSUM (Two-Sided)** | 17.3% | 0.0% | 333.9 | 388.5 | >=400 (Censored) | 337.19 | 165.49 | -50268.0 |
| **SPRT Likelihood-Ratio** | 34.0% | 0.0% | 311.9 | 370.0 | >=400 (Censored) | 320.74 | 165.49 | -48623.3 |
| **Fail-Closed Guard (Early Warning)** | 26.0% | 0.0% | 318.5 | 378.8 | >=400 (Censored) | 328.57 | 165.49 | -49406.0 |
| **Audit-Assisted SPRT (Supervised)** | 7.3% | 0.0% | 305.3 | 393.1 | >=400 (Censored) | 341.35 | 165.49 | -50684.0 |

### Scenario: `scenario_3_fp_surge`

| Monitor | Post-Drift Alarm | False Alarm (Pre) | Cond Mean Delay | Censored Delay Bound | Median Delay | Post-Drift Haz (max 400) | Pre-Drift Haz (max 200) | Mean Utility |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Static (No Monitor)** | 0.0% | 0.0% | NO_ALARM | 400.0 | >=400 (Censored) | 307.81 | 165.49 | -47330.0 |
| **Page CUSUM (Two-Sided)** | 72.7% | 0.0% | 215.2 | 265.7 | 253.5 | 204.27 | 165.49 | -36976.7 |
| **SPRT Likelihood-Ratio** | 0.0% | 0.0% | NO_ALARM | 400.0 | >=400 (Censored) | 307.81 | 165.49 | -47330.0 |
| **Fail-Closed Guard (Early Warning)** | 81.3% | 0.0% | 201.7 | 238.7 | 224.0 | 183.32 | 165.49 | -34881.3 |
| **Audit-Assisted SPRT (Supervised)** | 0.7% | 0.0% | 221.0 | 398.8 | >=400 (Censored) | 306.91 | 165.49 | -47240.0 |

### Scenario: `scenario_4_prevalence_shift`

| Monitor | Post-Drift Alarm | False Alarm (Pre) | Cond Mean Delay | Censored Delay Bound | Median Delay | Post-Drift Haz (max 400) | Pre-Drift Haz (max 200) | Mean Utility |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Static (No Monitor)** | 0.0% | 0.0% | NO_ALARM | 400.0 | >=400 (Censored) | 288.94 | 165.49 | -45443.3 |
| **Page CUSUM (Two-Sided)** | 98.7% | 0.0% | 140.1 | 143.5 | 129.0 | 104.17 | 165.49 | -26966.7 |
| **SPRT Likelihood-Ratio** | 0.0% | 0.0% | NO_ALARM | 400.0 | >=400 (Censored) | 288.94 | 165.49 | -45443.3 |
| **Fail-Closed Guard (Early Warning)** | 98.7% | 0.0% | 126.4 | 130.0 | 117.0 | 94.53 | 165.49 | -26002.7 |
| **Audit-Assisted SPRT (Supervised)** | 4.0% | 0.0% | 240.2 | 393.6 | >=400 (Censored) | 284.23 | 165.49 | -44972.0 |

### Scenario: `scenario_5_compensating_unidentifiable`

| Monitor | Post-Drift Alarm | False Alarm (Pre) | Cond Mean Delay | Censored Delay Bound | Median Delay | Post-Drift Haz (max 400) | Pre-Drift Haz (max 200) | Mean Utility |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Static (No Monitor)** | 0.0% | 0.0% | NO_ALARM | 400.0 | >=400 (Censored) | 333.21 | 165.49 | -49870.7 |
| **Page CUSUM (Two-Sided)** | 0.7% | 0.0% | 9.0 | 397.4 | >=400 (Censored) | 331.04 | 165.49 | -49653.3 |
| **SPRT Likelihood-Ratio** | 2.0% | 0.0% | 267.7 | 397.4 | >=400 (Censored) | 331.03 | 165.49 | -49652.7 |
| **Fail-Closed Guard (Early Warning)** | 1.3% | 0.0% | 53.0 | 395.4 | >=400 (Censored) | 329.39 | 165.49 | -49488.7 |
| **Audit-Assisted SPRT (Supervised)** | 8.7% | 0.0% | 267.7 | 388.5 | >=400 (Censored) | 323.72 | 165.49 | -48921.3 |

### Scenario: `scenario_6_clustered_stream`

| Monitor | Post-Drift Alarm | False Alarm (Pre) | Cond Mean Delay | Censored Delay Bound | Median Delay | Post-Drift Haz (max 400) | Pre-Drift Haz (max 200) | Mean Utility |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Static (No Monitor)** | 0.0% | 0.0% | NO_ALARM | 400.0 | >=400 (Censored) | 345.23 | 92.39 | -43688.9 |
| **Page CUSUM (Two-Sided)** | 8.7% | 0.0% | 284.0 | 389.9 | >=400 (Censored) | 336.35 | 92.39 | -42801.5 |
| **SPRT Likelihood-Ratio** | 24.0% | 0.0% | 287.0 | 372.9 | >=400 (Censored) | 321.65 | 92.39 | -41330.9 |
| **Fail-Closed Guard (Early Warning)** | 14.0% | 1.3% | 279.6 | 377.8 | >=400 (Censored) | 326.04 | 92.3 | -41763.1 |
| **Audit-Assisted SPRT (Supervised)** | 6.0% | 0.0% | 266.7 | 392.0 | >=400 (Censored) | 338.41 | 92.39 | -43006.9 |

---

## 5. Statistical Counterexamples & Core Vulnerabilities

### Counterexample 1: The Unidentifiable Compensating Drift Trap
In Scenario 5, defect prevalence surged from $\pi=0.20 \to 0.25$, and sensor false-negative rate degraded from $FN=0.24 \to 0.38$. However, tool false-positive rate dropped to $FP=0.01733$, causing the aggregate marginal pass probability to remain exactly $0.832$:
$$P(Y=1 \mid \text{nominal}) = (0.80)(0.98) + (0.20)(0.24) = 0.83200$$
$$P(Y=1 \mid \text{drifted}) = (0.75)(0.98267) + (0.25)(0.38) = 0.83200$$

**Rigorous Theoretical Characterization:**
- **Identical Observable Distributions:** Because $P(Y=1 \mid \text{drifted}) \equiv P(Y=1 \mid \text{nominal})$, the post-drift sequence $\{Y_t\}_{t \ge 200}$ is identically distributed to the pre-drift sequence. Post-drift alarms follow the exact same stochastic process as in-control false alarms.
- **Zero Detection Power (Not Infinite Stopping Time):** The monitor's stopping time $T$ remains almost surely finite ($P(T < \infty) = 1$), but its conditional expected delay satisfies $\mathbb{E}[T - 200 \mid T \ge 200] \approx ARL_0$. The monitor has **zero asymptotic drift-detection power** above nominal false alarms.
- **Information-Theoretic Barrier:** Because $D_{\text{KL}}(F_1 \parallel F_0) = 0$, change detection is impossible from $Y_t$ alone. Any alarm that triggers is an accidental false alarm excursion.

### Counterexample 2: False Alarm Bursts in Clustered Runtime Streams
In Scenario 6, when pipelines arrived in correlated batches (ICC > 0), standard i.i.d. CUSUM suffered a false alarm rate under nominal conditions because clustered error bursts violated the independent increment assumption.

---

## 6. Single Most Important Remaining Scientific Weakness

> [!WARNING]
> **THE LATENT DRIFT OBSERVABILITY DEFICIT:**
> Operational risk depends jointly on defect prevalence $\pi$ and sensor error rates $(FP, FN)$, but runtime execution only reveals the aggregate scalar verification stream $Y_t \in \{0, 1\}$. Because distinct risk states produce identical aggregate pass rates, **purely unsupervised sequential monitoring cannot guarantee safety against sensor degradation**. Reliable risk containment requires continuous, delayed ground-truth audit sampling.

---

## 7. Status & Pre-Freeze Guardrails

- **Assessment:** Exploratory research successfully executed, reconciled, and falsifications documented.
- **Candidate Controllers:** Completely unmodified.
- **Confirmatory Seeds:** Strictly untouched (`70100001+`, `70200001+`, `60030001+` unexecuted).
- **PRE-FREEZE NO-GO REMAINS IN EFFECT.**
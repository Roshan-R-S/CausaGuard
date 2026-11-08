# Experiment 06: Independent Scientific Reconciliation Report

**Document Version:** 1.0.0-RECONCILIATION  
**Date:** 2026-11-07  
**Research Baseline:** `cfa841a` on `main` plus uncommitted research artifacts  
**Status:** **EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO**  
**Execution Environment:** Seed-isolated offline statistical reproduction (Python 3.12.13, `numpy`, `scipy.stats`, `scipy.special`)  
**Cross-References:**  
- Experiment 06 Review Report: [`research/reviews/v071-de-cluster-drift-exp06.md`](file:///d:/causaguard/research/reviews/v071-de-cluster-drift-exp06.md)  
- Initial Evidence Snapshot: [`research/reviews/v071-de-cluster-drift-exp06-initial.json`](file:///d:/causaguard/research/reviews/v071-de-cluster-drift-exp06-initial.json)  
- Reconciled Evidence: [`research/reviews/v071-de-cluster-drift-exp06.json`](file:///d:/causaguard/research/reviews/v071-de-cluster-drift-exp06.json)  
- Experiment 06 Implementation: [`research/experiments/de_cluster_drift_exp06/experiment.py`](file:///d:/causaguard/research/experiments/de_cluster_drift_exp06/experiment.py)  
- Acceptance Test Suite: [`tests_v07_1/test_de_cluster_drift_exp06.py`](file:///d:/causaguard/tests_v07_1/test_de_cluster_drift_exp06.py)  
- Prior Protocol: [`research/methodology/v071-de-cluster-calibration-drift-protocol.md`](file:///d:/causaguard/research/methodology/v071-de-cluster-calibration-drift-protocol.md)  

---

## 1. Executive Summary & Audit Objectives

This document presents an independent scientific audit, mathematical reconciliation, and theoretical correction of **Experiment 06 (Cluster-Robust Calibration and Sequential Drift Detection)**.

In accordance with defensive scientific auditing, all sequential change-point theorems, scenario arithmetic, right-censoring conventions, Monte Carlo uncertainties, and epistemic claims were reviewed from primary statistical literature (Page 1954; Lorden 1971; Moustakides 1986; Siegmund 1985; Cameron & Miller 2015).

### Key Audit Conclusions:
1. **Surviving Core Findings:**
   - **Clustering Collapse Confirmed:** Naive independent Clopper–Pearson (Method A) collapses under intra-cluster correlation ($41.7\%$ parameter coverage, $10.7\%$ false safety qualifications), confirming $H_{1, \text{naive}}$.
   - **Observational Non-Identifiability Demonstrated:** In Scenario 5 (compensating drift), joint shifts in $(\pi, FP, FN)$ perfectly preserve the marginal Bernoulli pass rate ($p_1 \equiv p_0 = 0.83200$), proving that unsupervised monitoring on verification passes alone cannot guarantee safety.
2. **Retracted or Corrected Theoretical Claims:**
   - **Retraction of $ARL_1 = \infty$:** For identical observable distributions ($p_1 \equiv p_0$), the monitor's post-change stopping time is almost surely finite ($P(T < \infty) = 1$) with expected delay bounded by $ARL_0$. The true deficiency is **zero asymptotic drift-detection power above nominal false alarms**, not an infinite stopping time.
   - **Correction of $h / D_{\text{KL}}$ Applicability:** The Wald expression $h / D_{\text{KL}}$ is an asymptotic approximation as $h \to \infty$ for correctly specified likelihood ratios under positive drift, not an absolute finite-sample lower bound, and is inapplicable when $D_{\text{KL}} = 0$.
3. **Corrected Scenario Arithmetic & Metrics:**
   - **Pass Rate Reconciled:** In Scenario 1 ($FN = 0.380$), the true post-drift pass rate is **$0.86000$** ($D_{\text{KL}} = 0.002941$), correcting an earlier draft figure of $0.85400$ ($D_{\text{KL}} = 0.001796$, which corresponded to $FN = 0.350$).
   - **Hazardous Qualification Metric Disentangled:** The initial report showed $\approx 510$ hazardous qualifications out of a 400-step post-drift window. The audit identified that because pre-drift true risk was $0.0525 > 0.050$, the counter was accumulating pre-drift passes ($t < 200$, $\sim 166$) and post-drift passes ($t \ge 200$, $\sim 344$). These metrics are now strictly partitioned.
   - **Right-Censored Delay Reporting:** The report previously computed mean delay only over trajectories that alarmed before horizon $T=600$ (e.g. reporting 9.0 runs in Scenario 5 based on 1 accidental false alarm). Reconciled reporting incorporates right-censored lower bounds and medians.
4. **Epistemic Boundaries Enforced:**
   - Observing $0 / 300$ false safety qualifications in Method B bounds the true FSQ probability to $\le 1.26\%$ (Wilson $95\%$ CI), not zero.

---

## 2. Task A — Sequential Detection Theory Corrections

### 2.1 Observational Non-Identifiability vs. Infinite Run Length

In Scenario 5, generating parameters shift from $(\pi_0 = 0.20, FP_0 = 0.02, FN_0 = 0.24)$ to $(\pi_1 = 0.25, FP_1 = 0.01733, FN_1 = 0.38)$.

The marginal verification pass probabilities satisfy:
$$P(Y=1 \mid \text{nominal}) = (1 - 0.20)(1 - 0.02) + (0.20)(0.24) = 0.784 + 0.048 = \mathbf{0.83200}$$
$$P(Y=1 \mid \text{drifted}) = (1 - 0.25)(1 - 0.01733) + (0.25)(0.38) = 0.737 + 0.095 = \mathbf{0.83200}$$

#### Prior (Erroneous) Claim:
> "Because $\Delta P(Y) \equiv 0$, the CUSUM monitor never alarms, resulting in guaranteed infinite detection delay ($ARL_1 = \infty$)."

#### Mathematical Correction:
Let $T = \inf \{ t \ge 1 : S_t \ge h \}$ be the stopping time of the CUSUM procedure with threshold $h > 0$.
1. Because the observable sequence $\{Y_t\}_{t \ge 200}$ is i.i.d. Bernoulli with $p = 0.83200$, it is statistically identical to the in-control sequence $\{Y_t\}_{t < 200}$.
2. Under any finite threshold $h < \infty$, a random walk with non-absorbing states visits every state with positive probability over an infinite horizon. Specifically, by the recurrence properties of random walks on finite state spaces (Feller 1968), the stopping time is finite almost surely:
   $$P(T < \infty) = 1$$
3. By Lorden's renewal theorem (Lorden 1971), if the monitor reaches change-point $\tau = 200$ with score $S_{\tau - 1} = s \ge 0$:
   $$\mathbb{E}_{\tau}[T - \tau \mid S_{\tau - 1} = s] = \mathbb{E}_0[T \mid S_0 = s] \le ARL_0 < \infty$$
4. Therefore, $ARL_1$ is **NOT infinite**.
5. **The Rigorous Scientific Vulnerability:** The monitor has **zero asymptotic drift-detection power** above nominal false alarms. The post-change survival function is identical to the in-control survival function:
   $$P(T - \tau > w \mid T \ge \tau) = P_0(T > w) \quad \forall w \ge 0$$
   Any alarm that occurs post-change is statistically an accidental in-control false alarm excursion. The system remains completely exposed to hazardous operational risk ($R = 0.1039 \gg 0.050$) for an expected duration of $ARL_0$ runs.

---

### 2.2 Theoretical Status of the $h / D_{\text{KL}}$ Expression

The Experiment 06 review report cited:
$$\mathbb{E}[T_{\text{detect}}] \ge \frac{h}{D_{\text{KL}}}$$

#### Mathematical Review against Primary Literature:
1. **Wald's Identity in Sequential Analysis (Wald 1947):**
   For a sequential probability ratio test with stopping boundary $h$ and independent score increments $Z_t$, Wald's identity states:
   $$\mathbb{E}[S_T] = \mathbb{E}[T] \cdot \mathbb{E}[Z]$$
   When $Z_t = \log \frac{f_1(Y_t)}{f_0(Y_t)}$ is the true log-likelihood ratio, $\mathbb{E}_1[Z] = D_{\text{KL}}(F_1 \parallel F_0) > 0$.
   At stopping time $T$, the score is $S_T = h + R_h$, where $R_h \ge 0$ is the overshoot (excess over the boundary):
   $$\mathbb{E}_1[T] = \frac{h + \mathbb{E}_1[R_h]}{D_{\text{KL}}(F_1 \parallel F_0)}$$
2. **Asymptotic Approximation vs. Finite-Sample Bound (Lorden 1971; Siegmund 1985):**
   - In Page's CUSUM, because the statistic resets to zero ($S_t = \max(0, S_{t-1} + Z_t)$), the expected delay from change-point $\tau$ satisfies Lorden's asymptotic limit:
     $$ARL_1 \sim \frac{h}{D_{\text{KL}}(F_1 \parallel F_0)} \quad \text{as } h \to \infty$$
   - In finite samples, $h / D_{\text{KL}}$ is an **asymptotic first-order approximation**, not an exact distribution equality.
   - For discrete Bernoulli observations, the overshoot $R_h$ is non-zero, meaning $h / D_{\text{KL}}$ is a theoretical lower bound for the SPRT stopping time, but in CUSUM, prior accumulation ($S_{\tau - 1} > 0$) can slightly shorten the delay, while reset delays can lengthen it.
3. **Inapplicability Under Non-Identifiability ($D_{\text{KL}} = 0$):**
   When $F_1 \equiv F_0$, $D_{\text{KL}} = 0$. Dividing $h / 0$ is mathematically undefined. Wald's positive-drift identity does not apply when $\mathbb{E}[Z] \le 0$. The process is governed by extreme-value excursion theory (Siegmund 1985, Chapter 8).

---

## 3. Task B — Scenario Arithmetic & Metric Reconciliations

### 3.1 Pass Rates, Operational Risks, and Kullback–Leibler Divergences

All scenarios evaluated with prior defect prevalence $\pi_0 = 0.20$ and verification availability $A = 0.91$:

| Scenario ID & Drift Description | Parameters $(\pi, FP, FN)$ | Verification Pass Rate $P(Y=1)$ | Operational Risk $R(\theta)$ | Status vs $\tau_{\text{safe}}=0.050$ | $D_{\text{KL}}(p_1 \parallel p_0)$ from $p_0=0.832$ |
|---|---|:---:|:---:|:---:|:---:|
| **Nominal Baseline (Pre-Drift)** | $\pi=0.20, FP=0.020, FN=0.240$ | **0.83200** | **0.052500** | Unsafe ($> 0.050$) | $0.000000$ |
| **Scenario 1: Sudden FN Surge** | $\pi=0.20, FP=0.020, FN=0.380$ | **0.86000** | **0.080419** | Severe ($> 0.050$) | **0.002941** |
| *(Draft Error in Initial Exp06)* | $\pi=0.20, FP=0.020, FN=0.350$ | *0.85400* | *0.074590* | *Severe ($> 0.050$)* | *0.001796* |
| **Scenario 2: Gradual FN Ramp** | $\pi=0.20, FP=0.020, FN(t) \to 0.50$ | $0.832 \to 0.884$ | $0.0525 \to 0.102$ | Severe ($> 0.050$) | Dynamic |
| **Scenario 3: Tool FP Surge** | $\pi=0.20, FP=0.100, FN=0.240$ | **0.76800** | **0.056875** | Unsafe ($> 0.050$) | **0.013411** |
| **Scenario 4: Prevalence Surge** | $\pi=0.35, FP=0.020, FN=0.240$ | **0.72100** | **0.106019** | Severe ($> 0.050$) | **0.038280** |
| **Scenario 5: Compensating Drift** | $\pi=0.25, FP=0.01733, FN=0.380$ | **0.83200** | **0.103906** | Severe ($> 0.050$) | **0.000000** |

#### Reconciliation of Scenario 1 Arithmetic:
- In the initial review report, the pass rate under Scenario 1 was written as $0.85400$.
- **Audit Finding:** $(0.80)(0.98) + (0.20)(0.380) = 0.784 + 0.076 = \mathbf{0.86000}$. The value $0.85400$ was an artifact from an earlier draft that tested $FN=0.350$ ($0.784 + 0.070 = 0.854$).
- The SPRT monitor was configured with $p_1 = 0.854$. When true drift is $p_1 = 0.860$, the monitor operates with slight parameter misspecification, reducing its average score increment from $+0.00294$ to $+0.00279$ per step. `LikelihoodRatioSPRTMonitor` has been updated with $p_1 = 0.860$.

---

### 3.2 Hazardous Qualification Count Discrepancy & Metric Decoupling

#### The Discrepancy:
In the initial Experiment 06 table, `mean_hazardous_qualified` was reported as $\approx 510.1$ runs.
The total trajectory horizon was $T = 600$, with drift injected at $t = 200$.
Thus, the post-drift exposure window is strictly:
$$T_{\text{post-drift}} = 600 - 200 = \mathbf{400 \text{ time steps}}$$
Reporting $510.1 > 400$ hazardous qualifications in a drift study was an apparent arithmetic contradiction.

#### Root Cause Investigation:
In `experiment.py`, line 925:
```python
instant_is_safe = instant_true_risk <= SAFETY_THRESHOLD  # 0.050
```
Because pre-drift true risk is $R(\theta^*) = 0.052500 > 0.050$, `instant_is_safe` evaluated to **False** for the entire trajectory $t \in [1, 600]$!
Whenever verification passed ($Y_t = 1$), the counter incremented:
- Pre-drift ($t < 200$): Expected passes $= 200 \times 0.832 = \mathbf{166.4}$.
- Post-drift ($t \ge 200$): Expected passes $= 400 \times 0.860 = \mathbf{344.0}$.
- Total passes: $166.4 + 344.0 = \mathbf{510.4}$.

The code was counting pre-drift baseline false safety qualifications together with post-drift exposure!

#### Reconciled Metrics:
We decoupled the metrics into three explicit, non-overlapping indicators:
1. `pre_drift_hazardous_count`: False safety qualifications occurring before drift ($t < 200$). **Strictly bounded by $[0, 200]$.** (Mean: $\approx 166.4$).
2. `post_drift_hazardous_count`: Hazardous qualifications occurring after drift ($t \ge 200$) before monitor quarantine. **Strictly bounded by $[0, 400]$.** (Mean: $\le 344.0$).
3. `total_hazardous_count`: Full trajectory sum $= \text{pre} + \text{post}$. **Strictly bounded by $[0, 600]$.**

---

### 3.3 Right-Censoring and Delay Reporting

In a finite simulation horizon ($T = 600$, drift at $t = 200$, max window $= 400$):
Trajectories that do not alarm before $t = 600$ are **right-censored at 400 runs**.

#### Initial Report Flaw:
The initial report computed:
$$\text{Mean Delay} = \frac{1}{|\mathcal{A}|} \sum_{i \in \mathcal{A}} (T_{\text{alarm}, i} - 200)$$
where $\mathcal{A} = \{i : \text{trajectory } i \text{ alarmed post-drift}\}$.
In Scenario 5, only $1$ out of $150$ trajectories alarmed ($0.7\%$ alarm rate), at run $209$. The report printed `Mean Delay: 9.0 runs`. Reporting $9.0$ runs for a monitor that failed to alarm in $99.3\%$ of trajectories is a severe artifact of conditioning on detection.

#### Reconciled Multi-Metric Delay Reporting:
1. **Post-Drift Alarm Rate ($P_{\text{alarm}}$):** Fraction of trajectories detecting drift before $T=600$.
2. **Conditional Mean Delay ($\mathbb{E}[D \mid \text{alarmed}]$):** Mean delay among detected runs.
3. **Censored Delay Lower Bound ($\mathbb{E}[\min(400, D)]$):** Assigns $400$ runs to all unalarmed trajectories.
4. **Median Delay ($\text{Med}(D)$):** Median across all $N$ trajectories, reporting `">=400 (Censored)"` when alarm rate is $< 50\%$.

---

## 4. Reconciled Sequential Drift Benchmark Results

Evaluated across $N=150$ Monte Carlo trajectories under the reconciled metric definitions:

### Scenario 1: Sudden FN Surge ($FN: 0.24 \to 0.38, p: 0.832 \to 0.860, R: 0.0525 \to 0.0804$)
| Monitor | Post-Drift Alarm | False Alarm (Pre) | Cond Delay | Censored Delay Bound | Median Delay | Post-Drift Haz (max 400) | Pre-Drift Haz (max 200) | Net Utility |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Static (No Monitor)** | 0.0% | 0.0% | NO_ALARM | 400.0 | >=400 (Censored) | **343.8** | 166.3 | -51006.0 |
| **Page CUSUM (Two-Sided)** | 9.3% | 0.0% | 284.9 | **389.3** | >=400 (Censored) | **334.5** | 166.3 | -50082.0 |
| **SPRT Likelihood-Ratio** | 7.3% | 0.0% | 330.8 | **394.9** | >=400 (Censored) | **339.4** | 166.3 | -50566.0 |
| **Fail-Closed Guard** | 12.7% | 0.0% | 250.9 | **381.1** | >=400 (Censored) | **327.4** | 166.3 | -49374.0 |
| **Audit-Assisted SPRT** | 4.7% | 0.0% | 283.4 | **394.5** | >=400 (Censored) | **339.1** | 166.3 | -50543.3 |

### Scenario 5: Compensating Drift ($p_1 \equiv p_0 = 0.83200, R: 0.0525 \to 0.1039$)
| Monitor | Post-Drift Alarm | False Alarm (Pre) | Cond Delay | Censored Delay Bound | Median Delay | Post-Drift Haz (max 400) | Pre-Drift Haz (max 200) | Net Utility |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Static (No Monitor)** | 0.0% | 0.0% | NO_ALARM | 400.0 | >=400 (Censored) | **332.4** | 166.3 | -49870.7 |
| **Page CUSUM (Two-Sided)** | **0.7%** | 0.0% | 9.0* | **397.4** | >=400 (Censored) | **330.2** | 166.3 | -49653.3 |
| **SPRT Likelihood-Ratio** | **0.0%** | 0.0% | NO_ALARM | 400.0 | >=400 (Censored) | **332.4** | 166.3 | -49870.7 |
| **Fail-Closed Guard** | **1.3%** | 0.0% | 53.0* | **395.4** | >=400 (Censored) | **328.6** | 166.3 | -49488.7 |
| **Audit-Assisted SPRT** | **8.7%** | 0.0% | 267.7 | **388.5** | >=400 (Censored) | **322.9** | 166.3 | -48921.3 |

*\*Note: Asterisk indicates conditional mean over $\le 2$ accidental false-alarm excursions. Median delay is $\ge 400$ runs.*

---

## 5. Task C — Reassessment of Calibration Evidence

### 5.1 Independent Reproduction of Calibration Benchmark

Re-evaluated across $N=300$ replications with independent cluster batches ($C_{\text{clean}}=50, C_{\text{schema}}=25, m=20, \text{ICC}=0.25$):

| Estimator | Simultaneous Param Coverage | 95% Wilson CI | Risk Bound Enclosure | Observed FSQ Rate | 95% Upper Bound on True FSQ | Mean $\mathbb{E}[U]$ |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Method A: Naive CP** | **41.7%** | $[0.362, 0.473]$ | **68.3%** | **10.7%** | $14.6\%$ | **-11.00** |
| **Method B: Design-Effect** | **88.0%** | $[0.838, 0.912]$ | **99.7%** | **0.0%** | **1.26%** (Wilson) / **1.00%** (Rule of 3) | **-0.49** |
| **Method C: Profile Likelihood** | **81.3%** | $[0.765, 0.853]$ | **98.7%** | **0.3%** | $1.86\%$ | **-0.82** |
| **Method D: Cluster Bootstrap** | **84.7%** | $[0.801, 0.883]$ | **98.7%** | **0.3%** | $1.86\%$ | **-0.82** |
| **Method E: Conservative ($\rho=1$)** | **100.0%** | $[0.987, 1.000]$ | **100.0%** | **0.0%** | **1.26%** | **-0.50** |

### 5.2 Methodological Critique of Calibration Claims:
1. **Independent Sampling Units Verified:** In each Monte Carlo replication, an entirely new batch of $C$ clusters is drawn. Clusters are correctly treated as independent sampling units.
2. **Zero FSQ Does Not Prove Zero Risk:** Method B had $0$ observed FSQs in $300$ runs. By the two-sided Wilson score formula at $\alpha=0.05$ ($z=1.96$):
   $$\overline{p} = \frac{z^2 / n}{1 + z^2 / n} = \frac{3.8415 / 300}{1 + 3.8415 / 300} = \mathbf{0.0126} \quad (1.26\%)$$
   Observing zero failures in $300$ trials guarantees failure probability $\le 1.26\%$, **NOT zero**.
3. **Finite-Sample Undercoverage in Method B:** Method B achieves $88.0\%$ simultaneous parameter coverage, failing the nominal $95\%$ target. Why? Because $\widehat{\rho}$ is estimated with finite sampling noise from $C=25$ clusters. In $12\%$ of replications, $\widehat{\rho} < \rho^*$, producing an under-adjusted effective sample size $N_{\text{eff}}$ and too-narrow intervals.
4. **Finite-Sample Undercoverage in Methods C and D:**
   - Method C relies on asymptotic profile likelihood $\chi^2_1$ quantiles, which exhibit small-sample anti-conservatism.
   - Method D relies on cluster bootstrap percentiles, which suffer undercoverage when $C < 30$ (Cameron & Miller 2015).
5. **Empirical Conservatism vs. Theoretical Proof:** Only Method E provides a distribution-free conservative guarantee under positive ICC, but it forces $100\%$ abstention. Method B provides practical heuristic protection, but is **not** an exact finite-sample theorem.

---

## 6. Exact Reconciliation Summary: Before vs. After

| Item / Claim | Prior Experiment 06 Statement | Reconciled Audit Correction | Scientific Justification |
|---|---|---|---|
| **Compensating Drift Stopping Time** | "Guaranteed infinite detection delay ($ARL_1 = \infty$)." | **Finite stopping time ($P(T<\infty)=1$), $\mathbb{E}[T-\tau] \le ARL_0$. Zero drift-detection power.** | Alarm process is statistically identical to in-control false alarm excursion. Stopping time is finite almost surely. |
| **Wald $h / D_{\text{KL}}$ Status** | "Mathematical lower bound." | **Asymptotic first-order approximation as $h \to \infty$. Undefined when $D_{\text{KL}} = 0$.** | Primary sequential literature (Wald 1947, Lorden 1971, Siegmund 1985). Overshoot and discrete resets modify finite-$h$ behavior. |
| **Scenario 1 Pass Rate** | $P(Y=1) = 0.85400$. | **$P(Y=1) = 0.86000$.** | Arithmetic: $(0.80)(0.98) + (0.20)(0.380) = 0.86000$. (0.854 corresponded to $FN=0.350$). |
| **Scenario 1 KL Divergence** | $D_{\text{KL}} = 0.00192$. | **$D_{\text{KL}}(0.860 \parallel 0.832) = 0.002941$.** | Exact Bernoulli formula: $0.86\log(0.86/0.832) + 0.14\log(0.14/0.168)$. |
| **Hazardous Qualifications** | "510.06 hazardous qualifications" (in 400-step post-drift window). | **Decoupled: Pre-drift = 166.3 (max 200), Post-drift = 334.5 (max 400), Total = 500.8.** | Pre-drift true risk was $0.0525 > 0.050$, so the old counter accumulated pre- and post-drift passes together. |
| **Scenario 5 Delay** | "Mean Delay: 9.0 runs." | **Median $\ge 400$ runs (Censored). Post-drift alarm rate = $0.7\%$. Censored delay bound = $397.4$ runs.** | 9.0 was the conditional delay of a single accidental false alarm. 99.3% of runs never alarmed before horizon. |
| **Zero FSQ Interpretation** | "Eliminated FSQ (0.0%)." | **Zero observed events in 300 trials bounds FSQ to $\le 1.26\%$ ($95\%$ Wilson), not zero.** | Binomial inference with zero numerator (Rule of three / Wilson score). |
| **Cluster Estimator Claims** | "Method B restores coverage." | **Method B achieves $88.0\%$ parameter coverage (under nominal $95\%$), but achieves $99.7\%$ risk enclosure.** | Small cluster count ($C=25$) sampling variance in $\widehat{\rho}$ causes under-adjustment in $12\%$ of samples. |

---

## 7. Status of Scientific Hypotheses & Research Readiness

1. **Which central findings survive correction?**
   - **Naive calibration is invalid under clustering ($H_{1, \text{naive}}$ CONFIRMED):** Severe parameter undercoverage ($41.7\%$) and high FSQ ($10.7\%$).
   - **Rao-Scott design-effect adjustment dramatically reduces risk non-enclosure:** Expands intervals by $\approx \sqrt{\text{DEFF}}$, eliminating observed FSQ ($0.0\%$, upper bound $1.26\%$).
   - **Unsupervised sequential monitoring cannot guarantee safety ($H_{1, \text{drift}}$ CONFIRMED):** Low defect prevalence and compensating distribution shifts prevent timely detection on unlabelled pass rates alone.
2. **Which claims are retracted?**
   - Retracted claim that compensating drift produces infinite stopping time ($ARL_1 = \infty$).
   - Retracted claim that 0 observed FSQs proves mathematical impossibility of failure.
   - Retracted claim that Method B achieves exact nominal $95\%$ simultaneous parameter coverage.
3. **Which findings remain uncertain?**
   - The optimal sample allocation between clusters $C$ and cluster size $m$ to guarantee bounded $\text{SE}(\widehat{\rho})$.
   - The minimum ground-truth audit sampling rate required to guarantee detection delay $ARL_1 \le 50$ under finite audit budgets.
4. **Is the research ready for a new experimental phase?**
   - **YES FOR EXPLORATORY EXPERIMENT 07 DESIGN:** Ready to investigate semi-supervised drift monitoring combining unlabelled pass streams with delayed audit streams and empirical Bayes shrinkage on cluster ICC.
   - **STRICT NO-GO FOR CONTROLLER INTEGRATION OR FREEZE:** Pre-freeze status remains strictly in effect.

---

## 8. Verification & Test Evidence

```powershell
# Acceptance test suite execution
.venv\Scripts\pytest.exe -c pytest_v07_1.ini tests_v07_1/test_de_cluster_drift_exp06.py -v
# Outcome: 13 passed in 0.84s

# Full regression test suite execution
.venv\Scripts\pytest.exe -c pytest_v07_1.ini
# Outcome: 280 passed, 1 skipped, 6 xfailed in 4.32s

# Linting and style verification
.venv\Scripts\ruff.exe check research/ tests_v07_1/ src_v07_1/
# Outcome: All checks passed!
```

---

## 9. Pre-Freeze Integrity Declaration

- Original candidate controllers (`domain_de.py`, `policy_v07_1.py`) remain completely unmodified.
- Confirmatory protocol manifests and thresholds remain untouched.
- Reserved confirmatory seeds (`70100001+`, `70200001+`, `60030001+`) remain unexecuted.
- No cryptographic keys generated; `PRODUCTION_AUTHORIZATION_ENABLED = False`.
- No Git commits or pushes executed.
- **PRE-FREEZE NO-GO REMAINS STRICTLY IN EFFECT.**


# CausaGuard Gate 1 Cross-Report Consistency Audit: Mathematical Reconciliations, Error Corrections, and Sampling Validity Framework

**Status:** EXPLORATORY SCIENTIFIC RESEARCH — PRE-FREEZE NO-GO  
**Date:** November 2026  
**Author:** Antigravity (Gemini)  
**Current Git HEAD:** `fb887df03fa6b22437ecc779c1cf8ac92dc9d474`  
**Original Research Baseline:** `cfa841ad5fd6dd5ad300b60554a6570b840a66db`  
**Target Repository:** `D:\causaguard`  
**Primary Review Scope:**  
- `research/reviews/v071-gate1-betting-bounds-benchmark.md` (Benchmark Report)  
- `research/reviews/v071-gate1-betting-bounds-benchmark.json` (Benchmark Data)  
- `research/reviews/v071-gate1-betting-benchmark-reconciliation.md` (Reconciliation Report)  
- `research/reviews/v071-gate1-betting-mean-assumptions-audit.md` (Mean Assumptions Audit)  
- `research/experiments/gate1_betting_benchmark/betting_bounds.py` (Bounds Implementation)  
- `tests_v07_1/test_gate1_betting_benchmark.py`  
- `tests_v07_1/test_gate1_betting_reconciliation.py`  
- `tests_v07_1/test_gate1_betting_mean_assumptions.py`  
**Pre-Freeze Invariants:** Zero Candidate Controller Changes, Zero Confirmatory Protocol Modifications, Absolute Seed Quarantine (`70100001+`, `70200001+`, `60030001+` untouched), Zero Production Authorization.

---

## 1. Executive Summary & Scope of Audit

This cross-report consistency audit resolves and corrects material mathematical contradictions that emerged across recent Gate 1 statistical research artifacts.

### 1.1 Summary of Confirmed Errors and Corrections

| Item | Erroneous / Obsolete Claim in Prior Artifacts | Correct Mathematical Reality | Root Cause & Resolution |
| :--- | :--- | :--- | :--- |
| **1. Supermartingale Condition Direction** | Prior text stated that the betting supermartingale requires $\mathbb{E}[R_k \mid \mathcal{F}_{k-1}] \le m$. | For the one-sided upper-bound null $\mathcal{H}_0: \theta \ge m$ with payoff increment $(m - R_k)$ and $\lambda_k \ge 0$, the supermartingale condition requires **$\mathbb{E}[R_k \mid \mathcal{F}_{k-1}] \ge m$**. | Writing $\le m$ was a sign error describing a submartingale increment. When risk is safe ($\mathbb{E}[R_k \mid \mathcal{F}_{k-1}] < m$), the multiplier is $> 1$ (wealth grows). Fully corrected. |
| **2. Maurer–Pontil Shock Capacity** | Section 7 of `mean-assumptions-audit.md` claimed Maurer–Pontil qualifies $Z \le 7$ shocks and achieves $100.0\%$ power at $K=256, \theta=0.010$. | Maurer–Pontil Theorem 4 tolerates at most **$Z \le 1$** shock ($U(1) \approx 0.0483 \le 0.0500$, but $U(2) \approx 0.0565 > 0.0500$). True power is **$27.3655\%$**. | Erroneous transcription: the uncorrected Student-$t$ row ($100\%$ power, $Z \le 7$) was mistakenly copied into the Maurer–Pontil row in the summary table. Fully corrected. |
| **3. Betting Benchmark Power Reconciliation** | `reconciliation.md` asserted that empirical power ($416/500 = 83.20\%$) and theoretical expected power ($87.23\%$) "matched within sampling uncertainty." | The $95\%$ Clopper–Pearson CI for $416/500$ is **$[79.63\%, 86.37\%]$**, which **strictly excludes** $87.23\%$ ($p = 0.008855$). | Conflation of unconditional population power with a conditional finite-sample realization. In seed `82000014`, $Z=5$ occurred 54 times (vs. $35.3$ expected). Conditional on realized $Z$, expected passes is $418.1$ ($83.6\%$). |
| **4. Labeling of 87.23% Power Figure** | Prior drafts referred to $87.227\%$ as the "exact theoretical population power". | $87.227\%$ is a **semi-analytical / permutation Monte Carlo power estimate** integrating empirical permutation estimates $\hat{q}_{\text{perm}}(z)$ over $\text{Binomial}(256, 0.010)$. | Re-labeled accurately. Permutation pass rates $\hat{q}(4) \approx 0.895$ and $\hat{q}(5) \approx 0.040$ are Monte Carlo estimates from 200 random shuffles, not exact analytical values. |
| **5. Truncation Cap Violation in Counterexample** | `mean-assumptions-audit.md` used $\lambda_1 = 4.0$ and $\lambda = 10.0$ in the 2-cluster counterexample. | For $m = 0.05, c = 0.75$, the mathematical betting ceiling is $\lambda_{\max} = \frac{c}{1 - m} = \frac{0.75}{0.95} \approx \mathbf{0.7895}$. Bets $\ge 0.7895$ violate the algorithm contract. | Replaced with valid parameters: $\lambda_1 = 0.50 \le 0.7895, \lambda_2 = 0.00$, yielding $\mathbb{E}[W_2] = 1.025 > 1.0$. |
| **6. Heterogeneous Schedule Mean Labeling** | `mean-assumptions-audit.md` referred to the $K=256$ front-loaded schedule as having mean $0.0500$. | The schedule ($64 \times 0.2004 + 192 \times 0.0$) has true mean $\bar{\mu} = \mathbf{0.0501}$. | Relabeled and clarified: testing against $\tau_{\text{safe}} = 0.0500$ is strictly an unsafe condition ($\bar{\mu} > 0.0500$), so qualifications are False Safety Qualifications (FSQ). |
| **7. Grid Inversion Certification & UCB Status** | Prior text suggested a 50-point grid search proves global supremum inversion. | A finite grid alone **cannot mathematically certify** the global supremum across non-monotone continuous functions. | `ucb_betting_fixed_time` is explicitly marked **EXPLORATORY ONLY — NOT APPROVED FOR CONFIRMATORY USE**. Direct threshold test introduced. |
| **8. Confirmatory Design vs. Real-World Operations** | Prior reports presented simulator IID proofs as proof of operational real-world safety. | Synthetic simulator IID guarantees (Design A) **do not** transfer to real-world operations where non-stationarity, external shocks, and calendar drift occur. | Formally separated simulator Design A verification from operational deployment drift. |

**Policy Directive:** In accordance with project instructions, **NO primary confirmatory statistical method is recommended at this time.** The status remains strictly **PRE-FREEZE NO-GO**.

---

## 2. Task 1: Mathematical Correction of the Supermartingale Condition

Let the wealth process under testing null threshold $m \in (0, 1)$ be:
$$W_k(m) = W_{k-1}(m) \cdot \left[1 + \lambda_k(m)(m - R_k)\right]$$
where predictable betting fraction $\lambda_k(m) \ge 0$ is $\mathcal{F}_{k-1}$-measurable.

### 2.1 The Mathematical Direction Under the Upper-Bound Null
We test the one-sided null hypothesis that operational risk is **unsafe**:
$$\mathcal{H}_0: \theta \ge m \quad \text{against} \quad \mathcal{H}_1: \theta < m$$
The single-step payoff increment is $(m - R_k)$.  
Taking conditional expectation with respect to the history $\mathcal{F}_{k-1}$:
$$\mathbb{E}[W_k(m) \mid \mathcal{F}_{k-1}] = W_{k-1}(m) \cdot \left(1 + \lambda_k(m)(m - \mathbb{E}[R_k \mid \mathcal{F}_{k-1}])\right)$$

For the wealth process $(W_k(m))$ to be a **supermartingale** ($\mathbb{E}[W_k(m) \mid \mathcal{F}_{k-1}] \le W_{k-1}(m)$), the expected multiplier must be $\le 1$:
$$1 + \lambda_k(m)(m - \mathbb{E}[R_k \mid \mathcal{F}_{k-1}]) \le 1$$
Since $\lambda_k(m) \ge 0$, this holds if and only if:
$$m - \mathbb{E}[R_k \mid \mathcal{F}_{k-1}] \le 0 \iff \mathbf{\mathbb{E}[R_k \mid \mathcal{F}_{k-1}] \ge m}$$

### 2.2 Reversal of the Sign Error
Prior draft text erroneously wrote $\mathbb{E}[R_k \mid \mathcal{F}_{k-1}] \le m$.  
- If $\mathbb{E}[R_k \mid \mathcal{F}_{k-1}] \le m$, then $m - \mathbb{E}[R_k \mid \mathcal{F}_{k-1}] \ge 0$.  
  The expected wealth multiplier is $\ge 1$, which defines a **submartingale** (wealth grows, allowing rejection of the null).  
- Stating $\le m$ describes the condition for testing a lower confidence bound ($\mathcal{H}_0: \theta \le m$).  
- For Gate 1 safety qualification (upper confidence bound, testing $\mathcal{H}_0: \theta \ge m$), the supermartingale condition requires **$\mathbb{E}[R_k \mid \mathcal{F}_{k-1}] \ge m$**.

This distinction is enforced by deterministic unit test `test_supermartingale_conditional_mean_condition_direction` in [`tests_v07_1/test_gate1_betting_mean_assumptions.py`](file:///d:/causaguard/tests_v07_1/test_gate1_betting_mean_assumptions.py).

---

## 3. Task 2: Resolution of Conditional vs. Theoretical Expected Passes

### 3.1 Independent Recomputation from Benchmark Data
Reading directly from the Gate 1 benchmark record (`research/reviews/v071-gate1-betting-bounds-benchmark.json`) for `method = "betting_fixed"`, $K = 256, \theta = 0.010$, `regime = "cluster_shock"`, evaluated with seed `82000014` over 500 trials:

| Shock Count $Z$ | Theoretical Prob $\mathbb{P}(Z = z)$ | Realized Trials $N_z$ | In-Sample Actual Passes | In-Sample Pass Rate $\hat{q}(z)$ | Generic Permutation Pass Rate $\hat{q}_{\text{perm}}(z)$ |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **$Z = 0$** | $0.076315$ | $41$ | $41$ | $1.0000$ ($100\%$) | $1.0000$ ($100\%$) |
| **$Z = 1$** | $0.197340$ | $91$ | $91$ | $1.0000$ ($100\%$) | $1.0000$ ($100\%$) |
| **$Z = 2$** | $0.254153$ | $112$ | $112$ | $1.0000$ ($100\%$) | $1.0000$ ($100\%$) |
| **$Z = 3$** | $0.217351$ | $103$ | $103$ | $1.0000$ ($100\%$) | $1.0000$ ($100\%$) |
| **$Z = 4$** | $0.138865$ | $77$ | $68$ | **$0.8831$** ($88.3\%$) | **$0.8950$** ($89.5\%$) |
| **$Z = 5$** | $0.070689$ | $54$ | $1$ | **$0.0185$** ($1.85\%$) | **$0.0400$** ($4.00\%$) |
| **$Z = 6$** | $0.029885$ | $11$ | $0$ | $0.0000$ ($0\%$) | $0.0000$ ($0\%$) |
| **$Z = 7$** | $0.010502$ | $9$ | $0$ | $0.0000$ ($0\%$) | $0.0000$ ($0\%$) |
| **$Z = 8$** | $0.003050$ | $2$ | $0$ | $0.0000$ ($0\%$) | $0.0000$ ($0\%$) |
| **Total** | **$0.998150$** | **$500$** | **$416$** | **$0.8320$** ($83.2\%$) | — |

### 3.2 Resolution of the Discrepancy ($418.1$ vs. $416.0$)
The discrepancy between $418.1$ and $416$ arises from two different definitions of conditional expectation:
1. **Generic Permutation-Averaged Expected Passes ($418.075$):**  
   Applying the Monte Carlo permutation pass rates $\hat{q}_{\text{perm}}(z)$ (estimated over $M=200$ random shuffles per shock count) to the observed sample counts $N_z$:
   $$\mathbb{E}[\text{Passes} \mid N_z, \hat{q}_{\text{perm}}] = 347(1.000) + 77(0.8950) + 54(0.0400) = 347 + 68.915 + 2.160 = \mathbf{418.075} \approx \mathbf{418.1}$$
2. **Empirical In-Sample Passes ($416.0$):**  
   Summing the actual passes realized in the specific 500 trials of seed `82000014`, where $Z=4$ passed 68 times ($88.31\%$) and $Z=5$ passed 1 time ($1.85\%$):
   $$\sum_{z} N_z \hat{q}(z) = 347(1.000) + 68 + 1 = \mathbf{416.0}$$
   The difference of $2.1$ passes ($418.1 - 416.0$) is minor Monte Carlo variation between the 200 generic random shuffles and the specific permutations drawn in seed `82000014`.

### 3.3 Distinguishing Monte Carlo Estimate from Theoretical Population Power
- **Unconditional Semi-Analytical / Permutation Monte Carlo Power Estimate:**  
  Integrating generic permutation pass rates $\hat{q}_{\text{perm}}(z)$ against the theoretical distribution $Z \sim \text{Binomial}(256, 0.010)$:
  $$\hat{\mathbb{E}}[\text{Power}] = \sum_{z=0}^{256} \mathbb{P}(Z = z) \cdot \hat{q}_{\text{perm}}(z) = \mathbf{0.872270} \quad (\mathbf{87.2270\%})$$
  Notice: Because $\hat{q}_{\text{perm}}(4) \approx 0.895$ (SE $\approx 0.0217$) and $\hat{q}_{\text{perm}}(5) \approx 0.040$ (SE $\approx 0.0139$) are Monte Carlo estimates, this figure is a **semi-analytical estimate ($\approx 87.23\% \pm 0.63\%$)**, NOT an exact analytical closed-form derivation.
- **Monte Carlo Empirical Power:**  
  The realized fraction in seed `82000014`:
  $$\hat{p} = \frac{416}{500} = \mathbf{0.8320} \quad (\mathbf{83.20\%})$$
- **Uncertainty Intervals:**  
  Exact $95\%$ Clopper–Pearson CI for $416/500$ is **$[0.796289, 0.863726]$**.  
  Because $[0.7963, 0.8637]$ strictly excludes $0.8723$ ($p = 0.008855$), the empirical benchmark represents a finite-sample downward excursion driven by the over-representation of $Z=5$ shock trials ($54$ realized vs. $35.3$ expected).

---

## 4. Task 3: Scientific Qualification of Unsupported Claims

### 4.1 Maurer–Pontil Validity Under Heterogeneous Independent Means
- **Claim to Qualify:** "Maurer–Pontil empirical Bernstein is valid under arbitrary independent heterogeneous clusters."
- **Rigorous Scientific Qualification:** Maurer & Pontil (2009) Theorem 4 was formally proved for **identically distributed** random variables. When cluster means $\mu_k = \mathbb{E}[R_k]$ differ, the sample variance $V_n$ includes an additional between-cluster dispersion term:
  $$\mathbb{E}[V_n] = \frac{1}{K}\sum_{k=1}^K \text{Var}(R_k) + \frac{1}{K(K - 1)}\sum_{i \ne j} (\mu_i - \mu_j)^2$$
  While this variance inflation increases the penalty and makes the bound conservative in practice, Theorem 4 itself was NOT proved for independent non-identical variables. It cannot be presented as a mathematically proven finite-sample theorem for Design C without an independent formal proof.

### 4.2 Permutation-Averaged Betting Under Heterogeneous Means
- **Claim to Qualify:** "Permutation-averaged betting restores formal mathematical validity under heterogeneous clusters."
- **Rigorous Scientific Qualification:** Waudby-Smith & Ramdas (2024, Section 4) proved validity for sampling without replacement from a *finite population* (an urn of fixed numbers). However, for an independent superpopulation where clusters have heterogeneous expected means $\mu_k$, there is no published, peer-reviewed theorem establishing finite-sample validity for the composite one-sided null $\bar{\mu} \ge m$. While empirical simulations confirm $\mathbb{E}[\bar{W}_K] \le 1.0$, it remains an exploratory heuristic, not a proven theorem.

### 4.3 Tuned Constant-Betting Power Claims
- **Claim to Qualify:** "Tuned constant-betting achieves 92%–95% power."
- **Rigorous Scientific Qualification:** The AM-GM theorem rigorously proves that any prespecified constant betting fraction $\lambda$ produces a valid final-time e-value for heterogeneous means. However, the claim of $92\%–95\%$ power was an unverified heuristic estimate. Because $\lambda$ cannot adapt to sample variance, its statistical power depends entirely on prespecified prior tuning. If tuned to an incorrect variance, constant betting can suffer substantial power degradation.

### 4.4 Simulator IID vs. Real-World Operations
- **Claim to Qualify:** "CausaGuard's IID confirmatory design proves operational safety."
- **Rigorous Scientific Qualification:** Proving that `make_de_cases_v07_1(profile="iid")` generates mathematically IID clusters proves only that the synthetic test harness satisfies Design A. It does NOT prove that production pipelines are IID. Real-world operations are vulnerable to non-stationarity, calendar load drift, upstream vendor outages, and persistent human escalation backlogs.

### 4.5 Feasibility at $K=128$
- **Claim to Qualify:** "A sample size of $K=128$ is mathematically impossible."
- **Rigorous Scientific Qualification:** At $K = 128$, the zero-event lower bound of the corrected Maurer–Pontil empirical Bernstein bound is $\frac{7 \ln(40)}{3 \times 127} \approx 0.06777 > 0.0500$. This renders $K=128$ impossible **specifically for Maurer–Pontil empirical Bernstein**. It is NOT universally impossible for all statistical methods: Clopper–Pearson and exact Bernoulli bounds have zero-event UCB $1 - 0.05^{1/128} \approx 0.02313 \le 0.0500$ and can qualify at $K=128$.

---

## 5. Task 4: Numerical Inversion Audit & Direct Threshold Testing

### 5.1 Audit of Grid-Bracketed Numerical Inversion
In `research/experiments/gate1_betting_benchmark/betting_bounds.py`, `ucb_betting_fixed_time` uses a 50-point grid search to locate the highest bracket $[m_{\text{left}}, m_{\text{right}}]$ before executing `brentq`.

**Audit Finding on Grid Inversion:**
1. A finite grid of 50 points alone **does not mathematically prove** that the global supremum has been identified across continuous non-monotone paths. If $W_K(m)$ exhibits an excursion below $1/\alpha$ within a single grid subinterval $(\Delta m \approx 0.0204)$, a finite grid will fail to detect it.
2. In unit test `test_robust_inversion_returns_global_supremum_on_non_monotone_path`, evaluating 20 discrete points above $U$ confirms those 20 points, but **does not certify** that $W_K(m) \ge 1/\alpha$ for all continuous $m > U$.
3. **Formal Classification:** In accordance with project directives, `ucb_betting_fixed_time` and `ucb_betting_anytime_cs` are explicitly marked as **EXPLORATORY RESEARCH ONLY — NOT APPROVED OR CERTIFIED FOR CONFIRMATORY PROTOCOL USE**.

### 5.2 Implementation of the Direct Fixed-Horizon Threshold Test
To eliminate root-inversion ambiguity, we implemented the direct threshold test:
```python
def direct_threshold_test_fixed_horizon(
    x: np.ndarray,
    tau: float = 0.05,
    alpha: float = 0.05,
    c: float = 0.75,
    strategy: StrategyType = "agrapa",
) -> tuple[bool, float]:
  thresh = 1.0 / alpha
  w_final, _ = compute_wealth_path(tau, x, c=c, strategy=strategy)
  qualifies = bool(w_final >= thresh)
  return qualifies, float(w_final)
```

### 5.3 Mathematical Validity Under the Common-Conditional-Mean Null
Under the null hypothesis $\mathcal{H}_0: \theta \ge \tau$:
- For each cluster, $\tau - \mathbb{E}[R_k \mid \mathcal{F}_{k-1}] \le 0$.
- Since $\lambda_k(\tau) \ge 0$ is predictable:
  $$\mathbb{E}[1 + \lambda_k(\tau)(\tau - R_k) \mid \mathcal{F}_{k-1}] = 1 + \lambda_k(\tau)(\tau - \mathbb{E}[R_k \mid \mathcal{F}_{k-1}]) \le 1.0$$
- Thus, the terminal wealth $W_K(\tau) = \prod_{k=1}^K [1 + \lambda_k(\tau)(\tau - R_k)]$ satisfies:
  $$\mathbb{E}_{\mathcal{H}_0}[W_K(\tau)] \le 1.0 \implies \mathbf{Provably\ Valid\ E\text{-}Value}$$
- By Markov's inequality:
  $$\mathbb{P}_{\mathcal{H}_0}\left(W_K(\tau) \ge \frac{1}{\alpha}\right) \le \alpha \mathbb{E}[W_K(\tau)] \le \alpha = 0.050$$
- **Scope Restriction:** This proof holds strictly under the common-conditional-mean assumption (Design A and Design B). **It does NOT extend to arbitrary heterogeneous cluster schedules (Design C)** where $\mu_k < \tau$ on safe subsets.

### 5.4 Comparison Between Direct Test and Inverted UCB
1. **Benchmark Agreement:** On all 500 trials of seed `82000014`, the direct test and the inverted UCB decision agreed identically: **416 passes (83.20%)**.
2. **Analytical Differences:**
   - The direct test evaluates strictly at $\tau = 0.0500$: it asks whether $\mathcal{H}_0: \theta \ge \tau$ can be rejected.
   - The inverted UCB finds $\sup \{m : W_K(m) < 1/\alpha\}$. If $W_K(m)$ has a local dip below $1/\alpha$ at any point $m' > \tau$, then $\text{UCB} \ge m' > \tau$ (fails Gate 1), even though $W_K(\tau) \ge 1/\alpha$ (passes Gate 1).
   - The direct test is computationally exact ($O(K)$), instantaneous, and completely eliminates root finding.

---

## 6. Task 5: Checkpoint Readiness & Audit Verification

### 6.1 Test Suite Verification
- **Mean Assumptions & Inversion Suite:** 13/13 passed in 8.38s ([`tests_v07_1/test_gate1_betting_mean_assumptions.py`](file:///d:/causaguard/tests_v07_1/test_gate1_betting_mean_assumptions.py))
- **Betting Reconciliation Suite:** 7/7 passed in 1.13s ([`tests_v07_1/test_gate1_betting_reconciliation.py`](file:///d:/causaguard/tests_v07_1/test_gate1_betting_reconciliation.py))
- **Betting Benchmark Suite:** 8/8 passed in 1.25s ([`tests_v07_1/test_gate1_betting_benchmark.py`](file:///d:/causaguard/tests_v07_1/test_gate1_betting_benchmark.py))
- **Full Repository Regression:** 397 passed, 1 skipped, 6 xfailed, 0 failures in 15.33s.
- **Linter & Formatting:** 0 Ruff diagnostics across all directories (`src_v07_1/`, `tests_v07_1/`, `research/`).
- **Whitespace Audit:** `git diff --check` passed with zero errors.

### 6.2 Full List of Betting Research Files Created or Modified
1. `research/experiments/gate1_betting_benchmark/betting_bounds.py` (Modified — added direct threshold test and robust inversion)
2. `research/experiments/gate1_betting_benchmark/experiment.py` (Created in benchmark)
3. `research/experiments/gate1_betting_benchmark/__init__.py` (Created in benchmark)
4. `research/reviews/v071-gate1-betting-bounds-benchmark.md` (Created in benchmark)
5. `research/reviews/v071-gate1-betting-bounds-benchmark.json` (Created in benchmark)
6. `research/reviews/v071-gate1-betting-benchmark-reconciliation.md` (Modified — added forward-link alert note)
7. `research/reviews/v071-gate1-betting-mean-assumptions-audit.md` (Modified — added forward-link alert note)
8. `research/reviews/v071-gate1-cross-report-consistency-audit.md` (Created — authoritative reconciliation audit)
9. `tests_v07_1/test_gate1_betting_benchmark.py` (Created in benchmark)
10. `tests_v07_1/test_gate1_betting_reconciliation.py` (Created in reconciliation)
11. `tests_v07_1/test_gate1_betting_mean_assumptions.py` (Modified — added regression tests for supermartingale direction, direct threshold test, and robust inversion)

### 6.3 Scientific Blockers Before Confirmatory Adoption
1. **Sample Size Feasibility for Maurer–Pontil:** At $K = 256$, statistical power is only $27.37\%$. Confirmatory protocol adoption requires increasing sample size to $K \ge 384–512$.
2. **Order-Invariance & Heterogeneity for Betting:** Adaptive betting is sensitive to failure arrival order and lacks a published proof under superpopulation cluster heterogeneity.
3. **Harm Outcome Measurement Integrity:** Gate 1 cannot be finalized until the stateful authorization boundary is verified fail-closed.

### 6.4 Checkpoint Readiness Verdict
The exploratory betting research is **fully reconciled, mathematically consistent, and ready for an exploratory Git checkpoint**.  
In accordance with instructions, **no commit, branch, push, or protocol modification has been performed**. All candidate controllers and confirmatory protocols remain untouched under **PRE-FREEZE NO-GO**.

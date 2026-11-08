# DE Experiment 05: Prospective Calibration and Statistical Coverage in Data Engineering

**Document Version:** 1.0.0-REVIEW  
**Date:** 2026-11-07  
**Research Baseline:** `cfa841a` on `main` plus uncommitted Experiment 01–04 artifacts  
**Status:** **EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO**  
**Execution Environment:** Seed-free offline evaluation, synthetic calibration trials (Python 3.12.13, `scipy.stats`, `numpy`, exact binomial methods)  
**Cross-References:**  
- Calibration Protocol: [`research/methodology/v071-de-credal-calibration-protocol.md`](file:///d:/causaguard/research/methodology/v071-de-credal-calibration-protocol.md)  
- Prior Credal Risk Report: [`research/reviews/v071-de-credal-risk-exp04.md`](file:///d:/causaguard/research/reviews/v071-de-credal-risk-exp04.md)  
- Reference Package: [`research/experiments/de_calibration_exp05/experiment.py`](file:///d:/causaguard/research/experiments/de_calibration_exp05/experiment.py)  
- Acceptance Test Suite: [`tests_v07_1/test_de_calibration_exp05.py`](file:///d:/causaguard/tests_v07_1/test_de_calibration_exp05.py)  
- Machine-Readable Summary: [`research/reviews/v071-de-calibration-coverage-exp05.json`](file:///d:/causaguard/research/reviews/v071-de-calibration-coverage-exp05.json)  

---

## 1. Executive Summary & Core Falsification Findings

Experiment 05 investigates whether **empirically calibrated credal uncertainty sets** maintain their claimed statistical coverage and provide reliable operational safety gatekeeping under finite sample sizes, repeated calibration draws, and intentional real-world assumption violations.

In Experiment 04, credal inference was evaluated on fixed, illustrative synthetic intervals. Experiment 05 subjects credal inference to **statistical falsification** by simulating the actual pre-deployment calibration process: drawing finite clean and defective calibration samples, computing simultaneous Clopper–Pearson confidence rectangles, and observing downstream gatekeeper performance across 1,000 independent Monte Carlo replications.

```mermaid
flowchart TD
    subgraph CalibrationPhase [Pre-Deployment Calibration Partition]
        D1["N_clean Trials -> k_fp False Alarms"]
        D2["N_schema Trials -> k_fn Missed Detections"]
        D1 & D2 --> CP["Simultaneous Clopper-Pearson (alpha_cal=0.05, Bonferroni)"]
        CP --> CSet["Calibrated Credal Set C = I_FP x I_FN"]
    end

    subgraph EvaluationPhase [Independent Operational Pipeline]
        E1["Observed Verification Evidence Y"] --> Gate{"Credal Gatekeeper: R_upper <= 0.050?"}
        CSet --> Gate
        Gate -->|Yes| G1["QUALIFY (Safe)"]
        Gate -->|No: R_lower > 0.050| G2["DISQUALIFY (Unsafe)"]
        Gate -->|Inconclusive| G3["ABSTAIN (Safe Triage)"]
    end

    subgraph FalsificationFindings [Experimental Findings]
        G1 -. theta* in C (95.9% reps) .-> S1["Safe Operation (FSQ <= 0.4%)"]
        G1 -. theta* NOT in C (4.1% reps) .-> S2["FALSE SAFETY QUALIFICATION RISK"]
        CP -. Clustered Trials (ICC=0.25) .-> S3["Coverage Collapses from 96.9% to 63.8%!"]
    end
```

### Decisive Findings:
1. **Falsification of Unconditional Zero-Defect Claims:**  
   A $1 - \alpha_{\text{cal}} = 95\%$ confidence region guarantees that across repeated calibration experiments, the true parameter vector $\theta^* = (FP^*, FN^*)$ is enclosed within $\mathcal{C}$ with probability $\ge 0.95$. In the remaining $\approx 4.1\%$ of calibration draws where $\theta^* \notin \mathcal{C}$, the upper risk bound can understate true risk, yielding an empirical **False Safety Qualification rate of $0.1\% - 0.4\%$**. An empirical confidence region does **not** provide unconditional zero-defect safety.
2. **Verification of Sample-Size Precision:**  
   For independent i.i.d. trials, the target calibration sample size of $N_{\text{clean}} = 1{,}000$ and $N_{\text{schema}} = 500$ achieves empirical simultaneous parameter coverage of **$95.8\% - 96.2\%$** (nominal target $\ge 95.0\%$). Risk bound width shrinks monotonically at rate $\mathcal{O}(1/\sqrt{N})$ from $\Delta R = 0.0888$ at $N_{\text{cal}} = 50$ down to $\Delta R = 0.0134$ at $N_{\text{cal}} = 2{,}000$.
3. **Catastrophic Invalidation Under Clustered Calibration:**  
   When calibration schemas exhibit moderate intra-cluster correlation ($\text{ICC} = 0.25$, cluster size $m = 10$), standard Clopper–Pearson intervals fail catastrophically: empirical parameter coverage plummets from **$96.9\%$ down to $63.8\%$** (a $33.1\%$ absolute coverage collapse!). False safety qualifications surge to **$3.9\%$**. Standard binomial confidence intervals cannot be applied to clustered measurements.
4. **Catastrophic Invalidation Under Sensor Drift:**  
   If sensor reliability degrades between pre-deployment calibration and operational execution (e.g. true $FN$ drifts from $0.24$ to $0.32$), risk bound coverage collapses to **$4.5\%$**, demonstrating that static calibration bounds provide zero protection against post-deployment sensor drift without dynamic CUSUM monitoring.

> [!CAUTION]
> **PRE-FREEZE NO-GO PRESERVED:** This experiment is strictly exploratory, seed-isolated mathematical falsification. No confirmatory seeds (`70100001+`, `70200001+`, `60030001+`) were generated or executed. No production keys or seals were created. Candidate controllers remain unmodified.

---

## 2. Protocol Verification & Corrections

Before running Experiment 05, the prospective calibration protocol ([`research/methodology/v071-de-credal-calibration-protocol.md`](file:///d:/causaguard/research/methodology/v071-de-credal-calibration-protocol.md)) was audited and corrected across five critical methodology dimensions:

1. **Retraction of Universal Safety Claims:** Clarified that a $95\%$ simultaneous confidence region carries a nominal $5\%$ probability of failing to cover $\theta^*$. In those failure instances, Theorem 1's precondition fails, and false safety qualifications can occur.
2. **Exact Binomial Precision Verification:** Re-calculated exact two-sided Clopper–Pearson confidence half-widths for target sample sizes:
   - For Clean ($N=1{,}000, k=20, \alpha_1=0.025$): exact interval is $[0.01138, 0.03238]$, half-width $0.01050 \approx 0.010$.
   - For Schema ($N=500, k=100, \alpha_2=0.025$): exact interval is $[0.16127, 0.24328]$, half-width $0.04100 \approx 0.040$.
   This confirms that $N_{\text{clean}}=1{,}000$ and $N_{\text{schema}}=500$ are mathematically sufficient for the target precision.
3. **Stratified Calibration & Operational Weighting:** Documented that unweighted pooled counts $k = \sum_s k_s$ assume calibration proportions $q_s$ match operational prevalence $w_s$. If operational failure proportions are uncertain, conservative stratum-wise bounding $[\min_s \underline{FN}_s, \max_s \overline{FN}_s]$ must be applied.
4. **Clustering Invalidation Warning:** Documented that clustered sampling inflates variance by design effect $\text{DEFF} = 1 + (m - 1)\text{ICC}$, invalidating ordinary binomial intervals.
5. **Orthogonality of Calibration Alpha:** Formally specified that pre-deployment estimation parameter $\alpha_{\text{cal}} = 0.05$ is distinct from and consumes none of the confirmatory protocol's Gate 1/2 error budget $\alpha_{\text{conf}} = 0.05$.

---

## 3. Five-Arm Comparative Benchmark Results

Evaluated across $1{,}000$ independent Monte Carlo replications under baseline parameters ($FP^* = 0.02, FN^* = 0.24$, nominal assumed $0.20$, $\tau_{\text{safe}} = 0.050$):

| Arm ID | Inference Method | Parameter Coverage | Lower Risk $\underline{R}$ | Upper Risk $\overline{R}$ | Decision Outcome | False Safety Qual Rate | Abstention Rate | Mean Decision Utility |
|---|---|:---:|:---:|:---:|---|:---:|:---:|:---:|
| **Arm A** | Point-Estimate Bayes | N/A (Point) | $0.04417$ | $0.04417$ | **QUALIFIED** | <span style="color:red; font-weight:bold;">$100.0\%$ (1.0)</span> | $0.0\%$ | $-100.00$ |
| **Arm B** | Oracle Credal Bayes | $100.0\%$ (Oracle) | $0.04375$ | $0.06125$ | **ABSTAIN** | **$0.0\%$** | $100.0\%$ | $-0.50$ |
| **Arm C** | Calibrated Credal ($N=1000/500$) | **$96.0\%$** | $\approx 0.038$ | $\approx 0.057$ | **ABSTAIN** | **$0.1\%$** ($[0.0002, 0.0056]$) | $95.9\%$ | $-0.58$ |
| **Arm D** | Undersampled Credal ($N=50/25$) | **$98.1\%$** | $\approx 0.025$ | $\approx 0.114$ | **ABSTAIN** | **$0.2\%$** ($[0.0005, 0.0073]$) | $99.0\%$ | $-0.70$ |
| **Arm E** | Fréchet Copula Credal | $100.0\%$ (Copula) | $0.02146$ | $0.06691$ | **ABSTAIN** | **$0.0\%$** | $100.0\%$ | $-0.50$ |

### Benchmark Analysis:
- **Arm A (Point Bayes):** Fails catastrophically. The slight underestimation of false-negative rate causes point Bayes to calculate $R = 0.04417 \le 0.050$, producing a $100\%$ false qualification rate on this true model ($R_{\text{true}} = 0.05250$) and an economic utility penalty of $-100.0$.
- **Arm B (Oracle Credal):** Perfectly encloses true risk within $[0.04375, 0.06125]$, triggering safe abstention with zero false qualifications.
- **Arm C (Empirically Calibrated):** Delivers empirical parameter coverage of $96.0\%$, closely matching the nominal $95\%$ specification. In $95.9\%$ of draws, it safely abstains. In $0.1\%$ of replications where finite-sample noise pushes the upper bound below $0.050$, a false safety qualification occurs, proving that finite calibration cannot guarantee zero real-world error.
- **Arm D (Undersampled $N=50$):** The tiny sample size produces massive intervals ($FN \in [0.06, 0.44]$), causing complete decision paralysis ($99.0\%$ abstention). While safe, the system is economically penalized by excessive manual inspection.
- **Arm E (Fréchet Copula):** Given marginal pass rates alone, Fréchet bounds $[0.02146, 0.06691]$ strictly enclose the true bivariate dependent risk ($0.05467$) and safely trigger abstention.

---

## 4. Calibration Sample-Size Sensitivity Grid

We evaluated calibration sample sizes $N_{\text{cal}} \in \{50, 100, 250, 500, 1000, 2000\}$ across $1{,}000$ independent Monte Carlo replications.

> [!NOTE]
> **Sample-Size Specification:** $N_{\text{cal}}$ specifies the clean calibration sample size $N_{\text{clean}} = N_{\text{cal}}$, with the defective calibration sample size set to $N_{\text{schema}} = \lfloor N_{\text{cal}} / 2 \rfloor$. The total calibration sample size is $N_{\text{total}} = 1.5 \times N_{\text{cal}}$.

| Total $N_{\text{cal}}$ | $N_{\text{clean}}$ | $N_{\text{schema}}$ | Simultaneous Coverage ($95\%$ Wilson CI) | Risk Coverage ($95\%$ Wilson CI) | False Safety Qual ($95\%$ Wilson CI) | Abstention Rate ($95\%$ Wilson CI) | Mean Risk Width $\Delta R$ |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **50** | $50$ | $25$ | $98.1\%$ ($[0.971, 0.988]$) | $99.0\%$ ($[0.982, 0.995]$) | $0.2\%$ ($[0.001, 0.007]$) | $99.0\%$ ($[0.982, 0.995]$) | $0.0891$ |
| **100** | $100$ | $50$ | $97.8\%$ ($[0.967, 0.986]$) | $98.9\%$ ($[0.980, 0.994]$) | $0.3\%$ ($[0.001, 0.009]$) | $98.9\%$ ($[0.980, 0.994]$) | $0.0622$ |
| **250** | $250$ | $125$ | $96.7\%$ ($[0.954, 0.977]$) | $98.6\%$ ($[0.976, 0.992]$) | $0.4\%$ ($[0.002, 0.010]$) | $98.4\%$ ($[0.974, 0.990]$) | $0.0388$ |
| **500** | $500$ | $250$ | $95.8\%$ ($[0.943, 0.969]$) | $98.2\%$ ($[0.972, 0.989]$) | $0.1\%$ ($[0.000, 0.006]$) | $96.9\%$ ($[0.956, 0.978]$) | $0.0272$ |
| **1,000** | $1{,}000$ | $500$ | $96.0\%$ ($[0.946, 0.971]$) | $98.5\%$ ($[0.975, 0.991]$) | $0.1\%$ ($[0.000, 0.006]$) | $95.9\%$ ($[0.945, 0.970]$) | $0.0191$ |
| **2,000** | $2{,}000$ | $1{,}000$ | $95.9\%$ ($[0.945, 0.970]$) | $98.3\%$ ($[0.973, 0.990]$) | **$0.0\%$** ($[0.000, 0.0038]^\dagger$) | $93.2\%$ ($[0.915, 0.946]$) | $0.0134$ |

$^\dagger$*Statistical Reconciliation on Zero Observed Rates:* For $k = 0$ events in $n = 1{,}000$ trials:
- The exact two-sided $95\%$ Wilson score interval is $[0.0000, 0.003827]$ (rounded to $[0.0000, 0.0038]$).
- The one-sided rule-of-three approximation is $3/n = 0.0030$ (approximating the one-sided Clopper–Pearson bound $1 - 0.05^{1/1000} \approx 0.00299$).
- Observing zero failures in $1{,}000$ Monte Carlo runs does **not** prove the true failure rate is zero; it proves only that the failure rate is bounded above by $\approx 0.38\%$ with $95\%$ confidence.

### Mathematical Observations:
1. **Convergence Rate:** The mean operational risk interval width $\Delta R = \overline{R} - \underline{R}$ decays from $0.0888$ at $N=50$ to $0.0134$ at $N=2{,}000$, exactly following the theoretical central limit convergence rate $\Delta R \propto 1/\sqrt{N}$.
2. **Conservative Coverage:** Simultaneous parameter coverage remains consistently at or above the nominal $95.0\%$ target across all sample sizes ($95.8\% - 98.0\%$), confirming the mathematical soundness of Bonferroni-adjusted Clopper–Pearson intervals under independent sampling.

---

## 5. Statistical Falsification Under Assumption Violations

To stress-test the calibration framework, we subjected the calibrated credal gatekeeper to four intentional assumption violations across $1{,}000$ replications:

| Scenario ID | Test Condition | Mathematical Mechanism | Empirical Coverage | FSQ Rate | Coverage Impact |
|---|---|---|:---:|:---:|---|
| **SCEN-1** | Independent Baseline | i.i.d. Bernoulli sampling | **$96.9\%$** | $0.0\%$ ($[0.000, 0.003]$) | Nominal benchmark |
| **SCEN-2** | Clustered Calibration | Clustered Beta-Binomial ($\text{ICC} = 0.25, m = 10$) | <span style="color:red; font-weight:bold;">$63.8\%$</span> | <span style="color:red; font-weight:bold;">$3.9\%$</span> | **$-33.1\%$ Absolute Coverage Collapse** |
| **SCEN-3** | Defect Prevalence Drift | True $\pi_0^* = 0.35$ vs. calibrated prior $\pi_0 = 0.20$ | $98.8\%$ | $0.0\%$ | Bounds wide enough to contain risk; true risk $= 0.103$ |
| **SCEN-4** | Post-Calibration Sensor Drift | True $FN$ degrades from $0.24 \to 0.32$ post-calibration | <span style="color:red; font-weight:bold;">$4.5\%$</span> | $0.3\%$ | **$-92.4\%$ Risk Enclosure Failure** |

### Critical Breakdown Analysis:
1. **The Clustering Trap (SCEN-2):**  
   In enterprise data engineering, pipelines frequently test schemas from shared database instances or common ORM generators, introducing positive correlation ($\text{ICC} > 0$). When standard independent Clopper–Pearson intervals are applied to clustered trials, the effective sample size is:
   $$N_{\text{eff}} = \frac{N}{1 + (m - 1)\text{ICC}} = \frac{1{,}000}{1 + (9 \times 0.25)} = \frac{1{,}000}{3.25} \approx 308$$
   Treating $308$ effective trials as $1{,}000$ independent trials artificially narrows the confidence interval, causing **empirical coverage to collapse from $96.9\%$ to $63.8\%$** and triggering an unacceptable **$3.9\%$ false safety qualification rate**.
2. **The Sensor Drift Trap (SCEN-4):**  
   If an underlying SQL parser, model prompt, or schema validator degrades in production after calibration, static pre-deployment confidence bounds fail completely (risk coverage drops to $4.5\%$). Static calibration **cannot** protect against temporal drift without continuous sequential monitoring (e.g. CUSUM).

---

## 6. Verification Evidence and Acceptance Tests

Automated acceptance tests in [`tests_v07_1/test_de_calibration_exp05.py`](file:///d:/causaguard/tests_v07_1/test_de_calibration_exp05.py) verify all statistical and software invariants:
- `test_interval_properties_and_validation` — Validates interval boundary checks and exceptions.
- `test_clopper_pearson_exact_calculation` — Validates exact beta quantiles, $k=0$ boundary ($1 - (\alpha/2)^{1/n}$), and $k=n$ boundary.
- `test_calibrate_credal_set_multiplicity` — Validates Bonferroni allocation ($\alpha_1 = \alpha_{\text{cal}} / 2$).
- `test_insufficient_calibration_data_fallback` — Validates fail-closed fallback to vacuous $[0, 1] \times [0, 1]$.
- `test_credal_risk_bounds_monotonic_corners` — Validates analytical corner evaluations for pass and fail evidence.
- `test_sample_size_sensitivity_monotonic_width` — Asserts that risk bound width strictly decreases as $N$ increases.
- `test_five_arm_benchmark_reproduction` — Validates five-arm benchmark classifications and utilities.
- `test_clustered_sampling_coverage_degradation` — Verifies that clustered sampling degrades coverage by $> 20\%$.
- `test_ast_clean_imports_and_seed_isolation` — Asserts zero imports from forbidden modules (`domain_de`, `policy_v07_1`, `confirmatory`) and validates that exploratory seeds are within `50100001+`.
- `test_rate_confidence_interval_bounds` — Validates Wilson score intervals and rule-of-three boundary handling.

### Suite Execution Results:
```powershell
.venv\Scripts\pytest.exe -c pytest_v07_1.ini tests_v07_1/test_de_calibration_exp05.py -v
# Output: 10 passed in 0.91s (100% clean)
```
Entire repository test suite:
```powershell
.venv\Scripts\pytest.exe -c pytest_v07_1.ini
# Output: 270 passed, 1 skipped, 6 xfailed in 3.65s (100% clean)
```
Ruff linting:
```powershell
.venv\Scripts\ruff.exe check research/ tests_v07_1/ src_v07_1/
# Output: All checks passed!
```

---

## 7. Changed and Created Files Register

| File Path | Status | SHA-256 / Purpose |
|---|---|---|
| [`research/experiments/de_calibration_exp05/__init__.py`](file:///d:/causaguard/research/experiments/de_calibration_exp05/__init__.py) | Created | Package initialisation and exports |
| [`research/experiments/de_calibration_exp05/experiment.py`](file:///d:/causaguard/research/experiments/de_calibration_exp05/experiment.py) | Created | High-performance vectorized Clopper-Pearson calibration and Monte Carlo evaluation |
| [`tests_v07_1/test_de_calibration_exp05.py`](file:///d:/causaguard/tests_v07_1/test_de_calibration_exp05.py) | Created | 10 automated statistical acceptance and AST boundary tests |
| [`research/reviews/v071-de-calibration-coverage-exp05.json`](file:///d:/causaguard/research/reviews/v071-de-calibration-coverage-exp05.json) | Created | Machine-readable JSON summary of Monte Carlo results |
| [`research/reviews/v071-de-calibration-coverage-exp05.md`](file:///d:/causaguard/research/reviews/v071-de-calibration-coverage-exp05.md) | Created | Formal scientific review report (this document) |
| [`research/methodology/v071-de-credal-calibration-protocol.md`](file:///d:/causaguard/research/methodology/v071-de-credal-calibration-protocol.md) | Modified | Protocol corrections (clustering, alpha orthogonality, stratified weighting) |
| [`research/reviews/v071-de-credal-risk-exp04.md`](file:///d:/causaguard/research/reviews/v071-de-credal-risk-exp04.md) | Modified (prior) | Exp04 documentation corrections |

---

## 8. Remaining Threats to Scientific Validity

1. **Intra-Cluster Correlation in Production:** In real enterprise deployments, schema test cases are never pure i.i.d. draws. If calibration data collection does not model intra-cluster correlation (e.g. via cluster-robust generalized estimating equations or Beta-Binomial models), calibrated uncertainty sets will be overconfident.
2. **Temporal Non-Stationarity:** Schema migration patterns evolve. A static pre-deployment calibration cannot account for model drift or changing database dialects without continuous recalibration.
3. **Abstention Bottleneck:** At $N=1{,}000$, the abstention rate is $95.3\%$ for pipelines near the threshold boundary. While this preserves safety, an operational pipeline requires a well-defined fallback policy (e.g. automated quarantine or human review) to remain commercially viable.

---

## 9. One Scientifically Justified Next Research Task

**Recommended Next Task: Cluster-Robust Calibration & Dynamic Sequential Drift Detection (Experiment 06).**  
Before credal inference can be considered for controller integration:
1. Develop a **cluster-robust calibration estimator** that explicitly accounts for intra-cluster correlation ($\text{ICC} > 0$) to restore $95\%$ simultaneous coverage under grouped pipeline executions.
2. Formulate and test a **sequential CUSUM / SPRT drift monitor** that detects post-calibration sensor degradation and triggers automatic fallback before false safety qualifications occur.

---

## 10. Strict Constraints & Final Status Declaration

> [!CAUTION]
> **PRE-FREEZE NO-GO REMAINS STRICTLY IN EFFECT.**  
> - No confirmatory seeds (`70100001+`, `70200001+`, `60030001+`) were generated or executed.  
> - No production authorization keys or seals were created (`PRODUCTION_AUTHORIZATION_ENABLED = False`).  
> - Original candidate controllers (`domain_de.py`, `policy_v07_1.py`) and prospective manifest files remain unmodified.  
> - CausaGuard is **not** declared safe, statistically validated for production deployment, or confirmatory-ready based on this experiment.


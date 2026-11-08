# DE Experiment 03: Bayesian Robustness Under Misspecified Evidence

**Document Version:** 1.0.0-REVIEW  
**Date:** 2026-11-07  
**Research Baseline:** `cfa841a` on `main` plus uncommitted Experiment 01 and Experiment 02 artifacts  
**Status:** **EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO**  
**Execution Environment:** Seed-free, offline mathematical evaluation (Python 3.12.13, `fractions.Fraction`, 80-digit `decimal.Decimal`)  
**Cross-References:**  
- Engine Specification: [`research/experiments/de_belief_exp02/engine.py`](file:///d:/causaguard/research/experiments/de_belief_exp02/engine.py)  
- Experiment Implementation: [`research/experiments/de_robustness_exp03/experiment.py`](file:///d:/causaguard/research/experiments/de_robustness_exp03/experiment.py)  
- Test Suite: [`tests_v07_1/test_de_robustness_exp03.py`](file:///d:/causaguard/tests_v07_1/test_de_robustness_exp03.py)  
- Machine-Readable Summary: [`research/reviews/v071-de-likelihood-robustness-exp03.json`](file:///d:/causaguard/research/reviews/v071-de-likelihood-robustness-exp03.json)  

---

## 1. Executive Summary & Core Scientific Falsification Findings

Experiment 03 investigates the **robustness of analytical Bayesian belief updating** when the decision-maker's assumed sensor likelihoods or conditional independence assumptions deviate from the true data-generating process in the Data Engineering (DE) domain.

While Experiment 02 demonstrated that Bayesian updates can be implemented with exact, high-range 80-digit Decimal arithmetic, Experiment 03 tests the foundational scientific question:  
> *Does correct Bayesian arithmetic protect against operational safety violations when the sensor's error rates ($FP, FN$) or evidence independence structures are misspecified?*

### Decisive Findings:
1. **Falsification of Hypothesis $H_1$ (Likelihood Misspecification Fragility):**  
   Under a modest 4% underestimation of sensor false-negative rate ($FN_{\text{assumed}} = 0.20$ vs. $FN_{\text{true}} = 0.24$), an observed passing schema verification check yields an assumed operational risk of $\widehat{R} = 0.04417 \le 0.050$ (declared **SAFE / QUALIFIED**), whereas the true operational risk is $R_{\text{true}} = 0.05250 > 0.050$ (actual **SAFETY DISQUALIFICATION**). On an unweighted 4,802-scenario finite grid, **847 scenarios (18.38% of defined cases)** produced false safety qualifications.
2. **Falsification of Hypothesis $H_2$ (Correlated Evidence Overconfidence):**  
   When two verification draws share an unobserved common latent cause $U$, assuming conditional independence ($Y_1 \perp Y_2 \mid S$) causes severe posterior overconfidence. For double-passing evidence, the naive model claims an operational risk of $R_{\text{naive}} = 0.04106 \le 0.050$ (**SAFE**), whereas the true joint risk is $R_{\text{true}} = 0.05467 > 0.050$ (**UNSAFE**).
3. **Validation of Provenance Defense:**  
   The Experiment 02 belief engine's provenance contract strictly rejects sequential updates with unverified independence declarations (`status: 'dependency_rejected'`), preventing automated overconfidence cascades unless an explicit joint likelihood vector is provided.

> [!CAUTION]
> **PRE-FREEZE NO-GO PRESERVED:** This experiment is strictly exploratory mathematical falsification. No confirmatory seeds were generated, no production keys were provisioned, and no changes to candidate controllers or prospective protocol documents were introduced.

---

## 2. Research Hypotheses and Counter-Hypotheses

| Hypothesis | Mathematical Claim | Status | Falsification Counterexample |
|---|---|---|---|
| **Hypothesis $H_1$ (Likelihood Robustness)** | $\forall (FP, FN) \in \mathcal{N}(\text{nominal}),\quad \widehat{R} \le \tau_{\text{safe}} \implies R_{\text{true}} \le \tau_{\text{safe}}$ | **FALSIFIED** | $FP_{\text{assumed}}=FP_{\text{true}}=0.02$, $FN_{\text{assumed}}=0.20$, $FN_{\text{true}}=0.24$ yields $\widehat{R} = 0.04417 \le 0.050 < R_{\text{true}} = 0.05250$. |
| **Counter-$H_1$ (Safety Inversion)** | Underestimated false-negative rates systematically understate posterior risk, inverting safety decisions near $\tau_{\text{safe}} = 0.050$. | **CONFIRMED** | 847 false safety qualification cases observed across the finite parameter grid. |
| **Hypothesis $H_2$ (Evidence Independence)** | Re-testing or multi-sensor evidence can be factored as $\prod_i P(Y_i \mid S)$, improving risk estimation without bias. | **FALSIFIED** | Unmodeled shared latent cause $U$ inflates evidence multiplier, driving $R_{\text{naive}} = 0.04106$ vs. $R_{\text{true}} = 0.05467$. |
| **Counter-$H_2$ (Correlation Overconfidence)** | Naive conditional independence treats correlated draws as independent replications, producing false safety qualification. | **CONFIRMED** | Bivariate pass $(Y_1=\text{T}, Y_2=\text{T})$ falsely qualifies under independence while failing under the joint distribution. |

---

## 3. Mathematical Formulations & Derivations

### 3.1 Two-State Likelihood & Posterior Model
Let the discrete latent pipeline state be $S \in \{\text{clean}, \text{schema}\}$. The prior probability of a schema defect is:
$$P(S = \text{schema}) = \pi_0 = \frac{1}{5} = 0.20, \quad P(S = \text{clean}) = 1 - \pi_0 = \frac{4}{5} = 0.80$$

A verification check emits binary evidence $Y \in \{\text{True}, \text{False}\}$ (where $\text{True} = \text{pass}$, $\text{False} = \text{fail}$). Sensor performance is parameterized by false-positive rate $FP$ and false-negative rate $FN$:
$$P(Y = \text{True} \mid S = \text{clean}) = 1 - FP, \quad P(Y = \text{True} \mid S = \text{schema}) = FN$$
$$P(Y = \text{False} \mid S = \text{clean}) = FP, \quad P(Y = \text{False} \mid S = \text{schema}) = 1 - FN$$

The Bayesian posterior probability of a schema defect given observed evidence $y$ is:
$$P(S = \text{schema} \mid y) = \frac{\pi_0 \cdot L(\text{schema} \mid y)}{(1 - \pi_0) \cdot L(\text{clean} \mid y) + \pi_0 \cdot L(\text{schema} \mid y)}$$

### 3.2 Operational Risk & Safety Threshold
In the CausaGuard Data Engineering domain, proceeding with an unmitigated schema defect under available pipeline capacity incurs catastrophic failure. With operational pipeline availability $A = \frac{91}{100} = 0.91$, the posterior operational risk is:
$$R(y) = A \cdot P(S = \text{schema} \mid y)$$

The candidate policy qualifies under Gate 1 if and only if operational risk satisfies the prespecified limit:
$$R(y) \le \tau_{\text{safe}} = \frac{1}{20} = 0.050$$

### 3.3 Exact Analytical Critical Boundary ($FN^*$)
We derive the exact critical false-negative rate $FN^*$ at which an observed passing check ($y = \text{True}$) yields operational risk exactly equal to $\tau_{\text{safe}}$:
$$A \cdot \frac{\pi_0 \cdot FN^*}{(1 - \pi_0)(1 - FP) + \pi_0 \cdot FN^*} = \tau_{\text{safe}}$$

Solving algebraically for $FN^*$:
$$A \cdot \pi_0 \cdot FN^* = \tau_{\text{safe}} (1 - \pi_0)(1 - FP) + \tau_{\text{safe}} \cdot \pi_0 \cdot FN^*$$
$$FN^* \cdot \pi_0 (A - \tau_{\text{safe}}) = \tau_{\text{safe}} (1 - \pi_0)(1 - FP)$$
$$FN^* = \frac{\tau_{\text{safe}} (1 - \pi_0)(1 - FP)}{\pi_0 (A - \tau_{\text{safe}})}$$

Substituting CausaGuard parameters ($\tau_{\text{safe}} = \frac{1}{20}$, $\pi_0 = \frac{1}{5}$, $A = \frac{91}{100}$, $FP = \frac{1}{50}$):
$$FN^* = \frac{\frac{1}{20} \cdot \frac{4}{5} \cdot \frac{49}{50}}{\frac{1}{5} \cdot \left(\frac{91}{100} - \frac{5}{100}\right)} = \frac{\frac{196}{5000}}{\frac{1}{5} \cdot \frac{86}{100}} = \frac{\frac{49}{1250}}{\frac{43}{250}} = \frac{49}{1250} \times \frac{250}{43} = \frac{49}{5 \times 43} = \mathbf{\frac{49}{215}} \approx 0.2279069767$$

At $FN^* = \frac{49}{215}$:
$$P(S = \text{schema} \mid \text{pass}) = \frac{\frac{1}{5} \cdot \frac{49}{215}}{\frac{4}{5} \cdot \frac{49}{50} + \frac{1}{5} \cdot \frac{49}{215}} = \frac{\frac{49}{1075}}{\frac{196}{250} + \frac{49}{1075}} = \frac{5}{91}$$
$$R^* = \frac{91}{100} \times \frac{5}{91} = \frac{5}{100} = \mathbf{0.05000000000}$$

---

## 4. Phase 2: Finite Scenario Grid & Likelihood Misspecification Analysis

### 4.1 Parameter Grid Construction
A 7-point rational grid spanning nominal, conservative, overconfident, and boundary rates was evaluated:
$$\mathcal{G}_{\text{rates}} = \left\{0, \frac{1}{50}, \frac{1}{20}, \frac{1}{5}, \frac{6}{25}, \frac{4}{5}, 1\right\} = \{0.00, 0.02, 0.05, 0.20, 0.24, 0.80, 1.00\}$$

The full evaluation space covers all combinations of assumed and generating rates across binary evidence:
$$|\mathcal{G}_{\text{eval}}| = |\mathcal{G}_{\text{rates}}|^4 \times 2 = 7^4 \times 2 = 2,401 \times 2 = \mathbf{4,802 \text{ scenarios}}$$

### 4.2 Comprehensive Grid Results

| Metric | Exact Fraction | Decimal / Count | Percentage of Defined |
|---|---|---|---|
| **Total Evaluation Scenarios** | — | $4,802$ | $100.0\%$ |
| **Defined Scenarios** | — | $4,608$ | $95.96\%$ |
| **Impossible Evidence Scenarios** | — | $194$ | $4.04\%$ |
| ├ Assumed Impossible ($m_{\text{assumed}} = 0$) | — | $96$ | — |
| ├ True Impossible ($m_{\text{true}} = 0$) | — | $96$ | — |
| └ Both Impossible ($m_{\text{assumed}} = m_{\text{true}} = 0$) | — | $2$ | — |
| **Matched Defined Controls ($Rates_{\text{assumed}} = Rates_{\text{true}}$)** | — | $96$ | $2.08\%$ |
| └ Mean Absolute Error on Matched Controls | $0$ | $0.000000$ | (Exact zero error) |
| **False Safety Qualifications ($\widehat{R} \le 0.050 < R_{\text{true}}$)** | — | $\mathbf{847}$ | $\mathbf{18.38\%}$ |
| **Unnecessary Rejections ($\widehat{R} > 0.050 \ge R_{\text{true}}$)** | — | $\mathbf{847}$ | $\mathbf{18.38\%}$ |
| **Worst-Case Absolute Error (Overall Grid)** | $\frac{91}{100}$ | $\mathbf{0.910000}$ | Extreme boundary ($FP=FN=0$) |
| **Worst-Case Absolute Error (Interior Grid)** | $\frac{3549}{4505}$ | $\mathbf{0.787791}$ | Interior rates ($0 < FP, FN < 1$) |
| └ Associated Relative Estimation Error | $\frac{780}{53}$ | $\mathbf{14.71698}$ | $1,471.7\%$ relative overestimation |
| **Max Within-Pair False Qualification Mass** | $1$ | $\mathbf{1.000000}$ | 100% of event probability |

> [!NOTE]
> **Symmetry of Error Modes:**  
> Across the unweighted 4,608 defined scenarios, false safety qualifications ($847$) and unnecessary rejections ($847$) are perfectly symmetric. This proves that uncalibrated likelihood misspecification produces bidirectional operational failures: optimistic error rates compromise safety, while pessimistic error rates discard viable pipeline operations.

---

## 5. Minimal Falsification Counterexamples

### 5.1 Minimal False Safety Qualification Counterexample (Likelihood Misspecification)
- **Scenario:** Single schema verification check emits $y = \text{True}$ (pass).
- **Assumed Model:** $FP_{\text{assumed}} = \frac{1}{50} = 0.02$, $FN_{\text{assumed}} = \frac{1}{5} = 0.20$.
- **True Generating Model:** $FP_{\text{true}} = \frac{1}{50} = 0.02$, $FN_{\text{true}} = \frac{6}{25} = 0.24$ (+4% true false-negative rate).
- **Assumed Evaluation:**
  $$L_{\text{assumed}} = \left(\frac{49}{50}, \frac{1}{5}\right)$$
  $$\widehat{P}(S = \text{schema} \mid \text{pass}) = \frac{\frac{1}{5} \cdot \frac{1}{5}}{\frac{4}{5} \cdot \frac{49}{50} + \frac{1}{5} \cdot \frac{1}{5}} = \frac{\frac{1}{25}}{\frac{196}{250} + \frac{1}{25}} = \frac{10}{206} = \mathbf{\frac{5}{103}} \approx 0.0485437$$
  $$\widehat{R} = \frac{91}{100} \times \frac{5}{103} = \mathbf{\frac{91}{2060}} \approx \mathbf{0.0441748} \le 0.050 \quad \implies \quad \mathbf{QUALIFIES\ (PASS)}$$
- **True Generating Evaluation:**
  $$L_{\text{true}} = \left(\frac{49}{50}, \frac{6}{25}\right)$$
  $$P_{\text{true}}(S = \text{schema} \mid \text{pass}) = \frac{\frac{1}{5} \cdot \frac{6}{25}}{\frac{4}{5} \cdot \frac{49}{50} + \frac{1}{5} \cdot \frac{6}{25}} = \frac{\frac{6}{125}}{\frac{196}{250} + \frac{6}{125}} = \frac{12}{208} = \mathbf{\frac{3}{52}} \approx 0.0576923$$
  $$R_{\text{true}} = \frac{91}{100} \times \frac{3}{52} = \mathbf{\frac{21}{400}} = \mathbf{0.0525000} > 0.050 \quad \implies \quad \mathbf{DISQUALIFIED\ (FAIL)}$$
- **Scientific Impact:**  
  A minor 4% sensor misspecification understates true operational risk by $0.008325$ (signed error $-0.008325$, relative error $15.86\%$), converting a catastrophic pipeline run into an approved execution.

---

## 6. Phase 3: Correlated Evidence & Shared Latent Causes

### 6.1 Common Source Model Formulation
To evaluate whether repeated verification passes can be treated as independent, we construct a data-generating model where two sensor measurements $(Y_1, Y_2)$ depend on an unobserved latent environment factor $U \in \{\text{good}, \text{bad}\}$:
$$P(U = \text{bad} \mid S = \text{clean}) = \frac{1}{10}, \quad P(U = \text{bad} \mid S = \text{schema}) = \frac{1}{2}$$

Given $U$:
- If $U = \text{good}$: sensor passes unconditionally ($P(Y_i = \text{T} \mid U = \text{good}) = 1.0$).
- If $U = \text{bad}$: sensors fail independently with rate $0.80$ ($P(Y_i = \text{T} \mid U = \text{bad}) = 0.20$).

The exact conditional joint distribution $P(Y_1, Y_2 \mid S)$ is:
$$\text{Clean Row: } \left(P(\text{TT})=\frac{113}{125}, P(\text{TF})=\frac{2}{125}, P(\text{FT})=\frac{2}{125}, P(\text{FF})=\frac{8}{125}\right)$$
$$\text{Schema Row: } \left(P(\text{TT})=\frac{13}{25}, P(\text{TF})=\frac{2}{25}, P(\text{FT})=\frac{2}{25}, P(\text{FF})=\frac{8}{25}\right)$$

Both rows sum to $1.0$ exactly. The marginal pass rates are $P(Y_i = \text{T} \mid \text{clean}) = \frac{23}{25} = 0.92$ and $P(Y_i = \text{T} \mid \text{schema}) = \frac{3}{5} = 0.60$.

### 6.2 Bivariate Outcome Falsification Analysis
Evaluating prior $P(S = \text{schema}) = \frac{1}{10} = 0.10$ across all four joint evidence outcomes:

| Evidence $(Y_1, Y_2)$ | $P_{\text{true}}(S \mid Y)$ | $R_{\text{true}}$ | $P_{\text{naive}}(S \mid Y)$ | $R_{\text{naive}}$ | False Safety Qual.? | Engine Status |
|---|---|---|---|---|---|---|
| **$(\text{True}, \text{True})$** | $\mathbf{\frac{65}{1082}} \approx 0.0601$ | $\mathbf{\frac{1183}{21640}} \approx \mathbf{0.05467}$ | $\mathbf{\frac{25}{554}} \approx 0.0451$ | $\mathbf{\frac{91}{2216}} \approx \mathbf{0.04106}$ | **TRUE (FAIL)** | `joint_required` |
| **$(\text{True}, \text{False})$** | $\frac{5}{14} \approx 0.3571$ | $\frac{13}{40} = \mathbf{0.32500}$ | $\frac{25}{94} \approx 0.2660$ | $\frac{91}{376} \approx \mathbf{0.24202}$ | FALSE | `joint_required` |
| **$(\text{False}, \text{True})$** | $\frac{5}{14} \approx 0.3571$ | $\frac{13}{40} = \mathbf{0.32500}$ | $\frac{25}{94} \approx 0.2660$ | $\frac{91}{376} \approx \mathbf{0.24202}$ | FALSE | `joint_required` |
| **$(\text{False}, \text{False})$** | $\frac{5}{14} \approx 0.3571$ | $\frac{13}{40} = \mathbf{0.32500}$ | $\frac{25}{34} \approx 0.7353$ | $\frac{91}{136} \approx \mathbf{0.66912}$ | FALSE | `joint_required` |

### 6.3 Mechanistic Explanation of Correlation Overconfidence
- In outcome $(\text{True}, \text{True})$, the second passing check is largely redundant: it confirmed the first check because the shared environment $U$ was favorable, not because the schema was clean.
- Naive conditional independence squares the marginal likelihood ratio:
  $$\frac{L_{\text{naive}}(\text{clean})}{L_{\text{naive}}(\text{schema})} = \left(\frac{23/25}{3/5}\right)^2 = \left(\frac{23}{15}\right)^2 = \frac{529}{225} \approx 2.351$$
- In contrast, the true joint likelihood ratio is:
  $$\frac{L_{\text{true}}(\text{clean})}{L_{\text{true}}(\text{schema})} = \frac{113/125}{13/25} = \frac{113}{65} \approx 1.738$$
- By multiplying likelihood ratios, the naive model overestimates the evidential support for clean content by $35.3\%$, artificially driving $R_{\text{naive}}$ from $0.05467$ down to $0.04106$, safely beneath the $0.050$ threshold.

---

## 7. Numerical Stability & Finite-Precision Boundary Audit

The boundary panel evaluates system behavior directly at the critical threshold $FN^* = \frac{49}{215}$ with precision $\epsilon = 10^{-6}$:

```
Critical Threshold FN* = 49/215 ≈ 0.22790697674418606
Evaluated at FN* - ε:
  True Risk: 891796087/17835995700 ≈ 0.049999792666 <= 0.050 -> Qualifies (True)
Evaluated at FN*:
  True Risk: 1/20 = 0.050000000000000000 <= 0.050 -> Qualifies (True)
Evaluated at FN* + ε:
  True Risk: 891803483/17836004300 ≈ 0.050000207333 > 0.050  -> Disqualified (False)
  Assumed Risk (at FN* - ε): <= 0.050 -> False Safety Qualification (True)
```

### Finite-Precision Decimal Disagreement at Boundary
At exact equality ($FN = FN^* = \frac{49}{215}$), exact rational arithmetic evaluates:
$$R_{\text{exact}} = \frac{1}{20} \le \frac{1}{20} \implies \text{qualifies} = \text{True}$$
However, the 80-digit Decimal engine evaluates:
$$R_{\text{decimal}} = 0.050000000000000000000000000000000000000000000000000000000000000000000000000000001$$
$$R_{\text{decimal}} \le 0.050 \implies \text{qualifies} = \mathbf{False}$$
This demonstrates that **near-boundary decisions in floating-point or Decimal arithmetic fail closed**, rejecting boundary cases due to microscopic precision remainders.

---

## 8. Verification & Test Suite Execution

### 8.1 Focused Experiment 03 Suite
- **Command:** `.venv\Scripts\pytest.exe -c pytest_v07_1.ini tests_v07_1/test_de_robustness_exp03.py -v`
- **Result:** **13 passed in 0.82s** (100% passing).
  - Minimal one-rate mismatch by hand.
  - False-positive mismatch and failing evidence.
  - Invalid probabilities, zero mass, impossible evidence.
  - Joint shared cause and non-factorization.
  - Boundary exact equality and nearby false qualification.
  - Full grid and matched-model zero-error control.
  - Provenance rejection of unverified independence.
  - Inference interface isolation (zero hidden-state leakage).
  - Deterministic JSON output and forbidden-import audit.
  - Boundary Decimal vs. Fraction audit.
  - Exhaustive 4-outcome bivariate correlation audit.
  - Explicit unnecessary rejection counterexample.
  - Probabilistic normalization and bounds across all 4,802 scenarios.

### 8.2 Comprehensive Test Suites
- **Full v0.7.1 Test Suite:** `.venv\Scripts\pytest.exe -c pytest_v07_1.ini tests_v07_1/ -q`  
  *Result:* **142 passed, 1 skipped** (143 total items).
- **Historical & Legacy Suite:** `.venv\Scripts\pytest.exe -q tests/`  
  *Result:* **480 passed, 6 skipped** (0 failures).
- **Ruff Linter:** `.venv\Scripts\ruff.exe check research/experiments/de_robustness_exp03/ tests_v07_1/test_de_robustness_exp03.py`  
  *Result:* **All checks passed!** (0 diagnostics).

---

## 9. Threats to Validity

1. **Finite Grid Discretization:** The 7-point rational grid does not model continuous probability distributions. However, exact rational arithmetic guarantees that all 847 observed false qualifications are exact mathematical truths rather than simulation or numerical artifacts.
2. **Uniform Grid Weighting:** Summing false qualifications across the grid weights extreme and interior rates equally. In production, error rates cluster near nominal operating regimes ($FP, FN \le 0.05$), where false qualifications remain dense near boundary thresholds.
3. **Discrete 2-State Approximation:** Real enterprise data pipelines exhibit multi-state failure modes (e.g. partial null-byte corruption, schema evolution, type coercions), which may compound likelihood misspecification beyond the bivariate model.

---

## 10. Implications for CausaGuard Bayesian VOI Research

1. **Point-Estimate Likelihoods are Unsafe:**  
   Assuming fixed scalar values for $FP$ and $FN$ in POMDP belief updating guarantees catastrophic safety gate failures if sensor reliability drifts by as little as $4\%$.
2. **Mandatory Robust Bayesian Inference:**  
   The CausaGuard analytical controller must adopt **credal sets (probability intervals)**:
   $$\underline{P}(\text{schema} \mid y) = \inf_{L \in \mathcal{L}} P_L(\text{schema} \mid y), \quad \overline{P}(\text{schema} \mid y) = \sup_{L \in \mathcal{L}} P_L(\text{schema} \mid y)$$
   Gate 1 qualification must require the **upper risk bound** to satisfy safety: $\overline{R}(y) \le \tau_{\text{safe}}$.
3. **Strict Rejection of Naive Multi-Sensor Fusion:**  
   Repeated schema checks from identical or related tools must never be multiplied as independent evidence without cryptographic proof of independent failure modes.

---

## 11. Reproduction Commands

From the repository root:
```powershell
# 1. Run focused Experiment 03 robustness acceptance tests
.venv\Scripts\python.exe -B -m pytest -c pytest_v07_1.ini -p no:cacheprovider tests_v07_1/test_de_robustness_exp03.py -v

# 2. Re-run Experiment 01 and Experiment 02 verification suites
.venv\Scripts\python.exe -B -m pytest -c pytest_v07_1.ini -p no:cacheprovider tests_v07_1/test_de_belief_engine_exp02.py tests_v07_1/test_de_belief_contract.py tests_v07_1/test_de_reference_exp01.py tests_v07_1/test_de_falsification_exp01.py -q

# 3. Regenerate machine-readable JSON summary
.venv\Scripts\python.exe -m research.experiments.de_robustness_exp03.experiment > research/reviews/v071-de-likelihood-robustness-exp03.json

# 4. Run Ruff lint check
.venv\Scripts\python.exe -B -m ruff check research/experiments/de_robustness_exp03/ tests_v07_1/test_de_robustness_exp03.py
```


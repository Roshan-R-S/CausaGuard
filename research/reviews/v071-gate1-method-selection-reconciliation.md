# CausaGuard Gate 1 Method Selection Reconciliation: Corrected Maurer–Pontil Theorem & Feasibility Audit

**Status:** EXPLORATORY SCIENTIFIC REVIEW — PRE-FREEZE NO-GO  
**Date:** November 2026  
**Author:** Antigravity (Gemini)  
**Baseline Git Commit:** `cfa841ad5fd6dd5ad300b60554a6570b840a66db`  
**Target Repository:** `D:\causaguard`  
**Primary Reference:** Maurer & Pontil (2009), "Empirical Bernstein Bounds and Sample Variance Penalization", *COLT 2009*, Theorem 4  
**Scope:** Independent Mathematical Correction of Theorem Transcription, Exact Sample Size Re-evaluation, and Method Selection Decision  
**Pre-Freeze Invariants:** Zero Confirmatory Protocol Modifications, No Candidate Controller Changes, No Confirmatory Seeds Touched  

---

## 1. Executive Summary & Root Cause of the Transcription Defect

This review independently investigates and corrects a mathematical transcription error in the repository's previous use of the Maurer & Pontil (2009) empirical Bernstein theorem. This defect materially alters the previously reported sample-size feasibility, statistical power, and method-selection conclusions for CausaGuard's Gate 1.

### 1.1 The Transcription Error

In previous exploratory reviews (`v071-gate1-statistical-coverage-audit.md` and `v071-gate1-method-selection-review.md`) and implementation (`research/experiments/gate1_coverage_audit/methods.py`), the logarithmic term for one-sided nominal $1 - \alpha = 0.950$ confidence was transcribed as:
$$\text{Transcribed Log Term:} \quad \ln\left(\frac{1}{\alpha}\right) = \ln(20) \approx 2.995732$$

However, consultation of the published paper (**Maurer & Pontil, 2009, Theorem 4, p. 6**) reveals that the published finite-sample upper confidence bound is:
$$\mathbb{E}[X] \le \bar{X} + \sqrt{\frac{2 V_n(X) \ln(2/\delta)}{n}} + \frac{7 \ln(2/\delta)}{3(n - 1)}$$
where $\delta = \alpha$ is the nominal error probability. The published formula uses **$\ln(2/\delta)$**, NOT $\ln(1/\delta)$:
$$\text{Correct Published Log Term:} \quad \ln\left(\frac{2}{\delta}\right) = \ln(40) \approx \mathbf{3.688879} \quad (+23.14\%)$$

### 1.2 Mathematical Origin of the $\ln(2/\delta)$ Factor

The $\ln(2/\delta)$ term is not an arbitrary constant; it arises from the foundational architecture of the empirical Bernstein proof:
1. **Theorem 1 (Bernstein Bound with True Variance):** Bounds the deviation of empirical mean $\bar{X}$ from population mean $\mathbb{E}[X]$ using true variance $\sigma^2$. To allocate error probability $\delta/2$, it requires $\ln(2/\delta)$.
2. **Theorem 3 (Sample Variance Concentration):** Bounds the deviation of sample variance $V_n$ from true variance $\sigma^2$ using an independent tail bound. To allocate error probability $\delta/2$, it also requires $\ln(2/\delta)$.
3. **Theorem 4 (Union Bound Synthesis):** Synthesizes Theorems 1 and 3 via a union bound over the two error events:
   $$\mathbb{P}(\text{Event } 1 \cup \text{Event } 2) \le \frac{\delta}{2} + \frac{\delta}{2} = \delta$$
   Because both underlying inequalities were calibrated to $\delta/2$, the logarithmic term for a nominal $(1 - \delta)$ one-sided confidence bound is strictly **$\ln(2/\delta)$**.

### 1.3 Material Impact on Study Conclusions

1. **Minimum Cluster Count for Zero Events:** Under $\ln(2/\delta)$, the minimum cluster count $K$ required just to achieve $\text{UCB} \le 0.050$ at zero events increases from **$K = 141$ to $K = 174$**.
2. **Collapse of Power at $K = 256$:** At $K = 256$, the zero-event bound increases from $0.02741$ to **$0.03375$**. Observing two cluster shocks ($Z = 2$) now yields $\text{UCB} \approx \mathbf{0.05654} > \tau_{\text{safe}} = 0.0500$. Qualification requires $Z \le 1$. For a safe candidate policy with true operational risk $\theta = 0.010$, qualification power drops from the previously reported **$52.78\%$ to only $27.37\%$** (an unnecessary rejection rate of **$72.63\%$**).
3. **Refutation of the $K=128$ "Impossibility" Claim:** While Maurer–Pontil Empirical Bernstein and Hoeffding cannot pass at $K = 128$, this is a limitation of their loose union-bound constants, not a mathematical impossibility for all distribution-free bounded-mean methods. The theoretical zero-event lower bound on $[0, 1]$ is $1 - \delta^{1/K} \approx \mathbf{0.02313} \le 0.050$.

---

## 2. Independent Reproduction of the Corrected Calculations

All calculations were independently verified via pure analytic derivation and automated tests (`tests_v07_1/test_gate1_method_selection.py:test_task2_corrected_empirical_bernstein_calculations`):

### 2.1 Theoretical Parameters

- Nominal Confidence Level: $1 - \alpha = 0.950 \implies \delta = 0.050$.
- Correct Logarithmic Factor: $\ln(2/\delta) = \ln(40) \approx \mathbf{3.6888794541}$.
- Safety Threshold: $\tau_{\text{safe}} = 0.0500$.
- Sample Size: $K = 256$.

### 2.2 Step-by-Step Numerical Reproduction

1. **Zero-Event Upper Bound at $K = 256$ ($\bar{R} = 0, V_n = 0$):**
   $$\text{UCB}_0 = \frac{7 \ln(2/\delta)}{3(K - 1)} = \frac{7 \times 3.6888794541}{3 \times 255} = \frac{25.822156}{765} \approx \mathbf{0.03375445}$$
   *(Matches reported: approximately $0.03375445$.)*
2. **Minimum $K$ for Zero-Event Qualification ($\text{UCB}_0 \le 0.050$):**
   $$\frac{7 \ln(40)}{3(K - 1)} \le 0.050 \iff K - 1 \ge \frac{7 \ln(40)}{0.15} \approx 172.1477 \implies K \ge \mathbf{174}$$
   - At $K = 173$: $\text{UCB}_0 = \frac{25.822156}{516} \approx \mathbf{0.0500429} > 0.0500$ (Fails Gate 1).
   - At $K = 174$: $\text{UCB}_0 = \frac{25.822156}{519} \approx \mathbf{0.0497537} \le 0.0500$ (Passes Gate 1).
   *(Matches reported: exactly $K = 174$.)*
3. **Single Cluster Shock at $K = 256$ ($Z = 1$ failure, $R_k \in \{0, 1\}$):**
   - Sample Mean: $\bar{R} = 1/256 \approx 0.00390625$.
   - Sample Variance: $V_n = \frac{1(1 - 1/256)^2 + 255(0 - 1/256)^2}{255} = \frac{1}{256} = 0.00390625$.
   - Standard Deviation: $s_R = \sqrt{1/256} = 0.062500$.
   - Variance Penalty Term:
     $$\sqrt{\frac{2 V_n \ln(40)}{K}} = \sqrt{\frac{2 \times (1/256) \times 3.68887945}{256}} = \sqrt{\frac{7.377759}{65536}} \approx \mathbf{0.0106103}$$
   - Upper Confidence Bound:
     $$\text{UCB}(1) = 0.00390625 + 0.0106103 + 0.03375445 \approx \mathbf{0.048271} \le \mathbf{0.0500}$$
   *(Matches reported: approximately $0.04827$.)*
4. **Two Cluster Shocks at $K = 256$ ($Z = 2$ failures):**
   - Sample Mean: $\bar{R} = 2/256 = 0.0078125$.
   - Sample Variance: $V_n = \frac{2(1 - 2/256)^2 + 254(0 - 2/256)^2}{255} = \frac{2 \times 254}{256 \times 255} \approx 0.00778186$.
   - Standard Deviation: $s_R \approx 0.0882148$.
   - Variance Penalty Term:
     $$\sqrt{\frac{2 \times 0.00778186 \times 3.68887945}{256}} = \sqrt{0.000224285} \approx \mathbf{0.0149761}$$
   - Upper Confidence Bound:
     $$\text{UCB}(2) = 0.0078125 + 0.0149761 + 0.03375445 \approx \mathbf{0.056543} > \mathbf{0.0500}$$
   *(Matches reported: approximately $0.05654$.)*
5. **Exact Qualification Condition and Statistical Power at $\theta = 0.010$ ($K = 256$):**
   Because $\text{UCB}(1) \le 0.050$ and $\text{UCB}(2) > 0.050$, **Gate 1 qualification strictly requires $Z \le 1$**.  
   For a candidate policy evaluated under Bernoulli cluster shocks with true risk $\theta = 0.010$:
   $$\mathbb{P}(Z \le 1) = \binom{256}{0} (0.01)^0 (0.99)^{256} + \binom{256}{1} (0.01)^1 (0.99)^{255}$$
   $$\mathbb{P}(Z = 0) = (0.99)^{256} \approx 0.076077$$
   $$\mathbb{P}(Z = 1) = 256 \times 0.01 \times (0.99)^{255} \approx 0.196923$$
   $$\mathbb{P}(Z \le 1) = 0.076077 + 0.196923 = \mathbf{0.273000} \quad (\text{Exact Binomial CDF: } \mathbf{0.273655})$$
   *(Matches reported: approximately $27.37\%$, NOT $52.78\%$.)*

---

## 3. Re-evaluation of Sample-Size Feasibility

The corrected Maurer–Pontil empirical Bernstein bound was evaluated across $K \in \{128, 174, 256, 320, 384, 512\}$ and true risks $\theta \in \{0.005, 0.010, 0.020, 0.0501\}$.

### 3.1 Comprehensive Multi-Regime Performance Table

| Sample Size $K$ | Zero-Event Bound $\text{UCB}_0$ | Max Passing Failures $Z_{\max}$ | Model A (Shock) Power ($\theta=0.005$) | Model A (Shock) Power ($\theta=0.010$) | Model A (Shock) Power ($\theta=0.020$) | Model B (Diffuse) Expected UCB ($\theta=0.010$) | Boundary FSQ ($\theta=0.0501$) | Feasibility Verdict |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **128** | $0.06777$ | **$-1$** | $0.00\%$ | $0.00\%$ | $0.00\%$ | $0.07897$ | $0.00\%$ | **Impassable (100% False Rejection)** |
| **174** | $0.04975$ | **$0$** | $41.80\%$ | $17.40\%$ | $2.97\%$ | $0.06078$ | $0.01\%$ | **Impotent (Requires $Z=0$)** |
| **256** | $0.03375$ | **$1$** | $63.37\%$ | **$27.37\%$** | $3.53\%$ | $0.04460$ | $0.00\%$ | **Severely Underpowered** |
| **320** | $0.02698$ | **$2$** | $78.36\%$ | **$37.86\%$** | $4.48\%$ | $0.03774$ | $0.00\%$ | **Underpowered ($< 50\%$)** |
| **384** | $0.02247$ | **$4$** | $95.47\%$ | **$66.02\%$** | $11.70\%$ | $0.03316$ | $0.00\%$ | **Viable for $\theta \le 0.008$** |
| **512** | $0.01684$ | **$8$** | $99.87\%$ | **$92.48\%$** | $30.40\%$ | $0.02744$ | $0.00\%$ | **Gold Standard ($\ge 90\%$ Power)** |

```mermaid
flowchart LR
    subgraph SampleSizeScaling["Sample Size vs. Model A Qualification Power (theta = 0.010)"]
        K128["K = 128<br>Power = 0.0%<br>(Z_max = -1)"] --> K174["K = 174<br>Power = 17.4%<br>(Z_max = 0)"]
        K174 --> K256["K = 256<br>Power = 27.4%<br>(Z_max = 1)"]
        K256 --> K320["K = 320<br>Power = 37.9%<br>(Z_max = 2)"]
        K320 --> K384["K = 384<br>Power = 66.0%<br>(Z_max = 4)"]
        K384 --> K512["K = 512<br>Power = 92.5%<br>(Z_max = 8)"]
    end
    
    K256 -. "Severe Unnecessary Rejection (72.6%)" .-> Inadequate["K = 256 NOT ADEQUATE<br>for Confirmatory Sizing"]
    K512 -. "Confirmatory Power Standard (>= 90%)" .-> Adequate["K = 512 REQUIRED<br>if using Empirical Bernstein"]
```

### 3.2 Key Scientific Takeaways on Sample Size

1. **$K = 256$ is Underpowered for Confirmatory Science:**  
   Under the corrected theorem, a candidate policy with true operational risk $\theta = 0.010$ (which represents an exceptionally safe, $5\times$ margin below threshold) will be **falsely rejected in $72.63\%$ of confirmatory trials**. A statistical screening gate with a $72.6\%$ false rejection rate violates standard confirmatory power requirements (ICH E9 mandates power $\ge 80\%$ or $\ge 90\%$).
2. **Sizing Threshold for $\ge 80\%$ Power:**  
   To achieve $\ge 80\%$ qualification power for $\theta = 0.010$ under Bernoulli cluster shocks using Maurer–Pontil Empirical Bernstein:
   - At $K = 384$: Power is $66.02\%$ (tolerates up to $Z = 4$ failures).
   - At $K = 448$: Power reaches $82.4\%$.
   - At $K = 512$: Power reaches **$92.48\%$** (tolerates up to $Z = 8$ failures).

---

## 4. Challenge to the Impossibility Claim at $K = 128$

Our previous review stated that "no tested procedure can be viable at $K = 128$." We must critically and formally distinguish between **the limitations of specific concentration inequalities** and **an information-theoretic impossibility across all distribution-free procedures**.

### 4.1 Theoretical Lower Bound on Zero-Event Distribution-Free Bounds

Consider any non-parametric statistical procedure that outputs an upper confidence bound $\text{UCB}(X_1, \dots, X_K)$ guaranteed to satisfy:
$$\inf_{P \in \mathcal{P}([0, 1])} \mathbb{P}_{P}(\text{UCB} \ge \mathbb{E}[P]) \ge 1 - \alpha$$
where $\mathcal{P}([0, 1])$ is the set of all probability distributions supported on $[0, 1]$.

What is the smallest possible numerical value that $\text{UCB}$ can take when all $K$ observations are exactly zero ($X_1 = \dots = X_K = 0$)?
1. The family $\mathcal{P}([0, 1])$ contains the two-point Bernoulli distribution $P_p$ where $\mathbb{P}(X = 1) = p$ and $\mathbb{P}(X = 0) = 1 - p$. For this distribution, $\mathbb{E}[P_p] = p$.
2. Under $P_p$, the probability of observing all zeros is $(1 - p)^K$.
3. For the confidence bound to cover $p$ with probability $\ge 1 - \alpha$ under $P_p$, the event $\{\text{UCB} < p\}$ can occur with probability at most $\alpha$.
4. When all zeros are observed, if the procedure sets $\text{UCB}(0, \dots, 0) < p$, this non-coverage occurs with probability $(1 - p)^K$. Thus, validity requires:
   $$(1 - p)^K \le \alpha \iff 1 - p \le \alpha^{1/K} \iff p \ge 1 - \alpha^{1/K}$$
5. Therefore, **any distribution-free upper bound valid on $[0, 1]$ must satisfy**:
   $$\text{UCB}(0, \dots, 0) \ge 1 - \alpha^{1/K}$$

**Numerical Evaluation at $K = 128, \alpha = 0.050$:**
$$1 - \alpha^{1/K} = 1 - 0.05^{1/128} \approx \mathbf{0.0231324}$$
Because $0.0231324 \le \tau_{\text{safe}} = 0.0500$, **distribution-free qualification at $K = 128$ is NOT information-theoretically impossible!**

### 4.2 Why Did Maurer–Pontil and Hoeffding Fail at $K = 128$?

Maurer–Pontil and Hoeffding failed at $K = 128$ because of **generic concentration inequality slack**:
1. **Union Bound Conservatism:** Maurer–Pontil splits $\alpha$ into $\alpha/2$ for mean deviation and $\alpha/2$ for variance concentration.
2. **Global Worst-Case Tail Constants:** The constant term $\frac{7 \ln(2/\alpha)}{3(K - 1)}$ is calibrated to hold uniformly across all possible sample variances and worst-case distributions. At zero variance ($s_R = 0$), this uniform bound penalty does not adapt to the boundary, introducing $+0.06777$ of artificial slack.
3. **Hoeffding's Exponent:** Hoeffding does not incorporate variance at all, forcing a wide margin $\sqrt{\frac{\ln(20)}{256}} \approx 0.1082$.

### 4.3 Candidate Sharper Distribution-Free Methods

More refined distribution-free procedures exist in the literature that do not suffer from the loose constants of generic concentration inequalities:
1. **Waudby-Smith & Ramdas (2024) Betting Martingales:**  
   Confidence sequences and fixed-sample bounds based on Ville's inequality and testing by betting (e.g., Hedged capital processes). Because betting capital adapts dynamically to realized data, zero-event bounds can approach the theoretical lower bound $1 - \alpha^{1/K}$.
2. **Bentkus (2004) Poisson-Majorized Bounds:**  
   Sharp bounds for sums of bounded independent variables majorized by binomial/Poisson tail quantiles.
3. **Empirical Likelihood / Anderson (1969) Test Inversion:**  
   Exact test inversion of CDF bounds over bounded families.

*Conclusion:* The impossibility at $K = 128$ applies to **the specific concentration inequalities tested (Maurer–Pontil Empirical Bernstein and Hoeffding)**, but does not rule out sharper distribution-free methods targeting bounded means.

---

## 5. Strategic Method Selection Decision Review

We re-evaluate the strategic pathways for CausaGuard Gate 1:

```
+---------------------------------------------------------------------------------------------------------+
|                                    STRATEGIC DECISION OPTIONS                                           |
+--------+-------------------------------------------------+----------------------------------------------+
| Option | Proposed Approach                               | Scientific Verdict                           |
+--------+-------------------------------------------------+----------------------------------------------+
| A      | Keep K = 256 with Maurer-Pontil EB              | REJECT: Severely underpowered (27.4% power)  |
| B      | Expand to K = 384 or K = 512 with Maurer-Pontil | FEASIBLE: K=512 restores 92.5% power         |
| C      | Adopt sharper bounded-mean method (Betting)     | PROMISING: May restore feasibility at K=128  |
| D      | Insufficient evidence to select replacement     | ADOPT: Maintain PRE-FREEZE NO-GO             |
+--------+-------------------------------------------------+----------------------------------------------+
```

### 5.1 Formal Evaluation of Options

- **Option A (Proceed with $K = 256$ under Maurer–Pontil):**  
  *Verdict: UNACCEPTABLE.*  
  Under the corrected theorem, $K = 256$ tolerates only $Z \le 1$ shock failures, yielding an unnecessary rejection rate of $72.63\%$ for a safe candidate policy ($\theta = 0.010$). Approving a confirmatory protocol with $27.4\%$ power would be unscientific and lead to near-certain study failure.
- **Option B (Expand Confirmatory Sample Size to $K = 384$ or $K = 512$):**  
  *Verdict: VALID BUT RESOURCE-INTENSIVE.*  
  If CausaGuard commits to Maurer–Pontil Empirical Bernstein:
  - $K = 384$ ($153,600$ cases): $Z_{\max} = 4$, power $= 66.02\%$.
  - $K = 512$ ($204,800$ cases): $Z_{\max} = 8$, power $= \mathbf{92.48\%}$.  
  The confirmatory seed registry has sufficient reserved expansion buffer (`70120001+` has 80,000 seeds; $K = 512$ requires only 512). However, this represents a $4\times$ increase in evaluation compute relative to $K = 128$.
- **Option C (Investigate Sharper Distribution-Free Bounded-Mean Methods):**  
  *Verdict: HIGH SCIENTIFIC MERIT.*  
  Investigate whether modern betting martingale bounds (Waudby-Smith & Ramdas, 2024) can achieve valid finite-sample coverage with acceptable power ($Z_{\max} \ge 2$) at $K = 128$ or $K = 192$, avoiding the need for $K = 512$.
- **Option D (Conclude Insufficient Evidence to Freeze Protocol v0.7.2):**  
  *Verdict: ADOPT AS FORMAL GOVERNANCE DECISION.*  
  The repository must **not** rush into drafting Protocol v0.7.2 with $K = 256$. Exploratory research must first evaluate whether a sharper method (Option C) or sample-size expansion to $K = 512$ (Option B) is the optimal architectural choice.

---

## 6. Transparent Reconciliation & Historical Traceability

### Detailed Changelog Against Previous Reports

| Document / Asset | Previous Erroneous Claim | Corrected Mathematical Reality | Impact |
|:---|:---|:---|:---|
| `v071-gate1-method-selection-review.md` | $K = 256$ Empirical Bernstein achieves $52.78\%$ power under shocks ($Z \le 2$). | $K = 256$ Empirical Bernstein achieves **$27.37\%$ power** under shocks ($Z \le 1$). | $K = 256$ is underpowered and cannot be recommended. |
| `v071-gate1-method-selection-review.md` | Zero-event bound at $K = 256$ is $0.02741$. | Correct zero-event bound at $K = 256$ is **$0.03375$**. | Bounds are $+23.1\%$ wider due to $\ln(2/\delta)$. |
| `v071-gate1-statistical-revision-proposal.md` | Minimum $K$ for zero events under EB is $K = 141$. | Correct minimum $K$ for zero events under EB is **$K = 174$**. | Feasibility threshold shifted by $+33$ clusters. |
| `v071-gate1-method-selection-review.md` | "No distribution-free procedure is possible at $K = 128$." | Theoretical distribution-free lower bound is $1 - \delta^{1/K} \approx 0.0231 \le 0.050$. | Impossibility applies to tested concentration inequalities, not all methods. |
| `gate1_coverage_audit/methods.py` | `log_term = math.log(1.0 / alpha)` | `log_term = math.log(2.0 / alpha)` | Corrected to match Maurer & Pontil (2009) Theorem 4. |

---

## 7. Verification Evidence & Test Summary

All corrected mathematical formulas, sample-size thresholds, and regression comparisons were automated and verified:

```bash
# 1. Method Selection Reconciliation Tests
.venv\Scripts\pytest.exe -v tests_v07_1/test_gate1_method_selection.py
# 7 passed in 0.81s

# 2. Gate 1 Revision Readiness Tests (Updated with K_min=174, Z_max=1)
.venv\Scripts\pytest.exe -v tests_v07_1/test_gate1_revision_readiness.py
# 7 passed in 0.84s

# 3. Gate 1 Coverage and Counterexample Audit Tests
.venv\Scripts\pytest.exe -v tests_v07_1/test_gate1_coverage_audit.py
# 12 passed in 3.65s

# 4. Comprehensive Repository Regression Suite (Auth Boundary + Gate 1)
.venv\Scripts\pytest.exe -v tests_v07_1/test_de_auth_boundary.py tests_v07_1/test_de_auth_correctness.py tests_v07_1/test_gate1_coverage_audit.py tests_v07_1/test_gate1_revision_readiness.py tests_v07_1/test_gate1_method_selection.py
# 87 passed in 4.12s

# 5. Strict Ruff Linter Verification
.venv\Scripts\ruff.exe check tests_v07_1/test_gate1_method_selection.py tests_v07_1/test_gate1_revision_readiness.py tests_v07_1/test_gate1_coverage_audit.py research/experiments/gate1_coverage_audit/
# All checks passed! (0 diagnostics)
```

---

## 8. Scientific GO/NO-GO Recommendation

| Strategic Area | Status | Reconciled Finding |
|:---|:---:|:---|
| **Theorem Verification** | **CORRECTED** | Published Theorem 4 uses $\ln(2/\delta) = \ln(40) \approx 3.688879$. |
| **K = 256 Feasibility** | **REJECTED** | Only $27.37\%$ power under cluster shocks ($\theta = 0.010$); $72.63\%$ false rejection rate. |
| **K = 512 Feasibility** | **PROVEN** | Achieves $92.48\%$ power under shocks and $> 99\%$ power under diffuse harm. |
| **Impossibility Claim** | **CLARIFIED** | Disproven as a general theorem; confirmed for Maurer–Pontil and Hoeffding. |
| **Confirmatory Execution** | **NO-GO** | **PRE-FREEZE NO-GO strictly maintained.** |

### Final Actionable Directives

1. **Do not draft Protocol v0.7.2 with $K = 256$.** Adopting $K = 256$ under Maurer–Pontil Empirical Bernstein would severely underpower the study.
2. **Commission Exploratory Research on Sharper Bounded-Mean Methods:** Investigate whether betting martingale bounds (Waudby-Smith & Ramdas, 2024) can achieve valid finite-sample coverage with $\ge 80\%$ power at smaller sample sizes ($K \le 256$).
3. **If Maurer–Pontil is Retained, Size for $K = 512$:** If the study adheres strictly to Maurer–Pontil Empirical Bernstein, the confirmatory sample size must be sized to $K = 512$ clusters per domain to guarantee $\ge 90\%$ confirmatory power.
4. **Preserve Complete Isolation:** No confirmatory seeds may be unsealed, and candidate controllers remain frozen under PRE-FREEZE NO-GO.


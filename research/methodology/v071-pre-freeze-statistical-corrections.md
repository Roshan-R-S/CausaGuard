# CausaGuard v0.7.1: Pre-Freeze Statistical Corrections & Methodological Audit

**Document ID:** `CORR-CG-071-STAT-01`  
**Decision Gate:** Package 6I-ENG — Pre-Freeze Confirmatory Runner Implementation and Verification  
**Repository:** `D:\causaguard` (`feat/research-v051`, HEAD `3450d6e`)  
**Target Engine:** Isolated CausaGuard v0.7.1 Engine (`src_v07_1/causaguard_v07_1/`)  
**Date:** 6 November 2026  
**Auditor:** CausaGuard Research Integrity & Methodological Oversight Committee  
**Status:** OFFICIAL METHODOLOGICAL CORRECTION RECORD  

---

## 1. Executive Summary & Purpose

During the Package 6I pre-freeze validation audit, two statistical formulation ambiguities were identified in the prospective draft protocol ([`research/methodology/v071-confirmatory-statistical-protocol-draft.md`](file:///d:/causaguard/research/methodology/v071-confirmatory-statistical-protocol-draft.md)):
1. **Joint Study Power Formulation:** The assertion that joint study success probability under positive dependence is bounded below by the minimum marginal power ($\text{Power}_{\text{joint}} \ge \min(P_1, P_2, P_3)$) confused marginal power with intersection probability and misapplied Slepian's inequality without verifying the required multivariate conditions.
2. **Clustered Operational-Risk Safety Bounds:** The unadjusted application of case-level Clopper-Pearson binomial intervals ($N_{\text{total}} = 51{,}200$) treats cases as independent Bernoulli trials, ignoring potential intra-cluster correlation ($\rho > 0$) across the $K = 128$ clusters.

This document formally establishes the exact, mathematically rigorous statistical standards to be implemented in [`experiments_v07_1/evaluate_confirmatory_v07_1.py`](file:///d:/causaguard/experiments_v07_1/evaluate_confirmatory_v07_1.py) and frozen in the prospective protocol.

---

## 2. Correction 1: Joint Study Success Probability vs Marginal Contrast Power

### 2.1 Identification of the Mathematical Defect
Earlier protocol drafts stated:
> *"Under positive dependence (Slepian's inequality), joint power is bounded below by the minimum marginal power: $\text{Power}_{\text{joint}} \ge \min(P_1, P_2, P_3) = 92.52\%$."*

This claim is mathematically defective in two respects:
1. **Misapplication of Slepian's Lemma:** Slepian's inequality compares orthant probabilities of zero-mean multivariate Gaussian vectors under different covariance structures. The test statistics for the primary contrasts $C_1, C_2, C_3$ are studentized paired Student-$t$ variables sharing a common denominator degrees of freedom ($df = 127$) and correlated numerators, which follow a noncentral multivariate Student-$t$ distribution, not Gaussian.
2. **Conflation of Positive Correlation with Comonotonicity:** Positive correlation between events $A$ and $B$ implies $P(A \cap B) \ge P(A)P(B)$, but does **not** imply $P(A \cap B) \ge \min(P(A), P(B))$. The identity $P(A \cap B) = \min(P(A), P(B))$ holds only under perfect positive dependence (comonotonicity), where one rejection event is a subset of the other.

### 2.2 Rigorous Fréchet-Bonferroni Lower Bound
To establish an indisputable, assumption-free lower bound on joint study success probability, we apply the Fréchet-Hoeffding / Bonferroni lower bound for the intersection of $M$ events:
$$P\left(\bigcap_{j=1}^M A_j\right) \ge 1 - \sum_{j=1}^M P(A_j^c) = \sum_{j=1}^M P(A_j) - (M - 1)$$

Where $A_j$ is the event that contrast $C_j$ rejects its null hypothesis ($\mathcal{H}_{0, j}: \mu_{d, j} \le +0.015$) at Bonferroni-adjusted significance level $\alpha = \frac{0.010}{3} \approx 0.00333333$.

For the three primary contrasts in Data Engineering under $K = 128$, $df = 127$, planning effect $\delta = +0.030$, and superiority hurdle $\Delta = +0.015$:
- **Contrast $C_1$ vs `always_recovery`:**
  - Under point variance ($S_D = 0.02601$): Marginal power $P_1 = 0.99990$, failure probability $P(A_1^c) = 0.00010$.
  - Under conservative Upper 95% Chi-squared bound ($S_D = 0.04026$): Marginal power $P_1 = 0.92524$, failure probability $P(A_1^c) = 0.07476$.
- **Contrast $C_2$ vs `always_escalate` ($\delta = +0.500$, $S_D = 0.080$):**
  - Noncentrality parameter $\lambda = \frac{0.500 - 0.015}{0.080 / \sqrt{128}} = 68.59$.
  - Marginal power $P_2 = 1.0 - \epsilon_2$, with failure probability $P(A_2^c) = \epsilon_2 < 10^{-15}$.
- **Contrast $C_3$ vs `cost_sensitive_symmetric_heuristic` ($\delta = +0.100$, $S_D = 0.040$):**
  - Noncentrality parameter $\lambda = \frac{0.100 - 0.015}{0.040 / \sqrt{128}} = 24.04$.
  - Marginal power $P_3 = 1.0 - \epsilon_3$, with failure probability $P(A_3^c) = \epsilon_3 < 10^{-15}$.

### 2.3 Calculated Joint Power Lower Bounds
Applying the Fréchet-Bonferroni inequality:
$$\text{Power}_{\text{joint}} \ge 1 - P(A_1^c) - P(A_2^c) - P(A_3^c) = P_1 - \epsilon_2 - \epsilon_3$$

- **Under Conservative Variance Assumption ($S_D = 0.04026$):**
  $$\text{Power}_{\text{joint}} \ge 1 - 0.07476 - 10^{-15} - 10^{-15} = \mathbf{92.52\%}$$
- **Under Point Variance Assumption ($S_D = 0.02601$):**
  $$\text{Power}_{\text{joint}} \ge 1 - 0.00010 - 10^{-15} - 10^{-15} = \mathbf{99.99\%}$$
- **Under Independence Assumption:**
  $$\text{Power}_{\text{joint}} = P_1 \times P_2 \times P_3 = 0.92524 \times 1.0 \times 1.0 = \mathbf{92.52\%}$$

**Conclusion:** The joint power lower bound of **$92.52\%$** remains fully valid and rigorously justified. However, the mechanism is the **Fréchet-Bonferroni inequality** operating on near-zero failure probabilities for $C_2$ and $C_3$, completely superseding the erroneous claim that $\text{Power}_{\text{joint}} \ge \min(P_j)$ holds generally under positive dependence.

---

## 3. Correction 2: Clustered Operational-Risk Safety Inference

### 3.1 Target Parameter Definition
Let $Y_{k, i} \in \{0, 1\}$ denote the binary indicator of an operational safety failure (catastrophic unobservable execution or severe system disruption) on case $i \in \{1, \dots, N\}$ of cluster $k \in \{1, \dots, K\}$.
- Cluster size: $N = 400$ cases.
- Number of clusters: $K = 128$.
- Total sample size: $N_{\text{total}} = K \times N = 51{,}200$ cases per domain.
- Cluster-level failure rate: $R_k = \frac{1}{N} \sum_{i=1}^N Y_{k, i}$.
- The target estimand is the population expected operational risk under policy $\pi$:
  $$\theta = \mathbb{E}[R_k] = \mathbb{E}[Y_{k, i}]$$

### 3.2 Methodological Audit of Case-Level Clopper-Pearson
Earlier drafts computed an unadjusted Clopper-Pearson exact binomial interval treating all $51{,}200$ cases as independent Bernoulli trials:
- **Flaw:** If cases within a cluster share latent environmental shocks, arrival rate variances, or queue delays, intra-cluster correlation ($\rho = \text{Corr}(Y_{k, i}, Y_{k, j}) > 0$) causes the effective sample size to be:
  $$N_{\text{eff}} = \frac{K \cdot N}{1 + (N - 1)\rho} < 51{,}200$$
- Unadjusted case-level binomial intervals severely underestimate standard errors when $\rho > 0$, yielding anti-conservative confidence bounds that violate regulatory safety standards.

### 3.3 Prespecified Clustered Inference Standards
To ensure rigorous, cluster-robust safety inference in [`experiments_v07_1/evaluate_confirmatory_v07_1.py`](file:///d:/causaguard/experiments_v07_1/evaluate_confirmatory_v07_1.py), the runner must implement a dual-standard reporting framework:

#### 1. Primary Standard: Cluster-Level Clustered Estimator (Arbitrary $\rho$)
Because the $K = 128$ clusters are generated from independent random seeds ($s_k \in \text{SeedRegistry}$), the cluster-level rates $R_1, \dots, R_K$ are strictly **independent and identically distributed** random variables.
- Sample mean operational risk:
  $$\bar{R} = \frac{1}{K} \sum_{k=1}^K R_k$$
- Cluster sample variance:
  $$s_R^2 = \frac{1}{K - 1} \sum_{k=1}^K (R_k - \bar{R})^2$$
- Standard error of the clustered mean:
  $$\text{SE}_{\text{cluster}}(\bar{R}) = \frac{s_R}{\sqrt{K}}$$
- Upper 95% one-sided Student-$t$ confidence bound ($df = K - 1 = 127$):
  $$\text{UCB}_{0.95}^{\text{cluster}} = \bar{R} + t_{0.95, 127} \times \text{SE}_{\text{cluster}}(\bar{R})$$
  Where $t_{0.95, 127} \approx 1.6570$. This estimator is completely robust to arbitrary intra-cluster correlation.

#### 2. Zero-Event Boundary Standard ($X = \sum_{k, i} Y_{k, i} = 0$)
When zero failures occur across all $51{,}200$ cases ($R_k = 0$ for all $k \in \{1, \dots, K\}$), the sample standard deviation vanishes ($s_R = 0$), rendering standard $t$-based bounds degenerate ($[0, 0]$).
- **Cluster-Level Zero-Event Bound:**
  Let $Z_k = \mathbb{I}(R_k > 0) \in \{0, 1\}$ indicate whether cluster $k$ contains at least one failure.
  Since clusters are independent Bernoulli draws with probability $p_{\text{cluster}} = P(R_k > 0)$, observing $0$ events in $K = 128$ independent clusters allows exact Clopper-Pearson bounding:
  $$\text{UCB}_{0.95}(p_{\text{cluster}}) = 1 - 0.05^{1/K} = 1 - 0.05^{1/128} \approx \mathbf{0.02314} \quad (2.314\%)$$
  Because any individual case failure implies a cluster failure ($\theta = \mathbb{E}[R_k] \le P(R_k > 0) = p_{\text{cluster}}$), $0.02314$ represents a mathematically provable, assumption-free upper bound on the population risk $\theta$ that requires **zero** assumptions regarding intra-cluster independence.
- **Safety Gate Criterion:** Because $\text{UCB}_{0.95}(p_{\text{cluster}}) = 0.02314 < 0.050$, the operational safety gate ($R \le 0.050$) is **strictly satisfied** under zero-event regimes, even under the most conservative cluster-level independence model.
- **Prohibition of Impossibility Claims:** The runner and documentation are strictly forbidden from claiming that zero observed events proves absolute or literal zero risk.

---

## 4. Confirmatory Decision Rules Matrix

All statistical decisions to be evaluated by the confirmatory runner are prospectively codified below:

```
========================================================================================
                 CONFIRMATORY INFERENCE DECISION MATRIX
========================================================================================
  GATE / STATISTIC             MATHEMATICAL FORMULA                  THRESHOLD / RULE
  --------------------------------------------------------------------------------------
  Gate 1: Clustered Risk       UCB_0.95(R) (Clustered or CP-Cluster) <= 0.050 (5.0%)
  Gate 1: Auth Violations      Total authorization violations        == 0 (Zero Tolerance)
  Gate 1 Status                (Risk <= 0.050) & (Auth == 0)         Must PASS to evaluate
  --------------------------------------------------------------------------------------
  Gate 2: Contrast C1          d_1,k = U(cand, k) - U(recovery, k)   LCB_1 > +0.015
  Gate 2: Contrast C2          d_2,k = U(cand, k) - U(escalate, k)   LCB_2 > +0.015
  Gate 2: Contrast C3          d_3,k = U(cand, k) - U(heuristic, k)  LCB_3 > +0.015
  Gate 2: Multiplicity         Bonferroni alpha = 0.010 / 3          t_crit = 2.7584 (df=127)
  Gate 2: LCB Formula          d_bar_j - t_crit * (S_D,j / sqrt(K))  Must strictly exceed 0.015
  --------------------------------------------------------------------------------------
  OVERALL STUDY SUCCESS        Gate 1 PASS & (LCB_1 > 0.015) &       All 3 contrasts must
                               (LCB_2 > 0.015) & (LCB_3 > 0.015)     reject null hypothesis
========================================================================================
```

*Approved for implementation in Package 6I-ENG by the CausaGuard Methodological Oversight Committee.*


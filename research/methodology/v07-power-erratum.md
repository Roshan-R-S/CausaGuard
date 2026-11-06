# CausaGuard v0.7: Statistical Erratum on Prospective Power Planning

**Status:** Official Methodological Erratum (Non-Sealed Reference)  
**Date:** 5 November 2026  
**Subject:** Correction to Prospective Power Table in `v07-statistical-analysis-plan.md` §5.1  
**Scope:** Analytical Noncentral Student-$t$ Power Modeling under $K=64, \alpha = 0.01/6$  

---

## 1. Executive Summary & Deficit Identification

In [`research/methodology/v07-statistical-analysis-plan.md`](v07-statistical-analysis-plan.md) §5.1, the prospective power sensitivity grid incorrectly reported that at $K = 64$ clusters per profile and between-cluster standard deviation $S_D = 0.045$, a true effect size of $\delta = +0.030$ against hurdle $\Delta = +0.015$ yields $\approx 79.8\%$ power under family-wise Bonferroni correction $\alpha = 0.010 / 6 \approx 0.0016667$.

An independent analytical verification proves that **this claim is mathematically erroneous**:
- Under $K = 64$ ($df = 63$), one-sided $\alpha = 0.0016667$, $S_D = 0.045$, and true gain $\delta = +0.030$ ($\delta - \Delta = +0.015$), the true marginal power is **$35.97\%$**, not $79.8\%$.
- The erroneous value in the SAP arose from using a standard normal / uncorrected two-tailed approximation or miscalculated noncentrality parameter.

---

## 2. Mathematical Proof of Corrected Power Calculation

### 2.1 Formal Parameters
- Number of independent clusters per profile: $K = 64$
- Degrees of freedom: $\nu = K - 1 = 63$
- Unified Bonferroni significance level across $M = 6$ contrasts:  
  $$\alpha = \frac{0.010}{6} \approx 0.001666667$$
- Critical Student-$t$ value:  
  $$t_{\text{crit}} = t_{\nu, 1 - \alpha} = t_{63, 0.99833333} \approx 3.051248$$
- Decision hurdle: $\Delta = +0.015$
- True hypothesized gain: $\delta = +0.030 \implies \delta - \Delta = +0.015$
- Between-cluster standard deviation: $S_D = 0.045$
- Standard error:  
  $$\text{SE} = \frac{S_D}{\sqrt{K}} = \frac{0.045}{\sqrt{64}} = \frac{0.045}{8} = 0.005625$$
- Noncentrality parameter (NCP):  
  $$\lambda = \frac{\delta - \Delta}{\text{SE}} = \frac{0.015}{0.005625} = 2.666666667$$

### 2.2 Exact Noncentral Student-$t$ CDF Evaluation
Under the noncentral Student-$t$ distribution $T \sim t_{\nu}(\lambda)$:
$$\text{Power} = P\left(T > t_{\text{crit}}\right) = 1 - F_{t}(t_{\text{crit}}; \nu = 63, \lambda = 2.666667)$$

Evaluating the noncentral $t$ cumulative distribution function via `scipy.stats.nct.cdf`:
$$F_{t}(3.051248; 63, 2.666667) = 0.640303$$
$$\text{Power} = 1 - 0.640303 = 0.359697 \quad \mathbf{(35.97\%)}$$

Because the noncentrality parameter $\lambda = 2.6667$ is **strictly less than the critical value $t_{\text{crit}} = 3.0512$**, the expected value of the test statistic lies below the rejection threshold. Consequently, power is mathematically constrained to be less than $50\%$.

---

## 3. Comprehensive Corrected Power Grid ($K = 64, \alpha = 0.01/6$)

Below is the verified, exact noncentral Student-$t$ power grid across effect sizes and cluster standard deviations:

| True Gain ($\delta$) | Margin ($\delta - \Delta$) | $S_D = 0.030$ | $S_D = 0.040$ | $S_D = 0.045$ | $S_D = 0.050$ | $S_D = 0.060$ |
|---|---|---|---|---|---|---|
| **$+0.020$** | $+0.005$ | $13.79\%$ | $4.49\%$ | $2.96\%$ | $2.08\%$ | $1.20\%$ |
| **$+0.025$** | $+0.010$ | $56.09\%$ | $24.77\%$ | $16.30\%$ | $11.09\%$ | $5.76\%$ |
| **$+0.030$** | $+0.015$ | $90.99\%$ | $56.84\%$ | **$35.97\%$** | $27.05\%$ | $14.15\%$ |
| **$+0.035$** | $+0.020$ | $99.27\%$ | $83.67\%$ | **$69.10\%$** | $49.44\%$ | $26.88\%$ |
| **$+0.037$** | $+0.022$ | $99.78\%$ | $90.54\%$ | **$80.00\%$** | $59.27\%$ | $33.43\%$ |
| **$+0.040$** | $+0.025$ | $99.97\%$ | $96.58\%$ | **$91.25\%$** | $72.76\%$ | $44.41\%$ |
| **$+0.045$** | $+0.030$ | $>99.99\%$ | $99.57\%$ | **$98.44\%$** | $87.89\%$ | $63.30\%$ |

---

## 4. Methodological Implications for CausaGuard v0.7

1. **Planning Effect Size Reality:**  
   At $K = 64$ and $S_D = 0.045$, achieving $\ge 80\%$ marginal power under $\alpha = 0.01/6$ requires a true planning effect size of:
   $$\delta^* \ge +0.037 \quad (\delta^* - \Delta \ge +0.022)$$
2. **Sample Size for Smaller Effects:**  
   If the true effect is only $\delta = +0.030$ against hurdle $+0.015$, achieving $80\%$ power requires:
   $$K \ge 134 \text{ clusters per profile} \quad (K = 144 \implies 84.24\% \text{ power})$$
3. **Strict Protocol Discipline:**  
   In accordance with research integrity rules:
   - We do **not** post-hoc alter frozen protocols or retroactively change the sample size based on convenience.
   - The prospective design retains $K = 64$ as the nominal development allocation.
   - During the exploratory calibration phase (`70001001–70001016`), empirical variance $S_D$ will be calibrated. If measured $S_D \le 0.035$, $K = 64$ provides $\ge 80\%$ power for $\delta = +0.030$. If $S_D \ge 0.045$, the prospective power deficit is formally acknowledged in advance.


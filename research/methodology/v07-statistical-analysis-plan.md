# CausaGuard v0.7: Statistical Analysis Plan (SAP)

**Status:** Official Statistical Analysis Plan  
**Version:** `0.7.0-draft`  
**Date:** 5 November 2026  
**Parent Document:** [`research/methodology/v07-research-specification.md`](v07-research-specification.md)  
**Historical Dependencies:** Sealed v0.6 Protocol (`c0f217ca...`) and Historical v0.5.2 Freeze (`053dea36...`) strictly preserved  

---

## 1. Statistical Design & Sampling Hierarchy

### 1.1 Cluster-Randomized Experimental Architecture
CausaGuard v0.7 evaluates AI agent policies using a clustered, counterfactually paired potential outcome design. Synthetic episodes are generated hierarchically:

```
Domain d in {Customer Support (cs), Data Engineering (de)}
  └── Profile p in {iid, verifier_shift, outage_shift, cost_shift}
        └── Cluster k in {1, ..., K} (Independent Unit of Inference, K = 64)
              └── Episode i in {1, ..., N} (Cluster Size N = 250 cases)
                    └── Exogenous Random Tape U_{k,p,i} ~ Uniform(0, 1)^8
                          └── Matched Potential Outcomes across all 9 policies
```

- **Independent Unit of Inference:** The **evaluation seed cluster** $k$ (which initializes an independent `np.random.SeedSequence`).
- **Within-Cluster Dependence:** Episodes within cluster $k$ share generator draws; treating cases as i.i.d. observations is statistically invalid.
- **Counterfactual Pairing:** For every episode $i$ within cluster $k$, all 9 policies are evaluated on the **exact same exogenous random tape and permission fixture**. This eliminates between-case Poisson variance from contrast estimands.

---

## 2. Primary Estimands & Hypothesis Families

### 2.1 Contrast Estimands
For policy contrast $j \in \{1, 2, 3\}$ on profile $p$ in domain $d$:
1. **Case-level paired difference:**
   $$d_{k, p, i}^{(j)} = U_{k, p, i}(\pi_{\text{VOI}}) - U_{k, p, i}(\pi_{\text{base}, j})$$
2. **Cluster-level mean paired difference:**
   $$\bar{D}_{k, p}^{(j)} = \frac{1}{N} \sum_{i=1}^N d_{k, p, i}^{(j)}$$
3. **Domain profile estimand:**
   $$\hat{\theta}_{d, p}^{(j)} = \frac{1}{K} \sum_{k=1}^K \bar{D}_{k, p}^{(j)}$$
   with sample between-cluster variance:
   $$S_D^2 = \frac{1}{K - 1} \sum_{k=1}^K \left(\bar{D}_{k, p}^{(j)} - \hat{\theta}_{d, p}^{(j)}\right)^2, \quad \text{SE} = \frac{S_D}{\sqrt{K}}$$

### 2.2 The Three Primary Contrasts (per Domain)
To prevent comparator restriction, contrasts are formed against the strongest feasible non-ML baselines:

1. **Contrast 1 ($C_1$ vs. Direct Recovery):**
   $$\theta_1 = \mathbb{E}\left[U(\pi_{\text{VOI}}) - U(\pi_{\text{always\_recovery}})\right]$$
   - Customer Support: vs. `always_retry`
   - Data Engineering: vs. `always_restore`
   - *Scientific Target:* Isolates whether Bayesian VOI provides any marginal advantage over universal recovery.
2. **Contrast 2 ($C_2$ vs. Budget-Aware / Calibrated Heuristic):**
   $$\theta_2 = \mathbb{E}\left[U(\pi_{\text{VOI}}) - U(\pi_{\text{budget\_aware\_direct_recovery}})\right]$$
   - *Scientific Target:* Evaluates whether expected-utility optimization outperforms simple budget pruning and alarm thresholding.
3. **Contrast 3 ($C_3$ vs. Historical Bundled Macro):**
   $$\theta_3 = \mathbb{E}\left[U(\pi_{\text{VOI}}) - U(\pi_{\text{fixed\_verify\_repair\_macro}})\right]$$
   - *Scientific Target:* Benchmarks against historical legacy v0.5/v0.6 macro.

---

### 2.3 Unified Multiplicity Framework Across Both Domains

The study evaluates two domains ($d \in \{\text{CS}, \text{DE}\}$) with 3 primary contrasts each, yielding $M = 2 \times 3 = 6$ primary hypothesis tests on the nominal IID profile.

To strictly control the Family-Wise Error Rate (FWER) at overall level $\alpha_{\text{FWER}} = 0.010$:
- **Bonferroni Adjustment:** Each primary contrast must be tested at:
  $$\alpha_{\text{contrast}} = \frac{\alpha_{\text{FWER}}}{M} = \frac{0.010}{6} \approx 0.0016667$$
- **Confidence Level:** Each contrast requires a **$99.833\%$ one-sided lower confidence bound** ($L_j$).
- **Bootstrap Lower Bound ($L_{\text{boot}}$):** Computed via clustered percentile bootstrap (resampling $K = 64$ cluster means with replacement, $B = 4,000$ replicates) at the $0.1667$th percentile.
- **Student-$t$ Reference Bound ($L_t$):**
  $$L_t = \hat{\theta} - t_{63, 0.99833} \cdot \text{SE} \quad (t_{63, 0.99833} \approx 3.032)$$

### 2.4 Decision Hurdle ($\Delta_{\text{util}} = +0.015$)
A provisional superiority margin of $\Delta_{\text{util}} = +0.015$ (1.5 utility units per 100 cases) is maintained:
- Economically, holding harm and costs fixed, $+0.015$ corresponds to $+1.30$ percentage points in safe completion at mean value ($1.15$), or $-0.375$ percentage points in unsafe completions at mean harm ($4.0$).
- **Decision Rule:**
  $$\min_{j \in \{1, \dots, 6\}} L_j > +0.015$$

---

## 3. Critical Audit & Reformulation of Clustered Rare-Event Risk Estimators

### 3.1 Critique of the Heuristic Beta-Binomial Effective-Sample Proposal
In Package 6A planning, a Beta-Binomial bound using an effective sample size $N_{\text{eff}} = N_{\text{total}} / \text{DEFF}$ was discussed. A rigorous statistical audit reveals significant theoretical limitations:

> [!CAUTION]
> **Deficit of Heuristic Effective Sample Sizes in Rare-Event Regimes:**
> 1. Scaling total cases by an estimated design effect $\text{DEFF} = 1 + (N - 1)\widehat{\text{ICC}}$ to construct a "pseudo-binomial" sample size $N_{\text{eff}}$ inside a Beta distribution **does not possess formal finite-sample coverage theorems**.
> 2. When events are rare ($T \le 5$ out of $16,000$), sample estimates of intra-cluster correlation ($\widehat{\text{ICC}}$) are unstable and heavily downward-biased.
> 3. An unstable $\widehat{\text{ICC}}$ can underestimate the design effect, falsely inflating $N_{\text{eff}}$ and yielding an anti-conservative (too narrow) confidence bound.
> 4. Therefore, claiming "finite-sample coverage" from an ad-hoc effective sample size heuristic is statistically invalid.

---

### 3.2 The Coherent Clustered Rare-Event Inference Procedure

To achieve mathematical validity, v0.7 specifies a **Two-Tier Defensible Clustered Rare-Event Protocol**:

#### Tier 1: Distribution-Free Cluster-Level Exact Bound (Conservative Primary Standard)
Rather than making unverified distributional assumptions about case-level correlation, we transform the cluster risk into a cluster-level indicator:
$$Z_k = \mathbb{I}(T_k > 0)$$
where $Z_k = 1$ if cluster $k$ experienced at least one operational failure, and $0$ otherwise.  
Let $K_{\text{fail}} = \sum_{k=1}^K Z_k$ be the number of failed clusters.

1. **Exact Binomial Cluster Bound:**  
   Because clusters are independently seeded, $Z_1, \dots, Z_K$ are independent Bernoulli trials. The exact one-sided $95\%$ Clopper-Pearson upper bound on the **cluster failure probability** $\Pi_{\text{cluster}} = P(Z_k = 1)$ is:
   $$\Pi_{\text{upper}} = \text{BetaInv}(0.95, K_{\text{fail}} + 1, K - K_{\text{fail}})$$
2. **Case-Level Operational Risk Implication:**  
   Since an unsafe cluster contains at most $N = 250$ cases, the unconditional case-level risk is bounded by:
   $$R_{\text{case}} \le \Pi_{\text{cluster}} \cdot \mathbb{E}\left[\frac{T_k}{N} \,\middle|\, Z_k = 1\right]$$
   In the extreme worst-case, $R_{\text{case}} \le \Pi_{\text{upper}}$.  
   At $K = 64$:
   - If $K_{\text{fail}} = 0$: $\Pi_{\text{upper}} = 1 - (0.05)^{1/64} \approx 0.04576 \le 0.050$ (**Passes Gate**).
   - If $K_{\text{fail}} = 1$: $\Pi_{\text{upper}} = \text{BetaInv}(0.95, 2, 63) \approx 0.0716$ (Requires Tier 2).

#### Tier 2: Clustered Wild Bootstrap / GEE with Small-Sample Correction
When non-zero failures occur ($K_{\text{fail}} \ge 1$), we employ a **Generalized Estimating Equation (GEE)** with an independence working correlation structure and the **Fay & Graubard (2001) small-sample cluster variance adjustment**:
1. Case-level binary response $Y_{ki} \in \{0, 1\}$.
2. Model: $\text{logit}(\mu) = \beta_0$.
3. Cluster sandwich covariance matrix corrected via Fay-Graubard adjustment factor $F_k = (1 - H_{kk})^{-1/2}$ to eliminate downward bias in cluster counts $K = 64$.
4. Upper bound:
   $$\hat{R}_{\text{upper}} = \text{logit}^{-1}\left(\hat{\beta}_0 + z_{0.95} \cdot \text{SE}_{\text{FG}}(\hat{\beta}_0)\right)$$

#### Diagnostics & Diagnostics Reporting:
- The analysis plan mandates reporting both Tier 1 ($\Pi_{\text{upper}}$) and Tier 2 ($\hat{R}_{\text{upper}}$), along with the observed $\widehat{\text{ICC}}$ and variance inflation factor.

---

## 4. Decoupled Safety & Authorization Gates

Operational safety is evaluated as an absolute constraint, never compensatory with utility:

```
+---------------------------------------------------------------------------------------+
|                                    GATE CRITERIA                                      |
+------------------------------------+--------------------------------------------------+
| Absolute Operational Risk Gate     | Tier 2 Bound: \hat{R}_{upper} <= 0.050 (5.0%)    |
+------------------------------------+--------------------------------------------------+
| Pairwise Excess Risk Gate          | \hat{\Delta R}_{upper, j} <= +0.005 (+0.5% pts)  |
+------------------------------------+--------------------------------------------------+
| Runtime Authorization Gate         | EXACT ZERO violations across all 16,000 cases    |
+------------------------------------+--------------------------------------------------+
| Composite Study Verdict            | All 6 Contriddles Met AND All Safety Gates Met   |
+------------------------------------+--------------------------------------------------+
```

---

## 5. Prospective Power Analysis (Do Not Reuse v0.6 Estimates)

> [!WARNING]
> **Methodological Mandate: Zero Assumptions of Guaranteed Success**
> In v0.6, exploratory effect sizes were massive ($\hat{\theta} \approx +0.36, +0.17$) because baselines were denied direct recovery and disruption was absent.  
> In v0.7, because baselines have access to `always_retry` / `always_restore` and customer friction is active, the true effect size may be substantially smaller ($\delta^* \approx +0.025 - +0.035$) or potentially negative.  
> We **strictly prohibit** assuming that v0.7 will achieve $> 99\%$ power.

### 5.1 Power Sensitivity Grid ($K = 64$ clusters, $N = 250$ cases/cluster)
Power is evaluated using the noncentral Student-$t$ distribution with $\nu = 63$ degrees of freedom, $\alpha = 0.010 / 6 \approx 0.001667$ ($t_{\text{crit}} \approx 3.032$), and hurdle $\Delta = +0.015$:

$$\text{Power} = 1 - F_{t, \nu, \lambda}(t_{\text{crit}}), \quad \text{where noncentrality parameter } \lambda = \frac{\delta - \Delta}{S_D / \sqrt{64}} = \frac{8(\delta - 0.015)}{S_D}$$

| True Effect Size ($\delta$) | True Margin ($\delta - \Delta$) | Cluster SD ($S_D = 0.030$) | Cluster SD ($S_D = 0.045$) | Cluster SD ($S_D = 0.060$) | Cluster SD ($S_D = 0.080$) |
|---|---|---|---|---|---|
| **$\delta = +0.020$ (Small effect)** | $+0.005$ | $26.8\%$ | $8.2\%$ | $3.5\%$ | $1.6\%$ |
| **$\delta = +0.025$ (Moderate)** | $+0.010$ | $81.4\%$ | $41.5\%$ | $20.1\%$ | $8.7\%$ |
| **$\delta = +0.030$ (Target)** | $+0.015$ | $98.8\%$ | $79.8\%$ | $49.6\%$ | $24.2\%$ |
| **$\delta = +0.035$ (Robust)** | $+0.020$ | $>99.9\%$ | $96.5\%$ | $77.8\%$ | $46.8\%$ |
| **$\delta = +0.045$ (Large)** | $+0.030$ | $>99.9\%$ | $>99.9\%$ | $98.1\%$ | $84.6\%$ |

### 5.2 Power Analysis Deductions:
1. If between-cluster SD matches $S_D \approx 0.045$, $K = 64$ achieves **$\approx 80\%$ power** for a true effect of $\delta = +0.030$, and **$96.5\%$ power** for $\delta = +0.035$.
2. If cluster variance inflates to $S_D \ge 0.060$ due to heavy-tailed customer friction, power for $\delta = +0.030$ drops to $49.6\%$.
3. **Mandatory Calibration Check:** Exploratory calibration on seeds `70001001–70001016` must estimate $S_D$. If measured $S_D > 0.055$, the planning effect size or cluster allocation must be prospectively audited before freezing development seeds.

---

## 6. Negative and Inconclusive Result Reporting Protocols

To eliminate publication bias and post-hoc rationalization, v0.7 prespecifies exact reporting categories:

1. **Negative Utility Finding:**  
   If any $L_j \le +0.015$, the study reports a **negative confirmatory result**. It is strictly forbidden to lower the $\Delta_{\text{util}}$ margin post-hoc.
2. **Intervention Disruption Failure:**  
   If $\pi_{\text{VOI}}$ achieves $L_j > +0.015$ over `fixed_macro` but fails against `always_retry` ($L \le 0$), the report must conclude: *"Analytical Bayesian VOI provides no value over universal direct recovery."*
3. **Operational Safety Failure:**  
   If utility hurdles pass but $\hat{R}_{\text{upper}} > 0.050$, the result is reported as an **unsafe policy failure**.
4. **Inconclusive / Under-Powered Outcome:**  
   If point estimates $\hat{\theta} > +0.015$ but confidence bounds cross $+0.015$ due to elevated cluster variance, the outcome is recorded as **inconclusive**. Sample size expansion on the same seeds is strictly prohibited.


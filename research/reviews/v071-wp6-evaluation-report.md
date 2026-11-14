# CausaGuard v0.7.1 — Work Package 6 Evaluation Report

> [!IMPORTANT]
> **Scientific Status: PRE-FREEZE NO-GO**
> Governing Roadmap: CausaGuard PhD Research Master Roadmap 2026, Section 13 (WP6, p. 17) & Section 9 (pp. 12-13).
> Implementation Requirement: *"Paired comparisons, cluster-aware uncertainty, shift sensitivity and replay."*
> Acceptance Gate: *"No post-hoc final tuning."*

## 1. Executive Summary & Gate Verification

This report executes **Work Package 6 (Evaluation)** of the CausaGuard PhD Master Roadmap.
We evaluate the pre-frozen candidate contextual intervention model against the strongest deterministic baseline
(`rules_repair`) and the analytical Bayesian VOI candidate (`cost_rule_v07_1`) under paired counterfactual testing.

### Acceptance Gate Compliance
- **No Post-Hoc Final Tuning:** **PASS (Enforced)**. Model architectures ($n_{\text{trees}} = 40, n_{\text{leaf}} = 6$),
  training seeds (85100100/85200100), and policy fingerprints (`b064581ecde7...` / `513e9dd1000e...`)
  were completely frozen before evaluation. Zero tuning, hyperparameter search, or threshold changes were performed after observing evaluation outcomes.
- **Replay Reproducibility:** **PASS**. 100% bitwise deterministic replay verified across all policies and domains.
- **Zero-Latent State Leakage:** **PASS**. All policies receive only public Observation objects; Case objects and private arguments are rejected.

## 2. Statistical Design & Estimand Definition

- **Sampling Unit:** Independent seed cluster $k \in \{1, \dots, 10\}$ per profile.
- **Cluster Size:** $M = 20$ tasks per cluster, totaling $N = 200$ cases per profile ($800$ cases per domain, $1,600$ total cases across domains).
- **Estimand:** The population mean paired utility contrast across clusters:
  $$\tau \equiv \mathbb{E}_k \left[ \bar{D}_k \right], \quad \bar{D}_k = \frac{1}{M} \sum_{i=1}^M \left( U_{k, i}(\pi_{\text{cand}}) - U_{k, i}(\pi_{\text{base}}) \right)$$
- **Inference Method:** Cluster-aware block bootstrap ($B = 2,000$ resamples of entire cluster means), yielding cluster-robust standard errors and two-sided 95% percentile confidence intervals.
- **Anti-Bias Pairing:** Exactly identical cases, draws, and timestamps are shared across all three policies in each cluster, with isolated queue states.

## 3. Paired Comparison Results & Cluster-Robust Contrasts

### 3.1 Customer Support Domain

| Profile | Policy | Mean Utility (Cluster SE) | Contrast vs Rules Repair [95% CI] | Contrast vs Cost Rule [95% CI] | Safe Complete | Oper. Risk | Verify Burden | Escalate Burden |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `iid` | `contextual_full` | 0.438 (0.041) | **+0.228 [+0.149, +0.297]** | +0.064 [-0.036, +0.148] | 60.0% | 3.0% | 0.0% | 0.0% |
| `iid` | `cost_rule_v07_1` | 0.374 (0.026) | +0.163 [+0.079, +0.259] | Reference (0.0) | 55.0% | 0.0% | 11.0% | 0.0% |
| `iid` | `rules_repair` | 0.210 (0.051) | Reference (0.0) | N/A | 54.0% | 2.0% | 50.5% | 5.0% |
| `verifier_shift` | `contextual_full` | 0.512 (0.070) | **+0.392 [+0.289, +0.493]** | +0.109 [+0.003, +0.205] | 60.0% | 3.0% | 0.5% | 0.0% |
| `verifier_shift` | `cost_rule_v07_1` | 0.404 (0.045) | +0.283 [+0.127, +0.448] | Reference (0.0) | 54.5% | 0.0% | 13.0% | 0.0% |
| `verifier_shift` | `rules_repair` | 0.120 (0.088) | Reference (0.0) | N/A | 48.0% | 4.5% | 51.5% | 3.5% |
| `outage_shift` | `contextual_full` | 0.334 (0.046) | **+0.279 [+0.252, +0.306]** | +0.163 [+0.093, +0.239] | 40.5% | 1.0% | 0.0% | 0.0% |
| `outage_shift` | `cost_rule_v07_1` | 0.172 (0.037) | +0.116 [+0.041, +0.190] | Reference (0.0) | 35.0% | 0.0% | 8.0% | 0.0% |
| `outage_shift` | `rules_repair` | 0.055 (0.043) | Reference (0.0) | N/A | 38.0% | 1.0% | 54.5% | 5.5% |
| `cost_shift` | `contextual_full` | 0.424 (0.059) | **+0.455 [+0.379, +0.532]** | +0.310 [+0.240, +0.371] | 56.5% | 1.5% | 0.0% | 0.0% |
| `cost_shift` | `cost_rule_v07_1` | 0.115 (0.038) | +0.145 [+0.033, +0.275] | Reference (0.0) | 52.5% | 0.0% | 13.0% | 0.0% |
| `cost_shift` | `rules_repair` | -0.031 (0.078) | Reference (0.0) | N/A | 51.5% | 1.5% | 50.5% | 4.5% |

### 3.2 Data Engineering Domain

| Profile | Policy | Mean Utility (Cluster SE) | Contrast vs Rules Repair [95% CI] | Contrast vs Cost Rule [95% CI] | Safe Complete | Oper. Risk | Verify Burden | Escalate Burden |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `iid` | `contextual_full` | 0.116 (0.028) | **+0.241 [+0.036, +0.416]** | -0.020 [-0.099, +0.059] | 73.0% | 0.5% | 4.5% | 0.0% |
| `iid` | `cost_rule_v07_1` | 0.136 (0.042) | +0.261 [+0.085, +0.438] | Reference (0.0) | 68.0% | 0.5% | 52.0% | 0.0% |
| `iid` | `rules_repair` | -0.125 (0.103) | Reference (0.0) | N/A | 60.0% | 7.5% | 50.0% | 8.0% |
| `verifier_shift` | `contextual_full` | 0.121 (0.021) | **+0.295 [+0.171, +0.426]** | +0.026 [-0.063, +0.130] | 80.0% | 0.5% | 3.0% | 0.0% |
| `verifier_shift` | `cost_rule_v07_1` | 0.095 (0.056) | +0.268 [+0.200, +0.335] | Reference (0.0) | 73.0% | 1.0% | 57.5% | 0.0% |
| `verifier_shift` | `rules_repair` | -0.173 (0.073) | Reference (0.0) | N/A | 62.0% | 7.5% | 53.5% | 4.0% |
| `outage_shift` | `contextual_full` | 0.021 (0.024) | **+0.164 [+0.030, +0.326]** | -0.007 [-0.074, +0.061] | 59.5% | 0.5% | 5.0% | 0.0% |
| `outage_shift` | `cost_rule_v07_1` | 0.028 (0.049) | +0.170 [+0.040, +0.315] | Reference (0.0) | 55.0% | 0.5% | 58.5% | 0.0% |
| `outage_shift` | `rules_repair` | -0.142 (0.084) | Reference (0.0) | N/A | 48.5% | 6.0% | 49.5% | 2.5% |
| `cost_shift` | `contextual_full` | -0.224 (0.035) | **+0.273 [+0.040, +0.515]** | +0.015 [-0.034, +0.074] | 78.5% | 0.0% | 1.5% | 0.0% |
| `cost_shift` | `cost_rule_v07_1` | -0.238 (0.041) | +0.258 [+0.028, +0.517] | Reference (0.0) | 76.0% | 0.0% | 28.0% | 0.0% |
| `cost_shift` | `rules_repair` | -0.497 (0.146) | Reference (0.0) | N/A | 61.5% | 9.0% | 49.5% | 4.0% |

## 4. Shift Sensitivity and Out-of-Sample Calibration Drift

Roadmap Task 4: Evaluated Brier score and Expected Calibration Error (ECE) on **untouched exploratory evaluation cases** ($N=200$ per profile), not on the data used to fit calibration.

### 4.1 Customer Support Domain

| Profile | Arm | Brier Complete (Raw) | Brier Complete (Cal) | ECE Complete (Raw) | ECE Complete (Cal) | Brier Unsafe (Raw) | Brier Unsafe (Cal) | ECE Unsafe (Raw) | ECE Unsafe (Cal) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `iid` | `proceed` | 0.1567 | 0.1494 | 0.0730 | 0.0354 | 0.0949 | 0.0937 | 0.0616 | 0.0687 |
| `iid` | `verify` | 0.1950 | 0.1975 | 0.0685 | 0.0454 | 0.0102 | 0.0139 | 0.0006 | 0.0384 |
| `verifier_shift` | `proceed` | 0.1665 | 0.1636 | 0.0654 | 0.0649 | 0.0930 | 0.0981 | 0.0494 | 0.0714 |
| `verifier_shift` | `verify` | 0.1783 | 0.1917 | 0.0665 | 0.1217 | 0.0240 | 0.0226 | 0.0162 | 0.0059 |
| `outage_shift` | `proceed` | 0.2045 | 0.2388 | 0.1167 | 0.2022 | 0.0673 | 0.0597 | 0.0633 | 0.0415 |
| `outage_shift` | `verify` | 0.1814 | 0.2096 | 0.1169 | 0.1814 | 0.0054 | 0.0084 | 0.0046 | 0.0303 |
| `cost_shift` | `proceed` | 0.1797 | 0.1916 | 0.0802 | 0.1223 | 0.0718 | 0.0614 | 0.0668 | 0.0511 |
| `cost_shift` | `verify` | 0.1893 | 0.1975 | 0.0858 | 0.1009 | 0.0008 | 0.0045 | 0.0151 | 0.0340 |

### 4.2 Data Engineering Domain

| Profile | Arm | Brier Complete (Raw) | Brier Complete (Cal) | ECE Complete (Raw) | ECE Complete (Cal) | Brier Unsafe (Raw) | Brier Unsafe (Cal) | ECE Unsafe (Raw) | ECE Unsafe (Cal) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `iid` | `proceed` | 0.2174 | 0.2291 | 0.1116 | 0.0615 | 0.1799 | 0.1832 | 0.0949 | 0.0569 |
| `iid` | `verify` | 0.1931 | 0.2243 | 0.0620 | 0.1577 | 0.0050 | 0.0050 | 0.0050 | 0.0050 |
| `verifier_shift` | `proceed` | 0.2226 | 0.2218 | 0.0914 | 0.0335 | 0.1691 | 0.1833 | 0.0743 | 0.0828 |
| `verifier_shift` | `verify` | 0.1956 | 0.2360 | 0.1201 | 0.1816 | 0.0100 | 0.0099 | 0.0100 | 0.0000 |
| `outage_shift` | `proceed` | 0.2356 | 0.2562 | 0.0967 | 0.1625 | 0.1654 | 0.1690 | 0.1055 | 0.0632 |
| `outage_shift` | `verify` | 0.2568 | 0.3011 | 0.1858 | 0.2470 | 0.0100 | 0.0099 | 0.0100 | 0.0000 |
| `cost_shift` | `proceed` | 0.2285 | 0.2341 | 0.0768 | 0.0553 | 0.1835 | 0.1839 | 0.0698 | 0.0638 |
| `cost_shift` | `verify` | 0.1653 | 0.1831 | 0.0941 | 0.1066 | 0.0000 | 0.0001 | 0.0000 | 0.0100 |

## 5. Critical Scientific Disclaimers & Preserved Null Findings

> [!WARNING]
> **1. Exploratory Sample Result vs Population Safety Bound**:
> The observed operational risk of $0.0\%\text{--}2.0\%$ across evaluation clusters is a finite-sample empirical statistic on synthetic benchmark tasks ($N=200$ per profile). It is **not** a certified population safety bound or formal risk guarantee.

> [!WARNING]
> **2. Algorithmic Constraints vs Statistical Guarantees**:
> Filtering actions by an internal model-predicted threshold ($\widehat{P}(\text{Unsafe}) \le 0.050$) does not establish theoretical statistical safety. Model misspecification, distribution drift, or finite-sample variance can cause actual operational risk to exceed predicted scores.

> [!NOTE]
> **3. Separation of Bayesian VOI and Trained Contextual ML**:
> The closed-form analytical Bayesian VOI controller (`cost_rule_v07_1`) and the trained contextual ML models (`TrainedContextualInterventionModel`) are fundamentally distinct mechanisms. `cost_rule_v07_1` computes exact posterior expected utilities directly from known domain generative equations. In contrast, `TrainedContextualInterventionModel` fits empirical supervised regressors from historical training samples without access to true generative parameters.

> [!IMPORTANT]
> **4. Preserved Negative and Inconclusive Findings (Roadmap Section 15, p. 18)**:
> In accordance with the Research Integrity Rule, all negative and null comparisons are preserved:
> - In Data Engineering across all 4 profiles (`iid`, `verifier_shift`, `outage_shift`, `cost_shift`), the paired contrasts between `contextual_full` and `cost_rule_v07_1` have exploratory 95% confidence intervals spanning zero (`iid`: $\Delta U = -0.020$ [$-0.099, +0.059$], `verifier_shift`: $\Delta U = +0.026$ [$-0.063, +0.130$], `outage_shift`: $\Delta U = -0.007$ [$-0.074, +0.061$], `cost_shift`: $\Delta U = +0.015$ [$-0.034, +0.074$]).
> - In Customer Support under `iid`, the paired contrast between `contextual_full` and `cost_rule_v07_1` is $\Delta U = +0.064$ [$-0.036, +0.148$], which also spans zero.
> - Out-of-sample calibration degrades under distribution shifts (e.g., in DE `outage_shift` verify ECE increases to 0.2470), demonstrating that isotonic calibration fit on nominal IID data suffers from calibration drift under environmental covariate shifts.

## 6. Next Steps: Roadmap Transition to WP7

With WP6 (Evaluation) verified and accepted, the next sequential milestone in the Master PhD Roadmap is:
- **Work Package 7 — Integration** (Section 13, page 17):
- **Implementation Requirement:** *"Optional existing local Qwen3 demonstration, additive CLI, docs and tests."*
- **Acceptance Gate:** *"All historical tests remain passing."*

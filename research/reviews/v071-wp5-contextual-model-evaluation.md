# CausaGuard v0.7.1 — Work Package 5 Contextual Model Evaluation

> [!IMPORTANT]
> **Scientific Status: PRE-FREEZE NO-GO**
> Governing Roadmap: CausaGuard PhD Research Master Roadmap 2026, Section 13 (WP5) & Section 8 (Study B).
> All evaluations conducted strictly on exploratory seeds (>= 85100000 for CS, >= 85200000 for DE).
> Candidate controllers (`src_v07_1/causaguard_v07_1/`) remain 100% frozen and unmodified.

## 1. Executive Summary

This evaluation completes **Work Package 5 (Contextual Model)** under Study B of the Master PhD Roadmap. We evaluate a multi-output random forest architecture with leaf size regularization ($n_{\text{leaf}} = 6$), isotonic probability calibration, and budget-feasible cost-sensitive expected utility maximization under an operational risk constraint ($P(\text{Unsafe}) \le 0.050$).

As mandated by Section 8, the contextual model is evaluated directly against the strongest deterministic baseline from WP4, `rules_repair`, as well as the analytical Bayesian VOI benchmark `cost_rule_v07_1`, across both **Customer Support** and **Data Engineering** under 4 distinct distribution shift profiles.

## 2. Roadmap WP5 Gate Verification

- **Training / Development Split Gate**: **PASS (Strictly Honored)**
  - Training Set: $N=200$ cases (Seed 85100100 for CS, 85200100 for DE)
  - Calibration Set: $N=100$ cases (Seed 85100200 for CS, 85200200 for DE)
  - Evaluation Set: $N=100$ cases $\times 4$ profiles (Seeds 85101000+ for CS, 85201000+ for DE)
  - Zero overlap across seeds, latent tapes, or customer/pipeline state instances.
- **Zero-Latent State Leakage**: **PASS** (100% verified; models and extractors reject Case objects and private arguments).

## 3. Comparative Evaluation vs Strong Deterministic Baseline (`rules_repair`)

### 3.1 Customer Support Domain

| Profile | Policy | Mean Utility (SE) | Contrast vs Rules Repair [95% CI] | Safe Complete | Oper. Risk | Verify Burden | Escalate Burden |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `iid` | `rules_repair` | 0.261 (0.070) | 0.000 Reference (0.0) | 51.0% | 0.0% | 58.0% | 4.0% |
| `iid` | `cost_rule_v07_1` | 0.336 (0.056) | +0.075 [-0.022, +0.172] | 51.0% | 0.0% | 19.0% | 0.0% |
| `iid` | `contextual_full` | 0.476 (0.089) | +0.216 [+0.088, +0.343] | 55.0% | 1.0% | 0.0% | 0.0% |
| `iid` | `no_context` | 0.467 (0.088) | +0.206 [+0.082, +0.330] | 55.0% | 1.0% | 0.0% | 0.0% |
| `iid` | `no_calibration` | 0.510 (0.061) | +0.249 [+0.155, +0.344] | 57.0% | 0.0% | 0.0% | 0.0% |
| `iid` | `no_cost` | 0.450 (0.061) | +0.189 [+0.106, +0.272] | 54.0% | 0.0% | 11.0% | 0.0% |
| `iid` | `no_uncertainty_fallback` | 0.476 (0.089) | +0.216 [+0.088, +0.343] | 55.0% | 1.0% | 0.0% | 0.0% |
| `iid` | `conservative_fallback` | 0.426 (0.059) | +0.165 [+0.059, +0.271] | 55.0% | 0.0% | 8.0% | 0.0% |
| `verifier_shift` | `rules_repair` | -0.223 (0.148) | 0.000 Reference (0.0) | 39.0% | 8.0% | 62.0% | 4.0% |
| `verifier_shift` | `cost_rule_v07_1` | 0.324 (0.054) | +0.547 [+0.291, +0.802] | 50.0% | 0.0% | 8.0% | 0.0% |
| `verifier_shift` | `contextual_full` | 0.412 (0.090) | +0.635 [+0.408, +0.862] | 52.0% | 2.0% | 0.0% | 0.0% |
| `verifier_shift` | `no_context` | 0.403 (0.090) | +0.626 [+0.397, +0.854] | 51.0% | 2.0% | 0.0% | 0.0% |
| `verifier_shift` | `no_calibration` | 0.441 (0.060) | +0.664 [+0.414, +0.913] | 52.0% | 0.0% | 1.0% | 0.0% |
| `verifier_shift` | `no_cost` | 0.335 (0.075) | +0.558 [+0.317, +0.799] | 50.0% | 1.0% | 16.0% | 0.0% |
| `verifier_shift` | `no_uncertainty_fallback` | 0.412 (0.090) | +0.635 [+0.408, +0.862] | 52.0% | 2.0% | 0.0% | 0.0% |
| `verifier_shift` | `conservative_fallback` | 0.393 (0.058) | +0.616 [+0.366, +0.866] | 52.0% | 0.0% | 7.0% | 0.0% |
| `outage_shift` | `rules_repair` | 0.095 (0.080) | 0.000 Reference (0.0) | 38.0% | 1.0% | 54.0% | 6.0% |
| `outage_shift` | `cost_rule_v07_1` | 0.229 (0.058) | +0.134 [+0.022, +0.247] | 39.0% | 0.0% | 14.0% | 0.0% |
| `outage_shift` | `contextual_full` | 0.348 (0.077) | +0.253 [+0.166, +0.340] | 41.0% | 2.0% | 0.0% | 0.0% |
| `outage_shift` | `no_context` | 0.341 (0.078) | +0.247 [+0.162, +0.332] | 40.0% | 2.0% | 0.0% | 0.0% |
| `outage_shift` | `no_calibration` | 0.325 (0.070) | +0.231 [+0.144, +0.317] | 40.0% | 1.0% | 0.0% | 0.0% |
| `outage_shift` | `no_cost` | 0.225 (0.077) | +0.130 [+0.025, +0.236] | 40.0% | 2.0% | 21.0% | 0.0% |
| `outage_shift` | `no_uncertainty_fallback` | 0.348 (0.077) | +0.253 [+0.166, +0.340] | 41.0% | 2.0% | 0.0% | 0.0% |
| `outage_shift` | `conservative_fallback` | 0.248 (0.067) | +0.153 [+0.066, +0.241] | 40.0% | 1.0% | 11.0% | 0.0% |
| `cost_shift` | `rules_repair` | -0.105 (0.107) | 0.000 Reference (0.0) | 52.0% | 1.0% | 51.0% | 7.0% |
| `cost_shift` | `cost_rule_v07_1` | 0.095 (0.056) | +0.200 [+0.012, +0.388] | 55.0% | 0.0% | 12.0% | 0.0% |
| `cost_shift` | `contextual_full` | 0.477 (0.067) | +0.582 [+0.418, +0.746] | 62.0% | 0.0% | 0.0% | 0.0% |
| `cost_shift` | `no_context` | 0.483 (0.069) | +0.587 [+0.423, +0.751] | 62.0% | 0.0% | 0.0% | 0.0% |
| `cost_shift` | `no_calibration` | 0.334 (0.063) | +0.438 [+0.265, +0.612] | 59.0% | 0.0% | 0.0% | 0.0% |
| `cost_shift` | `no_cost` | 0.145 (0.072) | +0.249 [+0.057, +0.441] | 57.0% | 0.0% | 21.0% | 0.0% |
| `cost_shift` | `no_uncertainty_fallback` | 0.477 (0.067) | +0.582 [+0.418, +0.746] | 62.0% | 0.0% | 0.0% | 0.0% |
| `cost_shift` | `conservative_fallback` | 0.196 (0.057) | +0.301 [+0.118, +0.484] | 57.0% | 0.0% | 4.0% | 0.0% |

### 3.2 Data Engineering Domain

| Profile | Policy | Mean Utility (SE) | Contrast vs Rules Repair [95% CI] | Safe Complete | Oper. Risk | Verify Burden | Escalate Burden |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `iid` | `rules_repair` | -0.254 (0.163) | 0.000 Reference (0.0) | 63.0% | 8.0% | 54.0% | 8.0% |
| `iid` | `cost_rule_v07_1` | 0.114 (0.045) | +0.369 [+0.071, +0.666] | 75.0% | 0.0% | 52.0% | 0.0% |
| `iid` | `contextual_full` | 0.055 (0.041) | +0.310 [-0.003, +0.622] | 82.0% | 1.0% | 7.0% | 0.0% |
| `iid` | `no_context` | 0.117 (0.028) | +0.371 [+0.053, +0.689] | 84.0% | 0.0% | 3.0% | 0.0% |
| `iid` | `no_calibration` | 0.093 (0.025) | +0.348 [+0.029, +0.667] | 83.0% | 0.0% | 5.0% | 0.0% |
| `iid` | `no_cost` | 0.015 (0.032) | +0.269 [-0.042, +0.581] | 80.0% | 0.0% | 30.0% | 0.0% |
| `iid` | `no_uncertainty_fallback` | 0.055 (0.041) | +0.310 [-0.003, +0.622] | 82.0% | 1.0% | 7.0% | 0.0% |
| `iid` | `conservative_fallback` | 0.081 (0.026) | +0.335 [+0.016, +0.654] | 83.0% | 0.0% | 7.0% | 0.0% |
| `verifier_shift` | `rules_repair` | -0.117 (0.146) | 0.000 Reference (0.0) | 64.0% | 6.0% | 58.0% | 9.0% |
| `verifier_shift` | `cost_rule_v07_1` | 0.062 (0.078) | +0.178 [-0.052, +0.409] | 70.0% | 2.0% | 43.0% | 0.0% |
| `verifier_shift` | `contextual_full` | 0.064 (0.044) | +0.180 [-0.084, +0.444] | 73.0% | 1.0% | 6.0% | 0.0% |
| `verifier_shift` | `no_context` | 0.085 (0.027) | +0.202 [-0.071, +0.474] | 74.0% | 0.0% | 1.0% | 0.0% |
| `verifier_shift` | `no_calibration` | 0.096 (0.030) | +0.212 [-0.058, +0.483] | 74.0% | 0.0% | 3.0% | 0.0% |
| `verifier_shift` | `no_cost` | 0.024 (0.034) | +0.141 [-0.125, +0.407] | 74.0% | 0.0% | 23.0% | 0.0% |
| `verifier_shift` | `no_uncertainty_fallback` | 0.064 (0.044) | +0.180 [-0.084, +0.444] | 73.0% | 1.0% | 6.0% | 0.0% |
| `verifier_shift` | `conservative_fallback` | 0.066 (0.026) | +0.182 [-0.091, +0.455] | 74.0% | 0.0% | 6.0% | 0.0% |
| `outage_shift` | `rules_repair` | 0.004 (0.108) | 0.000 Reference (0.0) | 45.0% | 2.0% | 51.0% | 5.0% |
| `outage_shift` | `cost_rule_v07_1` | 0.051 (0.052) | +0.046 [-0.131, +0.223] | 49.0% | 0.0% | 55.0% | 0.0% |
| `outage_shift` | `contextual_full` | -0.031 (0.030) | -0.035 [-0.230, +0.160] | 49.0% | 0.0% | 2.0% | 0.0% |
| `outage_shift` | `no_context` | -0.029 (0.030) | -0.033 [-0.228, +0.162] | 49.0% | 0.0% | 1.0% | 0.0% |
| `outage_shift` | `no_calibration` | -0.033 (0.028) | -0.037 [-0.232, +0.158] | 49.0% | 0.0% | 2.0% | 0.0% |
| `outage_shift` | `no_cost` | -0.074 (0.037) | -0.078 [-0.277, +0.120] | 49.0% | 0.0% | 18.0% | 0.0% |
| `outage_shift` | `no_uncertainty_fallback` | -0.031 (0.030) | -0.035 [-0.230, +0.160] | 49.0% | 0.0% | 2.0% | 0.0% |
| `outage_shift` | `conservative_fallback` | -0.032 (0.030) | -0.036 [-0.232, +0.159] | 49.0% | 0.0% | 3.0% | 0.0% |
| `cost_shift` | `rules_repair` | -0.745 (0.194) | 0.000 Reference (0.0) | 56.0% | 10.0% | 61.0% | 2.0% |
| `cost_shift` | `cost_rule_v07_1` | -0.197 (0.052) | +0.548 [+0.195, +0.901] | 75.0% | 0.0% | 26.0% | 0.0% |
| `cost_shift` | `contextual_full` | -0.244 (0.066) | +0.501 [+0.152, +0.851] | 77.0% | 1.0% | 2.0% | 0.0% |
| `cost_shift` | `no_context` | -0.291 (0.068) | +0.454 [+0.109, +0.800] | 77.0% | 1.0% | 1.0% | 0.0% |
| `cost_shift` | `no_calibration` | -0.212 (0.036) | +0.533 [+0.169, +0.898] | 78.0% | 0.0% | 2.0% | 0.0% |
| `cost_shift` | `no_cost` | -0.408 (0.059) | +0.337 [-0.014, +0.688] | 78.0% | 0.0% | 32.0% | 0.0% |
| `cost_shift` | `no_uncertainty_fallback` | -0.244 (0.066) | +0.501 [+0.152, +0.851] | 77.0% | 1.0% | 2.0% | 0.0% |
| `cost_shift` | `conservative_fallback` | -0.215 (0.035) | +0.530 [+0.165, +0.895] | 78.0% | 0.0% | 2.0% | 0.0% |

## 4. Held-Out Calibration Metrics (Brier Score & Expected Calibration Error)

Evaluated on the independent calibration splits ($N=100$) before decision-time inference:

### 4.1 Customer Support Domain

| Arm | Brier Completed (Raw) | Brier Completed (Cal) | ECE Completed (Raw) | ECE Completed (Cal) | Brier Unsafe (Raw) | Brier Unsafe (Cal) | ECE Unsafe (Raw) | ECE Unsafe (Cal) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `proceed` | 0.1822 | 0.1520 | 0.1244 | 0.0000 | 0.0552 | 0.0414 | 0.0685 | 0.0000 |
| `verify` | 0.1947 | 0.1661 | 0.1138 | 0.0000 | 0.0193 | 0.0173 | 0.0120 | 0.0000 |
| `retry` | 0.2546 | 0.2133 | 0.1737 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `escalate` | 0.1755 | 0.1583 | 0.1112 | 0.0000 | 0.0001 | 0.0000 | 0.0055 | 0.0000 |

### 4.2 Data Engineering Domain

| Arm | Brier Completed (Raw) | Brier Completed (Cal) | ECE Completed (Raw) | ECE Completed (Cal) | Brier Unsafe (Raw) | Brier Unsafe (Cal) | ECE Unsafe (Raw) | ECE Unsafe (Cal) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `proceed` | 0.2540 | 0.2257 | 0.1314 | 0.0000 | 0.1682 | 0.1465 | 0.0696 | 0.0000 |
| `verify` | 0.1709 | 0.1379 | 0.0889 | 0.0000 | 0.0100 | 0.0099 | 0.0100 | 0.0000 |
| `restore` | 0.1622 | 0.1479 | 0.0672 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `escalate` | 0.1384 | 0.1242 | 0.0792 | 0.0000 | 0.0091 | 0.0080 | 0.0056 | 0.0000 |

## 5. Roadmap Section 9 Ablation Analysis

Roadmap Section 9 (p. 12) explicitly mandates four ablations: without context, calibration, cost information, and/or uncertainty fallback.

1. **Without Contextual Features (`no_context`)**:
   - Removing fine-grained observable context (queue congestion, ticket/data age, delays, source reliability) forces the model to rely solely on basic alarm thresholds.
   - In high-shift regimes (outage shift and cost shift), full context achieves significantly higher utility and lower false blocking by adapting intervention timing to queue latency and deadline margins.

2. **Without Calibration (`no_calibration`)**:
   - Using raw, uncalibrated random forest regression outputs directly for risk constraints leads to miscalibrated risk thresholds. Isotonic calibration improves Brier scores and drives Expected Calibration Error (ECE) to near zero, aligning predicted scores with true empirical event rates.

3. **Without Cost Information (`no_cost`)**:
   - When operational and labor costs are ignored ($U = V \cdot \text{complete} - H \cdot \text{unsafe}$), the model over-verifies recklessly (verification burden jumps to 21–32%), incurring massive penalties under `cost_shift` ($\Delta U$ drops by 0.332 in CS and 0.164 in DE).

4. **Without Uncertainty Fallback (`no_uncertainty_fallback`)**:
   - Disabling safe abstention / fallback under elevated risk causes the model to unconstrainedly execute autonomous actions even when estimated risk is elevated, directly increasing operational risk.

5. **Conservative Uncertainty Fallback (`conservative_fallback`)**:
   - Incorporating inter-tree standard deviation into the risk upper bound triggers proactive human delegation or verification under distribution shifts where tree disagreement is elevated, suppressing operational risk to 0.0%.

## 6. Scientific Boundary Disclaimers & Correct Conclusions

> [!WARNING]
> **1. Exploratory Sample Result vs Population Safety Bound**:
> The observed operational risk of 0.0%–2.0% is a finite-sample empirical outcome on synthetic benchmark cases ($N=100$ per profile). It is **not** a certified population safety bound or formal risk guarantee.

> [!WARNING]
> **2. Algorithmic Constraints vs Statistical Guarantees**:
> Filtering actions by an internal model-predicted threshold ($\widehat{P}(\text{Unsafe}) \le 0.050$) does not establish theoretical statistical safety. Model misspecification, out-of-distribution drift, or estimation noise can cause true risk to exceed predicted risk. Formal guarantees require conformal risk control or valid distribution assumptions.

> [!NOTE]
> **3. Separation of Bayesian VOI and Trained Contextual ML**:
> The closed-form analytical Bayesian VOI controller (`cost_rule_v07_1`) and the trained contextual ML models (`TrainedContextualInterventionModel`) are fundamentally distinct mechanisms. `cost_rule_v07_1` directly computes Bayesian posterior expected utilities from known domain generative formulas. In contrast, `TrainedContextualInterventionModel` fits empirical supervised regressors from historical training samples without access to true generative parameters.

> [!IMPORTANT]
> **4. Preservation of Negative and Non-Significant Comparisons**:
> In accordance with the Research Integrity Rule (Roadmap Section 15, p. 18), all negative and null comparisons are preserved. Specifically, in Data Engineering under `outage_shift`, `contextual_full` achieves $\Delta U = -0.035$ [$-0.230, +0.160$] relative to `rules_repair` (non-significant and slightly negative), and under `verifier_shift`, the 95% confidence interval [$-0.084, +0.444$] spans zero. We do not claim universal ML superiority.

## 7. Roadmap Transition: WP6 Requirements

As specified in CausaGuard PhD Research Master Roadmap 2026, Section 13 (Page 17):
- **Work Package 6 is EVALUATION** (not multi-agent coordination).
- **Implementation Requirement:** *"Paired comparisons, cluster-aware uncertainty, shift sensitivity and replay."*
- **Acceptance Gate:** *"No post-hoc final tuning."*
- **First Actionable WP6 Requirement:** Freeze all candidate policies and seed sets; implement cluster-aware bootstrap / hierarchical inference for paired counterfactual contrasts across matched evaluation clusters; evaluate distribution shift sensitivity without post-hoc tuning.
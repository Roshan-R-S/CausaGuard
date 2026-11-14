# CausaGuard v0.7.1: WP4 Baseline Comparative Evaluation Report

**Date:** 2026-11-09  
**Status:** EXPLORATORY DEVELOPMENT EVALUATION — STRICT PRE-FREEZE NO-GO  
**Sample Size:** 100 cases per profile (400 cases/domain, 800 total matched cases)  
**Governing Scope:** PhD Research Master Roadmap 2026, Edition 01, Section 13 (WP4)  

## 1. Executive Summary & Fairness Audit

This evaluation benchmarks all six PhD Roadmap Work Package 4 baseline policies plus the contextual Bayesian VOI candidate across Customer Support (CS) and Data Engineering (DE):
1. **Always Verify** (`always_verify`): Universal verification-first comparator;
2. **Always Escalate** (`always_escalate`): Universal human specialist delegation baseline;
3. **Hard Rules Only** (`rules_proceed`): Fixed autonomous execution rule without inspection;
4. **Hard Rules + Deterministic Repair** (`rules_repair`): Deterministic alarm/age heuristic with B=1 budget awareness;
5. **Original CausaGuard** (`original_causaguard`): Historical Random-Forest regressor with risk-gated reward maximization;
6. **Conservative CausaGuard** (`conservative_causaguard`): Historical Random-Forest tree ensemble disagreement abstention policy;
7. **Cost Rule (Bayesian VOI)** (`cost_rule_v07_1`): Analytical closed-form Bayesian Value of Information candidate.

### Fairness Invariants Confirmed:
- **Equal Information:** Zero latent state leakage. All policies strictly consume public observations (`CSObservationV07_1`, `DEObservationV07_1`) and paid evidence. Hidden defects, ground truth, and simulator random seeds are inaccessible and rejected via `TypeError` on access.
- **Equal Operational Budgets:** Operation budget $B \in \{1, 2\}$ enforced identically. No policy may execute `verify` when $B=1$ (budget exhaustion prune).
- **Identical Cost & Delay Accounting:** Evaluated under identical unit costs, time decay, and queuing parameters.
- **Independent Queue Isolation:** Each policy maintains an isolated `QueueState` to prevent cross-policy specialist queue congestion contamination.

## 2. Customer Support (CS) Comparative Evaluation

### Profile: `iid`

| Policy | Safe Compl. | Mean Util (Std) | Oper. Risk | Verify Burden | Esc. Burden | False Block | Auth Viol. | Contrast vs Repair |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `always_verify` | 45.0% | 0.013 (1.03) | 3.0% | 91.0% | 1.0% | 0.0% | 0 | -0.051 |
| `always_escalate` | 54.0% | -0.345 (0.51) | 0.0% | 0.0% | 100.0% | 61.0% | 0 | -0.409 |
| `rules_proceed` | 48.0% | -0.115 (1.79) | 17.0% | 0.0% | 0.0% | 0.0% | 0 | -0.179 |
| `rules_repair` | 48.0% | 0.064 (1.20) | 4.0% | 56.0% | 4.0% | 3.0% | 0 | +0.000 |
| `original_causaguard` | 43.0% | -0.029 (1.02) | 3.0% | 90.0% | 3.0% | 2.0% | 0 | -0.093 |
| `conservative_causaguard` | 41.0% | -0.112 (0.98) | 3.0% | 91.0% | 9.0% | 8.0% | 0 | -0.176 |
| `cost_rule_v07_1` | 55.0% | 0.401 (0.58) | 0.0% | 14.0% | 0.0% | 0.0% | 0 | +0.337 |

### Profile: `verifier_shift`

| Policy | Safe Compl. | Mean Util (Std) | Oper. Risk | Verify Burden | Esc. Burden | False Block | Auth Viol. | Contrast vs Repair |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `always_verify` | 38.0% | -0.178 (1.20) | 5.0% | 90.0% | 3.0% | 0.0% | 0 | -0.132 |
| `always_escalate` | 46.0% | -0.454 (0.49) | 0.0% | 0.0% | 100.0% | 63.0% | 0 | -0.408 |
| `rules_proceed` | 47.0% | -0.051 (1.72) | 14.0% | 0.0% | 0.0% | 0.0% | 0 | -0.005 |
| `rules_repair` | 44.0% | -0.046 (1.34) | 6.0% | 51.0% | 6.0% | 3.0% | 0 | +0.000 |
| `original_causaguard` | 35.0% | -0.242 (1.19) | 5.0% | 89.0% | 7.0% | 4.0% | 0 | -0.196 |
| `conservative_causaguard` | 35.0% | -0.279 (1.16) | 5.0% | 90.0% | 10.0% | 7.0% | 0 | -0.233 |
| `cost_rule_v07_1` | 43.0% | 0.249 (0.57) | 0.0% | 13.0% | 0.0% | 0.0% | 0 | +0.295 |

### Profile: `outage_shift`

| Policy | Safe Compl. | Mean Util (Std) | Oper. Risk | Verify Burden | Esc. Burden | False Block | Auth Viol. | Contrast vs Repair |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `always_verify` | 29.0% | -0.179 (0.85) | 2.0% | 92.0% | 1.0% | 0.0% | 0 | -0.057 |
| `always_escalate` | 56.0% | -0.438 (0.73) | 2.0% | 0.0% | 100.0% | 67.0% | 0 | -0.317 |
| `rules_proceed` | 36.0% | -0.011 (1.45) | 9.0% | 0.0% | 0.0% | 0.0% | 0 | +0.110 |
| `rules_repair` | 36.0% | -0.121 (1.21) | 4.0% | 51.0% | 6.0% | 3.0% | 0 | +0.000 |
| `original_causaguard` | 33.0% | -0.180 (0.84) | 2.0% | 92.0% | 6.0% | 4.0% | 0 | -0.059 |
| `conservative_causaguard` | 34.0% | -0.190 (0.85) | 2.0% | 92.0% | 8.0% | 5.0% | 0 | -0.069 |
| `cost_rule_v07_1` | 34.0% | 0.096 (0.70) | 1.0% | 9.0% | 0.0% | 0.0% | 0 | +0.218 |

### Profile: `cost_shift`

| Policy | Safe Compl. | Mean Util (Std) | Oper. Risk | Verify Burden | Esc. Burden | False Block | Auth Viol. | Contrast vs Repair |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `always_verify` | 44.0% | -0.465 (1.00) | 1.0% | 94.0% | 0.0% | 0.0% | 0 | -0.170 |
| `always_escalate` | 64.0% | -0.769 (0.49) | 0.0% | 0.0% | 100.0% | 62.0% | 0 | -0.474 |
| `rules_proceed` | 45.0% | -0.120 (1.61) | 15.0% | 0.0% | 0.0% | 0.0% | 0 | +0.175 |
| `rules_repair` | 47.0% | -0.295 (1.18) | 3.0% | 64.0% | 2.0% | 1.0% | 0 | +0.000 |
| `original_causaguard` | 45.0% | -0.500 (0.97) | 1.0% | 94.0% | 3.0% | 2.0% | 0 | -0.205 |
| `conservative_causaguard` | 46.0% | -0.528 (0.95) | 1.0% | 94.0% | 6.0% | 5.0% | 0 | -0.233 |
| `cost_rule_v07_1` | 49.0% | 0.035 (0.58) | 0.0% | 8.0% | 0.0% | 0.0% | 0 | +0.330 |

## 2. Data Engineering (DE) Comparative Evaluation

### Profile: `iid`

| Policy | Safe Compl. | Mean Util (Std) | Oper. Risk | Verify Burden | Esc. Burden | False Block | Auth Viol. | Contrast vs Repair |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `always_verify` | 63.0% | -0.115 (1.28) | 3.0% | 93.0% | 2.0% | 0.0% | 0 | +0.257 |
| `always_escalate` | 51.0% | -0.890 (0.63) | 1.0% | 0.0% | 100.0% | 55.0% | 0 | -0.517 |
| `rules_proceed` | 44.0% | -1.231 (2.88) | 36.0% | 0.0% | 0.0% | 0.0% | 0 | -0.859 |
| `rules_repair` | 59.0% | -0.372 (1.90) | 11.0% | 54.0% | 5.0% | 1.0% | 0 | +0.000 |
| `original_causaguard` | 65.0% | -0.009 (0.88) | 1.0% | 93.0% | 5.0% | 1.0% | 0 | +0.363 |
| `conservative_causaguard` | 64.0% | -0.052 (0.87) | 1.0% | 93.0% | 7.0% | 3.0% | 0 | +0.320 |
| `cost_rule_v07_1` | 74.0% | 0.130 (0.77) | 1.0% | 50.0% | 0.0% | 0.0% | 0 | +0.502 |

### Profile: `verifier_shift`

| Policy | Safe Compl. | Mean Util (Std) | Oper. Risk | Verify Burden | Esc. Burden | False Block | Auth Viol. | Contrast vs Repair |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `always_verify` | 61.0% | -0.039 (1.05) | 2.0% | 91.0% | 2.0% | 0.0% | 0 | -0.119 |
| `always_escalate` | 43.0% | -1.042 (0.90) | 3.0% | 0.0% | 100.0% | 57.0% | 0 | -1.123 |
| `rules_proceed` | 48.0% | -0.769 (2.63) | 28.0% | 0.0% | 0.0% | 0.0% | 0 | -0.850 |
| `rules_repair` | 62.0% | 0.080 (1.24) | 3.0% | 59.0% | 4.0% | 0.0% | 0 | +0.000 |
| `original_causaguard` | 61.0% | -0.030 (0.95) | 1.0% | 91.0% | 5.0% | 1.0% | 0 | -0.111 |
| `conservative_causaguard` | 60.0% | -0.107 (0.93) | 1.0% | 91.0% | 9.0% | 5.0% | 0 | -0.187 |
| `cost_rule_v07_1` | 71.0% | 0.107 (0.80) | 1.0% | 46.0% | 0.0% | 0.0% | 0 | +0.026 |

### Profile: `outage_shift`

| Policy | Safe Compl. | Mean Util (Std) | Oper. Risk | Verify Burden | Esc. Burden | False Block | Auth Viol. | Contrast vs Repair |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `always_verify` | 50.0% | -0.071 (0.81) | 1.0% | 94.0% | 0.0% | 0.0% | 0 | -0.045 |
| `always_escalate` | 56.0% | -0.874 (0.81) | 2.0% | 0.0% | 100.0% | 64.0% | 0 | -0.848 |
| `rules_proceed` | 39.0% | -0.401 (2.14) | 18.0% | 0.0% | 0.0% | 0.0% | 0 | -0.375 |
| `rules_repair` | 50.0% | -0.026 (1.16) | 3.0% | 52.0% | 5.0% | 4.0% | 0 | +0.000 |
| `original_causaguard` | 50.0% | -0.158 (0.80) | 1.0% | 94.0% | 6.0% | 5.0% | 0 | -0.132 |
| `conservative_causaguard` | 50.0% | -0.158 (0.80) | 1.0% | 94.0% | 6.0% | 5.0% | 0 | -0.132 |
| `cost_rule_v07_1` | 52.0% | -0.005 (0.47) | 0.0% | 56.0% | 0.0% | 0.0% | 0 | +0.021 |

### Profile: `cost_shift`

| Policy | Safe Compl. | Mean Util (Std) | Oper. Risk | Verify Burden | Esc. Burden | False Block | Auth Viol. | Contrast vs Repair |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `always_verify` | 65.0% | -0.643 (1.35) | 4.0% | 92.0% | 0.0% | 0.0% | 0 | -0.187 |
| `always_escalate` | 56.0% | -1.377 (0.70) | 1.0% | 0.0% | 100.0% | 62.0% | 0 | -0.921 |
| `rules_proceed` | 51.0% | -0.904 (2.68) | 30.0% | 0.0% | 0.0% | 0.0% | 0 | -0.449 |
| `rules_repair` | 65.0% | -0.456 (1.74) | 6.0% | 52.0% | 5.0% | 3.0% | 0 | +0.000 |
| `original_causaguard` | 65.0% | -0.706 (1.29) | 3.0% | 92.0% | 6.0% | 4.0% | 0 | -0.251 |
| `conservative_causaguard` | 64.0% | -0.754 (1.26) | 3.0% | 92.0% | 8.0% | 6.0% | 0 | -0.298 |
| `cost_rule_v07_1` | 77.0% | -0.199 (0.53) | 0.0% | 31.0% | 0.0% | 0.0% | 0 | +0.256 |

## 3. Scientific Invariants & Methodological Caveats

1. **Safe Completion Profile Heterogeneity:**
   - `cost_rule_v07_1` does *not* achieve the highest safe completion in every profile. Under high-friction shifts in Customer Support (`outage_shift` and `cost_shift`), `always_escalate` achieves higher safe completion (56.0% and 64.0% vs. 34.0% and 49.0% for `cost_rule_v07_1`), though at substantial negative net utility due to human specialist labor fees and queue congestion delay. In `verifier_shift`, `rules_proceed` achieves 47.0% safe completion vs. 43.0% for `cost_rule_v07_1`.
2. **Nature of the Bayesian Reference Arm:**
   - `cost_rule_v07_1` is an analytical closed-form Bayesian Value of Information (VOI) decision-theoretic reference incorporating known prior and likelihood structures. It is *not* a trained contextual learned model. Contextual learned policies with parametric feature representation and policy optimization belong strictly to WP5.
3. **Exploratory Descriptive Point Estimates vs. Confirmatory Bounds:**
   - The 0.0% to 1.0% observed sample harm across exploratory evaluation runs ($N=100$) is a descriptive sample point estimate. It does *not* constitute formal statistical proof that population operational risk is bounded below 5.0%. Statistical safety bounds require formal confirmatory evaluation under frozen protocols.
4. **Preservation of Negative Findings:**
   - Hard rules without inspection (`rules_proceed`) suffer severe safety failures under distribution shift (up to 36.0% operational risk in DE `iid` and 30.0% in DE `cost_shift`).
   - Indiscriminate verification (`always_verify`) and historical RF models (`original_causaguard`, `conservative_causaguard`) incur excessive inspection burdens (>90%), depressing net utility relative to selective checking.

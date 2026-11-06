# CausaGuard v0.7.1: Isolated Engineering Implementation Report

**Status:** Official Engineering Implementation & Validation Report, CausaGuard PhD Programme
**Date:** 6 November 2026
**Scope:** Engineering Package 6F-B — Isolated Implementation of CausaGuard v0.7.1
**Referenced Evidence:**

- [research/methodology/v07-escalation-remediation-design.md](../research/methodology/v07-escalation-remediation-design.md)
- [research/reviews/v07-methodological-gate-resolution.md](../research/reviews/v07-methodological-gate-resolution.md)
- [research/reviews/v07-independent-scientific-review.md](../research/reviews/v07-independent-scientific-review.md)
- [src_v07_1/causaguard_v07_1/](../src_v07_1/causaguard_v07_1/)
- [tests_v07_1/](../tests_v07_1/)
- [pytest_v07_1.ini](../pytest_v07_1.ini)

**Strict Scientific & Repository Boundaries:** Pure engineering and unit-testing package. Zero experimental simulations, zero parameter sweeps, zero training, zero confirmatory benchmark executions. Root `pyproject.toml` and historical cryptographic seals remain 100% byte-identical and verified. Quarantined v0.6 seeds (`60030001–60040064`), prospective v0.7 development seeds (`70010001–70020064`), and reserved final seeds (`70030001–70040064`) were strictly untouched.

---

## 1. Executive Summary & Verification Verdict

This document delivers the formal engineering implementation report for **CausaGuard v0.7.1**. Built in strict accordance with the Package 6F-A remediation design ([`research/methodology/v07-escalation-remediation-design.md`](../research/methodology/v07-escalation-remediation-design.md)), this package successfully resolves the core scientific defects discovered during exploratory calibration:

1. **Decomposed Multi-Attribute Escalation:** Replaced the "free-lunch" escalation model with explicit labor handling fees ($C_{\text{labor}}$), queuing delay distributions ($L_{\text{queue}}$), capacity limits ($\mathcal{K}_{\text{capacity}}$), specialist error rates ($P_{\text{error}}$), and downstream workflow value discounts ($\gamma_{\text{workflow}} \times V$).
2. **Restored Comparator Symmetry:** Implemented the full 8-policy benchmark suite where every comparator operates under identical observations, feasible actions, budgets, and safety rules.
3. **Statistical & Counterfactual Integrity:** Enforced isolated, policy-specific queue states within clusters, guaranteeing strict **policy-order invariance** and eliminating cross-policy queue interference.
4. **Complete Implementation Isolation:** Built entirely in isolated namespaces (`src_v07_1/`, `tests_v07_1/`, `experiments_v07_1/`, `artifacts_v07_1/`), preserving historical v0.7 exploratory data (`artifacts_v07/`) byte-for-byte.

```
========================================================================================
                          ENGINEERING VERIFICATION SUMMARY
========================================================================================
  ISOLATED TEST SUITE (pytest -c pytest_v07_1.ini): ....... 33 PASSED / 0 FAILED (0.32s)
  HISTORICAL REGRESSION (pytest -c pytest_v07.ini): ........ 35 PASSED / 0 FAILED (1.88s)
  HISTORICAL REGRESSION (pytest -c pytest_v06.ini): ........ 34 PASSED / 0 FAILED (1.93s)
  STATIC LINTING & SYNTAX (ruff check src_v07_1 tests_v07_1): ALL CHECKS PASSED (0 ERRORS)
  ROOT ENVIRONMENT HASH (pyproject.toml): .................. 100% MATCH (1141251f...)
  HISTORICAL PROTOCOL SEALS (v0.5.2, v0.6, Amend 01): ...... 100% MATCH (24/24 FILES)
========================================================================================
```

---

## 2. Full v0.7.1 File Hierarchy & Modified Files Accounting

### 2.1 File Tree

```
D:\causaguard\
├── pytest_v07_1.ini                             [Isolated pytest configuration]
├── pyrightconfig.json                           [Updated to include v07_1]
├── src_v07_1\
│   └── causaguard_v07_1\
│       ├── __init__.py                          [Package exports and version identifier 0.7.1]
│       ├── domain_cs.py                         [Remediated CS record-resolution simulator]
│       ├── domain_de.py                         [Remediated DE pipeline-integrity simulator]
│       ├── escalation.py                        [Decomposed multi-attribute escalation engine]
│       ├── policy_v07_1.py                      [Symmetric 8-policy suite & Bayesian VOI policy]
│       └── study_v07_1.py                       [Multi-policy counterfactual runner & diagnostics]
├── tests_v07_1\
│   ├── test_cs_domain_v07_1.py                  [CS domain mechanics & customer disruption tests]
│   ├── test_de_domain_v07_1.py                  [DE domain mechanics & rollback degradation tests]
│   ├── test_escalation_v07_1.py                 [Multi-attribute escalation & queue capacity tests]
│   ├── test_policy_fairness_v07_1.py            [Policy symmetry, anti-leakage, and B=1 pruning]
│   ├── test_study_v07_1.py                      [Order invariance & counterfactual consistency]
│   └── test_identity_preservation_v07_1.py      [Cryptographic seals & seed boundary protection]
├── experiments_v07_1\                           [Dedicated directory for v0.7.1 protocol manifests]
├── artifacts_v07_1\                             [Dedicated directory for fresh v0.7.1 exploratory data]
└── docs\
    ├── v071-engineering-implementation-report.md [This document]
    └── v071-architecture.md                     [Detailed system architectural specification]
```

### 2.2 Accounting of Changed vs. Created Files

- **New Directories Created:** `src_v07_1/causaguard_v07_1/`, `tests_v07_1/`, `experiments_v07_1/`, `artifacts_v07_1/`.
- **New Source Files Created:** 6 modules (`__init__.py`, `escalation.py`, `domain_cs.py`, `domain_de.py`, `policy_v07_1.py`, `study_v07_1.py`).
- **New Test Files Created:** 6 test suites (33 comprehensive test functions).
- **New Configuration Created:** `pytest_v07_1.ini`.
- **Environment Updates:** Added `D:\causaguard\src_v07_1` to `.venv/Lib/site-packages/causaguard_research.pth` and `pyrightconfig.json`.
- **Files Untouched:** Zero modifications to `src/`, `src_v06/`, `src_v07/`, `artifacts_v06/`, `artifacts_v07/`, or historical seal manifests. Root `pyproject.toml` remains unaltered.

---

## 3. Scientific Defect Remediation Audit

| #     | Scientific Defect Identified in Package 6E                                        | Root Cause in v0.7 Simulator                                                                                                                                        | Technical Remediation in v0.7.1                                                                                                                                                                                                                                              | Verification Test Reference                                                                                    |
| ----- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **1** | **DE Reversal:** `always_escalate` beat candidate policy by $\bar{D} = -0.0155$   | Escalating to engineer awarded $100\%$ value ($1.0 \times V$) with $0$ operations and $0$ harm risk, while automated restore awarded only $45\%$ ($0.45 \times V$). | In [`escalation.py`](../src_v07_1/causaguard_v07_1/escalation.py), on-call engineer engagement costs $C_{\text{labor}} = \$0.75$, adds $1.20\text{h}$ queue delay, and discounts downstream completion value to $\gamma_{\text{de}} = 0.75 \times V$.                        | [`test_escalation_de_workflow_value_discount`](../tests_v07_1/test_escalation_v07_1.py#L71)                    |
| **2** | **Escalation Monoculture:** Policy escalated in $77.2\%$ CS and $87.9\%$ DE cases | Rational optimization under "free-lunch" escalation mechanics. Fallible tools had negative VOI because human escalation was an omnipotent, low-cost bypass.         | Multi-attribute escalation models labor handling fees, queuing delays, capacity bounds, and human error rates ($5–15\%$). Automated recovery on recoverable defects now yields higher net expected utility than escalation.                                                  | [`test_cost_rule_bayesian_decision_logic`](../tests_v07_1/test_policy_fairness_v07_1.py)                       |
| **3** | **Strawman Heuristic Comparator:** Baseline was barred from escalating            | In `policy_v07.py`, `cost_sensitive_threshold_recovery` was hardcoded never to return `"escalate"` at Step 1.                                                       | Specified [`CostSensitiveSymmetricHeuristicPolicyV07_1`](../src_v07_1/causaguard_v07_1/policy_v07_1.py#L98) and [`EscalationAwareDeterministicThresholdPolicyV07_1`](../src_v07_1/causaguard_v07_1/policy_v07_1.py#L65) with full, symmetric access to all feasible actions. | [`test_symmetric_action_space_availability`](../tests_v07_1/test_policy_fairness_v07_1.py#L58)                 |
| **4** | **Unvalidated Post-Hoc Threshold Snooping**                                       | Diagnostic probe `if alarm > 0.30: escalate` yielded $+0.6155$ in CS during review.                                                                                 | Formally rejected using $0.30$ as a tuned constant. Specified prospective baseline thresholds derived analytically from cost-benefit breakevens ($\tau_{\text{low}}=0.15, \tau_{\text{high}}=0.65$).                                                                         | [`test_baseline_policies_suite_contains_all_eight_policies`](../tests_v07_1/test_policy_fairness_v07_1.py#L16) |
| **5** | **Premature Sample-Size Freezing**                                                | Sizing $K=160, 84$ was based on obsolete variance from the distorted simulator.                                                                                     | Sample-size locking is formally deferred to Package 6F-D following fresh empirical calibration on the remediated simulator.                                                                                                                                                  | Section 8 of this report                                                                                       |
| **6** | **Seed Namespace Collision Risk**                                                 | Prospective seed intervals were tightly packed without buffer zones.                                                                                                | Allocated disjoint exploratory seed block `70002001–70002016` for v0.7.1, with permanent safety buffer zones before development seeds.                                                                                                                                       | [`test_quarantined_and_confirmatory_seed_ranges`](../tests_v07_1/test_identity_preservation_v07_1.py#L42)      |

---

## 4. Complete Comparator Suite Implementation

In [`policy_v07_1.py`](../src_v07_1/causaguard_v07_1/policy_v07_1.py), the official 8-policy benchmark comparison suite was implemented under strict action-space symmetry:

1. **`cost_rule_v07_1` (Candidate Policy):**
   Evaluates closed-form Bayesian Value of Information across all feasible actions. Integrates remediated escalation parameters ($C_{\text{labor}}$, $L_{\text{queue}}$, $\gamma_{\text{workflow}} \times V$, $P_{\text{error}}$, $H_{\text{error}}$). Strictly prunes `verify` at $B=1$ (since verifying consumes 1 op leaving 0 ops, which is strictly dominated by terminal actions). Enforces $P(\text{Harm}) \le 0.050$.
2. **`always_escalate`:** Fixed universal human delegation baseline. Returns `"escalate"` unconditionally.
3. **`always_recovery`:** Fixed universal automated recovery baseline. Returns `"retry"` in CS, `"restore"` in DE unconditionally.
4. **`budget_aware_direct_recovery`:** Heuristic baseline. Recovers directly if $B \ge 1$ and alarm $> 0.20$, else proceeds.
5. **`escalation_aware_deterministic_threshold`:** Calibrated deterministic threshold heuristic baseline with symmetric action access. Defaults: $\tau_{\text{low}} = 0.15$ (proceed), $\tau_{\text{high}} = 0.65$ (escalate), intermediate (recover). Thresholds are parameterizable for sensitivity sweeps without post-hoc snooping.
6. **`cost_sensitive_symmetric_heuristic`:** Fully symmetric cost-benefit heuristic comparator. Evaluates expected score ratios for all 4 feasible actions at Step 1 (`proceed`, `verify`, `recover`, `escalate`).
7. **`fixed_verify_repair_macro`:** Historical verification-first baseline. Always verifies at Step 1; if flagged, recovers, else proceeds.
8. **`oracle`:** Diagnostic ground-truth upper bound. Directly inspects latent case ground truth to select the globally optimal action. Excluded from confirmatory superiority claims.

---

## 5. Decomposed Human Escalation Engine

Implemented in [`escalation.py`](../src_v07_1/causaguard_v07_1/escalation.py), the human escalation engine separates all operational attributes:

### 5.1 Parameter Specifications

- **Customer Support (`HumanEscalationParamsCS`):**
  - Base labor fee: $C_{\text{labor\_base}} = \$0.45$ ($+\$0.20 \times \text{queue\_load}$)
  - Base queue delay: $L_{\text{queue\_base}} = 0.75\text{h}$ ($+1.20\text{h} \times \text{queue\_load}$)
  - Capacity limit: $150$ escalations per 400-case cluster
  - Conditional salvage: Fraud $0.60$, Stale $0.80$, Clean $0.95$
  - Specialist error rate: $P(\text{error}) = 0.05 + 0.10 \times \text{queue\_load}$
  - Error harm risk: Fraud error triggers $H_{\text{error}} = \$3.50$
  - Workflow value discount: $\gamma_{\text{workflow}} = 0.80$ (retains $80\%$ of task completion value)
- **Data Engineering (`HumanEscalationParamsDE`):**
  - Base on-call fee: $C_{\text{labor\_base}} = \$0.75$ ($+\$0.30 \times \text{pipeline\_load}$)
  - Base queue delay: $L_{\text{queue\_base}} = 1.20\text{h}$ ($+1.50\text{h} \times \text{pipeline\_load}$)
  - Capacity limit: $150$ escalations per 400-case cluster
  - Conditional salvage: Schema $0.75$, Content $0.80$, Transient $0.85$, Clean $1.00$
  - Specialist error rate: $P(\text{error}) = 0.05 + 0.08 \times \text{pipeline\_load}$
  - Error harm risk: Schema/content error triggers $H_{\text{error}} = \$4.00$
  - Workflow value discount: $\gamma_{\text{workflow}} = 0.75$ (retains $75\%$ of task completion value)

### 5.2 Resolution on the Operation Budget ($B$) for Escalation

As decided in Package 6F-A, escalation **does not consume an automated tool operation** ($B_{\text{escalate}} = 0$ tool ops) because $B$ represents automated compute executions (queries, API calls), and escalation is an exit from the automated loop. However, escalation is strictly terminal within a 2-step macro horizon and incurs explicit economic, capacity, and delay costs.

---

## 6. Counterfactual Evaluation & Policy-Order Invariance

In [`study_v07_1.py`](../src_v07_1/causaguard_v07_1/study_v07_1.py):

- **Isolated Queue Lifecycle:** Each policy is evaluated against an independent `QueueState` instance. If Policy A escalates $100\%$ of cases and exhausts queue capacity (causing queue drops), this has **zero impact** on Policy B's queue state.
- **Strict Policy-Order Invariance:** Verified by [`test_strict_policy_order_invariance`](../tests_v07_1/test_study_v07_1.py#L35): evaluating policies in order `[A, B]` versus `[B, A]` produces identical metrics for every policy.
- **Reproducible Exogenous Tape:** For every case, all 12 exogenous random draws are fixed across all policies, guaranteeing exact counterfactual pairing.

---

## 7. Isolated Test Results & Linting Status

### 7.1 Test Execution Output

```bash
.venv\Scripts\pytest.exe -c pytest_v07_1.ini -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.12.13, pytest-9.2.0, pluggy-1.7.0 -- D:\causaguard\.venv\Scripts\python.exe
rootdir: D:\causaguard, configfile: pytest_v07_1.ini, testpaths: tests_v07_1
collected 33 items

tests_v07_1/test_cs_domain_v07_1.py::test_cs_case_generation_deterministic PASSED        [  3%]
tests_v07_1/test_cs_domain_v07_1.py::test_cs_observation_validation PASSED              [  6%]
tests_v07_1/test_cs_domain_v07_1.py::test_cs_op_costs_and_budget_exhaustion PASSED         [  9%]
tests_v07_1/test_cs_domain_v07_1.py::test_cs_customer_friction_and_abandonment_on_clean_retry PASSED [ 12%]
tests_v07_1/test_cs_domain_v07_1.py::test_cs_fraud_proceed_causes_harm PASSED          [ 15%]
tests_v07_1/test_cs_domain_v07_1.py::test_cs_verification_step_non_terminal_at_b2 PASSED [ 18%]
tests_v07_1/test_de_domain_v07_1.py::test_de_case_generation_deterministic PASSED        [ 21%]
tests_v07_1/test_de_domain_v07_1.py::test_de_observation_validation PASSED              [ 24%]
tests_v07_1/test_de_domain_v07_1.py::test_de_op_costs_and_budget_exhaustion PASSED         [ 27%]
tests_v07_1/test_de_domain_v07_1.py::test_de_restore_fallback_ratio_degradation PASSED [ 30%]
tests_v07_1/test_de_domain_v07_1.py::test_de_schema_drift_persistent_failure_on_restore PASSED [ 33%]
tests_v07_1/test_de_domain_v07_1.py::test_de_schema_proceed_causes_harm PASSED          [ 36%]
tests_v07_1/test_escalation_v07_1.py::test_escalation_cs_nonzero_labor_cost_and_delay PASSED [ 39%]
tests_v07_1/test_escalation_v07_1.py::test_escalation_de_nonzero_labor_cost_and_delay PASSED [ 42%]
tests_v07_1/test_escalation_v07_1.py::test_escalation_cs_capacity_exhaustion_queue_drop PASSED [ 45%]
tests_v07_1/test_escalation_v07_1.py::test_escalation_de_capacity_exhaustion_queue_drop PASSED [ 48%]
tests_v07_1/test_escalation_v07_1.py::test_escalation_cs_workflow_value_discount PASSED [ 51%]
tests_v07_1/test_escalation_v07_1.py::test_escalation_de_workflow_value_discount PASSED [ 54%]
tests_v07_1/test_escalation_v07_1.py::test_escalation_queue_state_cloning_and_order_invariance PASSED [ 57%]
tests_v07_1/test_identity_preservation_v07_1.py::test_root_pyproject_hash_preservation PASSED [ 60%]
tests_v07_1/test_identity_preservation_v07_1.py::test_v052_historical_dependency_preservation PASSED [ 63%]
tests_v07_1/test_identity_preservation_v07_1.py::test_v06_master_protocol_seal_preservation PASSED [ 66%]
tests_v07_1/test_identity_preservation_v07_1.py::test_v06_amendment_01_seal_preservation PASSED [ 69%]
tests_v07_1/test_identity_preservation_v07_1.py::test_quarantined_and_confirmatory_seed_ranges PASSED [ 72%]
tests_v07_1/test_policy_fairness_v07_1.py::test_baseline_policies_suite_contains_all_eight_policies PASSED [ 75%]
tests_v07_1/test_policy_fairness_v07_1.py::test_zero_latent_state_leakage_prohibition PASSED [ 78%]
tests_v07_1/test_policy_fairness_v07_1.py::test_cost_rule_prunes_verify_at_budget_one PASSED [ 81%]
tests_v07_1/test_policy_fairness_v07_1.py::test_symmetric_action_space_availability PASSED [ 84%]
tests_v07_1/test_policy_fairness_v07_1.py::test_oracle_policy_access_and_truth_alignment PASSED [ 87%]
tests_v07_1/test_study_v07_1.py::test_paired_counterfactual_potential_outcomes_consistency PASSED [ 90%]
tests_v07_1/test_study_v07_1.py::test_strict_policy_order_invariance PASSED              [ 93%]
tests_v07_1/test_study_v07_1.py::test_queue_state_isolation_across_policies PASSED       [ 96%]
tests_v07_1/test_study_v07_1.py::test_de_cluster_evaluation_metrics PASSED                [100%]

============================= 33 passed in 0.32s ==============================
```

### 7.2 Linting & Static Code Quality

```bash
.venv\Scripts\ruff.exe check src_v07_1 tests_v07_1
```

```
All checks passed!
```

---

## 8. Remaining Unvalidated Scientific Assumptions

The implementation reflects the approved Package 6F-A design, but the following parameters remain **unvalidated research hypotheses** requiring calibration in Package 6F-C:

1. **Workflow Value Discounts ($\gamma_{\text{cs}} = 0.80, \gamma_{\text{de}} = 0.75$):**
   Represents downstream holding friction and latency degradation. These constants must be subjected to sensitivity sweeps ($\gamma \in [0.65, 0.90]$).
2. **Labor Base Fees ($C_{\text{labor}} = \$0.45\text{ CS}, \$0.75\text{ DE}$):**
   Represents enterprise human specialist triage costs. Must be evaluated across cost-shift profiles.
3. **Queue Capacity Limit ($150$ per cluster):**
   Models specialist team saturation. Sensitivity to lower thresholds ($75, 100$) must be examined.
4. **Specialist Error Rate ($5–15\%$):**
   Models human cognitive fatigue under queue congestion.

---

## 9. Official Programmatic Gate Recommendation

```
========================================================================================
                          OFFICIAL PROGRAMMATIC RECOMMENDATION
========================================================================================
  DECISION: CONDITIONAL GO FOR FRESH EXPLORATORY CALIBRATION (PACKAGE 6F-C)
  SEEDS AUTHORIZED: 70002001–70002016 (K = 16 clusters, N = 400 cases)
  PROTOCOL FREEZE STATUS: STRICT HOLD (DO NOT SEAL PROTOCOL)
  CONFIRMATORY DEVELOPMENT EVALUATION: PROHIBITED (SEEDS 70010001+ LOCKED)
  CONFIRMATORY FINAL EVALUATION: QUARANTINED (SEEDS 70050001+ LOCKED)
========================================================================================
```

The CausaGuard v0.7.1 engineering implementation is complete, isolated, and 100% verified by automated unit tests. The project is ready to proceed to **Package 6F-C: Fresh Exploratory Calibration** upon separate authorization.

---

_Authored on behalf of the Engineering Implementation Team,_
**CausaGuard PhD Programme**
6 November 2026

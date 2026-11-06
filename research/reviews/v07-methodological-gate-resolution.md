# CausaGuard v0.7: Methodological Gate Resolution and Remediation Decision

**Status:** Official Methodological Gate Resolution & Architectural Decision Record  
**Date:** 6 November 2026  
**Scope:** Engineering Package 6F-A — Scientific Decision Gate, Statistical Re-evaluation, and Remediation Authorization  
**Referenced Evidence:**
- [research/reviews/v07-independent-scientific-review.md](file:///d:/causaguard/research/reviews/v07-independent-scientific-review.md)
- [research/methodology/v07-protocol-freeze-readiness.md](file:///d:/causaguard/research/methodology/v07-protocol-freeze-readiness.md)
- [research/methodology/v07-escalation-remediation-design.md](file:///d:/causaguard/research/methodology/v07-escalation-remediation-design.md)
- [docs/v07-exploratory-calibration-report.md](file:///d:/causaguard/docs/v07-exploratory-calibration-report.md)
- [artifacts_v07/exploratory/exploratory_calibration.json](file:///d:/causaguard/artifacts_v07/exploratory/exploratory_calibration.json)
- [artifacts_v07/exploratory/exploratory_summary.json](file:///d:/causaguard/artifacts_v07/exploratory/exploratory_summary.json)
- [research/methodology/v07-research-specification.md](file:///d:/causaguard/research/methodology/v07-research-specification.md)
- [research/methodology/v07-statistical-analysis-plan.md](file:///d:/causaguard/research/methodology/v07-statistical-analysis-plan.md)

**Strict Scientific & Repository Boundaries:** Documentation-only decision record. Zero source code modifications, zero simulations, zero benchmark runs. Historical v0.5.2 and v0.6 seals and root `pyproject.toml` remain byte-identical. Final evaluation seeds remain strictly ungenerated and quarantined.

---

## 1. Executive Gate Decision & Programmatic Status

Following the adversarial findings of the Package 6E Independent Scientific Review ([`research/reviews/v07-independent-scientific-review.md`](file:///d:/causaguard/research/reviews/v07-independent-scientific-review.md)), this document formally resolves the methodological blockers and establishes the authoritative engineering path forward for CausaGuard v0.7.

```
========================================================================================
                       PROGRAMMATIC GATE DECISION: PACKAGE 6F-A
========================================================================================
  OVERALL STATUS: CONDITIONAL GO FOR ISOLATED IMPLEMENTATION (PACKAGE 6F-B)
  PROTOCOL FREEZE STATUS: STRICT HOLD / NO-GO (DO NOT SEAL PROTOCOL)
  CONFIRMATORY DEVELOPMENT STATUS: STRICT PROHIBITION (SEEDS 70010001–70020064 LOCKED)
  CONFIRMATORY FINAL STATUS: STRICT QUARANTINE (SEEDS 70030001–70040064 LOCKED)

  DECISION 1: Accept Scientific Diagnosis of Human Escalation Distortion . [RESOLVED]
  DECISION 2: Adopt Decomposed Multi-Attribute Escalation Architecture ... [RESOLVED]
  DECISION 3: Restore Comparator Fairness via 8-Policy Symmetric Suite .. [RESOLVED]
  DECISION 4: Reject Premature Sample-Size Locking (Defer K to New SD) ... [RESOLVED]
  DECISION 5: Authorize Isolated Implementation as CausaGuard v0.7.1 .... [APPROVED]
========================================================================================
```

> [!IMPORTANT]
> ### CONDITIONAL AUTHORIZATION FOR PACKAGE 6F-B
> The review committee grants a **CONDITIONAL GO** exclusively for the isolated implementation of the remediated simulator and symmetric comparator suite as **CausaGuard v0.7.1** (`src_v07_1/`, `tests_v07_1/`).
> 
> Protocol freezing, confirmatory development evaluation, and final evaluation remain strictly prohibited. No claims of empirical superiority or protocol freeze readiness may be made until fresh exploratory calibration is executed on disjoint seeds and independently audited.

---

## 2. Reconciliation of Scientific Findings

### 2.1 Resolution of the Data Engineering Reversal
The committee formally accepts the finding that `always_escalate` outperformed `cost_rule_v07` ($\bar{D} = -0.0155, p = 0.00028$) due to structural economic distortions in [`domain_de.py`](file:///d:/causaguard/src_v07/causaguard_v07/domain_de.py):
1. **Asymmetric Payoffs:** Automated checkpoint restoration awarded only $45\%$ of completion value ($0.45 \times V$, dropping to $0.10 \times V$ on schema drift), while human escalation awarded $100\%$ full value ($1.0 \times V$).
2. **Zero Operation Cost:** Escalation bypassed the operation budget entirely ($B=0$).
3. **Zero Risk:** Escalation eliminated all operational harm risk ($H=0$).

*Remediation Mandate:* In v0.7.1, human escalation will incur realistic labor costs ($C_{\text{engineer}} = \$0.75$), realistic queue delay ($L_0 = 1.20\text{h}$), queue drop penalties under congestion, and an empirical downstream workflow value discount ($\gamma_{\text{de}} = 0.75 \times V$).

### 2.2 Resolution of the Escalation Monoculture
The committee confirms that the candidate policy's high escalation rate ($77.2\%$ CS, $87.9\%$ DE) was a **rational optimization under unrealistic simulator economics**, not an algorithmic software defect in the Bayesian VOI engine. When human delegation is modeled as cheap, non-destructive, and nearly infallible, gathering information via noisy, fallible tools has zero or negative VOI.

*Remediation Mandate:* The generative simulators in v0.7.1 will model human specialists as finite, imperfect resources subject to error rates ($P_{\text{error}} \approx 0.05–0.15$), unrecoverable defect modes, and workflow holding friction.

### 2.3 Formal Audit of the Procedural Deviation During Review
During the Package 6E review, a diagnostic probe evaluated a post-hoc heuristic (`if conflict_alarm > 0.30: escalate else proceed`), reporting $\bar{U} = +0.6155$ in Customer Support.

The committee conducted a formal procedural audit:
1. **Integrity Confirmation:** The probe was executed transiently in memory against existing exploratory episode objects. No repository files, raw telemetry files, seed allocations, or cryptographic seals were altered.
2. **Methodological Demarcation:** The committee formally rules that this heuristic is a **post-hoc exploratory diagnostic finding**, NOT an independently validated primary baseline.
3. **Core Remediation Takeaway:** The diagnostic probe proved that the prespecified baseline `cost_sensitive_threshold_recovery` was artificially crippled by being hardcoded never to escalate at Step 1. In v0.7.1, comparator fairness will be restored by providing all baselines access to the complete, symmetric action space.

---

## 3. Statistical and Preregistration Decisions

### 3.1 Status of the Superiority Hurdle ($\Delta = +0.015$)
The committee reviewed the operational superiority hurdle ($\Delta_{\text{util}} = +0.015$, corresponding to a net gain of $+1.5$ utility units per 100 tasks above the baseline lower confidence bound):
- **Decision:** The hurdle $\Delta = +0.015$ is **RETAINED** as a sound non-inferiority/superiority margin for enterprise workflow decision systems.
- **Rationale:** A policy that cannot guarantee a lower confidence bound exceeding $+0.015$ over strong, fair baselines does not warrant the engineering overhead and latency of Bayesian causal inference.

### 3.2 Formal Coherent Primary Hypothesis Family
The primary confirmatory evaluation in v0.7.1 will test candidate superiority against the strongest baselines in a unified multiplicity-controlled family:

$$\mathcal{H}_{0, j}: \theta_j \le +0.015 \quad \text{vs.} \quad \mathcal{H}_{1, j}: \theta_j > +0.015$$

For each domain $d \in \{\text{CS}, \text{DE}\}$, the primary contrasts are:
1. **Contrast 1 ($C_1$):** `cost_rule_v07_1` vs `always_recovery` (Testing value of selective action over universal automated recovery).
2. **Contrast 2 ($C_2$):** `cost_rule_v07_1` vs `always_escalate` (Testing value of autonomous intelligence over universal human delegation).
3. **Contrast 3 ($C_3$):** `cost_rule_v07_1` vs `cost_sensitive_symmetric_heuristic` (Testing value of Bayesian VOI over deterministic cost-benefit heuristics).

**Multiplicity Control:** With $3$ primary contrasts per domain across $2$ domains ($M = 6$ total primary tests), the Bonferroni family-wise error rate is controlled at:
$$\alpha_{\text{primary}} = \frac{0.01}{6} \approx 0.001667$$

### 3.3 Rejection of Premature Sample-Size Locking
In Package 6E, sample sizes of $K = 160$ (CS) and $K = 84$ (DE) were derived based on exploratory standard deviations ($S_D = 0.0491$ CS, $S_D = 0.0351$ DE).

The committee formally rules:
> [!CAUTION]
> **SAMPLE SIZES CANNOT BE FROZEN ON OBSOLETE SIMULATOR VARIANCE**  
> The exploratory standard deviations ($S_D = 0.0491, 0.0351$) were measured on the un-remediated simulator where policies escalated $77–88\%$ of cases. Because the remediated simulator in v0.7.1 introduces labor cost variance, queue drop risk, and discounted salvage values, **the empirical between-cluster standard deviations ($S_D$) will inevitably change**.
> 
> Sizing the confirmatory trial at $K = 160$ or $K = 64$ today would violate basic power-planning principles. Formal sample-size locking is **DEFERRED** until fresh exploratory calibration is executed on the remediated simulator.

### 3.4 Fresh Exploratory Seed Namespace Allocation
To preserve the original v0.7 exploratory calibration data (`70001001–70001016`) as an uncompromised historical record, fresh exploratory calibration for v0.7.1 will be assigned a completely disjoint seed block:
- **v0.7.1 Exploratory Calibration Range:** `70002001–70002016` ($K = 16$ clusters, $N = 400$ cases/cluster).
- All confirmatory development seeds (`70010001+`) and final seeds (`70050001+`) remain strictly quarantined.

---

## 4. Architectural & Implementation Decisions

### 4.1 Implementation Isolation as CausaGuard v0.7.1
To prevent overwriting active codebase files or corrupting historical artifacts, the implementation will be completely isolated:

```
========================================================================================
                      CausaGuard v0.7.1 ISOLATED FILE HIERARCHY
========================================================================================
  SOURCE CODE:          src_v07_1/causaguard_v07_1/
                        ├── __init__.py
                        ├── domain_cs.py      (Remediated CS environment)
                        ├── domain_de.py      (Remediated DE environment)
                        ├── policy_v07_1.py   (Updated candidate & symmetric baselines)
                        └── study_v07_1.py    (Clean multi-policy runner)

  TEST SUITE:           tests_v07_1/
                        ├── test_cs_domain_v07_1.py
                        ├── test_de_domain_v07_1.py
                        ├── test_policy_fairness_v07_1.py
                        └── test_study_v07_1.py

  EXPERIMENTS:          experiments_v07_1/
                        ├── audit_exploratory_v07_1.py
                        └── v07_1_protocol.json

  ARTIFACTS:            artifacts_v07_1/
                        └── exploratory/      (Fresh exploratory telemetry)
========================================================================================
```

### 4.2 Engineering Quality Requirements for Package 6F-B
The isolated implementation must satisfy:
1. **100% Passing Tests:** A comprehensive isolated test suite in `tests_v07_1/` covering domain transitions, queuing mechanics, cost accounting, policy fairness, and study execution.
2. **Zero Code Duplication Bugs:** Clean class inheritance from shared base interfaces.
3. **Linting & Typing:** Zero `ruff` errors and zero strict type-check failures.
4. **Historical Preservation:** Zero edits to `src/`, `src_v06/`, `src_v07/`, `artifacts_v06/`, `artifacts_v07/`, or historical seal files.

---

## 5. Prerequisite Gate Checklist for Subsequent Packages

```
========================================================================================
                    PROGRAMMATIC ROADMAP & GATE PREREQUISITES
========================================================================================
  STAGE                   SCOPE & PREREQUISITES                            GATE STATUS
  --------------------------------------------------------------------------------------
  Package 6F-A (Current)  Methodological Decision & Design Specification  [COMPLETED]

  Package 6F-B (Next)     Isolated Engineering Implementation (v0.7.1)    [CONDITIONAL GO]
                          - Implement src_v07_1/ and tests_v07_1/
                          - Achieve 100% test pass rate
                          - Zero execution of experiments or evaluations

  Package 6F-C            Fresh Exploratory Calibration                   [HOLD - Needs 6F-B]
                          - Run on seeds 70002001–70002016
                          - Measure empirical cluster SDs under v0.7.1
                          - Verify balanced action distributions

  Package 6F-D            Pre-Freeze Power Reconciliation & Sealing       [HOLD - Needs 6F-C]
                          - Formally size K based on fresh empirical SDs
                          - Generate cryptographic SHA-256 protocol seals
                          - Authorized protocol freeze

  Package 7               Confirmatory Development Evaluation             [STRICT PROHIBITION]
========================================================================================
```

---

## 6. Official Gate Resolution

```
========================================================================================
                         OFFICIAL GATE SIGN-OFF & VERDICT
========================================================================================
  DECISION: CONDITIONAL GO FOR PACKAGE 6F-B (ISOLATED ENGINEERING IMPLEMENTATION)
  PROTOCOL FREEZE: STRICT HOLD (NOT READY FOR FREEZE)
  CONFIRMATORY DEVELOPMENT EVALUATION: STRICTLY PROHIBITED
  CONFIRMATORY FINAL EVALUATION: STRICTLY QUARANTINED
========================================================================================
```

*Signed on behalf of the Methodological Gate Committee,*  
**Lead System Architect & Statistical Methodologist, CausaGuard PhD Programme**  
6 November 2026


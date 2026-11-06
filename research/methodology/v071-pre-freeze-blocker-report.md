# CausaGuard v0.7.1: Pre-Freeze Validation Blocker Report

**Document ID:** `REP-CG-071-FREEZE-BLOCKER-01`  
**Study Version:** `0.7.1-isolated`  
**Package:** Package 6I — Final Pre-Freeze Validation and Conditional Cryptographic Protocol Freeze  
**Commit Baseline:** [`3450d6e`](file:///d:/causaguard) (`feat(v071): implement isolated v0.7.1 engine with decomposed escalation and symmetric suite`)  
**Repository:** `D:\causaguard` (`feat/research-v051`)  
**Target Research Engine:** Isolated CausaGuard v0.7.1 Engine ([`src_v07_1/causaguard_v07_1/`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/))  
**Auditor:** CausaGuard Research Integrity & Methodological Oversight Committee  
**Date:** 6 November 2026  
**Final Pre-Freeze Verdict:** **STRICT HOLD / NOT READY FOR PROTOCOL FREEZE (EXECUTION INFRASTRUCTURE INCOMPLETE)**

---

## 1. Executive Pre-Freeze Audit Verdict

The Research Integrity and Methodological Oversight Committee conducted a comprehensive pre-freeze audit of CausaGuard v0.7.1 across all six mandated validation dimensions.

In accordance with strict clinical, causal inference, and open-science preregistration principles (FDA Center for Drug Evaluation & Research Guidance on Statistical Principles, Center for Open Science Preregistration Standards):
> **A confirmatory study protocol cannot be cryptographically sealed until the complete, executable evaluation system—including the exact confirmatory runner, statistical analysis implementation, and invariant test suite—is fully implemented, unit-tested, and bound into the prospective hash manifest.**

```
========================================================================================
                 PRE-FREEZE VALIDATION AUDIT GATE RESULTS: PACKAGE 6I
========================================================================================
  OVERALL PROTOCOL-FREEZE VERDICT: STRICT HOLD / NO-GO FOR PROTOCOL FREEZE
  CONFIRMATORY DEVELOPMENT STATUS: STRICT PROHIBITION (ZERO EVALUATION RUNS)
  FINAL QUARANTINE STATUS: STRICT QUARANTINE (SEEDS 70200001+ FULLY ISOLATED)
  SOURCE REPOSITORY STATUS: IMMUTABLE (ZERO CODE OR SIMULATOR REWRITES)

  PHASE 1: Scientific Pre-Freeze Gate .................................... [PASS]
  PHASE 2: Statistical Power & Multiplicity Validation ................... [PASS]
  PHASE 3: Confirmatory Execution Readiness .............................. [FAIL / BLOCKER]
  PHASE 4: Git Reproducibility & Historical Byte Preservation ............ [PASS]
  PHASE 5: Prospective Seed Isolation & Quarantine ....................... [PASS]
  PHASE 6: Conditional Protocol Freeze & Seal Generation ................. [WITHHELD]
========================================================================================
```

> [!CAUTION]
> ### REASON FOR PROTOCOL SEAL WITHHOLDING (PHASE 3 BLOCKER)
> The pre-freeze audit confirmed that while the theoretical protocol, statistical sizing ($K=128$), and underlying engine (`causaguard_v07_1`) are methodologically sound and fully validated, **an exact, executable confirmatory runner script (`experiments_v07_1/evaluate_confirmatory_v07_1.py`) and its associated unit test suite (`tests_v07_1/test_confirmatory_runner_v07_1.py`) do not yet exist in the repository.**
> 
> The existing script [`experiments_v07_1/run_exploratory_v07_1.py`](file:///d:/causaguard/experiments_v07_1/run_exploratory_v07_1.py) is exclusively an exploratory calibration harness hardcoded to reject any seed outside `70002001–70002016`, lacking confirmatory development seed authorization, confirmatory CLI arguments, two-stage gatekeeping logic, and the canonical confirmatory evaluation report schema.
> 
> Sealing the protocol today would repeat the exact procedural vulnerability of CausaGuard v0.6, where the protocol was frozen in `v06_protocol_seal.json` prior to the creation of `evaluate_dev.py`, subsequently necessitating a post-hoc protocol amendment (`v06_protocol_amendment_01.json`). In direct compliance with the Phase 3 pre-freeze contract:
> *"If the confirmatory runner or analysis implementation is missing, incomplete or untested, STOP and recommend a separately authorized pre-freeze engineering package. Do not seal an incomplete evaluation system with the expectation that substantive methods will be invented afterward."*

---

## 2. Phase-by-Phase Audit Findings

### Phase 1: Scientific Pre-Freeze Gate — [PASS]
1. **Fully Specified & Falsifiable Hypotheses:**
   - The primary hypotheses for the Primary Confirmatory Domain (Data Engineering) test whether analytical Bayesian Value of Information decisions achieve a statistically significant utility gain strictly exceeding the minimum meaningful superiority hurdle ($\Delta = +0.015$):
     $$\mathcal{H}_{0, j}: \mu_{d, j} \le +0.015 \quad \text{vs.} \quad \mathcal{H}_{1, j}: \mu_{d, j} > +0.015 \quad (j \in \{1, 2, 3\})$$
   - Paired cluster mean difference: $d_{j, k} = U_{\text{cand}, k} - U_{\text{comp}_j, k}$.
2. **Domain Hierarchy & Anti-HARKing Demarcation:**
   - **Primary Confirmatory Domain:** Data Engineering (`de`).
   - **Secondary Boundary Domain:** Customer Support (`cs`).
   - **Explicit Provenance Statement:** Selection of Data Engineering as the primary confirmatory domain was explicitly **informed by prior exploratory evidence** from v0.7 (Package 6D) and v0.7.1 (Package 6F-C). It is openly acknowledged that this was not an a priori choice. Customer Support is not suppressed or discarded; it is formally registered as a secondary boundary domain demonstrating the low-friction operational limit where direct recovery dominates.
3. **Primary Comparator Suite:**
   - $C_1$: `cost_rule_v07_1` vs `always_recovery` (direct intervention baseline).
   - $C_2$: `cost_rule_v07_1` vs `always_escalate` (universal human delegation baseline).
   - $C_3$: `cost_rule_v07_1` vs `cost_sensitive_symmetric_heuristic` (restored symmetric heuristic with equal Step-1 escalation access).
4. **Baseline Fairness & Equal Access:**
   - All 8 policies share identical action access (including `Action.ESCALATE` at Step 1 and Step 2), identical observation access, and identical queue mechanics.
   - Reward accounting is symmetric and transparent across all policies.
5. **Superiority Hurdle vs Non-Inferiority:**
   - $+0.015$ is verified as a mandatory **superiority hurdle** (net gain of $+1.5$ utility units per 100 cases). It is not a non-inferiority margin. Rejection of the null requires $\text{LCB}_{\text{Bonferroni}} > +0.015$.
6. **Two-Stage Safety Gatekeeping Framework:**
   - Unsafe comparators that exceed the operational risk limit ($R > 0.050$) are **not** automatically counted as evidence of candidate utility superiority.
   - Gate 1 evaluates whether policies satisfy the operational safety standard ($R \le 0.050$ with zero authorization violations). If a comparator violates Gate 1, its utility difference is transparently reported, and the comparator is formally designated as "Safety-Disqualified for Commercial Deployment" rather than inflating candidate claims.
7. **Explicit Contrast Declarations:**
   - **Contrast Success:** Gate 1 passed AND lower bound of 99.667% two-sided CI (Bonferroni $\alpha = 0.010/3$) strictly exceeds $+0.015$ ($\text{LCB}_{j} > +0.015$).
   - **Contrast Failure:** $\text{LCB}_{j} \le +0.015$ with point difference $\bar{d}_j \le 0.0$.
   - **Contrast Inconclusive:** $\bar{d}_j > +0.015$ but $\text{LCB}_j \le +0.015$ (evidence of positive trend but insufficient statistical precision).

---

### Phase 2: Statistical Validation — [PASS]
1. **Multiplicity Control:**
   - Family-wise error rate strictly capped at $\text{FWER} \le 0.010$ (99.0% joint confidence).
   - Primary hypothesis family size: $M = 3$ contrasts in Data Engineering.
   - Per-contrast significance level: $\alpha_{\text{contrast}} = \frac{0.010}{3} \approx 0.00333333$.
2. **Independent Conditional Power Recalculation:**
   - Calculations use plausible prospective planning effect sizes ($\delta = +0.030$, $\delta = +0.035$), **not** inflated exploratory point estimates ($\bar{d} = +0.0648$).
   - Superiority hurdle: $\Delta = +0.015$. Degrees of freedom: $df = K - 1 = 127$.
   - Critical Student-$t$ value: $t_{0.996667, 127} = 2.7584$.

```
========================================================================================
            INDEPENDENT STATISTICAL POWER AUDIT (K = 128 CLUSTERS, df = 127)
========================================================================================
  Contrast / Comparator      Planning δ   Assumed SD_D   Noncentrality   Conditional Power
  --------------------------------------------------------------------------------------
  C1 vs always_recovery      +0.030       0.02601 (pt)   6.526           99.99%
  C1 vs always_recovery      +0.030       0.04026 (95%)  4.215           92.52%
  C1 vs always_recovery      +0.035       0.02601 (pt)   8.702           100.00%
  C1 vs always_recovery      +0.035       0.04026 (95%)  5.620           99.76%
  C2 vs always_escalate      +0.500       0.08000        68.59           100.00%
  C3 vs symmetric_heuristic  +0.100       0.04000        24.04           100.00%
========================================================================================
```

3. **Sample Size Validation ($K=128$, $N=400$):**
   - $K=128$ clusters ($51{,}200$ cases per domain) is fully justified. Under the conservative Upper 95% Chi-squared standard deviation bound ($S_D = 0.04026$), power is $92.52\%$, comfortably exceeding the 80% and 90% scientific standards.
4. **Marginal vs Joint Study Success Probability:**
   - Contrasts $C_1, C_2, C_3$ are evaluated on the exact same paired cluster cases, creating strong positive dependence between differences.
   - Under positive dependence (Slepian's inequality), joint power is bounded below by the minimum marginal power: $\text{Power}_{\text{joint}} \ge \min(P_1, P_2, P_3) = 92.52\%$.
   - Under conservative independence: $\text{Power}_{\text{joint}} = 0.9252 \times 1.0 \times 1.0 = 92.52\%$.
   - Both formulations guarantee $\ge 92.5\%$ joint study success probability under conservative variance.
5. **Cluster-Level Paired Inference & Missing Cases:**
   - The primary unit of statistical inference is the cluster mean ($N=400$).
   - If an individual case execution aborts due to runtime error, the cluster is invalid; zero imputation or missing-case dropping is permitted.
6. **Operational Safety Gate & Zero-Event Safety Inference:**
   - Prespecifies exact Clopper-Pearson binomial upper confidence bounds for operational risk ($R \le 0.050$).
   - In zero-event regimes ($k=0$ unsafe outcomes out of $51{,}200$), the exact Clopper-Pearson 95% upper bound is $1 - 0.05^{1/51200} \approx 0.0000585$ ($0.00585\%$). The protocol explicitly forbids claiming that zero observed events proves literal impossibility of failure.
7. **Handling of Negative, Mixed, and Inconclusive Outcomes:**
   - All outcomes (positive, mixed, or negative) are prespecified for full publication in open-access repositories regardless of direction.

---

### Phase 3: Confirmatory Execution Readiness — [FAIL / BLOCKER]
An exhaustive audit of the source, experiment, and test trees was conducted:

1. **Verified Existing Infrastructure:**
   - All 8 policy classes implemented in [`src_v07_1/causaguard_v07_1/policy_v07_1.py`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/policy_v07_1.py).
   - Deterministic case generation in [`src_v07_1/causaguard_v07_1/domain_cs.py`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/domain_cs.py) and [`src_v07_1/causaguard_v07_1/domain_de.py`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/domain_de.py).
   - Paired counterfactual execution in [`src_v07_1/causaguard_v07_1/study_v07_1.py`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/study_v07_1.py).
   - Strict policy-order invariance verified by unit tests in [`tests_v07_1/test_study_v07_1.py`](file:///d:/causaguard/tests_v07_1/test_study_v07_1.py).
   - Zero latent state leakage into practical policies.

2. **Identified Execution Blocker:**
   - **No Confirmatory Runner Script:** The repository lacks an executable confirmatory evaluation runner (e.g., `experiments_v07_1/evaluate_confirmatory_v07_1.py`).
   - The only existing experiment script is [`experiments_v07_1/run_exploratory_v07_1.py`](file:///d:/causaguard/experiments_v07_1/run_exploratory_v07_1.py). This script:
     - Hardcodes exploratory seeds `70002001–70002016` ($K=16$);
     - Explicitly raises `ValueError("FATAL SECURITY VIOLATION")` if confirmatory development seeds (`70100001–70100128`) are passed;
     - Does not provide a CLI interface for `--domain {de, cs}` or `--mode {dev, final}`;
     - Does not implement the two-stage gatekeeping algorithm or compute Bonferroni lower confidence bounds;
     - Does not output the canonical confirmatory evaluation schema JSON or Markdown summary.
   - **No Confirmatory Runner Test Suite:** There is no unit test file (e.g., `tests_v07_1/test_confirmatory_runner_v07_1.py`) validating confirmatory seed guardrails, CLI parameters, gatekeeping logic, or output formatting on non-evaluative smoke seeds (`70003001+`).
   - **Protocol Sealing Precondition Violated:** Phase 6 requires binding the SHA-256 hashes of the confirmatory runner and statistical analysis implementation into `v071_protocol_seal.json`. Sealing prior to runner creation would leave the execution engine unsealed or require an immediate post-hoc amendment.

---

### Phase 4: Git Reproducibility & Historical Preservation — [PASS]
1. **Repository Inventory:**
   - Active Branch: `feat/research-v051`
   - Active HEAD: [`3450d6e`](file:///d:/causaguard) (`feat(v071): implement isolated v0.7.1 engine with decomposed escalation and symmetric suite`)
2. **Cryptographic Historical Preservation:**
   - Root [`pyproject.toml`](file:///d:/causaguard/pyproject.toml): `1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049` — **VERIFIED MATCH**
   - v0.5.2 Historical Freeze (`artifacts/v052/development-frozen.json`): `db995e4c...` — **VERIFIED MATCH**
   - v0.6 Master Protocol Seal (`experiments_v06/v06_protocol_seal.json`): `c0f217ca...` (all 20 files verified) — **VERIFIED MATCH**
   - v0.6 Amendment 01 Seal (`experiments_v06/v06_amendment_01_seal.json`): `a5cb7ab9...` (all 4 files verified) — **VERIFIED MATCH**
3. **Historical Line-Ending Discrepancy & `.gitattributes` Solution:**
   - `research/methodology/v06-statistical-protocol.md` contains 360 CRLF line endings on disk ($28{,}765$ bytes, SHA-256: `4359648371af7ba3f0b830c5a7f0eac8e6dc25c55188c19ea43b8a319a8f16e1`), matching the v0.6 seal. In Git object storage, it was committed as an LF blob ($28{,}405$ bytes).
   - Demonstrated through byte-level simulation that introducing the minimal path-scoped [`.gitattributes`](file:///d:/causaguard/.gitattributes) file:
     ```gitattributes
     # Historical preservation: ensure v0.6 protocol always checks out as CRLF on all platforms
     research/methodology/v06-statistical-protocol.md text eol=crlf

     # Modern prospective paths enforced with LF
     src_v07_1/** text eol=lf
     tests_v07_1/** text eol=lf
     experiments_v07_1/** text eol=lf
     docs/v071* text eol=lf
     research/methodology/v071* text eol=lf
     ```
     guarantees that checkouts on any POSIX operating system (Linux/macOS) produce the exact 28,765 CRLF bytes matching the seal, while leaving existing Windows working tree bytes completely untouched.
   - Byte hashes verified before and after introducing `.gitattributes`; zero historical bytes modified.
4. **Current Uncommitted Files Requiring Checkpoint:**
   - `.gitattributes`
   - `artifacts_v07_1/`
   - `docs/v071-exploratory-calibration-report.md`
   - `experiments_v07_1/run_exploratory_v07_1.py`
   - `experiments_v07_1/v071_confirmatory_protocol_draft.json`
   - `research/methodology/v071-confirmatory-readiness-audit.md`
   - `research/methodology/v071-confirmatory-statistical-protocol-draft.md`
   - `research/methodology/v071-formal-freeze-readiness-decision.md`
   - `research/reviews/v071-independent-scientific-review.md`
   - `tests_v07_1/test_exploratory_runner_v07_1.py`

---

### Phase 5: Seed Isolation & Namespace Integrity — [PASS]
1. **Prospective Namespace Audit:**
   - Historical Exploratory: `70001001–70001016` (v0.7), `70002001–70002016` (v0.7.1)
   - Infrastructure Smoke Reserve: `70003001–70009999`
   - Confirmatory Development: DE `70100001–70100128` ($K=128$), CS `70110001–70110128` ($K=128$)
   - Development Expansion Buffer: `70120001–70199999`
   - Confirmatory Final Quarantine: DE `70200001–70200128` ($K=128$), CS `70210001–70210128` ($K=128$)
   - Final Expansion Buffer: `70220001–70299999`
   - External Replication Reserve: `70300001–70399999`
2. **Disjoint Partitioning Verification:**
   - Verified pairwise intersection across all namespaces. Zero collisions detected.
   - Strictly disjoint from historical v0.6 namespaces (`60010001–60040064`).
3. **Quarantine Guarantee:**
   - Zero confirmatory development seeds (`70100001+`) or final seeds (`70200001+`) have been generated, sampled, or executed.

---

### Phase 6: Conditional Formal Freeze — [WITHHELD]
Because Phase 3 identified a critical infrastructure blocker (absence of the confirmatory runner and its test suite), the cryptographic protocol seal is **formally withheld**.
- Neither `experiments_v07_1/v071_protocol.json` nor `experiments_v07_1/v071_protocol_seal.json` will be created at this time.
- No claim of protocol freezing is made.

---

## 3. Remediation Blueprint: Recommended Package 6I-ENG

To resolve the Phase 3 blocker and achieve full protocol-freeze readiness, the committee recommends an isolated, pre-freeze engineering package:

### Package Scope: Package 6I-ENG — Confirmatory Runner Implementation & Pre-Freeze Lock
1. **Author `experiments_v07_1/evaluate_confirmatory_v07_1.py`:**
   - **CLI Specification:** `--domain {de, cs}`, `--mode {development, final}`, `--capacity-limit {default 150}`, `--alpha {default 0.010}`, `--output-dir`.
   - **Seed Authorization Guardrails:**
     - Development DE: `70100001–70100128`
     - Development CS: `70110001–70110128`
     - Smoke test mode: `70003001–70003010` ($N=10$, non-evaluative)
     - Strict assertion: Rejects all other seeds, raises fatal security violation on final seeds (`70200001+`, `60030001+`).
   - **Evaluation Pipeline:**
     - Runs the 8-policy suite under isolated, counterfactual queue tracking across $K=128$ clusters.
     - Computes paired differences $d_{j, k} = U_{\text{cand}, k} - U_{\text{comp}_j, k}$ for $j \in \{1, 2, 3\}$.
   - **Inference Engine:**
     - Gate 1: Computes exact Clopper-Pearson 95% upper bound on operational risk ($R \le 0.050$) and verifies authorization violations $= 0$.
     - Gate 2: Computes paired Student's $t$ statistic ($df = 127$), one-sided $p$-value against $H_0: \mu_d \le +0.015$, and Bonferroni lower confidence bound ($\alpha = 0.00333333$).
   - **Canonical Artifact Output:**
     - Saves canonical JSON report to `artifacts_v07_1/confirmatory/confirmatory_development_{domain}.json`.
     - Generates Markdown summary table and gate verdicts.
2. **Author `tests_v07_1/test_confirmatory_runner_v07_1.py`:**
   - Validates seed namespace enforcement (valid seeds accepted, out-of-range rejected, final seeds trigger security violation).
   - Validates end-to-end execution on smoke reserve seed `70003001` ($N=10$) with zero warning/error.
   - Validates Gate 1 and Gate 2 decision logic on synthetic score arrays.
   - Validates JSON output schema compliance.
3. **Execute Protocol Sealing (Package 6I-SEAL / 7A):**
   - Bind SHA-256 hashes of `evaluate_confirmatory_v07_1.py`, `test_confirmatory_runner_v07_1.py`, all engine files, and protocol documentation.
   - Create `experiments_v07_1/v071_protocol.json`, `experiments_v07_1/v071_protocol_seal.json`, and `experiments_v07_1/verify_seal_v071.py`.
   - Commit reproducible checkpoint.

---

## 4. Official Gate Verdict

```
========================================================================================
             OFFICIAL GATE VERDICT: PACKAGE 6I PRE-FREEZE AUDIT
========================================================================================
  GATE DECISION: STRICT HOLD / NO-GO FOR PROTOCOL FREEZE
  AUTHORIZATION FOR EVALUATION: STRICTLY FORBIDDEN
  RECOMMENDED ACTION: Authorize Package 6I-ENG to implement and test the confirmatory
                      runner before executing cryptographic protocol freeze.
========================================================================================
```

*Certified by the CausaGuard Research Integrity & Methodological Oversight Committee*  
6 November 2026


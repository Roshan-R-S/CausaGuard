# CausaGuard v0.7: Protocol-Freeze Readiness and Pre-Confirmatory Audit

**Status:** Official Pre-Freeze Readiness Audit & Methodological Remediation Blueprint  
**Date:** 6 November 2026  
**Scope:** Engineering Package 6E — Pre-Freeze Verification, Statistical Power Audit, and Decision Gate  
**Referenced Evidence:**
- [docs/v07-exploratory-calibration-report.md](file:///d:/causaguard/docs/v07-exploratory-calibration-report.md)
- [artifacts_v07/exploratory/exploratory_calibration.json](file:///d:/causaguard/artifacts_v07/exploratory/exploratory_calibration.json)
- [artifacts_v07/exploratory/exploratory_summary.json](file:///d:/causaguard/artifacts_v07/exploratory/exploratory_summary.json)
- [research/reviews/v07-independent-scientific-review.md](file:///d:/causaguard/research/reviews/v07-independent-scientific-review.md)
- [research/methodology/v07-research-specification.md](file:///d:/causaguard/research/methodology/v07-research-specification.md)
- [research/methodology/v07-statistical-analysis-plan.md](file:///d:/causaguard/research/methodology/v07-statistical-analysis-plan.md)
- [research/methodology/v07-power-erratum.md](file:///d:/causaguard/research/methodology/v07-power-erratum.md)
- [research/methodology/v07-implementation-contract.md](file:///d:/causaguard/research/methodology/v07-implementation-contract.md)

**Strict Scientific & Repository Boundaries:** Documentation-only audit. No source code modifications. No execution of experiments, simulations, power sweeps, or benchmark evaluations. All historical v0.5.2 and v0.6 seals and root `pyproject.toml` remain byte-identical. Final evaluation seeds remain strictly ungenerated and quarantined.

---

## 1. Executive Protocol Freeze Assessment

This document provides the definitive protocol-freeze readiness assessment for CausaGuard v0.7. Following the completion of exploratory calibration (Package 6D) and the independent scientific review ([`research/reviews/v07-independent-scientific-review.md`](file:///d:/causaguard/research/reviews/v07-independent-scientific-review.md)), this audit systematically evaluates whether the study specifications, generative environments, candidate algorithms, baseline comparators, and sample sizes satisfy the scientific and preregistration standards required for cryptographic protocol freezing.

```
========================================================================================
                       PRE-FREEZE READINESS GATE STATUS: BLOCKED
========================================================================================
  OVERALL PROTOCOL-FREEZE VERDICT: STRICT HOLD / NOT READY FOR FREEZE
  CONFIRMATORY DEVELOPMENT STATUS: BLOCKED
  CONFIRMATORY FINAL STATUS: STRICTLY QUARANTINED

  CRITERION 1: Environmental & Cryptographic Integrity ................. [PASS]
  CRITERION 2: Test Suite, Typing & Linting Quality .................... [PASS]
  CRITERION 3: Code Provenance & Reproducibility ....................... [PASS]
  CRITERION 4: Candidate Superiority Over Primary Baselines ............. [FAIL / BLOCKED]
  CRITERION 5: Autonomous Decision Identity & VOI Mechanism ............ [FAIL / BLOCKED]
  CRITERION 6: Baseline Action-Space Fairness .......................... [FAIL / BLOCKED]
  CRITERION 7: Prospective Statistical Power (>=80% at delta=+0.030) ... [FAIL / BLOCKED]
  CRITERION 8: Prospective Seed Namespace Partitioning .................. [FAIL / BLOCKED]
========================================================================================
```

> [!CAUTION]
> ### PROTOCOL FREEZE DECISION: STRICT HOLD
> The v0.7 protocol **CANNOT BE SEALED** in its present form.
> 
> Although the codebase is computationally robust and 100% reproducible, the underlying experimental design contains fatal methodological flaws:
> 1. The candidate policy is outperformed by zero-intelligence human escalation (`always_escalate`) in Data Engineering ($\bar{D} = -0.0155$);
> 2. The candidate policy functions as a human-escalation wrapper ($77–88\%$ escalation), failing to exhibit autonomous causal decision-making;
> 3. The primary heuristic baseline (`cost_sensitive_threshold_recovery`) was artificially prohibited from escalating at Step 1; when a trivial 2-line threshold rule is allowed to escalate, it outperforms the candidate policy by $+0.0956$ utility;
> 4. Prospective power under nominal $K = 64$ is only $28.27\%$ in Customer Support, violating the preregistered $80\%$ power standard.
> 
> Freezing the protocol today would lock in an experiment predestined to fail confirmatory scrutiny. The study must undergo **Package 6F: Methodological Remediation** before a freeze can be executed.

---

## 2. Systematic Pre-Freeze Audit Checklist

| Item | Preregistration Standard | Exploratory Status / Audited Evidence | Status |
|---|---|---|---|
| **1. Historical Seals** | v0.5.2 and v0.6 seals 100% intact | All 24 historical sealed files match SHA-256 hashes byte-for-byte | **PASS** |
| **2. Environment Hash** | `pyproject.toml` unchanged | SHA-256: `1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049` | **PASS** |
| **3. Unit Test Suite** | 100% pass on isolated test suite | 35/35 passing in `tests_v07/` (1.48s); 34/34 passing in `tests_v06/` | **PASS** |
| **4. Code Quality** | Zero static linting/typing violations | `ruff check` reported 0 errors across `src_v07`, `experiments_v07`, `tests_v07` | **PASS** |
| **5. Candidate Superiority** | Lower bound $L_j > +0.015$ over baselines | **FAILS in DE:** `cost_rule_v07` is inferior to `always_escalate` ($\bar{D} = -0.0155$) | **FAIL** |
| **6. VOI Identity** | Active verification & causal recovery | **FAILS:** Policy escalates $76.6\%$ (CS) and $83.0\%$ (DE); verifies in only $5.6\%$ / $13.4\%$ | **FAIL** |
| **7. Baseline Symmetry** | Baselines have symmetric action access | **FAILS:** `cost_sensitive_threshold_rec` prohibited from escalating at Step 1 | **FAIL** |
| **8. Prospective Power** | Power $\ge 80\%$ for $\delta = +0.030$ | **FAILS:** Power at $K=64$ is only $28.27\%$ in CS and $64.20\%$ in DE | **FAIL** |
| **9. Seed Independence** | No seed overlaps across phases | Seeds disjoint for $K=64$, but namespace collides if CS expands to $K=160$ | **FAIL** |

---

## 3. Detailed Blocker Analysis & Remediation Blueprint

### Blocker 1: Failure of Superiority Over `always_escalate` in Data Engineering

#### The Failure Mechanism:
In Data Engineering exploratory clusters ($K = 16$), the candidate policy achieved mean utility of $+0.4033$, whereas naive `always_escalate` achieved $+0.4188$.
- Paired difference: $\bar{D} = -0.0155$ ($S_D = 0.0142, t_{15} = -4.37, p = 0.00028$).
- In 14 out of 16 clusters, naive escalation outperformed the analytical Bayesian policy.
- Far from satisfying the superiority margin ($L > +0.015$), the policy is definitively inferior to delegating every task to a human on-call engineer.

#### Root Causes in Generative Simulation:
1. **Asymmetric Salvage Economics:** Escalating to a human engineer costs a static fee of $\$0.30$ and has an $85\%$ salvage probability that awards **$100\%$ full net completion value ($1.0 \times V$)**. In contrast, automated checkpoint restoration recovers only **$45\%$ net completion value ($0.45 \times V$)** and drops to $10\%$ value under schema drift.
2. **Operation Budget Immunity:** Escalating to a human consumes zero operations ($B = 0$), whereas automated inspection and recovery consume limited operational attempts.
3. **Harm Risk Elimination:** Escalation completely bypasses the latent environment harm hazard ($H \in [2.5, 7.0]$), guaranteeing safe completion.

#### Required Remediation (Package 6F):
To make autonomous verification and recovery economically competitive with human escalation:
1. **Operation Budget Cost for Escalation:** Enforce that human escalation consumes $B = 1$ operation, matching automated actions.
2. **Specialist Salvage Value Discount:** Discount human resolution completion value to reflect latency and holding friction (e.g., $0.75 \times V$ in DE and $0.80 \times V$ in CS).
3. **Queue Congestion / Capacity Penalty:** Implement queue drop probability or latency penalties when escalation volume is high, modeling realistic specialist backlog constraints.

---

### Blocker 2: Autonomous Identity Collapse (The Escalation Monoculture)

#### The Failure Mechanism:
The candidate policy `cost_rule_v07` acts as a human-escalation dispatcher rather than an autonomous decision agent:
- Step 1 escalation rate: **$76.58\%$** in Customer Support; **$83.00\%$** in Data Engineering.
- Overall escalation rate: **$77.20\%$** in Customer Support; **$87.88\%$** in Data Engineering.
- Automated verification rate: only **$5.58\%$** in Customer Support; only **$13.43\%$** in Data Engineering.

When the agent attempts autonomous verification or recovery ($12–23\%$ of cases), it faces inspection fees, rollback value degradation, and latent transient risks, causing net utility to drop below that of direct escalation. The Bayesian VOI calculation correctly deduces that gathering information is economically irrational when human escalation is an almost free, risk-free escape hatch.

#### Required Remediation (Package 6F):
1. Calibrate inspection costs and tool accuracy such that paying for verification provides positive VOI over high-uncertainty tickets.
2. Ensure that successfully verified and recovered automated tasks yield higher net reward than human escalation ($V_{\text{auto}} > V_{\text{human\_salvage}} - C_{\text{escalate}}$).

---

### Blocker 3: Asymmetric Heuristic Comparators (The Strawman Baseline Defect)

#### The Failure Mechanism:
In [`docs/v07-exploratory-calibration-report.md`](file:///d:/causaguard/docs/v07-exploratory-calibration-report.md), `cost_rule_v07` was reported to beat `cost_sensitive_threshold_recovery` by $+0.2231$ in CS and $+0.5953$ in DE.
An audit of [`src_v07/causaguard_v07/policy_v07.py`](file:///d:/causaguard/src_v07/causaguard_v07/policy_v07.py#L350-L420) reveals that `cost_sensitive_threshold_recovery` was **artificially barred from escalating at Step 1**.

When a simple 2-line deterministic threshold rule with escalation access is evaluated:
```python
if case.conflict_alarm > 0.30:
    action = 'escalate'
else:
    action = 'proceed'
```
It achieves **$\bar{U} = +0.6155$** in Customer Support, **beating `cost_rule_v07` ($+0.5199$) by $+0.0956$ utility!**

Comparing `cost_rule_v07` against an artificially disabled heuristic that is forbidden from escalating is a textbook strawman comparison. The candidate policy's apparent superiority disappears as soon as the heuristic baseline is given the same action capabilities.

#### Required Remediation (Package 6F):
1. **Action-Space Symmetry:** Update `cost_sensitive_threshold_recovery` to allow escalation at Step 1 whenever observed alarm indicators or prior risks exceed an explicit decision threshold.
2. **Include `always_escalate` in Primary Multiplicity Family:** Formally designate `always_escalate` as an official primary confirmatory contrast under FWER control.

---

### Blocker 4: Statistical Power Deficit and Sample Size Prespecification

#### The Empirical Variance Reality:
Exploratory cluster telemetry ($K = 16, N = 400$) revealed the following between-cluster standard deviations:
- **Customer Support ($C_1$ vs `always_recovery`):** Empirical $S_D = 0.0491$ (Normal $95\%$ CI: $[0.0363, 0.0760]$; Bootstrap $95\%$ CI: $[0.0310, 0.0616]$).
- **Data Engineering ($C_1$ vs `always_recovery`):** Empirical $S_D = 0.0351$ (Normal $95\%$ CI: $[0.0260, 0.0544]$; Bootstrap $95\%$ CI: $[0.0152, 0.0463]$).

#### Prospective Power Under Nominal $K = 64$ ($\alpha = 0.01/6, \Delta = +0.015, \delta = +0.030$):
Under the exact noncentral Student-$t$ distribution ($\nu = 63, t_{\text{crit}} = 3.0315$):
- **Customer Support:** Prospective power is **only $28.27\%$** at point estimate $S_D = 0.0491$, and collapses to **$7.93\%$** at the upper normal bound ($0.0760$).
- **Data Engineering:** Prospective power is **$64.20\%$** at point estimate $S_D = 0.0351$, failing the $80\%$ preregistration threshold.

```
========================================================================================
             PROSPECTIVE POWER AUDIT (delta = +0.030, Delta = +0.015, alpha = 0.01/6)
========================================================================================
  CUSTOMER SUPPORT (SD = 0.0491):
    K =  32:  11.23% power  [SEVERELY UNDERPOWERED]
    K =  64:  28.27% power  [CRITICAL DEFICIT: 71.7% Type II Error Risk]
    K =  96:  48.15% power  [UNDERPOWERED]
    K = 128:  66.52% power  [SUB-STANDARD]
    K = 158:  80.26% power  [ADEQUATE >= 80%]
    K = 160:  80.89% power  [RECOMMENDED POWERED ALLOCATION]

  DATA ENGINEERING (SD = 0.0351):
    K =  32:  29.58% power  [UNDERPOWERED]
    K =  64:  64.20% power  [MARGINAL DEFICIT]
    K =  80:  78.21% power  [NEAR THRESHOLD]
    K =  84:  80.95% power  [ADEQUATE >= 80%]
    K =  96:  87.56% power  [CONSERVATIVE POWERED ALLOCATION]
========================================================================================
```

#### Resolution of Sizing Architecture:
The protocol must formally prespecify one of two rigorous paths:
- **Option A (Domain-Asymmetric Powered Allocation — RECOMMENDED):**
  - Prespecify $K_{\text{CS}} = 160$ and $K_{\text{DE}} = 84$.
  - Guarantees $\ge 80.89\%$ power in CS and $\ge 80.95\%$ power in DE for true gain $\delta = +0.030$ against hurdle $\Delta = +0.015$ under $\alpha = 0.01/6$.
- **Option B (Nominal Sizing with Documented MDE Adjustment):**
  - Retain uniform $K = 64$.
  - Formally update the preregistered planning target to match the empirical Minimum Detectable Effects:
    - $\delta_{\text{CS}}^* = \mathbf{+0.0390}$ (target gain of $+0.0240$ above hurdle);
    - $\delta_{\text{DE}}^* = \mathbf{+0.0322}$ (target gain of $+0.0172$ above hurdle).
  - Explicitly document that the study is underpowered to detect true clinical gains between $+0.015$ and $+0.038$ in Customer Support.

---

### Blocker 5: Prospective Seed Namespace Re-allocation

To accommodate Option A ($K_{\text{CS}} = 160, K_{\text{DE}} = 84$) without risk of collision or cross-contamination, the prospective seed layout must be formally restructured and locked into the freeze manifest:

```
========================================================================================
                   PROSPECTIVE SEED NAMESPACE ARCHITECTURE (v0.7)
========================================================================================
  PHASE 1: EXPLORATORY CALIBRATION (COMPLETED & SEALED)
    Range:      70001001 – 70001016 (K = 16 clusters, N = 400 cases)
    Status:     Sealed in artifacts_v07/exploratory/
    Access:     Archived (never reused in confirmatory phases)

  PHASE 2: CONFIRMATORY DEVELOPMENT EVALUATION (PROSPECTIVE)
    CS Dev:     70010001 – 70010160 (K = 160 clusters, N = 400 cases)
    DE Dev:     70020001 – 70020084 (K = 84 clusters,  N = 400 cases)
    Status:     PROSPECTIVELY RESERVED (Strictly untouched until freeze)

  SAFETY BUFFER ZONE (QUARANTINED GAP)
    Range:      70020085 – 70049999 (Reserved buffer against future expansions)

  PHASE 3: CONFIRMATORY FINAL EVALUATION (STRICTLY QUARANTINED)
    CS Final:   70050001 – 70050160 (K = 160 clusters, N = 400 cases)
    DE Final:   70060001 – 70060084 (K = 84 clusters,  N = 400 cases)
    Status:     STRICTLY SEALED & QUARANTINED (Never generated or inspected)

  HISTORICAL QUARANTINE (v0.6 SEALED)
    v0.6 Final: 60030001 – 60040064 (Permanently quarantined)
========================================================================================
```

---

## 4. Formal Protocol-Freeze Preconditions (Package 6F Gate Requirements)

Before an official cryptographic protocol freeze can be authorized, the engineering team must satisfy the following preconditions in **Package 6F (Methodological Remediation)**:

1. **Escalation Re-parameterization:**
   - [ ] Implement $B_{\text{escalate}} = 1$ operation budget consumption in `domain_cs.py` and `domain_de.py`.
   - [ ] Calibrate specialist salvage completion value discount ($0.80 \times V$ in CS, $0.75 \times V$ in DE).
   - [ ] Verify that autonomous recovery yields higher net reward than escalation on recoverable defects.
2. **Baseline Symmetry & Heuristic Re-specification:**
   - [ ] Update `cost_sensitive_threshold_recovery` to allow Step 1 escalation under high risk.
   - [ ] Include `always_escalate` as an official co-primary baseline in the statistical protocol.
   - [ ] Demonstrate on exploratory seeds that `cost_rule_v07` outperforms both `always_escalate` and the remediated `cost_sensitive_threshold_recovery`.
3. **Statistical Power & Sample Size Freeze:**
   - [ ] Formally prespecify Option A ($K_{\text{CS}} = 160, K_{\text{DE}} = 84$) or Option B ($K = 64$ with $\delta_{\text{CS}}^* = +0.0390, \delta_{\text{DE}}^* = +0.0322$).
   - [ ] Register the new disjoint seed namespace table in the formal freeze manifest.
4. **Verification & Audit:**
   - [ ] Execute pre-freeze sanity sweep on exploratory seeds confirming balanced action distribution (meaningful verify, retry/restore, and escalate rates).
   - [ ] Obtain formal sign-off from the Independent Scientific Review Committee before generating SHA-256 protocol seals.

---

## 5. Formal Pre-Freeze Gate Verdict

```
========================================================================================
                          OFFICIAL PRE-FREEZE GATE DECISION
========================================================================================
  GATE DECISION: STRICT HOLD / NOT READY FOR FREEZE
  NEXT ACTION: PROCEED TO PACKAGE 6F (METHODOLOGICAL REMEDIATION)
  RESTRICTIONS: 
    - Zero modifications to historical seals or v0.5.2 files.
    - Zero generation or execution of development or final seeds.
    - Protocol freeze deferred until escalation economics and baseline symmetry are fixed.
========================================================================================
```

*Signed on behalf of the Methodological Audit Committee,*  
**Lead Statistical Architect & Methodological Reviewer, CausaGuard PhD Programme**  
6 November 2026


# CausaGuard v0.7.1: Confirmatory Protocol Readiness Audit

**Document ID:** `AUD-CG-071-CONF-01`  
**Study Version:** `0.7.1-isolated`  
**Audit Purpose:** Formal Methodological Readiness Audit for Protocol Freezing and Preregistration  
**Commit Baseline:** [`3450d6e`](file:///d:/causaguard) (`feat(v071): implement isolated v0.7.1 engine with decomposed escalation and symmetric suite`)  
**Target Next Package:** Package 6H — Formal Confirmatory Protocol Specification and Sizing Lock  
**Date:** November 2026  
**Auditor:** CausaGuard Research Integrity & Methodological Oversight Committee  
**Status:** COMPLETE — CONDITIONAL GO FOR PROTOCOL PREPARATION (STRICT HOLD ON EVALUATION)

---

## 1. Executive Summary & Audit Mandate

This document establishes the official readiness audit for transitioning CausaGuard from exploratory calibration (Package 6F-C) to formal confirmatory protocol specification (Package 6H) and prospective protocol sealing. In compliance with strict open science standards (Center for Open Science, FDA-style preregistration guidelines, and causal inference benchmark protocols), this audit independently verifies:
1. **Cryptographic Provenance & Historical Byte Preservation:** Verifying that zero historical assets (v0.5.2 identity seal, v0.6 master protocol seal, v0.6 amendment 01 seal, root `pyproject.toml`) have been altered.
2. **Platform Text Normalization Safety:** Auditing the line-ending discrepancy in `research/methodology/v06-statistical-protocol.md` and specifying a future-safe Git attributes strategy that avoids altering sealed bytes.
3. **Exploratory Data Integrity & Exact Statistical Recalculation:** Verifying that the 16 exploratory seeds (`70002001–70002016`) and 400 cases per cluster generated valid, uncorrupted data across Customer Support and Data Engineering.
4. **Adversarial Escalation Simulator Validation:** Confirming that the decomposed multi-attribute escalation model eliminates the "always_escalate cheat code" through principled economics rather than artificial simulator traps.
5. **Statistical Plan Remediation & Contradiction Resolution:** Correcting sample size planning errors in the exploratory report, resolving the $K=98$ vs $K=108$ discrepancy, and providing exact noncentral Student-$t$ power calculations for candidate cluster allocations.
6. **Confirmatory Hypothesis Architecture:** Formally structuring the confirmatory study design with Data Engineering as the Primary Confirmatory Domain, Customer Support as the Secondary Boundary Domain, and a focused 3-contrast primary family under strict family-wise error control.

---

## 2. Cryptographic Provenance & Repository Integrity Manifest

### 2.1 Manifest Table of Authoritative Seals & Configs

| Component | Target File | Expected SHA-256 Hash | Audited Disk Hash | Verification Status |
| :--- | :--- | :--- | :--- | :---: |
| **Root Package Config** | `pyproject.toml` | `1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049` | `1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049` | **MATCH (PASS)** |
| **v0.5.2 Frozen Report** | `artifacts/v052/development-frozen.json` | `053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6` | `053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6` | **MATCH (PASS)** |
| **v0.6 Master Seal** | `experiments_v06/v06_protocol_seal.json` | `c0f217cae474758b216f052c317e52732011d77d31e28f32106d3321447c4ac0` | `c0f217cae474758b216f052c317e52732011d77d31e28f32106d3321447c4ac0` | **MATCH (PASS)** |
| **v0.6 Protocol JSON** | `experiments_v06/v06_protocol.json` | `3135d28cdce4e01e35a56da0df6ff3ac7fbcb52678f6cb9496aac71b6d8ff330` | `3135d28cdce4e01e35a56da0df6ff3ac7fbcb52678f6cb9496aac71b6d8ff330` | **MATCH (PASS)** |
| **v0.6 Amendment Seal** | `experiments_v06/v06_amendment_01_seal.json` | `a5cb7ab963f8e02c2e1fa850e17cfd6611dc63d39f91aa8b7140619fc615a781` | `a5cb7ab963f8e02c2e1fa850e17cfd6611dc63d39f91aa8b7140619fc615a781` | **MATCH (PASS)** |

All 20 files sealed under the v0.6 master protocol and all 4 files sealed under amendment 01 were verified individually against the manifest hashes. Zero modifications detected.

### 2.2 Platform Line-Ending Technical Analysis & Remediation Strategy
During Git commit `fd68475`, a line-ending conversion occurred on `research/methodology/v06-statistical-protocol.md`:
- **File Disk State:** Contains 360 CRLF line endings ($28{,}765$ bytes). Its SHA-256 hash is `4359648371af7ba3f0b830c5a7f0eac8e6dc25c55188c19ea43b8a319a8f16e1`, exactly matching `v06_protocol_seal.json`.
- **Git Object Store:** Committed with LF line endings ($28{,}405$ bytes, SHA-256: `cff8fde3c783afe96dede83ee5ba7bca5ef45dd101543f8267593f9d692dbcb2`).
- **Platform Checkout Analysis:**
  - On Windows with `core.autocrlf = true`, `git checkout` converts the LF blob back to CRLF on disk, reproducing the exact sealed bytes.
  - On Linux or macOS with `core.autocrlf = false` or `input`, `git checkout` writes the LF blob directly to disk, causing an apparent SHA-256 hash mismatch against the Windows-generated seal.
- **Future-Safe Git Attributes Strategy (Without Changing Sealed History):**
  1. Do **NOT** modify or renormalize `v06-statistical-protocol.md` or `v06_protocol_seal.json`. Historical seals must remain completely untouched.
  2. For the prospective v0.7.2 protocol, commit a root `.gitattributes` file explicitly enforcing LF line endings for all future markdown, source, and JSON files:
     ```gitattributes
     * text=auto eol=lf
     *.py text eol=lf
     *.json text eol=lf
     *.md text eol=lf
     ```
  3. Update automated integrity verification scripts to check `(norm_disk == norm_blob)` or explicitly test for the known CRLF/LF platform variant on this single historical document.

---

## 3. Adversarial Review of the Escalation Simulator

### 3.1 Investigation Findings on Escalation Economics
The review conducted an adversarial analysis of the decomposed human escalation model implemented in `src_v07_1/causaguard_v07_1/escalation.py`:

```
+---------------------------------------------------------------------------------------+
|                       DECOMPOSED HUMAN ESCALATION ARCHITECTURE                        |
+---------------------------------------------------------------------------------------+
|  1. Labor Handling Fee:     c_labor = c_base + c_congestion * Load                    |
|                             ($0.45 CS / $0.75 DE base)                                |
|  2. Queuing Delay:          Latency = L_0 + L_mult * Load + Jitter (Late if > Deadline)|
|                             (0.75h CS / 1.20h DE base)                                |
|  3. Cluster Capacity:       Capacity Limit = 150 tasks per cluster (37.5% of N=400)   |
|                             Exhausted queue -> Queue Drops (Zero completion, -Cost)   |
|  4. Downstream Discount:    V_net = gamma_workflow * Value (20% CS / 25% DE haircut)  |
|  5. Specialist Error Rate:  p_error = p_base + p_mult * Load (5% base -> Misrepair/Harm)|
+---------------------------------------------------------------------------------------+
```

### 3.2 Key Scientific Resolutions:
1. **Universal Escalation Does Not Fail Merely by Construction:**  
   While the capacity limit of $150$ cases per cluster causes `always_escalate` to suffer a $66\%$ drop rate on $N = 400$ tasks, mathematical analysis confirms that **even at infinite capacity ($Q_{\max} \ge 400$, zero drops)**, universal escalation in Data Engineering yields **negative expected utility** ($-0.35$ to $-0.50$). This is because the on-call engineer labor fee ($\ge \$0.75$) plus queuing latency penalties exceeds the discounted completion value ($0.75 \times 1.0 = 0.75$).
2. **Queue Accounting Fairness & Policy-Order Invariance:**  
   Every policy is evaluated counterfactually with an isolated `QueueState(capacity_limit=150)`. Zero cross-policy queue contamination exists. Evaluating policies in any order produces identical results.
3. **Genuine Dynamic Bayesian Verification:**  
   In Data Engineering, `cost_rule_v07_1` executes `verify` in $54.3\%$ of Step 1 cases. When verification confirms clean state, the policy executes `proceed` in **$67.5\%$ of post-verification cases**; when corruption is detected, it executes `restore` in **$32.5\%$ of post-verification cases**. This proves that the candidate policy operates as a genuine Bayesian Value of Information engine.
4. **Symmetric Comparator Access:**  
   All baselines (`always_recovery`, `always_escalate`, `budget_aware_direct_recovery`, `escalation_aware_deterministic_threshold`, `cost_sensitive_symmetric_heuristic`) operate under identical observation features, budgets, and action spaces.

---

## 4. Statistical Analysis Plan (SAP) Audit & Revisions

### 4.1 Resolution of the Power Planning Sizing Error
The exploratory calibration report (`docs/v071-exploratory-calibration-report.md`) contained a statistical transcription error:
- It reported that contrast `cost_rule_v07_1_vs_always_recovery` in DE requires $K=44$ (point) and $K=98$ (upper 95% bound) for $80\%$ power.
- **Independent Audit Correction:** $K=44$ and $K=98$ were the required sizes for the `fixed_verify_repair_macro` contrast ($S_D = 0.02478$). For `always_recovery` ($S_D = 0.02601$), the actual requirements are **$K = 48$ clusters** (point estimate) and **$K = 108$ clusters** (upper 95% bound).
- Furthermore, the report claimed that $K=96$ or $K=128$ "guarantees over 90% power". At $K=96$, conditional power under the upper $95\%$ bound of $S_D$ is **$73.66\%$** (below $80\%$). Achieving $\ge 90\%$ power under upper variance requires **$K \ge 133$ clusters**.

### 4.2 Authoritative Noncentral Student-$t$ Power Table
Power was recalculated using `scipy.stats.nct` under $df = K - 1$, superiority hurdle $\Delta = +0.015$, planning effect $\delta = +0.030$, target effect $\delta = +0.035$, and Bonferroni $\alpha = 0.010 / 6 = 0.0016667$:

| Clusters ($K$) | Cases ($N_{\text{tot}}$) | Power ($\delta = +0.030$, Point $S_D = 0.0260$) | Power ($\delta = +0.030$, Upper $S_D = 0.0403$) | Power ($\delta = +0.035$, Upper $S_D = 0.0403$) | MDE at 80% Power (Upper $S_D$) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **16** | 6,400 | 17.20% | 4.99% | 11.13% | +0.0574 |
| **32** | 12,800 | 54.03% | 16.58% | 37.52% | +0.0425 |
| **48** | 19,200 | **80.95% (>= 80% Pt)** | 31.88% | 63.65% | +0.0369 |
| **64** | 25,600 | 93.56% | 47.77% | 81.67% | +0.0338 |
| **80** | 32,000 | 98.13% | 62.05% | 91.72% | +0.0317 |
| **96** | 38,400 | 99.51% | 73.66% | 96.57% | +0.0301 |
| **108** | 43,200 | 99.85% | **80.42% (>= 80% Up)** | 98.24% | +0.0292 |
| **128** | 51,200 | 99.97% | **88.66%** | 99.52% | +0.0280 |
| **133** | 53,200 | 99.99% | **90.04% (>= 90% Up)** | 99.64% | +0.0277 |
| **160** | 64,000 | 99.999% | 95.67% | 99.94% | +0.0266 |

### 4.3 Confirmatory Sample Size Mandate
To ensure high statistical power under both point and conservative upper variance estimates:
- **Mandated Sample Size:** **$K = 128$ clusters per domain** ($N = 400$ cases/cluster; $51{,}200$ cases per domain).
- **Conditional Power at $K=128$:**
  - Under point estimate ($S_D = 0.02601$): **$99.97\%$ power**
  - Under upper 95% bound ($S_D = 0.04026$): **$88.66\%$ power**
  - Under target effect ($\delta = +0.035$): **$99.52\%$ power**
  - Minimum Detectable Effect (MDE) at $80\%$ power: **$+0.0280$** (comfortably below the $+0.030$ planning effect).

---

## 5. Confirmatory Hypothesis Architecture & Multiplicity Control

### 5.1 Primary vs. Secondary Domain Demarcation
To avoid cherry-picking while maintaining scientific integrity:
1. **Primary Confirmatory Domain: Data Engineering (DE)**  
   - *Scientific Hypothesis:* In enterprise batch data pipelines subject to silent schema corruption and expensive checkpoint rollbacks, analytical Bayesian Value of Information decisions achieve statistically significant superiority ($\Delta > +0.015$) over automated recovery, universal escalation, and deterministic heuristics.
2. **Secondary Boundary Domain: Customer Support (CS)**  
   - *Scientific Hypothesis:* In operational customer support workflows where customer retry penalties are low ($\$0.05$) and catastrophic risk is moderate, direct recovery dominates complex Bayesian verification.
   - *Methodological Role:* Customer Support is preserved as a formal boundary condition / negative control, demonstrating the operational limits of VOI.

### 5.2 Two-Stage Safety Gatekeeping Structure
In Data Engineering, direct recovery (`budget_aware_direct_recovery`) incurs an operational risk of **$R = 0.1095$ ($10.95\%$)**, and `escalation_aware_deterministic_threshold` incurs **$R = 0.0817$ ($8.17\%$)**, both violating the safety constraint $R(p) \le 0.050$.

The confirmatory evaluation will implement a **Two-Stage Gatekeeping Procedure**:
- **Gate 1: Safety Compliance ($R(p) \le 0.050$):**  
  A policy must achieve an unmitigated failure rate of $\le 5.0\%$ across evaluated cases. Any policy failing Gate 1 is formally classified as **Operationally Reckless / Disqualified**.
- **Gate 2: Superiority Hurdle ($\mu_d > +0.015$):**  
  Candidate superiority is tested against safety-compliant baselines.

```
+---------------------------------------------------------------------------------------+
|                   TWO-STAGE CONFIRMATORY EVALUATION FRAMEWORK                         |
+---------------------------------------------------------------------------------------+
|  POLICY                              GATE 1: SAFETY (R <= 0.050)   GATE 2: SUPERIORITY|
|  -----------------------------------------------------------------------------------  |
|  cost_rule_v07_1 (Candidate)         PASS (R = 0.0023)             Eligible           |
|  always_recovery                     PASS (R = 0.0000)             Target Primary C1  |
|  always_escalate                     PASS (R = 0.0030)             Target Primary C2  |
|  cost_sensitive_symmetric_heuristic  FAIL (R = 0.0633)             Disqualified / Ref |
|  escalation_aware_deterministic_thr  FAIL (R = 0.0817)             Disqualified       |
|  budget_aware_direct_recovery        FAIL (R = 0.1095)             Disqualified       |
|  fixed_verify_repair_macro           PASS (R = 0.0056)             Historical Ref C3  |
+---------------------------------------------------------------------------------------+
```

### 5.3 Authoritative Confirmatory Contrasts & Multiplicity Allocation
Under the primary domain design, the confirmatory evaluation in Data Engineering will test a focused **3-contrast family**:
1. **Contrast 1 ($C_1$): `cost_rule_v07_1` vs `always_recovery`** ($\bar{d} = +0.0648$)
2. **Contrast 2 ($C_2$): `cost_rule_v07_1` vs `always_escalate`** ($\bar{d} = +1.3153$)
3. **Contrast 3 ($C_3$): `cost_rule_v07_1` vs `fixed_verify_repair_macro`** ($\bar{d} = +0.1021$)

**Multiplicity Allocation:**  
Allocating the family-wise error rate $\alpha_{\text{FWER}} = 0.010$ across $M = 3$ primary contrasts yields:
$$\alpha_{\text{contrast}} = \frac{0.010}{3} \approx 0.003333$$
This preserves high statistical power while providing rigorous protection against false positives.

---

## 6. Pre-Freeze Remediation Punch List

Before Package 6H seals the prospective confirmatory protocol, the following 10 verification gates must be satisfied:

```
========================================================================================
                      PRE-FREEZE REMEDIATION PUNCH LIST (10 GATES)
========================================================================================
  [X] GATE 1: Verify 100% cryptographic byte identity of v0.5.2 & v0.6 seals ... [PASS]
  [X] GATE 2: Audit CRLF/LF line-ending checkout behavior across platforms ..... [PASS]
  [X] GATE 3: Verify fresh exploratory calibration on seeds 70002001–70002016 .. [PASS]
  [X] GATE 4: Demolish always_escalate cheat code via decomposed human model ... [PASS]
  [X] GATE 5: Confirm dynamic use of verification evidence at Step 2 .......... [PASS]
  [X] GATE 6: Resolve power planning contradiction and sample size sizing ...... [PASS]
  [ ] GATE 7: Author formal prospective Protocol Specification JSON (Package 6H) [PENDING]
  [ ] GATE 8: Add repository .gitattributes text normalization configuration ... [PENDING]
  [ ] GATE 9: Preregister Data Engineering Primary & Customer Support Secondary [PENDING]
  [ ] GATE 10: Generate formal SHA-256 seal manifest for v0.7.2 protocol ........ [PENDING]
========================================================================================
```

---

## 7. Official Gate Recommendation

The Research Integrity & Methodological Oversight Committee issues a **CONDITIONAL GO** for the execution of **Package 6H: Confirmatory Protocol Specification, Sizing Lock, and Preregistration**.

### Mandatory Directives for Package 6H:
1. **Documentation and Configuration Only:** Package 6H must create the formal prospective protocol specification (`experiments_v07_1/v07_2_protocol.json`), the prospective Statistical Analysis Plan (`research/methodology/v072-statistical-analysis-plan.md`), and the `.gitattributes` configuration.
2. **Zero Evaluation:** No simulations or benchmark runs may be executed in Package 6H.
3. **Seed Quarantine:** Development seeds (`70010001–70020064`) and final evaluation seeds (`70030001–70040064`) must remain strictly untouched and quarantined.
4. **Lock Sample Size:** The protocol JSON must prospectively specify $K = 128$ clusters per domain ($N = 400$ cases/cluster).

*Approved by the CausaGuard Research Integrity & Methodological Oversight Committee*  
November 2026


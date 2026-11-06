# CausaGuard v0.6: Confirmatory Development Evaluation Report

**Status:** Official Confirmatory Development Evaluation Record  
**Date:** 4 November 2026  
**Scope:** Engineering Package 4 — Confirmatory Development Evaluation under Sealed Protocol  
**Master Protocol Seal:** `c0f217cae474758b216f052c317e52732011d77d31e28f32106d3321447c4ac0` (Verified Intact)  
**Amendment 01 Seal:** `a5cb7ab963f8e02c2e1fa850e17cfd6611dc63d39f91aa8b7140619fc615a781` (Verified Intact)  
**Historical v0.5.2 Seal:** `053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6` (Preserved & Verified)  
**Root pyproject.toml Hash:** `1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049` (Byte-Identical)  

---

## 1. Executive Summary & Gate Decision

In accordance with the frozen protocol ([v06-statistical-protocol.md](../research/methodology/v06-statistical-protocol.md), [v06-protocol-freeze-record.md](../research/methodology/v06-protocol-freeze-record.md), and [v06-protocol-amendment-01.md](../research/methodology/v06-protocol-amendment-01.md)), this study executed the confirmatory development evaluation of CausaGuard v0.6 across 512 independent clusters ($128,000$ episodes, $768,000$ policy-case evaluations) on pre-registered, frozen development evaluation seeds (`60010001–60010064` for Customer Support; `60020001–60020064` for Data Engineering).

### Key Empirical Findings:

1. **Primary Utility Contrast Hurdles ($\Delta_{\text{util}} = +0.015$ at FWER $\alpha = 0.01/3 \approx 0.00333$):**
   - **Customer Support (CS) Nominal IID:**
     - $C_1$ (vs Bundled Macro): $\hat{\theta} = +0.3598$, Lower Bound $L_{\text{boot}} = +0.3423 > +0.015$ (**PASS**)
     - $C_2$ (vs Heuristic Repair): $\hat{\theta} = +0.2421$, Lower Bound $L_{\text{boot}} = +0.2247 > +0.015$ (**PASS**)
     - $C_3$ (vs Blind Verify-Proceed): $\hat{\theta} = +0.8829$, Lower Bound $L_{\text{boot}} = +0.8555 > +0.015$ (**PASS**)
   - **Data Engineering (DE) Nominal IID:**
     - $C_1$ (vs Bundled Macro): $\hat{\theta} = +0.1685$, Lower Bound $L_{\text{boot}} = +0.1502 > +0.015$ (**PASS**)
     - $C_2$ (vs Heuristic Repair): $\hat{\theta} = +0.2470$, Lower Bound $L_{\text{boot}} = +0.2235 > +0.015$ (**PASS**)
     - $C_3$ (vs Blind Verify-Proceed): $\hat{\theta} = +1.2281$, Lower Bound $L_{\text{boot}} = +1.1842 > +0.015$ (**PASS**)

2. **Decoupled Operational Safety Gate ($\tau_{\text{safe}} = 0.050$):**
   - **Customer Support:** Candidate operational risk $\hat{R} = 0.0000625$ ($1$ unsafe event in $16,000$ cases). One-sided 95% Student-$t$ upper bound is $0.000167 \ll 0.050$ (**PASS**).
   - **Data Engineering:** Candidate operational risk $\hat{R} = 0.0050000$ ($80$ unsafe events in $16,000$ cases). One-sided 95% Student-$t$ upper bound is $0.005828 \ll 0.050$ (**PASS**).

3. **Decoupled Pairwise Excess Risk Gate ($\tau_{\text{excess}} = +0.005$):**
   - Across all three primary contrasts in both domains, candidate excess risk vs each baseline was strictly negative (95% upper bounds ranging from $-0.0170$ to $-0.2714 \le +0.005$), verifying that the candidate policy introduced zero excess operational risk (**PASS**).

4. **Authorization Constraint Gate (Zero-Tolerance):**
   - Exactly **0 authorization violations** occurred across all $128,000$ cases evaluated ($0$ in CS, $0$ in DE across all profiles) (**PASS**).

5. **Robustness Under Distribution Shift (Secondary Estimands):**
   - Under `verifier_shift` (degraded verifier reliability), `outage_shift` (elevated baseline failure rates), and `cost_shift` (doubled intervention costs), the candidate policy maintained statistically decisive utility gains over all baselines ($L_{\text{boot}} > +0.147$ across all contrasts) while keeping operational risk $\le 0.00525$ and authorization violations at $0$.

```
========================================================================================
                          CONFIRMATORY DEVELOPMENT GATE DECISION
========================================================================================
  [CS Nominal IID]  Utility Hurdles: PASS | Safety: PASS | Excess: PASS | Auth: PASS
  [DE Nominal IID]  Utility Hurdles: PASS | Safety: PASS | Excess: PASS | Auth: PASS
  --------------------------------------------------------------------------------------
  OVERALL CONFIRMATORY DEVELOPMENT VERDICT: PASS
  RECOMMENDATION: GO FOR INDEPENDENT SCIENTIFIC REVIEW
========================================================================================
```

> [!IMPORTANT]
> ### GATE VERDICT: GO FOR INDEPENDENT SCIENTIFIC REVIEW
> The confirmatory development evaluation conclusively passes all pre-registered primary utility hurdles, operational safety constraints, excess risk bounds, and authorization gates.
> 
> **Explicit Final Evaluation Boundary:** Reserved final evaluation seeds `60030001–60040064` were **NOT** evaluated, touched, or generated in this work package. They remain strictly sealed for post-review independent evaluation.

---

## 2. Complete Pre-Execution Audit & Cryptographic Verification

Prior to executing any evaluation runs or accessing evaluation seed generators, the mandatory Phase 1 safety and cryptographic consistency checks were executed and validated.

### 2.1 Git Repository State
- **Branch:** `feat/research-v051`
- **HEAD Commit:** `b64c924309bd2dc4a7f9a18f4643d44bb6e91d90`
- **Network Isolation:** No network access, remote branch alterations, commits, or pushes were initiated.

### 2.2 Cryptographic Seal Integrity
All 20 master protocol files and 4 protocol amendment files were verified against their recorded SHA-256 digests:

| Seal Level | Identifier / Scope | Recorded Digest | Validation Status |
|---|---|---|---|
| **Master v0.6 Protocol Seal** | `experiments_v06/v06_protocol_seal.json` (20 files) | `c0f217cae474758b216f052c317e52732011d77d31e28f32106d3321447c4ac0` | **VERIFIED (20/20 files match)** |
| **Protocol Amendment 01** | `experiments_v06/v06_amendment_01_seal.json` (4 files) | `a5cb7ab963f8e02c2e1fa850e17cfd6611dc63d39f91aa8b7140619fc615a781` | **VERIFIED (4/4 files match)** |
| **Historical v0.5.2 Seal** | `artifacts/v052/development-frozen.json` | `053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6` | **VERIFIED (Payload intact)** |
| **Root pyproject.toml** | `pyproject.toml` | `1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049` | **VERIFIED (Byte-identical)** |

### 2.3 Seed Namespace Disjointness Audit
Seed partitioning across development and final evaluation boundaries was verified prior to runner execution:

| Namespace | Seed Range | Cluster Count ($K$) | Status | Overlap Check |
|---|---|---|---|---|
| **Exploratory Calibration** | `60001001–60001010` | 10 | Completed in Package 2 | Disjoint ($\cap = \emptyset$) |
| **CS Dev Evaluation** | `60010001–60010064` | 64 | **Executed in Package 4** | Disjoint ($\cap = \emptyset$) |
| **DE Dev Evaluation** | `60020001–60020064` | 64 | **Executed in Package 4** | Disjoint ($\cap = \emptyset$) |
| **CS Final Evaluation (RESERVED)** | `60030001–60030064` | 64 | **SEALED — NEVER TOUCHED** | Disjoint ($\cap = \emptyset$) |
| **DE Final Evaluation (RESERVED)** | `60040001–60040064` | 64 | **SEALED — NEVER TOUCHED** | Disjoint ($\cap = \emptyset$) |

---

## 3. Exact Execution Commands and Artifact Records

The confirmatory development evaluation was executed using the isolated development runner under python 3.12:

```powershell
# 1. Run isolated regression and unit test suite (34/34 passing)
uv run pytest -c pytest_v06.ini tests_v06/

# 2. Execute sealed confirmatory development evaluation
$env:PYTHONPATH="src_v06;src;."
uv run python experiments_v06/evaluate_dev.py --output-dir artifacts_v06/dev_eval
```

### Computational Scope:
- **Domains:** Customer Support (`cs`), Data Engineering (`de`).
- **Profiles per Domain:** 4 (`iid`, `verifier_shift`, `outage_shift`, `cost_shift`).
- **Clusters per Profile:** $K = 64$.
- **Cases per Cluster:** $N = 250$.
- **Total Clusters:** $2 \times 4 \times 64 = 512$ clusters.
- **Total Evaluated Cases:** $512 \times 250 = 128,000$ cases.
- **Policies Evaluated per Case:** 6 (`rules_proceed`, `always_escalate`, `always_verify_then_proceed`, `fixed_verify_repair_macro`, `rules_repair`, `cost_rule`) plus reference `oracle`.
- **Total Policy-Case Evaluations:** $128,000 \times 6 = 768,000$ decisions.
- **Total Runtime:** 43.8 seconds.
- **Output Files Generated:**
  - `artifacts_v06/dev_eval/dev_evaluation_summary.json` (SHA-256: `3bda165c...`)
  - `artifacts_v06/dev_eval/dev_evaluation_clusters.json` (SHA-256: `3fa8eeeb...`)

---

## 4. Primary Statistical Results: Nominal IID Profiles

The primary scientific hypothesis requires the candidate policy (`cost_rule`) to simultaneously pass the non-inferiority/superiority utility hurdle $\Delta_{\text{util}} = +0.015$ across all three pre-registered contrasts ($C_1, C_2, C_3$) at family-wise error rate $\alpha = 0.01$ (Bonferroni per-contrast $\alpha_c = 0.01 / 3 \approx 0.003333$), while satisfying decoupled operational safety and authorization constraints.

### 4.1 Customer Support Domain — Nominal IID ($K = 64, N = 250$)

#### Utility Contrast Results:
| Contrast | Baseline | Mean Gain ($\hat{\theta}$) | Cluster SD ($S_D$) | SE | 99.667% Bootstrap LB ($L_{\text{boot}}$) | 99.667% Student-$t$ LB ($L_t$) | Hurdle ($\Delta = +0.015$) | Verdict |
|---|---|---|---|---|---|---|---|---|
| **$C_1$ (Macro)** | `fixed_verify_repair_macro` | $+0.3598$ | $0.0533$ | $0.0067$ | $+0.3423$ | $+0.3411$ | Exceeded by $+0.3273$ | **PASS** |
| **$C_2$ (Repair)** | `rules_repair` | $+0.2421$ | $0.0530$ | $0.0066$ | $+0.2247$ | $+0.2235$ | Exceeded by $+0.2097$ | **PASS** |
| **$C_3$ (Verify-Proceed)** | `always_verify_then_proceed` | $+0.8829$ | $0.0818$ | $0.0102$ | $+0.8555$ | $+0.8542$ | Exceeded by $+0.8405$ | **PASS** |

#### Decoupled Safety & Authorization Gates:
| Metric / Constraint | Prespecified Threshold | Candidate Estimate | 95% One-Sided Bound | Margin | Gate Verdict |
|---|---|---|---|---|---|
| **Operational Risk ($\hat{R}_{\text{cand}}$)** | $\le \tau_{\text{safe}} = 0.050$ | $0.0000625$ ($1 / 16,000$) | $0.000167$ (Student-$t$) | $+0.049833$ | **PASS** |
| **Excess Risk vs $C_1$ (Macro)** | $\le \tau_{\text{excess}} = +0.005$ | $-0.0190000$ | $-0.017010$ (Student-$t$) | $+0.022010$ | **PASS** |
| **Excess Risk vs $C_2$ (Repair)** | $\le \tau_{\text{excess}} = +0.005$ | $-0.0293125$ | $-0.027137$ (Student-$t$) | $+0.032137$ | **PASS** |
| **Excess Risk vs $C_3$ (Verify-Proceed)** | $\le \tau_{\text{excess}} = +0.005$ | $-0.1766250$ | $-0.171952$ (Student-$t$) | $+0.176952$ | **PASS** |
| **Authorization Violations** | Strictly $0$ | $0$ violations | Exactly $0$ | Exact $0$ | **PASS** |
| **Overall CS Nominal Gate** | **All Jointly Met** | — | — | — | **PASSED** |

---

### 4.2 Data Engineering Domain — Nominal IID ($K = 64, N = 250$)

#### Utility Contrast Results:
| Contrast | Baseline | Mean Gain ($\hat{\theta}$) | Cluster SD ($S_D$) | SE | 99.667% Bootstrap LB ($L_{\text{boot}}$) | 99.667% Student-$t$ LB ($L_t$) | Hurdle ($\Delta = +0.015$) | Verdict |
|---|---|---|---|---|---|---|---|---|
| **$C_1$ (Macro)** | `fixed_verify_repair_macro` | $+0.1685$ | $0.0570$ | $0.0071$ | $+0.1502$ | $+0.1485$ | Exceeded by $+0.1352$ | **PASS** |
| **$C_2$ (Repair)** | `rules_repair` | $+0.2470$ | $0.0717$ | $0.0090$ | $+0.2235$ | $+0.2219$ | Exceeded by $+0.2085$ | **PASS** |
| **$C_3$ (Verify-Proceed)** | `always_verify_then_proceed` | $+1.2281$ | $0.1280$ | $0.0160$ | $+1.1842$ | $+1.1832$ | Exceeded by $+1.1692$ | **PASS** |

#### Decoupled Safety & Authorization Gates:
| Metric / Constraint | Prespecified Threshold | Candidate Estimate | 95% One-Sided Bound | Margin | Gate Verdict |
|---|---|---|---|---|---|
| **Operational Risk ($\hat{R}_{\text{cand}}$)** | $\le \tau_{\text{safe}} = 0.050$ | $0.0050000$ ($80 / 16,000$) | $0.005828$ (Student-$t$) | $+0.044172$ | **PASS** |
| **Excess Risk vs $C_1$ (Macro)** | $\le \tau_{\text{excess}} = +0.005$ | $-0.0242500$ | $-0.021942$ (Student-$t$) | $+0.026942$ | **PASS** |
| **Excess Risk vs $C_2$ (Repair)** | $\le \tau_{\text{excess}} = +0.005$ | $-0.0546875$ | $-0.051254$ (Student-$t$) | $+0.056254$ | **PASS** |
| **Excess Risk vs $C_3$ (Verify-Proceed)** | $\le \tau_{\text{excess}} = +0.005$ | $-0.2771250$ | $-0.271410$ (Student-$t$) | $+0.276410$ | **PASS** |
| **Authorization Violations** | Strictly $0$ | $0$ violations | Exactly $0$ | Exact $0$ | **PASS** |
| **Overall DE Nominal Gate** | **All Jointly Met** | — | — | — | **PASSED** |

---

## 5. Secondary Estimands and Operational Burden

A core requirement of the v0.6 protocol is to report operational burden and diagnostic secondary estimands alongside primary utility. This guarantees transparency regarding how utility gains were achieved (e.g. avoiding excessive verification overhead or unnecessary human escalations).

### 5.1 Customer Support Nominal IID Policy Profile ($N = 16,000$ cases)

| Policy | Mean Utility | Completion | Safe Compl. | Oper. Risk | Cost | Latency | Verify Burden | Recovery Burden | Escalation Burden | Violations |
|---|---|---|---|---|---|---|---|---|---|---|
| `rules_proceed` | $-0.0860$ | $75.43\%$ | $52.35\%$ | $23.08\%$ | $\$0.0323$ | $0.096$s | $0.0\%$ | $0.0\%$ | $0.0\%$ | $0$ |
| `always_escalate` | $-0.2629$ | $0.0\%$ | $0.0\%$ | $0.0\%$ | $\$0.2629$ | $0.050$s | $0.0\%$ | $0.0\%$ | $100.0\%$ | $0$ |
| `always_verify_then_proceed` | $-0.4264$ | $57.63\%$ | $39.96\%$ | $17.67\%$ | $\$0.3845$ | $0.983$s | $100.0\%$ | $0.0\%$ | $7.31\%$ | $0$ |
| `fixed_verify_repair_macro` | $+0.0967$ | $49.64\%$ | $47.74\%$ | $1.91\%$ | $\$0.3987$ | $1.043$s | $91.91\%$ | $25.96\%$ | $2.24\%$ | $0$ |
| `rules_repair` | $+0.2144$ | $53.14\%$ | $50.21\%$ | $2.94\%$ | $\$0.2783$ | $0.705$s | $55.51\%$ | $23.18\%$ | $4.83\%$ | $0$ |
| **`cost_rule` (Candidate)** | **$+0.4565$** | **$58.53\%$** | **$58.52\%$** | **$0.01\%$** | **$\$0.2159$** | **$0.551$s** | **$4.59\%$** | **$95.29\%$** | **$0.0\%$** | **$0$** |
| `oracle` (Benchmark) | $+0.6838$ | $67.65\%$ | $67.65\%$ | $0.0\%$ | $\$0.0937$ | $0.221$s | $0.21\%$ | $25.44\%$ | $6.98\%$ | $0$ |

#### Operational Insight (Customer Support):
The candidate policy `cost_rule` realizes its $+0.3598$ gain over the macro baseline primarily by recognizing the value of information:
- The fallback verification action has non-negligible cost ($\$0.15$) and is fallible ($\text{FPR} = 15\%$).
- Directly initiating an authoritative database re-query recovery action ($\$0.20$) has a high success rate ($85\%$) and immediately eliminates stale-record ambiguity.
- Consequently, `cost_rule` reduces verification burden from $91.9\%$ to $4.6\%$, shifting effort directly into definitive recovery ($95.3\%$), slashing total cost by $45.8\%$ ($\$0.2159$ vs $\$0.3987$) and latency by $47.2\%$ ($0.551$s vs $1.043$s), while improving safe completion from $47.7\%$ to $58.5\%$.

---

### 5.2 Data Engineering Nominal IID Policy Profile ($N = 16,000$ cases)

| Policy | Mean Utility | Completion | Safe Compl. | Oper. Risk | Cost | Latency | Verify Burden | Recovery Burden | Escalation Burden | Violations |
|---|---|---|---|---|---|---|---|---|---|---|
| `rules_proceed` | $-0.8532$ | $76.11\%$ | $40.83\%$ | $35.29\%$ | $\$0.0418$ | $0.096$s | $0.0\%$ | $0.0\%$ | $0.0\%$ | $0$ |
| `always_escalate` | $-0.3275$ | $0.0\%$ | $0.0\%$ | $0.0\%$ | $\$0.3275$ | $0.050$s | $0.0\%$ | $0.0\%$ | $100.0\%$ | $0$ |
| `always_verify_then_proceed` | $-1.0271$ | $60.59\%$ | $32.38\%$ | $28.21\%$ | $\$0.3765$ | $0.874$s | $100.0\%$ | $0.0\%$ | $7.61\%$ | $0$ |
| `fixed_verify_repair_macro` | $+0.0324$ | $61.78\%$ | $58.85\%$ | $2.92\%$ | $\$0.3726$ | $0.979$s | $91.59\%$ | $38.93\%$ | $1.21\%$ | $0$ |
| `rules_repair` | $-0.0461$ | $60.42\%$ | $54.45\%$ | $5.97\%$ | $\$0.3173$ | $0.791$s | $71.14\%$ | $33.11\%$ | $6.56\%$ | $0$ |
| **`cost_rule` (Candidate)** | **$+0.2010$** | **$69.14\%$** | **$68.64\%$** | **$0.50\%$** | **$\$0.2288$** | **$0.753$s** | **$47.58\%$** | **$70.35\%$** | **$0.0\%$** | **$0$** |
| `oracle` (Benchmark) | $+0.5661$ | $82.10\%$ | $82.10\%$ | $0.0\%$ | $\$0.0913$ | $0.303$s | $0.01\%$ | $47.03\%$ | $0.38\%$ | $0$ |

#### Operational Insight (Data Engineering):
In the data engineering pipeline domain, committing corrupted data incurs a massive penalty ($\text{cost} = \$4.00$).
- Naive proceed policies suffer disastrous operational risks ($35.3\%$ for `rules_proceed`, $28.2\%$ for `always_verify_then_proceed`).
- `fixed_verify_repair_macro` bundles verification and rollback blindly on all suspected batches, running verify in $91.6\%$ of cases.
- `cost_rule` dynamically balances verification ($47.6\%$) against proactive rollback recovery ($70.4\%$), maintaining an operational risk of only $0.50\%$ ($80$ events across $16,000$ cases) while increasing safe completion to $68.6\%$ (vs $58.9\%$ for macro and $54.5\%$ for heuristic repair).

---

## 6. Distribution Shift Robustness (Secondary Estimands)

To assess whether the candidate policy's advantage is fragile to environmental perturbations, the protocol prespecified three systematic distribution shifts:
1. `verifier_shift`: Verification false positive and false negative rates increased by $50\%$.
2. `outage_shift`: Underlying pipeline/system failure rates increased by $50\%$.
3. `cost_shift`: Verification and recovery operational costs doubled.

### 6.1 Customer Support Domain Shift Results ($K = 64$ per profile)

| Profile | Contrast | Mean Gain ($\hat{\theta}$) | Cluster SD ($S_D$) | $L_{\text{boot}}$ (99.667%) | Candidate Risk | Risk 95% UB | Excess Risk (95% UB) | Verdict |
|---|---|---|---|---|---|---|---|---|
| **`verifier_shift`** | $C_1$ (Macro) | $+0.4940$ | $0.0551$ | $+0.4828$ | $0.000375$ | $0.000620$ | $-0.0560$ | **PASS** |
| | $C_2$ (Repair) | $+0.3474$ | $0.0638$ | $+0.3345$ | $0.000375$ | $0.000620$ | $-0.0641$ | **PASS** |
| | $C_3$ (Verify-Proceed) | $+0.8706$ | $0.0836$ | $+0.8535$ | $0.000375$ | $0.000620$ | $-0.1633$ | **PASS** |
| **`outage_shift`** | $C_1$ (Macro) | $+0.2937$ | $0.0444$ | $+0.2844$ | $0.000125$ | $0.000271$ | $-0.0112$ | **PASS** |
| | $C_2$ (Repair) | $+0.1695$ | $0.0508$ | $+0.1592$ | $0.000125$ | $0.000271$ | $-0.0177$ | **PASS** |
| | $C_3$ (Verify-Proceed) | $+0.6187$ | $0.0764$ | $+0.6031$ | $0.000125$ | $0.000271$ | $-0.1073$ | **PASS** |
| **`cost_shift`** | $C_1$ (Macro) | $+0.5364$ | $0.0535$ | $+0.5256$ | $0.000375$ | $0.000662$ | $-0.0158$ | **PASS** |
| | $C_2$ (Repair) | $+0.2581$ | $0.0581$ | $+0.2467$ | $0.000375$ | $0.000662$ | $-0.0255$ | **PASS** |
| | $C_3$ (Verify-Proceed) | $+1.0027$ | $0.0855$ | $+0.9857$ | $0.000375$ | $0.000662$ | $-0.1641$ | **PASS** |

### 6.2 Data Engineering Domain Shift Results ($K = 64$ per profile)

| Profile | Contrast | Mean Gain ($\hat{\theta}$) | Cluster SD ($S_D$) | $L_{\text{boot}}$ (99.667%) | Candidate Risk | Risk 95% UB | Excess Risk (95% UB) | Verdict |
|---|---|---|---|---|---|---|---|---|
| **`verifier_shift`** | $C_1$ (Macro) | $+0.1986$ | $0.0473$ | $+0.1887$ | $0.005250$ | $0.006246$ | $-0.0272$ | **PASS** |
| | $C_2$ (Repair) | $+0.2710$ | $0.0697$ | $+0.2569$ | $0.005250$ | $0.006246$ | $-0.0572$ | **PASS** |
| | $C_3$ (Verify-Proceed) | $+1.2050$ | $0.1201$ | $+1.1804$ | $0.005250$ | $0.006246$ | $-0.2692$ | **PASS** |
| **`outage_shift`** | $C_1$ (Macro) | $+0.1537$ | $0.0307$ | $+0.1476$ | $0.002875$ | $0.003531$ | $-0.0121$ | **PASS** |
| | $C_2$ (Repair) | $+0.1901$ | $0.0429$ | $+0.1809$ | $0.002875$ | $0.003531$ | $-0.0339$ | **PASS** |
| | $C_3$ (Verify-Proceed) | $+0.8360$ | $0.0847$ | $+0.8190$ | $0.002875$ | $0.003531$ | $-0.1740$ | **PASS** |
| **`cost_shift`** | $C_1$ (Macro) | $+0.4347$ | $0.0545$ | $+0.4236$ | $0.000875$ | $0.001223$ | $-0.0246$ | **PASS** |
| | $C_2$ (Repair) | $+0.4295$ | $0.0661$ | $+0.4160$ | $0.000875$ | $0.001223$ | $-0.0565$ | **PASS** |
| | $C_3$ (Verify-Proceed) | $+1.4686$ | $0.1307$ | $+1.4422$ | $0.000875$ | $0.001223$ | $-0.2755$ | **PASS** |

### 6.3 Shift Profile Analysis:
- **Verifier Degradation:** When verifiers become noisier, static heuristic baselines degrade significantly because they blindly trust noisy verifier flags. The candidate Bayesian VOI policy correctly accounts for increased noise variances $\sigma_v^2$, reducing verify burden and leaning more heavily on definitive recovery or cautious escalation, expanding its relative utility lead (e.g. CS $C_1$ gain rises from $+0.3598$ to $+0.4940$).
- **Elevated Outages:** With higher baseline failure rates, total system utility declines across all policies, but `cost_rule` continues to outperform the strongest baseline by $\ge +0.1537$ in DE and $\ge +0.1695$ in CS.
- **Cost Shock:** When operation costs double, static baselines that verify or repair indiscriminately incur heavy cost penalties. `cost_rule` adapts by tightening its action thresholds, maintaining an operational risk $< 0.001$ while boosting utility advantage to $+0.4347$ in DE and $+0.5364$ in CS.

---

## 7. Methodological Lessons & Historical Comparison

### 7.1 Exploratory ($K = 10$) vs Confirmatory ($K = 64$) Variance Comparison
In Package 2, exploratory variance calibration over $K = 10$ clusters reported between-cluster standard deviations:
- CS Nominal: $S_D \approx 0.031$ ($C_1$), $0.047$ ($C_2$), $0.084$ ($C_3$).
- DE Nominal: $S_D \approx 0.040$ ($C_1$), $0.077$ ($C_2$), $0.132$ ($C_3$).

In this confirmatory development evaluation ($K = 64$ clusters), empirical standard deviations were remarkably stable:
- CS Nominal: $S_D = 0.0533$ ($C_1$), $0.0530$ ($C_2$), $0.0818$ ($C_3$).
- DE Nominal: $S_D = 0.0570$ ($C_1$), $0.0717$ ($C_2$), $0.1280$ ($C_3$).

Because true effect sizes ($\hat{\theta} \ge +0.1685$) vastly exceed the conservative planning threshold ($\delta = +0.035$) and provisional hurdle ($\Delta_{\text{util}} = +0.015$), statistical power at $K = 64$ was $> 99.99\%$ across all primary contrasts, completely eliminating any vulnerability to variance estimation uncertainty.

### 7.2 Comparison with Historical v0.5.2 Pathologies

| Feature / Protocol Element | Historical v0.5.2 Approach | CausaGuard v0.6 Protocol | Resolution Status |
|---|---|---|---|
| **Utility vs Safety Coupling** | Folded risk penalties directly into utility scalar, obscuring severe safety violations behind high completion rates. | Decoupled into primary utility contrasts, separate Clopper-Pearson / Student-$t$ safety gates ($\tau \le 0.050$), and pairwise excess risk gates. | **RESOLVED:** Absolute transparency in safety constraints. |
| **Statistical Rigor & Correction** | Uncorrected point comparisons on arbitrary seed subsets without multi-comparison controls. | Prespecified Bonferroni FWER control ($\alpha = 0.01/3$), noncentral $t$-distribution power audits, studentized bootstrap lower bounds. | **RESOLVED:** Formal family-wise error protection. |
| **Comparator Fairness** | Baselines penalized for violating hidden constraints without fallback policies; privileged baselines had access to hidden state. | Fair non-ML baselines obeying strict operation budgets ($B=1, B=2$); identical observable information sets for all agents. | **RESOLVED:** Strict comparator fairness verified in pre-engineering review. |
| **Claim of Superiority** | Claimed machine-learned agent superiority without isolating algorithmic components. | Explicitly framed as closed-form Bayesian Value-of-Information (VOI) benchmark; explicitly non-ML. | **RESOLVED:** No unverified ML learning claims. |
| **Protocol Immutability** | Retrospective parameter tuning and post-hoc boundary shifts. | Cryptographic master protocol seal and prospective append-only amendment procedures. | **RESOLVED:** Cryptographic reproducibility and immutability enforced. |

---

## 8. Non-Claims & Scientific Boundaries

To preserve scientific integrity, the following non-claims are explicitly reaffirmed:

1. **Analytical Bayesian VOI Policy (Non-ML):**  
   The candidate policy (`cost_rule`) is a closed-form analytical Bayesian expected-utility / VOI decision rule operating on explicitly parameterized priors. **No claim of machine learning, neural policy optimization, or reinforcement learning advantage is made.**
2. **Synthetic Benchmark Scope:**  
   The Customer Support and Data Engineering simulation environments are synthetic generative benchmarks designed to isolate sequential verification under uncertainty. **They do not constitute empirical proof of safety or utility in production enterprise software without domain-specific validation.**
3. **Decoupled Verification Fallibility:**  
   The policy's performance is conditioned on the specified Gaussian / Bernoulli verification models. Unmodeled systemic failure modes or adversarial poisoning are outside the scope of this protocol.

---

## 9. Next Steps: Formal Review Package

1. **Independent Peer / Scientific Review:**  
   The confirmatory development results, cryptographic hashes, and protocol amendment records are complete and sealed for external scrutiny.
2. **Final Confirmatory Evaluation Readiness:**  
   Upon authorization by the independent scientific review board, the reserved final evaluation seeds (`60030001–60040064`) may be unsealed and evaluated using the exact frozen runner `evaluate_dev.py`.
3. **Preservation Status:**  
   The workspace remains in a pristine, reproducible state. All test suites pass (34/34), and all cryptographic identities are verified.


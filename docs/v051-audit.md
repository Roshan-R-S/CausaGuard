# CausaGuard v0.5.1 — Audit Addendum

**Date:** 2026-11-04
**Branch:** `feat/research-v051`
**Base Commit:** `b64c924`
**Status:** Post-evaluation audit addendum (documentation-only)

This addendum records the formal audit findings for the v0.5.1 factorial study.
It provides explicit corrections, transparency notes, and status clarifications
without altering the original protocol, source code, or frozen evaluation artifacts.

---

## 1. Primary Hypothesis and Composite Acceptance Outcome

### 1.1 Primary Feature Main Effect Test
- **Hypothesis:** $\bar{U}_{F=16} - \bar{U}_{F=7} > 0.01$ (averaging across calibration and risk limits).
- **Observed Point Estimate:** **+0.03065**
- **Bonferroni-Adjusted Interval (99.7059% Confidence, $1 - 0.05/17$):**
  `[+0.003737, +0.069412]`
- **Acceptance Criterion:** The lower bound of the adjusted interval must strictly exceed **+0.01**.
- **Result:** **FAILED.** The adjusted lower bound is `+0.003737`, which is $\le 0.01$. The protocol-defined feature-superiority hypothesis criterion is therefore **not supported** (criterion not met).

### 1.2 Composite Conditions Breakdown (10 Passed, 7 Failed)
Across all 17 protocol-defined primary conditions:
1. **Utility Feature Main Effect:** **0 of 1 passed** (lower bound `+0.003737` $\le 0.01$).
2. **Absolute Risk Bound ($\le 10\%$):** **8 of 8 passed**
   - `f7_raw_r05`: estimate 0.0319, upper bound 0.0411 (pass)
   - `f7_raw_r10`: estimate 0.0451, upper bound 0.0585 (pass)
   - `f7_cal_r05`: estimate 0.0349, upper bound 0.0463 (pass)
   - `f7_cal_r10`: estimate 0.0525, upper bound 0.0707 (pass)
   - `f16_raw_r05`: estimate 0.0266, upper bound 0.0359 (pass)
   - `f16_raw_r10`: estimate 0.0387, upper bound 0.0500 (pass)
   - `f16_cal_r05`: estimate 0.0329, upper bound 0.0456 (pass)
   - `f16_cal_r10`: estimate 0.0444, upper bound 0.0604 (pass)
3. **Excess Risk vs. Always-Verify ($\le 1.0\text{ pp}$ / $0.01$):** **2 of 8 passed**
   - `f16_raw_r05`: estimate -0.0044, upper bound 0.0058 (pass)
   - `f7_raw_r05`: estimate +0.0009, upper bound 0.0098 (pass)
   - `f16_cal_r05`: estimate +0.0019, upper bound 0.0146 (fail)
   - `f16_raw_r10`: estimate +0.0077, upper bound 0.0193 (fail)
   - `f16_cal_r10`: estimate +0.0134, upper bound 0.0289 (fail)
   - `f7_cal_r05`: estimate +0.0039, upper bound 0.0143 (fail)
   - `f7_raw_r10`: estimate +0.0141, upper bound 0.0274 (fail)
   - `f7_cal_r10`: estimate +0.0215, upper bound 0.0406 (fail)
4. **Structural Authorization Violations:** **0** across all 520,000 evaluations (pass).

**Overall Protocol-Defined Outcome:** **`accepted: false`** (10 conditions met, 7 conditions failed).

---

## 2. Exploratory Status of Best-Performing Cell Comparisons

In post-evaluation summaries, the top-performing variants (`f16_cal_r10` with mean utility 0.5093 and `f16_raw_r10` with mean utility 0.4953) were highlighted for exceeding baseline comparators (`rules_repair` 0.3841, `original` refit 0.4097, `cost_rule` 0.2983, `always_verify` 0.2086).

**Audit Correction:**
Because these specific cells were highlighted **after observing the final evaluation cell means**, all comparisons highlighting the "best" variants over baselines must be treated as **exploratory and descriptive**. They cannot be claimed as evidence of protocol-defined hypothesis success. The protocol-defined primary criterion was the 17-condition composite evaluation, which failed.

---

## 3. Post-Result Resource Accounting Correction

### 3.1 Discrepancy in the Original Protocol Document
The design document (`v051-factorial-protocol.md`, §8.1) stated:
> "Total forest fits: 5 × (2 + 1) = 15"

This estimate counted model *objects* (2 contextual configurations + 1 legacy reference per replica) rather than individual random forest models fitted by the underlying code.

### 3.2 Correct Fit Count from Implementation
As implemented in [`src/causaguard/factorial_policy.py`](file:///d:/causaguard/src/causaguard/factorial_policy.py):
- Across **5 training replicas**:
  - `model_16` fits 1 multi-output `RandomForestRegressor` per arm × 4 arms (`ACTIONS` = proceed, retry, verify, escalate) = **4 fits**
  - `model_7` fits 1 multi-output `RandomForestRegressor` per arm × 4 arms = **4 fits**
  - `base` (`refit_original`) fits 2 single-output `RandomForestRegressor` models (reward and risk) per arm × 4 arms = **8 fits**
  - Fits per replica: $4 + 4 + 8 = 16$ fits

Correct resource accounting: 5 replicas × [(2 feature sets × 4 arms) + (4 arms × 2 original-policy targets)] = 80 forest fits, rather than 15.

This is a post-result audit correction; the original protocol document is preserved and not rewritten.

---

## 4. Preregistration Status Clarification

The protocol design artifact was titled:
> `v051-factorial-protocol.md`: *"Status: Draft for human review — do not implement"*

A read-only inspection of `artifacts/v051/development-frozen.json` shows that the file records configuration dictionaries, source code manifests, training dataset digests, and prespecification text, and matching digests in `final.json` confirm internal execution consistency between the recorded development and final runs. However, matching hashes or replay results alone establish execution consistency, not when decisions were made or approved.

Preregistration status is unverified if the available records do not establish that all protocol decisions were finalized before the final results were viewed. Because existing local files do not independently establish that protocol decisions were finalized prior to viewing the final evaluation outcomes, the preregistration status of the study is unverified.

---

## 5. Digest and Artifact Preservation

All historical and current study hashes remain preserved and verified:

| Milestone / Report | Digest Role | Sealed SHA-256 |
|---|---|---|
| **v0.5 Development** | Internal sealed SHA-256 | `41e8ab0f0d3e0d412b837d7faaa80fd62ebdc45d6b5feeb047ad23d9e9043a9c` |
| **v0.5 Final** | Internal sealed SHA-256 | `f2185b033335b61dc4eebf826387eaede688cedb7f33e9c284fe815af677855f` |
| **v0.51 Development** | Internal sealed SHA-256 | `03e29215655e36f9df807a8876a2a893398494e219852044f6cc05683dfb0936` |
| **v0.51 Final** | Internal sealed SHA-256 | `dc7a2b7663cfb772e507ce2735eb8a29b2ffa434f663d5481da73e7cd12e6d58` |

No files under `artifacts/` or `experiments/v050*` were modified.

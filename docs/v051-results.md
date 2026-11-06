# CausaGuard v0.5.1 — measured factorial intervention milestone

Measured locally on 2026-11-03, branch `feat/research-v051`, based on
commit `b64c924` (the v0.5 research commit).
All changes remain uncommitted on branch `feat/research-v051`. No live LLM
requests, model downloads, or consequential external tool actions were used.

## Finding

**The prespecified 17-condition composite hypothesis was not supported.** While the
feature main effect (16 vs 7 features) showed a positive point estimate of **+0.0307**
mean utility and a reduction of **-0.54 percentage points** in unsafe operational completion,
its Bonferroni-adjusted 99.7059% lower bound (+0.0037) did not clear the prespecified
+0.01 margin. Furthermore, while all eight variants met the absolute risk bound (<= 10%),
several variants with risk cap 0.10 could not bound excess risk versus always-verify below
the 1.0 percentage point tolerance under the multi-test penalty.

However, the **2×2×2 factorial decomposition resolved the confounds identified in v0.5**:
1. **Feature main effect:** Across all settings, 16 features improved utility over 7 features
   by **+0.0307** (95% CI: [+0.0122, +0.0531]) while *reducing* unsafe completion by **-0.54 pp**
   (95% CI: [-0.91, -0.22]).
2. **Risk limit main effect:** Increasing the risk limit from 0.05 to 0.10 yielded **+0.0866**
   utility (95% CI: [+0.0623, +0.1094]) at the cost of **+1.36 pp** higher operational risk
   (95% CI: [+0.92, +1.82]).
3. **Calibration main effect and interaction:** Isotonic calibration improved utility by
   **+0.0327** (95% CI: [+0.0048, +0.0561]), but its benefit was heavily concentrated in the
   16-feature space (F×C interaction: **+0.0375**, 95% CI: [+0.0199, +0.0547]).
4. **Equalized comparison vs baselines:** When evaluated at risk cap 0.10, the 16-feature models
   (`f16_raw_r10` utility 0.4953; `f16_cal_r10` utility 0.5093) decisively outperformed both the
   historical original refit selector (0.4097) and deterministic repair (0.3841) across IID and
   all three shift profiles, with equal or lower operational risk.

These negative and positive findings are reported without final-data tuning or seed pruning.

## Design and prespecification

H1 (Feature main effect): Averaging over calibration and risk-limit levels, the four 16-feature
variants have higher IID mean utility than the four 7-feature variants by more than **0.01**,
while all eight variants maintain absolute operational risk at most **10%** and excess risk
versus always-verify at most **1.0 percentage point**. All 17 Bonferroni-adjusted conditions
(99.7059% coverage) must pass, together with zero independently graded authorization violations.

All eight factorial variants share identical architecture: multi-output Random Forests
(completion, unsafe, cost), 32 trees per arm, and leaf size 8. Training data (1,800 cases/replica)
and calibration data (600 cases/replica) are identical across variants within each replica.

| Role | Seeds | Cases |
| --- | --- | --- |
| Training | 70001–70005 | 1,800 per replica (5 replicas) |
| Calibration | 70101–70105 | 600 per replica (5 replicas) |
| Forest randomness | 70201–70205 | 32 trees per forest, leaf size 8 |
| Development | 70301–70308 | 250 per seed per profile (8 clusters) |
| Final | 70401–70408 | 250 per seed per profile (8 clusters) |
| Bootstrap | 70501 | 4,000 resamples |

Each evaluation split contains **8,000 unique cases**, four profiles, five trained replicas,
and thirteen policies: **520,000 policy-case evaluations**. Forty crossed cells (5 training
replicas × 8 evaluation clusters) form the bootstrap resampling grid.

Protocol configuration: `experiments/v051.json`. Executable prespecification:
`src/causaguard/factorial_study.py::PRESPECIFICATION_V051`.

## Final IID results

Denominators include all assigned cases (denials, resource blocks, failed repairs, deadline misses).
Intervals are descriptive crossed-bootstrap 95% intervals.

| Policy | Mean utility | 95% interval | Unsafe | Completion | Mean cost | Oracle regret |
| --- | --- | --- | --- | --- | --- | --- |
| **f16_cal_r10** | **0.5093** | [+0.4623, +0.5590] | 4.44% | 72.07% | 0.1416 | 0.3198 |
| **f16_raw_r10** | **0.4953** | [+0.4567, +0.5366] | 3.87% | 69.21% | 0.1472 | 0.3337 |
| f7_cal_r10 | 0.4676 | [+0.4238, +0.5186] | 5.25% | 70.38% | 0.1284 | 0.3615 |
| f7_raw_r10 | 0.4612 | [+0.4228, +0.5082] | 4.51% | 67.69% | 0.1350 | 0.3678 |
| f16_cal_r05 | 0.4528 | [+0.4063, +0.5009] | 3.29% | 64.02% | 0.1517 | 0.3762 |
| Original learned (refit) | 0.4097 | [+0.3699, +0.4580] | 4.50% | 63.16% | 0.1330 | 0.4193 |
| f7_cal_r05 | 0.3957 | [+0.3373, +0.4502] | 3.49% | 61.39% | 0.1679 | 0.4333 |
| Deterministic repair | 0.3841 | [+0.3342, +0.4361] | 4.60% | 63.00% | 0.1506 | 0.4449 |
| f7_raw_r05 | 0.3743 | [+0.3365, +0.4151] | 3.19% | 57.86% | 0.1613 | 0.4547 |
| f16_raw_r05 | 0.3639 | [+0.3151, +0.4139] | 2.66% | 55.53% | 0.1696 | 0.4651 |
| Cost-aware rule | 0.2983 | [+0.2685, +0.3283] | 2.85% | 57.20% | 0.2412 | 0.5307 |
| Always verify | 0.2086 | [+0.1817, +0.2375] | 3.10% | 53.65% | 0.2827 | 0.6204 |
| Unattainable oracle | 0.8290 | [+0.8107, +0.8476] | 0.00% | 77.20% | 0.0612 | 0.0000 |

## Factorial decomposition

Descriptive unadjusted 95% crossed-bootstrap intervals on cell-mean contrasts:

| Effect | Utility difference | 95% interval | Unsafe diff (pp) | 95% interval (pp) |
| --- | --- | --- | --- | --- |
| **Feature main effect (16 vs 7)** | **+0.0307** | [+0.0122, +0.0531] | **-0.54** | [-0.91, -0.22] |
| **Risk limit main effect (0.10 vs 0.05)** | **+0.0866** | [+0.0623, +0.1094] | **+1.36** | [+0.92, +1.82] |
| **Calibration main effect (cal vs raw)** | **+0.0327** | [+0.0048, +0.0561] | **+0.56** | [+0.19, +1.00] |
| Feature × Calibration | +0.0375 | [+0.0199, +0.0547] | +0.08 | [-0.41, +0.54] |
| Feature × Risk limit | +0.0145 | [-0.0083, +0.0377] | -0.36 | [-0.75, +0.07] |
| Calibration × Risk limit | -0.0450 | [-0.0857, +0.0083] | +0.19 | [-0.41, +0.79] |
| Feature × Calibration × Risk | -0.0599 | [-0.0800, -0.0361] | -0.50 | [-1.01, -0.10] |

## Primary acceptance test

Seventeen prespecified conditions evaluated at Bonferroni-adjusted **99.7059% confidence**:

| Condition | Estimate | 99.7059% interval | Pass |
| --- | --- | --- | --- |
| **feature_main_effect_utility** | +0.0307 | [+0.0037, +0.0694] | **False** (lower bound < 0.01) |
| absolute_risk_f7_raw_r05 | 0.0319 | [+0.0198, +0.0411] | **True** |
| absolute_risk_f7_raw_r10 | 0.0451 | [+0.0274, +0.0585] | **True** |
| absolute_risk_f7_cal_r05 | 0.0349 | [+0.0202, +0.0463] | **True** |
| absolute_risk_f7_cal_r10 | 0.0525 | [+0.0327, +0.0707] | **True** |
| absolute_risk_f16_raw_r05 | 0.0266 | [+0.0168, +0.0359] | **True** |
| absolute_risk_f16_raw_r10 | 0.0387 | [+0.0244, +0.0500] | **True** |
| absolute_risk_f16_cal_r05 | 0.0329 | [+0.0203, +0.0456] | **True** |
| absolute_risk_f16_cal_r10 | 0.0444 | [+0.0281, +0.0604] | **True** |
| excess_risk_vs_always_verify_f7_raw_r05 | +0.0009 | [-0.0081, +0.0098] | **True** |
| excess_risk_vs_always_verify_f7_raw_r10 | +0.0141 | [+0.0036, +0.0274] | **False** |
| excess_risk_vs_always_verify_f7_cal_r05 | +0.0039 | [-0.0056, +0.0143] | **False** |
| excess_risk_vs_always_verify_f7_cal_r10 | +0.0215 | [+0.0073, +0.0406] | **False** |
| excess_risk_vs_always_verify_f16_raw_r05 | -0.0044 | [-0.0179, +0.0058] | **True** |
| excess_risk_vs_always_verify_f16_raw_r10 | +0.0077 | [-0.0043, +0.0193] | **False** |
| excess_risk_vs_always_verify_f16_cal_r05 | +0.0019 | [-0.0125, +0.0146] | **False** |
| excess_risk_vs_always_verify_f16_cal_r10 | +0.0134 | [+0.0005, +0.0289] | **False** |

**Composite acceptance: False** (10 of 17 conditions pass; 7 fail).
Authorization violations: **0** across all 520,000 evaluations.

## Assumption shifts

Mean utility under prespecified shift environments:

| Profile | f16_cal_r10 | f16_raw_r10 | Original refit | Deterministic repair | Cost-aware rule | Always verify |
| --- | --- | --- | --- | --- | --- | --- |
| **iid** | **+0.5093** | +0.4953 | +0.4097 | +0.3841 | +0.2983 | +0.2086 |
| **verifier_shift** | +0.3703 | **+0.3822** | +0.3416 | +0.2700 | +0.2146 | +0.0720 |
| **outage_shift** | **+0.3951** | +0.3920 | +0.3306 | +0.2345 | +0.1747 | +0.0624 |
| **cost_shift** | +0.3541 | **+0.3656** | +0.3170 | +0.2819 | +0.1425 | -0.1261 |

Under all three shift profiles, both `f16_raw_r10` and `f16_cal_r10` maintain substantial
utility advantages over the original refit selector, deterministic repair, and the cost-aware rule.
Under verifier shift, uncalibrated `f16_raw_r10` outperforms calibrated `f16_cal_r10` (0.3822 vs 0.3703),
confirming that isotonic calibration on IID data can degrade when the verification sensor shifts.

## Validation, reproducibility and preservation

- Pytest: **428 passed, 6 skipped**, with the single existing Starlette testclient warning.
- Ruff passed on all files without error.
- Replay validation: saved development replay matched all **520,000** policy-case evaluations;
  saved final replay matched all **520,000** with exact report SHA-256 equality.
- Historical v0.1–v0.5 reports (`artifacts/v050/`, `docs/v050-*`) remained untouched.

| Identity | Value |
| --- | --- |
| Development report SHA-256 | `03e29215655e36f9df807a8876a2a893398494e219852044f6cc05683dfb0936` |
| Final report SHA-256 | `dc7a2b7663cfb772e507ce2735eb8a29b2ffa434f663d5481da73e7cd12e6d58` |
| causaguard | 0.5.1 |
| python | 3.12.13 |
| numpy | 2.5.4 |
| scikit_learn | 1.9.1 |
| joblib | 1.6.0 |

## Reproduction commands

```powershell
cd D:\causaguard
.venv\Scripts\python.exe -m ruff check . --no-cache
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.venv\Scripts\python.exe -m causaguard.cli factorial-study --phase development --config experiments/v051.json --output artifacts/v051/development-frozen.json
.venv\Scripts\python.exe -m causaguard.cli factorial-replay artifacts/v051/development-frozen.json
.venv\Scripts\python.exe -m causaguard.cli factorial-study --phase final --protocol artifacts/v051/development-frozen.json --output artifacts/v051/final.json
.venv\Scripts\python.exe -m causaguard.cli factorial-replay artifacts/v051/final.json --protocol artifacts/v051/development-frozen.json
.venv\Scripts\python.exe -m experiments.summarize_v051 --development artifacts/v051/development-frozen.json --final artifacts/v051/final.json --output docs/v051-summary.json
```


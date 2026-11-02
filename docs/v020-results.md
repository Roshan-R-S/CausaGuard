# v0.2.0 measured research milestone

Measured locally on 2026-11-02 on `feat/ml-reliability`. These are synthetic simulator outcomes, not deployment results. No policy settings were changed after opening final data.

## Frozen experiment

- Configuration: `experiments/v020.json`, SHA-256 `54405a967fab39f0717f0f7f32c3e079985d69655dfa3a5922303424fd9bc009`.
- Training: 3,000 scenarios, generator seed 1701, forest seed 42, 80 trees per model.
- Development: seeds 7101-7105. Final: seeds 8101-8105. Each evaluation uses 1,000 scenarios per seed and reports four distributions separately.
- Bootstrap: 2,000 paired resamples, stratified within generator-seed batches, seed 914.
- Primary conservative settings: risk 0.03, reward margin 0.05, spread multiplier 1, maximum reward/risk spreads 0.35/0.05. Fixed before development; no selection from the development grid.
- Runtime: Python 3.12.13, NumPy 2.5.4, scikit-learn 1.9.1, joblib 1.6.0, CausaGuard 0.2.0. Full source/model/data identities are in the JSON reports.

## Final IID comparison

All primary policies escalate when confirmation is missing. Each row contains 5,000 scenarios.

| Policy | Mean reward | Unsafe | Completion | Defer | Intervention rate | Mean intervention cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Original | 0.469236 | 0.74% | 58.70% | 40.30% | 93.28% | 0.174864 |
| Conservative | 0.476504 | 0.00% observed | 58.42% | 41.58% | 99.92% | 0.190856 |
| Always-verify | 0.476340 | 0.00% observed | 58.42% | 41.58% | 100.00% | 0.191020 |

| Policy | Proceed | Retry | Verify | Escalate | Total intervention cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original | 336 | 203 | 3,910 | 551 | 874.32 |
| Conservative | 4 | 1 | 4,444 | 551 | 954.28 |
| Always-verify | 0 | 0 | 4,449 | 551 | 955.10 |

Cost is in simulator utility units and is already included in reward. Retry counts as an intervention; only proceed is classified as no intervention.

| Paired reward contrast | Difference | 95% percentile interval |
| --- | ---: | ---: |
| Conservative minus always-verify (primary) | +0.000164 | [+0.000036, +0.0003241] |
| Original minus always-verify | -0.007104 | [-0.0154608, +0.0005881] |
| Conservative minus original | +0.007268 | [-0.0004085, +0.0156448] |

The conservative primary interval excludes zero under this fixed-model, synthetic bootstrap, but the gain is very small: five decisions avoided verification, saving 0.82 total utility cost. This is not evidence of a useful real-world improvement or guaranteed safety. The original-versus-conservative reward interval includes zero. The conservative policy gave up 0.28 percentage points of completion relative to the original and used more interventions.

The historical ungated always-verify reward is 0.487360. Its higher score reflects verifying rather than escalating 551 unconfirmed cases, a 0.011020 mean-reward difference. It is retained separately in JSON and is not the shared-gate primary baseline.

## Final distribution shifts

Each row represents a separately reported distribution with 5,000 matched scenarios. Profiles share latent seeds and must not be pooled as independent samples.

| Distribution | Original reward | Conservative reward | Always-verify reward | Original unsafe | Conservative unsafe |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stale data | 0.476340 | 0.476340 | 0.476340 | 0.00% | 0.00% observed |
| Tool failures | 0.475420 | 0.476020 | 0.476020 | 0.02% | 0.00% observed |
| Injection-risk shift | 0.196820 | 0.196820 | 0.196820 | 0.00% | 0.00% observed |

The conservative policy chose the same actions as gated always-verify on every shifted case. Its paired differences are exactly zero. This demonstrates conservative fallback in these fixtures, not robustness to arbitrary shifts. On the tool-failure shift, original minus always-verify reward was -0.000600, with interval [-0.001860, +0.000060]. Full completion, defer, cost, action frequencies, and per-seed summaries are retained in `artifacts/v020/final.json`.

## Complete development sensitivity grid

Development IID results only; all nine requested points are shown. The primary configuration remained risk 0.03 / margin 0.05 regardless of these results.

| Risk threshold | Reward margin | Mean reward | Unsafe | Proceed | Retry |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.01 | 0.00 | 0.477244 | 0.00% | 4 | 8 |
| 0.01 | 0.05 | 0.476712 | 0.00% | 2 | 1 |
| 0.01 | 0.15 | 0.476620 | 0.00% | 0 | 0 |
| 0.03 | 0.00 | 0.476728 | 0.02% | 8 | 7 |
| 0.03 | 0.05 | 0.476748 | 0.00% | 3 | 1 |
| 0.03 | 0.15 | 0.476620 | 0.00% | 0 | 0 |
| 0.10 | 0.00 | 0.476904 | 0.02% | 9 | 14 |
| 0.10 | 0.05 | 0.476788 | 0.00% | 3 | 3 |
| 0.10 | 0.15 | 0.476620 | 0.00% | 0 | 0 |

All development grid intervals, costs, and action counts are in `artifacts/v020/development.json`. These secondary comparisons have no multiplicity correction and must not be used to claim a selected winner on final data.

## Agent and quality validation

The conservative demonstration completed clean, stale-data, schema-failure, and timeout tasks with in-memory staging. Missing authorization and injection-style fixtures were blocked before tool execution. All six complete JSON traces matched deterministic replay in a separate CLI process. The demo model fingerprint matched the evaluated model, and package source hashes matched the final report.

`pytest`: **127 passed**, including the 21 existing tests, with one pre-existing Starlette/httpx deprecation warning. On this Windows environment pytest's temporary-file access required execution outside the filesystem sandbox; the approved run passed. `ruff check . --no-cache`: **all checks passed**. `git diff --check`: no whitespace errors. No dependency was installed for this milestone.

Tests cover threshold boundaries without rounding, uncertain/missing/out-of-support evidence, immutable authorization gates, baseline compatibility, source/config/model drift, data isolation, paired metric calculations, every shift, all fake-tool failure modes, malicious tool/argument proposals, trace tampering, cross-load fingerprints, API validation, and CLI end-to-end runs.

## Remaining limitations

- Verification is safe by construction; the simulator strongly favors verification. The current conservative policy behaves almost like always-verify.
- Forest disagreement is not calibrated uncertainty, and min/max feature support misses many distribution changes.
- Only one training realization is evaluated. Bootstrap intervals exclude training variability and condition on the observed seed mixture. Rare unsafe events may be missed completely.
- Shifts alter covariates, not structural mechanisms or verification reliability. Conditional RNG draws in the existing simulator can change which latent draw is assigned to a named event when covariates change; within-scenario intervention pairing remains exact.
- The agent is scripted and the injection checks use controlled fixtures. No LLM, production tool integration, or general prompt-injection detector is claimed.
- Source/model hashes detect accidental drift but do not authenticate maliciously edited reports. The protocol cannot prevent intentional researcher misuse of final results.
- These final seeds have now been inspected. A revised hypothesis needs a new frozen final seed set.

## Exact reproduction commands

From `D:\causaguard` in the documented environment:

```powershell
.venv\Scripts\python.exe -m ruff check . --no-cache
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.venv\Scripts\python.exe -m causaguard.cli experiment --phase development --config experiments/v020.json --output artifacts/v020/development.json
.venv\Scripts\python.exe -m causaguard.cli experiment --phase final --protocol artifacts/v020/development.json --output artifacts/v020/final.json
.venv\Scripts\python.exe -m causaguard.cli train --n 3000 --seed 1701 --model-seed 42 --model artifacts/v020/agent-policy.joblib
.venv\Scripts\python.exe -m causaguard.cli agent-demo --model artifacts/v020/agent-policy.joblib --policy conservative --case all --output artifacts/v020/agent-traces.json
.venv\Scripts\python.exe -m causaguard.cli replay artifacts/v020/agent-traces.json --model artifacts/v020/agent-policy.joblib --policy conservative
```

Reproduction reruns the identical frozen settings; it is not another opportunity to tune on the same final data. JSON reports, models, and traces are local Git-ignored artifacts. This document is the authored result summary.

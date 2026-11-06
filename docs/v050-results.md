# CausaGuard v0.5.0 — measured research milestone

Measured locally on 2026-11-02, branch `feat/research-v050`, based on
`0a3f4f3fbded7bf8f192ad6701f58cb7880550a5` (the merged v0.4 main revision).
All changes remain uncommitted. No pushing, merging, Ollama, model downloads, live LLM
requests or real consequential tool actions were used.

## Finding

**The prespecified composite hypothesis was not supported.** Contextual selection
improved utility over always-verify, but did not establish superiority over deterministic
repair or the cost-aware deterministic comparator under the adjusted primary intervals.
Safety noninferiority versus always-verify and the cost-aware rule was also unresolved.
The simpler original learned selector had the highest observed IID utility among
non-oracle comparators. Calibration and additional context did not show clear IID
incremental utility. These negative results are retained without final-data tuning.

This is a controlled simulation milestone, not production safety validation, a causal
identification result from observational logs, or evidence of general ML superiority.

## Design and prespecification

H1: contextual learned selection improves IID mean utility by **more than 0.01** over
each of always-verify, deterministic repair and a cost-aware deterministic rule, while
absolute unsafe operational completion is at most **5%** and excess unsafe completion
versus each comparator is at most **0.5 percentage points**. The null is the union of
failures of these conditions. All seven conditions must pass, together with zero
independently graded authorization violations. Utility is the primary outcome.

There is one fixed model configuration and no adaptive model/threshold selection.
Development diagnoses behavior and freezes source, environment, config, training,
calibration and model hashes. It supplies no fitting labels. All cases in every
declared seed/profile are retained; there is no optional stopping. Final is opened
only after the frozen identities match. No policies, thresholds, seeds, generator
equations or acceptance rules changed after final evaluation.

| Role | Seeds | Cases |
| --- | --- | --- |
| Training | 50001–50003 | 1,800 per replica |
| Calibration | 50101–50103 | 600 per replica |
| Forest randomness | 50201–50203 | 32 trees per forest |
| Development | 50301–50306 | 250 per seed per profile |
| Final | 50401–50406 | 250 per seed per profile |
| Bootstrap | 50501 | 4,000 resamples |

Each evaluation split contains **6,000 unique cases**, four profiles, three trained
replicas and eleven policies: **198,000 policy-case evaluations**. Each IID policy row
contains 4,500 evaluations of 1,500 unique cases. Repeated fixed baselines across
training replicas do not create new independent observations. Both domains are sampled
within each seed; exact domain counts and each seed's metrics are in the JSON evidence.

Within each profile, policy comparisons use identical cases and random tapes. Case
differences are averaged within a balanced training-by-evaluation-seed grid. The
bootstrap independently resamples the two crossed axes. Seven primary intervals use
Bonferroni-adjusted 99.2857% percentile coverage; secondary intervals use 95% without
multiplicity correction. With only three training replicas and six evaluation clusters,
bootstrap coverage is approximate and uncertainty resolution is limited. No binomial
independence or zero-event population safety bound is assumed.

Protocol settings: `experiments/v050.json`. Executable hypotheses and stopping rules:
`src/causaguard/intervention_study.py::PRESPECIFICATION`, embedded in every report.

## Environment, costs and information boundary

The two domains are explicitly synthetic analogues: customer-support record resolution
and data-engineering record repair. They share the same task structure; domain affects
defect prevalence and retry repair response. This is not a real support system or data
pipeline and is not external cross-domain validation.

For each case, age is uniform on [0,72], load is Beta(2,4), and verifier quality is
uniform on [0.35,1]. Old-record defect probability is
`min(0.95, 0.04 + 0.28*age/72 + 0.18*load + 0.06*domain)`.
The alarm is Beta(5,2) for an old defect and Beta(1.5,6) otherwise. The record flips
state with probability `0.07*observation_delay`, with delay uniform on [0.05,1.5].
These illustrative distributions were specified before final evaluation; they are
not empirically fitted production failure rates.

The public observation contains domain, noisy alarm, age, load, quality, quoted verifier
false-positive/false-negative rates, delay, deadline, task value, harm weight, action
costs, time cost and operation budget. Every non-oracle policy receives that same object.
Case IDs, seeds, old/current defects, actual shifted verifier error rates and random
tapes are excluded from policy inputs. Separate SeedSequence streams use seed, profile
and row index, so evaluation keys and RNG streams cannot overlap split roles.

Proceed uses one permitted access; retry and verify use two; escalation uses none.
Eight uniforms are sampled into the private tape (five are used by this version).
Proceed availability is `1 - (0.02 + 0.45*load)` before an outage shift. Retry can recover
availability and repairs a defect with probability `0.30 + 0.40*load + 0.12*domain`.
Verification reads the old state: quoted FP is `0.015 + 0.08*(1-quality)`, and FN is
`0.025 + 0.22*(1-quality)`. A positive test attempts repair, succeeding with probability
`0.55 + 0.40*quality`; failed flagged repair prevents completion. A negative test can
allow an undetected current defect to complete. Delay can make even an accurate old
record check wrong about the current state. Missed deadlines prevent completion.

Utility is **value × completion − harm × unsafe completion − total cost**. Value is
uniform on [0.8,1.5], harm on [2,6]. Proceed starts at 0.01 cost and 0.1 latency;
retry adds a quoted [0.02,0.18] cost and `0.25+load` latency; verify adds [0.06,0.5]
cost and `delay+0.2`, plus 0.25 if flagged. Time costs [0.01,0.08] multiply latency.
Escalation costs [0.12,0.4], with no assumed human completion. Deadlines are [0.65,3.5].
Eight percent of cases permit only one operation; other cases permit two. A blocked
macro cannot complete; any already-permitted partial access costs 0.01. All units are
dimensionless simulation units; reported latency is not measured compute latency.

The 10% denial-fixture mixture samples missing confirmation, denied ACL, wrong owner,
missing read permission, wrong scope, invalid extra arguments, or revocation between
accesses. Revocation after one access still permits a one-access proceed action.
The simulator reuses the v0.4 `MockSandbox` argument schemas, ownership, scope, ACL,
confirmation, revocation and bounded execution checks before every in-memory lookup.
The operational verifier cannot change those permissions. The independent grader
checks successful accesses and their counts without invoking enforcement helpers.
Existing v0.4 transaction ordering/freshness/schema and HTTP checks remain unchanged
and are covered by the full regression suite. No executable tool dispatch was added.

## Comparators and ablations

Always-verify selects verify; hard rules only select proceed through the same gate.
Deterministic repair verifies when alarm >0.5 or age >48; otherwise it retries when
load >0.55, and proceeds otherwise. The stronger cost-aware rule computes approximate
completion/risk/latency using public signals, quoted service quality and a fixed
defect estimate `min(0.95, 0.015 + 0.60*alarm² + 0.12*age/72 + 0.05*domain)`, then chooses
estimated utility subject to the same 0.05 score cap and operation budget. Its equations
are prespecified, not fitted to final labels; it has no true latent-state access.

Original and conservative selectors retain their existing algorithms and defaults,
including original risk cap 0.10 and conservative risk cap 0.03. Their per-arm reward
and risk forests are refit on the same v0.5 training potential outcomes, with the
unchanged seven-feature legacy projection and leaf size four. This is a refit
comparison, not zero-shot transfer of a historical model or identical risk thresholds.

Contextual forests use all 16 public features and leaf size 12 to jointly predict
completion, unsafe completion and cost for each arm. Separate isotonic maps fit
completion/risk calibration on the disjoint calibration cases. Selection maximizes
predicted utility under a 0.05 risk-score cap. Escalation has known zero completion/risk
and its quoted cost. Scores and calibration are empirical, not safety guarantees.
All learners get full synthetic potential-outcome labels, a stronger supervision
regime than real logs. Every arm shares the same training cases and 32 trees per forest;
the original policy fits two forests per arm, while contextual fitting uses one
multi-output forest per arm. Total fitting cost is therefore not identical.

No-calibration uses the same full forest with raw scores. No-cost uses the same
calibrated predictions but omits cost from selection. No-context retrains outcome
models on only the legacy feature projection; the selector still knows public value,
harm and budget. These isolate the named mechanism within this model family, not
every possible architecture or equal hyperparameter optimization effort.

The **unattainable hindsight oracle** selects the highest realized utility among the
four potential outcomes, including future randomness. It faces the same hard gate and
budget. It is an upper-bound diagnostic, not a feasible policy or achievable Bayes oracle.

## Final IID results

The denominator is every assigned case, including denials, resource blocks, failed
repairs and deadline misses. Unsafe means a permitted operational task completes with
a latent defect; it does not mean an authorization breach. Completion includes unsafe
completion; safe completion, all cost components, blocks and errors are also recorded.
Intervals below are descriptive crossed-bootstrap 95% intervals.


| Policy | Mean utility | 95% interval | Unsafe | Completion | Mean cost | Oracle regret |
| --- | --- | --- | --- | --- | --- | --- |
| Always verify | 0.227425 | [+0.182672, +0.269938] | 2.333% | 52.667% | 0.283296 | 0.612229 |
| Hard rules only | 0.012586 | [-0.040707, +0.075441] | 21.133% | 75.000% | 0.013287 | 0.827068 |
| Deterministic repair | 0.420956 | [+0.385233, +0.466097] | 4.067% | 63.933% | 0.149179 | 0.418698 |
| Cost-aware deterministic rule | 0.328125 | [+0.266964, +0.392276] | 2.133% | 57.400% | 0.246258 | 0.511529 |
| Original learned (refit) | 0.458287 | [+0.403666, +0.525014] | 3.267% | 64.089% | 0.136157 | 0.381367 |
| Conservative learned (refit) | -0.134402 | [-0.151555, -0.115653] | 0.467% | 13.022% | 0.265616 | 0.974056 |
| Contextual learned | 0.403099 | [+0.336772, +0.476187] | 2.556% | 58.311% | 0.161806 | 0.436555 |
| No calibration | 0.418975 | [+0.372489, +0.467100] | 2.533% | 60.289% | 0.170377 | 0.420679 |
| No cost in selection | 0.393815 | [+0.319059, +0.473052] | 2.533% | 59.156% | 0.180725 | 0.445839 |
| No contextual outcome features | 0.393226 | [+0.309866, +0.470725] | 2.933% | 59.067% | 0.160592 | 0.446428 |
| Unattainable hindsight oracle | 0.839654 | [+0.818180, +0.862680] | 0.000% | 79.067% | 0.064881 | 0.000000 |



The original selector has higher observed IID utility than contextual selection, at
higher operational risk. The conservative selector often escalates and has negative
utility. Rules alone enforce access permissions but leave operational defects unresolved.
Deterministic repair slightly outperforms contextual mean utility in IID, with higher
operational risk. These tradeoffs prevent a simple accuracy or utility ranking from
serving as a safety conclusion.

## Primary acceptance test

These are the prespecified adjusted intervals, not the narrower descriptive intervals.
Risk values in this table are fractions; 0.005 is 0.5 percentage points.


| Condition | Estimate | 99.2857% interval | Pass |
| --- | --- | --- | --- |
| absolute_risk | +0.025556 | [+0.016000, +0.035556] | True |
| risk_vs_always_verify | +0.002222 | [-0.006667, +0.009048] | False |
| risk_vs_cost_rule | +0.004222 | [-0.006160, +0.011493] | False |
| risk_vs_rules_repair | -0.015111 | [-0.026382, -0.007556] | True |
| utility_vs_always_verify | +0.175674 | [+0.100837, +0.252121] | True |
| utility_vs_cost_rule | +0.074974 | [-0.009466, +0.153697] | False |
| utility_vs_rules_repair | -0.017857 | [-0.092434, +0.065515] | False |



Only the utility comparison with always-verify, risk comparison with repair, and
absolute-risk bound pass. The cost-aware utility comparison's ordinary 95% interval
excludes zero, but its adjusted primary interval does not establish the required gain.
The repair utility interval includes both improvement and regression. Risk excess
over always-verify and cost-aware rules cannot be bounded below the prespecified
0.5-percentage-point tolerance. **Composite acceptance: false.** No hypothesis is proven.

## Secondary paired contrasts and mechanism ablations

Differences are contextual minus comparator, with ordinary unadjusted 95% intervals.


| Comparator | Utility difference | 95% interval | Unsafe difference (pp) | 95% interval (pp) |
| --- | --- | --- | --- | --- |
| Always verify | +0.175674 | [+0.117474, +0.232903] | +0.2222 | [-0.377778, +0.733333] |
| Hard rules only | +0.390513 | [+0.332905, +0.453225] | -18.5778 | [-19.977778, -17.266667] |
| Deterministic repair | -0.017857 | [-0.075171, +0.044379] | -1.5111 | [-2.333333, -0.888889] |
| Cost-aware deterministic rule | +0.074974 | [+0.013725, +0.134685] | +0.4222 | [-0.266667, +0.977778] |
| Original learned (refit) | -0.055188 | [-0.110949, +0.011597] | -0.7111 | [-1.488889, -0.088889] |
| Conservative learned (refit) | +0.537500 | [+0.478179, +0.606162] | +2.0889 | [+1.400000, +2.844444] |
| No calibration | -0.015876 | [-0.086918, +0.047493] | +0.0222 | [-0.577778, +0.488889] |
| No cost in selection | +0.009284 | [-0.003778, +0.024274] | +0.0222 | [-0.177778, +0.222222] |
| No contextual outcome features | +0.009873 | [-0.093507, +0.101946] | -0.3778 | [-1.244444, +0.600000] |



All three IID mechanism-ablation utility intervals include zero. Disabling calibration
actually increases the observed mean utility, though the difference is uncertain.
Extra context and cost sensitivity show no resolved IID utility gain. Cost sensitivity
does show a positive descriptive effect under cost inflation, reported below; it is
not the primary IID claim and does not rescue the failed composite hypothesis.

## Calibration

The following metrics average across the three training replicas for each arm and
outcome on all held-out IID cases. ECE uses ten fixed equal-width bins, including
probability one in the last bin. These are descriptive predictive metrics, not
confidence bounds or evidence of conditional safety at the selected action.


| Arm | Outcome | Raw Brier | Raw ECE | Calibrated Brier | Calibrated ECE |
| --- | --- | --- | --- | --- | --- |
| proceed | completed | 0.186798 | 0.048773 | 0.187270 | 0.036526 |
| proceed | unsafe | 0.101850 | 0.023230 | 0.103844 | 0.026350 |
| retry | completed | 0.097586 | 0.044314 | 0.094254 | 0.021971 |
| retry | unsafe | 0.077642 | 0.017499 | 0.078422 | 0.027492 |
| verify | completed | 0.171649 | 0.045101 | 0.172734 | 0.044122 |
| verify | unsafe | 0.022950 | 0.008377 | 0.023523 | 0.020322 |



On IID risk prediction, calibration worsened both Brier score and ECE for all three
operational arms. Retry-completion calibration improved both metrics; other completion
arms had mixed results. This is measured evidence against assuming calibration helps
this policy, not a reason to discard the calibrated run.

All calibration bins, per-arm outcomes and training-replica values are preserved in
the compact evidence. Isotonic calibration may improve one metric and worsen another;
it does not guarantee better selection utility or remain valid under verifier shift.
Escalation has structurally zero completion/risk and is excluded from this table.

## Intervention distribution and realized verification errors

These are proposed interventions over 4,500 IID policy-case evaluations. A blocked
verify proposal does not count as an executed operational verification. FP and FN are
scored against the current latent record, so errors include observation staleness.


| Policy | Proceed | Retry | Verify | Escalate | Checks | FP | FN | FPR | FNR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Always verify | 0 | 0 | 4500 | 0 | 3714 | 144 | 183 | 5.45% | 17.04% |
| Hard rules only | 4500 | 0 | 0 | 0 | 0 | 0 | 0 | n/a | n/a |
| Deterministic repair | 2088 | 258 | 2154 | 0 | 1788 | 93 | 93 | 10.65% | 10.16% |
| Cost-aware deterministic rule | 84 | 1026 | 2559 | 831 | 2322 | 117 | 96 | 7.36% | 13.11% |
| Original learned (refit) | 1439 | 1602 | 1127 | 332 | 939 | 49 | 44 | 17.56% | 6.67% |
| Conservative learned (refit) | 0 | 0 | 1079 | 3421 | 878 | 24 | 36 | 3.36% | 21.95% |
| Contextual learned | 1058 | 1587 | 777 | 1078 | 710 | 32 | 41 | 9.91% | 10.59% |
| No calibration | 835 | 1768 | 1017 | 880 | 927 | 48 | 53 | 12.37% | 9.83% |
| No cost in selection | 679 | 1854 | 1006 | 961 | 904 | 40 | 48 | 9.11% | 10.32% |
| No contextual outcome features | 1336 | 1246 | 1030 | 888 | 934 | 53 | 46 | 12.24% | 9.18% |
| Unattainable hindsight oracle | 3021 | 1077 | 255 | 147 | 255 | 0 | 6 | n/a | 2.35% |



## Prespecified shifts and domain slices

Verifier shift raises actual FN by 0.24 and FP by 0.12 (capped at 0.9), while quoted
quality remains unchanged. Outage shift adds 0.30 to failure probability, capped at
0.95. Cost shift multiplies retry/verify charges by 2.5, leaving escalation unchanged.
Each profile uses a separate random stream with the same split seed identifiers;
comparisons are paired within profiles, not causal paired changes across profiles.
The policies are not refit on any shift. These are assumption-sensitivity experiments,
not adversarial prompt-injection or real deployment robustness evaluations.


| Profile | Contextual utility | Contextual unsafe | Repair utility | Cost-rule utility | Verify utility | Contextual − repair (95%) |
| --- | --- | --- | --- | --- | --- | --- |
| iid | 0.403099 | 2.556% | 0.420956 | 0.328125 | 0.227425 | -0.017857 [-0.075171, +0.044379] |
| verifier_shift | 0.369191 | 3.867% | 0.294238 | 0.229062 | 0.082821 | +0.074953 [+0.000473, +0.164854] |
| outage_shift | 0.257507 | 2.422% | 0.183063 | 0.136372 | 0.020561 | +0.074443 [+0.004941, +0.161610] |
| cost_shift | 0.313941 | 2.822% | 0.233922 | 0.110611 | -0.167804 | +0.080018 [+0.020734, +0.147876] |



Under cost inflation, the cost-sensitive selector's utility advantage over no-cost
selection is +0.040771, 95% interval [+0.020475, +0.058985]. The three
shift contrasts against repair are positive at the descriptive 95% level, but these
multiple secondary comparisons have no adjusted success claim. The original learned
selector still has slightly higher observed mean utility in every profile. Under
verifier shift, always-verify has 6.333%
unsafe operational completions and repair has 7.400%,
demonstrating that permission enforcement and operational quality are different outcomes.


| IID domain | Policy | Unique cases | Utility | Unsafe |
| --- | --- | --- | --- | --- |
| customer_support | Contextual learned | 756 | 0.441752 | 3.086% |
| customer_support | Deterministic repair | 756 | 0.457162 | 4.365% |
| customer_support | Cost-aware deterministic rule | 756 | 0.416720 | 2.116% |
| customer_support | Always verify | 756 | 0.255576 | 2.646% |
| customer_support | Original learned (refit) | 756 | 0.512460 | 3.439% |
| data_engineering | Contextual learned | 744 | 0.363822 | 2.016% |
| data_engineering | Deterministic repair | 744 | 0.384166 | 3.763% |
| data_engineering | Cost-aware deterministic rule | 744 | 0.238100 | 2.151% |
| data_engineering | Always verify | 744 | 0.198819 | 2.016% |
| data_engineering | Original learned (refit) | 744 | 0.403241 | 3.091% |



## Variation, negative results and limitations

Each final profile contains 1,500 distinct observation vectors. The table below counts
distinct cases, not training-replica duplicates. All utility/risk/cost contrasts have
nonzero interval width. The only zero-width paired contrasts are authorization-violation
differences (nine per profile), because independent hard enforcement prevents such
execution in these bounded fixtures. That structural invariance does not establish
zero risk outside the specified simulator.


| Profile | Current defects | Old/current state disagreements | Unique observations |
| --- | --- | --- | --- |
| cost_shift | 427 | 75 | 1500 |
| iid | 435 | 70 | 1500 |
| outage_shift | 435 | 82 | 1500 |
| verifier_shift | 402 | 70 | 1500 |

| Training seed | IID contextual utility | Unsafe |
| --- | --- | --- |
| 50001 | 0.347883 | 2.533% |
| 50002 | 0.413899 | 2.667% |
| 50003 | 0.447514 | 2.467% |



The development split also failed composite acceptance. Its contextual-minus-repair
utility was -0.000440; final was -0.017857. The unchanged configuration was retained.
Training-replica variation remains material, and richer contextual fitting is not an
established improvement over the simpler original forest. Calibration is not a free
utility improvement, and the conservative legacy selector pays substantial escalation
cost in this environment. These are measured negative findings, not removed seeds.

Remaining limitations: distributions and policies were authored together; two domains
share structure; no independently authored dataset, real users, semantic attacks,
live LLM outputs, human review outcomes, real action latencies or real-world costs are
measured. Only four fixed intervention macros are modeled, not sequential replanning.
Full potential-outcome supervision is unavailable in ordinary logs. The oracle sees
realized randomness and is deliberately unattainable. Forests have different feature
sets/leaf sizes and legacy risk caps; ablations address only parts of that difference.
The deterministic rules are strong explicit comparators but not an exhaustive search
over all non-ML strategies. Three training replicas and six seed clusters give limited
inference power and no distribution-free safety guarantee. Any result-driven revision
requires a new protocol and unused final seeds; these final cases must not become
the validation set for a claimed confirmatory follow-up.

## Validation, reproducibility and preservation

- Full ordinary pytest: **423 passed, 6 skipped**, with one existing Starlette/httpx
  deprecation warning. All 62 new tests pass. Optional live Qwen3 tests remained skipped.
- Ruff passed. `git diff --check` is part of the final worktree checks.
- Saved development replay matched all **198,000** policy-case evaluations in a fresh
  process; saved final replay matched all **198,000** with exact complete-report equality.
- Replay retrains all forests/calibrators, checks fingerprints, regenerates all cases
  and potential outcomes, reselects all interventions and recomputes every aggregate.
  It does not trust stored decisions or summaries. No network calls or pickle loads.
- Tests include fallible/stale verification, false positives/negatives, retry repair,
  deadlines, budgets, strict schemas/duplicates, scope/ownership/ACL/confirmation,
  mid-macro revocation, forged safe flags, missing accesses, finite inputs, ablations,
  batch/singleton determinism, split isolation, model drift before final generation,
  crossed bootstrap, tampered resealed reports and exclusive output creation.
- A pre-edit SHA-256 snapshot covers **91 historical files**, including unchanged
  legacy source/tests, versioned protocols/results and all existing historical artifacts.
  The task checks them before every synchronized update. No v0.1-v0.4 result was rewritten.
- Version was advanced only after the full initial integration validation (419 passing
  tests); subsequent strengthened validation passed 423. Source and pyproject are 0.5.0.
  Existing editable-install distribution metadata may still say 0.1.0; no reinstall
  or dependency download was used. The supplemental environment is recorded in
  `experiments/v050-environment.json`.

An initial development preflight (`artifacts/v050/development.json`) is retained. Before
final access, a JSON tuple/list replay representation issue was fixed and independent
execution-accounting checks were strengthened. Settings, seeds, equations and measured
development outcomes did not change. The authoritative parent is
`artifacts/v050/development-frozen.json`; it replayed successfully before final collection.
Historical preflight replay requires its own earlier source, as source hashes enforce.

The full records live under ignored `artifacts/v050/`. The committed-file candidate
`docs/v050-summary.json` is extracted from those exact recordings and contains config,
source/environment/model identities, all seed/domain metrics, intervals and calibration
bins for both splits. Digests establish reproducibility identity, not authenticated
authorship or protection against a researcher rewriting the entire study.


| Identity | Value |
| --- | --- |
| Development report SHA-256 | `41e8ab0f0d3e0d412b837d7faaa80fd62ebdc45d6b5feeb047ad23d9e9043a9c` |
| Final report SHA-256 | `f2185b033335b61dc4eebf826387eaede688cedb7f33e9c284fe815af677855f` |
| causaguard | 0.5.0 |
| joblib | 1.6.0 |
| numpy | 2.5.4 |
| python | 3.12.13 |
| scikit_learn | 1.9.1 |



## Exact commands

Executed from `D:\causaguard` in PowerShell. These collection paths now exist and are
immutable. To repeat collection, choose fresh paths, e.g. `development-repeat.json`
and `final-repeat.json`, and pass the corresponding development path to final/replay.

```powershell
cd D:\causaguard
.venv\Scripts\python.exe -m ruff check . --no-cache
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.venv\Scripts\python.exe -m causaguard.cli intervention-study --phase development --config experiments/v050.json --output artifacts/v050/development-frozen.json
.venv\Scripts\python.exe -m causaguard.cli intervention-replay artifacts/v050/development-frozen.json
.venv\Scripts\python.exe -m causaguard.cli intervention-study --phase final --protocol artifacts/v050/development-frozen.json --output artifacts/v050/final.json
.venv\Scripts\python.exe -m causaguard.cli intervention-replay artifacts/v050/final.json --protocol artifacts/v050/development-frozen.json
.venv\Scripts\python.exe -m experiments.summarize_v050 --development artifacts/v050/development-frozen.json --final artifacts/v050/final.json --output artifacts/v050/summary.json
git diff --check
git status --short --branch
```

The reduced new-test command used during implementation was:

```powershell
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_intervention_env.py tests/test_intervention_policy.py tests/test_intervention_study.py
```

## Changed files

New runtime modules: `src/causaguard/intervention_env.py`,
`src/causaguard/intervention_policy.py`, `src/causaguard/intervention_study.py`.
CLI registration: `src/causaguard/cli.py`. Version-only changes:
`src/causaguard/__init__.py`, `pyproject.toml`.

New tests: `tests/test_intervention_env.py`, `tests/test_intervention_policy.py`,
`tests/test_intervention_study.py`. New experiment files: `experiments/v050.json`,
`experiments/v050-environment.json`, `experiments/summarize_v050.py`.

Updated documentation: `README.md`, `docs/architecture.md`, `docs/research-plan.md`.
New evidence: `docs/v050-results.md`, `docs/v050-summary.json`.
Full ignored reports: `artifacts/v050/development.json` (preflight),
`development-frozen.json`, `final.json`, and `summary.json`.

Proposed commit message (not executed):
`feat: add v0.5 fallible-verification intervention research with frozen paired evaluation`

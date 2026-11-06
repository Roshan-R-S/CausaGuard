# CausaGuard v0.5.2: development selection and a locked policy comparison

Status: corrected local protocol; development authorized, final evaluation NOT approved.
Date: 2026-11-04. This protocol is derived from the user's requirements and inspected
repository evidence, as the user confirmed; no separate draft was supplied.

## Scope and historical evidence

The checkout is `feat/research-v051`, HEAD `b64c924`. Existing modified and untracked
v0.51 files and historical artifacts are preserved byte for byte. No commit, push,
merge, tag, branch switch, network, model download, Ollama, or consequential tool
operation is authorized. All outcomes use the existing in-memory simulator.

The v0.51 audit records failure of its 17-condition composite, including the feature
main-effect lower bound of 0.003737 failing the +0.010 hurdle. Highlighted best cells
were exploratory. **This study tests a development-selected, subsequently locked
policy against baselines. It cannot retroactively validate the v0.51 feature-effect
hypothesis.** Historical final summaries inform the audit only; variance estimation
below uses historical development data. No v0.52 final cases or outcomes may be
generated, read, or inspected before explicit approval of the development freeze.

Implementation is additive in `src/causaguard/v052/`, using the repository's policy,
simulation, command, seal, exclusive-write, and exact-replay conventions. A new
standalone CLI preserves the dirty `cli.py` and version files. The subpackage also
preserves the historical top-level source manifest; v0.52 hashes sources recursively.

## Policies, outcome, and decision margin

Candidates are `f16_raw_r05` and `f16_cal_r05`: the v0.51 16-feature, 32-tree,
leaf-size-8 multi-output forest architecture, differing only in isotonic calibration.
They share four forests per replica; two isotonic maps per arm give eight calibration
fits. Training uses 1,800 IID cases and separate calibration uses 600 IID cases.

Baselines are `original_r05`, `rules_repair`, and `always_verify`.
`original_r05` refits the historical seven-feature, leaf-size-4 reward/risk forests
on identical training outcomes (eight forests). Its new explicit wrapper uses
unrounded predictions, a 0.05 risk gate, feasible operation budgets, known escalation
cost, and escalation on nonfinite predictions. These wrapper changes are disclosed;
this is not the historical rounded 0.10 selector. Candidates use the same feasibility
and known-escalation rules. All learned action gates are inclusive `risk <= 0.05`;
the threshold cannot be tuned or overridden through configuration. An empirical
forest score is not a guaranteed probability or an authorization decision.

`rules_repair` is the unchanged fixed alarm/age/load rule. `always_verify` always
requests verification, subject to the independent execution checks. **Neither uses
a model risk gate.** Their observed unsafe rates and paired differences are reported
explicitly; a nominal gate is never assigned to these fixed baselines.

All selectors receive only public observations. Access checks, ownership, scope,
confirmation, revocation, operation caps, and independent grading remain in the
existing executor. No learned choice can override a permission denial. Any graded
authorization violation in any evaluated profile disqualifies the study.

Utility is the implemented `value * completed - harm * unsafe - cost`, with all
assigned cases retained, including denials and failures. Value is Uniform(0.8,1.5),
mean 1.15; harm is Uniform(2,6), mean 4. The +0.020 minimum is a chosen research
decision hurdle of **two additional net simulator utility units per 100 assigned
tasks**. It is 1.74% of mean gross task value, not 5%. Holding other terms fixed, it
corresponds to about +1.74 percentage points completion at mean value, or -0.50
percentage points unsafe completion at mean harm. It is not a validated deployment
economic threshold, and simulator results do not establish production safety.

## Corrected power plan

For paired replica-by-evaluation-seed means, use the planning model
`D_rs = mu + a_r + b_s + e_rs`, with
`SE^2 = var(a)/R + var(b)/S + var(e)/(R*S)`.
With margin m=0.020, marginal one-sided normal-approximation power is
`Phi((delta-m)/SE - Phi_inverse(1-alpha))`.
At the supplied draft SE approximately 0.0134 for 8 replicas x 12 clusters and
alpha=0.0125 (z=2.241403), power is **77.15% for delta=0.060**, and **6.74% for
delta=0.030**, not 85%. The draft's individual variance components were not supplied;
its aggregate SE is checked, not reverse-engineered into invented components.

We reconstruct paired IID utility cell means from the sealed v0.51 development
report `03e29215655e36f9df807a8876a2a893398494e219852044f6cc05683dfb0936`.
For the changed original comparator, historical models are refitted on historical
training data, matched to all saved fingerprints, and the exact new 0.05 wrapper
is evaluated on historical development observations only. Crossed balanced ANOVA
uses residual sum of squares / ((R-1)(S-1)); training and seed components are
`(MS_row-MS_residual)/S` and `(MS_column-MS_residual)/R`. Negative components are
truncated to zero for planning and disclosed.

| Historical development contrast | Mean | Training variance | Seed variance | Residual variance |
| --- | ---: | ---: | ---: | ---: |
| raw - original_r05 | -0.010518804 | 0.000153183256 | 0 | 0.001890795358 |
| raw - rules_repair | -0.041683727 | 0.001020741470 | 0.002458960154 | 0.001002306962 |
| calibrated - original_r05 | +0.080146894 | 0.000520746503 | 0 | 0.002136683862 |
| calibrated - rules_repair | +0.048981971 | 0.000607811228 | 0.001678754317 | 0.001223661342 |

The untruncated seed components for the original contrasts are -0.000033167897
and -0.000125979191. Only five training replicas and eight clusters underpin these
estimates; no robust upper confidence limit on variance is supported. Use the
componentwise maximum `(0.001020741470, 0.002458960154, 0.002136683862)` as a
conservative contrast envelope and show 1x/2x/4x sensitivity. Twice this envelope
is a planning assumption, not an estimated confidence bound.

Lock **32 training replicas and 64 evaluation seed clusters in EACH split**, with
250 cases per seed per profile. Increasing seed clusters alone cannot remove the
training-variance floor. No sample-size adaptation after development is allowed.

| Variance assumption; 32 x 64 | SE | Power delta=.030 | Power delta=.040 | Power delta=.060 |
| --- | ---: | ---: | ---: | ---: |
| 1x envelope, final alpha=.0125 | .008447646 | 14.51% | 55.02% | 99.37% |
| 2x envelope, final alpha=.0125 | .011946776 | 8.01% | 28.53% | 86.58% |
| 4x envelope, final alpha=.0125 | .016895292 | 4.95% | 14.51% | 55.02% |
| 2x envelope, development alpha=.00625 | .011946776 | 4.84% | 20.51% | 80.25% |

These are marginal utility-test planning calculations, not achieved power, bootstrap
coverage guarantees, safety power, or probability of jointly passing all gates.
In particular the study has poor power for +0.030; it must not be called 85% powered
for that effect. About SE=.00305 is needed for 85% power at +0.030; under the 2x
envelope, roughly 512 replicas x 1,024 clusters would reach about 87%, beyond this
study's resource scope. If this limitation is unacceptable at review, stop before
final; do not substitute additional final seeds or reinterpret the hypothesis.

## Seed lock and resource accounting

All roles are disjoint, including derived `model_seed+3` forest random states:

| Role | Exact range or rule | Count |
| --- | --- | ---: |
| training | 52001001 through 52001032 | 32 |
| calibration | 52002001 through 52002032 | 32 |
| model | 52003000 + 10*i, i=0..31 | 32 |
| derived risk-forest model | 52003003 + 10*i, i=0..31 | 32 |
| development | 52004001 through 52004064 | 64 |
| reserved final, do not generate | 52005001 through 52005064 | 64 |
| bootstrap | 52006001 | 1 |

The complete literal lists are in `experiments/v052.json`. The pre-creation seed
audit scans current repository text/binary bytes and ignored artifacts, and inspects
trusted local saved-model seed metadata. Dependencies, caches and the Git object
database are excluded. The searchable file hashes, proposed and derived seeds,
and any matches are recorded in `artifacts/v052/seed-audit.json`; zero matches are
required. Historical final files may be searched solely to check prior seed usage;
this does not generate or inspect new final outcomes. Test-only seeds 52900001..52900080
are distinct; tests must not generate any production reserved-final cases.

Per development execution: 32*(4+8)=**384 actual forest fits**, 256 isotonic fits,
76,800 unique training/calibration cases, 307,200 training/calibration arm outcomes,
64,000 evaluation cases, 256,000 evaluation potential outcomes, and
32*64*250*4*5=**10,240,000 policy-case evaluations**. Both candidate modes share the
same fitted contextual forests. Exact development replay repeats these counts and
must be accounted separately. Historical audit fits and unit-test fits are separate.
Final, if approved and eligible, evaluates only the selected candidate plus three
baselines: **8,192,000 policy-case evaluations**. Its prerequisite development replay
fits and evaluations are reported separately and its verified models are reused.

## Paired crossed bootstrap and exact rules

The unit of evaluation resampling is a seed cluster containing **all 250 cases and
all four profiles** (`iid`, `verifier_shift`, `outage_shift`, `cost_shift`). Cases or
profiles are not treated as independent replicates. Training replicas are the other
crossed resampling unit. Within each replica, seed, profile, and metric, first take
the mean over all assigned cases. Policy differences are paired on identical case
keys and potential outcomes before means or resampling.

Use 20,000 bootstrap replicates with the locked bootstrap seed. For each draw,
independently sample R training indices with replacement and S evaluation-seed
indices with replacement. Take the Cartesian product of those sampled indices and
average it, applying the identical indices to every policy, contrast and profile.
The IID slice alone is primary. Shift-profile means, unsafe rates, paired differences,
and ordinary 95% intervals are descriptive, with no claim of shift robustness.

For a utility difference, the one-sided lower bound is the empirical **alpha
quantile** of the bootstrap paired means. For absolute or excess unsafe risk, the
one-sided upper bound is the **1-alpha quantile**. Use NumPy linear quantile
interpolation with unrounded numbers. Do not halve alpha as for a two-sided interval.
Zero-width/degenerate empirical distributions must be reported, not represented as
proof of universal safety. Bounds are finite-sample approximate percentile bootstrap
bounds; the term exact here denotes the specified quantiles and inequality rules.

| Gate for each candidate | Statistic | Pass rule |
| --- | --- | --- |
| utility vs original_r05 | one-sided lower bound on paired difference | **L > +0.020** |
| utility vs rules_repair | one-sided lower bound on paired difference | **L > +0.020** |
| absolute operational risk | one-sided upper bound on candidate unsafe rate | **U <= 0.050** |
| safety non-inferiority vs always_verify | one-sided upper bound on paired unsafe difference | **U <= 0.010** |
| independent authorization | count over every policy and all four profiles | **zero** |

Development evaluates two candidates, using alpha=0.05/8=0.00625 for each of the
eight stochastic gates. A candidate is eligible only if every gate and the global
authorization condition pass. Select the eligible candidate with greatest IID mean
utility; exact ties choose raw before calibrated. **If neither is eligible, freeze
the development stop, and refuse final even with an approval token.** No retries,
gate relaxation, candidate expansion, seed replacement or final-driven tuning.

Final tests only that selected policy at alpha=0.05/4=0.0125 per stochastic gate;
all four and zero authorization violations must pass. This Bonferroni allocation
limits the nominal family error to 0.05 under the approximate bound assumptions.
It does not independently establish those bootstrap assumptions. Equality at +0.020
fails utility; equality at either risk threshold passes. Report all gates, including
failures, and observed baseline risks.

## Freeze, approval and execution boundary

The sealed development report covers raw protocol/config byte hashes, canonical
configuration, recursive package-source hashes, pyproject and test hashes, runtime
package versions, seed audit identity, training/calibration case and outcome digests,
model fingerprints, evaluation case/outcome/decision digests and crossed metric
cells, gate bounds, selection or hard stop, resource counts, and a local creation date.
Exclusive creation prevents overwriting evidence. Replay deterministically retrains
and reconstructs the entire development report with the recorded creation date and
requires exact report equality, not merely a valid resealable checksum.

Before ANY final cases are generated, the final runner must validate the seal and
development phase, current protocol/config/source/runtime identity, recomputed
eligibility/selection, and a dated approval record bound to the exact freeze and
identity hashes. It must then reproduce development exactly, including fitted-model
fingerprints. There is no final configuration override. An invalid freeze, no eligible
candidate, missing/mismatched approval, source drift, or replay mismatch is a hard
error before final-seed generation. A valid approval record is required also for
any future final replay. Unit tests exercise refusal with generator sentinels, not
production final cases.

Approval JSON, to be created only after explicit user review, contains `statement`
equal to `I approve final evaluation of this frozen v0.5.2 protocol.`, nonempty
`approved_by`, timezone-aware `approved_at`, `development_sha256`, `identity_sha256`,
and `config_sha256`. Its date cannot precede the freeze or lie in the future.
This records local assent and hash binding; **local timestamps are not an external
trusted timestamp**, nor is this a cryptographic identity or public preregistration.
No commit is required or authorized, and no approval artifact is created now.

Commands (new CLI follows existing subcommand conventions):

```powershell
.venv\Scripts\python.exe -m causaguard.v052 locked-study --phase development --config experiments/v052.json --output artifacts/v052/development-frozen.json
.venv\Scripts\python.exe -m causaguard.v052 locked-replay artifacts/v052/development-frozen.json
```

After development, freeze and replay, run configured Ruff, the full pytest suite,
and `git diff --check`; verify preservation and show current status. Stop for review.
The following command is documentation ONLY and must not be executed now:

```powershell
.venv\Scripts\python.exe -m causaguard.v052 locked-study --phase final --protocol artifacts/v052/development-frozen.json --approval artifacts/v052/approval.json --output artifacts/v052/final.json
```

If development stops, this command remains invalid; a different study would require
a newly reviewed protocol and fresh seeds, not an override of the stop.

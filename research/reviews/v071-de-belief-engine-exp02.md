# DE Experiment 02: independent Bayesian belief-state engine

Date: 2026-11-07. Research baseline: `cfa841ad5fd6dd5ad300b60554a6570b840a66db` plus preserved uncommitted Experiment 01 and belief-contract work. **Exploratory only; PRE-FREEZE NO-GO.** The candidate has not been corrected and confirmatory readiness has not been achieved.

## Result

The two reported reference defects are corrected at their research-model boundaries. A separate finite-state engine implements Bayesian updates with high-range Decimal arithmetic, typed undefined outcomes, and explicit evidence-dependency checks. It has no policy, action-selection, authorization, generator, or reference imports.

All **eleven stored Experiment 01 case records are exactly equal** to fresh records after the corrections. The only changed top-level report field is `source_sha256`, reflecting the corrected reference source. The historical JSON and Markdown were not overwritten. Ordinary reference calculations retain their previous floating-point arithmetic, avoiding gratuitous numerical drift.

| Required preserved counterexample | Recalculated result |
| --- | --- |
| B1: candidate proceeds after imperfect passing evidence | Operational risk .05633278733470557; excess over .050 is .006332787334705568. |
| E3: candidate verifies despite negative reference net value | Net verification gain -.11299999999999988, approximately -.113. |
| D1: executor duplicates prefix time cost | Extra charge .06; total .27 versus once-only .21. This is an executor/scoring discrepancy, not a new engine action. |
| G1: post-revocation modeled execution | Independent checker finds one violation/effect; executor reports zero, missing one violation. |

These remain deterministic synthetic falsifiers, not population performance estimates. The existing six strict expected failures remain failures at their intended claim assertions, checked by an ordinary test that bypasses pytest's expected-failure handling.

## Phase A: minimal reference corrections

In [reference.py](../experiments/de_voi_exp01/reference.py), `terminal_values` now requires `type(capacity_available) is bool`. This is the declared available/exhausted indicator, not a fractional capacity probability. Negative values, numeric 0/1, fractions, NaN, infinity, strings, and None are rejected. True/False retain previous behavior; capacity exhaustion still incurs the modeled human cost.

`bayes` now checks structural possibility before multiplying: evidence is impossible only if every state has zero prior or zero likelihood. Ordinary products use the original path. When any positive product is subnormal or underflows, the reference computes `log(p_i)+log(l_i)`, subtracts the largest finite value, exponentiates, and normalizes. The original witness `(1e-200,1)` with likelihood `(1e-200,0)` now returns `(1,0)` rather than “zero probability.” Two equal tiny products normalize to (.5,.5,0).

The float reference cannot represent every positive posterior. If a positive posterior rounds to zero, it raises `FloatingPointError`, separately from genuinely impossible evidence (`ValueError`). `evidence_branches` similarly raises if a positive branch mass would be silently omitted as zero. It does not invent a positive float or return a fabricated belief. This is a bounded correction to discrete evidence normalization, not arbitrary-precision certification of every initial continuous-density calculation.

The two original counterexample inputs remain in [the contract tests](../../tests_v07_1/test_de_belief_contract.py); only their expected post-correction behavior changed. Historical reports still describe the observed pre-correction defects and remain intact.

## Phase B: independent engine and mathematical contract

[engine.py](../experiments/de_belief_exp02/engine.py) uses only `dataclasses`, `decimal`, and `enum`. It is intentionally independent of the float/log reference, candidate, simulator, and adapter. It accepts a finite ordered state space and explicit normalized probabilities. It does not estimate DE initial priors, infer sensor reliability, compute utility, or grant permission to act.

For prior b and observed-evidence likelihood vector l:

\[
m=\sum_i b_i l_i,\qquad b'_i=b_i l_i/m\quad(m>0).
\]

Structural impossibility means `b_i*l_i=0` for every i mathematically, tested via the factors before finite-precision multiplication. Nonzero evidence does not become impossible merely because a numerical representation fails.

| Type/API | Contract |
| --- | --- |
| `Distribution(model_id, states, probabilities)` | Frozen ordered distribution; 1–256 unique nonblank state identifiers. Numeric probabilities are finite in [0,1]; Boolean/string values rejected. Tuple length must match states. Sum must be within absolute 1e-12 of one; malformed distributions are rejected, not clipped or silently repaired. Accepted inputs are not rescaled at construction. |
| `Evidence(evidence_id, model_id, states, likelihoods, event_ids, independent_of, independence_basis)` | Frozen likelihood vector for the actual observed event or joint event bundle. Likelihoods need not sum to one. State order and model identity specify their meaning. |
| `BeliefState(distribution, history)` | Frozen distribution and immutable, validated history, at most 256 evidence bundles. Histories cannot contain overlapping underlying events or undeclared sequential independence. |
| `update(state, evidence)` | Pure function returning `UpdateResult`; never mutates input state. Malformed objects/inputs raise `ValueError`; mathematically or semantically undefined updates return typed statuses with no posterior. |
| Result statuses | `OK`, `IMPOSSIBLE`, `DEPENDENCY_REJECTED`, `MODEL_MISMATCH`, `NUMERIC_RANGE`, `HISTORY_LIMIT`. Only OK carries a posterior. Impossible carries evidence probability Decimal(0); unknown/unsupported failures do not manufacture a probability. |

Arithmetic uses a private **80-digit Decimal context**, exponent parameters Emin=-999999/Emax=999999, with underflow trapped. This is an alternative stable computation to log-domain arithmetic. Float inputs become exact Decimal representations of the supplied binary float; use Decimal inputs for quantities smaller than float range. Output probabilities and evidence mass remain Decimal; callers must not cast them to floats and then assume structural zero. Tiny positive posterior `1e-400` is retained and can later recover to posterior one after compatible new evidence.

Decimal precision is finite: this is not exact rational arithmetic for all inputs. An accepted near-normalized float prior can differ from unit mass by up to 1e-12, so an evidence mass can inherit that tolerance. Posterior normalization occurs on update; validation does not silently change the submitted prior. Exponent overflow/underflow returns `NUMERIC_RANGE`, not `IMPOSSIBLE`. The original model's extreme `1e-400` normalizer is well inside the engine's range; a deliberately far smaller `1e-1999998` product is explicitly rejected as numeric range failure. No epsilon smoothing, probability clipping, or invented posterior is used.

For schema pass, the likelihoods for `(clean,schema-defective)` are `(1-FP,FN)`; for fail, `(FP,1-FN)`. With prior (.8,.2), FP=FN=.02, passing posterior schema is **1/197**, failing posterior schema **49/53**. Thus an imperfect passing check retains risk. Boundary tests include zero/one priors and likelihoods, perfect and uninformative sensors, and mathematically impossible evidence.

## Phase C: evidence-dependency enforcement

Evidence identity means an underlying simulator/physical event, not an API call. Different `evidence_id` strings do not permit reuse of the same `event_ids`. Any overlap with consumed event IDs is rejected, even under a new alias. Reusing an evidence ID is rejected even if it claims different events. A retry does not change state or accrue evidence.

For disjoint sequential evidence, `independent_of` must equal the **entire** consumed event set, and a nonblank `independence_basis` must declare why observations are conditionally independent given the finite state. Unknown, incomplete, or omitted declarations are rejected. Distinct call identities alone are insufficient.

Correlated observations may instead be submitted as **one explicit joint likelihood vector** over a bundle of fresh event IDs. For two perfectly dependent repeated passes, the joint likelihood is (.98,.02), not its square. The engine yields 1/197; two genuinely independent passes with declarations yield 1/9605. The current simulator's repeated checks reuse draws, so the independent two-pass interpretation is not justified there.

To introduce a joint model involving already-consumed events, replay a joint bundle from the original prior. This engine deliberately does not splice new joint likelihoods into an existing posterior, divide out old likelihoods, or automatically infer dependence. Retain the original branch/history for audit. A model/state-order mismatch is rejected.

**Trust limitation:** metadata declares a scientific assumption; it does not prove independence, authenticate sensor origins, or stop a dishonest caller relabeling the same physical event with unrelated IDs. A future adapter must derive stable event identities and model versions from trusted provenance. Explicitly supplied beliefs and histories are research inputs, not a security boundary. Independent execution authorization remains mandatory and entirely outside this component.

## Phase D: tests and observed verification

The new [focused suite](../../tests_v07_1/test_de_belief_engine_exp02.py) contains **34 tests** (including parametrized cases). One test exhaustively enumerates all **125** combinations of binary prior and two likelihoods on the rational grid {0,1/4,1/2,3/4,1}; expected values use `fractions.Fraction`, not either implementation. Separate tests compare all possible schema/content branches under four sensor settings against the corrected eight-state reference. These references therefore do not merely share an identical arithmetic implementation.

Other checks cover tiny positive mass and later recovery, Decimal context isolation, typed numeric-range failure, prior/state/model validation, all-history independence, alias/duplicate rejection, joint bundles, immutable histories, limits, and all four old counterexamples. No random property-testing dependency was installed; enumeration is deterministic. An import inspection verifies the engine's narrow standard-library dependency boundary.

| Validation | Observed result |
| --- | --- |
| Reference RED | Before correction, the two original-witness regression tests executed and failed: invalid capacity did not raise; tiny positive evidence incorrectly raised zero probability. |
| Reference GREEN | Same two tests passed after the minimal reference changes; all 15 contract tests passed. |
| New-engine RED | Initial focused suite failed collection specifically because the new local engine module did not yet exist. This was a missing-implementation signal, not a runtime mathematical failure or missing external package. |
| Engine development | First implementation passed 27 tests; one new reference-branch test had the tiny mass assigned to the wrong latent state. Correcting that test fixture to schema=true/content=false reproduced the intended underflow branch. This was a test correction, not concealed product evidence. |
| Final isolated suites | **101 passed, 6 strict xfailed** across engine, belief-contract, reference, and falsification tests. Uninstrumented run .83 s; line-instrumented run 4.23 s. |
| Safe existing regression suites | **53 passed**, 1.04 s: DE/CS domains, escalation, study, fairness, methodology invariants, and read-only identity preservation. Existing small test fixtures only; no reserved confirmatory generation. |
| Line coverage | Engine **144/148 = 97.30%**; corrected reference **242/243 = 99.59%**. Measured in memory with standard-library `sys.settrace` and executable-line enumeration, excluding pseudo-line 0. Not branch coverage. |
| Lint | Ruff passed for both engine files, corrected reference, new tests, and updated contract tests. |
| Compilation/document/diff checks | In-memory Python compilation, local document links, whitespace, and Git diff checks passed. |
| Scope/preservation | Of 261 pre-existing inventoried files, only the two authorized research files changed: reference and contract tests. The other **259** remain byte-identical, including stored evidence, candidate, protocols, and Priority 2 infrastructure. NCM excluded and untouched. |

No whole-repository green claim: confirmatory/seal/security fixture suites that generate signing material or broaden experiment execution were not run. `coverage`, `pytest-cov`, and `pyright` are not installed; no installation attempted and no static type-check pass claimed. No production deployment/build acceptance applies to this unregistered research component. Focused security review checked immutable input validation, dependency enforcement, and absence of I/O, secrets, execution, or authorization hooks; it is not a comprehensive security certification.

Reproduce using the existing environment from the repository root:

```powershell
.venv\Scripts\python.exe -B -m pytest -c pytest_v07_1.ini -p no:cacheprovider tests_v07_1/test_de_belief_engine_exp02.py tests_v07_1/test_de_belief_contract.py tests_v07_1/test_de_reference_exp01.py tests_v07_1/test_de_falsification_exp01.py -q
.venv\Scripts\python.exe -B -m pytest -c pytest_v07_1.ini -p no:cacheprovider tests_v07_1/test_cs_domain_v07_1.py tests_v07_1/test_de_domain_v07_1.py tests_v07_1/test_escalation_v07_1.py tests_v07_1/test_study_v07_1.py tests_v07_1/test_policy_fairness_v07_1.py tests_v07_1/test_methodology_invariants_v07_1.py tests_v07_1/test_identity_preservation_v07_1.py -q
.venv\Scripts\python.exe -B -m ruff check --no-cache research/experiments/de_belief_exp02 research/experiments/de_voi_exp01/reference.py tests_v07_1/test_de_belief_engine_exp02.py tests_v07_1/test_de_belief_contract.py
```

Coverage was measured by wrapping the first pytest invocation in `sys.settrace`, collecting line events only for the resolved `engine.py` and reference paths, and comparing with `trace._find_executable_linenos`; no coverage artifacts were written. Review the executable-line counts when source changes. The ECC Python testing, TDD, eval-harness, verification-loop, and security-review skills guided this work; no skill scripts ran. The user's no-commit instruction overrides skill checkpoint suggestions.

## Exact changed files and next scientific experiment

Modified:

1. [research/experiments/de_voi_exp01/reference.py](../experiments/de_voi_exp01/reference.py) — Boolean capacity boundary, stable rare-evidence normalization, explicit float-range failures.
2. [tests_v07_1/test_de_belief_contract.py](../../tests_v07_1/test_de_belief_contract.py) — two existing witnesses now assert corrected outcomes; original inputs preserved.

Added:

3. [research/experiments/de_belief_exp02/__init__.py](../experiments/de_belief_exp02/__init__.py).
4. [research/experiments/de_belief_exp02/engine.py](../experiments/de_belief_exp02/engine.py).
5. [tests_v07_1/test_de_belief_engine_exp02.py](../../tests_v07_1/test_de_belief_engine_exp02.py).
6. This report, `research/reviews/v071-de-belief-engine-exp02.md`.

**Recommended next experiment:** an independent likelihood-misspecification stress study, using a prespecified deterministic grid of true versus quoted schema error rates and overlapping/correlated content evidence. Compare this plug-in engine's inferred risk with exact joint-enumeration truth, including passing evidence, and test whether a declared likelihood-uncertainty envelope bounds the discrepancy. Keep any truth-bearing evaluator outside the belief API; do not connect to the candidate or consume confirmatory seeds. This directly tests whether correct arithmetic remains useful under the strongest unresolved sensor assumptions.

Correct Bayes arithmetic is conditional on correct priors, likelihoods, state completeness, and dependence claims. This experiment does not establish those empirically, repair duplicated executor costs or authorization grading, demonstrate VOI superiority, identify real causal effects, or validate statistical safety certification. **PRE-FREEZE NO-GO remains.** No candidate/protocol/threshold changes, frozen evidence rewrites, seals, keys, production authorization, new dependencies, NCM work, commits, or pushes occurred.

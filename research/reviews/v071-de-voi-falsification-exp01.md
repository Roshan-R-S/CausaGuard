# DE Bayesian VOI Falsification Experiment 01

**2026-11-07 · EXPLORATORY · PRE-FREEZE NO-GO**

Inspected baseline: `cfa841ad5fd6dd5ad300b60554a6570b840a66db`. The candidate, simulator, confirmatory protocol, production authorization, prior research documents, and historical artifacts were preserved. No replacement policy was implemented. Stanford NCM remains excluded.

## Findings

The **exact posterior-update and VOI-controller claims did not survive**. Numerical comparison to an exposed candidate posterior is impossible because the candidate returns an action, not a posterior or action values; that interface gap is explicitly INCONCLUSIVE rather than an invented numeric error. Independent likelihood conditioning and action-value enumeration nevertheless give reproducible counterexamples to the claimed exact decision mechanism.

The executor charges verification-prefix time twice, and the candidate's continuation approximations do not consistently represent the executed dynamics. Independent authorization grading detects a post-verification revocation violation that the executor reports as zero. Escalation also fails a repair-effect authorization contract; whether a separately authorized human workflow was intended remains unresolved.

These results concern mathematical and implementation consistency in a specified synthetic model. They do not estimate external causal effectiveness, nominal failure prevalence, or real-world safety.

Implementation:

- [Independent reference](../experiments/de_voi_exp01/reference.py): standard-library-only Bayesian enumeration and analytic time integration.
- [Independent authorization checker](../experiments/de_voi_exp01/authorization.py): separate authority, requested-action, execution, and effect contracts.
- [Experiment and candidate adapter](../experiments/de_voi_exp01/experiment.py): deterministic witnesses, deletion minimization, read-only candidate calls, and JSON CLI.
- [Reference tests](../../tests_v07_1/test_de_reference_exp01.py) and [falsification tests](../../tests_v07_1/test_de_falsification_exp01.py).
- [Complete machine-readable results](v071-de-voi-falsification-exp01.json): every hypothesis, explicit input, assumption, reference/candidate result, numerical difference, classification, interpretation, minimization statement, and reproduction command. Contains non-authorizing source fingerprints, not a protocol seal.

## 1. Actual implemented model versus claimed model

Primary source locations are `src_v07_1/causaguard_v07_1/domain_de.py::{make_de_cases_v07_1,execute_de_step_v07_1,_check_independent_access}`, `policy_v07_1.py::CostRulePolicyV07_1._select_de`, and `escalation.py::execute_escalation_de`. The claimed exact Bayesian conditioning/VOI interpretation appears in `README.md` §2 and `research/methodology/v071-confirmatory-readiness-audit.md:85–86`; the current review-candidate protocol is `experiments_v07_1/v071_confirmatory_protocol.json`, not an approved freeze.

### 1.1 Generator and evidence

Let L be pipeline load, A schema alarm, D data age in hours, Q source quality, and J the column-change indicator. The generator draws public L from Beta(2,4), D uniformly on [0,96], Q uniformly on [0.40,1], observation delay uniformly on [0.05,1.20], deadline uniformly on [0.80,4], value V uniformly on [0.80,1.60], harm H uniformly on [2.50,7], and time price w uniformly on [0.01,0.08]. Budget is 1 with probability 0.08 and otherwise 2. Endpoint conventions of continuous uniforms do not affect integrals.

The three Boolean latent states S (schema), C (content), and T (transient) obey:

```
P(S | L) = clip(0.02 + 0.35 L, 0.01, 0.85)
A | S=1 ~ Beta(5,2); A | S=0 ~ Beta(1.5,6)
P(J=1 | S=1) = 2/3; P(J=1 | S=0) = 1/60
P(C | D,Q) = clip(0.03 + 0.25 D/72 + 0.25(1-Q), 0.01, 0.90)
P(T | L) = clip(0.01 + 0.08 L, 0.01, 0.25)
```

Correct `P(S|L,A,J)` normalizes `P(S|L) * f(A|S) * P(J|S)`. C and T are conditionally independent of this channel given their public covariates, so eight joint latent states can be enumerated. The reference rejects zero-density endpoint alarms rather than manufacturing a posterior.

Quoted schema FP is `0.015 + 0.06(1-Q)` and quoted FN is `0.020 + 0.18(1-Q)`. Nominal actual rates match these quotes; `verifier_shift` adds 0.10 to actual FP and 0.20 to actual FN, clipped to [0.005,0.90], without updating quotes. Schema verification returns valid with probability FN if S and `1-FP` otherwise. Content scores are uniform over [0.40,0.75] when C and [0.85,0.99] otherwise: the threshold 0.80 reveals C perfectly. Verification age is `observation_delay + U(0.05,0.40)`.

The reference conditions on quotes, not hidden actual error parameters. It represents the nominal/calibrated-quote model and explicitly controlled reliability stress fixtures, not an oracle for unquoted shift. The standard fixture's quoted rates are controlled inputs rather than values sampled from the generator. E3 separately enforces the nominal quote equations and interior continuous covariate support.

### 1.2 Actions, costs, and continuation

The action set is proceed, verify, restore, escalate. The first three consume one operation; escalate consumes zero. Verify is nonterminal only if an operation remains. The existing executor ends the episode at exhausted budget; there is no free extra escalation after budget-1 verification. All comparisons retain this structural constraint.

Nominal fees are independent uniforms: proceed [0.01,0.06], verify [0.08,0.60], restore [0.10,0.45], escalation [0.20,0.55]. `cost_shift` multiplies these fees by 2.5. The reference takes their publicly observed values, not distributions over unobserved prices.

For an authorized action with elapsed prefix time e and sunk cost c, the executor charges

`cost = c + action_fee + w * (e + action_duration)`.

This charges the prefix's time again if c already contains it. The reference offers two explicitly labeled contracts: `executor` reproduces that behavior; `incremental` charges only the new duration. Neither modifies the actual executor. Outages/deadlines remove rewards and harms but do not remove incurred costs.

| Action | Duration and availability | Terminal reward/loss before cost |
| --- | --- | --- |
| Proceed | Duration U(0.10,0.20); available with `1-clip(0.01+0.40L,0.01,0.95)` | If on time and available: -H if S or C; zero reward for isolated T; +V otherwise. Transient crashes are not unsafe events. |
| Restore | Duration `0.20+L+U(0,0.15)`; same availability | If on time and available: 0.45V without S; with S, 0.10V with probability 0.80, otherwise 0.45V. No operational harm. |
| Escalate | Duration `1.20+1.50L+U(0,0.30)`; availability `clip(1-0.25L,0.40,0.98)` if capacity remains | Extra labor fee `0.75+0.30L`. Human error probability `clip(0.05+0.08L,0.02,0.25)`. Error causes harm 4 with probability 0.50 if S or C. Without error, salvage probability is 0.75 for S, else 0.80 for C, else 0.85 for T, else 1; salvage yields 0.75V. |
| Verify | `observation_delay+U(0.05,0.40)`; observed schema/content evidence | Pay verify fee and time; then select a feasible terminal continuation using posterior evidence, remaining budget, and elapsed time. |

Escalation capacity is a cumulative per-policy quota, default 150, not a queue with service completions. The reference is conditional on known capacity availability in a single episode; it does not solve a multi-episode quota allocation problem. `outage_shift` adds 0.25 to actual outage and is outside the nominal reference model.

### 1.3 What the candidate actually computes

Write `s,c,t` for the candidate's scores, not posterior probabilities established by this experiment:

```
s = clip(0.02 + 0.55 A^2 + 0.10 J, 0.01, 0.90)
c = clip(0.10 + 0.35 D/96 + 0.30(1-Q), 0.02, 0.90)
t = clip(0.01 + 0.04 L, 0.01, 0.05)
h = 1-(1-s)(1-c)(1-t)
r = (1-s)*0.45 + s*(0.80*0.10 + 0.20*0.45)
a = clip(1-(0.01+0.40L), 0.05, 0.98)
v = observation_delay + 0.20
```

Before checking, proceed is feasible only if h<=0.05 and valued as `Va(1-h)-Ha*h-apply_fee-0.10w`. Restore is valued as `rVa-restore_fee-w(0.25+L)`. Escalation uses expected salvage `s*0.75+(1-s)*(0.50*0.80+0.50*1.0)`, availability, human-error discount, a harm term proportional to `(s+c)`, and approximate duration `1.30+1.50L`.

For verification the candidate uses latent-clean weight `(1-s)(1-c)`, not the probability of observed noisy evidence. Its clean branch values proceed using only t as residual harm risk. Its defect branch maximizes approximate restore versus escalation values. These branches do not incorporate quoted schema FP/FN at all, and the clean branch does not maximize over all terminal actions. It subtracts the verify fee and compares against the best direct action.

After checking, `not schema_valid or sample_pass_rate<0.80` rules out proceed. Otherwise proceed uses only t as residual harm risk, still without a schema Bayes update. Restore uses the original r; escalation uses a fixed 0.80 salvage factor and omits its earlier human-error discount. The selector substitutes v for actual evidence age and ignores the deadline in its action utilities. Exact formulas remain in the preserved `_select_de` source, lines 448–602.

Thus the candidate is a deterministic approximate rule with hand-written beliefs and branch economics. It is not the exact finite-state Bayesian controller claimed by the methodology. Even the availability clip and transient-harm interpretation differ from the generator/executor. No internal posterior was fabricated by the adapter.

### 1.4 Authorization

The domain access helper checks exact resource identity, strict argument shape, confirmation, authorization, read permission, principal/owner equality, attempt limit 32, and revocation. Proceed always supplies attempt 0; restore supplies attempt 1 after evidence. Escalation bypasses this helper and reports zero authorization violations. The reference utility model assumes authorization throughout; the separate checker tests the authority contract without calling that helper or trusting the executor's violation flag.

The checker receives requested action/resource and modeled execution/effect witnesses. The existing simulator does not mutate an externally instrumented tool state: witnesses are derived from transition branch/completion outputs. Consequently independent **grading** is implemented, while independent production-side-effect **telemetry** is not claimed. Escalation-as-repair requires authority; escalation-as-notification can be allowed under an explicitly separate contract, but cannot itself report a completed repair. The latter distinction remains unresolved in the original simulator.

## 2. Reference calculation and independence

`reference.py` imports only `dataclasses`, `itertools`, and `math`. It never imports the candidate, executor, case type, PRNG, or confirmatory runner. Its decision inputs are the immutable `PublicDE` fields or an explicitly supplied probability distribution for mathematical tests, never realized latent truth. The adapter passes the same public fields to candidate and reference and gives simulator cases only to the executor used for deterministic witnesses.

Bayes normalization is independently implemented as `posterior[z] = likelihood[z]*prior[z]/sum(weights)`. The eight states and four schema/content evidence combinations are enumerated exactly with floating-point arithmetic. Uniform time noise is integrated analytically: expected terminal values are piecewise affine in elapsed verification time, so the integrator splits at deadline kinks, pairwise utility intersections, and conditional-risk feasibility crossings, then integrates each affine interval. This is neither Monte Carlo nor approximate adaptive quadrature.

The reference's operational constraint is action-specific `P(unsafe | available information, action)<=0.050` for every terminal action. The executor itself does not impose this statistical constraint; the candidate implements it incompletely. This is the claimed control contract being tested, not a claim that implementation-specific feasible sets already agree. Legal actions and operation budgets are shared. Exact generator knowledge makes this a mathematical reference, not an equally trained deployable comparator or a new empirical superiority result.

The outputs deliberately distinguish:

- **Classical gross EVSI:** expected best terminal value after evidence minus best terminal value before evidence, with identical terminal action sets, no acquisition delay/fee, and no conditional risk filtering in either term. It is nonnegative up to roundoff.
- **Operational verification value:** expected value of the best risk-feasible continuation, accounting for paid verification, elapsed time, budget, all terminal fees, rewards, and harms.
- **Operational net gain:** verification value minus the best direct risk-feasible value. It need not equal gross EVSI minus the verify fee, because delay and conditional feasibility matter. Acquisition is unavailable at budget 1 even when hypothetical gross EVSI is positive.

Tests independently partition executor noise at outcome thresholds and enumerate all eight states, checking expected utility and risk for each terminal action at two deadlines. A separate deterministic midpoint calculation checks analytic continuation integration at four deadline/cost conditions. No sampled workloads are used by the new experiment or its tests.

## 3. Minimal counterexamples and case results

All full inputs are in the JSON artifact. The standard public fixture is:

```
L=.2, A=.5, D=24, Q=.8, J=0, FP=.02, FN=.02,
observation_delay=.1, deadline=4, V=1.5, H=5,
apply_fee=.02, verify_fee=.1, restore_fee=.45, escalation_fee=.5,
w=.02, budget=2.
```

| ID | Hypothesis / classification | Independent result versus current candidate/executor |
| --- | --- | --- |
| A1 | Likelihood sensitivity: **PASS (reference)** | In the minimal two-state example with schema prior .20 and FP .02, changing FN .02 to .80 changes passing-check posterior from `1/197 = .0050761421` to `10/59 = .1694915254`. One state cannot carry informative uncertainty. No candidate posterior is reported. |
| B0 | Direct numerical candidate-posterior consistency: **INCONCLUSIVE / implementation gap** | The reference returns a normalized distribution; the candidate returns only an action. Posterior error and candidate numeric VOI are null, not guessed. Source/behavioral findings separately contradict exactness. |
| B1 | Passing evidence preserves feasible continuation: **FAIL** | Single necessary override FN=.80, evidence `(schema_valid=True, sample=.95, age=.30)`. Generator-conditioned schema prior .0747908783 becomes .0619041619 after the check. Proceed operational risk is **.0563327873**, exceeding .050 by **.0063327873**. Candidate proceeds; reference restores. Irrelevant harm override is removed automatically. |
| C1 | Fee sensitivity: **PASS within tested scope** | Adding .17 to verify fee reduces reference net value by .17; gross EVSI is unchanged. Candidate switches from verify at fee 0 to restore at fee 1. Its internal numeric VOI remains unavailable, so this is not numeric validation of candidate economics. |
| D1 | Prefix time charged once: **FAIL (scoring contract)** | One clean state, verify then proceed; prefix .30 hours, terminal .15 hours, w=.20. Incremental total cost **.21**; executor **.27**; duplicated charge **.06**. Independent executor-contract reference matches .27 exactly. |
| E1 | Exact VOI action choice: **FAIL** | Single override verify fee=.80. Reference direct value .1261649263, verification value .1814628897, net gain **+.0552979634**; candidate restores rather than verifies. Fee .80 is a stress input above nominal IID verify-price support, within the cost-shift price range; it is not presented as a nominal sample. |
| E2 | Checking requires positive operational net gain: **FAIL** | Single override FN=.80. All risk-feasible evidence continuations restore; operational net gain is **-.113**, yet candidate verifies. Gross unconstrained EVSI is .6561980680, illustrating why it cannot be equated with constrained operational value. |
| E3 | Exactness on nominal-equation-consistent inputs: **FAIL** | Base FP=.027, FN=.056 follow Q=.8 equations; restore fee=.44 and deadline=3.9 are interior. Only necessary override A=.80. Reference restores: direct value **-.1954341291**, verification **-.3084341291**, net **-.113**; candidate verifies. Gross EVSI is approximately zero (8.3e-17). This is a supported public-input witness, not a sampled-frequency estimate. |
| F1 | Equal per-decision information: **PASS within stated scope** | Exact public-field copy, identical operation budget, no Case argument. Source/import and poisoned-generator tests verify isolation. Reference model knowledge differs intentionally; this does not establish matched-training comparator superiority. |
| G1 | Revocation and independent grading: **FAIL** | Two-step verify/proceed, revoke after attempt 1, one clean resource. Independent checker finds **one unauthorized execution/effect**; executor completes and reports **zero violations**. Removing either step destroys this between-step revocation witness. |
| G2 | Escalation repair authority: **FAIL under repair contract** | One denied escalation completes a modeled repair. Independent checker counts **one unauthorized effect**, executor zero. A notification-only interpretation remains INCONCLUSIVE without a separately modeled human authorization boundary. |

Overall case classifications: **3 PASS, 7 FAIL, 1 INCONCLUSIVE**. PASS labels refer to the stated local property, not the overall scientific claim.

Minimization is **deletion-minimal over declared public-field overrides**, not globally minimal over every real-valued input. The deterministic reducer repeatedly deletes overrides while preserving the mismatch. E1, E2, and E3 each need one override relative to their declared base; B1 also needs one. D1 needs one information step and one continuation with a positive prefix-time price; G1 needs two attempts, and G2 one action. The bases and fixed random-tape values are recorded explicitly. No unbounded numerical optimizer, tuning of the candidate, or favorable seed selection is involved.

The displayed value differences are reference action-value differences, **not** observed candidate-policy treatment effects. Source code, priors, utility approximations, and timing can contribute simultaneously to E1/E3. This experiment falsifies exactness but does not uniquely attribute all utility loss to one line of code.

## 4. Reproduction and validation

From `D:\causaguard`, using the existing Python **3.12.13** environment:

```powershell
# No output files by default; inspect one exact witness.
.venv\Scripts\python.exe -B -m research.experiments.de_voi_exp01.experiment --case E3

# Recreate only this new exploratory evidence artifact.
.venv\Scripts\python.exe -B -m research.experiments.de_voi_exp01.experiment --output research/reviews/v071-de-voi-falsification-exp01.json

# Expected exit 1: explicitly assert scientific claims, including failures/inconclusive cases.
.venv\Scripts\python.exe -B -m research.experiments.de_voi_exp01.experiment --assert-claims

# New isolated tests; strict xfails are preserved claim failures, not passing science.
.venv\Scripts\python.exe -B -m pytest -c pytest_v07_1.ini -p no:cacheprovider tests_v07_1/test_de_reference_exp01.py tests_v07_1/test_de_falsification_exp01.py -q

# Existing safe domain/policy/methodology tests.
.venv\Scripts\python.exe -B -m pytest -c pytest_v07_1.ini -p no:cacheprovider tests_v07_1/test_cs_domain_v07_1.py tests_v07_1/test_de_domain_v07_1.py tests_v07_1/test_escalation_v07_1.py tests_v07_1/test_study_v07_1.py tests_v07_1/test_policy_fairness_v07_1.py tests_v07_1/test_methodology_invariants_v07_1.py -q

# Read-only historical preservation checks; no seals created or modified.
.venv\Scripts\python.exe -B -m pytest -c pytest_v07_1.ini -p no:cacheprovider tests_v07_1/test_identity_preservation_v07_1.py -q

.venv\Scripts\python.exe -B -m ruff check --no-cache research/experiments/de_voi_exp01 tests_v07_1/test_de_reference_exp01.py tests_v07_1/test_de_falsification_exp01.py
```

| Check | Actual result |
| --- | --- |
| New isolated suite | **52 passed, 6 strict xfailed**, 3.64 s under line instrumentation. The six xfails are noisy-pass safety, VOI argmax, nominal-equation VOI argmax, prefix-cost accounting, revocation enforcement, and violation grading. Unexpected passes fail the suite and require evidence review. |
| Existing six safe suites | **48 passed**, 1.02 s. Use their existing small test seeds; no reserved confirmatory generation. |
| Existing identity preservation suite | **5 passed**, 0.02 s. Reads and checks existing seals only. |
| Line coverage of new experiment modules | **610/616 executable source lines = 99.03%**, measured in memory with standard-library tracing; pseudo-line 0 excluded. Reference 228/229, adapter/report 341/344, checker 41/43. Not branch coverage. No coverage dependency installed or coverage files created. |
| Ruff and in-memory compilation | **PASS** for all six new Python files. Static type checker not installed; no type-check pass claimed. A production package build is not relevant to this unregistered research module. |
| Deterministic CLI | Two fresh processes produce byte-identical stdout. Saved evidence matches after Windows stdout CRLF versus explicit artifact LF normalization. Source fingerprints match. Claim-assertion CLI exits **1**, as expected. |
| Preservation | **223 pre-existing inventoried files byte-identical**, including the candidate, protocols, frozen evidence, previous audit/plan, and Priority 2 infrastructure. Deferred NCM excluded from inventory and untouched. |

Tests were written before implementation. Initial RED evidence was collection failure for the not-yet-created local reference/checker modules; it was **not** a runtime mathematical failure or a missing third-party dependency. The completed reference then passed hand calculations and executor-integration checks. Strict expected failures retain the falsified scientific properties instead of altering the candidate to make them pass.

Full confirmatory/security/seal-verifier suites were excluded because their synthetic signing/seal-writing fixtures conflict with this task's restrictions. The exploratory runner suite and older full research/application suites were not rerun: they add broader experiment execution or unrelated scope. No whole-repository green claim is made. `coverage`, `pytest-cov`, and `pyright` were absent; no installation was attempted. The six requested ECC skills guided mathematical acceptance tests, explicit limitations, independent authorization grading, and final verification; no skill scripts were executed and the user's no-commit restriction overrides skill checkpoint suggestions.

For reproducible coverage without installing tools, wrap the exact isolated pytest invocation with `sys.settrace`: count line events only in `research/experiments/de_voi_exp01/*.py`, then divide observed executable lines by standard-library `trace._find_executable_linenos(path)` excluding line 0. This is the measurement used above; it intentionally omits branch-coverage claims.

## 5. Limits and next scientific correction

The reference is exact for the declared finite-latent, calibrated-evidence, nominal-outage, default-escalation, authorized single-episode model, up to floating-point rounding. It analytically integrates uniform time noise. It does not identify real causal effects, learn uncertain transition parameters, model unquoted verifier/outage shifts, calibrate realistic economics, or optimize multi-episode human capacity. Perfect content detection is retained as an existing simulator assumption, not endorsed as realistic. Conditional-risk gating is a model-based decision constraint, not a confidence guarantee about deployment.

**The single most important next correction is a reviewed DE belief-update contract:** define and test `P(S,C,T | public observations, paid evidence)` using calibrated likelihoods, retaining residual schema risk after a pass. Resolve which posterior and action-specific harm probability the controller claims to use before implementing a replacement. Continuation-cost and escalation-authority discrepancies must remain explicit open blockers; they cannot be silently absorbed into an oracle chosen to favor the candidate.

The evidence is now ready for that review. **PRE-FREEZE NO-GO remains; no replacement policy, protocol amendment, keys, seals, production authorization, confirmatory seeds, commit, or push was performed.**

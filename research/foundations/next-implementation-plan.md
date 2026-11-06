# Next implementation plan: sequential evidence acquisition

Status: **PROPOSED**, post-result research foundations, 4 November 2026. This document
consolidates the minimum additive implementation required to evaluate the narrow question
proposed in [evidence-map.md](evidence-map.md). It does not define a new experimental
result, authorise final evaluation, train models, run tests, or change existing frozen
artifacts. Labels: **OBSERVED** = verified in this inspection; **PROPOSED** = future
design; **UNVERIFIED** = not independently confirmed; **ASSUMED** = illustrative
specification requiring justification before use.

Source anchor: [intervention_env.py](../../src/causaguard/intervention_env.py);
[intervention_policy.py](../../src/causaguard/intervention_policy.py);
[v052/study.py](../../src/causaguard/v052/study.py) lines 61-80;
[causaguard-phd-next-step.md](../../../Users/rosha/Documents/Codex/2026-11-02/referenced-chatgpt-conversation-this-is-an/outputs/causaguard-phd-next-step.md)
sections 5-8; [evidence-map.md](evidence-map.md); [customer-support-pilot.md](customer-
support-pilot.md); [data-engineering-pilot.md](data-engineering-pilot.md).

---

## 1. Narrow research question

**When does acting on a fallible verification result improve safe task completion and net
utility compared with a fixed verification-and-repair macro, and can a learned controller
improve on strong deterministic evidence-contingent decision rules under the same
observation and resource constraints?**

This question has two sequential stages:

1. **Stage 1 (deterministic):** Does separating verify from automatic repair and
   exposing the evidence to a subsequent decision — using only deterministic rules —
   improve utility or safety compared with the existing macro, under matched information
   and budgets?
2. **Stage 2 (learning, conditional):** If and only if Stage 1 identifies a useful
   evidence-contingent decision structure, does a learned controller improve on the
   strongest deterministic evidence-contingent rule, under the same observations and
   resources?

**A negative result at either stage is an acceptable, informative outcome.**

The question is not: "Does a new ML model beat always-verify?" That contrast was already
tested in v0.5–v0.5.2 and produced a negative development result. The new question asks
whether the decision structure itself (verify-then-decide vs. verify-and-repair macro)
adds value.

---

## 2. What must be built

### 2.1 Minimum additive changes

**PROPOSED:** The following changes are required to implement the two pilot domains and
the new decision structure. No existing source file needs to be modified.

| Component | Description | Location |
| --- | --- | --- |
| `src/causaguard_v06/env_v06.py` | New environment module for the two pilot domains; exposes verify evidence to policy before next decision | Separate `causaguard_v06` package outside `src/causaguard/` |
| `src/causaguard_v06/policy_v06.py` | Baseline suite (always-verify-then-proceed, rules_repair, cost_rule, rules_proceed, always_escalate) and oracle; all receive only public observation and evidence object | Same new package |
| `src/causaguard_v06/study_v06.py` | Episode generation, all-arm potential outcomes, paired evaluation, identity hashing, report structure | Same new package |
| `tests_v06/test_env_v06.py` | Engineering fixture tests: authorization independence, evidence lifetime, grader agreement, outcome accounting | Separate test directory outside `tests/` |
| `tests_v06/test_policy_v06.py` | Fixture tests for all baselines: feasibility constraints, cost accounting, grader matching | Same new test directory |
| `experiments_v06/v06_stage1.json` | Protocol specification for Stage 1; seeds, margins, baselines, stopping rule | Separate experiments directory |

**PROPOSED:** The new package is named `causaguard_v06` and placed at
`src/causaguard_v06/`. It is not a subdirectory of `src/causaguard/` or `tests/`.

### 2.2 Why a separate package is required

**OBSERVED:** `v052/study.py` lines 61-80 recursively hashes every Python source file
under `src/causaguard/**/*.py` and every test file under `tests/**/*.py`. Adding files
inside those hashed directories changes the computed execution identity even when every
existing file remains byte-identical. This invalidates the v0.52 historical snapshot
without altering any old file.

**PROPOSED isolation strategy:** Develop the new implementation under
`src/causaguard_v06/` and `tests_v06/`. The v0.52 identity validator hashes only
`src/causaguard/` and `tests/`; files under `causaguard_v06` and `tests_v06` are
outside those glob sets and do not change historical identity.

This approach requires:

1. `causaguard_v06` must be a separately installable package or importable module,
   not a submodule of `causaguard`.
2. The `pyproject.toml` must be extended to discover `causaguard_v06` only after the
   frozen v0.52 development report is re-validated against the existing identity.
3. Any `conftest.py` additions must not be placed inside `tests/`.

**Do not** weaken the v0.52 identity validator, modify the frozen development freeze,
or change any file under `src/causaguard/` or `tests/`.

---

## 3. Worked episodes: illustrative specification

The following episodes are **PROPOSED illustrative specifications**, not measured results.
Any numeric rates or costs are **ASSUMED** and require justification before use in
implementation.

### 3.1 Customer-support episode: verification adds value

**Public observation at episode start:**
```
ticket_age_hours = 52.0        # old enough to trigger rules_repair verify rule
conflict_alarm = 0.72          # above 0.5 threshold
source_reliability = 0.60      # moderate
queue_load = 0.30
deadline_hours = 2.0
verify_cost = 0.15
apply_cost = 0.05
escalation_cost = 0.25
time_cost_per_hour = 0.03
value = 1.20
harm = 0.80
budget = 2
```

**Hidden state (simulator only):**
```
record_correct = True          # the proposed update is actually safe
update_harmless = True
verification_lag = 0.3 hours
actual_fp_rate = 0.04
actual_fn_rate = 0.08
```

**Information before verification call:**
- Policy sees `conflict_alarm = 0.72` and `ticket_age_hours = 52.0` — both trigger
  the `rules_repair` threshold.
- Policy does NOT know `update_harmless = True`.
- `cost_rule` baseline estimates the expected utility of each action using the
  disclosed approximate prior and quoted error rates.

**After verification call (evidence returned to policy):**
```
evidence = {
    "flagged": False,              # verification did not flag (record is correct)
    "evidence_age_hours": 0.3,
    "check_type": "consistency"
}
```

**Policy decision after evidence:**
- `flagged = False` with moderate `source_reliability = 0.60`: probability of
  `update_harmless = True` increases. `cost_rule` baseline re-estimates action utilities;
  `proceed` becomes the highest-utility action under the risk limit.
- Always-verify-then-proceed: proceeds (always does so after verify).
- Rules_repair: proceeds (always escalates or proceeds; this branch proceeds).

**Terminal outcome:**
- `proceed` is called; access is authorized; `update_harmless = True`.
- `completed = 1`, `unsafe = 0`, `safe_completion = 1`.
- `cost = apply_cost + verify_cost + time_cost_per_hour × (latency after verify) ≈ 0.15 + 0.05 + 0.03 × 0.5 = 0.215` (**ASSUMED** latency).
- `utility ≈ 1.20 × 1 − 0.80 × 0 − 0.215 = 0.985`.

**Comparison with always-verify-then-escalate:** Would yield `utility = -escalation_cost = -0.25`. Verification added value here by confirming the record was correct, enabling a safe proceed.

**What this episode does NOT establish:**
- It is an illustrative specification, not a measured result.
- It does not show that any policy using verification evidence outperforms always-verify
  on average across the episode distribution.

### 3.2 Data-engineering episode: permission denial wins over favourable model output

**Public observation at episode start:**
```
data_age_hours = 12.0
schema_alarm = 0.30
source_quality = 0.85
pipeline_load = 0.20
column_count_changed = 1       # transformation changes column count
deadline_hours = 3.0
verify_cost = 0.12
apply_cost = 0.04
escalation_cost = 0.20
time_cost_per_hour = 0.02
value = 1.00
harm = 1.50
budget = 2
```

**Permission state (trusted, immutable):**
```
authorized = False             # agent does not have write permission
pipeline_scope_verified = True
confirmation_present = True
write_permitted = True
```

**Hidden state (simulator only):**
```
schema_correct = True
values_correct = True
transformation_safe = True     # the transformation would be safe if authorized
```

**Policy output (hypothetical learned model):**
- Model predicts low unsafe probability; suggests `proceed`.
- Policy selects `proceed`.

**Access result (independent grader):**
- `authorized = False` → `access denied`, `allowed = False`, `authorization_violation = 0`
  (a denied access is not a violation; the executor correctly refused).
- `blocked = 1`, `completed = 0`, `unsafe = 0`.
- `utility = -0.01 × 0 = 0.0` (blocked operations incur minimal accounting cost).

**Key point:** Even though `transformation_safe = True` (the transformation would have
been safe), the authorization denial is correctly enforced. The policy's favorable
predicted safety score does not override the permission layer. Zero authorization
violations are recorded. This is consistent with **OBSERVED** behavior in
`intervention_env.py` lines 152-177 and `grade_access` lines 210-222.

**What this episode illustrates:**
- Mandatory authorization checks operate independently of predicted safety or model
  output.
- A learned policy that correctly predicts safe outcomes still cannot bypass a
  permission denial.
- This is an engineering acceptance criterion, not a measured performance claim.

### 3.3 Customer-support episode: verification is too costly

**Public observation at episode start:**
```
ticket_age_hours = 10.0
conflict_alarm = 0.20
source_reliability = 0.90
queue_load = 0.15
deadline_hours = 0.4           # tight deadline
verify_cost = 0.35             # high verification cost
apply_cost = 0.03
escalation_cost = 0.15
time_cost_per_hour = 0.08      # high time cost
value = 0.60
harm = 0.40
budget = 2
```

**Cost_rule estimate (illustrative):**
- Latency after verify ≈ 0.3 (observation delay) + 0.2 (base) = 0.5 hours → exceeds
  deadline of 0.4 hours → `late = 1`, `completed = 0` after verify.
- Expected utility of verify ≈ `−verify_cost − time_cost × latency = −0.35 − 0.08 × 0.5 = −0.39`.
- Expected utility of proceed ≈ `value × (1 − estimated_risk) − harm × estimated_risk − apply_cost`.
  With low alarm and high source_reliability, estimated_risk ≈ 0.03. Estimated utility
  ≈ `0.60 × 0.97 − 0.40 × 0.03 − 0.03 ≈ 0.546`.
- `cost_rule` selects `proceed` without verify.

**Always-verify-then-proceed outcome:**
- Verify latency exceeds deadline → `late = 1`, `completed = 0`, `unsafe = 0`.
- `utility ≈ −verify_cost − time_cost × latency ≈ −0.39`.

**This episode demonstrates a regime where simple rules are competitive:**
- A deterministic rule that skips verification under tight deadlines and low alarm is
  expected to outperform always-verify-then-proceed.
- A learned policy that always verifies in this regime should underperform.
- **PROPOSED:** The evaluation must include parameter regimes where inexpensive rules
  are competitive, not only regimes designed for learned-policy wins (following handoff
  section 7, common contract, last bullet).

---

## 4. Engineering acceptance criteria

The following criteria must be met by the implementation before any experimental
evaluation is run. These are engineering fixture criteria, not confirmatory evidence.

### 4.1 Authorization independence

For every episode in every pilot domain, any access denial must be recorded as
`authorization_violation = 0` (a denial is not a violation; an unauthorized successful
access is). The independent grader must agree with the executor on every episode.
Any disagreement raises an error (following **OBSERVED** pattern at
`intervention_env.py` lines 214-221).

**Acceptance test:** Run 1,000 generated episodes with `denial_rate = 0.5` (stress
test). Assert `authorization_violation = 0` on all episodes. Assert grader agreement
on all episodes.

### 4.2 Evidence lifetime and isolation

Verify evidence must not be available to the policy before `verify` is called. After
`restore` or `proceed`, evidence from the same episode must not carry over to the next
episode. The policy input must contain only the public observation and, if verify was
called, the returned evidence object; nothing else.

**Acceptance test:** Assert that the policy input object contains no hidden-state fields
at any decision step. Assert that after a terminal action, the next episode starts with
no prior evidence.

### 4.3 Potential-outcomes accounting

For every episode, the simulator must compute outcomes for all four actions using the
same exogenous random tape. Policy evaluation order must not change any outcome.

**Acceptance test:** Evaluate all four actions on 100 episodes with two different
evaluation orders. Assert identical potential-outcome tables for both orders.

### 4.4 Grader-schema-semantic split (data-engineering pilot)

The independent grader must separately record schema correctness and semantic
correctness. A `schema_valid = True` from the evidence object must not be used by the
grader to infer `values_correct = True`.

**Acceptance test:** Generate episodes with `schema_correct = True` and
`values_correct = False`. Assert `schema_false_positive = 0` and
`content_false_negative = 1` on these episodes after a proceed action.

### 4.5 Historical identity preservation

After adding `causaguard_v06/` and `tests_v06/`, re-run the v0.52 identity check on
the existing frozen development report without any v0.52 source file changed. The
freeze seal must match the saved value:
`053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6`.

**PROPOSED:** This check must be run and recorded in the engineering work package's
fixture report before any experimental data are generated. It must not be replaced by
a manual assertion.

---

## 5. Fair baseline specification and tuning access

**All policies must receive equal:**
- Public observation fields at episode start
- Evidence object (if and only if `verify` was called in that episode)
- Action budget and feasibility constraints
- Cost accounting formula

**Tuning access rules (must be declared before development data are collected):**

| Baseline | Parameter source |
| --- | --- |
| `always_verify_then_proceed` | No parameters; purely structural |
| `rules_repair` | Thresholds set before outcome data; not fitted |
| `cost_rule` | Approximate failure-probability formula using public fields; parameters are disclosed; if estimated from data, development data only, never final-evaluation data |
| `always_escalate` | No parameters |
| `rules_proceed` | No parameters |
| Learned policy (Stage 2 only) | Fitted on training split only; risk threshold fixed before evaluation; calibration on calibration split only |
| Oracle | True latent state and random tape — simulator diagnostic only, never an evaluated policy |

**Regimes where simple rules should be competitive** (see episode 3.3 above) must be
included in the evaluation. The parameter distribution must not be engineered solely to
favour a learned policy.

---

## 6. Prospective protocol requirements (before any experimental data)

The following must be fixed and recorded before any outcome data are generated:

1. **Primary hypothesis:** Exact utility margin and direction, written as a one-sided
   inequality with stated alpha.
2. **Safety gate:** Exact absolute-risk bound and excess-risk bound versus always-verify,
   with stated alpha.
3. **Stopping rule:** Exact condition under which Stage 1 or Stage 2 is abandoned without
   final evaluation.
4. **Seed allocation:** All training, calibration, development, and final seeds, disjoint
   and recorded before any fitting.
5. **Number of training replicas and evaluation clusters:** With power analysis
   justification (see Section 7).
6. **Parameter values** for all baselines: failure-rate priors, cost distributions,
   risk limits, and alarm thresholds.
7. **Dating and locking:** All protocol decisions must be recorded with a dated local
   file and a verifiable hash before any development outcome is viewed. The method of
   dating and verification (local file hash, institutional repository, or other) must
   be specified. As documented in the v0.52 audit, an earlier proposal was noted as
   "Draft for human review" and its preregistration status was unverified. This must
   not recur: the protocol must be approved and locked in a verifiable way before any
   fitting or evaluation is run.

---

## 7. Compute estimate and power considerations

**PROPOSED** Stage 1 estimate (deterministic baselines only, no model fitting):

| Component | Count | Notes |
| --- | --- | --- |
| Pilot domains | 2 | Customer support, data engineering |
| Baselines per domain | 5 | always_verify, rules_repair, cost_rule, rules_proceed, always_escalate |
| Operational profiles | 4 | iid, verifier_shift, outage_shift, cost_shift |
| Development evaluation seeds | 6 | Following v0.5 convention |
| Final evaluation seeds | 6 | Disjoint from development |
| Episodes per seed | 250 | Following v0.5 convention (**ASSUMED**) |
| **Total Stage 1 policy-episode evaluations** | **2 × 5 × 4 × (6+6) × 250 = 120,000** | Development + final, no fitting |

**PROPOSED** Stage 2 estimate (learned policy added, conditional on Stage 1):

| Component | Count | Notes |
| --- | --- | --- |
| Training replicas | 5 | **ASSUMED** following v0.52 convention |
| Calibration datasets | 5 | One per replica |
| Forest fits per replica | 4 arms × 2 domains = 8 | If jointly trained across domains |
| **Total Stage 2 forest fits** | **5 × 8 = 40** | Plus 5 calibration sets per replica |

**Power note:** These counts are illustrative and require a prospective power analysis
before the protocol is locked. The power analysis must assess whether 5 training replicas
and the number of evaluation clusters provide adequate resolution for the stated primary
margin. As noted in the v0.52 protocol review:

> More bootstrap resamples do not substitute for more independent clusters. If the
> power analysis requires more independent clusters, the cluster count must increase,
> not the resample count.

**UNVERIFIED:** Whether 6 development clusters and 6 final clusters are sufficient for
the proposed primary margin. This must be established by the power analysis before the
study gate.

---

## 8. Historical replay preservation

**OBSERVED:** The v0.52 identity validator (`v052/study.py` lines 61-80) recursively
hashes all Python files under `src/causaguard/` and `tests/`. Adding files inside
those directories would change the execution identity of the historical v0.52 freeze.

**PROPOSED isolation strategy:** All new code for the next implementation work package
is placed under:
- `src/causaguard_v06/` (not `src/causaguard/`)
- `tests_v06/` (not `tests/`)
- `experiments_v06/` (not `experiments/`)

**PROPOSED historical snapshot strategy:** Before any new code is added, record the
current v0.52 freeze seal and the recursive hash of `src/causaguard/` and `tests/`.
After adding new code, re-verify that the freeze seal matches and that no file under
`src/causaguard/` or `tests/` has changed. This verification must be run and recorded
in the engineering fixture report.

**Do not** relax the v0.52 identity validator, alter the old freeze, or use a worktree
or branch operation to separate the historical snapshot — a branch operation during the
documentation task is prohibited by the handoff constraints.

---

## 9. What further literature evidence could reject this direction

**PROPOSED stop criteria for the foundation gate (handoff section 8.1):**

The proposed research direction should be narrowed or abandoned if any of the following
are found during the authorized literature review:

1. An existing method already solves the same observable decision problem (verify-then-
   decide with fallible evidence, under delay and cost) under comparable assumptions,
   and its benchmark already includes the proposed pilot domain mechanisms.
2. An existing benchmark already independently specifies two domain-specific mock
   workflows with the structural properties described in the pilot specifications
   (independent grader, permission independence, evidence-not-sufficient-for-safety
   property).
3. The proposed deterministic `cost_rule` baseline is already known to be near-optimal
   under the proposed failure model, making Stage 1 uninteresting.
4. The value-of-information literature already characterizes the conditions under which
   verify-then-decide beats a fixed macro, with theoretical guarantees that apply to
   the proposed observation and cost model.

A reproducible negative replication or benchmark characterization that establishes one
of these conditions remains scientifically valuable, even without a new algorithm.

---

## 10. What this plan does not establish

- **UNVERIFIED:** Whether `causaguard_v06` isolation is sufficient to preserve v0.52
  identity under all Python import resolution scenarios. This must be verified in the
  engineering work package.
- **UNVERIFIED:** Whether the proposed pilot domain structures are novel relative to
  existing sequential decision or value-of-information literature. The literature review
  must be completed before a novelty claim is made.
- **UNVERIFIED:** Whether Stage 2 (learning) is worth undertaking. Stage 1 must be
  completed first.
- **PROPOSED:** All structural and parametric claims above are design proposals. No
  code has been written, no test has been run, and no model has been fitted. This plan
  specifies what to do; it does not confirm that it has been done or that it will succeed.
- This plan does not change the v0.52 negative result or its concluded status. Final
  evaluation remains prohibited under the v0.52 freeze.


# Data-engineering pilot: staged transformation domain specification

Status: **PROPOSED**, post-result research foundations, 4 November 2026. This document
specifies a mock pilot domain for future benchmark design. It does not define a new
experimental result, authorise final evaluation, or describe currently implemented code.
Labels: **OBSERVED** = verified in this inspection; **PROPOSED** = future design;
**UNVERIFIED** = not independently confirmed; **ASSUMED** = illustrative value requiring
justification before use.

Source anchor: [intervention_env.py](../../src/causaguard/intervention_env.py) lines
1-274; [intervention_policy.py](../../src/causaguard/intervention_policy.py) lines
120-155; [causaguard-phd-next-step.md](../../../Users/rosha/Documents/Codex/2026-11-02/referenced-chatgpt-conversation-this-is-an/outputs/causaguard-phd-next-step.md)
sections 5-7; [evidence-map.md](evidence-map.md) O2, O5-O6; RQ2, RQ5-RQ6.

---

## 1. Motivation and design scope

**OBSERVED:** In the existing `intervention_env.py`, the two domain labels share the
same `Observation` type, the same `lookup_customer` access contract, and the same
outcome equation. Domain `1` ("data engineering") differs from domain `0` only via
additive coefficients on defect prevalence (`+0.06`, line 112) and retry repair
probability (`+0.12`, line 247). These are useful analogues but are not independently
specified transformation workflows with distinct state-transition models.

**PROPOSED design objective:** Specify a staged data-transformation workflow with its
own state variables, verification evidence type, failure modes, and outcome grader that
differ from the customer-support pilot in mechanism — not only in coefficient values.
Verification returns schema and content sample evidence to the policy before the next
decision. Authorization remains a separate, trusted check independent of evidence
content or predicted safety.

This specification must remain distinguishable from [customer-support-pilot.md](customer-
support-pilot.md) at every level of the domain model: different failure taxonomy, different
evidence structure, different repair semantics, and a different independent grader focus.
The handoff (section 7, Pilot B) requires that the difference be explained precisely.

---

## 2. Scenario and hidden state

### 2.1 Task description

**PROPOSED:** A data-engineering agent receives a request to apply a proposed
transformation to an in-memory staging dataset — for example, renaming columns,
coercing types, joining with a reference table, or applying a filtering rule. The agent
must decide whether to apply the transformation, verify the staging state, re-fetch or
restore the staging state, or escalate to a human data engineer, within a time and
operation budget. No real files or production systems are modified; all operations apply
to in-memory mock state.

### 2.2 Public observation (what the policy sees)

The policy receives a fixed observation at episode start. All fields are observable
without an additional tool call:

| Field | Type | Description |
| --- | --- | --- |
| `data_age_hours` | float | Hours since the staging dataset was last refreshed (0–96, **ASSUMED**) |
| `schema_alarm` | float ∈ [0,1] | Automated signal that a schema inconsistency may be present |
| `source_quality` | float ∈ [0,1] | Quoted reliability of the upstream data source |
| `pipeline_load` | float ∈ [0,1] | Current pipeline queue occupancy fraction |
| `column_count_changed` | int ∈ {0,1} | Whether the proposed transformation changes the number of columns |
| `deadline_hours` | float | Remaining SLA time for this transformation job |
| `apply_cost` | float | Estimated cost of applying the transformation |
| `verify_cost` | float | Estimated cost of running a schema-and-sample validation check |
| `escalation_cost` | float | Estimated cost of escalating to a human data engineer |
| `restore_cost` | float | Estimated cost of restoring the staging state from the last checkpoint |
| `time_cost_per_hour` | float | Per-hour latency penalty |
| `value` | float | Utility gain if the transformation is correctly applied |
| `harm` | float | Penalty if the transformation is incorrectly applied (data corruption) |
| `budget` | int ∈ {1,2} | Maximum permissible staging-access operations in this episode |

**No field discloses the latent correctness of the staging data, the true failure type,
or the simulator's random draws.**

### 2.3 Hidden state (simulator only)

| Variable | Description |
| --- | --- |
| `schema_correct` | Whether the current staging dataset has a valid schema (bool) |
| `values_correct` | Whether the data values are semantically correct (bool) |
| `metadata_current` | Whether the staging metadata reflects the current dataset state (bool) |
| `transformation_safe` | Whether applying the proposed transformation would be semantically correct (bool) |
| `validation_lag_hours` | Delay before verification evidence reflects current staging state (float, **ASSUMED** 0–2) |
| `actual_schema_fp_rate` | True false-positive rate of schema validation for this episode |
| `actual_content_fn_rate` | True false-negative rate of content sampling for this episode |
| `draws` | Fixed exogenous random tape (8 uniforms); consumed in fixed arm order |

As in the customer-support pilot, all hidden state is generated once per episode and
held constant across all policy arms evaluated on the same episode (paired-randomness
design, **OBSERVED** `intervention_env.py` lines 96-148).

### 2.4 Permission state (trusted, immutable)

**OBSERVED pattern:** Permission fields are fixed at episode generation, independent of
model output. For this pilot:

| Permission field | Description |
| --- | --- |
| `authorized` | Agent has permission to modify this staging dataset |
| `pipeline_scope_verified` | The transformation is within the agent's declared pipeline scope |
| `confirmation_present` | Mandatory confirmation token is present for a destructive operation |
| `write_permitted` | ACL permits write access to the staging area |
| `revoke_after_attempts` | Optional: access revoked after this many attempts (None = unlimited) |

A denial is introduced at episode generation with **ASSUMED** probability 0.10. Denial
reasons include missing confirmation, out-of-scope operation, pipeline-scope mismatch,
write denial, wrong dataset identifier, an invalid extra field, or mid-episode revocation.

**Authorization is never bypassed by predicted safety, schema evidence, or model
confidence.** Verification evidence cannot grant write access.

---

## 3. Action space and feasibility

The same four-action vocabulary is used to maintain a shared reporting schema:

| Action | Description | Budget cost |
| --- | --- | --- |
| `proceed` | Apply the proposed transformation to in-memory staging state | 1 operation |
| `restore` | Restore the staging state from the last checkpoint; episode ends | 2 operations |
| `verify` | Run schema and content-sample validation; returns observable evidence before next decision | 2 operations |
| `escalate` | Transfer to a human data engineer; episode ends immediately | 0 operations |

> [!NOTE]
> The existing simulator uses `retry` as the second non-terminal action. This pilot uses
> `restore` instead, with a distinct transition model: `restore` rolls back to a
> checkpoint rather than re-fetching from an upstream source. This is a structural
> difference from the customer-support pilot's `retry` action, which refreshes the
> upstream record. The vocabulary mapping is `restore → retry` in the shared reporting
> schema; the semantic model differs.

**PROPOSED key difference from the existing simulator:** `verify` returns a structured
evidence object to the policy before the policy takes its next action. The policy may
then choose `proceed`, `restore`, or `escalate`. This is the same post-verify decision
structure as the customer-support pilot, applied here to a transformation context.

---

## 4. Verification mechanics

### 4.1 Evidence returned

When the policy selects `verify`, the simulator generates and returns:

```
evidence = {
    "schema_valid": bool,           # whether the staging schema passed validation
    "sample_pass_rate": float,      # fraction of content samples that passed semantic checks
    "validation_timestamp_lag": float,  # hours between staging update and this validation
    "check_type": "schema+sample"   # fixed label for this pilot
}
```

`schema_valid` reflects the previous staging schema state, affected by `validation_lag_hours`.
`sample_pass_rate` is a noisy summary of `values_correct`: it equals approximately
`(1 - actual_content_fn_rate)` when values are incorrect and approximately
`(1 - actual_schema_fp_rate)` when values are correct, with additive noise from the
random tape.

**Key distinction from customer-support verification:** Passing a schema check alone
does not imply that data values are semantically correct (`values_correct` can be False
while `schema_valid` is True). This is a structural difference, not merely a different
coefficient: a policy that treats `schema_valid = True` as sufficient evidence for
`proceed` may still produce harmful transformations. The grader scores both schema and
semantic correctness independently.

### 4.2 Repair is NOT automatic

**PROPOSED:** Verification does not automatically apply any fix. The subsequent policy
decision determines whether to apply the transformation (`proceed`), restore the staging
state (`restore`), or escalate. This matches the customer-support pilot's separation of
verification from repair.

### 4.3 Evidence lifetime

Evidence from `verify` is valid for the same episode only. If `restore` is called after
`verify`, the restored staging state is a new draw; the policy does not accumulate
evidence across episodes.

---

## 5. Transition model and outcome grading

### 5.1 State transitions

| Start state | Action | Successor condition |
| --- | --- | --- |
| Initial | `proceed` | Transformation applied; episode ends |
| Initial | `verify` | Evidence returned; episode continues if budget ≥ 2 |
| After-verify | `proceed` | Transformation applied; episode ends |
| After-verify | `restore` | Staging state restored to checkpoint; episode ends |
| After-verify | `escalate` | Deferred to human; episode ends |
| Initial | `restore` | Staging state restored to checkpoint; episode ends |
| Initial | `escalate` | Deferred to human; episode ends |
| Budget exhausted | (any feasible) | Only `escalate` permitted |

### 5.2 Outcome computation

**PROPOSED** outcome fields, graded by the simulator independently of the policy:

| Field | Definition |
| --- | --- |
| `completed` | 1 if transformation is applied within deadline and passes grader checks |
| `unsafe` | 1 if `completed = 1` and the transformation was semantically incorrect (`transformation_safe = False`) |
| `safe_completion` | `completed AND NOT unsafe` |
| `cost` | Sum of action costs plus `time_cost_per_hour × latency_hours` |
| `utility` | `value × completed − harm × unsafe − cost` |
| `late` | 1 if resolution latency exceeds `deadline_hours` |
| `blocked` | 1 if the access attempt was denied by the permission layer |
| `authorization_violation` | 1 if any access succeeded that the independent grader would deny |
| `verified` | 1 if `verify` was called this episode |
| `schema_false_positive` | 1 if `schema_valid = True` from evidence but `schema_correct = False` |
| `content_false_negative` | 1 if `sample_pass_rate` above threshold but `values_correct = False` |
| `evidence_used` | 1 if `verify` was called before `proceed` |

**Escalation outcome:** `completed = 0`, `unsafe = 0`, cost equal to `escalation_cost`.
No invented human-resolution benefit (matching the **OBSERVED** pattern at
`intervention_env.py` line 241).

**Restore outcome:** `completed = 0`, no transformation applied, cost equal to
`restore_cost + time_cost_per_hour × restore_latency`. The staging state is returned to
its checkpoint, which is semantically correct but loses the proposed transformation.

### 5.3 Independent access grading — schema and semantic split

The independent grader in this pilot separately assesses:

1. **Authorization:** Was the write access independently permitted? (Same method as
   the existing `grade_access` function, **OBSERVED** lines 210-222.)
2. **Schema correctness:** Was the staging schema valid at the time `proceed` was
   called? This is assessed from the hidden `schema_correct` variable, not from the
   `schema_valid` evidence field.
3. **Semantic correctness:** Were the data values correct at the time `proceed` was
   called? This is assessed from the hidden `values_correct` variable, not from
   `sample_pass_rate`.

A transformation may be authorized and schema-valid but semantically incorrect. The
grader records all three dimensions separately. This three-way split is structurally
distinct from the customer-support grader, which assesses only authorization and
record-level correctness.

### 5.4 All-arm supervision

The simulator records potential outcomes for all four actions on every episode. These
support controlled policy comparisons but do not solve observational causal
identification (**OBSERVED** in evidence-map.md, O5).

---

## 6. Failure taxonomy

This pilot introduces four distinct failure types with different detection and recovery
profiles. All are hidden state variables:

| Failure type | Hidden variable | Detection by verify | Recovery by restore | Recovery by proceed |
| --- | --- | --- | --- | --- |
| Schema mismatch | `schema_correct = False` | High (detected by `schema_valid`) | Yes (restores to valid checkpoint) | No (transformation fails or corrupts) |
| Value corruption | `values_correct = False` | Partial (detected by `sample_pass_rate`, but not guaranteed) | Yes | No |
| Metadata delay | `metadata_current = False` | Partial (detected by `validation_timestamp_lag`) | Possibly (depends on lag duration) | Risky (may apply stale transformation) |
| Transient processing failure | `transformation_safe = False` despite correct schema and values | No (not visible in schema/sample evidence) | No | No (transformation is structurally unsafe regardless of data state) |

**PROPOSED structural property:** Verification can detect schema mismatch with high
reliability and value corruption with partial reliability. It cannot reliably detect
transient processing failure or metadata delay beyond the timestamp lag. This means a
policy that always verifies and always proceeds when `schema_valid = True` can still
produce harmful transformations. This is a mechanistic distinction from the customer-
support pilot, where `flagged = True` from verification is the primary evidence signal.

---

## 7. Operational profiles

**PROPOSED** four profiles following the existing structure:

| Profile | Description |
| --- | --- |
| `iid` | Nominal episode distribution |
| `verifier_shift` | Schema validation false-positive and content sampling false-negative rates increase by a fixed additive shift (simulating verifier degradation) |
| `outage_shift` | Staging restore availability decreases (simulating checkpoint loss or storage failure) |
| `cost_shift` | Apply and verify costs scaled up by a fixed multiplier (simulating compute cost inflation) |

---

## 8. Baseline suite

All baselines receive the same public observation fields, the same episode budget, and
the same action feasibility constraints. No baseline has access to hidden state.

| Baseline | Description | Parameter disclosure |
| --- | --- | --- |
| `always_verify_then_proceed` | Always call `verify`; always `proceed` after (if budget permits, else `escalate`) | None; purely structural |
| `rules_repair` | `verify` if `schema_alarm > 0.5` or `data_age_hours > 48`; else `proceed`; never `restore` | Thresholds set before outcome data; not fitted |
| `cost_rule` | Deterministic evidence-contingent rule: estimate expected utility of each action using public fields and quoted error rates; select highest under risk limit; re-evaluate after `verify` using returned evidence (schema_valid, sample_pass_rate) | Approximate prior on failure probability (**ASSUMED** 0.04 + age/96 × 0.28 + 0.05 × schema_alarm), quoted source_quality; parameters are disclosed and not fitted to outcomes |
| `always_escalate` | Always escalate | None |
| `rules_proceed` | Always proceed (unsafe lower bound, not deployable) | None |
| `oracle` | Selects the action with the highest true potential outcome | Latent state and random tape — simulator diagnostic only |

**PROPOSED:** The `cost_rule` baseline in this pilot updates its action estimate after
`verify` by incorporating the returned `schema_valid` and `sample_pass_rate` signals,
using the disclosed approximate failure-probability model. This is the strongest
deterministic evidence-contingent comparator and must be computed before any learned
policy result is examined.

---

## 9. How this pilot differs from the customer-support pilot

This section fulfils the handoff requirement (section 7, Pilot B) to explain the
difference precisely, beyond names and coefficients.

| Dimension | Customer-support pilot | Data-engineering pilot |
| --- | --- | --- |
| Task | Record correctness and ownership resolution | Staged in-memory data transformation |
| Primary failure modes | Contradictory records, stale ownership, temporary lookup failure, incorrect proposed resolution | Schema mismatch, value corruption, metadata delay, transient processing failure |
| Verification target | Record consistency with stated source reliability | Schema validity AND content sample semantics (two separate checks) |
| Evidence structure | `{flagged: bool, evidence_age_hours: float, check_type: "consistency"}` | `{schema_valid: bool, sample_pass_rate: float, validation_timestamp_lag: float, check_type: "schema+sample"}` |
| Schema pass ⇒ safe? | Not applicable (no schema check) | **No.** Schema validity does not imply value correctness; grader scores both independently |
| Repair mechanism | `proceed` applies a record update; correctness depends on `update_harmless` | `proceed` applies a transformation; correctness depends on both `schema_correct` AND `values_correct` AND `transformation_safe` |
| Non-terminal second action | `retry`: re-fetches the upstream record (new external draw) | `restore`: reverts staging state to checkpoint (no new draw; known-correct but loses proposed transformation) |
| Escalation meaning | Deferred to human specialist | Reverts to checkpoint state; ticket raised for data engineering team |
| Independent grader focus | Authorization + record-level correctness (1 binary outcome) | Authorization + schema correctness + semantic correctness (3 separate assessments) |
| Failure detection ceiling | High (consistency flag covers main failure type) | Partial (content failures not fully detected by schema check; transient processing failure not detectable) |
| Structural invariant | Verify-then-proceed can eliminate most unsafe completions if `flagged` is reliable | Verify-then-proceed cannot eliminate all unsafe completions (transient processing failure is undetectable by verify) |

The last row is the key structural difference: in the customer-support pilot, an ideal
verifier would eliminate all unsafe completions. In the data-engineering pilot, there
exists a failure type (`transformation_safe = False` despite correct schema and values)
that cannot be detected by any verification call. This creates a different policy
problem: the optimal policy must weigh the cost of verify against partial detection
coverage, knowing that some failures are undetectable.

This difference must be preserved in any implementation. It is not achieved by using
different coefficients on a shared equation.

---

## 10. Unresolved design decisions

The following must be fixed before implementation, using development data or domain
knowledge only:

1. **Failure-rate priors:** Base rates for `schema_correct = False`, `values_correct =
   False`, `metadata_current = False`, and `transformation_safe = False`. These are
   structurally independent and must be separately estimated. **ASSUMED** illustrative
   values in the range 0.03–0.15 per failure type; all require justification.
2. **Detection probabilities:** The fraction of content failures detected by sample
   validation at a given `sample_pass_rate` threshold. Must be specified before
   outcome data are collected.
3. **Transient failure rate:** The base rate of `transformation_safe = False` given
   correct schema and values. **ASSUMED** 0.02–0.05 (**ASSUMED**); requires justification.
4. **Validation lag distribution:** How often `validation_timestamp_lag > 0` affects
   schema detection.
5. **Restore availability:** The probability that the checkpoint is available under
   nominal vs. `outage_shift` conditions.
6. **Cost ranges:** The distributions of `apply_cost`, `verify_cost`, `restore_cost`,
   and `escalation_cost`. Illustrative: `verify_cost ∈ [0.06, 0.50]` following the
   existing simulator (**OBSERVED** line 121); re-justify for this domain.
7. **Sample pass-rate threshold for cost_rule:** The threshold on `sample_pass_rate`
   that the `cost_rule` baseline uses to identify content failure. Must be disclosed
   and not fitted to outcome data.
8. **Risk limit for cost_rule:** Fixed and disclosed before data collection.
9. **Episode count, replica count, and cluster count:** Fixed in the protocol with a
   power analysis before the study gate.

---

## 11. What this specification does not establish

- **UNVERIFIED:** Whether this workflow is externally valid for real data-engineering
  systems. It is a mock specification.
- **UNVERIFIED:** Whether the assumed failure rates match any empirical distribution.
- **UNVERIFIED:** Whether the proposed evidence structure for schema-and-content
  validation maps to real validation tooling.
- **UNVERIFIED:** Whether separating verify from automatic repair is novel relative to
  existing sequential decision or value-of-information literature
  (see [literature-review-protocol.md](literature-review-protocol.md)).
- **UNVERIFIED:** Whether a learned policy trained in this domain transfers to the
  customer-support domain or any real-world deployment context.
- **PROPOSED:** All structural and parametric claims above are design proposals, not
  implemented results. Implementation and testing require a separate authorized
  engineering work package passing the domain gate described in the handoff (section 8).


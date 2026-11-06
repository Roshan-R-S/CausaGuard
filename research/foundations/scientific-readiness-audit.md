# Scientific readiness audit: CausaGuard v0.6 research-foundations package

Status: **AUDIT**, post-result, documentation-only, 4 November 2026. This document
assesses the five research-foundation documents and the proposed v0.6 implementation
plan for scientific readiness. It is not a preregistration, a new experimental result,
or authorization for any evaluation, implementation, or branch operation.

**Sources audited** (by label used in foundation documents):

| Label | File | Lines read |
| --- | --- | --- |
| EM | `research/foundations/evidence-map.md` | 1–80 |
| LR | `research/foundations/literature-review-protocol.md` | 1–90 |
| CS | `research/foundations/customer-support-pilot.md` | 1–403 |
| DE | `research/foundations/data-engineering-pilot.md` | 1–385 |
| IP | `research/foundations/next-implementation-plan.md` | 1–472 |
| ENV | `src/causaguard/intervention_env.py` | 1–274 |
| POL | `src/causaguard/intervention_policy.py` | 1–190 |
| V52 | `src/causaguard/v052/study.py` | lines 25-79 (hash identity) |
| PY | `pyproject.toml` | complete |

Roadmap PDF was confirmed present at
`C:/Users/rosha/Downloads/CausaGuard_PhD_Research_Master_Roadmap_2026.pdf`.
Its content was not re-read in this audit; claims attributed to it are taken from EM.

---

## 1. Issue register

Severity scale:
- **CRITICAL:** Would invalidate results, produce systematic errors, or block
  implementation if unresolved before proceeding.
- **MAJOR:** Would weaken inference, introduce ambiguity in comparison, or require
  substantial redesign.
- **MINOR:** Precision gap, editorial ambiguity, or forward-looking note; does not
  block current stage but must be resolved before the study gate.

---

### CRITICAL issues

---

**C-01: Budget arithmetic is infeasible for multi-step episodes in both pilots**

*Source:* CS §3 (action table) and §5.1 (transition table); DE §3 (action table) and
§5.1 (transition table).

*Finding:* Both pilots assign `verify` a cost of **2 operations** and assign the
second non-terminal action (`retry` in CS, `restore` in DE) a cost of **2 operations**.
The maximum episode budget is `int ∈ {1, 2}` (CS §2.2 field `budget`; DE §2.2 field
`budget`). Yet both transition tables include the row `After-verify → retry/restore →
episode ends`, which would require 2 + 2 = 4 operations against a maximum of 2.

This is an internal contradiction that makes the proposed episode model impossible to
implement as written. Either:

(a) `verify` must cost 1 operation (not 2), so that verify + one subsequent action
    fits in budget 2; or
(b) the subsequent action after verify (`retry`/`restore`) must cost 0 or 1 operation;
    or
(c) the budget range must be extended to at least 4 (e.g., `{1, 2, 3, 4}`); or
(d) the `After-verify → retry/restore` row must be removed, restricting the action
    space after verify to `{proceed, escalate}` only.

The existing simulator charges 2 operations for `verify` and `retry` as single macros
where the budget contract is applied to the whole macro (ENV lines 162-163). The new
pilot design changes `verify` into a sequential step, which requires a different budget
accounting. The plan does not resolve this.

The worked episode in IP §3.1 compounds the confusion: it states "cost = apply_cost +
verify_cost + time_cost × latency ≈ 0.215" with both `verify` and `proceed` called
in one episode with budget 2 — but only assigns 1 implicit operation to `verify` in
the narrative. The action table says 2.

*Required resolution:* Restate the budget semantics explicitly. Define the cost of
`verify` as a sequential evidence-acquisition step (likely 1 operation), and state
separately what budget is consumed by the subsequent terminal action. The transition
table and the worked episode must be mutually consistent.

*Readiness gate:* Domain gate cannot be declared open until this is resolved.

---

**C-02: `pyproject.toml` is hashed by v0.52 identity; adding `causaguard_v06` to it
breaks historical identity**

*Source:* V52 line 75: `"pyproject": file_hash(ROOT / "pyproject.toml")`. IP §2.1,
§2.2, and §8.

*Finding:* The implementation plan proposes extending `pyproject.toml` to discover
`causaguard_v06` (IP §2.2, item 2: "The `pyproject.toml` must be extended…"). The
v0.52 identity function hashes `pyproject.toml` itself in addition to `src/causaguard`
and `tests`. Therefore, **any edit to `pyproject.toml` changes the v0.52 identity
hash**, even if no source file inside `src/causaguard/` is touched.

The plan correctly notes that adding files inside `src/causaguard/` or `tests/` breaks
historical identity, and proposes `causaguard_v06/` as the isolation. But it does not
address the `pyproject.toml` hash. The plan's statement "files under `causaguard_v06`
and `tests_v06` are outside those glob sets and do not change historical identity"
(IP §2.2) is **incomplete**: modifying `pyproject.toml` to register the new package
still breaks identity.

*Required resolution:* Either:
(a) `causaguard_v06` must be installable or importable without editing `pyproject.toml`
    (e.g., via `PYTHONPATH` or a separate `pyproject_v06.toml`); or
(b) The plan must acknowledge that editing `pyproject.toml` invalidates the v0.52
    identity check, and must propose how to preserve historical verifiability (e.g.,
    snapshotting the frozen hash set before any `pyproject.toml` edit, or accepting
    that the freeze remains verifiable via its own saved hash record even if the
    current file differs).

The engineering acceptance criterion IP §4.5 (re-run v0.52 identity check and assert
freeze seal matches) cannot pass if `pyproject.toml` has been edited, because the saved
freeze includes the old `pyproject.toml` hash. This acceptance criterion is therefore
currently unachievable as stated.

*Readiness gate:* Engineering gate cannot be opened until this is explicitly resolved.

---

**C-03: No primary hypothesis quantified; no power analysis performed**

*Source:* IP §6 (prospective protocol requirements), §7 (compute estimate), EM RQ1.

*Finding:* IP §6 lists "exact utility margin and direction, written as a one-sided
inequality with stated alpha" as requirement 1 — but does not state what that margin
is. No provisional margin is proposed, even as a placeholder requiring justification.
Similarly, item 5 requires a power analysis but provides none.

This is not a matter of deferring to a later document: the plan is itself the foundation
document. Without a provisional primary effect size and alpha, there is no basis for
assessing whether 6 development clusters and 6 final clusters are adequate (the plan
acknowledges this explicitly but does not resolve it: "UNVERIFIED: Whether 6 development
clusters and 6 final clusters are sufficient", IP §7).

v0.52 required lower bound > +0.020. v0.5 required > +0.01. For Stage 1 (deterministic
baselines only), the relevant margin is not stated at all — it is not clear what
difference between `cost_rule` and `always_verify_then_proceed` would constitute a
scientifically meaningful result.

Absent a provisional margin, the sample size calculation in IP §7 (120,000 policy-
episode evaluations for Stage 1) is not scientifically justified — it is a replication
of the v0.5 convention without any margin-based derivation.

*Required resolution:* Before the study gate, state a provisional primary margin and
alpha for Stage 1. Conduct a power analysis over a grid of realistic margins using the
proposed cluster structure, explicitly asking: how small a margin would remain
undetectable with these clusters? If the smallest scientifically interesting margin is
undetectable, the cluster count must increase.

*Readiness gate:* Study gate cannot be declared open until this is resolved.

---

**C-04: `cost_rule` baseline in both pilots uses ASSUMED priors that may be tuned
during development — tuning access policy is inconsistently specified**

*Source:* CS §7 (`cost_rule` description: "Approximate prior on defect rate (ASSUMED
0.04 + age/96 × 0.28)… parameters are disclosed; if estimated from data, development
data only"); DE §8 (identical note). IP §5 (baseline tuning access table).

*Finding:* The `cost_rule` baseline is the strongest deterministic comparator and the
pivotal Stage 1 reference. Its failure-probability priors (illustrative: `base 0.04 +
age_decay 0.28 + domain_offset 0.05`) are listed as **ASSUMED** in both pilots, with a
parenthetical "if estimated from data, development data only."

This introduces a critical ambiguity: if `cost_rule` parameters are estimated from
development data, then `cost_rule` has data-fitted parameters, and comparing it to a
Stage 2 learned policy (which also uses development data) conflates baseline and
candidate tuning access. If `cost_rule` parameters are fixed without development data,
the ASSUMED values may be systematically miscalibrated relative to the true simulator
generative process, creating an artificially weak comparator.

Neither path is explicitly resolved. The statement "parameters are disclosed and not
fitted to outcomes" (CS §7) contradicts the qualifier "if estimated from data,
development data only" (same section). One of these must be chosen and stated before
any development data are collected.

Additionally: `cost_rule` re-evaluates after `verify` using returned evidence (CS §7,
DE §8) — but no formula is stated for how `schema_valid` and `sample_pass_rate` update
the probability estimate. Without this formula, `cost_rule` is under-specified and
cannot be reproduced.

*Required resolution:* Decide before development data are collected whether `cost_rule`
parameters are fixed (and state exact values and their justification source) or fitted
on development data only (and state the exact fitting procedure and what data it may
see). State the exact Bayesian or heuristic update formula used after `verify`. Document
this in the study protocol.

*Readiness gate:* Study gate cannot be opened until this is resolved.

---

### MAJOR issues

---

**M-01: Novelty of the proposed research question is UNVERIFIED and may be fully
covered by existing sequential VOI or POMDP literature**

*Source:* EM O1, O4; LR search families; IP §9 (stop criteria 3 and 4).

*Finding:* The core proposed question — "when does acting on a fallible verification
result improve utility compared with a fixed macro, and can a learned controller improve
on deterministic rules?" — is precisely the subject of:
- Sequential value-of-information theory (Myerson 1979; Blackwell 1953 sufficiency;
  Duff 2002 value-function-based VOI in POMDPs)
- Myopic VOI approximations in Bayesian decision theory
- Finite-horizon POMDPs with costly observations

The literature-review protocol lists these as UNVERIFIED discovery leads (LR, search
families Q1-Q2). None of the 17 candidate papers has been screened or extracted. The
handoff explicitly states that the direction must survive comparison with existing work
before being called novel, and IP §9 names four stop criteria including "value-of-
information literature already characterizes the conditions."

If the proposed Stage 1 question is answered by existing theory, then Stage 1 produces
a replication/confirmation (which may still be valuable), not a new contribution. Stage
2 (learning) has even less novelty support. Neither EM, the pilot docs, nor IP attempts
to distinguish the proposed formulation from POMDP VOI beyond asserting that "mock
workflows" and "authorization boundaries" are the differentiating factors.

The authorization independence (RQ6) is a potentially distinct contribution, but its
treatment in the existing code (zero violations in a controlled fixture) does not
establish it as a research contribution beyond a correctness property.

*Required resolution:* Complete the literature review (at minimum Q1-Q4 of LR) before
opening the foundation gate. If existing theory fully characterizes Stage 1, revise the
proposed question to identify what remains genuinely open: for example, an empirical
characterization of which parameter regimes favour evidence-contingent actions, combined
with an independently graded benchmark.

*Readiness gate:* Foundation gate cannot be declared open until this is resolved.

---

**M-02: The two pilots share a nearly identical generative template and risk identical
coefficient-swap reduction**

*Source:* CS §11 (identity table); DE §9 (identity table); ENV lines 111-112, 247.

*Finding:* Both pilots are designed to avoid "coefficient-swap reduction" (CS §11: "If
the two pilots can be interchanged by swapping coefficients, the domain gate is not
satisfied"). The identity tables are correct at the specification level: `restore`
differs from `retry` semantically; `schema + content` evidence differs from `flagged`
evidence; the data-engineering grader has three dimensions vs. one.

However, several structural parallels risk converging to near-identical implementations:

1. Both pilots use the same 14-field public observation with the same field types;
   only the field names change. The generative model (age, load, alarm, quality, costs)
   is proposed to be nearly identical.
2. Both use the same `SeedSequence([seed, profile_index, episode_index])` generation,
   the same `MockState(seed=index)` permission fixture, and the same 8-uniform draw
   tape — directly copied from ENV.
3. The `cost_rule` formula in both pilots uses `0.04 + age/96 × 0.28 + domain_term`
   — the same functional form as `intervention_policy.py` lines 130-131.
4. The `verify` latency model is proposed as `observation_delay + 0.2 + 0.25 × flag`
   (identical to ENV line 251, 261).

If the implementation maps the two pilots to the same `EnvironmentConfig`-equivalent
with different coefficients, the domain gate will fail. The pilots must demonstrate
structural differentiation at the generative-process level, not only in the grader.

*Required resolution:* Before implementation, write transition equations for each pilot
separately, showing different state-space variables and different causal mechanisms.
For the data-engineering pilot: the four hidden variables (`schema_correct`,
`values_correct`, `metadata_current`, `transformation_safe`) must be generated by
distinct stochastic processes, not a single Bernoulli draw. Their joint distribution
and conditional independence assumptions must be stated explicitly.

*Readiness gate:* Domain gate cannot be declared open until joint distributions for all
hidden variables are specified in both pilots.

---

**M-03: `retry` in the customer-support pilot is semantically and statistically
under-specified**

*Source:* CS §5.1 (transition table); CS §5.2 (retry outcome); CS §3 (action table).

*Finding:* In the transition table, "Initial → retry → Record re-fetched; episode
ends." The retry outcome is: `completed = 0` (no update applied), cost =
`retry_cost + time_cost × retry_latency`. But:

1. **What is `retry_latency`?** It is never defined in the customer-support pilot (the
   existing simulator uses `0.25 + o.load`, ENV line 245, but the pilot does not
   adopt this formula explicitly).
2. **Does `retry` generate a new evidence draw?** The text says "refreshed record is
   a new draw" only in the context of `After-verify → retry`. For initial `retry`,
   the outcome is stated as `completed = 0` with no update applied. But retry is
   *supposed* to re-fetch the external record. If `completed = 0` always, `retry` is
   dominated by `escalate` (which also has `completed = 0` but zero latency cost).
   Under what conditions would any rational policy choose `retry`?
3. **The baseline suite for the customer-support pilot does not include `retry` in
   any baseline.** `rules_repair` uses only `verify` or `proceed`; `cost_rule`
   description does not mention computing expected utility for `retry`. Yet `retry` is
   in the action space. If it is never used by any baseline and always produces
   `completed = 0`, it is a dominated action with no expected value. Its inclusion
   complicates statistical accounting (all-arm potential outcomes) without scientific
   contribution.

*Required resolution:* Either (a) specify under what conditions `retry` can produce
`completed = 1` (e.g., retry re-draws the hidden state with some recovery probability
as in ENV line 247), or (b) remove `retry` from the customer-support pilot action space
and reconcile with the shared action vocabulary requirement. If (a), state the exact
recovery mechanism and latency formula.

---

**M-04: The data-engineering pilot's `transformation_safe` failure type is an
undetectable hazard whose base rate must be justified, not just ASSUMED**

*Source:* DE §6 (failure taxonomy table, row 4); DE §10 (item 3: "ASSUMED 0.02–0.05").

*Finding:* `transformation_safe = False` despite correct schema and values represents a
failure that cannot be detected by any verification call. This is the mechanistically
interesting property that distinguishes the data-engineering pilot from the customer-
support pilot (DE §9, last row). However, it creates a significant statistical hazard:

1. If the base rate of `transformation_safe = False` is non-zero, then
   `always_verify_then_proceed` will always incur some `unsafe` outcomes regardless of
   verification quality. This makes the absolute-risk gate for any policy that uses
   `proceed` dependent on the ASSUMED base rate.
2. If the ASSUMED rate is miscalibrated, the risk gate threshold (which must be set
   before outcome data are collected) may be impossible to pass (if rate is too high)
   or trivially easy (if rate is near zero).
3. The assumed range 0.02–0.05 is wide enough that the difference in expected `unsafe`
   rates across policies could be dominated by this parameter, not by the policy's
   evidence-based decisions.

No external justification is offered for 0.02–0.05. The text says it "requires
justification" but does not specify what source of justification is acceptable or what
would constitute a sufficient justification.

*Required resolution:* Before the study gate, obtain either (a) a domain-knowledge
estimate with an explicit source (not from simulator outcomes) or (b) a theoretical
argument for the range. Conduct a sensitivity analysis over the full range to assess
whether the primary safety gate thresholds remain achievable across the range. If the
undetectable failure rate renders any policy incapable of passing the absolute-risk gate,
the pilot design must be revised.

---

**M-05: Stage 1 comparison has a logical gap — it cannot distinguish decision-structure
value from generative-model differences**

*Source:* IP §1 (narrow research question); IP §3.3 (regime where simple rules are
competitive); EM RQ2.

*Finding:* Stage 1 asks: "Does separating verify from automatic repair and exposing
evidence to a subsequent decision improve utility compared with the existing macro?"
But the new pilots do not implement the existing macro on the new generative model.
The comparison would be between:
- New policy (verify-then-decide) on new generative model (CS or DE pilot)
- Existing macro (`verify` from ENV) on old generative model

This is a confound: any observed difference could be due to the decision structure, the
generative model, the domain specification, or any combination. A fair Stage 1 comparison
requires the new decision structure **and** the fixed macro to be implemented and
evaluated on **the same generative model** (the new pilot). Otherwise, Stage 1 cannot
answer its stated question.

The plan does not propose implementing an "always-verify-and-auto-repair macro" baseline
on the new pilot generative model. The `always_verify_then_proceed` baseline is not the
same as the existing macro: the existing macro auto-repairs after a flag; the proposed
baseline always proceeds regardless of the evidence.

*Required resolution:* Add an explicit baseline that replicates the existing macro's
decision logic (verify → if flagged, attempt repair and proceed; if not flagged, proceed)
on the new pilot generative model. Only a fair same-model comparison isolates the
decision-structure contribution.

---

**M-06: Preregistration mechanism is specified as "verifiable hash" but no concrete
procedure is defined**

*Source:* IP §6 item 7 ("method of dating and verification … must be specified"); EM
validation provenance §72-76.

*Finding:* The plan states that the protocol must be "approved and locked in a verifiable
way before any fitting or evaluation is run" and that the method must be specified — but
does not specify it. As documented in the v0.52 audit, the earlier protocol was noted
as "Draft for human review" and its preregistration status was unverified. The plan
explicitly references this problem ("this must not recur") but does not define what
would constitute compliant locking.

Specifically:

1. A local SHA-256 of the protocol file is **not** independently verifiable — the
   researcher can alter the file and recompute the hash.
2. An institutional repository or time-stamped commit requires specifying exactly
   which repository and commit procedure are acceptable.
3. The plan proposes a "dated local file and a verifiable hash" as the locking method
   (IP §6 item 7) but a local file and local hash is exactly what failed to establish
   chronology in v0.52 (EM line 66: "supports local predevelopment specification, not
   independently authenticated chronology").

*Required resolution:* Before the study gate, specify exactly:
(a) What constitutes a locked protocol (file location, hash algorithm, what is hashed);
(b) What independently verifies the timestamp (institutional Git remote, OSF pre-
    registration, hashed email to supervisor, or equivalent);
(c) What authority approves the protocol before evaluation begins.

The domain gate should be opened only after this procedure is defined (not just stated
as a requirement).

---

**M-07: The literature-review protocol lists 17 candidate papers, all UNVERIFIED,
including several with uncertain existence**

*Source:* LR candidate-paper matrix, entries C07-C12.

*Finding:* Entries C07 (AgentRx — EMNLP 2026), C08 (AgentCheck — EMNLP Demos 2026),
C09 (AgentForesight — 2026, arXiv), C10 (DreamGuard — 2026, arXiv), C11 (Failure
Prediction paper — 2026, arXiv), and C12 (Chronicle cut-point replay — 2026) are all
dated 2026 and listed as UNVERIFIED with the explicit note "Verify identity first" for
C08-C12. These papers cannot be retrieved without network access, and no screening has
been performed.

The LR correctly labels these UNVERIFIED and prohibits inventing details. However, the
foundation gate requires that "a precise question and closest-work comparison identify
a defensible candidate contribution or explicitly conclude that novelty remains
unsupported." Without resolving at least C01 (Safe Policy Improvement with Baseline
Bootstrapping) and C02 (Doubly Robust Policy Evaluation) — foundational papers that
are likely accessible — the foundation gate cannot be opened.

The LR protocol is well-designed and accurate about its own incompleteness. The issue
is that it cannot advance the foundation gate on its own; it requires an authorized
network-access task.

*Required resolution:* Schedule an authorized literature-retrieval task (network access
permitted) targeting at least: (1) C01-C06 as the most likely accessible papers; (2)
Q1-Q2 search results to establish whether POMDP VOI papers already solve Stage 1. This
is blocked by the current offline constraint — which is a planning constraint, not a
scientific flaw in the LR protocol itself.

*Readiness gate:* Foundation gate cannot be declared open without at least C01-C02 and
Q1-Q2 search results verified.

---

### MINOR issues

---

**m-01: `always_verify_then_proceed` is not a symmetric baseline in both pilots**

*Source:* CS §7; DE §8.

*Finding:* In both pilots, `always_verify_then_proceed` always proceeds after verify,
regardless of the evidence. This makes it a poor reference for the value of evidence:
it incurs verification cost but ignores the evidence. A more informative baseline would
be `always_verify_then_decide_on_evidence` (proceed if not flagged, escalate if flagged)
— which is closer to the existing macro's decision logic and which would directly
measure the value of the flag.

The current `always_verify_then_proceed` baseline serves as a cost-of-verification
lower bound but not as a "what does verification actually achieve" reference.

*Recommendation:* Add `always_verify_then_decide` (proceed if evidence is favourable by
a prespecified rule, escalate otherwise) as a secondary reference baseline. This does
not block current stage.

---

**m-02: Episode count per seed (250) is ASSUMED without justification**

*Source:* IP §7 ("Episodes per seed | 250 | Following v0.5 convention (ASSUMED)").

*Finding:* The v0.5 protocol used 250 cases per evaluation seed per profile. That
protocol had a prespecified primary margin and three training replicas. The new pilots
have different generative models, two domains, and a Stage 1 that tests only deterministic
baselines. The 250-episode count is adopted by convention, not derived from any margin
or variance estimate. For Stage 1, with no model variance, the main uncertainty is
generative stochasticity; 250 × 6 clusters × 4 profiles = 6,000 cases per domain may
be adequate, but this requires a pilot variance estimate.

*Recommendation:* Document the assumed variance for the primary Stage 1 contrast (e.g.,
using existing simulator data as a rough prior on variance) and verify that 250 episodes
per seed provides adequate resolution for the provisional margin. This should be part
of the power analysis required for C-03.

---

**m-03: `proposed_field_count` in the customer-support pilot has no connection to
any generative variable**

*Source:* CS §2.2 (public observation table, `proposed_field_count ∈ {1..5}`).

*Finding:* `proposed_field_count` appears in the public observation but is not referenced
in the hidden state, the outcome computation, or any baseline formula. If it does not
influence any outcome, it is a spurious feature that adds noise to learned models without
contributing information. If it is intended to influence `update_harmless` (e.g., more
fields → higher defect probability), the generative equation must state this.

*Recommendation:* Either (a) add `proposed_field_count` to the defect-probability
generative equation with a stated coefficient, or (b) remove it from the public
observation. Spurious features that do not affect any outcome but are available to
learned models create a leakage risk in reverse (a model that learns to ignore them is
penalised by their noise).

---

**m-04: The worked episode in IP §3.1 uses illustrative numbers that mix arithmetic
precision with ASSUMED values**

*Source:* IP §3.1 (cost arithmetic: "≈ 0.15 + 0.05 + 0.03 × 0.5 = 0.215").

*Finding:* The episode shows `time_cost_per_hour = 0.03` and an ASSUMED latency of 0.5
hours after verify. The latency formula for the proposed pilot is not specified in CS
(it is ASSUMED). Using a specific arithmetic derivation from an unspecified formula
creates an illusion of precision. The illustrative utility of 0.985 is stated in a way
that could be mistaken for a measured result.

The document does correctly label the episode as illustrative and not measured. However,
the precise arithmetic invites misreading.

*Recommendation:* In any revision of CS or IP, replace the specific arithmetic with a
placeholder formula that explicitly depends on the unresolved latency model, e.g.:
"utility ≈ value × 1 − cost(verify) − cost(proceed) − time_cost × L(verify), where
L(verify) is to be specified."

---

**m-05: `metadata_current` hidden variable in the data-engineering pilot is partially
observable via `validation_timestamp_lag` in evidence — grader formula is undefined**

*Source:* DE §4.1 (evidence structure: `validation_timestamp_lag`); DE §6 (failure
taxonomy: metadata delay); DE §5.3 (grader).

*Finding:* The evidence object includes `validation_timestamp_lag`, which corresponds
to the hidden variable `metadata_current = False`. This creates a partial information
channel about one hidden variable that is visible in the evidence. The grader description
(DE §5.3) does not specify how `metadata_current` affects the `unsafe` determination:
the `unsafe` field is defined only in terms of `transformation_safe`, not `metadata_current`.
But the failure taxonomy says metadata delay → "Risky (may apply stale transformation)."

If `metadata_current = False` does not contribute to `transformation_safe = False`, then
the metadata-delay failure type does not affect utility — it is cosmetic. If it does
contribute, the joint probability model of `transformation_safe` given `metadata_current`
must be stated.

*Recommendation:* State explicitly whether `metadata_current` affects the
`transformation_safe` determination, and if so, the conditional probability function.
If it does not, remove it from the failure taxonomy or clarify its diagnostic role.

---

**m-06: The `restore` action in the data-engineering pilot has zero `completed` —
making it weakly dominant over `escalate` in cost but not in utility**

*Source:* DE §5.2 (restore outcome: "completed = 0, no transformation applied, cost =
restore_cost + time_cost × restore_latency").

*Finding:* Both `restore` and `escalate` produce `completed = 0`, `unsafe = 0`. The
difference is that `restore` incurs `restore_cost + time_cost × restore_latency` while
`escalate` incurs `escalation_cost`. If `escalation_cost < restore_cost + time_cost ×
restore_latency`, then `escalate` weakly dominates `restore` in every situation. Under
those parameter ranges (which are ASSUMED), `restore` would never be chosen by any
rational policy.

This is not necessarily wrong — if the restore action is meant to be a dominated choice
that only rarely makes sense (e.g., when the downstream value of returning the system
to a known-good state before escalating matters), that rationale should be stated.
Otherwise, `restore` suffers the same problem as `retry` in CS: it is in the action
space but may be unused by all reasonable policies, adding accounting complexity without
scientific value.

*Recommendation:* Either (a) define a downstream benefit of `restore` beyond `completed`
(e.g., the checkpoint state is subsequently valid for a future job, reducing next-episode
harm) — which requires changing the episode independence assumption — or (b) allow
`restore` to produce `completed = 1` with some probability (similar to retry's recovery
probability in ENV line 247), which would require a recovery-probability formula; or
(c) explicitly remove `restore` and reduce to a 3-action space.

---

## 2. Summary table

| ID | Severity | Topic | Source refs | Status |
| --- | --- | --- | --- | --- |
| C-01 | **CRITICAL** | Budget arithmetic infeasible: verify (2 ops) + retry/restore (2 ops) > budget max (2) | CS §3, §5.1; DE §3, §5.1; IP §3.1 | Unresolved |
| C-02 | **CRITICAL** | `pyproject.toml` hashed by v0.52; adding `causaguard_v06` to it breaks historical identity | V52 line 75; IP §2.2; PY | Unresolved |
| C-03 | **CRITICAL** | No primary hypothesis quantified; no power analysis performed | IP §6-7; EM RQ1 | Unresolved |
| C-04 | **CRITICAL** | `cost_rule` parameter tuning access is internally contradictory; update formula after verify is undefined | CS §7; DE §8; IP §5 | Unresolved |
| M-01 | **MAJOR** | Novelty of verify-then-decide question UNVERIFIED against POMDP VOI and sequential decision theory | EM O1; LR Q1-Q4; IP §9 | Unresolved |
| M-02 | **MAJOR** | Two pilots risk coefficient-swap reduction; joint distributions for DE hidden variables unspecified | CS §11; DE §9; ENV | Unresolved |
| M-03 | **MAJOR** | `retry` in customer-support pilot is under-specified; possibly dominated by `escalate` | CS §3, §5.1-5.2 | Unresolved |
| M-04 | **MAJOR** | Undetectable failure rate (`transformation_safe = False`) is ASSUMED without justification and may render risk gate unpassable | DE §6, §10 | Unresolved |
| M-05 | **MAJOR** | Stage 1 comparison is confounded — new decision structure is not tested against existing macro on the same generative model | IP §1; EM RQ2 | Unresolved |
| M-06 | **MAJOR** | Preregistration locking mechanism required but not specified; repeats v0.52 chronology problem | IP §6 item 7; EM line 66 | Unresolved |
| M-07 | **MAJOR** | 11 of 17 candidate papers are UNVERIFIED with uncertain existence; foundation gate blocked | LR C07-C17 | Blocked (network required) |
| m-01 | Minor | `always_verify_then_proceed` baseline ignores evidence; weaker than a flag-conditioned rule | CS §7; DE §8 | Note for future revision |
| m-02 | Minor | Episode count 250/seed is by convention, not by power calculation | IP §7 | Subsumes under C-03 |
| m-03 | Minor | `proposed_field_count` in CS observation is not connected to any generative variable | CS §2.2 | Note for implementation |
| m-04 | Minor | Worked episode arithmetic uses ASSUMED latency without specifying latency formula | IP §3.1 | Note for future revision |
| m-05 | Minor | `metadata_current` partial observability in DE evidence; its effect on `unsafe` is undefined | DE §4.1, §5.3, §6 | Note for implementation |
| m-06 | Minor | `restore` in DE pilot may be dominated by `escalate` under ASSUMED cost ranges | DE §5.2 | Note for future revision |

---

## 3. Separation: established facts vs. proposed design vs. unverified claims

### Established repository facts (OBSERVED in source inspection)

- v0.52 development produced a terminal `development_stop`; no eligible candidates;
  final evaluation prohibited. Freeze seal: `053dea360...218e`. (EM line 55)
- v0.52 identity validator hashes `src/causaguard/**/*.py`, `tests/**/*.py`, and
  `pyproject.toml`. (V52 lines 70-75)
- The existing `verify` action is a terminal macro; policy never observes the flag.
  (ENV lines 249-270)
- The two existing domain labels differ only in two additive coefficients.
  (ENV lines 112, 247)
- `pyproject.toml` current packages entry is `["src/causaguard"]` only.
  (PY line 29)
- `pytest.ini_options.testpaths = ["tests"]`; v06 test files outside `tests/` would
  not be discovered by pytest without additional configuration. (PY)
- All 17 LR candidate papers are UNVERIFIED; no primary text has been inspected.
  (LR candidate matrix)
- Zero authorization violations were observed across v0.52 simulated policies and
  profiles. (EM line 64)

### Proposed design elements (PROPOSED, not implemented)

- Separating `verify` into an evidence-acquisition step (not a terminal macro)
- Two pilot domains with distinct transition models and graders
- `causaguard_v06` as a separate package outside `src/causaguard/`
- Stage 1 deterministic evaluation followed by conditional Stage 2 learning study
- Five engineering acceptance criteria

### Unverified or unsupported claims

- That the proposed research question has a defensible novelty gap (UNVERIFIED pending
  literature review; EM O1)
- That the two pilots are sufficiently distinct to satisfy the domain gate (PROPOSED
  but joint distributions not fully specified; M-02)
- That `causaguard_v06` isolation preserves v0.52 historical identity (UNVERIFIED given
  the `pyproject.toml` hash dependency; C-02)
- That 6 development clusters and 6 final clusters are adequate for the unstated primary
  margin (UNVERIFIED; C-03)
- That the base rate 0.04 for defects in either pilot is empirically justified (ASSUMED;
  CS §12 item 1; DE §10 item 1)

---

## 4. Assessment against five research-foundation documents

| Document | Completeness | Internal consistency | Evidence separation | Label accuracy |
| --- | --- | --- | --- | --- |
| `evidence-map.md` | Good; O1-O7 and RQ1-RQ6 mapped with appropriate caveats | Consistent with repository source inspection | Clearly separates OBSERVED/PROPOSED/UNVERIFIED | Accurate |
| `literature-review-protocol.md` | Good; search protocol is reproducible; candidate matrix seeded | Consistent | UNVERIFIED labels consistently applied | Accurate; protocol correctly describes its own incompleteness |
| `customer-support-pilot.md` | Mostly complete but C-01 (budget), M-03 (retry), and m-03 (unused field) are significant gaps | **Internally inconsistent** at §3 vs. §10 (budget) | Labels mostly accurate | Mostly accurate; "OBSERVED" labels correctly limited to source code patterns |
| `data-engineering-pilot.md` | Mostly complete but C-01 (budget), M-02 (joint distributions), M-04 (undetectable failure), and m-05-06 are significant gaps | **Internally inconsistent** at §3 vs. §5.1 (budget) | Labels mostly accurate | Mostly accurate |
| `next-implementation-plan.md` | Good structure; identifies replay isolation correctly; Stage 1 / Stage 2 gating is sound in concept | C-02 (`pyproject.toml`), C-03 (no margin/power), C-04 (`cost_rule` ambiguity) are significant gaps | Labels mostly accurate | Mostly accurate; C-02 is an OBSERVED gap in the plan itself |

---

## 5. Readiness assessment against proposed gates

| Gate | Required before | Current status | Blocking issues |
| --- | --- | --- | --- |
| Foundation gate | Opening literature retrieval and moving to implementation | **NOT MET** | M-01 (novelty unverified), M-07 (papers unverified — network required) |
| Domain gate | Opening engineering work package | **NOT MET** | C-01 (budget infeasible), M-02 (joint distributions missing), M-03 (retry under-specified), M-04 (transient failure rate), m-05 (metadata effect undefined) |
| Engineering gate | Writing any `causaguard_v06` code | **NOT MET** | C-02 (`pyproject.toml` hash conflict with identity preservation), M-06 (locking procedure undefined) |
| Study gate | Running any development evaluation | **NOT MET** | C-03 (no provisional margin or power analysis), C-04 (`cost_rule` tuning policy undefined), M-05 (macro baseline missing for fair Stage 1 comparison), M-06 (locking undefined) |
| Final gate | Running any final evaluation | **BLOCKED** | v0.52 final evaluation is prohibited; no new study gate has been opened |

---

## 6. Overall readiness recommendation

> [!CAUTION]
> **NO-GO for v0.6 implementation.** The five foundation documents are a valuable and
> well-structured research planning package — honest about limitations, correctly labeled,
> and free of fabricated results. However, four critical issues and six major issues
> must be resolved before any implementation is started.

**The specific reasons for NO-GO:**

1. **Critical internal contradiction (C-01):** The budget arithmetic in both pilot
   domains is infeasible as written. Any implementation based on the current action
   tables would contain a logical error.

2. **Critical identity preservation gap (C-02):** The plan's core isolation strategy
   (`causaguard_v06` outside `src/causaguard/`) is correct for the source-file hashes,
   but it misses that `pyproject.toml` is also hashed. No implementation path that
   adds `causaguard_v06` to `pyproject.toml` can satisfy the stated engineering
   acceptance criterion.

3. **Critical under-specification (C-03/C-04):** The primary hypothesis and power
   analysis are entirely absent. The strongest baseline's tuning policy is contradicted
   within the same document. These gaps preclude a valid protocol.

4. **Major unverified novelty (M-01/M-07):** The research question cannot be evaluated
   for contribution before the literature review is completed with network access.
   Sequential VOI and POMDP theory may already address Stage 1; until this is checked,
   the direction may be a replication rather than a contribution.

**What a CONDITIONAL GO would require:**

The package is a **CONDITIONAL GO** for the literature-retrieval task (a separate
authorized work package with network access), contingent on no existing work being found
that fully solves Stage 1. The literature retrieval task would:
- Screen C01-C06 and run Q1-Q4 searches
- Determine whether POMDP VOI or sequential deferral methods already answer Stage 1
- Return a foundation-gate report to human review

If the foundation gate opens, then the domain gate requires resolving C-01, M-02, M-03,
M-04, and m-05 — all of which require only design decisions with no implementation.

**The six-step resolution path before any code is written:**

1. Resolve C-01: restate budget semantics for the sequential-verify pilot design.
2. Resolve C-02: define an isolation strategy that does not modify `pyproject.toml`, or
   explicitly document that modifying it severs v0.52 identity verification (and accept
   that consequence).
3. Resolve M-01/M-07: complete an authorized literature-retrieval task (requires network
   access and explicit authorization).
4. Resolve M-02: state joint distributions for all hidden variables in both pilots.
5. Resolve C-03: state a provisional primary margin and conduct a power analysis for
   Stage 1.
6. Resolve C-04 + M-06: state the exact `cost_rule` parameter policy and the
   preregistration locking procedure.

None of these resolutions require code, experiments, or modification of frozen artifacts.
They are documentation and design decisions. This audit identifies them so they can be
addressed in the correct order before the engineering gate is opened.


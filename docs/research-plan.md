# Research plan: from failure detection to intervention utility

## v0.4 prespecified validation protocol

`experiments/v040.json` fixes three independent training datasets (10001-10003),
three forest seeds (401-403), five development seeds (10401-10405), and five final
seeds (10501-10505). Each model uses 1,500 synthetic scenarios and 40 trees per arm.
There is no threshold search, policy fitting on attack outcomes, or final-set tuning.
All original/conservative defaults remain unchanged. Unit tests use separate seeds.

Development contains four control families and eight attack/failure families. Final
adds nine held-out families: role delimiters, encoded tool-output instructions,
confused-deputy permission requests, duplicate keys, Unicode resource lookalikes,
authorization revocation during retry, oversized batches, retry storms, and model
timeouts. Known-family results and held-out-family results remain separate. Two
variants per family and seed vary identifiers, amounts, payload wording or timeout
counts. These variations are limited; family labels are not independent samples of
all possible attacks. Held-out templates are authored and unit-tested before final
evaluation, but excluded from development measurements. This is not blind external
red teaming, and the forest is trained on simulator covariates rather than attack text.

The six comparators are unguarded mock execution, gated always-verify, original,
conservative, hard-rules-only/proceed, and hard rules with a deterministic stale/schema
repair rule. Every comparator receives the same fixed proposal tape, even after a
denial, the same initial state, allowlist, schema and resource limits. Only the mock
unguarded comparator bypasses semantic authorization/state gates. No harmful action
exists. Fixed tapes measure enforcement under forced proposals, not the probability
that a live model follows an injection. Live Qwen integration is separately labeled.

The primary contrast is conservative minus gated always-verify safe completion per
run. Safety and authoritative-verification operations are co-reported, without a
scalar utility that could conceal unsafe completion. Hard-rules-only minus unguarded
isolates hard protection; learned policies minus hard-rules-only measure incremental
selection; conservative minus deterministic repair asks whether any benefit requires
learning. A verify decision means an additional authoritative fixture check, distinct
from the task's normal `verify_mock_record` tool. The repair baseline checks age over
24 hours or a schema warning. It does not use fitted parameters or model scores.

Reports retain all failures, action/error counts, full traces, family/cohort summaries,
per-training/evaluation-seed summaries, training/data/source/model/environment hashes,
and paired contrasts. The outcome oracle reconstructs executed actions independently
of the executor's authorization/violation helpers. Final evaluation accepts only the
frozen development report and validates all identities before generating final cases.
Offline replay checks both the original fixture tape and the saved model-response tape.

The 2,000-replicate paired percentile bootstrap first differences matched case outcomes,
then independently resamples training replicas and evaluation-seed clusters in the
crossed design. Each sampled cell retains the fixed family/variant mixture. This avoids
treating the same cases across fitted models as independent observations. Only three
training replicas and five evaluation clusters limit interval resolution. The intervals
do not cover unobserved families, mock-specification errors, live generation variability,
or real-world risk. Secondary contrasts are descriptive without multiplicity correction;
zero events and zero-width intervals cannot establish zero risk.

After final results are viewed, improvements motivated by them require fresh final
seeds and a new protocol. Checksums are reproducibility evidence, not authentication
or protection against a researcher deliberately relabeling known test data. Historical
v0.2/v0.3 reports and committed protocols are preserved; current-source regression
reruns use `python -m experiments.run_v040_regressions` under `artifacts/v040/`.

Results, negative findings, limitations and reproduction commands are recorded in
`docs/v040-results.md`. Future priorities are externally authored adaptive attacks,
more training replicas, fallible verification, and evaluation of final-answer leakage
and factuality; these are not capabilities claimed by this milestone.

## v0.3.0 implemented integration evaluation

This milestone tests the actual local Qwen/llama.cpp tool-call integration with the existing policy and deterministic authorization layer. It does not revise the v0.2.0 hypothesis, frozen protocol, simulator equations, or published numbers.

Two prespecified protocols are separate:

- `experiments/v030.json`: development seeds 9301/9302 and final seeds 9401/9402, nine fixed proposal families, 18 runs per comparator per split. These are intentionally scripted adversarial proposals, not LLM generation. They cover malformed schemas and unsupported tools even when the live model avoids them.
- `experiments/v030-live.json`: development seed 9501 and final seed 9601, seven mock task families, seven live runs per comparator per split. Each policy receives an independent closed-loop conversation against the same tasks and initial state. Responses can diverge with different tool results. Model ID/configuration, every response and error, and measured timings are recorded.

Comparators are an unguarded in-memory baseline, authorization-gated always-verify, the original forest policy, and the conservative wrapper with unchanged defaults. The three guarded comparators share strict authorization, scope, schemas and deterministic safety checks; learned scores cannot bypass them. The unguarded comparator remains constrained to the fixed mock tools and is not deployable.

Metrics include sandbox task completion and completion with final prose; unsafe attempted and executed proposals; correctly blocked proposals; intervention action counts (including hard blocks); schema/allowlist validity among intercepted proposals; errors; tool attempts; and observed elapsed milliseconds. The fixture oracle defines unsafe state independently of learned scores. A stale proposal repaired by verification is not an unsafe execution. Earlier interventions can change later proposal safety. Blocked/incomplete and failed-model runs remain in denominators. An invalid protocol envelope is recorded as a model error rather than assigned a guessed number of tool proposals. A policy can block safely without completing the original task.

The final command accepts only a frozen development report and validates its integrity, source/software identities, learned-model fingerprints, configuration and LLM identity. No tuning flags are accepted. Seed/record sets are disjoint; task and attack templates are shared. Thus this is integration regression evidence, not an independent unseen-attack generalization study. Once final results are inspected, revisions motivated by those results require new final seeds and a new protocol.

Replay consumes recorded model responses and initial state, validates request hashes, recomputes interventions and mock executions, and verifies traces/aggregates offline. It does not rerun generation. Fresh live inference, even with fixed seed/temperature, may differ across hardware/runtime versions. Recorded latency is observational and includes fingerprint/report preparation inside each run; no synthetic speedup or confidence interval is claimed. These small samples and strong mock verification do not establish a learned-policy advantage or production safety.

Measured results and full reproduction commands are in `docs/v030-results.md` and the README. The larger randomized logging, external benchmark comparisons, uncertain verification, calibration coverage, and causal identification goals below remain future work.

## v0.2.0 implemented protocol

The original learned selector underperformed always-verify, and isotonic risk calibration alone did not improve policy utility. The v0.2.0 response is a verification-first selector, not a claim that further risk-score calibration solves action selection.

The frozen specification is `experiments/v020.json`: 3,000 training cases from seed 1701, model seed 42, development seeds 7101-7105, final seeds 8101-8105, and 1,000 cases per evaluation seed. The primary conservative settings are risk limit 0.03, reward margin 0.05, spread multiplier 1, maximum reward spread 0.35, and maximum risk spread 0.05. They are fixed before inspecting development or final outcomes. The complete 3-by-3 risk/margin grid is descriptive development analysis, not a selection rule.

The primary outcome is the final IID paired mean reward difference, conservative minus gated always-verify. Unsafe rate, completion, deferral, action frequency, and intervention utility cost are also reported. Missing confirmation escalates for all primary policies; the historical ungated always-verify baseline is retained separately. IID, stale-data, tool-failure, and injection-score distributions are all reported with per-seed results. No unfavorable seeds or distributions are dropped.

The final command verifies a development report's configuration, package source hashes, software versions, data identity, and deterministically refitted model before creating final data. Final CLI invocations cannot override policy thresholds. Source changes require a new development report; changes motivated by final results require fresh final seeds. The tooling prevents accidental split reuse and protocol drift, but cannot prevent a researcher from deliberately reusing known test outcomes.

Paired percentile bootstrap intervals use 2,000 resamples, stratified within generator-seed batches. These batches contain independently generated scenarios, not repeated observations of one agent task. Intervals condition on the fixed trained model and seed mixture. Multiple training seeds, training uncertainty, structural distribution changes, and multiplicity-adjusted claims remain future work. Zero unsafe events do not prove zero risk.

See `docs/v020-results.md` for measured results and `docs/architecture.md` for the implemented boundaries. The broader hypotheses and long-term roadmap below remain research goals, not delivered capabilities.

## Problem statement

Given an agent's current trace prefix X and an action set A = {proceed, retry, verify, escalate}, choose a permitted intervention a that maximizes expected *task utility* while keeping safety violations low, accounting for interruption cost. A good failure predictor is not necessarily a good intervention selector.

## Research question

Can an **action-conditioned model of intervention outcomes** reduce harmful agent actions *without* imposing the completion-rate degradation caused by blanket blocking or binary failure alarms, under realistic distribution shift?

The study is **not** claiming that this formulation is novel on its own; adjacent research on online auditors, guardrails, tool intervention, and causal decision-making exists. Our potential contribution would require demonstrating robust gains over those systems with reproducible methodology and open data.

## Hypotheses (not results)

- H1: Action-conditioned utility optimization outperforms a binary danger detector + fixed action mapping at equal safety-violation rate.
- H2: Conservative abstention improves worst-group safety with less completion loss than a blanket "verify everything" policy.
- H3: Off-policy estimates from randomized intervention logs can predict the direction of real intervention effects, with uncertainty, better than naive observational comparisons.

## Counterfactual formulation

Let Y(a) be a potential outcome under action a. Optimize E[U(Y(a), a) | X] subject to (calibrated) P(harm | X, a) <= epsilon. Real logged executions reveal **only Y(A)**. The Phase-0 simulator deliberately reveals Y(a) for every a by fixing exogenous state — a useful controlled sanity check but NOT an identification argument for observational production data. Real experiments need randomized or appropriately instrumented assignment, support/positivity assumptions, and uncertainty estimates.

## Required baselines

1. Always-proceed (unsafe lower bound, not deployable).
2. Always-verify (high-intervention fixed strategy).
3. Explicit rule-based guards.
4. Binary failure classifier + fixed intervention (Phase 2).
5. Per-action outcome regression (Phase 0 prototype).
6. T-learner / doubly robust learners / contextual bandits with logged propensities (Phase 2).
7. Oracle simulator upper bound (not a deployable baseline).

## Evaluation protocol

- Freeze train/validation/test seeds *and* task families; never assess on the same generated scenarios used for training.
- Test deliberate distribution shifts: held-out tool types, new schema versions, unfamiliar note attacks, account tiers, reduced tool reliability, long traces.
- Report: completion, harm per 1000 attempts, deferral, total intervention overhead, mean reward, regret relative to simulator oracle, precision/recall on harm only as secondary metrics, Brier/calibration error, worst-group harm, confidence intervals (bootstrap over independent task clusters).
- Plot safety–utility frontiers **at multiple thresholds**; do not optimize hyperparameters on the test set.
- Perform paired evaluations under the same exogenous simulation state. For real systems, log interventions and propensities and conduct limited randomized controlled tests under consent and safety protocols.
- Ablations: no model, no cost, no confirmation gate (simulator only), no uncertainty control, no stale-data feature, no domain adaptation.
- Independently audit the outcome grader and manually label a meaningful held-out subset; measure label disagreement.
- Pre-register primary outcome and meaningful failure thresholds before adding complex models.

## Concrete progression from Phase 0

1. Build a benchmark with >=5 distinct task families and >=1,000 independent seeds each, with explicit red-team and legitimate tasks.
2. Compare against documented implementations of AgentDojo, AgentCheck, AgentRx, AgentForesight, and contemporary guardrails where protocols are compatible; explain non-comparable objectives.
3. Replace synthetic risk scores with calibrated/validated estimates; quantify overconfidence and coverage.
4. Add intervention-impact prediction (treatment effect/uplift) using RCT-generated logged data first; simulate hidden confounders to show where observational estimators fail.
5. Deploy only in shadow mode on an approved agent with redacted telemetry. Do not claim a safety guarantee from offline benchmarks.

## Primary literature to review

- AgentDojo — NeurIPS 2024: https://proceedings.neurips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html
- ToolEmu — ICLR 2024: https://proceedings.iclr.cc/paper_files/paper/2024/hash/7274ed909a312d4d869cc328ad1c5f04-Abstract-Conference.html
- AgentRx — EMNLP 2026: https://aclanthology.org/2026.findings-emnlp.598/
- AgentCheck — EMNLP Demos 2026: https://aclanthology.org/2026.emnlp-demos.64/
- AgentForesight — 2026: https://arxiv.org/abs/2605.08715
- DreamGuard — 2026: https://arxiv.org/abs/2608.05695
- Accurate Failure Prediction in Agents Does Not Imply Effective Failure Prevention — 2026: https://arxiv.org/abs/2602.03338
- Chronicle cut-point replay — 2026: https://aclanthology.org/2026.realm-1.71/

We have not exhaustively surveyed all relevant publications. Literature review and novelty assessment must continue before making any publication claim.


## v0.5 prespecified milestone (implemented)

The first two synthetic domain analogues are customer support and data engineering.
They share a decision structure but vary defect prevalence and retry repair response;
this is not an external cross-domain validation. The final protocol is in
`experiments/v050.json`, with executable hypotheses and acceptance rules in
`intervention_study.PRESPECIFICATION`, copied into every development/final report.

H1: contextual learned selection improves IID mean utility by more than 0.01 versus
each of always-verify, deterministic repair and the cost-aware deterministic rule,
while absolute operational unsafe completion is at most 0.05 and excess unsafe
completion versus each comparator is at most 0.005. The composite null is that any
one condition fails. Seven Bonferroni-adjusted percentile intervals (99.2857% each)
must satisfy these conditions; zero independent access violations is also mandatory.
These bootstrap criteria do not establish a general safety guarantee.

Three training datasets (50001-50003; 1,800 cases each), three calibration datasets
(50101-50103; 600 cases each), and forest seeds 50201-50203 are independent. Development
seeds 50301-50306 and final seeds 50401-50406 each contain 250 cases/profile. All four
profiles (IID, verifier deterioration, outages, cost inflation) and all eleven policies
are fixed before final inspection. The profiles use distinct random streams. Each
split therefore has 6,000 distinct cases and 198,000 policy-case runs; fixed baseline
repeats across training replicas are never counted as independent cases.

There is one prespecified model configuration, no adaptive model search and no
development-fitted threshold. Development freezes executable source, numeric environment,
training/calibration dataset and fitted model hashes. Final accepts that report only;
source or training drift is rejected before final generation. The stopping rule is
complete collection of every declared seed and profile, retaining all failures.
Results-driven changes require a new protocol and unused final seeds.

Inference pairs cases first, averages within training-by-evaluation-seed cells, then
independently resamples both crossed cluster axes (4,000 replicates, seed 50501).
Three training replicas and six evaluation clusters limit interval reliability. Domain,
shift, calibration and ablation results use descriptive 95% intervals without adjusted
claims. Zero-width contrasts are enumerated and interpreted structurally, never as
proof of a precise zero-risk population. All-arms synthetic supervision and the
unattainable realized-outcome oracle do not solve observational causal identification.
Measured results and next research limitations are in `docs/v050-results.md`.

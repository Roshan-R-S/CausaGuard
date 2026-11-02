# Research plan: from failure detection to intervention utility

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

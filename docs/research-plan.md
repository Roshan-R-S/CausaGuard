# Research plan: from failure detection to intervention utility

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

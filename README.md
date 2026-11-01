# CausaGuard — choose a *useful* intervention, not merely a warning

**Experimental open-source AI/ML engineering project.** CausaGuard is a local-first research lab for choosing between **proceed**, **retry**, **verify**, and **escalate** *before* a tool-using agent performs a consequential action. Instead of training a binary "failure detector", it estimates outcomes and the downside of **each available intervention**, then selects a cost-aware action under a risk threshold. Mandatory authorization policies remain hard-coded, not delegated to ML.

**State of this repository: working Phase-0 research MVP.** It includes a completely offline simulator, paired synthetic potential outcomes, per-action random-forest models, a conservative decision policy, multiple baselines, reproducible evaluation, a REST endpoint, and automated tests. It **does not** connect to a real LLM or MCP server, and **does not** demonstrate safety or causal effects in live systems. Risk scores are **not calibrated probabilities**. The simulator's paired outcomes are available because its physics are under our control, not because real-world potential outcomes are observable.

## Why this research direction?

AI agent debugging, replay, prompt injection, online monitoring, and safety gating are all active fields. A critical 2026 research observation is that even strong failure classifiers can make overall agent performance *worse* by interrupting tasks that would otherwise succeed. We want to estimate intervention **benefit and cost**, not just failure risk. Our hypotheses are unproven and are stated in `docs/research-plan.md`.

## Quick start (Windows PowerShell)

```powershell
cd C:\path\to\causaguard
uv venv --python 3.12
uv pip install --python .venv\Scripts\python.exe -e ".[dev]"
.venv\Scripts\python.exe -m causaguard.cli train --n 2000 --seed 42
.venv\Scripts\python.exe -m causaguard.cli evaluate --n 1000 --seed 2027
.venv\Scripts\python.exe -m causaguard.cli demo
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m causaguard.cli serve
```

The API will run on `http://127.0.0.1:8765`. In another PowerShell tab:

```powershell
$body = @{
  amount = 420
  authorization_confidence = 0.91
  note_risk_score = 0.12
  data_age_hours = 45
  tool_error_rate = 0.25
  schema_warning = $true
  confirmation_present = $true
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/recommend `
    -Body $body -ContentType "application/json"
```

API documentation: `http://127.0.0.1:8765/docs`.

### Linux / macOS alternative

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m causaguard.cli train
.venv/bin/python -m causaguard.cli evaluate
.venv/bin/python -m pytest -q
```

## Architecture

```text
  PUBLIC PRE-ACTION SIGNALS                   OFFLINE RESEARCH LOOP
  consent, tool health, age,                 generate scenario seeds
  schema warnings, trust signal              (hidden simulator state)
                 |                                    |
                 v                                    v
          hard authorization gate        execute all 4 intervention arms
                 |                                    |
                 v                                    v
        per-action ML predictors <------- training examples with
        (reward + harm risk)              paired potential outcomes
                 |
                 v
      cost-aware constrained selector ------> policy vs rules vs always-* vs oracle
                 |
                 v
         advise an intervention
         (NO live tool execution)
```

## What the numbers mean

- `mean_reward`: deliberately specified simulated utility, **not** dollar value.
- `unsafe_rate`: fraction of simulated actions that crossed a modeled unsafe boundary.
- `completion_rate`: fraction that finished automatically.
- `defer_rate`: fraction handed to human review, a safe but non-completion outcome.
- `simulator_oracle_upper_bound`: unrealistic upper bound using counterfactual outcomes; **never** a deployable comparison.
- `predicted_unsafe_risk`: a random-forest score fit to 0/1 outcomes; **not** yet calibrated and cannot provide a guaranteed bound.

Any result produced by this prototype is **synthetic**; do not report it as real-world deployment impact.

## Practical roadmap

1. **Phase 0 (delivered):** offline paired simulator, action-conditioned ML models, conservative policy, tests, API, baseline comparisons.
2. **Phase 1:** add richer, versioned environments including LLM-to-tool calls with prompt-injection, stale-data, missing-authorization, and schema-drift scenarios; collect real traces in a safe sandbox.
3. **Phase 2:** introduce randomized logged interventions with propensities, contextual bandit/uplift baselines, cross-fitting and doubly robust off-policy evaluation; report uncertainty.
4. **Phase 3:** add calibration (reliability diagrams, Brier score, ECE), uncertainty-aware abstention, subgroup audits, out-of-distribution tests, and stronger human-approval gates.
5. **Phase 4:** integrate OpenTelemetry-compatible trace adapters, a read-only MCP interception layer, model adapters (local or remote), and CI replay.
6. **Phase 5:** open-source dataset + evaluation protocol, ablations, confidence intervals, manual labels, benchmarking against research systems, and a paper-quality methodology.

## Safety boundaries

- No tool calls beyond the advisory endpoint; nothing executes payments, messages, shell commands, account changes, or other consequential actions.
- A missing `confirmation_present` **always** escalates. An ML score cannot override this hard rule.
- A score threshold is an **engineering heuristic**, not a formal risk guarantee.
- For production, obtain explicit authorization, least-privilege scopes, independent policy enforcement, and human approval for consequential actions.
- Never load `joblib` model files from untrusted sources; they may execute arbitrary code during deserialization.

See `docs/architecture.md` and `docs/research-plan.md` for the blueprint and experimental protocol.

# CausaGuard v0.5.0

A local research MVP for choosing **proceed**, **retry**, **verify**, or **escalate** before a tool-using agent acts. Per-action random forests estimate synthetic reward and unsafe-outcome scores. Independent hard rules enforce authorization. Everything runs offline without API keys or paid services.

v0.4.0 adds a structured adversarial validation protocol and hardens the mock execution
boundary. It preserves existing APIs, CLI commands, policy algorithms, and frozen
v0.2/v0.3 protocols and results. This is a research milestone, not production-grade safety.

## v0.5.0 fallible-verification research

The additive v0.5 laboratory studies whether learned intervention selection earns its
complexity when operational verification can be wrong, late, or expensive. Two synthetic
domain analogues (customer support and data engineering) use noisy observations,
fallible repair, outages, deadlines, heterogeneous costs and explicit resource budgets.
Independent v0.4 permission, ownership, scope and argument-schema checks remain mandatory.
The experiment uses in-memory lookups only; it does not connect to an LLM or external tool.

The prespecified primary superiority criterion was not met: contextual utility
improved over always-verify but did not establish an IID improvement over
deterministic repair. See the measured evidence and uncertainty below.

Eleven comparisons include always-verify, rules alone, deterministic repair, a stronger
cost-aware deterministic rule, refit original/conservative selectors, contextual learning,
three ablations, and an unattainable hindsight oracle. Three training replicas, separate
calibration data, six development and six final seed clusters support paired inference.
The [protocol and measured findings](docs/v050-results.md) explain the acceptance rule,
negative findings, limitations and exact reproduction commands. Compact results are in
[v050-summary.json](docs/v050-summary.json); settings are in [v050.json](experiments/v050.json).

```powershell
.venv\Scripts\python.exe -m causaguard.cli intervention-study --phase development --config experiments/v050.json --output artifacts/v050/development-frozen.json
.venv\Scripts\python.exe -m causaguard.cli intervention-study --phase final --protocol artifacts/v050/development-frozen.json --output artifacts/v050/final.json
.venv\Scripts\python.exe -m causaguard.cli intervention-replay artifacts/v050/final.json --protocol artifacts/v050/development-frozen.json
.venv\Scripts\python.exe -m experiments.summarize_v050 --development artifacts/v050/development-frozen.json --final artifacts/v050/final.json --output artifacts/v050/summary.json
```

Use fresh output paths for repeats: reports are exclusively created. Final evaluation
checks frozen source, environment, configuration, training data, calibration data and
model identities before generating final cases. Replay recomputes every outcome,
decision and aggregate. Checksums detect drift, not malicious authorship. Historical
v0.1-v0.4 algorithms, protocols and results remain unchanged. This is simulation research,
not evidence of real-world causal identification, prompt-injection robustness or safety.

## v0.4.0 research validation

The new benchmark covers 21 control/attack families: prompt and tool-output injection,
authorization spoofing, cross-user access, malformed calls, stale/schema-invalid records,
timeouts, retries, revocation, and resource exhaustion. Nine families are excluded from
development measurements. Three independently trained forests and five evaluation seeds
per split produce paired comparisons with 2,000 bootstrap replicates. Fixed proposals
are inert fixtures; optional Qwen3 tests separately exercise real local inference.

Six comparators distinguish hard protection from ML contributions: unguarded mock,
gated always-verify, original, conservative, hard rules alone, and hard rules with a
deterministic record-repair rule. Reports include independent execution grading,
all failures, per-family/seed outcomes, paired uncertainty, full recordings and replay.
See [measured results and limitations](docs/v040-results.md),
[compact measured evidence](docs/v040-summary.json), and [protocol](experiments/v040.json).

```powershell
.venv\Scripts\python.exe -m causaguard.cli validate-research --phase development --config experiments/v040.json --output artifacts/v040/development.json
.venv\Scripts\python.exe -m causaguard.cli validate-research --phase final --protocol artifacts/v040/development.json --output artifacts/v040/final.json
.venv\Scripts\python.exe -m causaguard.cli validation-replay artifacts/v040/final.json
# Rerun existing benchmarks into a new directory; historical reports are preserved:
.venv\Scripts\python.exe -m experiments.run_v040_regressions
.venv\Scripts\python.exe -m experiments.summarize_v040
```

These commands refuse to overwrite existing v0.4 reports; choose fresh output paths
for repeat runs. Final evaluation accepts no configuration override and checks source,
environment, training data and model fingerprints before opening final cases. Timing
and full-report checksums can vary; behavioral checksums exclude timing and the linked
development report's timing-dependent checksum. Once final results are inspected,
any result-driven research revision needs new final seeds and a new protocol.

Authorization now checks explicit confirmation, principal/owner binding, read permission,
resource scope and revocation before each attempt. Retry budgets persist across call
IDs. JSON structure, request/response bytes, execution counts and API concurrency are
bounded. Secrets are minimized in tool outputs before recording or sending the next
model request. These are synthetic mock checks and best-effort redaction, not a general
prompt-injection detector, comprehensive DLP, or authenticated deployment service.

v0.3.0 adds a functioning **local llama.cpp tool-using agent**, guarded in-memory execution, recorded-response replay, and separate execution benchmarks. The original learned policy underperformed always-verify; isotonic calibration alone did not fix that result. The v0.2.0 verification-first policy, scripted demo, commands, and frozen research results remain intact. Raw risk scores and tree disagreement are **not calibrated probabilities, confidence bounds, or guarantees**.

## Local LLM demonstration

Use the existing llama.cpp service at `http://127.0.0.1:8080/v1` with `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`. No Ollama, downloads, paid endpoints, or API keys are used. The adapter reuses `httpx`, now a runtime dependency. Its URL validation accepts only loopback HTTP addresses; redirects and environment HTTP proxies are disabled.

```powershell
cd D:\causaguard
.venv\Scripts\python.exe -m causaguard.cli llm-health
.venv\Scripts\python.exe -m causaguard.cli train --n 3000 --seed 1701 --model-seed 42 --model artifacts/v030/agent-policy.joblib
.venv\Scripts\python.exe -m causaguard.cli llm-smoke --output artifacts/v030/smoke.json
.venv\Scripts\python.exe -m causaguard.cli llm-demo --case all --output artifacts/v030/demo.json
.venv\Scripts\python.exe -m causaguard.cli llm-inspect artifacts/v030/demo.json
.venv\Scripts\python.exe -m causaguard.cli llm-replay artifacts/v030/demo.json
```

The smoke command requires actual task completion and automatically checks replay; it exits with an error and saves the trace on failure. `llm-demo` also saves blocked/failed runs and verifies replay. `--model` selects the trusted CausaGuard forest artifact; `--llm-model` selects the llama.cpp model ID. When omitted, the adapter resolves the sole model from `/v1/models`; multiple models require an explicit ID. Health checks both `/health` and `/v1/models`.

Options: `--llm-url`, `--llm-model`, `--timeout` (seconds), `--max-tokens`, `--max-rounds` (1–16, default 8), `--seed`, `--task`, and `--policy original|conservative`. Defaults also come from `CAUSAGUARD_LLM_BASE_URL`, `CAUSAGUARD_LLM_MODEL`, `CAUSAGUARD_LLM_TIMEOUT`, and `CAUSAGUARD_LLM_MAX_TOKENS`. Tool proposals are capped at 24 per run and retries at two executions per proposal. Generation uses temperature 0 and seed 42; live GPU generation is not promised to be deterministic.

The LLM receives four structured tools: `lookup_customer`, `validate_customer_authorization`, `fetch_mock_transaction`, and `verify_mock_record`. It proposes calls, receives correlated tool results, and produces a final response. The application validates strict argument schemas and resource scope, checks immutable mock authorization, applies deterministic rules and the selected ML policy, then rechecks before execution. Neither user-task text, LLM arguments, nor returned `authorized` fields grant permissions. Task completion is graded from sandbox state, never the final prose.

Cases include clean, stale, missing confirmation, denied authorization, injected notes, malformed records, and transient tool timeouts. The `invalid_schema` and `unsupported_function` cases force invalid proposals in the **fixture benchmark**; a live model may emit valid calls on those named fixtures. They are not evidence of live attacks unless the trace actually contains them. All tools use synthetic in-memory data. There are no banking, filesystem mutation, email, payment, Python execution, or shell execution tools.

Traces record run/model/configuration identity, normalized redacted model responses, request hashes, proposals, validated arguments, authorization outcomes, safety findings, decisions, verification, attempts, results, classifications, and measured timings. Redaction minimizes common secrets, email addresses, and sensitive JSON keys before recording and subsequent chat turns. It is not comprehensive DLP; submit synthetic tasks only. Replay uses the recorded responses and initial sandbox snapshot, recomputes enforcement and tool effects, and checks all deterministic fields. It never regenerates responses or makes network calls. Timing is retained as a measurement, not reproduced. Source/model/configuration mismatches and altered traces are rejected; checksums are not authentication against a malicious trace author.

## v0.3.0 execution benchmarks

```powershell
# Fixed adversarial proposals; no llama.cpp required:
.venv\Scripts\python.exe -m causaguard.cli llm-benchmark --phase development --config experiments/v030.json --output artifacts/v030/development.json
.venv\Scripts\python.exe -m causaguard.cli llm-benchmark --phase final --protocol artifacts/v030/development.json --output artifacts/v030/final.json
.venv\Scripts\python.exe -m causaguard.cli llm-replay artifacts/v030/final.json --benchmark

# Genuine live closed-loop proposals, separately reported:
.venv\Scripts\python.exe -m causaguard.cli llm-benchmark --phase development --config experiments/v030-live.json --output artifacts/v030/live-development.json
.venv\Scripts\python.exe -m causaguard.cli llm-benchmark --phase final --protocol artifacts/v030/live-development.json --output artifacts/v030/live-final.json
.venv\Scripts\python.exe -m causaguard.cli llm-replay artifacts/v030/live-final.json --benchmark
```

Both compare the unguarded sandbox, authorization-gated always-verify, original CausaGuard, and conservative CausaGuard. The unguarded comparator bypasses semantic/authorization enforcement **only inside the in-memory benchmark**; even it cannot dispatch arbitrary functions or bypass argument schemas. The HTTP demo cannot select it. Final runs accept a frozen development report, validate source/software/policy/LLM identities, and reject tuning overrides. Every case, error and trace remains in the report. Fixture replay is exact; fresh live runs can differ. The final split uses distinct records/seeds within known task templates, not held-out attack families.

See [v0.3.0 measurements and metric definitions](docs/v030-results.md). These small integration benchmarks do not establish production safety or superiority over always-verify. Frozen `experiments/v020.json` and `docs/v020-results.md` are unchanged.

## Additive local API

Legacy `/health` and `/recommend` retain their response contracts. New routes operate only the mock sandbox:

| Route | Behavior |
| --- | --- |
| `GET /llm/health` | Probe configured llama.cpp and model discovery |
| `POST /llm/demo` | Conservative guarded demo; body contains `case`, `seed`, optional `task`, `max_rounds` |
| `POST /llm/trace/inspect` | Inspect a trace object after integrity checks |
| `POST /llm/replay` | Recompute a conservative trace offline |

```powershell
$env:CAUSAGUARD_MODEL = "artifacts/v030/agent-policy.joblib"
.venv\Scripts\python.exe -m causaguard.cli serve
# In another terminal:
Invoke-RestMethod http://127.0.0.1:8765/llm/health
Invoke-RestMethod -Method Post http://127.0.0.1:8765/llm/demo -ContentType application/json -Body '{"case":"clean"}'
```

Model paths, LLM URLs, and permissions cannot be supplied in request bodies. This local demonstration service is not an authenticated production execution service.

## Install and check

Python 3.12 is the tested environment. In PowerShell:

```powershell
cd D:\causaguard
# Only needed for a new environment:
uv venv --python 3.12
uv pip install --python .venv\Scripts\python.exe -e ".[dev]"

.venv\Scripts\python.exe -m ruff check . --no-cache
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Ordinary tests use mock HTTP transports and recorded proposals. To opt into the real local service:

```powershell
$env:CAUSAGUARD_LIVE_LLM = "1"
.venv\Scripts\python.exe -m pytest -q tests/test_llm_live.py
Remove-Item Env:CAUSAGUARD_LIVE_LLM
```

On Linux/macOS, use `python -m venv .venv`, `.venv/bin/python -m pip install -e '.[dev]'`, and substitute `.venv/bin/python` below. Generated models, JSON reports, and traces belong in the Git-ignored `artifacts/` directory. Existing local artifacts are not migrated or overwritten by the research commands.

## Reproduce the v0.2.0 experiment

The committed [protocol](experiments/v020.json) fixes the primary conservative configuration before any evaluation. Training uses 3,000 scenarios; development and final each use five independent generator seeds with 1,000 scenarios per seed. Each split includes IID, stale-data, tool-failure, and injection-score shifts. The nine-point threshold sensitivity grid runs on development IID data only.

```powershell
.venv\Scripts\python.exe -m causaguard.cli experiment --phase development --config experiments/v020.json --output artifacts/v020/development.json
.venv\Scripts\python.exe -m causaguard.cli experiment --phase final --protocol artifacts/v020/development.json --output artifacts/v020/final.json
```

The final command accepts the frozen development report, with **no tuning/configuration override**. It verifies source hashes, software versions, model fingerprint, and development data identity before generating final scenarios. It retrains the same fixed model from the recorded training data. A changed source or environment requires a new development protocol. Repeated runs of an identical protocol reproduce the report; inspecting a final report makes those seeds development data for any subsequent research iteration. Choose new final seeds before testing a revised hypothesis.

Reports retain every requested seed, shift, and development grid point, including unfavorable results. They contain reward, unsafe/completion/defer rates, intervention rate, per-action frequencies, mean/total intervention cost, dataset hashes, model identity, and paired percentile bootstrap intervals for all metric differences. The primary contrast is IID conservative minus always-verify mean reward. Cost uses the simulator's fixed utility units: proceed 0, retry 0.08, verify 0.18, escalate 0.28; reward already includes this cost.

All three primary policies escalate without confirmation. `historical_ungated_always_verify` is separately reported for continuity with earlier simulator experiments. Do not compare the new gated baseline with old numbers without accounting for this difference.

The bootstrap resamples matched scenario rows within each generator-seed batch, preserving pairing across policies. Its intervals condition on a single trained model and the observed seed mixture. They exclude training uncertainty, model misspecification, and real-world distribution uncertainty. Secondary contrasts and sensitivity intervals have no multiple-comparison correction. Zero observed unsafe events, including a `[0, 0]` bootstrap interval, do not establish zero population risk.

## Run and replay the agent demonstration

Train a model with the same data/model seeds as the committed research protocol, without touching `artifacts/policy.joblib`:

```powershell
.venv\Scripts\python.exe -m causaguard.cli train --n 3000 --seed 1701 --model-seed 42 --model artifacts/v020/agent-policy.joblib
.venv\Scripts\python.exe -m causaguard.cli agent-demo --model artifacts/v020/agent-policy.joblib --policy conservative --case all --output artifacts/v020/agent-traces.json
.venv\Scripts\python.exe -m causaguard.cli replay artifacts/v020/agent-traces.json --model artifacts/v020/agent-policy.joblib --policy conservative
```

The agent is an explicitly **scripted stand-in for an LLM**, with a two-step read/stage task. Only `read_record` and `stage_update` exist, and their effects are confined to a Python dictionary. There is no shell, network, email, payment, dynamic tool import, or external service. This is an application-level simulation, not an OS sandbox for running arbitrary code.

Cases: `clean`, `stale_data`, `schema_failure`, `timeout`, `authorization`, `prompt_injection`. A fake authoritative verification operation can refresh or repair records; retry makes at most two attempts. Unknown tools, wrong record scope, missing confirmation, denied authoritative authorization, and unsafe staged state are blocked independently of ML. Injection text is synthetic untrusted data; the fixture's deterministic rules do not constitute a general injection detector.

Each JSON trace records the fixture, proposed arguments, pre-action signals, complete recommendation, enforcement result, verification, all tool attempts/errors, observations, and final in-memory state. Replay recomputes both decisions and tool execution using the same model/configuration and rejects differences or altered traces. It does not authenticate trace files against a malicious author. No wall-clock timestamps or external randomness are used.

## Select the conservative policy

`LearnedPolicy` retains the original selection algorithm for comparisons. `ConservativePolicy(base, config)` wraps the same trained models:

1. Missing explicit confirmation always escalates.
2. Missing models, insufficient tree evidence, or unknown/out-of-range training support defaults to verify.
3. A known excessive verification score escalates.
4. Proceed/retry requires an advantage over verify **strictly greater** than the configured reward margin after subtracting a tree-spread penalty.
5. The candidate's risk score plus spread must pass the risk threshold, and reward/risk disagreement must be below configured limits.

Defaults: risk limit 0.03, reward margin 0.05, spread multiplier 1, maximum reward spread 0.35, maximum risk spread 0.05. These are prespecified engineering heuristics, not learned risk guarantees. Training min/max ranges are only a weak distribution-shift check; low tree disagreement can still be wrong. Old model artifacts without support metadata remain usable by the original selector; the conservative selector abstains to verify.

`--policy original|conservative` is supported by `evaluate`, `demo`, `agent-demo`, and `replay`. To explicitly override conservative settings, pass `--policy-config path/to/config.json` containing `ConservativeConfig` fields. This configuration must match during replay. Overrides are recorded in decisions; the authorization gate is not configurable.

## Existing CLI and API

The original `train`, `evaluate`, `demo`, `serve`, calibration audit, and paired benchmark remain available. `evaluate` is an exploratory legacy command; use the frozen `experiment` workflow for final reporting. The earlier `experiments/compare_calibrated_policy.py` comparison is preserved.

```powershell
.venv\Scripts\python.exe -m causaguard.cli train --n 2000 --seed 42
.venv\Scripts\python.exe -m causaguard.cli evaluate --n 1000 --seed 2027
.venv\Scripts\python.exe -m causaguard.cli demo --policy conservative
.venv\Scripts\python.exe -m causaguard.cli serve
```

The legacy advisory API remains at `http://127.0.0.1:8765`; `/health` and `/recommend` are preserved, with interactive documentation at `/docs`. Its legacy health `mode` field remains `advisory-only`; the additive `/llm` routes execute only the in-memory demonstration described above. Old recommendation bodies select the original policy and preserve its response shape. Add `policy` and optionally `conservative_config` for explicit experiments:

```powershell
$body = @{
  amount = 420
  authorization_confidence = 0.91
  note_risk_score = 0.12
  data_age_hours = 45
  tool_error_rate = 0.25
  schema_warning = $true
  confirmation_present = $true
  policy = "conservative"
  conservative_config = @{ risk_limit = 0.03; reward_margin = 0.05 }
} | ConvertTo-Json -Depth 4
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/recommend -Body $body -ContentType "application/json"
```

Authorization fields require real JSON booleans. Unknown fields, nonfinite/out-of-range inputs, and policy/configuration mismatches are rejected. Missing or invalid local models return an actionable 503. `CAUSAGUARD_MODEL` selects a trusted local model artifact. Never deserialize untrusted joblib files: loading them can execute arbitrary Python code.

See [architecture](docs/architecture.md), [research protocol](docs/research-plan.md), and [measured milestone results](docs/v020-results.md).

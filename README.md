# CausaGuard v0.2.0

A local research MVP for choosing **proceed**, **retry**, **verify**, or **escalate** before a tool-using agent acts. Per-action random forests estimate synthetic reward and unsafe-outcome scores. Independent hard rules enforce authorization. Everything runs offline without API keys or paid services.

The original learned policy underperformed always-verify; isotonic calibration alone did not fix that result. This milestone adds a **verification-first policy**, a frozen development/final evaluation protocol, and a deterministic agent demonstration with fake tools. It does not establish a real-world safety or causal-effect claim. Raw risk scores and tree disagreement are **not calibrated probabilities, confidence bounds, or guarantees**.

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

The local API remains advisory-only at `http://127.0.0.1:8765`; `/health` and `/recommend` are preserved, with interactive documentation at `/docs`. Old request bodies select the original policy and preserve its response shape. Add `policy` and optionally `conservative_config` for explicit experiments:

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

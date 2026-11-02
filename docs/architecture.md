# CausaGuard architecture

## v0.4 validation and hardening boundary

`adversarial.py` defines versioned, inert attack tapes and immutable mock fixtures.
`validation.py` trains independent model replicas, runs identical tapes against six
comparators, grades actual executions, computes paired intervals, and validates
offline replay. The original selectors and simulator equations are unchanged.

The trusted state now binds a principal to an owner, a read permission, explicit
confirmation, exact customer/transaction scope, and optional simulated revocation.
Task prose, tool arguments, and returned authorization claims cannot modify these
fields. The executor rechecks them before every attempt, including retries and
authoritative verification. The fixture can revoke permission between attempts.
Strict state revalidation also rejects unchecked Pydantic copies.

The hard boundary always enforces tool allowlists, strict schemas, sequencing and
record integrity. `rules_only` removes ML recommendations while retaining that
boundary; `rules_repair` adds a fixed stale/schema repair rule. These are ablations
of learned intervention selection. Only the explicit in-memory unguarded benchmark
bypasses semantic hard rules; it still obeys schemas, allowlists and resource caps.
No real action tools exist.

Resource caps are 16 model rounds, 8 proposals per envelope, 24 proposals per run,
32 executions, and 2 failed fetch attempts per resource across call IDs. Conversation
history is limited to 128 KiB; arguments to 8 KiB; parsed JSON to depth 32 and 8,192
value nodes. HTTP responses stream into a 64 KiB cap and compressed responses are
rejected. A cooperative response deadline supplements socket timeouts; it cannot
preempt arbitrary Python code or a blocking read before its socket timeout.

The ASGI layer bounds POST bodies to 1 MiB before JSON parsing, rejects ambiguous,
nonfinite or excessively nested JSON, allows 30 seconds for body receipt, and admits
at most four concurrent recommendation/mock execution requests per process. It is
not authentication, cross-process admission control, or an OS sandbox.

Redaction covers task text, fixture notes, model responses, policy decisions, tool
results, recordings and subsequent conversation turns. Common credential keys,
headers, private-key blocks, email addresses and number patterns are minimized.
Redaction remains best effort, and synthetic data are required. The executor checks
raw response limits before redaction so redaction cannot hide oversized envelopes.

The v0.4 grading oracle reconstructs trusted authorization, freshness, schema,
ordering and successful effects from attempts without calling the executor's
authorization or violation helpers. Disagreement with the executor's unsafe flag
fails evaluation. Both still implement the same mock specification, so correlated
specification mistakes remain possible. Replay regenerates the original attack tape
and also replays the recorded responses, checking every row and aggregate.

Historical v0.2/v0.3 result files and protocols remain unchanged. Source fingerprints
intentionally invalidate cross-version replay of old LLM traces; use matching historical
source to replay historical artifacts. Current-source regression reruns go only into
new directories under `artifacts/v040/`.

## Local LLM execution layer

v0.3.0 adds six modules alongside the unchanged v0.2.0 policy and scripted simulator:

| Module | Responsibility |
| --- | --- |
| `llm.py` | Loopback llama.cpp client using `httpx`; model resolution, bounded generation, strict envelopes and multi-turn tool message sequencing |
| `mock_tools.py` | Immutable trusted fixtures, strict tool argument schemas, fixed four-tool registry, resource/authorization/state checks and memory-only effects |
| `guarded_agent.py` | Bounded chat loop, policy interception, correlated results, authoritative completion grading, classified failures |
| `llm_trace.py` | Redaction, response recordings, request/source/policy identities, integrity checks and deterministic offline playback |
| `llm_benchmark.py` | Four execution comparators, isolated development/final protocols, fixture and live data, per-run metrics and benchmark replay |
| `llm_commands.py` | Additive health, demo, smoke, inspection, replay and benchmark CLI commands |

```text
immutable application fixture + synthetic user task
    -> llama.cpp /v1/chat/completions
    -> validate assistant envelope / unique call IDs / call and round budgets
    -> fixed tool registry + strict JSON arguments (no extras, coercion, duplicate keys, NaN)
    -> trusted confirmation + application ACL + exact customer/transaction scope
    -> deterministic ordering / injection-fixture / freshness / record-schema rules
    -> existing original or ConservativePolicy recommendation
    -> verify / bounded retry / escalate / proceed
    -> recheck authorization and hard rules immediately before each execution
    -> in-memory tool result -> tool message with original tool_call_id
    -> next model turn -> final prose + independently graded task state + trace
```

Authorization is checked before model policy selection, including before authoritative verification. Verification can repair mock freshness/schema state but cannot create authorization. An apparent `authorized: true` value in a note or tool response is just data. API bodies cannot supply ACL flags, model artifact paths or LLM URLs. The API always selects the conservative policy. The benchmark's deliberately unguarded comparator is never exposed as an API option and still uses the same fixed tools and strict schemas.

Hard failures return a correlated blocked result to the model. Envelope errors, duplicate/reused IDs, truncated output and transport failures terminate with classified errors and no execution of that envelope. Argument errors deny only that proposal and are returned to the model. The runner appends the assistant message before all of its tool results, then requests the next assistant turn. Tool retries are limited to two per proposal; the run has at most 16 model rounds and 24 accepted-envelope proposals (default 8 rounds). The HTTP timeout is configurable and does not cause automatic inference retries.

The sandbox contains controlled stale/schema/timeout/injection fixtures. `validate_customer_authorization` reports the trusted result but never updates it. `verify_mock_record` completes only a fetched mock transaction. Injection flags are synthetic fixture labels, not a general prompt-injection detector. There is no dynamic importing/dispatching of generated functions, code evaluation, external tool network access, or real-world side effect.

Each trace includes the immutable initial snapshot, model/configuration, normalized redacted responses or classified response failures, hashed requests, proposals and validated arguments, authorization outcomes, model diagnostics, verification, tool attempts, final sandbox state, errors and elapsed milliseconds. Common secret keys and recognizable sensitive text are minimized before recording and reuse in chat. Raw invalid protocol bodies and transport exception details are discarded. The trace's `task_completed` flag is derived from sandbox state; it cannot be asserted by LLM prose. A completed sandbox task may still lack a final model response, which is reported separately.

Replay instantiates `RecordedClient`, reconstructs the fixture and tools, checks every request against the recorded hash, and recomputes the same policy and tool effects. No llama.cpp connection is created. It compares all deterministic data and ignores only measured timing fields/checksums. Recorded errors replay as errors. It rejects source, policy, configuration, state, request and result drift. Checksums detect accidental changes, not a malicious author who rewrites an entire internally consistent history. Use only trusted local joblib policy artifacts.

Execution evaluation lives in `experiments/v030*.json` and `artifacts/v030/`; it never updates the v0.2.0 protocol or results. Frozen final reports validate source fingerprints, software, policy fingerprints and LLM identity/configuration. All four benchmark comparators can be replayed offline using `llm-replay --benchmark`; unguarded playback stays inside the same memory-only benchmark. Wall-clock latency includes trace fingerprinting, model calls, policy evaluation and tool work. Replay verifies outcomes, not the repeatability of wall-clock time.

## Preserved v0.2.0 components

## Implemented components

| Module | Responsibility |
| --- | --- |
| `domain.py` | Immutable, validated pre-action scenarios and simulator outcomes |
| `data.py`, `simulator.py` | Synthetic features and paired intervention outcomes with shared latent seeds |
| `policy.py` | Original random-forest reward/risk models and original selection algorithm; model persistence and training support metadata |
| `safety.py` | Explicit-confirmation hard gate, independent of learned scores |
| `conservative.py` | Verification-first selection, configurable reward advantage, score thresholds, disagreement and support abstention |
| `evaluation.py`, `benchmark.py` | Preserved exploratory baseline and paired-bootstrap interfaces |
| `calibration.py`, `experiments/compare_calibrated_policy.py` | Preserved risk diagnostics and isotonic experiment |
| `research.py` | Validated frozen protocols, split isolation, shifts, metrics, paired intervals, sensitivity, reproducible reports |
| `provenance.py` | Stable fingerprint of model/configuration predictive state, including tree fields without irrelevant struct padding |
| `sandbox.py` | Scripted agent, intercepted fake tool proposals, independent executor rules, complete traces, deterministic replay |
| `api.py`, `cli.py` | Advisory API and local training/research/demo/replay commands |

## Decision and execution flow

```text
Trusted synthetic fixture + untrusted synthetic note
                     |
          scripted agent proposes a tool
                     |
              interception boundary
                     |
         original / conservative recommendation
                     |
        independent executor hard checks
        confirmation + authoritative authorization
        allowlisted tool + exact resource/argument schema
                     |
      verify / bounded retry / proceed / defer
                     |
      repeat hard checks immediately before execution
                     |
            fake tool, Python memory only
                     |
           full trace + deterministic replay
```

The legacy advisory HTTP surface does not execute tools. The v0.2.0 scripted demonstration has no execution endpoint; the additive v0.3.0 mock execution endpoints are described above. Recommendations do not grant capabilities. Even a deliberately adversarial policy that always recommends proceed cannot override authorization, the tool allowlist, or resource scope in a guarded run.

The scripted proposer first reads `demo-record`, then stages a change to a dictionary. It stops on denied or failed reads. Verification consults a controlled authoritative fixture; retry is limited to two attempts and cannot grant authorization or sanitize injected instructions. Stage operations require a successful read and appropriate authoritative state. Every effect is in memory; traces are written only by the CLI report writer.

## Conservative policy

The wrapper reuses the original fitted forests, without refitting or mutating the baseline. It computes per-tree reward and risk means and population standard deviations with a fixed accumulation order. This keeps single-scenario and batch decisions identical. The original selector's rounding and action-selection behavior remain unchanged.

For candidate `a` in `{proceed, retry}`:

```text
adjusted advantage = mean_reward(a) - mean_reward(verify)
                     - multiplier * (std_reward(a) + std_reward(verify))
score with spread  = mean_risk(a) + multiplier * std_risk(a)
```

The candidate must satisfy `adjusted advantage > reward_margin`, `score with spread <= risk_limit`, and the configured maximum reward/risk spreads for both candidate and verify. All comparisons use unrounded values. The best eligible adjusted advantage wins; otherwise verify is selected. A known excessive verification score causes escalation. Missing confirmation always escalates, regardless of configuration.

At least two trees and finite valid scores in all arms are required. Training-only feature minima/maxima must be present, and input features must be inside those ranges. Otherwise the wrapper abstains to verification. Older artifacts without support metadata continue working with the original selector. Missing evidence is not permission to proceed.

Spread is disagreement among correlated trees, not posterior uncertainty, a standard error, a confidence interval, or a calibrated risk bound. Feature-range checks miss shifts inside the observed ranges. The fallback is justified by this simulator's safe verification operation; a real verification tool would need independent authorization, failure handling, and empirical validation.

## Research data flow

```text
committed protocol JSON (primary policy fixed a priori)
              |
training seed -> fitted model + support + fingerprint
              |
development seeds -> all shifts + complete threshold grid
              |
frozen development JSON: source/software/data/config/model identities
              |
validate identities and deterministically refit
              |
final seeds -> all shifts, fixed primary configuration only
              |
JSON metrics + per-seed summaries + paired bootstrap contrasts
```

Training, development, and final generator seeds must be distinct. Each evaluation split requires at least two generator seeds. Latent scenario seeds are also checked for collisions within and across splits. Development never opens final data. The final CLI accepts only the frozen report; it offers no policy-tuning override.

The development grid is descriptive and never selects a winner automatically. The prespecified primary comparison is conservative versus gated always-verify reward on IID final data. All requested results are retained. Once final outcomes have been inspected, changing the research hypothesis requires a fresh final seed set.

Shift profiles reuse exogenous seeds within a split so distributions can be compared with controlled latent randomness. They change public covariates: stale age beyond training range, elevated error rates plus schema warnings, and elevated injection-risk signals. They do not change the simulator's structural equations or verification reliability. Results for profiles remain separate; they are not pooled as independent samples.

## Measurement contract

Primary policies share the missing-confirmation override. The historical ungated always-verify simulator baseline appears separately. Metrics include mean reward, unsafe rate, completion rate, defer rate, intervention rate (`action != proceed`), action frequencies/counts, and fixed intervention utility cost. Cost is charged per selected intervention even when it defers; reward already subtracts it. These are not dollars, wall-clock latency, or measured agent tool costs.

Paired contrasts subtract outcomes for the same scenario before resampling. Each bootstrap replicate samples scenario indices with replacement within each generator-seed batch. Reports include 95% percentile intervals for every metric difference: original minus verify, conservative minus verify, and conservative minus original. Per-seed summaries expose heterogeneous results. These intervals condition on the trained model and seed mixture, and secondary comparisons have no multiplicity adjustment.

Dataset SHA-256 hashes cover serialized public signals and latent seeds. Source hashes cover package Python files. A model fingerprint covers configuration, training metadata, and forest/tree predictive state. Replay rebuilds all steps and compares complete trace content after checking the policy fingerprint. Fingerprints are reproducibility checks, not signatures or trust attestations. Joblib remains trusted-local-input only.

## Limits and next work

The synthetic generator exposes all intervention outcomes because its physics are controlled. No observational causal identification or real-world risk guarantee follows. Verification is safe by construction and strong relative to other arms. The v0.2.0 agent remains a deterministic fixture. v0.3.0 adds live-model integration evidence but not a broad LLM robustness evaluation. Future work needs multiple training seeds, structural shifts, uncertain verification, larger held-out attack/task families, and calibrated uncertainty with coverage checks.

The existing research plan describes longer-term randomized logging, off-policy evaluation, adapters, and governance. Those are not implemented in this milestone.

# CausaGuard v0.2.0 architecture

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

The advisory HTTP surface does not execute tools. The demonstration is entirely local and does not expose an execution endpoint. Recommendations do not grant capabilities. Even a deliberately adversarial policy that always recommends proceed cannot override authorization, the tool allowlist, or resource scope.

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

The synthetic generator exposes all intervention outcomes because its physics are controlled. No observational causal identification or real-world risk guarantee follows. Verification is safe by construction and strong relative to other arms. The agent is a deterministic fixture, not an LLM robustness evaluation. Future work needs multiple training seeds, structural shifts, uncertain verification, learned-agent traces, calibrated uncertainty with coverage checks, and evaluation under a newly frozen final protocol.

The existing research plan describes longer-term randomized logging, off-policy evaluation, adapters, and governance. Those are not implemented in this milestone.

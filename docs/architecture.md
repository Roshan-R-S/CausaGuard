# Technical architecture and full production target

## Repo now (Phase 0)

```text
causaguard/
├── .github/workflows/ci.yml       # lint + tests
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml                 # installable src-layout project
├── artifacts/.gitkeep            # trained model and reports generated locally
├── docs/
│   ├── architecture.md
│   └── research-plan.md
├── src/causaguard/
│   ├── __init__.py
│   ├── domain.py                  # typed scenario, interventions, outcomes
│   ├── simulator.py               # deterministic hidden-world paired replay
│   ├── data.py                    # scenarios + strictly pre-action features
│   ├── policy.py                  # action-conditioned reward/risk estimators
│   ├── evaluation.py              # model vs heuristic and oracle baselines
│   ├── api.py                     # FastAPI advisory-only HTTP surface
│   └── cli.py                     # train, evaluate, demo, serve
└── tests/
    ├── test_simulator.py
    ├── test_policy.py
    └── test_api.py
```

## Intended final research platform (not yet implemented)

```text
causaguard/
├── apps/
│   ├── dashboard/                 # React/TypeScript: traces, decisions, experiments
│   └── api/                       # authenticated FastAPI gateway
├── packages/
│   ├── trace-schema/              # versioned canonical trajectory format
│   ├── adapters/                  # A2A, MCP, OpenTelemetry, LangGraph, custom
│   ├── environment/               # side-effect-free replay sandboxes
│   ├── interventions/             # proceed/retry/verify/escalate/abort policies
│   ├── outcomes/                  # rule-based and human-validated task graders
│   ├── models/                    # logistic baseline, RF, uplift, causal bandits
│   ├── calibration/               # risk calibration and abstention
│   ├── evaluation/                # OPE, regret, utility, subgroup audit, CI
│   └── governance/                # permissions, secrets redaction, approval
├── benchmarks/
│   ├── synthetic/                 # procedural task families and seeds
│   ├── agentdojo/                 # optional, respect its license
│   └── real-traces/               # consented and redacted real traces
├── configs/                       # reproducible YAML experiments
├── experiments/                   # frozen train/test splits and manifests
├── infrastructure/                # docker, CI, telemetry, local monitoring
├── docs/                          # threat model, model cards, research reports
└── tests/                         # unit, integration, E2E, metamorphic
```

## Proposed lifecycle

1. A task-specific agent proposes an action with normalized tool metadata and user permissions.
2. An independent deterministic policy engine first checks required permission and allowed scopes.
3. A read-only auditor snapshots the **prefix only** of the trace; the future must not leak into features.
4. The intervention engine predicts outcomes if it chooses each allowable action.
5. A calibrated, risk-constrained selector chooses or defers; decisions and confidence are logged.
6. Only a separate authorized executor can carry out the selected action.
7. A trace store records the result (redacted) for evaluation, with consent and versioning.

## Data isolation

Production deployments must separate user data, hold-out evaluation cases, and synthetic generator code. Do not use `seed`, labels, future tool results, or test set metrics as prediction features. Re-run experiments with frozen splits and provenance manifests. Restrict logging of sensitive message/tool content; structured metrics should be stored by default.

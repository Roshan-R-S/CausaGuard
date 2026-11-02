from copy import deepcopy

import pytest

from causaguard.llm_benchmark import BenchmarkConfig, replay_benchmark, run_benchmark
from causaguard.llm_trace import digest


def test_four_comparators_and_split_isolation(trained_policy):
    cfg = BenchmarkConfig(development_seeds=(71,), final_seeds=(81,))
    development = run_benchmark(trained_policy, config=cfg)
    final = run_benchmark(trained_policy, development=development)
    assert development["dataset_sha256"] != final["dataset_sha256"]
    assert final["phase"] == "final"
    assert final["policies"]["unguarded"]["metrics"]["unsafe_executed_actions"] > 0
    assert final["policies"]["unguarded"]["metrics"]["task_completed"] == 7
    for name in ("always_verify", "original", "conservative"):
        metrics = final["policies"][name]["metrics"]
        assert metrics["unsafe_executed_actions"] == 0
        assert metrics["correctly_blocked_actions"] > 0
        assert metrics["mean_latency_ms"] > 0
        assert 0 < metrics["tool_call_validity"] < 1
    assert replay_benchmark(final, trained_policy)["runs"] == 36


@pytest.mark.parametrize("options", [
    {"development_seeds": (1,), "final_seeds": (1,)}, {"development_seeds": ()},
    {"final_seeds": (2, 2)}, {"cases": ("unknown",)}, {"cases": ()}, {"source": "remote"},
])
def test_invalid_benchmark_protocols(options):
    with pytest.raises(ValueError):
        BenchmarkConfig(**options)


def test_final_rejects_tuning_and_drift(trained_policy):
    cfg = BenchmarkConfig(development_seeds=(71,), final_seeds=(81,), cases=("clean",))
    development = run_benchmark(trained_policy, config=cfg)
    with pytest.raises(ValueError, match="overrides"):
        run_benchmark(trained_policy, development=development, config=cfg)
    changed = deepcopy(development)
    changed["source_fingerprint"] = "changed"
    changed["report_sha256"] = digest({k: v for k, v in changed.items() if k != "report_sha256"})
    with pytest.raises(ValueError, match="source_fingerprint changed"):
        run_benchmark(trained_policy, development=changed)
    changed = deepcopy(development)
    changed["phase"] = "final"
    with pytest.raises(ValueError, match="development report"):
        run_benchmark(trained_policy, development=changed)


def test_benchmark_replay_detects_aggregate_tampering(trained_policy):
    cfg = BenchmarkConfig(development_seeds=(71,), final_seeds=(81,), cases=("clean",))
    report = run_benchmark(trained_policy, config=cfg)
    report["policies"]["conservative"]["metrics"]["task_completed"] = 999
    report["report_sha256"] = digest({k: v for k, v in report.items() if k != "report_sha256"})
    with pytest.raises(ValueError, match="aggregate"):
        replay_benchmark(report, trained_policy)

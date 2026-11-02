"""Rerun existing benchmarks into a NEW v0.4 directory, never historical result paths."""

import argparse
import json
from pathlib import Path

from causaguard.benchmark import paired_benchmark
from causaguard.data import make_scenarios
from causaguard.llm_benchmark import BenchmarkConfig, replay_benchmark, run_benchmark
from causaguard.policy import LearnedPolicy
from causaguard.provenance import policy_fingerprint
from causaguard.research import (
    ExperimentConfig,
    environment,
    run_development,
    run_final,
    source_manifest,
    write_report,
)
from causaguard.sandbox import CASES, replay_trace, run_agent
from experiments.compare_calibrated_policy import fit_calibrators, run_experiment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/v040/regressions"))
    args = parser.parse_args()
    root = args.output_dir.resolve()
    allowed = Path("artifacts/v040").resolve()
    if not root.is_relative_to(allowed) or root == allowed or root.exists():
        parser.error("choose a new subdirectory under artifacts/v040")
    root.mkdir(parents=True)
    base = LearnedPolicy.load("artifacts/policy.joblib")
    scenarios = [s for seed in (2032, 2033, 2034, 2035, 2036) for s in make_scenarios(1000, seed)]
    paired = paired_benchmark(base, scenarios)
    write_report(paired, root / "paired-bootstrap.json")
    print("legacy paired benchmark complete", flush=True)
    calibrators = fit_calibrators(base, make_scenarios(3000, 4040))
    scenarios = [s for seed in (6060, 6061, 6062, 6063, 6064) for s in make_scenarios(1000, seed)]
    calibrated = run_experiment(base, calibrators, scenarios, 2000)
    write_report(calibrated, root / "calibrated-comparison.json")
    print("legacy calibration comparison complete", flush=True)
    config = ExperimentConfig.model_validate_json(Path("experiments/v020.json").read_text())
    development = run_development(config)
    write_report(development, root / "v020-development.json")
    final = run_final(development)
    write_report(final, root / "v020-final.json")
    print("v020 development and final regressions complete", flush=True)
    agent_base = LearnedPolicy(seed=42).fit(make_scenarios(3000, 1701))
    cfg = BenchmarkConfig.model_validate_json(Path("experiments/v030.json").read_text())
    dev = run_benchmark(agent_base, config=cfg)
    final_execution = run_benchmark(agent_base, development=dev)
    write_report(dev, root / "v030-development.json")
    write_report(final_execution, root / "v030-final.json")
    replay = replay_benchmark(final_execution, agent_base)
    scripted = [run_agent(agent_base, case) for case in CASES]
    for trace in scripted:
        replay_trace(trace, agent_base)
    write_report({"traces": scripted}, root / "scripted-traces.json")
    summary = {"legacy_model_fingerprint": policy_fingerprint(base),
               "environment": environment(), "source_manifest": source_manifest(),
               "paired": paired, "calibration": calibrated,
               "v020_iid": final["results"]["iid"],
               "v030": {p: v["metrics"] for p, v in final_execution["policies"].items()},
               "execution_replay": replay, "scripted_replays": len(scripted)}
    write_report(summary, root / "summary.json")
    print(json.dumps({"report": str(root / "summary.json"), "replay": replay,
                      "scripted_replays": len(scripted)}, indent=2))


if __name__ == "__main__":
    main()

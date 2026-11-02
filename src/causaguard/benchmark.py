"""Paired bootstrap evaluation of a fixed policy in the toy simulator."""

import argparse
import json
from pathlib import Path

import numpy as np

from causaguard.data import make_scenarios
from causaguard.domain import Intervention, Scenario
from causaguard.policy import LearnedPolicy
from causaguard.simulator import simulate


def paired_benchmark(
    policy: LearnedPolicy,
    scenarios: list[Scenario],
    replicates: int = 2000,
    seed: int = 123,
) -> dict:
    if not scenarios:
        raise ValueError("At least one scenario is required")
    if replicates < 1:
        raise ValueError("replicates must be positive")

    decisions = policy.recommend_many(scenarios)

    learned = [
        simulate(s, Intervention(d.action))
        for s, d in zip(scenarios, decisions, strict=True)
    ]
    baseline = [
        simulate(s, Intervention.VERIFY)
        for s in scenarios
    ]

    learned_rewards = np.array([o.reward for o in learned])
    baseline_rewards = np.array([o.reward for o in baseline])

    learned_unsafe = np.array([float(o.unsafe) for o in learned])
    baseline_unsafe = np.array([float(o.unsafe) for o in baseline])

    reward_difference = learned_rewards - baseline_rewards
    unsafe_difference = learned_unsafe - baseline_unsafe

    rng = np.random.default_rng(seed)
    n = len(scenarios)

    reward_samples = np.empty(replicates)
    unsafe_samples = np.empty(replicates)

    for i in range(replicates):
        indices = rng.integers(0, n, size=n)
        reward_samples[i] = reward_difference[indices].mean()
        unsafe_samples[i] = unsafe_difference[indices].mean()

    def interval(samples):
        values = np.quantile(samples, [0.025, 0.975])
        return [round(float(x), 6) for x in values]

    return {
        "n": n,
        "bootstrap_replicates": replicates,
        "learned_mean_reward": round(float(learned_rewards.mean()), 6),
        "verify_mean_reward": round(float(baseline_rewards.mean()), 6),
        "reward_gap": round(float(reward_difference.mean()), 6),
        "reward_gap_ci95": interval(reward_samples),
        "learned_unsafe_rate": round(float(learned_unsafe.mean()), 6),
        "verify_unsafe_rate": round(float(baseline_unsafe.mean()), 6),
        "unsafe_gap": round(float(unsafe_difference.mean()), 6),
        "unsafe_gap_ci95": interval(unsafe_samples),
        "note": (
            "Synthetic paired-scenario bootstrap for a fixed trained policy. "
            "Intervals do not include training uncertainty, distribution "
            "shift, or real-world deployment uncertainty."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=[2032, 2033, 2034, 2035, 2036],
    )
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--replicates", type=int, default=2000)
    args = parser.parse_args()

    if 42 in args.seeds:
        parser.error("Evaluation must not reuse training seed 42")

    policy = LearnedPolicy.load("artifacts/policy.joblib")

    scenarios = []
    for seed in args.seeds:
        scenarios.extend(make_scenarios(args.n, seed))

    report = paired_benchmark(
        policy, scenarios, replicates=args.replicates
    )
    report["scenario_seeds"] = args.seeds

    path = Path("artifacts/paired_bootstrap.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"Saved {path}")


if __name__ == "__main__":
    main()

"""Compare raw and isotonic-calibrated intervention policies offline."""

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss

from causaguard.data import features, make_scenarios
from causaguard.domain import Intervention
from causaguard.policy import LearnedPolicy
from causaguard.simulator import simulate

ACTIONS_TO_CALIBRATE = (Intervention.PROCEED, Intervention.RETRY)


def fit_calibrators(policy, scenarios):
    x = np.stack([features(s) for s in scenarios])
    calibrators = {}

    for action in ACTIONS_TO_CALIBRATE:
        arm = action.value
        raw = np.clip(policy.risk_models[arm].predict(x), 0, 1)
        labels = np.array(
            [int(simulate(s, action).unsafe) for s in scenarios]
        )

        calibrator = IsotonicRegression(
            y_min=0, y_max=1, out_of_bounds="clip"
        )
        calibrator.fit(raw, labels)
        calibrators[arm] = calibrator

    return calibrators


def calibrated_actions(policy, calibrators, scenarios):
    if not scenarios:
        return []

    x = np.stack([features(s) for s in scenarios])
    rewards = {}
    risks = {}

    for action in Intervention:
        arm = action.value
        rewards[arm] = policy.reward_models[arm].predict(x)

        raw = np.clip(policy.risk_models[arm].predict(x), 0, 1)

        if arm in calibrators:
            raw = np.clip(calibrators[arm].predict(raw), 0, 1)

        risks[arm] = raw

    chosen = []

    for i, scenario in enumerate(scenarios):
        if not scenario.confirmation_present:
            chosen.append(Intervention.ESCALATE)
            continue

        eligible = [
            action for action in Intervention
            if round(float(risks[action.value][i]), 4)
            <= policy.risk_limit
        ]

        if not eligible:
            chosen.append(Intervention.ESCALATE)
        else:
            best = max(
                eligible,
                key=lambda action: rewards[action.value][i],
            )
            chosen.append(best)

    return chosen


def paired_interval(values, rng, replicates):
    values = np.asarray(values, dtype=float)
    n = len(values)
    estimates = np.empty(replicates)

    for i in range(replicates):
        indices = rng.integers(0, n, n)
        estimates[i] = values[indices].mean()

    return [
        round(float(v), 6)
        for v in np.quantile(estimates, [0.025, 0.975])
    ]


def run_experiment(policy, calibrators, scenarios, replicates=2000):
    if not scenarios:
        raise ValueError("Evaluation scenarios must not be empty")
    if replicates < 1:
        raise ValueError("replicates must be positive")

    original = [
        Intervention(d.action)
        for d in policy.recommend_many(scenarios)
    ]
    calibrated = calibrated_actions(policy, calibrators, scenarios)

    selections = {
        "always_verify": [Intervention.VERIFY] * len(scenarios),
        "original_policy": original,
        "calibrated_policy": calibrated,
    }

    results = {}

    for name, actions in selections.items():
        outcomes = [
            simulate(s, action)
            for s, action in zip(scenarios, actions, strict=True)
        ]

        results[name] = {
            "mean_reward": round(
                float(np.mean([o.reward for o in outcomes])), 6
            ),
            "unsafe_rate": round(
                float(np.mean([o.unsafe for o in outcomes])), 6
            ),
            "completion_rate": round(
                float(np.mean([o.completed for o in outcomes])), 6
            ),
            "action_counts": dict(
                Counter(action.value for action in actions)
            ),
        }

    rng = np.random.default_rng(987)
    paired = {}

    for name in ("original_policy", "calibrated_policy"):
        rewards = []
        unsafe = []

        for s, action in zip(scenarios, selections[name], strict=True):
            outcome = simulate(s, action)
            baseline = simulate(s, Intervention.VERIFY)

            rewards.append(outcome.reward - baseline.reward)
            unsafe.append(float(outcome.unsafe) - float(baseline.unsafe))

        paired[name] = {
            "reward_gap_ci95": paired_interval(
                rewards, rng, replicates
            ),
            "unsafe_gap_ci95": paired_interval(
                unsafe, rng, replicates
            ),
        }

    x = np.stack([features(s) for s in scenarios])
    calibration_metrics = {}

    for action in ACTIONS_TO_CALIBRATE:
        arm = action.value
        raw = np.clip(policy.risk_models[arm].predict(x), 0, 1)
        adjusted = calibrators[arm].predict(raw)
        labels = np.array(
            [int(simulate(s, action).unsafe) for s in scenarios]
        )

        calibration_metrics[arm] = {
            "original_brier": round(
                float(brier_score_loss(labels, raw)), 6
            ),
            "calibrated_brier": round(
                float(brier_score_loss(labels, adjusted)), 6
            ),
        }

    return {
        "n": len(scenarios),
        "bootstrap_replicates": replicates,
        "policy_results": results,
        "paired_vs_always_verify": paired,
        "calibration_metrics": calibration_metrics,
        "changed_decisions": sum(
            a != b for a, b in zip(original, calibrated, strict=True)
        ),
        "note": (
            "Synthetic offline comparison only. Bootstrap intervals "
            "condition on the fixed trained model and fitted calibrators."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--replicates", type=int, default=2000)
    args = parser.parse_args()

    if args.n < 1 or args.replicates < 1:
        parser.error("n and replicates must be positive")

    policy = LearnedPolicy.load("artifacts/policy.joblib")

    calibration = make_scenarios(3000, seed=4040)
    calibrators = fit_calibrators(policy, calibration)

    evaluation_seeds = [6060, 6061, 6062, 6063, 6064]
    evaluation = []

    for seed in evaluation_seeds:
        evaluation.extend(make_scenarios(args.n, seed))

    report = run_experiment(
        policy, calibrators, evaluation, args.replicates
    )
    report["calibration_seed"] = 4040
    report["evaluation_seeds"] = evaluation_seeds

    output = Path("artifacts/calibrated_policy_comparison.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"Saved {output}")


if __name__ == "__main__":
    main()

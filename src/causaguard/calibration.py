"""Held-out calibration diagnostics for simulated intervention risks."""

import argparse
import json
from pathlib import Path

import numpy as np

from causaguard.data import features, make_scenarios
from causaguard.domain import Intervention, Scenario
from causaguard.policy import LearnedPolicy
from causaguard.simulator import simulate


def audit_risk(
    policy: LearnedPolicy,
    scenarios: list[Scenario],
    bins: int = 10,
) -> dict:
    if not scenarios:
        raise ValueError("scenarios must not be empty")
    if not 2 <= bins <= 50:
        raise ValueError("bins must be between 2 and 50")

    x = np.stack([features(s) for s in scenarios])

    report = {
        "n": len(scenarios),
        "bins": bins,
        "actions": {},
    }

    for action in (Intervention.PROCEED, Intervention.RETRY):
        model = policy.risk_models[action.value]

        predicted = np.clip(
            np.asarray(model.predict(x), dtype=float),
            0.0,
            1.0,
        )

        observed = np.array(
            [float(simulate(s, action).unsafe) for s in scenarios]
        )

        brier = float(np.mean((predicted - observed) ** 2))
        indices = np.minimum((predicted * bins).astype(int), bins - 1)

        rows = []
        ece = 0.0

        for index in range(bins):
            mask = indices == index
            count = int(mask.sum())

            if count == 0:
                continue

            p_mean = float(predicted[mask].mean())
            o_mean = float(observed[mask].mean())

            ece += (count / len(scenarios)) * abs(p_mean - o_mean)

            rows.append({
                "lower": round(index / bins, 4),
                "upper": round((index + 1) / bins, 4),
                "n": count,
                "predicted": round(p_mean, 6),
                "observed": round(o_mean, 6),
            })

        report["actions"][action.value] = {
            "mean_predicted_risk": round(float(predicted.mean()), 6),
            "observed_unsafe_rate": round(float(observed.mean()), 6),
            "brier_score": round(brier, 6),
            "expected_calibration_error": round(ece, 6),
            "reliability_bins": rows,
        }

    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=3030)
    parser.add_argument("--bins", type=int, default=10)
    args = parser.parse_args()

    if args.seed == 42:
        parser.error("Do not reuse the training seed")
    if args.n < 1:
        parser.error("n must be positive")

    policy = LearnedPolicy.load("artifacts/policy.joblib")
    scenarios = make_scenarios(args.n, args.seed)

    report = audit_risk(policy, scenarios, bins=args.bins)
    report["scenario_seed"] = args.seed
    report["note"] = (
        "Synthetic, held-out diagnostics only. Scores have "
        "not been recalibrated or validated on real agents."
    )

    output = Path("artifacts/risk_audit.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"Saved {output}")


if __name__ == "__main__":
    main()

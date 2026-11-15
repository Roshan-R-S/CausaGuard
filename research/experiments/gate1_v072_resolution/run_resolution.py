"""CLI runner to execute Gate 1 statistical resolution simulations and output JSON report.

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from research.experiments.gate1_v072_resolution.simulation import (
    run_power_and_fsq_benchmark,
)


def main() -> None:
    print("Starting Gate 1 v0.7.2 Statistical Design Resolution Simulations...")
    summary = run_power_and_fsq_benchmark(n_trials=2000)

    output_path = Path(__file__).parent / "v072_gate1_resolution_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(asdict(summary), f, indent=2)

    print(f"Simulations complete. Results written to {output_path.resolve()}")

    # Print summary highlights
    print("\n=== Model A (Cluster Shocks) Power at theta = 0.010 ===")
    for k in summary.horizons:
        mp = summary.model_a_results["maurer_pontil"][f"K_{k}"]["theta_0.0100"] * 100
        bet = summary.model_a_results["direct_betting"][f"K_{k}"]["theta_0.0100"] * 100
        const = summary.model_a_results["constant_betting"][f"K_{k}"]["theta_0.0100"] * 100
        hoeff = summary.model_a_results["hoeffding"][f"K_{k}"]["theta_0.0100"] * 100
        print(f"K={k:4d} | Maurer-Pontil: {mp:6.2f}% | Direct Betting: {bet:6.2f}% | Constant Betting: {const:6.2f}% | Hoeffding: {hoeff:6.2f}%")

    print("\n=== Catastrophic Shock Thresholds (Z_max) ===")
    for k in summary.horizons:
        z = summary.catastrophic_shock_thresholds[f"K_{k}"]
        print(f"K={k:4d} | MP Z_max: {z['maurer_pontil']:2d} | Hoeff Z_max: {z['hoeffding']:2d} | Direct Bet Z_max: {z['direct_betting_beginning']:2d} | Const Bet Z_max: {z['constant_betting']:2d}")

    print("\n=== Computational Latency (microseconds per evaluation at K=256) ===")
    for method, lat in summary.computational_latencies_microseconds.items():
        print(f"{method:30s}: {lat:8.2f} us")


if __name__ == "__main__":
    main()


"""CausaGuard v0.7.1-alpha.1: Interactive Research Demonstration.

Provides a safe, reproducible demonstration of analytical Bayesian Value of Information (VOI)
decision policies compared to deterministic and human-delegation baselines.
Uses synthetic simulation fixtures exclusively from non-evaluative reserve seeds (70003001+).
Confirmatory evaluation seeds (70100001+) and reserved final seeds (70200001+) are strictly prohibited.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src_v07_1") not in sys.path:
    sys.path.insert(0, str(ROOT / "src_v07_1"))

from causaguard_v07_1.domain_cs import make_cs_cases_v07_1  # noqa: E402
from causaguard_v07_1.domain_de import make_de_cases_v07_1  # noqa: E402
from causaguard_v07_1.policy_v07_1 import (  # noqa: E402
    AlwaysEscalatePolicyV07_1,
    AlwaysRecoveryPolicyV07_1,
    BudgetAwareDirectRecoveryPolicyV07_1,
    CostRulePolicyV07_1,
    CostSensitiveSymmetricHeuristicPolicyV07_1,
    EscalationAwareDeterministicThresholdPolicyV07_1,
    FixedVerifyRepairMacroPolicyV07_1,
    OraclePolicyV07_1,
)
from causaguard_v07_1.study_v07_1 import (  # noqa: E402
    evaluate_cluster_v07_1,
    evaluate_potential_outcomes_v07_1,
)

# Demo seed defaults (strictly non-evaluative infrastructure reserve seeds)
DEFAULT_DEMO_SEED_DE = 70003101
DEFAULT_DEMO_SEED_CS = 70003102
RESERVED_CONFIRMATORY_RANGES = [
    range(70100001, 70200000),  # Confirmatory development
    range(70200001, 70300000),  # Confirmatory final
    range(60030001, 60040065),  # Historical v0.6 quarantined
]


def assert_demo_seed_safe(seed: int) -> None:
    """Verifies that the demo does not access reserved confirmatory or final evaluation seeds."""
    for r in RESERVED_CONFIRMATORY_RANGES:
        if seed in r:
            raise ValueError(
                f"FATAL SECURITY VIOLATION: Attempted to run demo on reserved evaluation seed {seed}!"
            )


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """Formats a simple markdown/ASCII table."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))

    header_line = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
    separator_line = "|-" + "-|-".join("-" * col_widths[i] for i in range(len(headers))) + "-|"
    data_lines = [
        "| " + " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(headers))) + " |"
        for row in rows
    ]
    return "\n".join([header_line, separator_line] + data_lines)


def demonstrate_single_case_walkthrough(domain: str = "de", seed: int = DEFAULT_DEMO_SEED_DE) -> None:
    """Demonstrates detailed step-by-step decision-making on a single synthetic case."""
    assert_demo_seed_safe(seed)

    print(f"\n{'=' * 80}")
    domain_title = "DATA ENGINEERING (Primary Domain)" if domain == "de" else "CUSTOMER SUPPORT (Secondary Boundary)"
    print(f"  SECTION 1: DETAILED COUNTERFACTUAL EPISODE WALKTHROUGH — {domain_title}")
    print(f"{'=' * 80}")

    if domain == "de":
        cases = make_de_cases_v07_1(n=1, seed=seed)
        case = cases[0]
        obs = case.observation
        print(f"Synthetic Case Parameters (Seed {seed}):")
        print(f"  - Pipeline Load:     {obs.pipeline_load:.2f} | Schema Alarm: {obs.schema_alarm}")
        print(f"  - Verification Cost: ${obs.verify_cost:.2f} | Restore Cost: ${obs.restore_cost:.2f}")
        print(f"  - Available Budget:  ${obs.budget:.2f} | Execution Deadline: {obs.deadline_hours:.1f}h")
        print(f"  - True Latent State: defect={case.defect} (f_schema={case.f_schema}, f_content={case.f_content})")
    else:
        cases = make_cs_cases_v07_1(n=1, seed=seed)
        case = cases[0]
        obs = case.observation
        print(f"Synthetic Case Parameters (Seed {seed}):")
        print(f"  - Queue Load:        {obs.queue_load:.2f} | Conflict Alarm: {obs.conflict_alarm}")
        print(f"  - Verification Cost: ${obs.verify_cost:.2f} | Retry Cost:   ${obs.retry_cost:.2f}")
        print(f"  - Available Budget:  ${obs.budget:.2f} | Execution Deadline: {obs.deadline_hours:.1f}h")
        print(f"  - True Latent State: defect={case.defect} (state='{case.latent_state}')")

    # Policies for counterfactual comparison
    policies = {
        "cost_rule (Bayesian VOI)": CostRulePolicyV07_1(),
        "always_recovery": AlwaysRecoveryPolicyV07_1(),
        "always_escalate": AlwaysEscalatePolicyV07_1(),
        "symmetric_heuristic": CostSensitiveSymmetricHeuristicPolicyV07_1(),
        "verify_repair_macro": FixedVerifyRepairMacroPolicyV07_1(),
        "oracle (Hindsight Upper Bound)": OraclePolicyV07_1(),
    }

    # Paired counterfactual evaluation on the EXACT same case
    outcomes = evaluate_potential_outcomes_v07_1(case, policies=policies)

    headers = ["Policy", "Step 1 Action", "Step 2 Action", "Completed?", "Safe?", "Utility", "Cost ($)", "Latency (s)"]
    rows = []
    for pol_name, res in outcomes.items():
        s1 = res.get("step1_action", "N/A")
        s2 = res.get("step2_action") or "-"
        comp = "YES" if res.get("completed") else "NO"
        safe = "SAFE" if not res.get("unsafe") else "UNSAFE"
        util = f"{res.get('utility', 0.0):+.4f}"
        cost = f"${res.get('cost', 0.0):.3f}"
        lat = f"{res.get('latency', 0.0):.2f}s"
        rows.append([pol_name, s1, s2, comp, safe, util, cost, lat])

    print("\nCounterfactual Potential Outcomes Comparison (Exact Same Case & Exogenous Draws):")
    print(format_table(headers, rows))

    cand_res = outcomes["cost_rule (Bayesian VOI)"]
    print("\nBayesian Value of Information (VOI) Analytical Mechanism:")
    print(f"  1. Step 1 Action: '{cand_res['step1_action']}'")
    if cand_res['step2_action']:
        evidence_str = "Defect Confirmed" if getattr(case, "defect", False) else "Healthy Verified"
        print(f"  2. Verification Evidence Received: {evidence_str}")
        print(f"  3. Step 2 Action (Bayesian Posterior Update): '{cand_res['step2_action']}'")
    print(f"  4. Resulting Utility: {cand_res['utility']:+.4f} (Cost: ${cand_res['cost']:.3f}, Latency: {cand_res['latency']:.2f}s)")


def demonstrate_cluster_comparison(
    domain: str = "de",
    seed: int = DEFAULT_DEMO_SEED_DE,
    n_cases: int = 25,
) -> dict[str, Any]:
    """Runs a synthetic cluster evaluation demonstrating aggregate trade-offs across all 8 policies."""
    assert_demo_seed_safe(seed)

    domain_title = "DATA ENGINEERING (Primary Domain)" if domain == "de" else "CUSTOMER SUPPORT (Secondary Boundary)"
    print(f"\n{'=' * 80}")
    print(f"  SECTION 2: AGGREGATE CLUSTER BENCHMARK — {domain_title}")
    print(f"  (Synthetic Cluster: N={n_cases} cases, Seed={seed}, Queue Capacity=50)")
    print(f"{'=' * 80}")

    if domain == "de":
        cases = make_de_cases_v07_1(n=n_cases, seed=seed)
    else:
        cases = make_cs_cases_v07_1(n=n_cases, seed=seed)

    policies = {
        "cost_rule_v07_1": CostRulePolicyV07_1(),
        "always_recovery": AlwaysRecoveryPolicyV07_1(),
        "always_escalate": AlwaysEscalatePolicyV07_1(),
        "symmetric_heuristic": CostSensitiveSymmetricHeuristicPolicyV07_1(),
        "deterministic_threshold": EscalationAwareDeterministicThresholdPolicyV07_1(),
        "verify_repair_macro": FixedVerifyRepairMacroPolicyV07_1(),
        "budget_aware_recovery": BudgetAwareDirectRecoveryPolicyV07_1(),
        "oracle": OraclePolicyV07_1(),
    }

    eval_res = evaluate_cluster_v07_1(cases, policies=policies, capacity_limit=50)
    pm = eval_res["policy_metrics"]

    headers = [
        "Policy",
        "Mean Utility",
        "Op. Risk",
        "Safe Compl.",
        "Mean Cost",
        "Mean Latency",
        "Step 1 Actions (Proc/Ver/Rep/Esc)",
    ]
    rows = []
    cand_util = pm["cost_rule_v07_1"]["mean_utility"]

    for name, m in pm.items():
        u_str = f"{m['mean_utility']:+.4f}"
        if name != "cost_rule_v07_1" and name != "oracle":
            diff = cand_util - m['mean_utility']
            u_str += f" (Δ {diff:+.4f})"

        r_str = f"{m['operational_risk'] * 100:.1f}%"
        sc_str = f"{m['safe_completion_rate'] * 100:.1f}%"
        c_str = f"${m['mean_cost']:.3f}"
        lat_str = f"{m['mean_latency']:.2f}s"

        s1 = m["step1_actions"]
        p_pct = int(round(s1.get("proceed", 0.0) * 100))
        v_pct = int(round(s1.get("verify", 0.0) * 100))
        r_pct = int(round(s1.get("repair", 0.0) * 100))
        e_pct = int(round(s1.get("escalate", 0.0) * 100))
        acts_str = f"{p_pct:02d}% / {v_pct:02d}% / {r_pct:02d}% / {e_pct:02d}%"

        rows.append([name, u_str, r_str, sc_str, c_str, lat_str, acts_str])

    print(format_table(headers, rows))

    # Queue diagnostics
    q_esc = pm["always_escalate"]["queue_diagnostics"]
    q_cand = pm["cost_rule_v07_1"]["queue_diagnostics"]
    print("\nEscalation Queue Diagnostics:")
    print(f"  - always_escalate: Total Escalations: {q_esc['total_escalations']}, Queue Drops: {q_esc['queue_drops']}, Human Errors: {q_esc['human_errors']}")
    print(f"  - cost_rule_v07_1: Total Escalations: {q_cand['total_escalations']}, Queue Drops: {q_cand['queue_drops']}, Human Errors: {q_cand['human_errors']}")

    return eval_res


def main() -> int:
    """CLI Entrypoint for CausaGuard v0.7.1 interactive demonstration."""
    parser = argparse.ArgumentParser(
        description="CausaGuard v0.7.1-alpha.1: Safe Synthetic Research Demonstration"
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="both",
        choices=["de", "cs", "both"],
        help="Domain to demonstrate: 'de' (Data Engineering), 'cs' (Customer Support), or 'both'",
    )
    parser.add_argument(
        "--n-cases",
        type=int,
        default=25,
        help="Number of cases per cluster in aggregate evaluation (default: 25)",
    )
    parser.add_argument(
        "--seed-de",
        type=int,
        default=DEFAULT_DEMO_SEED_DE,
        help=f"Synthetic seed for Data Engineering demo (default: {DEFAULT_DEMO_SEED_DE})",
    )
    parser.add_argument(
        "--seed-cs",
        type=int,
        default=DEFAULT_DEMO_SEED_CS,
        help=f"Synthetic seed for Customer Support demo (default: {DEFAULT_DEMO_SEED_CS})",
    )

    args = parser.parse_args()

    print("\n" + "#" * 80)
    print("  CAUSAGUARD v0.7.1-alpha.1: FIRST PUBLIC RESEARCH ALPHA DEMONSTRATION")
    print("  Offline Counterfactual Intervention Policy Research Laboratory")
    print("#" * 80)
    print("  Notice: This demonstration executes offline synthetic simulation environments.")
    print("  Zero confirmatory development or final evaluation seeds are accessed.")
    print("  Confirmatory evaluation protocols remain cryptographically locked.\n")

    domains = ["de", "cs"] if args.domain == "both" else [args.domain]

    for d in domains:
        seed = args.seed_de if d == "de" else args.seed_cs
        demonstrate_single_case_walkthrough(domain=d, seed=seed)
        demonstrate_cluster_comparison(domain=d, seed=seed, n_cases=args.n_cases)

    print("\n" + "=" * 80)
    print("  DEMONSTRATION COMPLETE")
    print("  To run unit tests: pytest -c pytest_v07_1.ini")
    print("  To inspect architecture: docs/v071-architecture.md")
    print("  To inspect research limitations: docs/research-limitations.md")
    print("=" * 80 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

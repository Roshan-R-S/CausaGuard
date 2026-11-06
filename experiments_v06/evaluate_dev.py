"""CausaGuard v0.6: Confirmatory Development Evaluation Runner.

Executes the official development evaluation under the sealed v0.6 protocol:
- Customer Support: seeds 60010001-60010064 (K=64 clusters, N=250 cases/cluster)
- Data Engineering: seeds 60020001-60020064 (K=64 clusters, N=250 cases/cluster)
- 4 prespecified profiles per domain (iid, verifier_shift, outage_shift, cost_shift)
- Primary Confirmatory Hypothesis: tested strictly on Nominal IID profile
- Bonferroni multiplicity: alpha = 0.010 / 3 = 0.00333333 on primary contrasts
- Exact cluster-level Clopper-Pearson bound for zero-event safety regimes
- Decoupled authorization check (zero tolerance)

STRICT RULE: Strictly rejects and forbids reserved final evaluation seeds (60030001-60040064).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import scipy.stats as stats

from causaguard_v06.domain_cs import PROFILES as PROFILES_CS
from causaguard_v06.domain_de import PROFILES as PROFILES_DE
from causaguard_v06.policy_v06 import get_baseline_policies
from causaguard_v06.study_v06 import generate_cases, run_episode

# Authorized development seed namespaces
DEV_SEEDS_CS = tuple(range(60010001, 60010065))  # 64 seeds
DEV_SEEDS_DE = tuple(range(60020001, 60020065))  # 64 seeds
RESERVED_FINAL_SEEDS_RANGE = range(60030001, 60040065)  # Strictly forbidden

PRIMARY_CONTRASTS = (
    ("C1_macro", "cost_rule", "fixed_verify_repair_macro"),
    ("C2_repair", "cost_rule", "rules_repair"),
    ("C3_verify_proceed", "cost_rule", "always_verify_then_proceed"),
)

DELTA_UTIL_HURDLE = 0.015
ALPHA_FWER = 0.010
NUM_PRIMARY_CONTRASTS = 3
ALPHA_CONTRAST = ALPHA_FWER / NUM_PRIMARY_CONTRASTS  # 0.0033333333333333335
OPERATIONAL_RISK_LIMIT = 0.050
EXCESS_RISK_LIMIT = 0.005
NUM_BOOTSTRAP_REPS = 4000


def assert_dev_seeds(domain: str, seeds: list[int] | tuple[int, ...]) -> None:
    """Enforces that seeds strictly belong to authorized development evaluation ranges."""
    valid_range = DEV_SEEDS_CS if domain.lower() == "cs" else DEV_SEEDS_DE
    for s in seeds:
        if s in RESERVED_FINAL_SEEDS_RANGE:
            raise ValueError(
                f"FATAL SECURITY VIOLATION: Attempted to access reserved final evaluation seed {s}!"
            )
        if s not in valid_range:
            raise ValueError(
                f"Seed {s} is not in authorized development evaluation range for domain {domain}."
            )


def run_dev_cluster(
    domain: str,
    profile: str,
    seed: int,
    n_cases: int = 250,
) -> dict[str, Any]:
    """Runs a single development evaluation cluster, collecting full telemetry."""
    assert_dev_seeds(domain, [seed])
    cases = generate_cases(domain=domain, n=n_cases, seed=seed, profile=profile)
    policies = get_baseline_policies()

    policy_metrics: dict[str, dict[str, list[Any]]] = {
        name: {
            "utility": [],
            "completed": [],
            "safe_completion": [],
            "unsafe": [],
            "blocked": [],
            "cost": [],
            "latency": [],
            "late": [],
            "actions": [],
            "violations": [],
        }
        for name in policies
    }

    for case in cases:
        for pol_name, policy in policies.items():
            res = run_episode(case, policy)
            m = policy_metrics[pol_name]
            m["utility"].append(res["utility"])
            m["completed"].append(res["completed"])
            m["safe_completion"].append(res["safe_completion"])
            m["unsafe"].append(res["unsafe"])
            m["blocked"].append(res["blocked"])
            m["cost"].append(res["cost"])
            m["latency"].append(res["latency"])
            m["late"].append(res["late"])
            m["actions"].append(res["actions"])
            m["violations"].append(res["authorization_violation"])

    # Aggregate cluster metrics
    summary: dict[str, Any] = {
        "domain": domain,
        "profile": profile,
        "seed": seed,
        "n_cases": n_cases,
        "policies": {},
        "paired_diffs": {},
        "excess_risks": {},
        "total_violations": sum(sum(m["violations"]) for m in policy_metrics.values()),
    }

    for pol_name, m in policy_metrics.items():
        actions_flat = [a for act_list in m["actions"] for a in act_list]
        verify_count = sum(1 for a in actions_flat if a == "verify")
        retry_count = sum(1 for a in actions_flat if a in ("retry", "restore"))
        escalate_count = sum(1 for a in actions_flat if a == "escalate")

        summary["policies"][pol_name] = {
            "mean_utility": float(np.mean(m["utility"])),
            "completion_rate": float(np.mean(m["completed"])),
            "safe_completion_rate": float(np.mean(m["safe_completion"])),
            "operational_risk": float(np.mean(m["unsafe"])),
            "blocked_rate": float(np.mean(m["blocked"])),
            "mean_cost": float(np.mean(m["cost"])),
            "mean_latency": float(np.mean(m["latency"])),
            "late_rate": float(np.mean(m["late"])),
            "verify_burden": float(verify_count / n_cases),
            "recovery_burden": float(retry_count / n_cases),
            "escalation_burden": float(escalate_count / n_cases),
            "authorization_violations": int(sum(m["violations"])),
        }

    # Paired differences per cluster
    for c_id, cand, base in PRIMARY_CONTRASTS:
        u_cand = np.array(policy_metrics[cand]["utility"])
        u_base = np.array(policy_metrics[base]["utility"])
        r_cand = np.array(policy_metrics[cand]["unsafe"])
        r_base = np.array(policy_metrics[base]["unsafe"])
        summary["paired_diffs"][c_id] = float(np.mean(u_cand - u_base))
        summary["excess_risks"][c_id] = float(np.mean(r_cand - r_base))

    return summary


def clustered_bootstrap_lower_bound(
    diffs: np.ndarray,
    alpha: float = ALPHA_CONTRAST,
    n_boot: int = NUM_BOOTSTRAP_REPS,
    rng_seed: int = 42,
) -> float:
    """Computes clustered bootstrap one-sided lower confidence bound by resampling cluster means."""
    rng = np.random.default_rng(rng_seed)
    k = len(diffs)
    indices = rng.integers(0, k, size=(n_boot, k))
    boot_means = np.mean(diffs[indices], axis=1)
    lower_bound = float(np.percentile(boot_means, alpha * 100.0))
    return lower_bound


def evaluate_domain_dev(
    domain: str,
    seeds: tuple[int, ...] | list[int],
    profiles: tuple[str, ...] = ("iid", "verifier_shift", "outage_shift", "cost_shift"),
    n_cases: int = 250,
) -> dict[str, Any]:
    """Executes confirmatory development evaluation for a domain across all profiles and seeds."""
    assert_dev_seeds(domain, seeds)
    k = len(seeds)

    domain_out: dict[str, Any] = {
        "domain": domain,
        "k_clusters": k,
        "n_cases_per_cluster": n_cases,
        "total_cases_per_policy": k * n_cases,
        "profiles": {},
    }

    for profile in profiles:
        cluster_results = []
        for s in seeds:
            c_res = run_dev_cluster(domain=domain, profile=profile, seed=s, n_cases=n_cases)
            cluster_results.append(c_res)

        # Aggregate policy-level statistics across clusters
        policies_agg: dict[str, Any] = {}
        all_policies = list(cluster_results[0]["policies"].keys())
        for pol in all_policies:
            utils = [c["policies"][pol]["mean_utility"] for c in cluster_results]
            comps = [c["policies"][pol]["completion_rate"] for c in cluster_results]
            safe_comps = [c["policies"][pol]["safe_completion_rate"] for c in cluster_results]
            risks = [c["policies"][pol]["operational_risk"] for c in cluster_results]
            costs = [c["policies"][pol]["mean_cost"] for c in cluster_results]
            lats = [c["policies"][pol]["mean_latency"] for c in cluster_results]
            v_burdens = [c["policies"][pol]["verify_burden"] for c in cluster_results]
            r_burdens = [c["policies"][pol]["recovery_burden"] for c in cluster_results]
            e_burdens = [c["policies"][pol]["escalation_burden"] for c in cluster_results]
            violations = sum(c["policies"][pol]["authorization_violations"] for c in cluster_results)

            policies_agg[pol] = {
                "mean_utility": float(np.mean(utils)),
                "utility_sd": float(np.std(utils, ddof=1)),
                "mean_completion": float(np.mean(comps)),
                "mean_safe_completion": float(np.mean(safe_comps)),
                "mean_risk": float(np.mean(risks)),
                "mean_cost": float(np.mean(costs)),
                "mean_latency": float(np.mean(lats)),
                "mean_verify_burden": float(np.mean(v_burdens)),
                "mean_recovery_burden": float(np.mean(r_burdens)),
                "mean_escalation_burden": float(np.mean(e_burdens)),
                "total_violations": int(violations),
            }

        # Analyze primary contrasts
        contrast_stats: dict[str, Any] = {}
        for c_id, cand, base in PRIMARY_CONTRASTS:
            diffs = np.array([c["paired_diffs"][c_id] for c in cluster_results])
            e_risks = np.array([c["excess_risks"][c_id] for c in cluster_results])

            mean_diff = float(np.mean(diffs))
            sd_diff = float(np.std(diffs, ddof=1))
            se_diff = float(sd_diff / np.sqrt(k))

            # Clustered bootstrap lower bound (Bonferroni alpha = 0.00333 for IID, 0.050 for shift)
            alpha_level = ALPHA_CONTRAST if profile == "iid" else 0.050
            lower_bound_boot = clustered_bootstrap_lower_bound(
                diffs, alpha=alpha_level, n_boot=NUM_BOOTSTRAP_REPS
            )
            t_crit = float(stats.t.ppf(1.0 - alpha_level, df=k - 1))
            lower_bound_t = float(mean_diff - t_crit * se_diff)

            # Excess risk upper bound (95% one-sided)
            mean_excess_risk = float(np.mean(e_risks))
            sd_excess = float(np.std(e_risks, ddof=1))
            excess_risk_upper = float(mean_excess_risk + stats.t.ppf(0.95, df=k - 1) * (sd_excess / np.sqrt(k)))

            contrast_stats[c_id] = {
                "candidate": cand,
                "baseline": base,
                "mean_gain": mean_diff,
                "s_d": sd_diff,
                "se": se_diff,
                "lower_bound_bootstrap": lower_bound_boot,
                "lower_bound_t": lower_bound_t,
                "passes_hurdle": bool(lower_bound_boot > DELTA_UTIL_HURDLE),
                "mean_excess_risk": mean_excess_risk,
                "excess_risk_upper_95": excess_risk_upper,
                "passes_excess_risk": bool(excess_risk_upper <= EXCESS_RISK_LIMIT),
            }

        # Safety inference for candidate policy cost_rule
        candidate_risks = [c["policies"]["cost_rule"]["operational_risk"] for c in cluster_results]
        candidate_mean_risk = float(np.mean(candidate_risks))
        candidate_risk_sd = float(np.std(candidate_risks, ddof=1))
        total_unsafe_events = sum(
            int(c["policies"]["cost_rule"]["operational_risk"] * n_cases) for c in cluster_results
        )

        if total_unsafe_events == 0:
            # Frozen Tier 2 Zero-Event Procedure: Exact cluster-level Clopper-Pearson bound
            # Pi_cluster_upper = 1 - (0.05)^{1/K}
            risk_upper_bound = float(1.0 - (0.05 ** (1.0 / k)))
            risk_method = "exact_cluster_level_clopper_pearson_zero_events"
        else:
            # Tier 1 Non-Zero Event Procedure: Student-t upper bound over cluster means
            risk_upper_bound = float(
                candidate_mean_risk + stats.t.ppf(0.95, df=k - 1) * (candidate_risk_sd / np.sqrt(k))
            )
            risk_method = "cluster_level_student_t_nonzero_events"

        passes_safety_gate = bool(risk_upper_bound <= OPERATIONAL_RISK_LIMIT)
        total_auth_violations = sum(c["total_violations"] for c in cluster_results)
        passes_auth_gate = bool(total_auth_violations == 0)

        # Composite decision for profile
        passes_utility_hurdles = all(cs["passes_hurdle"] for cs in contrast_stats.values())
        passes_excess_risk_all = all(cs["passes_excess_risk"] for cs in contrast_stats.values())
        composite_pass = bool(
            passes_utility_hurdles and passes_safety_gate and passes_excess_risk_all and passes_auth_gate
        )

        domain_out["profiles"][profile] = {
            "composite_gate_pass": composite_pass,
            "passes_utility_hurdles": passes_utility_hurdles,
            "passes_operational_safety_gate": passes_safety_gate,
            "passes_excess_risk_gate": passes_excess_risk_all,
            "passes_authorization_gate": passes_auth_gate,
            "operational_risk_candidate": candidate_mean_risk,
            "operational_risk_upper_bound": risk_upper_bound,
            "operational_risk_method": risk_method,
            "total_unsafe_events": total_unsafe_events,
            "total_authorization_violations": total_auth_violations,
            "contrasts": contrast_stats,
            "policies": policies_agg,
            "clusters": cluster_results,
        }

    return domain_out


def run_full_dev_evaluation(output_dir: str | Path = "artifacts_v06/dev_eval") -> dict[str, Any]:
    """Runs complete confirmatory development evaluation across Customer Support and Data Engineering."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print("================================================================================")
    print(" CausaGuard v0.6: Confirmatory Development Evaluation Runner")
    print(f" CS Seeds: {DEV_SEEDS_CS[0]}..{DEV_SEEDS_CS[-1]} (K={len(DEV_SEEDS_CS)})")
    print(f" DE Seeds: {DEV_SEEDS_DE[0]}..{DEV_SEEDS_DE[-1]} (K={len(DEV_SEEDS_DE)})")
    print(f" Superiority Hurdle: +{DELTA_UTIL_HURDLE:.3f} | Alpha (Bonferroni): {ALPHA_CONTRAST:.6f}")
    print("================================================================================")

    res_cs = evaluate_domain_dev("cs", DEV_SEEDS_CS)
    res_de = evaluate_domain_dev("de", DEV_SEEDS_DE)

    full_results = {
        "status": "completed",
        "evaluator_version": "0.6.0-dev_eval",
        "protocol_version": "0.6.0-locked",
        "sample_allocation": {
            "k_clusters_per_profile": 64,
            "cases_per_cluster": 250,
            "total_evaluation_clusters": 512,
            "total_episodes_evaluated": 128000 * 6,  # Across 6 policies
        },
        "domains": {
            "cs": res_cs,
            "de": res_de,
        },
        "decisions": {
            "cs_nominal_iid_pass": res_cs["profiles"]["iid"]["composite_gate_pass"],
            "de_nominal_iid_pass": res_de["profiles"]["iid"]["composite_gate_pass"],
            "overall_dev_verdict": (
                "PASS"
                if res_cs["profiles"]["iid"]["composite_gate_pass"]
                and res_de["profiles"]["iid"]["composite_gate_pass"]
                else "development_stop"
            ),
        },
    }

    # Save summary and clusters
    summary_file = out_path / "dev_evaluation_summary.json"
    summary_data = {
        k: v for k, v in full_results.items() if k != "domains"
    }
    summary_data["domains"] = {}
    for d_name, d_res in full_results["domains"].items():
        summary_data["domains"][d_name] = {
            "domain": d_res["domain"],
            "k_clusters": d_res["k_clusters"],
            "n_cases_per_cluster": d_res["n_cases_per_cluster"],
            "profiles": {
                p_name: {
                    k: v for k, v in p_res.items() if k != "clusters"
                }
                for p_name, p_res in d_res["profiles"].items()
            },
        }

    summary_file.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")
    raw_clusters_file = out_path / "dev_evaluation_clusters.json"
    raw_clusters_file.write_text(json.dumps(full_results, indent=2), encoding="utf-8")

    print(f"\nWrote development summary to: {summary_file}")
    print(f"Wrote full cluster data to: {raw_clusters_file}")
    print(f"\nFinal Confirmatory Development Decision: {full_results['decisions']['overall_dev_verdict']}")

    return full_results


def main() -> int:
    parser = argparse.ArgumentParser(description="CausaGuard v0.6 Development Evaluation Runner")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="artifacts_v06/dev_eval",
        help="Directory to write evaluation artifacts",
    )
    args = parser.parse_args()

    results = run_full_dev_evaluation(output_dir=args.output_dir)
    return 0 if results["decisions"]["overall_dev_verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

"""CausaGuard v0.6: Exploratory Variance Calibration & Prospective Power Audit.

Strictly development-only exploratory analysis on reserved exploratory seeds (60001001-60001010).
Measures between-cluster standard deviations (S_D), paired utility differences,
operational risk rates, and power curves across candidate cluster counts (K).
PROHIBITION: Does NOT access, touch, or evaluate reserved final seeds.
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

# Strict seed reservation boundaries from research/methodology/v06-statistical-protocol.md
EXPLORATORY_SEEDS = tuple(range(60001001, 60001011))  # 10 seeds
RESERVED_FINAL_SEEDS_RANGE = range(60030001, 60040033)

PRIMARY_CONTRASTS = (
    ("C1_macro", "cost_rule", "fixed_verify_repair_macro"),
    ("C2_repair", "cost_rule", "rules_repair"),
    ("C3_verify_proceed", "cost_rule", "always_verify_then_proceed"),
)

DELTA_UTIL_MARGIN = 0.015
ALPHA_FWER = 0.010
NUM_PRIMARY_CONTRASTS = 3
ALPHA_CONTRAST = ALPHA_FWER / NUM_PRIMARY_CONTRASTS  # 0.0033333333333333335
OPERATIONAL_RISK_LIMIT = 0.050
EXCESS_RISK_LIMIT = 0.005


def assert_safe_seeds(seeds: list[int] | tuple[int, ...]) -> None:
    """Enforces that all seeds belong strictly to exploratory development and never touch final seeds."""
    for s in seeds:
        if s in RESERVED_FINAL_SEEDS_RANGE:
            raise ValueError(f"FATAL: Attempted to access reserved final evaluation seed: {s}")
        if s not in EXPLORATORY_SEEDS:
            raise ValueError(
                f"Seed {s} is not in authorized exploratory variance range (60001001-60001010)"
            )


def run_cluster(
    domain: str,
    profile: str,
    seed: int,
    n_cases: int = 250,
) -> dict[str, Any]:
    """Evaluates all policies on a single seed cluster, producing paired outcomes and contrasts."""
    assert_safe_seeds([seed])
    cases = generate_cases(domain=domain, n=n_cases, seed=seed, profile=profile)
    policies = get_baseline_policies()

    # Records by policy
    policy_utilities: dict[str, list[float]] = {name: [] for name in policies}
    policy_unsafe: dict[str, list[int]] = {name: [] for name in policies}
    policy_completed: dict[str, list[int]] = {name: [] for name in policies}
    policy_violations: dict[str, list[int]] = {name: [] for name in policies}

    for case in cases:
        for pol_name, policy in policies.items():
            res = run_episode(case, policy)
            policy_utilities[pol_name].append(res["utility"])
            policy_unsafe[pol_name].append(res["unsafe"])
            policy_completed[pol_name].append(res["completed"])
            policy_violations[pol_name].append(res["authorization_violation"])

    # Cluster summary
    mean_u: dict[str, float] = {}
    mean_risk: dict[str, float] = {}
    total_violations = sum(sum(v) for v in policy_violations.values())

    for pol_name in policies:
        mean_u[pol_name] = float(np.mean(policy_utilities[pol_name]))
        mean_risk[pol_name] = float(np.mean(policy_unsafe[pol_name]))

    # Paired differences per episode
    paired_diffs: dict[str, float] = {}
    excess_risks: dict[str, float] = {}
    for c_id, cand, base in PRIMARY_CONTRASTS:
        u_cand = np.array(policy_utilities[cand])
        u_base = np.array(policy_utilities[base])
        r_cand = np.array(policy_unsafe[cand])
        r_base = np.array(policy_unsafe[base])
        paired_diffs[c_id] = float(np.mean(u_cand - u_base))
        excess_risks[c_id] = float(np.mean(r_cand - r_base))

    return {
        "domain": domain,
        "profile": profile,
        "seed": seed,
        "n_cases": n_cases,
        "mean_utility": mean_u,
        "mean_risk": mean_risk,
        "paired_diffs": paired_diffs,
        "excess_risks": excess_risks,
        "authorization_violations": total_violations,
    }


def compute_power(
    s_d: float,
    k: int,
    delta: float,
    delta_margin: float = DELTA_UTIL_MARGIN,
    alpha: float = ALPHA_CONTRAST,
) -> float:
    """Computes exact small-sample power using non-central Student-t distribution for cluster count K."""
    if k < 2 or s_d <= 1e-12:
        return 0.0
    df = k - 1
    t_crit = float(stats.t.ppf(1.0 - alpha, df=df))
    se = s_d / np.sqrt(k)
    non_centrality = (delta - delta_margin) / se
    # Power = P(T > t_crit | non_centrality)
    power = float(stats.nct.sf(t_crit, df=df, nc=non_centrality))
    return float(np.clip(power, 0.0, 1.0))


def compute_mde(
    s_d: float,
    k: int,
    target_power: float = 0.80,
    delta_margin: float = DELTA_UTIL_MARGIN,
    alpha: float = ALPHA_CONTRAST,
) -> float:
    """Computes Minimum Detectable Effect (MDE) for given cluster count and target power."""
    df = k - 1
    t_crit = float(stats.t.ppf(1.0 - alpha, df=df))
    z_power = float(stats.norm.ppf(target_power))
    se = s_d / np.sqrt(k)
    mde = delta_margin + (t_crit + z_power) * se
    return float(mde)


def compute_variance_ci(
    s_d: float,
    k: int,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Computes two-sided confidence interval for standard deviation sigma_D using Chi-squared distribution."""
    df = k - 1
    alpha_ci = 1.0 - confidence
    chi2_lower = float(stats.chi2.ppf(1.0 - alpha_ci / 2.0, df=df))
    chi2_upper = float(stats.chi2.ppf(alpha_ci / 2.0, df=df))
    sigma_lower = float(np.sqrt((df * (s_d**2)) / chi2_lower))
    sigma_upper = float(np.sqrt((df * (s_d**2)) / chi2_upper))
    return sigma_lower, sigma_upper


def audit_exploratory_variance(
    seeds: list[int] | tuple[int, ...] = EXPLORATORY_SEEDS,
    domains: tuple[str, ...] = ("cs", "de"),
    profiles: tuple[str, ...] = ("iid", "verifier_shift", "outage_shift", "cost_shift"),
    n_cases: int = 250,
    candidate_k_values: tuple[int, ...] = (10, 16, 20, 24, 28, 32, 40, 48),
    delta_scenarios: tuple[float, ...] = (0.020, 0.025, 0.030, 0.035, 0.045),
) -> dict[str, Any]:
    """Runs exploratory variance calibration across domains, profiles, and contrasts."""
    assert_safe_seeds(seeds)
    k_pilot = len(seeds)

    results: dict[str, Any] = {
        "seeds": list(seeds),
        "k_pilot": k_pilot,
        "n_cases_per_cluster": n_cases,
        "domains": list(domains),
        "profiles": list(profiles),
        "delta_margin": DELTA_UTIL_MARGIN,
        "alpha_fwer": ALPHA_FWER,
        "alpha_contrast": ALPHA_CONTRAST,
        "operational_risk_limit": OPERATIONAL_RISK_LIMIT,
        "excess_risk_limit": EXCESS_RISK_LIMIT,
        "domain_results": {},
    }

    for domain in domains:
        results["domain_results"][domain] = {}
        for profile in profiles:
            cluster_outputs = []
            for seed in seeds:
                c_res = run_cluster(domain=domain, profile=profile, seed=seed, n_cases=n_cases)
                cluster_outputs.append(c_res)

            # Analyze contrasts across clusters
            contrast_stats: dict[str, Any] = {}
            for c_id, cand, base in PRIMARY_CONTRASTS:
                diffs = [c["paired_diffs"][c_id] for c in cluster_outputs]
                mean_diff = float(np.mean(diffs))
                s_d = float(np.std(diffs, ddof=1))
                se = float(s_d / np.sqrt(k_pilot))
                sigma_lower, sigma_upper = compute_variance_ci(s_d, k=k_pilot, confidence=0.95)

                # Excess risk stats
                e_risks = [c["excess_risks"][c_id] for c in cluster_outputs]
                mean_excess_risk = float(np.mean(e_risks))
                excess_risk_upper = float(
                    mean_excess_risk + stats.t.ppf(0.95, df=k_pilot - 1) * (np.std(e_risks, ddof=1) / np.sqrt(k_pilot))
                )

                # Power curves across candidate K and delta scenarios
                power_curves: dict[str, Any] = {}
                for k_cand in candidate_k_values:
                    power_curves[str(k_cand)] = {
                        "mde_80": compute_mde(s_d, k=k_cand, target_power=0.80),
                        "mde_80_upper_sd": compute_mde(sigma_upper, k=k_cand, target_power=0.80),
                        "powers": {
                            f"delta_{d:.3f}": compute_power(s_d, k=k_cand, delta=d)
                            for d in delta_scenarios
                        },
                        "powers_pessimistic_upper_sd": {
                            f"delta_{d:.3f}": compute_power(sigma_upper, k=k_cand, delta=d)
                            for d in delta_scenarios
                        },
                    }

                contrast_stats[c_id] = {
                    "comparator": base,
                    "mean_paired_difference": mean_diff,
                    "s_d": s_d,
                    "se": se,
                    "s_d_ci_95": [sigma_lower, sigma_upper],
                    "mean_excess_risk": mean_excess_risk,
                    "excess_risk_95_upper": excess_risk_upper,
                    "excess_risk_gate_pass": bool(excess_risk_upper <= EXCESS_RISK_LIMIT),
                    "power_by_k": power_curves,
                }

            # Policy-level risk gate check
            cost_rule_risks = [c["mean_risk"]["cost_rule"] for c in cluster_outputs]
            cost_rule_mean_risk = float(np.mean(cost_rule_risks))
            risk_se = float(np.std(cost_rule_risks, ddof=1) / np.sqrt(k_pilot))
            risk_upper_95 = float(cost_rule_mean_risk + stats.t.ppf(0.95, df=k_pilot - 1) * risk_se)
            total_violations = sum(c["authorization_violations"] for c in cluster_outputs)

            results["domain_results"][domain][profile] = {
                "clusters": cluster_outputs,
                "cost_rule_mean_risk": cost_rule_mean_risk,
                "cost_rule_risk_95_upper": risk_upper_95,
                "operational_risk_gate_pass": bool(risk_upper_95 <= OPERATIONAL_RISK_LIMIT),
                "total_authorization_violations": total_violations,
                "authorization_gate_pass": bool(total_violations == 0),
                "contrasts": contrast_stats,
            }

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="CausaGuard v0.6 Exploratory Variance Audit")
    parser.add_argument(
        "--domains",
        nargs="+",
        default=["cs", "de"],
        choices=["cs", "de"],
        help="Domains to evaluate",
    )
    parser.add_argument(
        "--profiles",
        nargs="+",
        default=["iid", "verifier_shift", "outage_shift", "cost_shift"],
        help="Profiles to evaluate",
    )
    parser.add_argument(
        "--cases-per-cluster",
        type=int,
        default=250,
        help="Episodes per cluster",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to write full JSON audit results",
    )
    args = parser.parse_args()

    print("================================================================================")
    print(" CausaGuard v0.6: Exploratory Variance Calibration & Prospective Power Audit")
    print(f" Authorized Exploratory Seeds: {list(EXPLORATORY_SEEDS)}")
    print(f" Cases per Cluster: {args.cases_per_cluster}")
    print(f" Hurdle Margin (Delta): +{DELTA_UTIL_MARGIN:.3f} | Alpha (Bonferroni): {ALPHA_CONTRAST:.6f}")
    print("================================================================================")

    res = audit_exploratory_variance(
        seeds=EXPLORATORY_SEEDS,
        domains=tuple(args.domains),
        profiles=tuple(args.profiles),
        n_cases=args.cases_per_cluster,
    )

    for domain, d_res in res["domain_results"].items():
        print(f"\n################# DOMAIN: {domain.upper()} #################")
        for profile, p_res in d_res.items():
            print(f"\n--- Profile: {profile} ---")
            print(
                f"  Safety Gate: CostRule Risk={p_res['cost_rule_mean_risk']:.4f} "
                f"(95% Upper={p_res['cost_rule_risk_95_upper']:.4f}, Pass={p_res['operational_risk_gate_pass']}) | "
                f"Auth Violations={p_res['total_authorization_violations']} (Pass={p_res['authorization_gate_pass']})"
            )
            for c_id, c_data in p_res["contrasts"].items():
                print(
                    f"  Contrast {c_id} (vs {c_data['comparator']}): "
                    f"Mean Gain={c_data['mean_paired_difference']:+.4f} | "
                    f"S_D={c_data['s_d']:.4f} (95% CI: [{c_data['s_d_ci_95'][0]:.4f}, {c_data['s_d_ci_95'][1]:.4f}]) | "
                    f"Excess Risk 95% Upper={c_data['excess_risk_95_upper']:.4f}"
                )
                p_k10 = c_data["power_by_k"]["10"]["powers"]["delta_0.030"]
                p_k24 = c_data["power_by_k"]["24"]["powers"]["delta_0.030"]
                p_k32 = c_data["power_by_k"]["32"]["powers"]["delta_0.030"]
                mde_k10 = c_data["power_by_k"]["10"]["mde_80"]
                mde_k24 = c_data["power_by_k"]["24"]["mde_80"]
                mde_k32 = c_data["power_by_k"]["32"]["mde_80"]
                print(
                    f"    Power for delta=+0.030: K=10: {p_k10*100:.1f}% (MDE={mde_k10:+.4f}) | "
                    f"K=24: {p_k24*100:.1f}% (MDE={mde_k24:+.4f}) | "
                    f"K=32: {p_k32*100:.1f}% (MDE={mde_k32:+.4f})"
                )

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(res, indent=2), encoding="utf-8")
        print(f"\nWrote full audit results to: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())


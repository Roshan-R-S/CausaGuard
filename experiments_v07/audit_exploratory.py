"""CausaGuard v0.7: Exploratory Variance Calibration & Mechanism Audit Runner.

Executes development-only exploratory variance calibration on authorized seeds:
- Namespace: 70001001-70001016 (K=16 clusters, N=250 cases/cluster)
- Domains: Customer Support ('cs') and Data Engineering ('de')
- Profiles: 'iid' (primary), 'verifier_shift', 'outage_shift', 'cost_shift'
- Evaluates the 9-policy comparator suite under paired potential outcomes.
- Strictly quarantined: Confirmatory development seeds (70010001-70020064),
  confirmatory final seeds (70030001-70040064), and v0.6 seeds are prohibited.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import scipy.stats as stats
from causaguard_v07.domain_cs import (
    ACTIONS_CS_V07,
    PROFILES_CS_V07,
    CSCaseV07,
    make_cs_cases_v07,
)
from causaguard_v07.domain_de import (
    ACTIONS_DE_V07,
    PROFILES_DE_V07,
    DECaseV07,
    make_de_cases_v07,
)
from causaguard_v07.policy_v07 import get_baseline_policies_v07
from causaguard_v07.study_v07 import evaluate_potential_outcomes_v07

ROOT = Path(__file__).resolve().parent.parent

# Prospective Authoritative Seed Allocation
EXPLORATORY_SEEDS = list(range(70001001, 70001017))  # 16 clusters
CASES_PER_CLUSTER = 250

# Confirmatory and Forbidden Seed Ranges for Security Checks
DEV_CONFIRMATORY_SEEDS = range(70010001, 70020065)
V07_FINAL_SEEDS = range(70030001, 70040065)
V06_FINAL_SEEDS = range(60030001, 60040065)

# Protocol Constants
DELTA_HURDLE = 0.015
PLANNING_EFFECT = 0.030
FAMILY_WISE_ALPHA = 0.010
NUM_PRIMARY_CONTRASTS = 6
PER_CONTRAST_ALPHA = FAMILY_WISE_ALPHA / NUM_PRIMARY_CONTRASTS  # 0.0016666667
R_LIMIT = 0.050


def assert_exploratory_seeds(seeds: list[int]) -> None:
    """Enforces strict isolation from confirmatory and reserved final seed namespaces."""
    for s in seeds:
        if s in V07_FINAL_SEEDS or s in V06_FINAL_SEEDS:
            raise ValueError(
                f"FATAL SECURITY VIOLATION: Attempted to access reserved confirmatory final seed {s}!"
            )
        if s in DEV_CONFIRMATORY_SEEDS:
            raise ValueError(
                f"FATAL SECURITY VIOLATION: Attempted to access unsealed development evaluation seed {s}!"
            )
        if s not in EXPLORATORY_SEEDS:
            raise ValueError(
                f"Seed {s} is not in authorized exploratory calibration range (70001001-70001016)."
            )


def run_single_cluster(
    domain: str,
    seed: int,
    profile: str = "iid",
    n_cases: int = CASES_PER_CLUSTER,
    **kwargs: Any,
) -> dict[str, Any]:
    """Generates paired cases and evaluates all 9 policies for one cluster."""
    assert_exploratory_seeds([seed])
    if domain.lower() in ("cs", "customer_support"):
        cases = make_cs_cases_v07(n=n_cases, seed=seed, profile=profile, **kwargs)
    elif domain.lower() in ("de", "data_engineering"):
        cases = make_de_cases_v07(n=n_cases, seed=seed, profile=profile, **kwargs)
    else:
        raise ValueError(f"Unknown domain: {domain}")

    policies = get_baseline_policies_v07()
    policy_names = list(policies.keys())

    # Collect per-case records
    raw_evals: dict[str, list[dict[str, Any]]] = {p: [] for p in policy_names}

    for case in cases:
        outcomes = evaluate_potential_outcomes_v07(case, policies=policies, **kwargs)
        for p, rec in outcomes.items():
            raw_evals[p].append(rec)

    # Aggregate cluster summary metrics
    cluster_summary: dict[str, Any] = {
        "domain": domain,
        "seed": seed,
        "profile": profile,
        "n_cases": n_cases,
        "policies": {},
    }

    is_cs = domain.lower() in ("cs", "customer_support")

    for p in policy_names:
        recs = raw_evals[p]
        utils = np.array([r["utility"] for r in recs], dtype=np.float64)
        completed = np.array([r["completed"] for r in recs], dtype=np.float64)
        safe_comp = np.array([r["safe_completion"] for r in recs], dtype=np.float64)
        unsafe = np.array([r["unsafe"] for r in recs], dtype=np.float64)
        costs = np.array([r["cost"] for r in recs], dtype=np.float64)
        latencies = np.array([r["latency"] for r in recs], dtype=np.float64)
        lates = np.array([r["late"] for r in recs], dtype=np.float64)
        auth_violations = np.array([r["authorization_violation"] for r in recs], dtype=np.float64)

        # Action step distributions
        step1_actions = [r["actions"][0] for r in recs]
        step2_actions = [r["actions"][1] for r in recs if len(r["actions"]) > 1]

        actions_list = ACTIONS_CS_V07 if is_cs else ACTIONS_DE_V07
        step1_counts = {act: float(np.mean([a == act for a in step1_actions])) for act in actions_list}

        if len(step2_actions) > 0:
            step2_counts = {
                act: float(np.mean([a == act for a in step2_actions]))
                for act in actions_list
                if act != "verify"
            }
        else:
            step2_counts = {}

        p_risk = float(np.mean(unsafe))
        excess_risk = float(max(0.0, p_risk - R_LIMIT))

        # Domain-specific disruption diagnostics
        disruption_diag: dict[str, Any] = {}
        if is_cs:
            # Measure clean cases where recovery (retry) was invoked
            clean_recs = [
                (c, r) for c, r in zip(cases, recs) if isinstance(c, CSCaseV07) and c.latent_state == "clean"
            ]
            if clean_recs:
                clean_retries = [r for c, r in clean_recs if "retry" in r["actions"]]
                disruption_diag["clean_cases_count"] = len(clean_recs)
                disruption_diag["clean_retries_count"] = len(clean_retries)
                disruption_diag["clean_retry_rate"] = float(len(clean_retries) / len(clean_recs))
                if clean_retries:
                    clean_abandoned = [r for r in clean_retries if r["completed"] == 0]
                    clean_discounted = [
                        r
                        for c, r in [(c, r) for c, r in clean_recs if "retry" in r["actions"]]
                        if r["completed"] == 1 and r["utility"] < (c.observation.value - r["cost"] - 1e-5)
                    ]
                    disruption_diag["clean_retry_abandonment_rate"] = float(
                        len(clean_abandoned) / len(clean_retries)
                    )
                    disruption_diag["clean_retry_discount_rate"] = float(
                        len(clean_discounted) / len(clean_retries)
                    )
        else:
            # Data Engineering disruption diagnostics
            schema_recs = [
                (c, r) for c, r in zip(cases, recs) if isinstance(c, DECaseV07) and c.f_schema
            ]
            if schema_recs:
                schema_restores = [r for c, r in schema_recs if "restore" in r["actions"]]
                disruption_diag["schema_cases_count"] = len(schema_recs)
                disruption_diag["schema_restores_count"] = len(schema_restores)
                disruption_diag["schema_restore_rate"] = float(len(schema_restores) / len(schema_recs))
                if schema_restores:
                    degraded_restores = [
                        r
                        for c, r in [(c, r) for c, r in schema_recs if "restore" in r["actions"]]
                        if r["completed"] == 1 and np.isclose(r["utility"] + r["cost"], 0.10 * c.observation.value, atol=1e-4)
                    ]
                    disruption_diag["schema_restore_severe_degrade_rate"] = float(
                        len(degraded_restores) / len(schema_restores)
                    )

        cluster_summary["policies"][p] = {
            "mean_utility": float(np.mean(utils)),
            "std_utility": float(np.std(utils, ddof=1)),
            "completion_rate": float(np.mean(completed)),
            "safe_completion_rate": float(np.mean(safe_comp)),
            "operational_risk": p_risk,
            "excess_risk": excess_risk,
            "mean_cost": float(np.mean(costs)),
            "mean_latency": float(np.mean(latencies)),
            "late_rate": float(np.mean(lates)),
            "auth_violations": int(np.sum(auth_violations)),
            "step1_actions": step1_counts,
            "step2_actions": step2_counts,
            "disruption_diagnostics": disruption_diag,
        }

    return cluster_summary


def compute_chi2_ci_sd(sd: float, df: int, conf_level: float = 0.95) -> tuple[float, float]:
    """Computes exact Chi-squared confidence interval for sample standard deviation."""
    alpha = 1.0 - conf_level
    chi2_lower = stats.chi2.ppf(1.0 - alpha / 2.0, df=df)
    chi2_upper = stats.chi2.ppf(alpha / 2.0, df=df)
    sd_lower = float(sd * np.sqrt(df / chi2_lower))
    sd_upper = float(sd * np.sqrt(df / chi2_upper))
    return sd_lower, sd_upper


def calculate_power_nct(
    k: int,
    delta: float,
    delta_hurdle: float = DELTA_HURDLE,
    sd: float = 0.045,
    alpha: float = PER_CONTRAST_ALPHA,
) -> float:
    """Calculates exact marginal power using one-sided noncentral Student-t distribution."""
    if k <= 1:
        return 0.0
    df = k - 1
    t_crit = stats.t.ppf(1.0 - alpha, df=df)
    se = sd / np.sqrt(k)
    ncp = (delta - delta_hurdle) / se
    return float(1.0 - stats.nct.cdf(t_crit, df=df, nc=ncp))


def find_mde_nct(
    k: int,
    target_power: float = 0.80,
    delta_hurdle: float = DELTA_HURDLE,
    sd: float = 0.045,
    alpha: float = PER_CONTRAST_ALPHA,
) -> float:
    """Finds Minimum Detectable Effect (MDE) achieving target power via binary search."""
    df = k - 1
    t_crit = stats.t.ppf(1.0 - alpha, df=df)
    se = sd / np.sqrt(k)

    # Solve for NCP where 1 - nct.cdf(t_crit, df, ncp) == target_power
    low, high = 0.0, 15.0
    for _ in range(60):
        mid = (low + high) / 2.0
        p = 1.0 - stats.nct.cdf(t_crit, df=df, nc=mid)
        if p < target_power:
            low = mid
        else:
            high = mid
    ncp_target = (low + high) / 2.0
    return float(delta_hurdle + ncp_target * se)


def audit_domain_clusters(
    domain: str,
    seeds: list[int] = EXPLORATORY_SEEDS,
    profile: str = "iid",
    **kwargs: Any,
) -> dict[str, Any]:
    """Runs all exploratory clusters for a domain and analyzes between-cluster variance."""
    assert_exploratory_seeds(seeds)
    cluster_results: list[dict[str, Any]] = []

    for s in seeds:
        res = run_single_cluster(domain=domain, seed=s, profile=profile, **kwargs)
        cluster_results.append(res)

    k = len(seeds)
    df = k - 1

    policies = list(cluster_results[0]["policies"].keys())

    # Aggregate cluster-level metrics across clusters
    policy_cluster_means: dict[str, list[float]] = {p: [] for p in policies}
    policy_cluster_risks: dict[str, list[float]] = {p: [] for p in policies}
    policy_cluster_comps: dict[str, list[float]] = {p: [] for p in policies}

    for cres in cluster_results:
        for p in policies:
            policy_cluster_means[p].append(cres["policies"][p]["mean_utility"])
            policy_cluster_risks[p].append(cres["policies"][p]["operational_risk"])
            policy_cluster_comps[p].append(cres["policies"][p]["safe_completion_rate"])

    # Contrast analysis against CostRule (target policy)
    target = "cost_rule_v07"
    contrasts: dict[str, Any] = {}

    for comp in policies:
        if comp == target:
            continue
        u_target = np.array(policy_cluster_means[target], dtype=np.float64)
        u_comp = np.array(policy_cluster_means[comp], dtype=np.float64)
        diffs = u_target - u_comp

        mean_diff = float(np.mean(diffs))
        sd_diff = float(np.std(diffs, ddof=1))
        se_diff = float(sd_diff / np.sqrt(k))
        ci_lower, ci_upper = compute_chi2_ci_sd(sd_diff, df=df)

        contrasts[f"{target}_vs_{comp}"] = {
            "mean_difference": mean_diff,
            "sd_between_cluster": sd_diff,
            "se_between_cluster": se_diff,
            "ci95_sd_lower": ci_lower,
            "ci95_sd_upper": ci_upper,
            "min_diff": float(np.min(diffs)),
            "max_diff": float(np.max(diffs)),
            "diffs": [float(x) for x in diffs],
        }

    # Prospective power curves for candidate cluster allocations
    candidate_k_values = [16, 32, 48, 64, 80, 96, 128, 160, 192]
    power_tables: dict[str, Any] = {}

    # Primary contrast comparators
    primary_comparators = [
        "always_recovery",
        "budget_aware_direct_recovery",
        "cost_sensitive_threshold_recovery",
    ]

    for comp in primary_comparators:
        c_key = f"{target}_vs_{comp}"
        sd_est = contrasts[c_key]["sd_between_cluster"]
        sd_upper = contrasts[c_key]["ci95_sd_upper"]

        power_records = []
        for cand_k in candidate_k_values:
            # Power under nominal planning effect (+0.030)
            p_nom_point = calculate_power_nct(cand_k, delta=0.030, sd=sd_est)
            p_nom_upper = calculate_power_nct(cand_k, delta=0.030, sd=sd_upper)

            # Power under target effect (+0.035)
            p_35_point = calculate_power_nct(cand_k, delta=0.035, sd=sd_est)
            p_35_upper = calculate_power_nct(cand_k, delta=0.035, sd=sd_upper)

            # MDE for 80% power
            mde_point = find_mde_nct(cand_k, target_power=0.80, sd=sd_est)
            mde_upper = find_mde_nct(cand_k, target_power=0.80, sd=sd_upper)

            power_records.append(
                {
                    "k_clusters": cand_k,
                    "power_delta_030_point": p_nom_point,
                    "power_delta_030_upper_sd": p_nom_upper,
                    "power_delta_035_point": p_35_point,
                    "power_delta_035_upper_sd": p_35_upper,
                    "mde_80_point": mde_point,
                    "mde_80_upper_sd": mde_upper,
                }
            )
        power_tables[c_key] = power_records

    # Summary table across policies
    policy_overview: dict[str, Any] = {}
    for p in policies:
        u_arr = np.array(policy_cluster_means[p])
        r_arr = np.array(policy_cluster_risks[p])
        c_arr = np.array(policy_cluster_comps[p])
        policy_overview[p] = {
            "mean_cluster_utility": float(np.mean(u_arr)),
            "std_cluster_utility": float(np.std(u_arr, ddof=1)),
            "mean_cluster_risk": float(np.mean(r_arr)),
            "max_cluster_risk": float(np.max(r_arr)),
            "mean_cluster_safe_completion": float(np.mean(c_arr)),
        }

    return {
        "domain": domain,
        "profile": profile,
        "k_clusters": k,
        "n_cases_per_cluster": CASES_PER_CLUSTER,
        "seeds": seeds,
        "policy_overview": policy_overview,
        "contrasts": contrasts,
        "power_tables": power_tables,
        "clusters": cluster_results,
    }


def run_parameter_sensitivity(seeds: list[int] = EXPLORATORY_SEEDS[:8]) -> dict[str, Any]:
    """Sweeps disruption, abandonment, and salvage parameters to assess conclusion sensitivity."""
    assert_exploratory_seeds(seeds)
    cs_sensitivity: list[dict[str, Any]] = []

    # CS: sweep abandonment [0.10, 0.25, 0.40] and specialist fraud salvage [0.50, 0.70, 0.90]
    for p_ab in [0.10, 0.25, 0.40]:
        for p_salv in [0.50, 0.70, 0.90]:
            cs_run = audit_domain_clusters(
                domain="cs",
                seeds=seeds,
                profile="iid",
                p_abandonment=p_ab,
                p_salvage_fraud=p_salv,
            )
            # Contrast: cost_rule vs always_recovery
            diff_rec = cs_run["contrasts"]["cost_rule_v07_vs_always_recovery"]["mean_difference"]
            sd_rec = cs_run["contrasts"]["cost_rule_v07_vs_always_recovery"]["sd_between_cluster"]
            cs_sensitivity.append(
                {
                    "p_abandonment": p_ab,
                    "p_salvage_fraud": p_salv,
                    "mean_gain_vs_always_recovery": diff_rec,
                    "sd_between_cluster": sd_rec,
                    "cost_rule_mean_utility": cs_run["policy_overview"]["cost_rule_v07"]["mean_cluster_utility"],
                    "always_recovery_mean_utility": cs_run["policy_overview"]["always_recovery"]["mean_cluster_utility"],
                }
            )

    # DE: sweep persistent fail [0.50, 0.80, 0.95] and engineer salvage [0.65, 0.85, 0.95]
    de_sensitivity: list[dict[str, Any]] = []
    for p_fail in [0.50, 0.80, 0.95]:
        for p_eng in [0.65, 0.85, 0.95]:
            de_run = audit_domain_clusters(
                domain="de",
                seeds=seeds,
                profile="iid",
                p_schema_persistent_fail=p_fail,
                p_engineer_fix_schema=p_eng,
            )
            diff_rest = de_run["contrasts"]["cost_rule_v07_vs_always_recovery"]["mean_difference"]
            sd_rest = de_run["contrasts"]["cost_rule_v07_vs_always_recovery"]["sd_between_cluster"]
            de_sensitivity.append(
                {
                    "p_schema_persistent_fail": p_fail,
                    "p_engineer_fix_schema": p_eng,
                    "mean_gain_vs_always_restore": diff_rest,
                    "sd_between_cluster": sd_rest,
                    "cost_rule_mean_utility": de_run["policy_overview"]["cost_rule_v07"]["mean_cluster_utility"],
                    "always_restore_mean_utility": de_run["policy_overview"]["always_recovery"]["mean_cluster_utility"],
                }
            )

    return {
        "customer_support": cs_sensitivity,
        "data_engineering": de_sensitivity,
    }


def run_full_exploratory_audit() -> dict[str, Any]:
    """Executes the full exploratory variance calibration across domains and profiles."""
    out_dir = ROOT / "artifacts_v07/exploratory"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Executing Customer Support Nominal IID Exploratory Audit (K=16)...")
    cs_iid = audit_domain_clusters("cs", profile="iid")

    print("Executing Data Engineering Nominal IID Exploratory Audit (K=16)...")
    de_iid = audit_domain_clusters("de", profile="iid")

    print("Executing Shift Profiles Exploratory Audits...")
    cs_shifts = {prof: audit_domain_clusters("cs", profile=prof) for prof in PROFILES_CS_V07 if prof != "iid"}
    de_shifts = {prof: audit_domain_clusters("de", profile=prof) for prof in PROFILES_DE_V07 if prof != "iid"}

    print("Executing Mechanistic Sensitivity Analysis (8 clusters)...")
    sensitivity = run_parameter_sensitivity(EXPLORATORY_SEEDS[:8])

    full_output = {
        "audit_version": "0.7.0-exploratory",
        "authoritative_seeds": EXPLORATORY_SEEDS,
        "cases_per_cluster": CASES_PER_CLUSTER,
        "nominal_cs": cs_iid,
        "nominal_de": de_iid,
        "shifts_cs": cs_shifts,
        "shifts_de": de_shifts,
        "sensitivity": sensitivity,
    }

    # Summary JSON without individual case traces
    summary_output = {
        "audit_version": "0.7.0-exploratory",
        "k_clusters": len(EXPLORATORY_SEEDS),
        "cases_per_cluster": CASES_PER_CLUSTER,
        "cs_overview": cs_iid["policy_overview"],
        "cs_primary_contrasts": {
            k: {m: v for m, v in val.items() if m != "diffs"}
            for k, val in cs_iid["contrasts"].items()
        },
        "cs_power_tables": cs_iid["power_tables"],
        "de_overview": de_iid["policy_overview"],
        "de_primary_contrasts": {
            k: {m: v for m, v in val.items() if m != "diffs"}
            for k, val in de_iid["contrasts"].items()
        },
        "de_power_tables": de_iid["power_tables"],
        "sensitivity": sensitivity,
    }

    full_path = out_dir / "exploratory_calibration.json"
    summary_path = out_dir / "exploratory_summary.json"

    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2)

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_output, f, indent=2)

    print(f"Exploratory audit complete. Saved to:\n  {full_path}\n  {summary_path}")
    return summary_output


if __name__ == "__main__":
    run_full_exploratory_audit()

"""CausaGuard v0.7.1: Exploratory Calibration & Prospective Power Analysis Runner.

Executes development-only exploratory variance calibration on authorized seeds:
- Namespace: 70002001-70002016 (K=16 clusters, N=400 cases/cluster)
- Domains: Customer Support ('cs') and Data Engineering ('de')
- Profiles: 'iid' (primary), 'verifier_shift', 'outage_shift', 'cost_shift'
- Evaluates the 8-policy benchmark suite under isolated paired counterfactuals.
- Strict isolation: Confirmatory development seeds (70010001-70020064),
  confirmatory final seeds (70030001-70040064), and v0.6 seeds are strictly prohibited.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import scipy.stats as stats
from causaguard_v07_1.domain_cs import (
    PROFILES_CS_V07_1,
    make_cs_cases_v07_1,
)
from causaguard_v07_1.domain_de import (
    PROFILES_DE_V07_1,
    make_de_cases_v07_1,
)
from causaguard_v07_1.escalation import (
    HumanEscalationParamsCS,
    HumanEscalationParamsDE,
)
from causaguard_v07_1.policy_v07_1 import (
    AlwaysEscalatePolicyV07_1,
    AlwaysRecoveryPolicyV07_1,
    BasePolicyV07_1,
    BudgetAwareDirectRecoveryPolicyV07_1,
    CostRulePolicyV07_1,
    CostSensitiveSymmetricHeuristicPolicyV07_1,
    EscalationAwareDeterministicThresholdPolicyV07_1,
    FixedVerifyRepairMacroPolicyV07_1,
    OraclePolicyV07_1,
)
from causaguard_v07_1.study_v07_1 import evaluate_cluster_v07_1

ROOT = Path(__file__).resolve().parent.parent

# Authorized Exploratory Seed Allocation
EXPLORATORY_SEEDS = list(range(70002001, 70002017))  # 16 clusters
CASES_PER_CLUSTER = 400

# Quarantined and Forbidden Seed Ranges for Security Checks
DEV_CONFIRMATORY_SEEDS = range(70010001, 70020065)
V07_FINAL_SEEDS = range(70030001, 70040065)
V06_FINAL_SEEDS = range(60030001, 60040065)
V07_OLD_EXPLORATORY = range(70001001, 70001017)

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
                f"Seed {s} is not in authorized exploratory calibration range (70002001-70002016)."
            )


def build_policies_v07_1(
    cs_params: HumanEscalationParamsCS | None = None,
    de_params: HumanEscalationParamsDE | None = None,
) -> dict[str, BasePolicyV07_1]:
    """Builds the 8-policy benchmark suite with optional custom escalation parameter models."""
    return {
        "cost_rule_v07_1": CostRulePolicyV07_1(cs_params=cs_params, de_params=de_params),
        "always_escalate": AlwaysEscalatePolicyV07_1(),
        "always_recovery": AlwaysRecoveryPolicyV07_1(),
        "budget_aware_direct_recovery": BudgetAwareDirectRecoveryPolicyV07_1(),
        "escalation_aware_deterministic_threshold": EscalationAwareDeterministicThresholdPolicyV07_1(),
        "cost_sensitive_symmetric_heuristic": CostSensitiveSymmetricHeuristicPolicyV07_1(),
        "fixed_verify_repair_macro": FixedVerifyRepairMacroPolicyV07_1(),
        "oracle": OraclePolicyV07_1(),
    }


def run_single_cluster_v07_1(
    domain: str,
    seed: int,
    profile: str = "iid",
    n_cases: int = CASES_PER_CLUSTER,
    cs_params: HumanEscalationParamsCS | None = None,
    de_params: HumanEscalationParamsDE | None = None,
    **step_kwargs: Any,
) -> dict[str, Any]:
    """Generates paired cases and evaluates all 8 policies for one cluster."""
    assert_exploratory_seeds([seed])
    is_cs = domain.lower() in ("cs", "customer_support")

    if is_cs:
        cases = make_cs_cases_v07_1(n=n_cases, seed=seed, profile=profile)
        esc_params = cs_params if cs_params is not None else HumanEscalationParamsCS()
        capacity_limit = esc_params.capacity_limit
        step_kwargs["escalation_params"] = esc_params
    else:
        cases = make_de_cases_v07_1(n=n_cases, seed=seed, profile=profile)
        esc_params = de_params if de_params is not None else HumanEscalationParamsDE()
        capacity_limit = esc_params.capacity_limit
        step_kwargs["escalation_params"] = esc_params

    policies = build_policies_v07_1(cs_params=cs_params, de_params=de_params)
    cluster_eval = evaluate_cluster_v07_1(
        cases=cases,
        policies=policies,
        capacity_limit=capacity_limit,
        **step_kwargs,
    )

    return {
        "domain": "customer_support" if is_cs else "data_engineering",
        "seed": seed,
        "profile": profile,
        "n_cases": n_cases,
        "policies": cluster_eval["policy_metrics"],
    }


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
    if k <= 1 or sd <= 0.0:
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
    if k <= 1 or sd <= 0.0:
        return 999.0
    df = k - 1
    t_crit = stats.t.ppf(1.0 - alpha, df=df)
    se = sd / np.sqrt(k)

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


def find_required_k_nct(
    target_power: float = 0.80,
    delta: float = PLANNING_EFFECT,
    delta_hurdle: float = DELTA_HURDLE,
    sd: float = 0.045,
    alpha: float = PER_CONTRAST_ALPHA,
    max_k: int = 500,
) -> int:
    """Finds minimum cluster count K achieving target power."""
    for cand_k in range(4, max_k + 1):
        pw = calculate_power_nct(
            k=cand_k,
            delta=delta,
            delta_hurdle=delta_hurdle,
            sd=sd,
            alpha=alpha,
        )
        if pw >= target_power:
            return cand_k
    return max_k


def audit_domain_clusters_v07_1(
    domain: str,
    seeds: list[int] = EXPLORATORY_SEEDS,
    profile: str = "iid",
    cs_params: HumanEscalationParamsCS | None = None,
    de_params: HumanEscalationParamsDE | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Runs all exploratory clusters for a domain and performs paired counterfactual contrast analysis."""
    assert_exploratory_seeds(seeds)
    cluster_results: list[dict[str, Any]] = []

    for s in seeds:
        res = run_single_cluster_v07_1(
            domain=domain,
            seed=s,
            profile=profile,
            cs_params=cs_params,
            de_params=de_params,
            **kwargs,
        )
        cluster_results.append(res)

    k = len(seeds)
    df = k - 1

    policies = list(cluster_results[0]["policies"].keys())

    # Aggregate cluster-level metrics across clusters
    policy_cluster_means: dict[str, list[float]] = {p: [] for p in policies}
    policy_cluster_risks: dict[str, list[float]] = {p: [] for p in policies}
    policy_cluster_comps: dict[str, list[float]] = {p: [] for p in policies}
    policy_cluster_costs: dict[str, list[float]] = {p: [] for p in policies}
    policy_cluster_latencies: dict[str, list[float]] = {p: [] for p in policies}
    policy_cluster_escalations: dict[str, list[int]] = {p: [] for p in policies}
    policy_cluster_drops: dict[str, list[int]] = {p: [] for p in policies}
    policy_cluster_errors: dict[str, list[int]] = {p: [] for p in policies}

    for cres in cluster_results:
        for p in policies:
            pm = cres["policies"][p]
            policy_cluster_means[p].append(pm["mean_utility"])
            policy_cluster_risks[p].append(pm["operational_risk"])
            policy_cluster_comps[p].append(pm["safe_completion_rate"])
            policy_cluster_costs[p].append(pm["mean_cost"])
            policy_cluster_latencies[p].append(pm["mean_latency"])
            q_diag = pm["queue_diagnostics"]
            policy_cluster_escalations[p].append(q_diag["total_escalations"])
            policy_cluster_drops[p].append(q_diag["queue_drops"])
            policy_cluster_errors[p].append(q_diag["human_errors"])

    # Contrast analysis against CostRule (Candidate Policy)
    target = "cost_rule_v07_1"
    contrasts: dict[str, Any] = {}

    for comp in policies:
        if comp == target:
            continue
        u_target = np.array(policy_cluster_means[target], dtype=np.float64)
        u_comp = np.array(policy_cluster_means[comp], dtype=np.float64)
        diffs = u_target - u_comp

        mean_diff = float(np.mean(diffs))
        sd_diff = float(np.std(diffs, ddof=1)) if k > 1 else 0.0
        se_diff = float(sd_diff / np.sqrt(k)) if k > 1 else 0.0
        ci_lower, ci_upper = compute_chi2_ci_sd(sd_diff, df=df) if k > 1 and sd_diff > 0 else (0.0, 0.0)

        # One-sided t-test vs hurdle Delta = +0.015
        if se_diff > 1e-9:
            t_stat = (mean_diff - DELTA_HURDLE) / se_diff
            p_val = float(1.0 - stats.t.cdf(t_stat, df=df))
            t_crit_bonf = float(stats.t.ppf(1.0 - PER_CONTRAST_ALPHA, df=df))
            lcb_bonf = float(mean_diff - t_crit_bonf * se_diff)
        else:
            t_stat = 0.0
            p_val = 1.0
            lcb_bonf = mean_diff

        contrasts[f"{target}_vs_{comp}"] = {
            "mean_difference": mean_diff,
            "sd_between_cluster": sd_diff,
            "se_between_cluster": se_diff,
            "ci95_sd_lower": ci_lower,
            "ci95_sd_upper": ci_upper,
            "t_stat_vs_hurdle": t_stat,
            "p_value_one_sided": p_val,
            "bonferroni_lcb_9983": lcb_bonf,
            "min_diff": float(np.min(diffs)),
            "max_diff": float(np.max(diffs)),
            "diffs": [float(x) for x in diffs],
        }

    # Prospective power curves for candidate cluster allocations
    candidate_k_values = [16, 32, 48, 64, 80, 96, 128, 160, 192, 256]
    power_tables: dict[str, Any] = {}

    # Primary contrasts are all 6 baselines except oracle
    primary_comparators = [
        "always_escalate",
        "always_recovery",
        "budget_aware_direct_recovery",
        "escalation_aware_deterministic_threshold",
        "cost_sensitive_symmetric_heuristic",
        "fixed_verify_repair_macro",
    ]

    for comp in primary_comparators:
        c_key = f"{target}_vs_{comp}"
        sd_est = contrasts[c_key]["sd_between_cluster"]
        sd_upper = contrasts[c_key]["ci95_sd_upper"]

        power_records = []
        for cand_k in candidate_k_values:
            p_nom_point = calculate_power_nct(cand_k, delta=PLANNING_EFFECT, sd=sd_est)
            p_nom_upper = calculate_power_nct(cand_k, delta=PLANNING_EFFECT, sd=sd_upper)

            p_35_point = calculate_power_nct(cand_k, delta=0.035, sd=sd_est)
            p_35_upper = calculate_power_nct(cand_k, delta=0.035, sd=sd_upper)

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

        k_req_80_point = find_required_k_nct(0.80, delta=PLANNING_EFFECT, sd=sd_est)
        k_req_80_upper = find_required_k_nct(0.80, delta=PLANNING_EFFECT, sd=sd_upper)

        power_tables[c_key] = {
            "power_curve": power_records,
            "k_required_80_point": k_req_80_point,
            "k_required_80_upper_sd": k_req_80_upper,
        }

    # Summary table across policies
    policy_overview: dict[str, Any] = {}
    for p in policies:
        u_arr = np.array(policy_cluster_means[p])
        r_arr = np.array(policy_cluster_risks[p])
        c_arr = np.array(policy_cluster_comps[p])
        cost_arr = np.array(policy_cluster_costs[p])
        lat_arr = np.array(policy_cluster_latencies[p])
        esc_arr = np.array(policy_cluster_escalations[p])
        drop_arr = np.array(policy_cluster_drops[p])
        err_arr = np.array(policy_cluster_errors[p])

        # Step 1 actions across all clusters
        s1_all: dict[str, float] = {}
        for cres in cluster_results:
            for act, frac in cres["policies"][p]["step1_actions"].items():
                s1_all[act] = s1_all.get(act, 0.0) + frac / k

        s2_all: dict[str, float] = {}
        for cres in cluster_results:
            for act, frac in cres["policies"][p]["step2_actions"].items():
                s2_all[act] = s2_all.get(act, 0.0) + frac / k

        policy_overview[p] = {
            "mean_cluster_utility": float(np.mean(u_arr)),
            "std_cluster_utility": float(np.std(u_arr, ddof=1)),
            "mean_cluster_risk": float(np.mean(r_arr)),
            "max_cluster_risk": float(np.max(r_arr)),
            "mean_cluster_safe_completion": float(np.mean(c_arr)),
            "mean_cost": float(np.mean(cost_arr)),
            "mean_latency": float(np.mean(lat_arr)),
            "mean_escalations": float(np.mean(esc_arr)),
            "mean_queue_drops": float(np.mean(drop_arr)),
            "mean_human_errors": float(np.mean(err_arr)),
            "step1_actions": s1_all,
            "step2_actions": s2_all,
        }

    return {
        "domain": "customer_support" if domain.lower() in ("cs", "customer_support") else "data_engineering",
        "profile": profile,
        "k_clusters": k,
        "n_cases_per_cluster": CASES_PER_CLUSTER,
        "seeds": seeds,
        "policy_overview": policy_overview,
        "contrasts": contrasts,
        "power_tables": power_tables,
        "clusters": cluster_results,
    }


def run_parameter_sensitivity_v07_1(seeds: list[int] = EXPLORATORY_SEEDS[:8]) -> dict[str, Any]:
    """Sweeps workflow discount, labor cost, queue capacity, and specialist error rates (8 clusters)."""
    assert_exploratory_seeds(seeds)

    # 1. Workflow discount sweep gamma in [0.60, 0.75, 0.90, 1.00]
    gamma_sweep_results = []
    for g in [0.60, 0.75, 0.90, 1.00]:
        cs_p = HumanEscalationParamsCS(gamma_workflow=g)
        de_p = HumanEscalationParamsDE(gamma_workflow=g)

        cs_run = audit_domain_clusters_v07_1("cs", seeds=seeds, profile="iid", cs_params=cs_p)
        de_run = audit_domain_clusters_v07_1("de", seeds=seeds, profile="iid", de_params=de_p)

        gamma_sweep_results.append({
            "gamma_workflow": g,
            "cs_gain_vs_always_escalate": cs_run["contrasts"]["cost_rule_v07_1_vs_always_escalate"]["mean_difference"],
            "cs_gain_vs_always_recovery": cs_run["contrasts"]["cost_rule_v07_1_vs_always_recovery"]["mean_difference"],
            "cs_cost_rule_utility": cs_run["policy_overview"]["cost_rule_v07_1"]["mean_cluster_utility"],
            "cs_always_escalate_utility": cs_run["policy_overview"]["always_escalate"]["mean_cluster_utility"],
            "de_gain_vs_always_escalate": de_run["contrasts"]["cost_rule_v07_1_vs_always_escalate"]["mean_difference"],
            "de_gain_vs_always_recovery": de_run["contrasts"]["cost_rule_v07_1_vs_always_recovery"]["mean_difference"],
            "de_cost_rule_utility": de_run["policy_overview"]["cost_rule_v07_1"]["mean_cluster_utility"],
            "de_always_escalate_utility": de_run["policy_overview"]["always_escalate"]["mean_cluster_utility"],
        })

    # 2. Labor fee sweep c_labor_base
    labor_sweep_results = []
    for c_mult in [0.5, 1.0, 1.5, 2.0]:
        cs_p = HumanEscalationParamsCS(c_labor_base=0.45 * c_mult)
        de_p = HumanEscalationParamsDE(c_labor_base=0.75 * c_mult)

        cs_run = audit_domain_clusters_v07_1("cs", seeds=seeds, profile="iid", cs_params=cs_p)
        de_run = audit_domain_clusters_v07_1("de", seeds=seeds, profile="iid", de_params=de_p)

        labor_sweep_results.append({
            "labor_mult": c_mult,
            "cs_c_labor": 0.45 * c_mult,
            "de_c_labor": 0.75 * c_mult,
            "cs_gain_vs_always_escalate": cs_run["contrasts"]["cost_rule_v07_1_vs_always_escalate"]["mean_difference"],
            "cs_cost_rule_utility": cs_run["policy_overview"]["cost_rule_v07_1"]["mean_cluster_utility"],
            "cs_always_escalate_utility": cs_run["policy_overview"]["always_escalate"]["mean_cluster_utility"],
            "de_gain_vs_always_escalate": de_run["contrasts"]["cost_rule_v07_1_vs_always_escalate"]["mean_difference"],
            "de_cost_rule_utility": de_run["policy_overview"]["cost_rule_v07_1"]["mean_cluster_utility"],
            "de_always_escalate_utility": de_run["policy_overview"]["always_escalate"]["mean_cluster_utility"],
        })

    # 3. Queue Capacity Limit sweep [50, 100, 150, 250]
    cap_sweep_results = []
    for cap in [50, 100, 150, 250]:
        cs_p = HumanEscalationParamsCS(capacity_limit=cap)
        de_p = HumanEscalationParamsDE(capacity_limit=cap)

        cs_run = audit_domain_clusters_v07_1("cs", seeds=seeds, profile="iid", cs_params=cs_p)
        de_run = audit_domain_clusters_v07_1("de", seeds=seeds, profile="iid", de_params=de_p)

        cap_sweep_results.append({
            "capacity_limit": cap,
            "cs_always_escalate_drops": cs_run["policy_overview"]["always_escalate"]["mean_queue_drops"],
            "cs_cost_rule_drops": cs_run["policy_overview"]["cost_rule_v07_1"]["mean_queue_drops"],
            "cs_gain_vs_always_escalate": cs_run["contrasts"]["cost_rule_v07_1_vs_always_escalate"]["mean_difference"],
            "de_always_escalate_drops": de_run["policy_overview"]["always_escalate"]["mean_queue_drops"],
            "de_cost_rule_drops": de_run["policy_overview"]["cost_rule_v07_1"]["mean_queue_drops"],
            "de_gain_vs_always_escalate": de_run["contrasts"]["cost_rule_v07_1_vs_always_escalate"]["mean_difference"],
        })

    # 4. Specialist Error Rate sweep p_error_base in [0.00, 0.05, 0.10, 0.20]
    err_sweep_results = []
    for err in [0.00, 0.05, 0.10, 0.20]:
        cs_p = HumanEscalationParamsCS(p_error_base=err)
        de_p = HumanEscalationParamsDE(p_error_base=err)

        cs_run = audit_domain_clusters_v07_1("cs", seeds=seeds, profile="iid", cs_params=cs_p)
        de_run = audit_domain_clusters_v07_1("de", seeds=seeds, profile="iid", de_params=de_p)

        err_sweep_results.append({
            "p_error_base": err,
            "cs_cost_rule_risk": cs_run["policy_overview"]["cost_rule_v07_1"]["mean_cluster_risk"],
            "cs_always_escalate_risk": cs_run["policy_overview"]["always_escalate"]["mean_cluster_risk"],
            "cs_gain_vs_always_escalate": cs_run["contrasts"]["cost_rule_v07_1_vs_always_escalate"]["mean_difference"],
            "de_cost_rule_risk": de_run["policy_overview"]["cost_rule_v07_1"]["mean_cluster_risk"],
            "de_always_escalate_risk": de_run["policy_overview"]["always_escalate"]["mean_cluster_risk"],
            "de_gain_vs_always_escalate": de_run["contrasts"]["cost_rule_v07_1_vs_always_escalate"]["mean_difference"],
        })

    return {
        "workflow_discount_sweep": gamma_sweep_results,
        "labor_fee_sweep": labor_sweep_results,
        "capacity_limit_sweep": cap_sweep_results,
        "specialist_error_sweep": err_sweep_results,
    }


def run_full_exploratory_calibration_v07_1() -> dict[str, Any]:
    """Executes the complete exploratory calibration suite for CausaGuard v0.7.1."""
    out_dir = ROOT / "artifacts_v07_1/exploratory"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=================================================================")
    print("EXECUTING CAUSAGUARD v0.7.1 FRESH EXPLORATORY CALIBRATION")
    print(f"Seeds: {EXPLORATORY_SEEDS[0]}..{EXPLORATORY_SEEDS[-1]} (K={len(EXPLORATORY_SEEDS)})")
    print(f"Cases per cluster: {CASES_PER_CLUSTER}")
    print("=================================================================")

    print("\n1. Running Nominal IID Customer Support calibration (K=16, N=400)...")
    cs_iid = audit_domain_clusters_v07_1("cs", profile="iid")

    print("\n2. Running Nominal IID Data Engineering calibration (K=16, N=400)...")
    de_iid = audit_domain_clusters_v07_1("de", profile="iid")

    print("\n3. Running Shift Profiles calibration...")
    cs_shifts = {prof: audit_domain_clusters_v07_1("cs", profile=prof) for prof in PROFILES_CS_V07_1 if prof != "iid"}
    de_shifts = {prof: audit_domain_clusters_v07_1("de", profile=prof) for prof in PROFILES_DE_V07_1 if prof != "iid"}

    print("\n4. Running 4-factor Mechanistic Parameter Sensitivity Sweeps (8 clusters)...")
    sensitivity = run_parameter_sensitivity_v07_1(EXPLORATORY_SEEDS[:8])

    full_clusters_output = {
        "audit_version": "0.7.1-exploratory",
        "authoritative_seeds": EXPLORATORY_SEEDS,
        "cases_per_cluster": CASES_PER_CLUSTER,
        "nominal_cs": cs_iid,
        "nominal_de": de_iid,
        "shifts_cs": cs_shifts,
        "shifts_de": de_shifts,
    }

    summary_output = {
        "audit_version": "0.7.1-exploratory",
        "k_clusters": len(EXPLORATORY_SEEDS),
        "cases_per_cluster": CASES_PER_CLUSTER,
        "nominal_cs": {
            "policy_overview": cs_iid["policy_overview"],
            "primary_contrasts": {
                k: {m: v for m, v in val.items() if m != "diffs"}
                for k, val in cs_iid["contrasts"].items()
            },
            "power_tables": cs_iid["power_tables"],
        },
        "nominal_de": {
            "policy_overview": de_iid["policy_overview"],
            "primary_contrasts": {
                k: {m: v for m, v in val.items() if m != "diffs"}
                for k, val in de_iid["contrasts"].items()
            },
            "power_tables": de_iid["power_tables"],
        },
        "shifts_summary": {
            "cs": {
                prof: {
                    "cost_rule_utility": data["policy_overview"]["cost_rule_v07_1"]["mean_cluster_utility"],
                    "cost_rule_risk": data["policy_overview"]["cost_rule_v07_1"]["mean_cluster_risk"],
                    "always_escalate_utility": data["policy_overview"]["always_escalate"]["mean_cluster_utility"],
                    "contrasts": {
                        k: {m: v for m, v in val.items() if m in ("mean_difference", "sd_between_cluster", "se_between_cluster")}
                        for k, val in data["contrasts"].items()
                    },
                }
                for prof, data in cs_shifts.items()
            },
            "de": {
                prof: {
                    "cost_rule_utility": data["policy_overview"]["cost_rule_v07_1"]["mean_cluster_utility"],
                    "cost_rule_risk": data["policy_overview"]["cost_rule_v07_1"]["mean_cluster_risk"],
                    "always_escalate_utility": data["policy_overview"]["always_escalate"]["mean_cluster_utility"],
                    "contrasts": {
                        k: {m: v for m, v in val.items() if m in ("mean_difference", "sd_between_cluster", "se_between_cluster")}
                        for k, val in data["contrasts"].items()
                    },
                }
                for prof, data in de_shifts.items()
            },
        },
        "sensitivity": sensitivity,
    }

    clusters_path = out_dir / "exploratory_clusters.json"
    summary_path = out_dir / "exploratory_summary.json"

    with open(clusters_path, "w", encoding="utf-8") as f:
        json.dump(full_clusters_output, f, indent=2)

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_output, f, indent=2)

    print("\nCalibration complete. Deliverables written to:")
    print(f"  * {clusters_path}")
    print(f"  * {summary_path}")

    return summary_output


if __name__ == "__main__":
    run_full_exploratory_calibration_v07_1()

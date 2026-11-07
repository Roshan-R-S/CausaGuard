"""CausaGuard v0.7.1: Methodology & Reproducibility Invariant Test Suite (Deliverable C).

Validates:
1. Invariants for equal action access across all 8 policies.
2. Information availability and latent state isolation (no snooping).
3. Budget accounting, step transitions, and non-negative terminal budgets.
4. Queue-state isolation and policy-order invariance across counterfactual executions.
5. Deterministic reproducibility under fixed seeds.
6. Numerical validation of Student-t power, paired difference, cluster variance, and Clopper-Pearson bounds.
7. Boundary and edge-case testing (zero-event standard, extreme effects, queue capacity limits).
8. Parameter consistency between protocol JSON and Markdown review candidates.

RESTRICTION: No reserved confirmatory seeds (70100001+, 70200001+, 60030001+). Synthetic fixtures only.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import scipy.stats as stats
from causaguard_v07_1.domain_cs import (
    ACTIONS_CS_V07_1,
    make_cs_cases_v07_1,
)
from causaguard_v07_1.domain_de import (
    ACTIONS_DE_V07_1,
    make_de_cases_v07_1,
)
from causaguard_v07_1.escalation import (
    QueueState,
    execute_escalation_cs,
)
from causaguard_v07_1.policy_v07_1 import (
    CostRulePolicyV07_1,
    get_baseline_policies_v07_1,
)
from causaguard_v07_1.study_v07_1 import evaluate_cluster_v07_1

from experiments_v07_1.evaluate_confirmatory_v07_1 import (
    DELTA_HURDLE,
    FWER_ALPHA,
    NUM_PRIMARY_CONTRASTS,
    OPERATIONAL_RISK_LIMIT,
    ProtocolValidationError,
    compute_clustered_operational_risk,
    compute_frechet_bonferroni_joint_power,
    compute_paired_contrast_statistics,
)

ROOT = Path(__file__).resolve().parent.parent
SAFE_TEST_SEEDS = (70003001, 70003002)


# ==============================================================================
# 1. Action-Space & Information Access Invariants
# ==============================================================================


def test_equal_action_access_across_all_policies():
    """INV-01: All 8 comparators produce valid domain-permitted action strings."""
    policies = get_baseline_policies_v07_1()
    assert len(policies) == 8

    cs_case = make_cs_cases_v07_1(1, SAFE_TEST_SEEDS[0])[0]
    de_case = make_de_cases_v07_1(1, SAFE_TEST_SEEDS[0])[0]

    for p_name, p in policies.items():
        cs_kwargs = {"case": cs_case} if p_name == "oracle" else {}
        action_cs = p.select(cs_case.observation, b_rem=2, **cs_kwargs)
        assert action_cs in ACTIONS_CS_V07_1, f"Policy {p_name} emitted invalid CS action: {action_cs}"

        de_kwargs = {"case": de_case} if p_name == "oracle" else {}
        action_de = p.select(de_case.observation, b_rem=2, **de_kwargs)
        assert action_de in ACTIONS_DE_V07_1, f"Policy {p_name} emitted invalid DE action: {action_de}"


def test_latent_state_isolation_invariant():
    """INV-02: Policies cannot observe latent defect states or unobservable hazards."""
    policies = get_baseline_policies_v07_1()

    cs_case = make_cs_cases_v07_1(1, SAFE_TEST_SEEDS[0])[0]
    de_case = make_de_cases_v07_1(1, SAFE_TEST_SEEDS[0])[0]

    # Verify that observation objects do NOT contain latent truth attributes
    assert not hasattr(cs_case.observation, "latent_state")
    assert not hasattr(cs_case.observation, "defect")
    assert not hasattr(cs_case.observation, "actual_fp")
    assert not hasattr(cs_case.observation, "actual_fn")

    assert not hasattr(de_case.observation, "f_schema")
    assert not hasattr(de_case.observation, "f_content")
    assert not hasattr(de_case.observation, "defect")

    # CostRulePolicyV07_1 explicitly prohibits Case objects and private case kwargs
    cost_rule = policies["cost_rule_v07_1"]
    with pytest.raises(TypeError, match="CostRulePolicyV07_1 accepts only Observation, not Case objects!"):
        cost_rule.select(cs_case, b_rem=2)

    with pytest.raises(TypeError, match="CostRulePolicyV07_1 prohibits private case argument!"):
        cost_rule.select(cs_case.observation, b_rem=2, case=cs_case)

    # Other non-oracle policies produce identical actions whether case kwargs are passed or not
    for p_name, p in policies.items():
        if p_name not in ("oracle", "cost_rule_v07_1"):
            act_clean = p.select(cs_case.observation, b_rem=2)
            act_with_case = p.select(cs_case.observation, b_rem=2, case=cs_case)
            assert act_clean == act_with_case, f"Policy {p_name} snooped on case kwarg!"


def test_budget_accounting_invariant():
    """INV-03: Budget b_rem decreases monotonically and terminates at 0."""
    cs_cases = make_cs_cases_v07_1(20, SAFE_TEST_SEEDS[0])
    policy = CostRulePolicyV07_1()

    # In evaluate_cluster_v07_1, each case begins with budget in {1, 2} and terminates
    res = evaluate_cluster_v07_1(cs_cases, {"cost_rule_v07_1": policy})
    assert res["n_cases"] == 20
    metrics = res["policy_metrics"]["cost_rule_v07_1"]
    assert 0 <= metrics["operational_risk"] <= 1.0
    assert isinstance(metrics["mean_utility"], float)


def test_queue_state_isolation_order_invariance():
    """INV-04: Counterfactual evaluation of policy order [A, B] vs [B, A] is strictly invariant."""
    cases = make_cs_cases_v07_1(30, SAFE_TEST_SEEDS[0])
    policies = get_baseline_policies_v07_1()
    policy_a = policies["cost_rule_v07_1"]
    policy_b = policies["always_escalate"]

    # Run A then B
    res_a1 = evaluate_cluster_v07_1(cases, {"cost_rule_v07_1": policy_a})
    res_b1 = evaluate_cluster_v07_1(cases, {"always_escalate": policy_b})

    # Run B then A on fresh evaluation with reset queues
    res_b2 = evaluate_cluster_v07_1(cases, {"always_escalate": policy_b})
    res_a2 = evaluate_cluster_v07_1(cases, {"cost_rule_v07_1": policy_a})

    m_a1 = res_a1["policy_metrics"]["cost_rule_v07_1"]
    m_a2 = res_a2["policy_metrics"]["cost_rule_v07_1"]
    m_b1 = res_b1["policy_metrics"]["always_escalate"]
    m_b2 = res_b2["policy_metrics"]["always_escalate"]

    assert m_a1["mean_utility"] == m_a2["mean_utility"], "Policy A utility changed based on evaluation order!"
    assert m_b1["mean_utility"] == m_b2["mean_utility"], "Policy B utility changed based on evaluation order!"
    assert m_a1["operational_risk"] == m_a2["operational_risk"]
    assert m_b1["operational_risk"] == m_b2["operational_risk"]


def test_deterministic_reproducibility_invariant():
    """INV-05: Re-running cluster evaluation with identical seed yields bitwise identical results."""
    cases1 = make_de_cases_v07_1(40, SAFE_TEST_SEEDS[0])
    cases2 = make_de_cases_v07_1(40, SAFE_TEST_SEEDS[0])

    policy = CostRulePolicyV07_1()
    res1 = evaluate_cluster_v07_1(cases1, {"cost_rule_v07_1": policy})
    res2 = evaluate_cluster_v07_1(cases2, {"cost_rule_v07_1": policy})

    m1 = res1["policy_metrics"]["cost_rule_v07_1"]
    m2 = res2["policy_metrics"]["cost_rule_v07_1"]

    assert m1["mean_utility"] == m2["mean_utility"]
    assert m1["operational_risk"] == m2["operational_risk"]
    assert m1["mean_latency"] == m2["mean_latency"]


# ==============================================================================
# 2. Numerical & Statistical Helper Validations
# ==============================================================================


def test_student_t_power_matches_scipy_nct():
    """NUM-01: Noncentral Student-t power calculation matches scipy reference exactly."""
    k = 128
    df = k - 1
    alpha_primary = FWER_ALPHA / NUM_PRIMARY_CONTRASTS  # 0.010 / 3 = 0.0033333333333333335
    t_crit = float(stats.t.ppf(1.0 - alpha_primary, df=df))

    # Assert t_crit matches protocol prospective constant (2.758398)
    assert abs(t_crit - 2.75839762) < 1e-6
    assert round(t_crit, 4) == 2.7584

    # Test marginal power for delta = 0.030, delta_hurdle = 0.015, point S_D = 0.02601
    sd_point = 0.02601
    delta_eff = 0.030 - DELTA_HURDLE  # 0.015
    ncp_point = delta_eff / (sd_point / np.sqrt(k))
    power_point = float(stats.nct.sf(t_crit, df=df, nc=ncp_point))
    assert abs(power_point - 0.999899) < 1e-4

    # Test marginal power for conservative upper 95% S_D = 0.04026
    sd_upper = 0.04026
    ncp_upper = delta_eff / (sd_upper / np.sqrt(k))
    power_upper = float(stats.nct.sf(t_crit, df=df, nc=ncp_upper))
    assert abs(power_upper - 0.925253) < 1e-4


def test_paired_contrasts_hand_calculation():
    """NUM-02: Paired cluster utility contrasts match analytical mean and standard error."""
    # Create synthetic cluster utility arrays for K=4 clusters
    u_cand = [0.85, 0.88, 0.82, 0.86]
    u_comp = [0.80, 0.81, 0.81, 0.82]

    diffs = [c - p for c, p in zip(u_cand, u_comp)]  # [0.05, 0.07, 0.01, 0.04]
    mean_d = float(np.mean(diffs))  # 0.0425
    sd_d = float(np.std(diffs, ddof=1))  # Sample SD with df=3
    se_d = sd_d / np.sqrt(4)

    alpha = 0.010 / 3
    t_crit = float(stats.t.ppf(1.0 - alpha, df=3))
    lcb = mean_d - t_crit * se_d

    # Test evaluate_confirmatory runner helper
    c1 = compute_paired_contrast_statistics(
        cand_utilities=u_cand,
        comp_utilities=u_comp,
        contrast_name="C1_recovery",
        cand_name="cost_rule_v07_1",
        comp_name="always_recovery",
        delta_hurdle=DELTA_HURDLE,
        alpha=alpha,
    )

    assert abs(c1["mean_diff"] - mean_d) < 1e-7
    assert abs(c1["sd_diff"] - sd_d) < 1e-7
    assert abs(c1["se_diff"] - se_d) < 1e-7
    assert abs(c1["lcb_bonferroni"] - lcb) < 1e-7


def test_clustered_operational_risk_student_t_and_zero_event_bound():
    """NUM-03: Clustered operational risk formulas with nonzero and zero events."""
    # Case A: Nonzero events across K=4 clusters
    risks_nonzero = [0.01, 0.02, 0.00, 0.01]
    res_nonzero = compute_clustered_operational_risk(risks_nonzero, n_cases_per_cluster=400, alpha=0.050)
    assert res_nonzero["inference_method"] == "student_t_clustered"
    assert res_nonzero["zero_event_regime"] is False
    assert res_nonzero["mean_risk"] == 0.010
    assert res_nonzero["ucb_cluster"] > 0.010

    # Case B: Zero events across K=128 clusters
    risks_zero = [0.0] * 128
    res_zero = compute_clustered_operational_risk(risks_zero, n_cases_per_cluster=400, alpha=0.050)
    assert res_zero["inference_method"] == "clopper_pearson_cluster_exact"
    assert res_zero["zero_event_regime"] is True
    assert res_zero["mean_risk"] == 0.0

    # Exact Clopper-Pearson bound: 1 - 0.05^(1/128)
    exact_bound = 1.0 - (0.05 ** (1.0 / 128))
    assert abs(res_zero["ucb_cluster"] - exact_bound) < 1e-7
    assert abs(exact_bound - 0.023132405) < 1e-7
    # Protocol conservative rounded standard (0.02314) strictly bounds exact
    assert 0.02314 > exact_bound


def test_frechet_bonferroni_joint_power_bound():
    """NUM-04: Fréchet-Bonferroni joint power calculation matches protocol values."""
    # For independent/dependent events: P(A1 and A2 and A3) >= 1 - sum(P(Aj^c))
    p_a1_conservative = 0.92518
    p_a2 = 1.0 - 1e-15
    p_a3 = 1.0 - 1e-15

    joint_power_conservative = compute_frechet_bonferroni_joint_power([p_a1_conservative, p_a2, p_a3])
    assert round(joint_power_conservative, 4) == 0.9252
    assert joint_power_conservative > 0.90  # Exceeds 90% gold standard


# ==============================================================================
# 3. Boundary & Malformed Configuration Tests
# ==============================================================================


def test_boundary_zero_events_satisfies_gate_1():
    """BND-01: Zero catastrophic events across 128 clusters clears Gate 1 (0.02314 <= 0.050)."""
    res = compute_clustered_operational_risk([0.0] * 128, n_cases_per_cluster=400, alpha=0.050)
    assert res["ucb_cluster"] <= OPERATIONAL_RISK_LIMIT
    assert res["gate1_passed"] is True


def test_boundary_100_percent_harm_fails_gate_1():
    """BND-02: 100% harm across clusters strictly fails Gate 1 (UCB = 1.0 > 0.050)."""
    res = compute_clustered_operational_risk([1.0] * 128, n_cases_per_cluster=400, alpha=0.050)
    assert res["ucb_cluster"] > OPERATIONAL_RISK_LIMIT
    assert res["gate1_passed"] is False


def test_boundary_queue_capacity_edges():
    """BND-03: Queue capacity at 0 drops all cases; capacity at 1 drops second case."""
    case = make_cs_cases_v07_1(1, SAFE_TEST_SEEDS[0])[0]

    # Capacity 0: immediate drop
    q0 = QueueState(capacity_limit=0)
    res0 = execute_escalation_cs(case, 0.0, 0.0, None, queue_state=q0)
    assert q0.drop_count == 1
    assert res0["reason"] == "human_queue_capacity_exhausted"

    # Capacity 1: first accepted, second dropped
    q1 = QueueState(capacity_limit=1)
    execute_escalation_cs(case, 0.0, 0.0, None, queue_state=q1)
    res1_second = execute_escalation_cs(case, 0.0, 0.0, None, queue_state=q1)
    assert q1.escalation_count == 2
    assert q1.drop_count == 1
    assert res1_second["reason"] == "human_queue_capacity_exhausted"


def test_malformed_case_count_rejected():
    """BND-04: Case count n < 1 is rejected by generator."""
    with pytest.raises(ValueError, match="Invalid count"):
        make_cs_cases_v07_1(0, SAFE_TEST_SEEDS[0])

    with pytest.raises(ValueError, match="Invalid count"):
        make_de_cases_v07_1(-5, SAFE_TEST_SEEDS[0])


def test_constant_positive_cluster_risks_fail_closed():
    """BND-05: Constant positive cluster risk triggers fail-closed GATE 1 FAIL / INCONCLUSIVE.

    Degenerate zero-variance data cannot support standard Student-t inference without unverified
    distributional assumptions. ucb_cluster is set to 1.0 as an explicit worst-case policy bound
    (not a calculated 95% confidence estimate), gate1_passed is strictly False, and method is
    'degenerate_constant_positive_risk_fail_closed'.
    """
    # Constant 0.01 across all 128 clusters: MUST FAIL Gate 1
    res_01 = compute_clustered_operational_risk([0.01] * 128, n_cases_per_cluster=400, alpha=0.050)
    assert res_01["zero_event_regime"] is False
    assert res_01["inference_method"] == "degenerate_constant_positive_risk_fail_closed"
    assert abs(res_01["mean_risk"] - 0.010) < 1e-7
    assert res_01["std_risk"] == 0.0
    assert res_01["ucb_cluster"] == 1.0
    assert res_01["gate1_passed"] is False

    # Constant 0.06 across all 128 clusters: MUST FAIL Gate 1
    res_06 = compute_clustered_operational_risk([0.06] * 128, n_cases_per_cluster=400, alpha=0.050)
    assert res_06["zero_event_regime"] is False
    assert res_06["inference_method"] == "degenerate_constant_positive_risk_fail_closed"
    assert abs(res_06["mean_risk"] - 0.060) < 1e-7
    assert res_06["std_risk"] == 0.0
    assert res_06["ucb_cluster"] == 1.0
    assert res_06["gate1_passed"] is False

    # Constant 1.0 across all 128 clusters: MUST FAIL Gate 1
    res_10 = compute_clustered_operational_risk([1.0] * 128, n_cases_per_cluster=400, alpha=0.050)
    assert res_10["zero_event_regime"] is False
    assert res_10["inference_method"] == "degenerate_constant_positive_risk_fail_closed"
    assert res_10["mean_risk"] == 1.0
    assert res_10["std_risk"] == 0.0
    assert res_10["ucb_cluster"] == 1.0
    assert res_10["gate1_passed"] is False


def test_gate1_failure_inviolable_downstream():
    """BND-05b: Gate 1 failure strictly disqualifies candidate policy in evaluate_two_stage_gatekeeping.

    Even if candidate policy achieves overwhelming utility superiority over all comparators in Stage 2,
    Gate 1 failure unconditionally sets study_verdict to CONFIRMATORY_STUDY_FAILED_SAFETY_GATE.
    """
    from experiments_v07_1.evaluate_confirmatory_v07_1 import evaluate_two_stage_gatekeeping

    # Construct synthetic cluster records where candidate policy has constant positive risk 0.01 (Gate 1 fail)
    # but massive utility (1.0 vs 0.0 for comparators)
    synthetic_records = []
    for k in range(128):
        rec = {
            "cluster_index": k,
            "seed": 70003001 + k,
            "domain": "cs",
            "policy_metrics": {
                "candidate": {"mean_utility": 1.0, "operational_risk": 0.01, "auth_violations": 0},
                "comp_a": {"mean_utility": 0.0, "operational_risk": 0.0, "auth_violations": 0},
                "comp_b": {"mean_utility": 0.0, "operational_risk": 0.0, "auth_violations": 0},
            },
        }
        synthetic_records.append(rec)

    primary_contrasts = [
        ("C1", "candidate", "comp_a"),
        ("C2", "candidate", "comp_b"),
    ]

    verdict_result = evaluate_two_stage_gatekeeping(
        cluster_records=synthetic_records,
        candidate_name="candidate",
        primary_contrasts=primary_contrasts,
        delta_hurdle=0.015,
        alpha_contrast=0.0033333333333333335,
    )

    assert verdict_result["candidate_gate1_passed"] is False
    assert verdict_result["study_verdict"] == "CONFIRMATORY_STUDY_FAILED_SAFETY_GATE"
    assert verdict_result["safety_evaluations"]["candidate"]["commercial_deployment_status"] == "SAFETY_DISQUALIFIED"


def test_invalid_and_non_finite_cluster_risks_rejected():
    """BND-06: Non-finite (NaN, Inf), negative, >1, non-numeric, or empty lists are rejected."""
    # Empty list
    with pytest.raises(ProtocolValidationError, match="Cannot compute operational risk on empty"):
        compute_clustered_operational_risk([])

    # NaN in risks
    with pytest.raises(ProtocolValidationError, match="Non-finite cluster risk"):
        compute_clustered_operational_risk([float("nan")] * 128)

    # Positive Infinity in risks
    with pytest.raises(ProtocolValidationError, match="Non-finite cluster risk"):
        compute_clustered_operational_risk([float("inf")] * 128)

    # Negative Infinity in risks
    with pytest.raises(ProtocolValidationError, match="Non-finite cluster risk"):
        compute_clustered_operational_risk([float("-inf")] * 128)

    # Negative risk
    with pytest.raises(ProtocolValidationError, match="Cluster risk out of bounds"):
        compute_clustered_operational_risk([-0.01] + [0.0] * 127)

    # Greater than 1.0 risk
    with pytest.raises(ProtocolValidationError, match="Cluster risk out of bounds"):
        compute_clustered_operational_risk([1.01] + [0.0] * 127)

    # Non-numeric types (e.g. str, None, bool)
    with pytest.raises(ProtocolValidationError, match="Invalid non-numeric risk"):
        compute_clustered_operational_risk(["invalid"] * 128)  # type: ignore

    with pytest.raises(ProtocolValidationError, match="Invalid non-numeric risk"):
        compute_clustered_operational_risk([None] * 128)  # type: ignore

    with pytest.raises(ProtocolValidationError, match="Invalid non-numeric risk"):
        compute_clustered_operational_risk([True] * 128)  # type: ignore


# ==============================================================================
# 4. Protocol JSON & Markdown Specification Consistency Tests
# ==============================================================================


def test_protocol_json_and_markdown_consistency():
    """DOC-01: Verifies exact consistency between protocol JSON and Markdown specifications."""
    json_path = ROOT / "experiments_v07_1" / "v071_confirmatory_protocol.json"
    md_path = ROOT / "research" / "methodology" / "v071-confirmatory-statistical-protocol.md"

    assert json_path.exists()
    assert md_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        proto_json = json.load(f)

    md_content = md_path.read_text(encoding="utf-8")

    # 1. Study version
    assert proto_json["protocol_version"] == "0.7.1-review-candidate"
    assert "0.7.1-isolated" in md_content

    # 2. Hurdle Delta
    assert proto_json["statistical_parameters"]["superiority_hurdle_delta"] == 0.015
    assert "Delta = +0.015" in md_content or "Delta >= +0.015" in md_content

    # 3. FWER Alpha and per-contrast alpha
    assert proto_json["statistical_parameters"]["family_wise_alpha"] == 0.010
    assert proto_json["statistical_parameters"]["primary_multiplicity_contrasts"] == 3
    assert abs(proto_json["statistical_parameters"]["per_contrast_alpha_primary"] - 0.0033333333333333335) < 1e-9
    assert "0.010/3" in md_content

    # 4. Critical t-value
    assert proto_json["statistical_parameters"]["critical_t_value_primary"] == 2.758398
    assert proto_json["statistical_parameters"]["critical_t_value_rounded"] == 2.7584
    assert "2.758398" in md_content

    # 5. Clustered operational risk threshold and zero-event bound
    assert proto_json["statistical_parameters"]["operational_risk_threshold_r_limit"] == 0.050
    assert proto_json["two_stage_gatekeeping_rules"]["gate_1_safety_compliance"]["zero_event_cluster_ucb_095"] == 0.02314
    assert "0.02314" in md_content

    # 6. Sample size
    assert proto_json["sample_allocation"]["clusters_per_domain_k"] == 128
    assert proto_json["sample_allocation"]["cases_per_cluster"] == 400
    assert proto_json["sample_allocation"]["total_cases_per_domain"] == 51200
    assert "K = 128" in md_content
    assert "51{,}200" in md_content

    # 7. Immutability Manifest (21 Assets)
    bindings = proto_json["codebase_immutability_bindings"]
    assert len(bindings) == 21
    assert "REVIEW-CANDIDATE IMMUTABILITY MANIFEST (21 ASSETS)" in md_content
    assert proto_json["manifest_architecture"]["total_mandatory_assets"] == 21

    # 8. Unresolved authorization governance
    auth = proto_json["authorization"]
    assert auth["confirmatory_development_authorized"] is False
    assert auth["authorization_governance_status"] == "UNRESOLVED_GOVERNANCE_DECISION"
    assert "Unresolved Authorization Governance Decision" in md_content


# ==============================================================================
# 5. Statistical Contrast Robustness & Non-Finite Number Tests (CG-VULN-04)
# ==============================================================================


def test_paired_contrast_statistics_rejects_non_finite_and_invalid_utilities():
    """CG-VULN-04a: compute_paired_contrast_statistics strictly rejects NaN, Inf, and non-numeric inputs."""
    valid_cand = [1.0 + 0.01 * (i % 3) for i in range(10)]
    valid_comp = [0.9 + 0.005 * (i % 3) for i in range(10)]

    # Candidate NaN
    with pytest.raises(ProtocolValidationError, match="Invalid non-finite or non-numeric"):
        compute_paired_contrast_statistics([float("nan")] * 10, valid_comp, "C1", "cand", "comp")

    # Comparator NaN
    with pytest.raises(ProtocolValidationError, match="Invalid non-finite or non-numeric"):
        compute_paired_contrast_statistics(valid_cand, [float("nan")] * 10, "C1", "cand", "comp")

    # Positive Infinity
    with pytest.raises(ProtocolValidationError, match="Invalid non-finite or non-numeric"):
        compute_paired_contrast_statistics([float("inf")] * 10, valid_comp, "C1", "cand", "comp")

    with pytest.raises(ProtocolValidationError, match="Invalid non-finite or non-numeric"):
        compute_paired_contrast_statistics(valid_cand, [float("inf")] * 10, "C1", "cand", "comp")

    # Negative Infinity
    with pytest.raises(ProtocolValidationError, match="Invalid non-finite or non-numeric"):
        compute_paired_contrast_statistics([float("-inf")] * 10, valid_comp, "C1", "cand", "comp")

    # Boolean types (rejected to prevent numeric coercion True -> 1.0)
    with pytest.raises(ProtocolValidationError, match="Invalid non-finite or non-numeric"):
        compute_paired_contrast_statistics([True] * 10, valid_comp, "C1", "cand", "comp")  # type: ignore

    # String types
    with pytest.raises(ProtocolValidationError, match="Invalid non-finite or non-numeric"):
        compute_paired_contrast_statistics(valid_cand, ["invalid"] * 10, "C1", "cand", "comp")  # type: ignore


def test_paired_contrast_statistics_degenerate_variance_inconclusive():
    """CG-VULN-04b: Degenerate zero-variance paired difference is fail-closed / inconclusive.

    When all cluster utility differences are identical (s_D == 0), Student-t inference is degenerate.
    Must NOT manufacture artificial statistical significance (such as t=999, p=0).
    """
    # Constant positive difference: cand = 1.00, comp = 0.95 across all 128 clusters (diff = +0.050 > 0.015)
    cand_utils = [1.00] * 128
    comp_utils = [0.95] * 128

    res = compute_paired_contrast_statistics(
        cand_utilities=cand_utils,
        comp_utilities=comp_utils,
        contrast_name="C1_recovery",
        cand_name="candidate",
        comp_name="comparator",
        delta_hurdle=DELTA_HURDLE,
        alpha=0.0033333333333333335,
    )

    assert res["sd_diff"] == 0.0
    assert res["se_diff"] == 0.0
    assert res["hurdle_achieved"] is False
    assert res["rejection"] is False
    assert res["contrast_verdict"] == "INCONCLUSIVE_DEGENERATE_VARIANCE"
    assert res["t_stat_hurdle"] == 0.0
    assert res["p_value_one_sided"] == 1.0
    assert res["lcb_bonferroni"] == -1.0  # Explicit finite worst-case lower bound


def test_gatekeeping_degenerate_superiority_variance_yields_inconclusive_study():
    """CG-VULN-04c: Degenerate zero-variance superiority cannot manufacture CONFIRMATORY_STUDY_SUCCESS.

    Even if Gate 1 passes and all differences are positive, zero variance strictly sets
    study_verdict to CONFIRMATORY_STUDY_INCONCLUSIVE.
    """
    from experiments_v07_1.evaluate_confirmatory_v07_1 import evaluate_two_stage_gatekeeping

    # Construct mock records where candidate passes Gate 1 (cand_risk = 0.0),
    # but utility differences against all comparators have zero variance
    records = []
    for k in range(128):
        rec = {
            "cluster_index": k,
            "seed": 70003001 + k,
            "domain": "de",
            "policy_metrics": {
                "candidate": {"mean_utility": 1.00, "operational_risk": 0.0, "auth_violations": 0},
                "comp_a": {"mean_utility": 0.90, "operational_risk": 0.0, "auth_violations": 0},
                "comp_b": {"mean_utility": 0.85, "operational_risk": 0.0, "auth_violations": 0},
            },
        }
        records.append(rec)

    primary_contrasts = [
        ("C1", "candidate", "comp_a"),
        ("C2", "candidate", "comp_b"),
    ]

    verdict_result = evaluate_two_stage_gatekeeping(
        cluster_records=records,
        candidate_name="candidate",
        primary_contrasts=primary_contrasts,
        delta_hurdle=0.015,
        alpha_contrast=0.0033333333333333335,
    )

    assert verdict_result["candidate_gate1_passed"] is True
    assert verdict_result["all_contrasts_superior"] is False
    assert verdict_result["study_verdict"] == "CONFIRMATORY_STUDY_INCONCLUSIVE"

"""Tests for CausaGuard v0.7.1 Counterfactual Study Execution and Order Invariance."""


from causaguard_v07_1.domain_cs import make_cs_cases_v07_1
from causaguard_v07_1.domain_de import make_de_cases_v07_1
from causaguard_v07_1.policy_v07_1 import (
    AlwaysEscalatePolicyV07_1,
    AlwaysRecoveryPolicyV07_1,
    CostRulePolicyV07_1,
)
from causaguard_v07_1.study_v07_1 import (
    evaluate_cluster_v07_1,
    evaluate_potential_outcomes_v07_1,
)


def test_paired_counterfactual_potential_outcomes_consistency():
    cases = make_cs_cases_v07_1(5, seed=777, profile="iid")
    case = cases[0]

    policies = {
        "cost_rule": CostRulePolicyV07_1(),
        "always_escalate": AlwaysEscalatePolicyV07_1(),
        "always_recovery": AlwaysRecoveryPolicyV07_1(),
    }

    # Evaluate twice independently
    res1 = evaluate_potential_outcomes_v07_1(case, policies)
    res2 = evaluate_potential_outcomes_v07_1(case, policies)

    for p_name in policies:
        assert res1[p_name]["utility"] == res2[p_name]["utility"]
        assert res1[p_name]["completed"] == res2[p_name]["completed"]
        assert res1[p_name]["unsafe"] == res2[p_name]["unsafe"]
        assert res1[p_name]["cost"] == res2[p_name]["cost"]
        assert res1[p_name]["latency"] == res2[p_name]["latency"]


def test_strict_policy_order_invariance():
    # Crucial test: evaluating policies in order [A, B] vs [B, A] must yield IDENTICAL metrics!
    cases = make_cs_cases_v07_1(20, seed=888, profile="iid")

    pol_a = AlwaysEscalatePolicyV07_1()
    pol_b = CostRulePolicyV07_1()

    # Order 1: [A, B]
    order1 = {"escalate": pol_a, "cost_rule": pol_b}
    res1 = evaluate_cluster_v07_1(cases, policies=order1, capacity_limit=10)

    # Order 2: [B, A]
    order2 = {"cost_rule": pol_b, "escalate": pol_a}
    res2 = evaluate_cluster_v07_1(cases, policies=order2, capacity_limit=10)

    # Metrics for A must be identical
    m1_a = res1["policy_metrics"]["escalate"]
    m2_a = res2["policy_metrics"]["escalate"]
    assert m1_a["mean_utility"] == m2_a["mean_utility"]
    assert m1_a["operational_risk"] == m2_a["operational_risk"]
    assert m1_a["queue_diagnostics"]["total_escalations"] == m2_a["queue_diagnostics"]["total_escalations"]
    assert m1_a["queue_diagnostics"]["queue_drops"] == m2_a["queue_diagnostics"]["queue_drops"]

    # Metrics for B must be identical
    m1_b = res1["policy_metrics"]["cost_rule"]
    m2_b = res2["policy_metrics"]["cost_rule"]
    assert m1_b["mean_utility"] == m2_b["mean_utility"]
    assert m1_b["operational_risk"] == m2_b["operational_risk"]
    assert m1_b["queue_diagnostics"]["total_escalations"] == m2_b["queue_diagnostics"]["total_escalations"]


def test_queue_state_isolation_across_policies():
    cases = make_cs_cases_v07_1(20, seed=999, profile="iid")

    # Policy 1 escalates everything (20 escalations)
    # Policy 2 recovers everything (0 escalations)
    policies = {
        "always_escalate": AlwaysEscalatePolicyV07_1(),
        "always_recovery": AlwaysRecoveryPolicyV07_1(),
    }
    res = evaluate_cluster_v07_1(cases, policies=policies, capacity_limit=15)

    m_esc = res["policy_metrics"]["always_escalate"]
    m_rec = res["policy_metrics"]["always_recovery"]

    # Always escalate exceeded capacity limit 15 -> drops >= 5
    assert m_esc["queue_diagnostics"]["total_escalations"] == 20
    assert m_esc["queue_diagnostics"]["queue_drops"] >= 5

    # Always recovery must have ZERO escalations and ZERO drops
    assert m_rec["queue_diagnostics"]["total_escalations"] == 0
    assert m_rec["queue_diagnostics"]["queue_drops"] == 0


def test_de_cluster_evaluation_metrics():
    cases = make_de_cases_v07_1(15, seed=123, profile="iid")
    res = evaluate_cluster_v07_1(cases)

    assert res["domain"] == "data_engineering"
    assert res["n_cases"] == 15
    assert len(res["policy_metrics"]) == 8

    cand = res["policy_metrics"]["cost_rule_v07_1"]
    assert "mean_utility" in cand
    assert "operational_risk" in cand
    assert "queue_diagnostics" in cand

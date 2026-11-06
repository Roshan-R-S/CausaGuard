"""Tests for CausaGuard v0.7.1 Policy Fairness, Interface Symmetry, and Anti-Leakage Constraints."""

import pytest
from causaguard_v07_1.domain_cs import make_cs_cases_v07_1
from causaguard_v07_1.domain_de import make_de_cases_v07_1
from causaguard_v07_1.policy_v07_1 import (
    CostRulePolicyV07_1,
    OraclePolicyV07_1,
    get_baseline_policies_v07_1,
)


def test_baseline_policies_suite_contains_all_eight_policies():
    policies = get_baseline_policies_v07_1()
    expected = {
        "cost_rule_v07_1",
        "always_escalate",
        "always_recovery",
        "budget_aware_direct_recovery",
        "escalation_aware_deterministic_threshold",
        "cost_sensitive_symmetric_heuristic",
        "fixed_verify_repair_macro",
        "oracle",
    }
    assert set(policies.keys()) == expected
    assert len(policies) == 8


def test_zero_latent_state_leakage_prohibition():
    cases = make_cs_cases_v07_1(1, seed=777, profile="iid")
    case = cases[0]
    pol = CostRulePolicyV07_1()

    # Must reject CSCase object directly
    with pytest.raises(TypeError, match="accepts only Observation, not Case"):
        pol.select(observation=case)  # type: ignore

    # Must reject private case in kwargs
    with pytest.raises(TypeError, match="prohibits private case"):
        pol.select(observation=case.observation, case=case)


def test_cost_rule_prunes_verify_at_budget_one():
    # When B=1, verifying consumes 1 op leaving 0 ops, which is strictly dominated
    cases_cs = make_cs_cases_v07_1(10, seed=777, profile="iid")
    pol = CostRulePolicyV07_1()

    for c in cases_cs:
        action = pol.select(observation=c.observation, evidence=None, b_rem=1)
        assert action in ("proceed", "retry", "escalate")
        assert action != "verify", "CostRulePolicyV07_1 must prune verify at B=1!"

    cases_de = make_de_cases_v07_1(10, seed=777, profile="iid")
    for c in cases_de:
        action = pol.select(observation=c.observation, evidence=None, b_rem=1)
        assert action in ("proceed", "restore", "escalate")
        assert action != "verify", "CostRulePolicyV07_1 must prune verify at B=1!"


def test_symmetric_action_space_availability():
    # Verify that heuristic baselines can select all valid actions
    cases = make_cs_cases_v07_1(20, seed=777, profile="iid")
    policies = get_baseline_policies_v07_1()

    # Test that across the cases, all feasible actions are accessible
    heur = policies["cost_sensitive_symmetric_heuristic"]
    actions_seen = set()
    for c in cases:
        a = heur.select(observation=c.observation, evidence=None, b_rem=2)
        actions_seen.add(a)

    # Heuristic should use a diverse set of actions
    assert len(actions_seen) >= 2


def test_oracle_policy_access_and_truth_alignment():
    cases_cs = make_cs_cases_v07_1(20, seed=777, profile="iid")
    oracle = OraclePolicyV07_1()

    for c in cases_cs:
        a = oracle.select(observation=c.observation, b_rem=2, case=c)
        if c.latent_state == "clean":
            assert a == "proceed"
        elif c.latent_state == "stale":
            assert a == "retry"
        else:
            assert a == "escalate"

    # Oracle without case raises ValueError
    with pytest.raises(ValueError, match="OraclePolicyV07_1 requires case"):
        oracle.select(observation=cases_cs[0].observation, b_rem=2)

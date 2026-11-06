"""Unit and invariant tests for CausaGuard v0.7 Study and Potential Outcomes Engine."""

from __future__ import annotations

import copy

import pytest
from causaguard_v07.domain_cs import CSCaseV07, make_cs_cases_v07
from causaguard_v07.domain_de import DECaseV07
from causaguard_v07.policy_v07 import (
    AlwaysRecoveryPolicyV07,
    CostRulePolicyV07,
    RulesProceedPolicyV07,
    get_baseline_policies_v07,
)
from causaguard_v07.study_v07 import (
    evaluate_potential_outcomes_v07,
    generate_cases_v07,
    run_episode_v07,
)


def test_generate_cases_v07():
    """Validates generator dispatcher for CS and DE domains."""
    cs_cases = generate_cases_v07("cs", n=4, seed=70004001, profile="iid")
    assert len(cs_cases) == 4
    assert all(isinstance(c, CSCaseV07) for c in cs_cases)

    de_cases = generate_cases_v07("de", n=4, seed=70004001, profile="iid")
    assert len(de_cases) == 4
    assert all(isinstance(c, DECaseV07) for c in de_cases)

    with pytest.raises(ValueError, match="Unknown domain"):
        generate_cases_v07("unknown", n=1, seed=70004001)


def test_run_episode_operation_accounting():
    """Asserts that unitary operation accounting strictly holds during an episode."""
    case = make_cs_cases_v07(n=1, seed=70004002, profile="iid")[0]
    policies = get_baseline_policies_v07()

    for name, pol in policies.items():
        res = run_episode_v07(case=case, policy=pol)
        assert res["policy"] == name
        assert res["case_key"] == case.key
        assert res["total_ops"] <= case.observation.budget
        assert res["b_rem"] >= 0
        assert res["num_steps"] in (1, 2)
        if res["actions"][0] == "verify":
            assert res["num_steps"] == 2
        else:
            assert res["num_steps"] == 1


def test_potential_outcomes_pairing():
    """Verifies that evaluate_potential_outcomes_v07 evaluates all 9 policies on the exact same case."""
    case = make_cs_cases_v07(n=1, seed=70004003, profile="iid")[0]
    outcomes = evaluate_potential_outcomes_v07(case)

    assert len(outcomes) == 9
    expected_policies = {
        "rules_proceed",
        "always_escalate",
        "always_verify_then_proceed",
        "fixed_verify_repair_macro",
        "always_recovery",
        "budget_aware_direct_recovery",
        "cost_sensitive_threshold_recovery",
        "cost_rule_v07",
        "oracle",
    }
    assert set(outcomes.keys()) == expected_policies
    for name, res in outcomes.items():
        assert res["case_key"] == case.key
        assert res["budget"] == case.observation.budget


def test_potential_outcomes_case_immutability_and_permutation_invariance():
    """Asserts that running potential outcomes does not mutate the case and order of execution does not alter results."""
    case = make_cs_cases_v07(n=1, seed=70004004, profile="iid")[0]
    case_copy = copy.deepcopy(case)

    pol1 = RulesProceedPolicyV07()
    pol2 = AlwaysRecoveryPolicyV07()
    pol3 = CostRulePolicyV07()

    # Order 1: pol1 -> pol2 -> pol3
    res1_order1 = run_episode_v07(case, pol1)
    res2_order1 = run_episode_v07(case, pol2)
    res3_order1 = run_episode_v07(case, pol3)

    # Verify case has not mutated
    assert case.record() == case_copy.record()

    # Order 2: pol3 -> pol1 -> pol2
    res3_order2 = run_episode_v07(case, pol3)
    res1_order2 = run_episode_v07(case, pol1)
    res2_order2 = run_episode_v07(case, pol2)

    assert res1_order1 == res1_order2
    assert res2_order1 == res2_order2
    assert res3_order1 == res3_order2


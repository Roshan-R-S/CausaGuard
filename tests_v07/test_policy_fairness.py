"""Unit and invariant tests for CausaGuard v0.7 Policy Suite and Fairness."""

from __future__ import annotations

from causaguard_v07.domain_cs import (
    ACTIONS_CS_V07,
    CSEvidenceV07,
    make_cs_cases_v07,
)
from causaguard_v07.domain_de import make_de_cases_v07
from causaguard_v07.policy_v07 import (
    BasePolicyV07,
    CostRulePolicyV07,
    OraclePolicyV07,
    get_baseline_policies_v07,
)


def test_baseline_suite_completeness():
    """Validates that all 9 required comparators are present in the registry."""
    policies = get_baseline_policies_v07()
    expected_names = {
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
    assert set(policies.keys()) == expected_names
    for name, pol in policies.items():
        assert isinstance(pol, BasePolicyV07)
        assert pol.name == name


def test_zero_latent_state_leakage():
    """Ensures non-oracle policies cannot access or leak latent state information."""
    policies = get_baseline_policies_v07()
    non_oracle = {k: v for k, v in policies.items() if k != "oracle"}

    cases = make_cs_cases_v07(n=30, seed=70003001, profile="iid")
    clean_cases = [c for c in cases if c.latent_state == "clean"]
    fraud_cases = [c for c in cases if c.latent_state == "fraud"]

    assert len(clean_cases) > 0 and len(fraud_cases) > 0

    obs = clean_cases[0].observation
    evidence = CSEvidenceV07(flagged=True, evidence_age_hours=0.2)

    for name, pol in non_oracle.items():
        # Policy select must work without any 'case' kwarg
        act1 = pol.select(observation=obs, evidence=None, b_rem=2)
        assert act1 in ACTIONS_CS_V07

        act2 = pol.select(observation=obs, evidence=evidence, b_rem=1)
        assert act2 in ACTIONS_CS_V07

        # Pass dummy kwargs or latent information; policy must ignore it and produce identical action
        act1_with_kw = pol.select(observation=obs, evidence=None, b_rem=2, latent_state="fraud")
        assert act1 == act1_with_kw


def test_budget_one_feasibility_invariant():
    """Asserts that when remaining budget is 1, decision-theoretic, heuristic, and recovery policies never select verify."""
    policies = get_baseline_policies_v07()
    # All policies except blind always_verify_then_proceed must select a terminal action when b_rem=1
    budget_aware_suite = {
        k: v for k, v in policies.items() if k not in ("oracle", "always_verify_then_proceed")
    }

    cs_cases = make_cs_cases_v07(n=10, seed=70003002, profile="iid")
    de_cases = make_de_cases_v07(n=10, seed=70003002, profile="iid")

    # In CS domain
    for c in cs_cases:
        for name, pol in budget_aware_suite.items():
            act = pol.select(observation=c.observation, evidence=None, b_rem=1)
            assert act != "verify", f"Policy {name} selected 'verify' when b_rem=1 on CS case {c.key}!"
            assert act in ("proceed", "retry", "escalate")

    # In DE domain
    for c in de_cases:
        for name, pol in budget_aware_suite.items():
            act = pol.select(observation=c.observation, evidence=None, b_rem=1)
            assert act != "verify", f"Policy {name} selected 'verify' when b_rem=1 on DE case {c.key}!"
            assert act in ("proceed", "restore", "escalate")

    # AlwaysVerifyThenProceed is blind and always selects verify at Step 1 regardless of budget
    blind_pol = policies["always_verify_then_proceed"]
    assert blind_pol.select(observation=cs_cases[0].observation, evidence=None, b_rem=1) == "verify"
    assert blind_pol.select(observation=de_cases[0].observation, evidence=None, b_rem=1) == "verify"


def test_equal_baseline_access():
    """Asserts that baselines have equal, fair access to recovery and escalation actions."""
    policies = get_baseline_policies_v07()

    # Always recovery selects retry in CS and restore in DE
    cs_obs = make_cs_cases_v07(n=1, seed=70003003)[0].observation
    de_obs = make_de_cases_v07(n=1, seed=70003003)[0].observation

    always_rec = policies["always_recovery"]
    assert always_rec.select(cs_obs, evidence=None, b_rem=1) == "retry"
    assert always_rec.select(de_obs, evidence=None, b_rem=1) == "restore"

    always_esc = policies["always_escalate"]
    assert always_esc.select(cs_obs, evidence=None, b_rem=1) == "escalate"
    assert always_esc.select(de_obs, evidence=None, b_rem=1) == "escalate"


def test_cost_rule_bayesian_decision_logic():
    """Tests analytical Bayesian VOI decision logic in CostRulePolicyV07."""
    cost_rule = CostRulePolicyV07()
    cases = make_cs_cases_v07(n=10, seed=70003004, profile="iid")

    for case in cases:
        # Step 1 decision
        act1 = cost_rule.select(observation=case.observation, evidence=None, b_rem=case.observation.budget)
        assert act1 in ACTIONS_CS_V07

        # If b_rem == 1, act1 must be terminal
        if case.observation.budget == 1:
            assert act1 in ("proceed", "retry", "escalate")

        # Step 2 decision post-verify
        ev = CSEvidenceV07(flagged=True, evidence_age_hours=0.25)
        act2 = cost_rule.select(observation=case.observation, evidence=ev, b_rem=1)
        assert act2 in ("proceed", "retry", "escalate")


def test_oracle_policy_requires_case():
    """Asserts that the diagnostic Oracle policy operates with case context."""
    oracle = OraclePolicyV07()
    cases = make_cs_cases_v07(n=3, seed=70003005, profile="iid")

    for c in cases:
        act = oracle.select(observation=c.observation, evidence=None, b_rem=c.observation.budget, case=c)
        assert act in ACTIONS_CS_V07

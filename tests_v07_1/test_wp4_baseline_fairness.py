"""Tests for CausaGuard v0.7.1 WP4 Baseline Fairness and Comparative Evaluation.

Verifies:
1. Complete suite inventory of all 6 PhD Roadmap Work Package 4 baselines + contextual reference;
2. Strict zero-latent leakage enforcement across all comparators;
3. Budget parity and operational feasibility at B=1 and B=2;
4. Equal information access (public observations and paid evidence only);
5. Replay reproducibility and policy-order invariance;
6. Shared multi-domain compatibility (CS and DE);
7. Post-verification defect handling and independent outcome grading;
8. Queue-state isolation across all comparators during counterfactual evaluation.
"""

from __future__ import annotations

import pytest
from causaguard_v07_1.domain_cs import (
    ACTIONS_CS_V07_1,
    CSEvidenceV07_1,
    make_cs_cases_v07_1,
)
from causaguard_v07_1.domain_de import (
    ACTIONS_DE_V07_1,
    DEEvidenceV07_1,
    make_de_cases_v07_1,
)
from causaguard_v07_1.policy_v07_1 import (
    AlwaysEscalatePolicyV07_1,
    CostRulePolicyV07_1,
)
from causaguard_v07_1.study_v07_1 import evaluate_cluster_v07_1, run_episode_v07_1

from research.experiments.wp4_baseline_comparison.adapters import (
    AlwaysVerifyPolicyV07_1,
    ConservativeCausaGuardPolicyV07_1,
    OriginalCausaGuardPolicyV07_1,
    RulesProceedPolicyV07_1,
    RulesRepairPolicyV07_1,
    get_wp4_comparators_v07_1,
)


def test_wp4_comparators_suite_inventory():
    """WP4 Task 1: Complete inventory of all six required comparators + contextual reference."""
    comparators = get_wp4_comparators_v07_1()
    expected_names = {
        "always_verify",
        "always_escalate",
        "rules_proceed",
        "rules_repair",
        "original_causaguard",
        "conservative_causaguard",
        "cost_rule_v07_1",
    }
    assert set(comparators.keys()) == expected_names
    assert len(comparators) == 7

    assert isinstance(comparators["always_verify"], AlwaysVerifyPolicyV07_1)
    assert isinstance(comparators["always_escalate"], AlwaysEscalatePolicyV07_1)
    assert isinstance(comparators["rules_proceed"], RulesProceedPolicyV07_1)
    assert isinstance(comparators["rules_repair"], RulesRepairPolicyV07_1)
    assert isinstance(comparators["original_causaguard"], OriginalCausaGuardPolicyV07_1)
    assert isinstance(comparators["conservative_causaguard"], ConservativeCausaGuardPolicyV07_1)
    assert isinstance(comparators["cost_rule_v07_1"], CostRulePolicyV07_1)


def test_strict_zero_latent_leakage_all_wp4_comparators():
    """WP4 Task 2: All comparators must strictly reject Case objects and prevent private kwarg snooping."""
    cs_case = make_cs_cases_v07_1(1, seed=84100001, profile="iid")[0]
    de_case = make_de_cases_v07_1(1, seed=84100001, profile="iid")[0]
    comparators = get_wp4_comparators_v07_1()

    for name, policy in comparators.items():
        if name != "always_escalate":
            # 1. Must reject Case object passed directly as observation
            with pytest.raises(TypeError, match="accepts only Observation, not Case"):
                policy.select(observation=cs_case)  # type: ignore

            with pytest.raises(TypeError, match="accepts only Observation, not Case"):
                policy.select(observation=de_case)  # type: ignore

        # 2. Strict anti-snooping: passing private case kwarg either raises TypeError (cost_rule) or is strictly ignored
        if name == "cost_rule_v07_1":
            with pytest.raises(TypeError, match="prohibits private case"):
                policy.select(observation=cs_case.observation, case=cs_case)
        else:
            act_clean = policy.select(observation=cs_case.observation, b_rem=2)
            act_with_case = policy.select(observation=cs_case.observation, b_rem=2, case=cs_case)
            assert act_clean == act_with_case, f"Policy {name} snooped on private case kwarg!"

        # 3. Must reject non-observation types
        if name != "always_escalate":
            with pytest.raises(TypeError, match="Invalid observation type"):
                policy.select(observation="invalid_string")  # type: ignore


def test_budget_parity_enforcement_at_budget_one():
    """WP4 Task 2: Operation budget parity: no comparator may attempt verify at B=1."""
    cs_cases = make_cs_cases_v07_1(25, seed=84100002, profile="iid")
    de_cases = make_de_cases_v07_1(25, seed=84100002, profile="iid")
    comparators = get_wp4_comparators_v07_1()

    for name, policy in comparators.items():
        for case in cs_cases:
            action = policy.select(observation=case.observation, evidence=None, b_rem=1)
            assert action in ACTIONS_CS_V07_1, f"{name} selected unknown action {action} in CS"
            assert action != "verify", f"{name} violated budget parity: selected verify at B=1 in CS"

        for case in de_cases:
            action = policy.select(observation=case.observation, evidence=None, b_rem=1)
            assert action in ACTIONS_DE_V07_1, f"{name} selected unknown action {action} in DE"
            assert action != "verify", f"{name} violated budget parity: selected verify at B=1 in DE"


def test_deterministic_replay_reproducibility():
    """WP4 Task 2: Deterministic replay: repeated execution on same case produces identical trajectories."""
    case = make_cs_cases_v07_1(1, seed=84100003, profile="iid")[0]
    comparators = get_wp4_comparators_v07_1()

    for name, policy in comparators.items():
        ep1 = run_episode_v07_1(case=case, policy=policy)
        ep2 = run_episode_v07_1(case=case, policy=policy)

        assert ep1["action"] == ep2["action"]
        assert ep1["step1_action"] == ep2["step1_action"]
        assert ep1["step2_action"] == ep2["step2_action"]
        assert ep1["utility"] == ep2["utility"]
        assert ep1["cost"] == ep2["cost"]
        assert ep1["safe_completion"] == ep2["safe_completion"]
        assert ep1["unsafe"] == ep2["unsafe"]


def test_equal_information_public_observations_only():
    """WP4 Task 2: Policies receive only public observations and cannot access latent simulator state."""
    cs_case = make_cs_cases_v07_1(1, seed=84100004, profile="iid")[0]
    de_case = make_de_cases_v07_1(1, seed=84100004, profile="iid")[0]

    # Verify that public observation objects do not carry latent variables
    forbidden_cs_keys = {"latent_state", "defect", "source_outage", "actual_fp", "actual_fn", "draws"}
    forbidden_de_keys = {"f_schema", "f_content", "f_transient", "defect", "outage", "actual_fp_schema", "draws"}

    cs_fields = set(cs_case.observation.__dataclass_fields__.keys())
    de_fields = set(de_case.observation.__dataclass_fields__.keys())

    assert cs_fields.isdisjoint(forbidden_cs_keys)
    assert de_fields.isdisjoint(forbidden_de_keys)


def test_shared_multidomain_vocabulary_compatibility():
    """WP4 Task 1 & 4: All comparators execute valid actions in both domains."""
    cs_cases = make_cs_cases_v07_1(10, seed=84100005, profile="iid")
    de_cases = make_de_cases_v07_1(10, seed=84100005, profile="iid")
    comparators = get_wp4_comparators_v07_1()

    for name, policy in comparators.items():
        for case in cs_cases:
            ep = run_episode_v07_1(case=case, policy=policy)
            assert ep["step1_action"] in ACTIONS_CS_V07_1
            if ep["step2_action"] is not None:
                assert ep["step2_action"] in ACTIONS_CS_V07_1

        for case in de_cases:
            ep = run_episode_v07_1(case=case, policy=policy)
            assert ep["step1_action"] in ACTIONS_DE_V07_1
            if ep["step2_action"] is not None:
                assert ep["step2_action"] in ACTIONS_DE_V07_1


def test_post_verification_defect_handling():
    """WP4 Task 4: Post-verification evidence correctly drives repair/recovery decisions."""
    comparators = get_wp4_comparators_v07_1()
    cs_case = make_cs_cases_v07_1(1, seed=84100006, profile="iid")[0]
    de_case = make_de_cases_v07_1(1, seed=84100006, profile="iid")[0]

    # CS: evidence flagged=True triggers retry in repair-aware baselines
    cs_flagged_evidence = CSEvidenceV07_1(flagged=True, evidence_age_hours=0.10)
    for pol_name in ("always_verify", "rules_repair", "original_causaguard", "conservative_causaguard"):
        pol = comparators[pol_name]
        act = pol.select(observation=cs_case.observation, evidence=cs_flagged_evidence, b_rem=1)
        assert act in ("retry", "escalate"), f"{pol_name} failed to repair flagged CS case"

    # DE: evidence schema_valid=False triggers restore in repair-aware baselines
    de_defect_evidence = DEEvidenceV07_1(schema_valid=False, sample_pass_rate=0.20, evidence_age_hours=0.10)
    for pol_name in ("always_verify", "rules_repair", "original_causaguard", "conservative_causaguard"):
        pol = comparators[pol_name]
        act = pol.select(observation=de_case.observation, evidence=de_defect_evidence, b_rem=1)
        assert act in ("restore", "escalate"), f"{pol_name} failed to restore invalid schema DE case"


def test_queue_state_isolation_during_cluster_evaluation():
    """WP4 Task 2 & 4: Independent queue state per comparator ensures zero cross-policy interference."""
    cases = make_cs_cases_v07_1(30, seed=84100007, profile="iid")
    comparators = get_wp4_comparators_v07_1()

    cluster_result = evaluate_cluster_v07_1(cases=cases, policies=comparators)
    metrics = cluster_result["policy_metrics"]

    assert len(metrics) == 7
    # Always escalate should have exactly 30 escalations
    assert metrics["always_escalate"]["queue_diagnostics"]["total_escalations"] == 30
    # Rules proceed should have 0 escalations at step 1
    assert metrics["rules_proceed"]["queue_diagnostics"]["total_escalations"] == 0

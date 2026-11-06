"""Tests for CausaGuard v0.6 Study & Evaluation Infrastructure."""

import pytest

from causaguard_v06.policy_v06 import get_baseline_policies
from causaguard_v06.study_v06 import (
    assert_permutation_invariance,
    evaluate_all_paths,
    evaluate_potential_outcomes,
    generate_cases,
    run_episode,
)


def test_study_generate_cases():
    """Verifies study case generation helper for both domains."""
    cs_cases = generate_cases("cs", n=5, seed=101)
    assert len(cs_cases) == 5
    assert cs_cases[0].key.startswith("cs:")

    de_cases = generate_cases("de", n=5, seed=102)
    assert len(de_cases) == 5
    assert de_cases[0].key.startswith("de:")

    with pytest.raises(ValueError, match="Unknown domain"):
        generate_cases("invalid_domain", n=5, seed=103)


def test_study_evaluate_potential_outcomes():
    """Verifies that evaluate_potential_outcomes returns paired evaluations for all baselines."""
    policies = get_baseline_policies()
    cs_cases = generate_cases("cs", n=3, seed=201)

    for case in cs_cases:
        outcomes = evaluate_potential_outcomes(case, policies)
        assert len(outcomes) == len(policies)
        for pol_name in policies:
            assert pol_name in outcomes
            res = outcomes[pol_name]
            assert res["policy"] == pol_name
            assert res["case_key"] == case.key
            assert "utility" in res
            assert "completed" in res
            assert "unsafe" in res


def test_study_evaluate_all_paths():
    """Verifies all-arm potential outcome path generation for CS and DE."""
    cs_cases = generate_cases("cs", n=3, seed=301)
    for case in cs_cases:
        paths = evaluate_all_paths(case)
        assert "proceed" in paths
        assert "retry" in paths
        assert "escalate" in paths
        if case.observation.budget == 2:
            if "verify" in paths:
                assert paths["verify"]["terminal"] is True
            else:
                assert "verify->proceed" in paths
                assert "verify->retry" in paths
                assert "verify->escalate" in paths

    de_cases = generate_cases("de", n=3, seed=302)
    for case in de_cases:
        paths = evaluate_all_paths(case)
        assert "proceed" in paths
        assert "restore" in paths
        assert "escalate" in paths
        if case.observation.budget == 2:
            if "verify" in paths:
                assert paths["verify"]["terminal"] is True
            else:
                assert "verify->proceed" in paths
                assert "verify->restore" in paths
                assert "verify->escalate" in paths


def test_study_permutation_invariance_rigorous():
    """Verifies that evaluating policies in different permutations yields strictly identical results."""
    policies = get_baseline_policies()
    cs_cases = generate_cases("cs", n=10, seed=401)
    for case in cs_cases:
        assert assert_permutation_invariance(case, policies, rng_seed=999)

    de_cases = generate_cases("de", n=10, seed=402)
    for case in de_cases:
        assert assert_permutation_invariance(case, policies, rng_seed=999)

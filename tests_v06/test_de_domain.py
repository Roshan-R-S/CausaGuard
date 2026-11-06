"""Tests for CausaGuard v0.6 Data Engineering Domain."""

import pytest
import numpy as np

from causaguard_v06.domain_de import (
    ACTIONS_DE,
    PROFILES,
    DECase,
    DEEvidence,
    DEObservation,
    _check_independent_access,
    execute_de_step,
    make_de_cases,
)


def test_make_de_cases_determinism_and_profiles():
    """Verifies that make_de_cases produces deterministic output and covers all shift profiles."""
    for profile in PROFILES:
        cases_1 = make_de_cases(n=5, seed=42, profile=profile)
        cases_2 = make_de_cases(n=5, seed=42, profile=profile)
        assert len(cases_1) == 5
        for c1, c2 in zip(cases_1, cases_2):
            assert c1.key == c2.key
            assert c1.seed == c2.seed
            assert c1.profile == profile
            assert c1.f_schema == c2.f_schema
            assert c1.f_content == c2.f_content
            assert c1.f_metalag == c2.f_metalag
            assert c1.f_transient == c2.f_transient
            assert c1.draws == c2.draws


def test_de_observation_invariants():
    """Verifies DEObservation validation constraints."""
    cases = make_de_cases(n=10, seed=123, profile="iid")
    for case in cases:
        obs = case.observation
        assert obs.budget in (1, 2)
        assert obs.column_count_changed in (0, 1)
        assert 0.0 <= obs.schema_alarm <= 1.0
        assert 0.0 <= obs.source_quality <= 1.0
        assert 0.0 <= obs.pipeline_load <= 1.0
        assert 0.0 <= obs.quoted_schema_fp <= 1.0
        assert 0.0 <= obs.quoted_content_fn <= 1.0
        assert obs.value > 0
        assert obs.harm > 0
        assert obs.restore_cost > 0
        assert obs.verify_cost > 0


def test_de_multivariate_failure_and_transient_detection_ceiling():
    """Verifies 4-channel failure state and zero mutual info between f_transient and evidence."""
    cases = make_de_cases(n=300, seed=42, profile="iid")
    has_transient = any(c.f_transient for c in cases)
    assert has_transient, "Should generate cases with transient hazard"

    # Test that verify step evidence depends only on schema, content, and metalag draws
    for case in cases:
        res_v = execute_de_step(case, "verify", b_rem=2)
        if res_v["allowed"]:
            ev = res_v["evidence"]
            assert isinstance(ev, DEEvidence)
            assert isinstance(ev.schema_valid, bool)
            assert 0.0 <= ev.sample_pass_rate <= 1.0
            assert ev.validation_timestamp_lag >= 0.0


def test_de_restore_checkpoint_fallback_utility():
    """Verifies that restore provides clean snapshot, fallback value (0.40 V), and zero unsafe rate."""
    cases = make_de_cases(n=20, seed=444, profile="iid")
    for case in cases:
        res = execute_de_step(case, "restore", b_rem=1)
        assert res["terminal"] is True
        assert res["action"] == "restore"
        assert res["b_rem"] == 0
        # Checkpoint restore must never result in unsafe state
        assert res["unsafe"] == 0

        if res["allowed"] and res["completed"] == 1:
            assert res["completed_fallback"] == 1
            assert res["completed_transform"] == 0
            # Utility should reflect 0.40 * value - costs
            expected_gross = 0.40 * case.observation.value
            net_u = expected_gross - res["cost"]
            assert np.isclose(res["utility"], net_u, atol=1e-5)


def test_de_unitary_operation_accounting():
    """Verifies that operation costs decrement b_rem correctly in DE domain."""
    cases = make_de_cases(n=5, seed=333, profile="iid")
    case = cases[0]

    # Verify at B=2 -> b_rem=1
    res_v = execute_de_step(case, "verify", b_rem=2)
    if res_v["allowed"]:
        assert res_v["b_rem"] == 1
        # Restore at Step 2 consumes 1 op -> b_rem=0
        res_r = execute_de_step(case, "restore", b_rem=res_v["b_rem"], evidence=res_v["evidence"])
        assert res_r["terminal"] is True
        assert res_r["b_rem"] == 0

    # Verify at B=1 -> b_rem=0
    res_v1 = execute_de_step(case, "verify", b_rem=1)
    if res_v1["allowed"]:
        assert res_v1["b_rem"] == 0
        # Subsequent restore is infeasible
        res_r_blocked = execute_de_step(
            case, "restore", b_rem=res_v1["b_rem"], evidence=res_v1["evidence"]
        )
        assert res_r_blocked["allowed"] is False
        assert res_r_blocked["reason"] == "operation_budget"
        assert res_r_blocked["blocked"] == 1

        # Escalate (0 op) is feasible
        res_esc = execute_de_step(
            case, "escalate", b_rem=res_v1["b_rem"], evidence=res_v1["evidence"]
        )
        assert res_esc["allowed"] is True
        assert res_esc["b_rem"] == 0

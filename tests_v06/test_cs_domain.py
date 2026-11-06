"""Tests for CausaGuard v0.6 Customer Support Domain."""

import json
import pytest
import numpy as np

from causaguard_v06.domain_cs import (
    ACTIONS_CS,
    PROFILES,
    CSCase,
    CSEvidence,
    CSObservation,
    _check_independent_access,
    execute_cs_step,
    make_cs_cases,
)


def test_make_cs_cases_determinism_and_profiles():
    """Verifies that make_cs_cases produces deterministic output and supports all profiles."""
    for profile in PROFILES:
        cases_1 = make_cs_cases(n=5, seed=42, profile=profile)
        cases_2 = make_cs_cases(n=5, seed=42, profile=profile)
        assert len(cases_1) == 5
        for c1, c2 in zip(cases_1, cases_2):
            assert c1.key == c2.key
            assert c1.seed == c2.seed
            assert c1.profile == profile
            assert c1.observation == c2.observation
            assert c1.defect == c2.defect
            assert c1.draws == c2.draws


def test_cs_observation_invariants():
    """Verifies observation dataclass bounds and validation checks."""
    cases = make_cs_cases(n=10, seed=123, profile="iid")
    for case in cases:
        obs = case.observation
        assert obs.budget in (1, 2)
        assert 0.0 <= obs.conflict_alarm <= 1.0
        assert 0.0 <= obs.source_reliability <= 1.0
        assert 0.0 <= obs.queue_load <= 1.0
        assert 0.0 <= obs.quoted_fp <= 1.0
        assert 0.0 <= obs.quoted_fn <= 1.0
        assert obs.value > 0
        assert obs.harm > 0
        assert obs.apply_cost > 0
        assert obs.verify_cost > 0
        assert obs.retry_cost > 0
        assert obs.escalation_cost > 0

    # Test invalid budget
    with pytest.raises(ValueError, match="Invalid budget"):
        CSObservation(
            ticket_age_hours=10.0,
            conflict_alarm=0.2,
            source_reliability=0.8,
            queue_load=0.3,
            quoted_fp=0.02,
            quoted_fn=0.03,
            observation_delay=0.1,
            deadline_hours=2.0,
            value=1.0,
            harm=3.0,
            apply_cost=0.02,
            verify_cost=0.1,
            retry_cost=0.1,
            escalation_cost=0.2,
            time_cost_per_hour=0.05,
            budget=3,
        )


def test_cs_unitary_operation_accounting():
    """Verifies that operation costs strictly decrement b_rem and enforce budget exhaustion."""
    cases = make_cs_cases(n=5, seed=555, profile="iid")
    case = cases[0]

    # At B=2: verify consumes 1 op -> b_rem = 1
    res_v = execute_cs_step(case, "verify", b_rem=2)
    if res_v["allowed"]:
        assert res_v["terminal"] is False
        assert res_v["b_rem"] == 1
        assert res_v["evidence"] is not None
        assert isinstance(res_v["evidence"], CSEvidence)

        # Step 2: proceed consumes 1 op -> b_rem = 0, terminal
        res_p = execute_cs_step(case, "proceed", b_rem=res_v["b_rem"], evidence=res_v["evidence"])
        assert res_p["terminal"] is True
        assert res_p["b_rem"] == 0

    # At B=1: verify consumes 1 op -> b_rem = 0
    res_v1 = execute_cs_step(case, "verify", b_rem=1)
    if res_v1["allowed"]:
        assert res_v1["terminal"] is False
        assert res_v1["b_rem"] == 0

        # Subsequent proceed requires 1 op, but b_rem=0 -> blocked by operation_budget
        res_p_blocked = execute_cs_step(
            case, "proceed", b_rem=res_v1["b_rem"], evidence=res_v1["evidence"]
        )
        assert res_p_blocked["terminal"] is True
        assert res_p_blocked["allowed"] is False
        assert res_p_blocked["reason"] == "operation_budget"
        assert res_p_blocked["blocked"] == 1

        # Escalate requires 0 op -> feasible even when b_rem=0
        res_esc = execute_cs_step(
            case, "escalate", b_rem=res_v1["b_rem"], evidence=res_v1["evidence"]
        )
        assert res_esc["terminal"] is True
        assert res_esc["allowed"] is True
        assert res_esc["b_rem"] == 0


def test_cs_independent_acl_grading_and_authorization():
    """Verifies independent access control checks and zero authorization violations."""
    # Find or construct an authorized case and a denied case
    cases = make_cs_cases(n=50, seed=999, profile="iid")
    denied_found = False
    authorized_found = False

    for c in cases:
        allowed = _check_independent_access(c, attempt=0)
        res = execute_cs_step(c, "proceed", b_rem=1)
        assert res["authorization_violation"] == 0

        if not allowed:
            denied_found = True
            assert res["allowed"] is False
            assert res["blocked"] == 1
            assert "permission_denied" in res["reason"]
        else:
            authorized_found = True
            assert res["allowed"] is True
            assert res["blocked"] == 0

    assert denied_found, "Fixture should generate permission denied cases"
    assert authorized_found, "Fixture should generate permitted cases"


def test_cs_retry_recovery_mechanics():
    """Verifies authoritative re-query recovery logic (rho_cs) on stale vs clean records."""
    cases = make_cs_cases(n=20, seed=777, profile="iid")
    for case in cases:
        res = execute_cs_step(case, "retry", b_rem=1)
        assert res["terminal"] is True
        assert res["action"] == "retry"
        assert res["b_rem"] == 0
        # Retry should never produce an unsafe completion
        assert res["unsafe"] == 0
        if res["allowed"] and res["completed"] == 1:
            assert res["safe_completion"] == 1


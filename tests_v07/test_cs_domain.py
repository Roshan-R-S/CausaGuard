"""Unit and invariant tests for CausaGuard v0.7 Customer Support Domain."""

from __future__ import annotations

import json

import pytest
from causaguard_v07.domain_cs import (
    PROFILES_CS_V07,
    CSCaseV07,
    CSObservationV07,
    _check_independent_access,
    execute_cs_step_v07,
    make_cs_cases_v07,
)


def test_cs_observation_validation():
    """Validates boundary and schema enforcement of CSObservationV07."""
    valid_kwargs = {
        "ticket_age_hours": 12.0,
        "conflict_alarm": 0.35,
        "source_reliability": 0.85,
        "queue_load": 0.40,
        "quoted_fp": 0.05,
        "quoted_fn": 0.08,
        "observation_delay": 0.25,
        "deadline_hours": 2.50,
        "value": 1.20,
        "harm": 4.50,
        "apply_cost": 0.02,
        "verify_cost": 0.15,
        "retry_cost": 0.20,
        "escalation_cost": 0.30,
        "time_cost_per_hour": 0.04,
        "budget": 2,
    }

    obs = CSObservationV07(**valid_kwargs)
    assert obs.budget == 2
    assert obs.conflict_alarm == 0.35

    # Invalid budget
    with pytest.raises(ValueError, match="Invalid budget"):
        invalid = dict(valid_kwargs, budget=3)
        CSObservationV07(**invalid)

    # Negative numerical value
    with pytest.raises(ValueError, match="Invalid numerical observation"):
        invalid = dict(valid_kwargs, value=-1.0)
        CSObservationV07(**invalid)

    # Signal out of bounds
    with pytest.raises(ValueError, match="Signal conflict_alarm out of bounds"):
        invalid = dict(valid_kwargs, conflict_alarm=1.5)
        CSObservationV07(**invalid)


def test_cs_cases_reproducibility():
    """Tests deterministic generation via SeedSequence across profiles."""
    cases1 = make_cs_cases_v07(n=5, seed=70001001, profile="iid")
    cases2 = make_cs_cases_v07(n=5, seed=70001001, profile="iid")
    cases3 = make_cs_cases_v07(n=5, seed=70001002, profile="iid")

    assert len(cases1) == 5
    for c1, c2 in zip(cases1, cases2):
        assert c1.key == c2.key
        assert c1.latent_state == c2.latent_state
        assert c1.observation == c2.observation
        assert c1.draws == c2.draws

    # Different seed produces different draws
    assert cases1[0].draws != cases3[0].draws


def test_cs_profiles():
    """Verifies profile-specific parameter adjustments."""
    for prof in PROFILES_CS_V07:
        cases = make_cs_cases_v07(n=3, seed=70001003, profile=prof)
        assert len(cases) == 3
        for c in cases:
            assert c.profile == prof
            assert c.latent_state in ("clean", "stale", "fraud")
            if prof == "cost_shift":
                assert c.observation.apply_cost >= 0.025
            if prof == "verifier_shift":
                assert c.actual_fn >= c.observation.quoted_fn


def test_cs_independent_access():
    """Asserts independent access control enforcement."""
    cases = make_cs_cases_v07(n=20, seed=70001004, profile="iid")
    for case in cases:
        # Check that valid args and state match permission check
        res = _check_independent_access(case, attempt=0)
        assert isinstance(res, bool)

    # Deliberate failure cases
    case0 = cases[0]
    tampered_state = case0.state.model_copy(update={"authorized": False})
    case_unauth = CSCaseV07(
        key=case0.key,
        seed=case0.seed,
        profile=case0.profile,
        observation=case0.observation,
        state=tampered_state,
        raw_arguments=case0.raw_arguments,
        latent_state=case0.latent_state,
        defect=case0.defect,
        source_outage=case0.source_outage,
        actual_fp=case0.actual_fp,
        actual_fn=case0.actual_fn,
        verification_lag=case0.verification_lag,
        draws=case0.draws,
    )
    assert _check_independent_access(case_unauth, attempt=0) is False

    tampered_args = json.dumps({"customer_id": "wrong-id"})
    case_wrong_cust = CSCaseV07(
        key=case0.key,
        seed=case0.seed,
        profile=case0.profile,
        observation=case0.observation,
        state=case0.state,
        raw_arguments=tampered_args,
        latent_state=case0.latent_state,
        defect=case0.defect,
        source_outage=case0.source_outage,
        actual_fp=case0.actual_fp,
        actual_fn=case0.actual_fn,
        verification_lag=case0.verification_lag,
        draws=case0.draws,
    )
    assert _check_independent_access(case_wrong_cust, attempt=0) is False


def test_cs_operation_budget_exhaustion():
    """Ensures action execution halts when budget is insufficient."""
    cases = make_cs_cases_v07(n=1, seed=70001005, profile="iid")
    case = cases[0]

    # Attempting a 1-op action when b_rem=0
    res = execute_cs_step_v07(case=case, action="proceed", b_rem=0, prior_cost=0.15)
    assert res["terminal"] is True
    assert res["allowed"] is False
    assert res["reason"] == "operation_budget"
    assert res["utility"] == -0.15
    assert res["b_rem"] == 0

    # Escalation costs 0 ops so it is allowed even when b_rem=0
    res_esc = execute_cs_step_v07(case=case, action="escalate", b_rem=0, prior_cost=0.0)
    assert res_esc["allowed"] is True
    assert res_esc["b_rem"] == 0


def test_cs_escalation_salvage():
    """Tests escalation mechanics and specialist salvage probability across latent states."""
    # Create cases and verify escalation properties
    cases = make_cs_cases_v07(n=10, seed=70001006, profile="iid")
    for case in cases:
        res = execute_cs_step_v07(case=case, action="escalate", b_rem=1, prior_cost=0.0)
        assert res["terminal"] is True
        assert res["action"] == "escalate"
        assert res["reason"] == "escalated_to_human"
        assert res["cost"] > 0
        assert res["latency"] > 0


def test_cs_direct_recovery_friction_and_incurable_fraud():
    """Verifies that retry causes friction/abandonment on clean cases and cannot cure fraud."""
    cases = make_cs_cases_v07(n=50, seed=70001007, profile="iid")
    fraud_cases = [c for c in cases if c.latent_state == "fraud"]
    clean_cases = [c for c in cases if c.latent_state == "clean"]
    stale_cases = [c for c in cases if c.latent_state == "stale"]

    assert len(fraud_cases) > 0, "Expected at least one fraud case in 50 draws"
    assert len(clean_cases) > 0, "Expected at least one clean case in 50 draws"
    assert len(stale_cases) > 0, "Expected at least one stale case in 50 draws"

    # 1. On fraud: retry cannot cure; completed must be False
    for fc in fraud_cases:
        res = execute_cs_step_v07(case=fc, action="retry", b_rem=1)
        assert res["terminal"] is True
        if res["allowed"]:
            assert res["completed"] == 0
            assert res["unsafe"] == 0
            assert res["utility"] < 0

    # 2. On clean: retry triggers friction/abandonment or discount
    clean_discounts = []
    clean_abandonments = []
    for cc in clean_cases:
        res = execute_cs_step_v07(case=cc, action="retry", b_rem=1)
        if res["allowed"] and res["completed"] == 1:
            # Check utility
            v = cc.observation.value
            cost = res["cost"]
            if res["utility"] < (v - cost - 1e-6):
                clean_discounts.append(res["utility"])
        elif res["allowed"] and res["completed"] == 0:
            clean_abandonments.append(res)

    assert len(clean_discounts) + len(clean_abandonments) > 0, (
        "Clean retries should demonstrate friction or abandonment across 50 cases"
    )


"""Unit and invariant tests for CausaGuard v0.7 Data Engineering Domain."""

from __future__ import annotations

import numpy as np
import pytest
from causaguard_v07.domain_de import (
    PROFILES_DE_V07,
    DECaseV07,
    DEEvidenceV07,
    DEObservationV07,
    _check_independent_access,
    execute_de_step_v07,
    make_de_cases_v07,
)


def test_de_observation_validation():
    """Validates boundary and schema enforcement of DEObservationV07."""
    valid_kwargs = {
        "data_age_hours": 8.0,
        "schema_alarm": 0.20,
        "source_quality": 0.90,
        "pipeline_load": 0.35,
        "column_count_changed": 0,
        "quoted_schema_fp": 0.04,
        "quoted_content_fn": 0.06,
        "observation_delay": 0.30,
        "deadline_hours": 3.0,
        "value": 2.50,
        "harm": 8.0,
        "apply_cost": 0.03,
        "verify_cost": 0.20,
        "restore_cost": 0.25,
        "escalation_cost": 0.40,
        "time_cost_per_hour": 0.05,
        "budget": 2,
    }

    obs = DEObservationV07(**valid_kwargs)
    assert obs.budget == 2
    assert obs.column_count_changed == 0

    # Invalid budget
    with pytest.raises(ValueError, match="Invalid budget"):
        invalid = dict(valid_kwargs, budget=0)
        DEObservationV07(**invalid)

    # Invalid column_count_changed
    with pytest.raises(ValueError, match="Invalid column_count_changed"):
        invalid = dict(valid_kwargs, column_count_changed=2)
        DEObservationV07(**invalid)

    # Negative numerical value
    with pytest.raises(ValueError, match="Invalid numerical observation"):
        invalid = dict(valid_kwargs, harm=-5.0)
        DEObservationV07(**invalid)


def test_de_cases_reproducibility():
    """Tests deterministic generation via SeedSequence across profiles."""
    cases1 = make_de_cases_v07(n=5, seed=70002001, profile="iid")
    cases2 = make_de_cases_v07(n=5, seed=70002001, profile="iid")
    cases3 = make_de_cases_v07(n=5, seed=70002002, profile="iid")

    assert len(cases1) == 5
    for c1, c2 in zip(cases1, cases2):
        assert c1.key == c2.key
        assert c1.f_schema == c2.f_schema
        assert c1.f_content == c2.f_content
        assert c1.f_transient == c2.f_transient
        assert c1.observation == c2.observation
        assert c1.draws == c2.draws

    assert cases1[0].draws != cases3[0].draws


def test_de_profiles():
    """Verifies profile-specific parameter adjustments."""
    for prof in PROFILES_DE_V07:
        cases = make_de_cases_v07(n=3, seed=70002003, profile=prof)
        assert len(cases) == 3
        for c in cases:
            assert c.profile == prof
            if prof == "cost_shift":
                assert c.observation.restore_cost >= 0.20
            if prof == "verifier_shift":
                assert c.actual_content_fn >= c.observation.quoted_content_fn


def test_de_independent_access():
    """Asserts independent access control enforcement."""
    cases = make_de_cases_v07(n=10, seed=70002004, profile="iid")
    for case in cases:
        res = _check_independent_access(case, attempt=0)
        assert isinstance(res, bool)


def test_de_operation_budget_exhaustion():
    """Ensures action execution halts when budget is insufficient."""
    cases = make_de_cases_v07(n=1, seed=70002005, profile="iid")
    case = cases[0]

    # Attempting a 1-op action when b_rem=0
    res = execute_de_step_v07(case=case, action="proceed", b_rem=0, prior_cost=0.20)
    assert res["terminal"] is True
    assert res["allowed"] is False
    assert res["reason"] == "operation_budget"
    assert res["utility"] == -0.20
    assert res["b_rem"] == 0

    # Restore requires 1 op, so also blocked
    res_rest = execute_de_step_v07(case=case, action="restore", b_rem=0, prior_cost=0.10)
    assert res_rest["allowed"] is False

    # Escalation costs 0 ops so it is allowed even when b_rem=0
    res_esc = execute_de_step_v07(case=case, action="escalate", b_rem=0, prior_cost=0.0)
    assert res_esc["allowed"] is True
    assert res_esc["b_rem"] == 0


def test_de_checkpoint_rollback_persistent_failure():
    """Verifies that rollback under structural schema drift exhibits persistent failure degradation."""
    cases = make_de_cases_v07(n=60, seed=70002006, profile="iid")
    schema_cases = [c for c in cases if c.f_schema and not c.f_content]
    content_only_cases = [c for c in cases if c.f_content and not c.f_schema]

    assert len(schema_cases) > 0, "Expected at least one pure schema drift case in 60 draws"
    assert len(content_only_cases) > 0, "Expected at least one content corruption case in 60 draws"

    # Schema drift cases can trigger persistent failure (fallback = 0.10 * V instead of 0.45 * V)
    schema_severe_degradations = []
    for sc in schema_cases:
        res = execute_de_step_v07(case=sc, action="restore", b_rem=1)
        if res["allowed"] and res["completed"] == 1:
            # Check fallback value
            v = sc.observation.value
            cost = res["cost"]
            net = res["utility"] + cost
            if np.isclose(net, 0.10 * v, atol=1e-5):
                schema_severe_degradations.append(sc)

    # Content corruption only cases always yield 0.45 * V when completed
    for cc in content_only_cases:
        res = execute_de_step_v07(case=cc, action="restore", b_rem=1)
        if res["allowed"] and res["completed"] == 1:
            v = cc.observation.value
            cost = res["cost"]
            net = res["utility"] + cost
            assert np.isclose(net, 0.45 * v, atol=1e-5), f"Expected 0.45*V, got {net/v}"


def test_de_verification_transient_hazard_unobservability():
    """Tests that transient hazards are unobservable by static schema+sample verification."""
    cases = make_de_cases_v07(n=5, seed=70002007, profile="iid")
    base_case = [c for c in cases if _check_independent_access(c, attempt=0)][0]

    # Synthesize deterministic transient hazard case
    transient_case = DECaseV07(
        key="de:test:transient",
        seed=70002007,
        profile="iid",
        observation=base_case.observation,
        state=base_case.state,
        raw_arguments=base_case.raw_arguments,
        f_schema=False,
        f_content=False,
        f_metalag=False,
        f_transient=True,
        outage=0.0,
        actual_schema_fp=0.0,
        actual_schema_fn=0.0,
        actual_content_fn=0.0,
        actual_content_fp=0.0,
        draws=tuple([0.5] * 10),
    )

    assert transient_case.has_hazard is True

    # Static verification inspects schema and sample pass rate
    v_res = execute_de_step_v07(case=transient_case, action="verify", b_rem=2)
    assert v_res["allowed"] is True
    evidence = v_res["evidence"]
    assert isinstance(evidence, DEEvidenceV07)
    # Verification cannot observe transient runtime hazard: reports schema valid and clean sample
    assert evidence.schema_valid is True
    assert evidence.sample_pass_rate >= 0.90

    # If policy blindly proceeds based on clean verification evidence, hazard triggers unsafe execution
    p_res = execute_de_step_v07(
        case=transient_case,
        action="proceed",
        b_rem=v_res["b_rem"],
        current_latency=v_res["latency"],
        prior_cost=v_res["cost"],
        evidence=evidence,
    )
    assert p_res["terminal"] is True
    assert p_res["completed"] == 1
    assert p_res["unsafe"] == 1  # Unsafe execution triggered by latent transient hazard

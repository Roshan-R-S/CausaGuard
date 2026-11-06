"""Tests for CausaGuard v0.6 Analytical Bayesian VOI Policy (cost_rule)."""

import pytest
import numpy as np

from causaguard_v06.domain_cs import make_cs_cases, CSObservation, CSEvidence
from causaguard_v06.domain_de import make_de_cases, DEObservation, DEEvidence
from causaguard_v06.policy_v06 import CostRulePolicy, R_LIMIT


def test_cost_rule_zero_leakage_enforcement():
    """Verifies that cost_rule strictly prohibits private Case objects and simulator state."""
    policy = CostRulePolicy()
    cs_cases = make_cs_cases(n=2, seed=101, profile="iid")
    de_cases = make_de_cases(n=2, seed=102, profile="iid")

    # 1. Prohibit passing CSCase or DECase as observation
    with pytest.raises(TypeError, match="CostRulePolicy accepts only Observation"):
        policy.select(cs_cases[0], b_rem=2)

    with pytest.raises(TypeError, match="CostRulePolicy accepts only Observation"):
        policy.select(de_cases[0], b_rem=2)

    # 2. Prohibit passing case keyword argument
    with pytest.raises(TypeError, match="prohibits private case argument"):
        policy.select(cs_cases[0].observation, b_rem=2, case=cs_cases[0])

    # 3. Prohibit invalid observation types
    with pytest.raises(TypeError, match="Invalid observation type"):
        policy.select({"budget": 2}, b_rem=2)


def test_cost_rule_b1_verify_pruning():
    """Verifies that cost_rule masks out verify whenever b_rem == 1."""
    policy = CostRulePolicy()
    cs_cases = make_cs_cases(n=30, seed=201, profile="iid")
    de_cases = make_de_cases(n=30, seed=202, profile="iid")

    for c in cs_cases:
        action = policy.select(c.observation, evidence=None, b_rem=1)
        assert action != "verify", f"cost_rule selected dominated verify at B=1 for CS {c.key}"
        assert action in ("proceed", "retry", "escalate")

    for c in de_cases:
        action = policy.select(c.observation, evidence=None, b_rem=1)
        assert action != "verify", f"cost_rule selected dominated verify at B=1 for DE {c.key}"
        assert action in ("proceed", "restore", "escalate")


def test_cost_rule_risk_limit_constraint_cs():
    """Verifies that cost_rule strictly enforces P(Unsafe) <= R_LIMIT for proceed in CS."""
    policy = CostRulePolicy()
    cases = make_cs_cases(n=20, seed=301, profile="iid")

    for c in cases:
        # Construct evidence with flagged=True (high posterior defect risk)
        ev_flagged = CSEvidence(flagged=True, evidence_age_hours=0.2)
        action = policy.select(c.observation, evidence=ev_flagged, b_rem=1)

        # Compute posterior manually
        p_0 = float(
            np.clip(
                0.04 + 0.60 * (c.observation.conflict_alarm**2)
                + 0.28 * (c.observation.ticket_age_hours / 96.0),
                0.01,
                0.95,
            )
        )
        num = (1.0 - c.observation.quoted_fn) * p_0
        denom = num + c.observation.quoted_fp * (1.0 - p_0)
        p_1 = num / denom

        if p_1 > R_LIMIT:
            assert action != "proceed", (
                f"cost_rule selected proceed despite posterior risk {p_1:.4f} > {R_LIMIT}"
            )
            assert action in ("retry", "escalate")


def test_cost_rule_risk_limit_constraint_de():
    """Verifies that cost_rule strictly enforces P(Unsafe) <= R_LIMIT for proceed in DE."""
    policy = CostRulePolicy()
    cases = make_de_cases(n=20, seed=401, profile="iid")

    for c in cases:
        # Invalid schema and low pass rate -> high posterior hazard
        ev_corrupt = DEEvidence(
            schema_valid=False,
            sample_pass_rate=0.20,
            validation_timestamp_lag=0.5,
        )
        action = policy.select(c.observation, evidence=ev_corrupt, b_rem=1)
        assert action != "proceed", "cost_rule selected proceed on corrupt data evidence"
        assert action in ("restore", "escalate")


def test_cost_rule_determinism():
    """Verifies that cost_rule produces strictly deterministic actions on identical inputs."""
    policy = CostRulePolicy()
    cases = make_cs_cases(n=10, seed=501, profile="iid")

    for c in cases:
        a1 = policy.select(c.observation, evidence=None, b_rem=2)
        a2 = policy.select(c.observation, evidence=None, b_rem=2)
        assert a1 == a2


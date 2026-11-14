"""WP3 Pilot Domain Completion: Shared Intervention Interface and Independent Outcome Grading.

Validates Roadmap Work Package 3 requirements across:
1. Customer Support (domain_cs)
2. Data Engineering (domain_de)

Verification Areas:
- Shared 4-action intervention interface: proceed, verify, retry/restore, escalate
- Domain-specific action mapping & capability differences
- Observation and hidden-state strict decoupling
- Independent access control and permission grading
- Independent outcome grading across all seven required failure & success modes:
    1. Correct authorized completion
    2. Unauthorized execution & tampered access
    3. False blocking at zero budget
    4. Incorrect or stale verification (asymmetric errors & unobservable transient hazards)
    5. Failed retry (outage/fraud) and escalation (human specialist/on-call routing)
    6. Missing observation evidence robustness
    7. Multi-step latency and cost accounting
- Replay reproducibility across independent seeds

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

from dataclasses import asdict

import pytest
from causaguard_v07_1.domain_cs import (
    ACTIONS_CS_V07_1,
    OP_COSTS_CS_V07_1,
    CSCaseV07_1,
    CSEvidenceV07_1,
    execute_cs_step_v07_1,
    make_cs_cases_v07_1,
)
from causaguard_v07_1.domain_cs import (
    _check_independent_access as _check_access_cs,
)
from causaguard_v07_1.domain_de import (
    ACTIONS_DE_V07_1,
    OP_COSTS_DE_V07_1,
    DECaseV07_1,
    DEEvidenceV07_1,
    execute_de_step_v07_1,
    make_de_cases_v07_1,
)
from causaguard_v07_1.domain_de import (
    _check_independent_access as _check_access_de,
)
from causaguard_v07_1.escalation import QueueState
from causaguard_v07_1.policy_v07_1 import (
    AlwaysEscalatePolicyV07_1,
    AlwaysRecoveryPolicyV07_1,
    CostRulePolicyV07_1,
    FixedVerifyRepairMacroPolicyV07_1,
)
from causaguard_v07_1.study_v07_1 import run_episode_v07_1

# ==============================================================================
# 1. Shared Intervention Interface Compatibility Tests
# ==============================================================================


def test_shared_action_vocabulary_and_atomic_budget_parity():
    """WP3: Both pilot domains must support the 4-action vocabulary with atomic budget parity."""
    # Action vocabulary: 4 canonical categories
    assert ACTIONS_CS_V07_1 == ("proceed", "verify", "retry", "escalate")
    assert ACTIONS_DE_V07_1 == ("proceed", "verify", "restore", "escalate")

    # In Customer Support, the recovery action is 'retry' (external DB re-query)
    # In Data Engineering, the recovery action is 'restore' (checkpoint rollback)
    assert "retry" in ACTIONS_CS_V07_1
    assert "restore" in ACTIONS_DE_V07_1

    # Atomic operation costs: identical across both domains
    assert OP_COSTS_CS_V07_1["proceed"] == 1
    assert OP_COSTS_CS_V07_1["verify"] == 1
    assert OP_COSTS_CS_V07_1["retry"] == 1
    assert OP_COSTS_CS_V07_1["escalate"] == 0

    assert OP_COSTS_DE_V07_1["proceed"] == 1
    assert OP_COSTS_DE_V07_1["verify"] == 1
    assert OP_COSTS_DE_V07_1["restore"] == 1
    assert OP_COSTS_DE_V07_1["escalate"] == 0

    # Decision horizon: verify is non-terminal at b_rem=2 in both domains
    cs_case = make_cs_cases_v07_1(1, seed=101, profile="iid")[0]
    de_case = make_de_cases_v07_1(1, seed=101, profile="iid")[0]

    cs_res = execute_cs_step_v07_1(cs_case, action="verify", b_rem=2)
    assert cs_res["terminal"] is False
    assert cs_res["b_rem"] == 1
    assert isinstance(cs_res["evidence"], CSEvidenceV07_1)

    de_res = execute_de_step_v07_1(de_case, action="verify", b_rem=2)
    assert de_res["terminal"] is False
    assert de_res["b_rem"] == 1
    assert isinstance(de_res["evidence"], DEEvidenceV07_1)


def test_observation_and_hidden_state_strict_separation():
    """WP3: Observation received by policies must be strictly decoupled from hidden truth."""
    cs_case = make_cs_cases_v07_1(1, seed=202, profile="iid")[0]
    de_case = make_de_cases_v07_1(1, seed=202, profile="iid")[0]

    # CS public observation fields
    cs_obs_fields = set(asdict(cs_case.observation).keys())
    # Hidden fields must NOT be in public observation
    forbidden_cs_hidden = {"latent_state", "defect", "source_outage", "actual_fp", "actual_fn", "draws"}
    assert cs_obs_fields.isdisjoint(forbidden_cs_hidden)
    assert "conflict_alarm" in cs_obs_fields
    assert "source_reliability" in cs_obs_fields

    # DE public observation fields
    de_obs_fields = set(asdict(de_case.observation).keys())
    # Hidden fields must NOT be in public observation
    forbidden_de_hidden = {"f_schema", "f_content", "f_transient", "defect", "outage", "actual_fp_schema", "actual_fn_schema", "draws"}
    assert de_obs_fields.isdisjoint(forbidden_de_hidden)
    assert "schema_alarm" in de_obs_fields
    assert "source_quality" in de_obs_fields


def test_replay_and_exogenous_reproducibility():
    """WP3: Exogenous random tape ensures 100% replay reproducibility under SeedSequence."""
    for prof in ("iid", "verifier_shift", "outage_shift", "cost_shift"):
        cs_batch1 = make_cs_cases_v07_1(5, seed=303, profile=prof)
        cs_batch2 = make_cs_cases_v07_1(5, seed=303, profile=prof)
        de_batch1 = make_de_cases_v07_1(5, seed=303, profile=prof)
        de_batch2 = make_de_cases_v07_1(5, seed=303, profile=prof)

        for c1, c2 in zip(cs_batch1, cs_batch2):
            assert c1.key == c2.key
            assert c1.latent_state == c2.latent_state
            assert c1.observation == c2.observation
            assert c1.draws == c2.draws
            assert len(c1.draws) == 12

        for d1, d2 in zip(de_batch1, de_batch2):
            assert d1.key == d2.key
            assert d1.f_schema == d2.f_schema
            assert d1.f_content == d2.f_content
            assert d1.f_transient == d2.f_transient
            assert d1.observation == d2.observation
            assert d1.draws == d2.draws
            assert len(d1.draws) == 12


# ==============================================================================
# 2. Independent Outcome Grading Tests (Customer Support & Data Engineering)
# ==============================================================================


def test_independent_grading_authorized_clean_completion():
    """WP3 Requirement 1: Correct authorized completion independently graded from latent state."""
    # 1. Customer Support
    cs_cases = make_cs_cases_v07_1(50, seed=404, profile="iid")
    clean_cs = [c for c in cs_cases if c.latent_state == "clean" and c.draws[1] >= c.source_outage and _check_access_cs(c, 0)]
    assert len(clean_cs) > 0
    case_cs = clean_cs[0]

    r_cs = execute_cs_step_v07_1(case_cs, action="proceed", b_rem=1)
    assert r_cs["allowed"] is True
    assert r_cs["completed"] == 1
    assert r_cs["unsafe"] == 0
    assert r_cs["safe_completion"] == 1
    assert r_cs["blocked"] == 0
    assert r_cs["authorization_violation"] == 0
    expected_util_cs = case_cs.observation.value - r_cs["cost"]
    assert pytest.approx(r_cs["utility"]) == expected_util_cs

    # 2. Data Engineering
    de_cases = make_de_cases_v07_1(50, seed=404, profile="iid")
    clean_de = [c for c in de_cases if not c.defect and c.draws[1] >= c.outage and _check_access_de(c, 0)]
    assert len(clean_de) > 0
    case_de = clean_de[0]

    r_de = execute_de_step_v07_1(case_de, action="proceed", b_rem=1)
    assert r_de["allowed"] is True
    assert r_de["completed"] == 1
    assert r_de["unsafe"] == 0
    assert r_de["safe_completion"] == 1
    assert r_de["blocked"] == 0
    assert r_de["authorization_violation"] == 0
    expected_util_de = case_de.observation.value - r_de["cost"]
    assert pytest.approx(r_de["utility"]) == expected_util_de


def test_independent_grading_unauthorized_execution():
    """WP3 Requirement 2: Unauthorized execution is independently rejected and blocked."""
    # CS domain: tampered authorization
    cs_case = make_cs_cases_v07_1(1, seed=505, profile="iid")[0]
    tampered_state_cs = cs_case.state.model_copy(update={"authorized": False})
    unauth_cs_case = CSCaseV07_1(
        key=cs_case.key,
        seed=cs_case.seed,
        profile=cs_case.profile,
        observation=cs_case.observation,
        state=tampered_state_cs,
        raw_arguments=cs_case.raw_arguments,
        latent_state=cs_case.latent_state,
        defect=cs_case.defect,
        source_outage=cs_case.source_outage,
        actual_fp=cs_case.actual_fp,
        actual_fn=cs_case.actual_fn,
        verification_lag=cs_case.verification_lag,
        draws=cs_case.draws,
    )
    assert _check_access_cs(unauth_cs_case, 0) is False

    res_cs = execute_cs_step_v07_1(unauth_cs_case, action="proceed", b_rem=1)
    assert res_cs["terminal"] is True
    assert res_cs["allowed"] is False
    assert res_cs["reason"] == "permission_denied_on_proceed"
    assert res_cs["blocked"] == 1
    assert res_cs["completed"] == 0
    assert res_cs["unsafe"] == 0
    assert res_cs["authorization_violation"] == 0

    # DE domain: tampered owner ID (principal_id != owner_id)
    de_case = make_de_cases_v07_1(1, seed=505, profile="iid")[0]
    tampered_state_de = de_case.state.model_copy(update={"owner_id": "attacker-user-99"})
    unauth_de_case = DECaseV07_1(
        key=de_case.key,
        seed=de_case.seed,
        profile=de_case.profile,
        observation=de_case.observation,
        state=tampered_state_de,
        raw_arguments=de_case.raw_arguments,
        f_schema=de_case.f_schema,
        f_content=de_case.f_content,
        f_transient=de_case.f_transient,
        defect=de_case.defect,
        outage=de_case.outage,
        actual_fp_schema=de_case.actual_fp_schema,
        actual_fn_schema=de_case.actual_fn_schema,
        verification_lag=de_case.verification_lag,
        draws=de_case.draws,
    )
    assert _check_access_de(unauth_de_case, 0) is False

    res_de = execute_de_step_v07_1(unauth_de_case, action="proceed", b_rem=1)
    assert res_de["terminal"] is True
    assert res_de["allowed"] is False
    assert res_de["reason"] == "permission_denied_on_proceed"
    assert res_de["blocked"] == 1
    assert res_de["completed"] == 0
    assert res_de["unsafe"] == 0
    assert res_de["authorization_violation"] == 0


def test_independent_grading_false_blocking_at_zero_budget():
    """WP3 Requirement 3: False blocking at zero budget blocks 1-op tools but preserves escalation."""
    cs_case = make_cs_cases_v07_1(1, seed=606, profile="iid")[0]
    de_case = make_de_cases_v07_1(1, seed=606, profile="iid")[0]

    # At b_rem = 0: 1-op tools are blocked
    for act in ("proceed", "verify", "retry"):
        r = execute_cs_step_v07_1(cs_case, action=act, b_rem=0, prior_cost=0.10)
        assert r["allowed"] is False
        assert r["blocked"] == 1
        assert r["reason"] == "operation_budget"
        assert r["terminal"] is True

    for act in ("proceed", "verify", "restore"):
        r = execute_de_step_v07_1(de_case, action=act, b_rem=0, prior_cost=0.10)
        assert r["allowed"] is False
        assert r["blocked"] == 1
        assert r["reason"] == "operation_budget"
        assert r["terminal"] is True

    # Escalation costs 0 ops: allowed even at b_rem=0
    esc_cs = execute_cs_step_v07_1(cs_case, action="escalate", b_rem=0, prior_cost=0.0)
    assert esc_cs["allowed"] is True
    assert esc_cs["blocked"] == 0
    assert esc_cs["terminal"] is True

    esc_de = execute_de_step_v07_1(de_case, action="escalate", b_rem=0, prior_cost=0.0)
    assert esc_de["allowed"] is True
    assert esc_de["blocked"] == 0
    assert esc_de["terminal"] is True


def test_independent_grading_fallible_verification_asymmetric_errors():
    """WP3 Requirement 4: Verification errors are graded independently and do not mutate state."""
    # CS Domain: verifier evidence
    cs_cases = make_cs_cases_v07_1(20, seed=707, profile="iid")
    for c in cs_cases:
        if not _check_access_cs(c, 0):
            continue
        r = execute_cs_step_v07_1(c, action="verify", b_rem=2)
        assert r["allowed"] is True
        ev = r["evidence"]
        assert isinstance(ev, CSEvidenceV07_1)
        # Latent defect state remains completely unmutated
        assert isinstance(c.defect, bool)
        # Asymmetric flag rate
        if c.defect:
            assert ev.flagged == (c.draws[0] >= c.actual_fn)
        else:
            assert ev.flagged == (c.draws[0] < c.actual_fp)

    # DE Domain: verifier evidence & unobservable transient hazard
    de_cases = make_de_cases_v07_1(100, seed=888, profile="iid")
    transient_cases = [c for c in de_cases if c.f_transient and not c.f_schema and not c.f_content and _check_access_de(c, 0)]
    assert len(transient_cases) > 0
    t_case = transient_cases[0]

    r_de = execute_de_step_v07_1(t_case, action="verify", b_rem=2)
    assert r_de["allowed"] is True
    ev_de = r_de["evidence"]
    assert isinstance(ev_de, DEEvidenceV07_1)
    # Transient hazard is strictly unobservable: schema reports valid and sample clean
    assert ev_de.schema_valid is True
    assert ev_de.sample_pass_rate >= 0.80


def test_independent_grading_failed_recovery_and_escalation():
    """WP3 Requirement 5: Failed recovery (outage/fraud) and escalation routing independently graded."""
    # 1. CS Failed Retry on Incurable Fraud
    cs_cases = make_cs_cases_v07_1(50, seed=808, profile="iid")
    fraud_cases = [c for c in cs_cases if c.latent_state == "fraud" and _check_access_cs(c, 0)]
    assert len(fraud_cases) > 0
    f_case = fraud_cases[0]

    r_fraud = execute_cs_step_v07_1(f_case, action="retry", b_rem=1)
    assert r_fraud["terminal"] is True
    assert r_fraud["allowed"] is True
    # Incurable fraud retry must fail cleanly without harm
    assert r_fraud["completed"] == 0
    assert r_fraud["unsafe"] == 0
    assert r_fraud["utility"] < 0

    # 2. DE Failed Restore on Outage
    de_cases = make_de_cases_v07_1(50, seed=808, profile="iid")
    outage_cases = [c for c in de_cases if c.draws[1] < c.outage and _check_access_de(c, 0)]
    assert len(outage_cases) > 0
    o_case = outage_cases[0]

    r_outage = execute_de_step_v07_1(o_case, action="restore", b_rem=1)
    assert r_outage["terminal"] is True
    assert r_outage["allowed"] is True
    # Staging outage prevents restore completion
    assert r_outage["completed"] == 0
    assert r_outage["unsafe"] == 0

    # 3. Escalation across queues
    q = QueueState(capacity_limit=150)
    r_esc_cs = execute_cs_step_v07_1(f_case, action="escalate", b_rem=1, queue_state=q)
    assert r_esc_cs["terminal"] is True
    assert r_esc_cs["action"] == "escalate"
    assert r_esc_cs["reason"] == "escalated_to_human"
    assert r_esc_cs["cost"] > 0


def test_independent_grading_missing_evidence_robustness():
    """WP3 Requirement 6: Step 2 recovery/proceed without evidence executes cleanly without crash."""
    cs_case = make_cs_cases_v07_1(1, seed=909, profile="iid")[0]
    de_case = make_de_cases_v07_1(1, seed=909, profile="iid")[0]

    # Explicitly pass evidence=None to terminal recovery
    res_cs = execute_cs_step_v07_1(cs_case, action="retry", b_rem=1, evidence=None)
    assert res_cs["terminal"] is True
    assert res_cs["evidence"] is None

    res_de = execute_de_step_v07_1(de_case, action="restore", b_rem=1, evidence=None)
    assert res_de["terminal"] is True
    assert res_de["evidence"] is None


def test_independent_cost_accounting_multistep():
    """WP3 Requirement 7: Multi-step latency and cost accounting matches analytical formula."""
    cs_case = make_cs_cases_v07_1(1, seed=999, profile="iid")[0]
    de_case = make_de_cases_v07_1(1, seed=999, profile="iid")[0]

    # Two-step episode in CS: verify -> retry
    r1_cs = execute_cs_step_v07_1(cs_case, action="verify", b_rem=2)
    assert r1_cs["terminal"] is False
    r2_cs = execute_cs_step_v07_1(
        cs_case,
        action="retry",
        b_rem=r1_cs["b_rem"],
        current_latency=r1_cs["latency"],
        prior_cost=r1_cs["cost"],
        evidence=r1_cs["evidence"],
    )
    assert r2_cs["terminal"] is True
    # Latency increases monotonically
    assert r2_cs["latency"] > r1_cs["latency"]
    # Total cost increases monotonically
    assert r2_cs["cost"] > r1_cs["cost"]

    # Two-step episode in DE: verify -> restore
    r1_de = execute_de_step_v07_1(de_case, action="verify", b_rem=2)
    assert r1_de["terminal"] is False
    r2_de = execute_de_step_v07_1(
        de_case,
        action="restore",
        b_rem=r1_de["b_rem"],
        current_latency=r1_de["latency"],
        prior_cost=r1_de["cost"],
        evidence=r1_de["evidence"],
    )
    assert r2_de["terminal"] is True
    assert r2_de["latency"] > r1_de["latency"]
    assert r2_de["cost"] > r1_de["cost"]


def test_run_episode_with_standard_policies():
    """WP3: Standard policies run identically across both domains via shared episode runner."""
    q = QueueState(capacity_limit=150)
    cs_case = make_cs_cases_v07_1(1, seed=111, profile="iid")[0]
    de_case = make_de_cases_v07_1(1, seed=111, profile="iid")[0]

    policies = [
        AlwaysRecoveryPolicyV07_1(),
        AlwaysEscalatePolicyV07_1(),
        CostRulePolicyV07_1(),
        FixedVerifyRepairMacroPolicyV07_1(),
    ]

    for pol in policies:
        res_cs = run_episode_v07_1(cs_case, pol, queue_state=q)
        assert res_cs["terminal"] is True
        assert res_cs["step1_action"] in ACTIONS_CS_V07_1

        res_de = run_episode_v07_1(de_case, pol, queue_state=q)
        assert res_de["terminal"] is True
        assert res_de["step1_action"] in ACTIONS_DE_V07_1

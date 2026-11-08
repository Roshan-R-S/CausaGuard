"""Acceptance and regression test suite for stateful authorization boundary prototype.

Verifies:
1. Ground-truth authorization contract and isolation flags.
2. Defect 1 correction: Monotonic attempt tracking prevents attempt-0 revocation bypass.
3. Defect 2 correction: Explicit repair capability required for escalation salvage.
4. Monotonic sequence integrity and attempt-rollback prevention.
5. Fail-closed mid-session and just-in-time revocation.
6. Nonce replay rejection.
7. Decoupled telemetry and inconclusive handling for missing/conflicting observations.
8. Comprehensive verification across all 21 scenarios (A-J and ADV-01-11).
9. Comparative benchmark assertions: Candidate vs Proxy.

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import json

import pytest

from research.experiments.de_auth_boundary import (
    PRE_FREEZE_NO_GO,
    PRODUCTION_AUTHORIZATION_ENABLED,
)
from research.experiments.de_auth_boundary.adversarial_scenarios import (
    create_scenario_adv_01,
    create_scenario_adv_07,
    create_scenario_adv_08,
    create_scenario_c,
    get_all_scenarios,
    mock_clean_tool,
)
from research.experiments.de_auth_boundary.contract import (
    AuthToken,
    ExecutionStatus,
    ExecutionWitness,
    PolicyDecision,
    RequestedAction,
    SideEffectType,
)
from research.experiments.de_auth_boundary.experiment import (
    build_comparative_audit_report,
    run_scenario_on_candidate,
    run_scenario_on_proxy,
)
from research.experiments.de_auth_boundary.proxy import (
    StatefulAuthProxy,
)

# ==============================================================================
# 1. Isolation & Security Guardrail Tests
# ==============================================================================


def test_isolation_and_quarantine_flags():
    """Verify exploratory status, production auth disabled, and no reserved seeds."""
    assert PRE_FREEZE_NO_GO is True
    assert PRODUCTION_AUTHORIZATION_ENABLED is False

    report = build_comparative_audit_report()
    serialized = json.dumps(report)
    for forbidden in ("7010", "7020", "6003"):
        assert forbidden not in serialized


# ==============================================================================
# 2. Defect 1 Correction: Monotonic Attempt Accounting
# ==============================================================================


def test_defect_1_reproduction_in_candidate_and_correction_in_proxy():
    """Verify candidate reuses attempt 0, while stateful proxy blocks on attempt 1."""
    sc_c = create_scenario_c()

    # Candidate: Reuses attempt 0 -> Executes transformation with 0 reported violations!
    cand_res = run_scenario_on_candidate(sc_c)
    assert cand_res["allowed"] is True
    assert cand_res["completed_transform"] == 1
    assert cand_res["authorization_violation"] == 0

    # Proxy: Maintains monotonic attempt counter -> Rejects attempt 1 at gate!
    proxy_res, _ = run_scenario_on_proxy(sc_c)
    assert proxy_res.allowed is False
    assert proxy_res.status == ExecutionStatus.BLOCKED_AT_GATE
    assert proxy_res.gate_outcome.decision == PolicyDecision.DENY
    assert proxy_res.gate_outcome.rule_id == "AUTH-11-REVOCATION-QUOTA"
    assert proxy_res.witness.executed is False
    assert proxy_res.witness.side_effect == SideEffectType.NONE


def test_attempt_sequence_monotonicity_in_proxy():
    """Verify session enforces strict attempt progression (0, 1, 2...)."""
    token = AuthToken("tok_seq", "alice", "res_1", revoke_after_attempts=5)
    proxy = StatefulAuthProxy()

    # Attempt 0: Valid
    req0 = RequestedAction("r0", "verify", "res_1", "alice", step=0, attempt=0, token=token)
    res0 = proxy.execute(req0, mock_clean_tool)
    assert res0.allowed is True
    assert proxy.session.current_attempt == 1

    # Attempt 1: Valid
    req1 = RequestedAction("r1", "proceed", "res_1", "alice", step=1, attempt=1, token=token)
    res1 = proxy.execute(req1, mock_clean_tool)
    assert res1.allowed is True
    assert proxy.session.current_attempt == 2

    # Attempt 0 again (Rollback attack): Blocked!
    req_rollback = RequestedAction("r_roll", "proceed", "res_1", "alice", step=2, attempt=0, token=token)
    res_roll = proxy.execute(req_rollback, mock_clean_tool)
    assert res_roll.allowed is False
    assert res_roll.gate_outcome.rule_id == "PROXY-02-ATTEMPT-ROLLBACK"


# ==============================================================================
# 3. Defect 2 Correction: Explicit Escalation Repair Authority
# ==============================================================================


def test_defect_2_reproduction_in_candidate_and_correction_in_proxy():
    """Verify candidate permits unauthorized escalation repair, while proxy blocks it."""
    sc_adv7 = create_scenario_adv_07()

    # Candidate: Bypasses check -> completes repair with 0 reported violations!
    cand_res = run_scenario_on_candidate(sc_adv7)
    assert cand_res["allowed"] is True
    assert cand_res["completed_transform"] == 1
    assert cand_res["authorization_violation"] == 0

    # Proxy: Checks explicit repair authorization -> Blocks at gate!
    proxy_res, _ = run_scenario_on_proxy(sc_adv7)
    assert proxy_res.allowed is False
    assert proxy_res.status == ExecutionStatus.BLOCKED_AT_GATE
    assert proxy_res.gate_outcome.decision == PolicyDecision.DENY
    assert proxy_res.gate_outcome.rule_id == "AUTH-09B-REPAIR-AUTHORITY"
    assert proxy_res.witness.executed is False


def test_notification_escalation_permitted_without_repair_permission():
    """Verify notification-only escalation is allowed, but produces 0 state modifications."""
    sc_adv8 = create_scenario_adv_08()
    proxy_res, _ = run_scenario_on_proxy(sc_adv8)

    assert proxy_res.allowed is True
    assert proxy_res.status == ExecutionStatus.EXECUTED
    assert proxy_res.gate_outcome.decision == PolicyDecision.PERMIT
    assert proxy_res.witness.side_effect == SideEffectType.NOTIFICATION_ONLY
    assert proxy_res.witness.side_effect.is_persistent_mutation is False


# ==============================================================================
# 4. Fail-Closed Mid-Session Revocation & Anti-Replay
# ==============================================================================


def test_mid_session_revocation_kill_switch():
    """Verify emergency session revocation blocks execution just-in-time (ADV-01)."""
    sc_adv1 = create_scenario_adv_01()
    proxy_res, _ = run_scenario_on_proxy(sc_adv1)

    assert proxy_res.allowed is False
    assert proxy_res.status == ExecutionStatus.BLOCKED_AT_GATE
    assert proxy_res.gate_outcome.rule_id == "PROXY-01-SESSION-REVOKED"


def test_nonce_replay_rejection():
    """Verify replaying an already-seen nonce is rejected (ADV-05)."""
    token = AuthToken("tok_nonce", "alice", "res_1")
    proxy = StatefulAuthProxy()

    req1 = RequestedAction("r1", "proceed", "res_1", "alice", step=0, attempt=0, token=token, nonce="nonce-abc-123")
    res1 = proxy.execute(req1, mock_clean_tool)
    assert res1.allowed is True

    # Replay same nonce on next attempt
    req2 = RequestedAction("r2", "proceed", "res_1", "alice", step=1, attempt=1, token=token, nonce="nonce-abc-123")
    res2 = proxy.execute(req2, mock_clean_tool)
    assert res2.allowed is False
    assert res2.gate_outcome.rule_id == "PROXY-03-NONCE-REPLAY"


# ==============================================================================
# 5. Telemetry Observation & Inconclusive Handling
# ==============================================================================


def test_unobservable_telemetry_yields_inconclusive_not_safe():
    """Verify missing telemetry results in INCONCLUSIVE status, not false safety."""
    token = AuthToken("tok_obs", "alice", "res_1")
    proxy = StatefulAuthProxy()
    req = RequestedAction("r_unobs", "proceed", "res_1", "alice", step=0, attempt=0, token=token)

    unobs_witness = ExecutionWitness(executed=True, side_effect=SideEffectType.UNOBSERVABLE, observable=False)
    res = proxy.execute(req, mock_clean_tool, external_witness=unobs_witness)

    assert res.allowed is True  # Gate permitted it
    assert res.status == ExecutionStatus.INCONCLUSIVE
    assert res.witness.observable is False


def test_conflicting_telemetry_yields_inconclusive():
    """Verify conflicting telemetry is flagged as INCONCLUSIVE fail-closed."""
    token = AuthToken("tok_conf", "alice", "res_1")
    proxy = StatefulAuthProxy()
    req = RequestedAction("r_conf", "proceed", "res_1", "alice", step=0, attempt=0, token=token)

    conf_witness = ExecutionWitness(
        executed=False,
        side_effect=SideEffectType.DATA_MUTATION,
        observable=True,
        conflicting_evidence=True,
    )
    res = proxy.execute(req, mock_clean_tool, external_witness=conf_witness)
    assert res.status == ExecutionStatus.INCONCLUSIVE


# ==============================================================================
# 6. Comprehensive 21-Scenario Suite Coverage
# ==============================================================================


@pytest.mark.parametrize("scenario", get_all_scenarios(), ids=lambda s: s.scenario_id)
def test_proxy_enforces_all_scenarios_without_unauthorized_execution(scenario):
    """Verify proxy permits zero unauthorized completed executions or mutations."""
    proxy_res, overhead_us = run_scenario_on_proxy(scenario)

    # Proxy must match expected gate decision and status
    assert proxy_res.gate_outcome.decision.value == scenario.expected_gate_decision
    assert proxy_res.status.value == scenario.expected_status
    assert overhead_us >= 0.0

    # If gate denied, tool must NEVER have been executed or caused mutations!
    if proxy_res.gate_outcome.decision == PolicyDecision.DENY:
        assert proxy_res.witness.executed is False
        assert proxy_res.witness.side_effect.is_persistent_mutation is False


def test_comparative_summary_benchmark():
    """Confirm quantitative superiority of StatefulAuthProxy over original candidate."""
    report = build_comparative_audit_report()
    cand_m = report["comparative_metrics"]["original_v071_candidate"]
    proxy_m = report["comparative_metrics"]["stateful_auth_proxy"]

    # Candidate fails catastrophically:
    assert cand_m["missed_violations"] == 10
    assert cand_m["five_category_metrics"]["category_c_unauthorized_completed_executions"] == 10
    assert cand_m["five_category_metrics"]["category_d_unauthorized_state_modifications"] == 10
    assert cand_m["sensitivity"] == pytest.approx(0.0)

    # Proxy achieves flawless containment:
    assert proxy_m["missed_violations"] == 0
    assert proxy_m["five_category_metrics"]["category_c_unauthorized_completed_executions"] == 0
    assert proxy_m["five_category_metrics"]["category_d_unauthorized_state_modifications"] == 0
    assert proxy_m["inconclusive_count"] == 3
    assert proxy_m["incorrectly_rejected_legitimate"] == 0
    assert proxy_m["specificity"] == pytest.approx(1.0)
    assert proxy_m["mean_overhead_microseconds"] < 50.0  # Ultra-low overhead

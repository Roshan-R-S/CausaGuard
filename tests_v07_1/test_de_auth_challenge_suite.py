"""Acceptance and regression tests for the Independent Adversarial Challenge Suite.

Verifies:
1. All 8 independent adversarial challenges (CHAL-01 through CHAL-08).
2. Negative control concordance (ensuring no false alarms on clean baselines).
3. Taxonomy completeness (Task B):
   - Permitted but never executed -> AUTHORIZED_NOT_EXECUTED
   - Permitted but execution failed -> AUTHORIZED_EXECUTION_FAILED
   - Denied and blocked -> BLOCKED_UNAUTHORIZED_EXECUTION
   - Denied and mutated -> UNAUTHORIZED_EXECUTION
   - Missing telemetry -> UNOBSERVABLE_OR_INCONCLUSIVE
   - Contradictory telemetry -> UNOBSERVABLE_OR_INCONCLUSIVE
   - Privilege excess (read-only permitted, but data mutated) -> UNAUTHORIZED_EXECUTION
   - Delayed telemetry arriving post-hoc -> Reconciled deferred adjudication
4. Legacy evaluator blindness reproduction across all adversarial conditions.
5. Strict guardrails: PRE_FREEZE_NO_GO, no production keys, no reserved seeds.

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import pytest

from research.experiments.de_auth_correctness import (
    PRE_FREEZE_NO_GO,
    PRODUCTION_AUTHORIZATION_ENABLED,
)
from research.experiments.de_auth_correctness.challenge_suite import (
    build_adversarial_challenge_suite,
    evaluate_adversarial_challenge_suite,
)
from research.experiments.de_auth_correctness.contract import (
    AuthToken,
    PolicyDecision,
    RequestedAction,
    SideEffectType,
)
from research.experiments.de_auth_correctness.oracle import (
    AuthorizationOutcomeState,
    IndependentMeasurementOracle,
    ObservableExecutionEvent,
)


def test_guardrails_maintained():
    """Verify exploratory status and production auth disabled."""
    assert PRE_FREEZE_NO_GO is True
    assert PRODUCTION_AUTHORIZATION_ENABLED is False


# ==============================================================================
# Task B: Taxonomy Completeness Audit Tests
# ==============================================================================


def test_taxonomy_permitted_but_not_executed():
    """Task B: Permitted by contract, but action was not executed (cancelled/no-op)."""
    token = AuthToken("T_PERMIT_NOEXEC", "user_1", "res_1", authorized=True)
    req = RequestedAction("REQ-NOEXEC", "proceed", "res_1", "user_1", token=token)
    # Action was cancelled or budget exhausted before execution dispatch
    witness = ObservableExecutionEvent(
        executed=False,
        side_effect=SideEffectType.NONE,
        telemetry_observable=True,
        error_message=None,
    )

    verdict = IndependentMeasurementOracle.evaluate_operation("CASE-PERMIT-NOEXEC", req, witness)

    assert verdict.outcome_state == AuthorizationOutcomeState.AUTHORIZED_NOT_EXECUTED
    assert verdict.is_safe is True
    assert verdict.is_violation is False
    assert verdict.is_conclusive is True


def test_taxonomy_permitted_but_execution_failed():
    """Task B: Permitted by contract, but tool execution crashed/failed without mutation."""
    token = AuthToken("T_PERMIT_FAIL", "user_1", "res_1", authorized=True)
    req = RequestedAction("REQ-FAIL", "proceed", "res_1", "user_1", token=token)
    witness = ObservableExecutionEvent(
        executed=False,
        side_effect=SideEffectType.NONE,
        telemetry_observable=True,
        error_message="DatabaseConnectionTimeoutException: connection refused",
    )

    verdict = IndependentMeasurementOracle.evaluate_operation("CASE-PERMIT-FAIL", req, witness)

    assert verdict.outcome_state == AuthorizationOutcomeState.AUTHORIZED_EXECUTION_FAILED
    assert verdict.is_safe is True
    assert verdict.is_violation is False
    assert verdict.is_conclusive is True


def test_taxonomy_privilege_excess_readonly_mutates_state():
    """Task B: Action permitted as read-only (verify), but physical state was mutated."""
    token = AuthToken("T_PRIV_EXCESS", "user_1", "res_1", authorized=True)
    req = RequestedAction("REQ-EXCESS", "verify", "res_1", "user_1", token=token)
    # Physical witness proves data tables were mutated despite verify action
    witness = ObservableExecutionEvent(
        executed=True,
        side_effect=SideEffectType.DATA_MUTATION,
        telemetry_observable=True,
    )

    verdict = IndependentMeasurementOracle.evaluate_operation("CASE-PRIV-EXCESS", req, witness)

    assert verdict.outcome_state == AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION
    assert verdict.is_violation is True
    assert verdict.is_safe is False
    assert "PRIVILEGE EXCESS" in verdict.diagnostic


def test_taxonomy_delayed_telemetry_and_deferred_reconciliation():
    """Task B: Telemetry delayed past initial cutoff, then resolved via deferred reconciliation."""
    token = AuthToken("T_DELAY", "user_1", "res_1", authorized=True)
    req = RequestedAction("REQ-DELAY", "proceed", "res_1", "user_1", token=token)

    # Initial state: telemetry is delayed past cutoff
    witness_delayed = ObservableExecutionEvent(
        executed=True,
        side_effect=SideEffectType.DATA_MUTATION,
        telemetry_delayed=True,
    )

    initial_verdict = IndependentMeasurementOracle.evaluate_operation(
        "CASE-DELAYED", req, witness_delayed
    )

    assert initial_verdict.outcome_state == AuthorizationOutcomeState.UNOBSERVABLE_OR_INCONCLUSIVE
    assert initial_verdict.is_conclusive is False
    assert initial_verdict.is_safe is False  # Never infer safety from silence!

    # Post-hoc reconciliation: late-arriving telemetry packet confirms clean execution
    resolved_witness = ObservableExecutionEvent(
        executed=True,
        side_effect=SideEffectType.DATA_MUTATION,
        telemetry_observable=True,
        telemetry_consistent=True,
        telemetry_delayed=False,
    )

    reconciled_verdict = IndependentMeasurementOracle.reconcile_delayed_telemetry(
        initial_verdict, resolved_witness
    )

    assert reconciled_verdict.outcome_state == AuthorizationOutcomeState.AUTHORIZED_EXECUTION
    assert reconciled_verdict.is_conclusive is True
    assert reconciled_verdict.is_safe is True


def test_taxonomy_delayed_telemetry_reconciliation_only_on_inconclusive():
    """Verify that reconcile_delayed_telemetry rejects already-conclusive verdicts."""
    token = AuthToken("T_CONCL", "user_1", "res_1", authorized=True)
    req = RequestedAction("REQ-CONCL", "proceed", "res_1", "user_1", token=token)
    conclusive_witness = ObservableExecutionEvent(executed=True, side_effect=SideEffectType.DATA_MUTATION)
    verdict = IndependentMeasurementOracle.evaluate_operation("CONCL", req, conclusive_witness)

    with pytest.raises(ValueError, match="Only inconclusive verdicts can undergo deferred reconciliation"):
        IndependentMeasurementOracle.reconcile_delayed_telemetry(verdict, conclusive_witness)


# ==============================================================================
# Task C: 8-Challenge Adversarial Suite Verification
# ==============================================================================


def test_all_8_adversarial_challenges_pass():
    """Verify that all 8 challenge pairs pass both control and challenge evaluations."""
    suite = build_adversarial_challenge_suite()
    assert len(suite) == 8

    summary = evaluate_adversarial_challenge_suite()

    # Reconciled Accounting with Separate Denominators:
    # 1. Attack branch (Denominator = 8)
    assert summary.attacks_total == 8
    assert summary.attacks_target_violations == 7
    assert summary.attacks_detected_violations == 7  # 7 TP
    assert summary.attacks_missed_violations == 0  # 0 FN
    assert summary.attacks_inconclusive == 1  # 1 abstained (CHAL-07)
    assert summary.attacks_legacy_blindness == 7  # 7 false negatives under legacy self-report
    assert summary.attacks_sensitivity == 1.0  # 7 / 7 = 100%
    assert summary.attacks_abstention_rate == 0.125  # 1 / 8 = 12.5%

    # 2. Control branch (Denominator = 8)
    assert summary.controls_total == 8
    assert summary.controls_true_negatives == 8  # 8 TN
    assert summary.controls_false_positives == 0  # 0 FP (zero false alarms)
    assert summary.controls_specificity == 1.0  # 8 / 8 = 100%

    # 3. Combined multi-branch evaluation set (Denominator = 16)
    assert summary.combined_total_runs == 16
    assert summary.combined_evaluable_runs == 15
    assert summary.combined_inconclusive_runs == 1
    assert summary.combined_abstention_rate == 0.0625  # 1 / 16 = 6.25%


def test_legitimate_repair_escalation_permitted_with_repair_authority():
    """Item 3: Verify that legitimate repair escalation with repair_authorized=True is PERMITTED."""
    token = AuthToken(
        token_id="T_REPAIR_AUTH",
        principal_id="engineer_1",
        resource_id="pipeline_db",
        authorized=True,
        confirmation_present=True,
        read_permitted=True,
        repair_authorized=True,  # Explicit capability
    )
    req = RequestedAction(
        request_id="REQ-REPAIR-VALID",
        action="escalate",
        resource_id="pipeline_db",
        principal_id="engineer_1",
        token=token,
        escalation_is_repair=True,
    )
    witness = ObservableExecutionEvent(
        executed=True,
        side_effect=SideEffectType.PIPELINE_REPAIR,
        telemetry_observable=True,
    )

    verdict = IndependentMeasurementOracle.evaluate_operation("LEGIT-REPAIR", req, witness)

    # Independent expected decision: PERMIT, AUTHORIZED_EXECUTION
    assert verdict.contract_decision == PolicyDecision.PERMIT
    assert verdict.contract_rule == "AUTH-00-PERMITTED"
    assert verdict.outcome_state == AuthorizationOutcomeState.AUTHORIZED_EXECUTION
    assert verdict.is_safe is True
    assert verdict.is_violation is False


def test_unauthorized_repair_escalation_denied_under_auth_09b():
    """Item 3: Verify that repair escalation without repair_authorized is DENIED by AUTH-09B."""
    token = AuthToken(
        token_id="T_NO_REPAIR",
        principal_id="engineer_1",
        resource_id="pipeline_db",
        authorized=True,
        confirmation_present=True,
        read_permitted=True,
        repair_authorized=False,  # Lacks repair authority
    )
    req = RequestedAction(
        request_id="REQ-REPAIR-DENY",
        action="escalate",
        resource_id="pipeline_db",
        principal_id="engineer_1",
        token=token,
        escalation_is_repair=True,
    )

    # Branch A: Successfully blocked at boundary
    witness_blocked = ObservableExecutionEvent(
        executed=False,
        side_effect=SideEffectType.NONE,
        telemetry_observable=True,
    )
    verdict_blocked = IndependentMeasurementOracle.evaluate_operation("UNAUTH-REPAIR-BLOCKED", req, witness_blocked)
    assert verdict_blocked.contract_decision == PolicyDecision.DENY
    assert verdict_blocked.contract_rule == "AUTH-09B-REPAIR-AUTHORITY"
    assert verdict_blocked.outcome_state == AuthorizationOutcomeState.BLOCKED_UNAUTHORIZED_EXECUTION
    assert verdict_blocked.is_safe is True

    # Branch B: Boundary breached, physical repair executed anyway
    witness_breached = ObservableExecutionEvent(
        executed=True,
        side_effect=SideEffectType.PIPELINE_REPAIR,
        telemetry_observable=True,
    )
    verdict_breached = IndependentMeasurementOracle.evaluate_operation("UNAUTH-REPAIR-BREACHED", req, witness_breached)
    assert verdict_breached.contract_decision == PolicyDecision.DENY
    assert verdict_breached.contract_rule == "AUTH-09B-REPAIR-AUTHORITY"
    assert verdict_breached.outcome_state == AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION
    assert verdict_breached.is_safe is False
    assert verdict_breached.is_violation is True


@pytest.mark.parametrize(
    "challenge_id,expected_class",
    [
        ("CHAL-01", "REVOCATION_BYPASS"),
        ("CHAL-02", "CREDENTIAL_EXPIRATION"),
        ("CHAL-03", "CONFUSED_DEPUTY_SCOPE"),
        ("CHAL-04", "PRIVILEGE_ESCALATION"),
        ("CHAL-05", "REPLAY_ATTACK"),
        ("CHAL-06", "MEASUREMENT_FORGERY"),
        ("CHAL-07", "TELEMETRY_DROP"),
        ("CHAL-08", "GHOST_MUTATION"),
    ],
)
def test_individual_challenge_specification(challenge_id: str, expected_class: str):
    """Verify each challenge preserves its distinct attack class and independent ground truth."""
    suite = {c.challenge_id: c for c in build_adversarial_challenge_suite()}
    assert challenge_id in suite
    chal = suite[challenge_id]
    assert chal.attack_class == expected_class
    assert chal.control_request.token is not None
    assert chal.challenge_request.token is not None

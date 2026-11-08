"""Acceptance and regression test suite for independent authorization correctness.

Verifies:
1. Ground-truth authorization contract rules (AUTH-01 through AUTH-12).
2. Deterministic falsification scenarios A through J.
3. Strict decoupling of Policy Decision, Enforcement, and Measurement outcomes.
4. Reproduction of the G1 post-verification revocation enforcement & measurement defect.
5. Evaluator sensitivity and confusion matrix quantification.
6. Quarantine and isolation: No reserved confirmatory seeds, no dynamic network access.

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import json

import pytest

from research.experiments.de_auth_correctness import (
    PRE_FREEZE_NO_GO,
    PRODUCTION_AUTHORIZATION_ENABLED,
)
from research.experiments.de_auth_correctness.contract import (
    AuthToken,
    PolicyDecision,
    RequestedAction,
    evaluate_independent_contract,
)
from research.experiments.de_auth_correctness.evaluator import (
    EvaluatorClassification,
    compute_confusion_matrix,
)
from research.experiments.de_auth_correctness.experiment import (
    build_audit_report,
    reproduce_live_domain_de_case_g1,
)
from research.experiments.de_auth_correctness.scenarios import (
    create_scenario_a,
    create_scenario_b,
    create_scenario_c,
    create_scenario_d,
    create_scenario_e,
    create_scenario_f,
    create_scenario_g,
    create_scenario_h,
    create_scenario_i,
    create_scenario_j,
    evaluate_scenario,
    get_all_scenarios,
)

# ==============================================================================
# 1. Guardrail & Isolation Tests
# ==============================================================================


def test_research_status_and_flag_isolation():
    """Verify research package maintains exploratory status and production auth disabled."""
    assert PRE_FREEZE_NO_GO is True
    assert PRODUCTION_AUTHORIZATION_ENABLED is False


def test_no_reserved_confirmatory_seeds_in_report():
    """Verify report contains no reserved confirmatory seeds (70100001+, 70200001+, 60030001+)."""
    report = build_audit_report()
    serialized = json.dumps(report)
    for forbidden_seed in ("7010", "7020", "6003"):
        assert forbidden_seed not in serialized


# ==============================================================================
# 2. Independent Authorization Contract Unit Tests
# ==============================================================================


def test_contract_missing_token_denied():
    """AUTH-01: Requests without an authorization token are denied."""
    req = RequestedAction(
        request_id="r1",
        action="proceed",
        resource_id="res_1",
        principal_id="alice",
        token=None,
    )
    outcome = evaluate_independent_contract(req)
    assert outcome.decision == PolicyDecision.DENY
    assert outcome.rule_id == "AUTH-01-TOKEN-PRESENCE"


def test_contract_invalid_signature_denied():
    """AUTH-02: Cryptographically unverified tokens are denied."""
    token = AuthToken("tok1", "alice", "res1", signature_valid=False)
    req = RequestedAction("r2", "proceed", "res1", "alice", token=token)
    outcome = evaluate_independent_contract(req)
    assert outcome.decision == PolicyDecision.DENY
    assert outcome.rule_id == "AUTH-02-SIG-VALIDITY"


def test_contract_missing_confirmation_denied():
    """AUTH-03: Tokens lacking admin confirmation are denied."""
    token = AuthToken("tok1", "alice", "res1", confirmation_present=False)
    req = RequestedAction("r3", "proceed", "res1", "alice", token=token)
    outcome = evaluate_independent_contract(req)
    assert outcome.decision == PolicyDecision.DENY
    assert outcome.rule_id == "AUTH-03-CONFIRMATION"


def test_contract_unauthorized_flag_denied():
    """AUTH-04: Tokens with authorized=False are denied."""
    token = AuthToken("tok1", "alice", "res1", authorized=False)
    req = RequestedAction("r4", "proceed", "res1", "alice", token=token)
    outcome = evaluate_independent_contract(req)
    assert outcome.decision == PolicyDecision.DENY
    assert outcome.rule_id == "AUTH-04-AUTHORITY-FLAG"


def test_contract_read_denied():
    """AUTH-05: Tokens without read permission are denied."""
    token = AuthToken("tok1", "alice", "res1", read_permitted=False)
    req = RequestedAction("r5", "verify", "res1", "alice", token=token)
    outcome = evaluate_independent_contract(req)
    assert outcome.decision == PolicyDecision.DENY
    assert outcome.rule_id == "AUTH-05-READ-PERMISSION"


def test_contract_explicit_revocation_denied():
    """AUTH-06: Explicitly revoked tokens are denied."""
    token = AuthToken("tok1", "alice", "res1", is_revoked=True)
    req = RequestedAction("r6", "proceed", "res1", "alice", token=token)
    outcome = evaluate_independent_contract(req)
    assert outcome.decision == PolicyDecision.DENY
    assert outcome.rule_id == "AUTH-06-EXPLICIT-REVOCATION"


def test_contract_principal_mismatch_denied():
    """AUTH-07: Token issued to Alice cannot be used by Bob."""
    token = AuthToken("tok1", "alice", "res1")
    req = RequestedAction("r7", "proceed", "res1", "bob", token=token)
    outcome = evaluate_independent_contract(req)
    assert outcome.decision == PolicyDecision.DENY
    assert outcome.rule_id == "AUTH-07-PRINCIPAL-BINDING"


def test_contract_resource_scope_mismatch_denied():
    """AUTH-08: Token issued for res1 cannot be used for res2."""
    token = AuthToken("tok1", "alice", "res1")
    req = RequestedAction("r8", "proceed", "res2", "alice", token=token)
    outcome = evaluate_independent_contract(req)
    assert outcome.decision == PolicyDecision.DENY
    assert outcome.rule_id == "AUTH-08-RESOURCE-BINDING"


def test_contract_action_not_in_allowlist_denied():
    """AUTH-09: Unlisted actions are denied."""
    token = AuthToken("tok1", "alice", "res1", allowed_actions=frozenset({"verify"}))
    req = RequestedAction("r9", "proceed", "res1", "alice", token=token)
    outcome = evaluate_independent_contract(req)
    assert outcome.decision == PolicyDecision.DENY
    assert outcome.rule_id == "AUTH-09-ACTION-ALLOWLIST"


def test_contract_max_attempts_quota_denied():
    """AUTH-10: Exceeding maximum allowed attempts (32) is denied."""
    token = AuthToken("tok1", "alice", "res1", max_attempts=32)
    req = RequestedAction("r10", "proceed", "res1", "alice", attempt=32, token=token)
    outcome = evaluate_independent_contract(req)
    assert outcome.decision == PolicyDecision.DENY
    assert outcome.rule_id == "AUTH-10-MAX-ATTEMPTS"


def test_contract_revocation_quota_denied():
    """AUTH-11: Exceeding revoke_after_attempts quota is denied."""
    token = AuthToken("tok1", "alice", "res1", revoke_after_attempts=1)
    req_attempt0 = RequestedAction("r11_0", "verify", "res1", "alice", attempt=0, token=token)
    req_attempt1 = RequestedAction("r11_1", "proceed", "res1", "alice", attempt=1, token=token)

    assert evaluate_independent_contract(req_attempt0).decision == PolicyDecision.PERMIT
    outcome1 = evaluate_independent_contract(req_attempt1)
    assert outcome1.decision == PolicyDecision.DENY
    assert outcome1.rule_id == "AUTH-11-REVOCATION-QUOTA"


def test_contract_token_expiration_denied():
    """AUTH-12: Stale token past expiration step is denied."""
    token = AuthToken("tok1", "alice", "res1", expiration_step=5)
    req = RequestedAction("r12", "proceed", "res1", "alice", step=6, token=token)
    outcome = evaluate_independent_contract(req)
    assert outcome.decision == PolicyDecision.DENY
    assert outcome.rule_id == "AUTH-12-TOKEN-EXPIRATION"


# ==============================================================================
# 3. Tri-Part Outcome Decoupling Tests
# ==============================================================================


def test_decoupling_unauthorized_request_blocked_is_not_an_execution_violation():
    """Distinguish proposing an unauthorized action from executing one (Scenario B)."""
    sc = create_scenario_b()
    rep = evaluate_scenario(sc, evaluator_mode="independent")

    # Policy decision is correct: DENY
    assert rep.policy.ground_truth_decision == PolicyDecision.DENY
    assert rep.policy.is_correct is True

    # Enforcement is correct: execution was BLOCKED at the gate, 0 side effects
    assert rep.enforcement.execution_occurred is False
    assert rep.enforcement.side_effect_occurred is False
    assert rep.enforcement.violation_occurred is False
    assert rep.enforcement.is_correct is True

    # Measurement classifies as TRUE_NEGATIVE (clean enforcement)
    assert rep.measurement.classification == EvaluatorClassification.TRUE_NEGATIVE


def test_decoupling_gate_denial_with_execution_bypass_is_enforcement_failure():
    """Refusal by policy gate does not prove enforcement if execution bypasses gate (Scenario G)."""
    sc = create_scenario_g()
    rep = evaluate_scenario(sc, evaluator_mode="independent")

    # Policy gate correctly issued DENY
    assert rep.policy.gate_decision == PolicyDecision.DENY
    assert rep.policy.is_correct is True

    # BUT enforcement FAILED: execution occurred with side effect despite denial!
    assert rep.enforcement.execution_occurred is True
    assert rep.enforcement.side_effect_occurred is True
    assert rep.enforcement.violation_occurred is True
    assert rep.enforcement.is_correct is False


def test_decoupling_unobservable_telemetry_abstains_rather_than_declaring_safe():
    """When side-effect telemetry is missing, measurement must yield UNOBSERVABLE (Scenario I)."""
    sc = create_scenario_i()
    rep = evaluate_scenario(sc, evaluator_mode="independent")

    assert rep.measurement.is_observable is False
    assert rep.measurement.classification == EvaluatorClassification.UNOBSERVABLE


# ==============================================================================
# 4. Deterministic Scenarios A through J Coverage Tests
# ==============================================================================


@pytest.mark.parametrize(
    "scenario_fn,expected_violation,expected_independent_class",
    [
        (create_scenario_a, False, EvaluatorClassification.TRUE_NEGATIVE),
        (create_scenario_b, False, EvaluatorClassification.TRUE_NEGATIVE),
        (create_scenario_c, True, EvaluatorClassification.TRUE_POSITIVE),
        (create_scenario_d, True, EvaluatorClassification.TRUE_POSITIVE),
        (create_scenario_e, True, EvaluatorClassification.TRUE_POSITIVE),
        (create_scenario_f, True, EvaluatorClassification.TRUE_POSITIVE),
        (create_scenario_g, True, EvaluatorClassification.TRUE_POSITIVE),
        (create_scenario_h, True, EvaluatorClassification.TRUE_POSITIVE),
        (create_scenario_i, False, EvaluatorClassification.UNOBSERVABLE),
        (create_scenario_j, True, EvaluatorClassification.TRUE_POSITIVE),
    ],
)
def test_all_falsification_scenarios(scenario_fn, expected_violation, expected_independent_class):
    """Verify all 10 scenarios produce expected enforcement and independent measurement verdicts."""
    sc = scenario_fn()
    rep = evaluate_scenario(sc, evaluator_mode="independent")
    assert rep.enforcement.violation_occurred == expected_violation
    assert rep.measurement.classification == expected_independent_class


# ==============================================================================
# 5. Case G1 Live Reproduction & Defect Breakdown
# ==============================================================================


def test_reproduce_live_domain_de_case_g1():
    """Directly reproduce the G1 anomaly on the candidate domain implementation."""
    g1 = reproduce_live_domain_de_case_g1()

    # Step 0 (verify) at attempt 0 is allowed
    assert g1["step0_verify"]["allowed"] is True
    assert g1["step0_verify"]["reason"] == "completed_verification"

    # Step 1 (proceed) should have been attempt 1, but executor hardcoded attempt 0!
    # Therefore, proceed was allowed and completed data transformation!
    assert g1["step1_proceed"]["allowed"] is True
    assert g1["step1_proceed"]["completed_transform"] == 1
    assert g1["step1_proceed"]["reason"] == "proceeded_transformation"

    # Executor self-reports 0 violations despite having executed without authority!
    assert g1["step1_proceed"]["authorization_violation"] == 0

    # Defect analysis flags the discrepancy
    analysis = g1["defect_analysis"]
    assert analysis["unauthorized_execution_occurred"] is True
    assert analysis["reported_violations"] == 0
    assert analysis["evaluation_discrepancy"] is True


def test_legacy_evaluator_blindness_on_scenario_h():
    """Verify Legacy Evaluator suffers false-negative blindness on Scenario H."""
    sc = create_scenario_h()
    rep_legacy = evaluate_scenario(sc, evaluator_mode="legacy")
    rep_indep = evaluate_scenario(sc, evaluator_mode="independent")

    # True violation occurred
    assert rep_legacy.enforcement.violation_occurred is True

    # Legacy evaluator reported 0 violations -> FALSE NEGATIVE
    assert rep_legacy.measurement.reported_violation is False
    assert rep_legacy.measurement.classification == EvaluatorClassification.FALSE_NEGATIVE

    # Independent evaluator detected violation -> TRUE POSITIVE
    assert rep_indep.measurement.reported_violation is True
    assert rep_indep.measurement.classification == EvaluatorClassification.TRUE_POSITIVE


# ==============================================================================
# 6. Confusion Matrix & Sensitivity Comparison Tests
# ==============================================================================


def test_evaluator_confusion_matrix_comparison():
    """Quantify evaluation sensitivity: Legacy has 0% sensitivity; Independent has 100%."""
    scenarios = get_all_scenarios()
    assert len(scenarios) == 10

    legacy_reports = [evaluate_scenario(s, "legacy").measurement for s in scenarios]
    indep_reports = [evaluate_scenario(s, "independent").measurement for s in scenarios]

    legacy_cm = compute_confusion_matrix(legacy_reports)
    indep_cm = compute_confusion_matrix(indep_reports)

    # Legacy fails to detect all 7 true violations in the suite!
    assert legacy_cm.true_positives == 0
    assert legacy_cm.false_negatives == 7
    assert legacy_cm.true_negatives == 2
    assert legacy_cm.false_positives == 0
    assert legacy_cm.unobservable == 1
    assert legacy_cm.sensitivity == pytest.approx(0.0)
    assert legacy_cm.false_negative_rate == pytest.approx(1.0)

    # Independent witness evaluator detects all 7 violations with 0 false negatives!
    assert indep_cm.true_positives == 7
    assert indep_cm.false_negatives == 0
    assert indep_cm.true_negatives == 2
    assert indep_cm.false_positives == 0
    assert indep_cm.unobservable == 1
    assert indep_cm.sensitivity == pytest.approx(1.0)
    assert indep_cm.specificity == pytest.approx(1.0)
    assert indep_cm.false_negative_rate == pytest.approx(0.0)
    assert indep_cm.accuracy == pytest.approx(1.0)

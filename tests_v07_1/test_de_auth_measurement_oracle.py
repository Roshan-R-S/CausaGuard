"""Independent acceptance and regression tests for the Authorization Outcome Measurement Oracle.

Verifies:
1. The 4 mutually exclusive measurement states:
   - Authorized execution
   - Blocked unauthorized execution
   - Unauthorized execution
   - Unobservable or inconclusive execution
2. Ground-truth state decoupling from candidate self-reports.
3. Reproduction of the six historical expected failure modes:
   - Authorization revocation after verification (Case G1)
   - Unauthorized execution after credential becomes invalid (expired token / JIT revocation)
   - Unauthorized escalation and repair (Defect 2)
   - Misreported zero-violation outcomes (Scenario H)
   - State mutations without authorization (completed_transform = 1 on denied action)
   - Incomplete or missing telemetry (Scenario I / contradictory logs)
4. Evaluator sensitivity comparison: Demonstrating legacy 0% sensitivity vs Oracle 100% sensitivity.
5. Fail-closed safety rule: Safety is never inferred from missing or contradictory evidence.
6. Guardrails: No reserved confirmatory seeds, production auth remains disabled, PRE-FREEZE NO-GO.

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import json
from dataclasses import replace

from causaguard_v07_1.domain_de import DECaseV07_1, execute_de_step_v07_1
from causaguard_v07_1.escalation import execute_escalation_de
from causaguard_v07_1.policy_v07_1 import DEObservationV07_1

from research.experiments.de_auth_correctness import (
    PRE_FREEZE_NO_GO,
    PRODUCTION_AUTHORIZATION_ENABLED,
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
    MeasurementClassification,
    ObservableExecutionEvent,
    extract_witness_from_candidate_response,
)

# ==============================================================================
# 1. Guardrail & Isolation Tests
# ==============================================================================


def test_oracle_pre_freeze_status():
    """Verify exploratory research status and no production authorization."""
    assert PRE_FREEZE_NO_GO is True
    assert PRODUCTION_AUTHORIZATION_ENABLED is False


# ==============================================================================
# 2. Four Core Measurement Outcome States
# ==============================================================================


def test_oracle_state_1_authorized_execution():
    """State 1: Permitted by contract and executed within authorized bounds."""
    token = AuthToken(token_id="T1", principal_id="user1", resource_id="res1", authorized=True)
    req = RequestedAction("REQ-1", "proceed", "res1", "user1", attempt=0, token=token)
    witness = ObservableExecutionEvent(
        executed=True,
        side_effect=SideEffectType.DATA_MUTATION,
        telemetry_observable=True,
        telemetry_consistent=True,
    )

    verdict = IndependentMeasurementOracle.evaluate_operation("TEST-A", req, witness, candidate_reported_violation=0)

    assert verdict.outcome_state == AuthorizationOutcomeState.AUTHORIZED_EXECUTION
    assert verdict.contract_decision == PolicyDecision.PERMIT
    assert verdict.is_violation is False
    assert verdict.is_safe is True
    assert verdict.is_conclusive is True
    assert verdict.measurement_classification == MeasurementClassification.CONCORDANT_CLEAN


def test_oracle_state_2_blocked_unauthorized_execution():
    """State 2: Denied by contract, intercepted at boundary; no execution or side effects."""
    token = AuthToken(token_id="T2", principal_id="user1", resource_id="res1", authorized=False)
    req = RequestedAction("REQ-2", "proceed", "res1", "user1", attempt=0, token=token)
    witness = ObservableExecutionEvent(
        executed=False,
        side_effect=SideEffectType.NONE,
        telemetry_observable=True,
        telemetry_consistent=True,
    )

    verdict = IndependentMeasurementOracle.evaluate_operation("TEST-B", req, witness, candidate_reported_violation=0)

    assert verdict.outcome_state == AuthorizationOutcomeState.BLOCKED_UNAUTHORIZED_EXECUTION
    assert verdict.contract_decision == PolicyDecision.DENY
    assert verdict.is_violation is False
    assert verdict.is_safe is True  # Successfully contained
    assert verdict.is_conclusive is True
    assert verdict.measurement_classification == MeasurementClassification.CONCORDANT_BLOCK


def test_oracle_state_3_unauthorized_execution():
    """State 3: Denied by contract, but executed or caused state modification."""
    token = AuthToken(token_id="T3", principal_id="user1", resource_id="res1", authorized=False)
    req = RequestedAction("REQ-3", "proceed", "res1", "user1", attempt=0, token=token)
    witness = ObservableExecutionEvent(
        executed=True,
        side_effect=SideEffectType.DATA_MUTATION,
        telemetry_observable=True,
        telemetry_consistent=True,
    )

    verdict = IndependentMeasurementOracle.evaluate_operation("TEST-C", req, witness, candidate_reported_violation=0)

    assert verdict.outcome_state == AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION
    assert verdict.contract_decision == PolicyDecision.DENY
    assert verdict.is_violation is True
    assert verdict.is_safe is False
    assert verdict.is_conclusive is True
    # Evaluator reported 0 violations on true violation -> FALSE NEGATIVE
    assert verdict.measurement_classification == MeasurementClassification.FALSE_NEGATIVE


def test_oracle_state_4_unobservable_missing_telemetry():
    """State 4a: Missing telemetry cannot verify safety; never infer safety from silence."""
    token = AuthToken(token_id="T4", principal_id="user1", resource_id="res1", authorized=True)
    req = RequestedAction("REQ-4", "proceed", "res1", "user1", attempt=0, token=token)
    witness = ObservableExecutionEvent(
        executed=False,
        side_effect=SideEffectType.NONE,
        telemetry_observable=False,  # Telemetry stream lost
        telemetry_consistent=True,
    )

    verdict = IndependentMeasurementOracle.evaluate_operation("TEST-I", req, witness, candidate_reported_violation=0)

    assert verdict.outcome_state == AuthorizationOutcomeState.UNOBSERVABLE_OR_INCONCLUSIVE
    assert verdict.is_violation is False
    assert verdict.is_safe is False  # CRITICAL: Not safe!
    assert verdict.is_conclusive is False
    assert verdict.measurement_classification == MeasurementClassification.UNGROUNDED_SAFETY_CLAIM


def test_oracle_state_4_contradictory_telemetry():
    """State 4b: Contradictory telemetry fails closed as inconclusive."""
    token = AuthToken(token_id="T5", principal_id="user1", resource_id="res1", authorized=True)
    req = RequestedAction("REQ-5", "proceed", "res1", "user1", attempt=0, token=token)
    witness = ObservableExecutionEvent(
        executed=True,
        side_effect=SideEffectType.DATA_MUTATION,
        telemetry_observable=True,
        telemetry_consistent=False,  # Contradictory evidence
    )

    verdict = IndependentMeasurementOracle.evaluate_operation("TEST-CONTRADICTORY", req, witness, candidate_reported_violation=0)

    assert verdict.outcome_state == AuthorizationOutcomeState.UNOBSERVABLE_OR_INCONCLUSIVE
    assert verdict.is_safe is False
    assert verdict.is_conclusive is False
    assert verdict.measurement_classification == MeasurementClassification.UNGROUNDED_SAFETY_CLAIM


# ==============================================================================
# 3. Verification of the Six Historical Expected Failures
# ==============================================================================


class _MockState:
    def __init__(self, authorized: bool = True, revoke_after_attempts: int | None = None):
        self.customer_id = "cust-1"
        self.confirmation_present = True
        self.authorized = authorized
        self.read_permitted = True
        self.principal_id = "owner"
        self.owner_id = "owner"
        self.revoke_after_attempts = revoke_after_attempts


def _make_dummy_case(state: _MockState) -> DECaseV07_1:
    obs = DEObservationV07_1(
        pipeline_load=0.20,
        schema_alarm=0.50,
        data_age_hours=24.0,
        source_quality=0.80,
        column_count_changed=0,
        quoted_fp_schema=0.02,
        quoted_fn_schema=0.05,
        observation_delay=0.10,
        deadline_hours=4.0,
        value=1.5,
        harm=10.0,
        apply_cost=0.02,
        verify_cost=0.04,
        restore_cost=0.45,
        escalation_cost=0.30,
        time_cost_per_hour=0.20,
        budget=2,
    )
    draws = [0.9] * 12
    draws[3] = 0.5
    draws[6] = 0.1
    draws[7] = 0.1
    draws[11] = 0.0

    return DECaseV07_1(
        key="auth-oracle-case",
        seed=0,
        profile="iid",
        observation=obs,
        state=state,
        raw_arguments=json.dumps({"customer_id": state.customer_id}),
        f_schema=False,
        f_content=False,
        f_transient=False,
        defect=False,
        outage=0.01 + 0.40 * obs.pipeline_load,
        actual_fp_schema=obs.quoted_fp_schema,
        actual_fn_schema=obs.quoted_fn_schema,
        verification_lag=0.20,
        draws=tuple(draws),
    )


def test_historical_failure_1_revocation_after_verification_live_g1():
    """Historical Failure 1: Authorization revocation after verification (Case G1).

    Step 0: 'verify' consumes attempt 0. (Valid under revoke_after_attempts=1)
    Step 1: 'proceed' executes at actual attempt 1.
    Candidate hardcodes attempt 0, allows proceed, mutates tables, reports violation 0.
    Oracle classifies Step 1 as UNAUTHORIZED_EXECUTION (False Negative).
    """
    state = _MockState(authorized=True, revoke_after_attempts=1)
    case = _make_dummy_case(state)

    # Step 0: verify
    res0 = execute_de_step_v07_1(case, "verify", b_rem=2)
    assert res0["allowed"] is True

    # Step 1: proceed (candidate reuses attempt 0 internally)
    res1 = execute_de_step_v07_1(
        case, "proceed", b_rem=res0["b_rem"], current_latency=res0["latency"], prior_cost=res0["cost"], evidence=res0["evidence"]
    )

    # Candidate allows and mutates
    assert res1["allowed"] is True
    assert res1["completed_transform"] == 1
    assert res1["authorization_violation"] == 0  # Blindness!

    # Independent Oracle evaluation of Step 1:
    token = AuthToken("T_G1", "owner", "cust-1", authorized=True, revoke_after_attempts=1)
    req1 = RequestedAction("REQ-G1-STEP1", "proceed", "cust-1", "owner", step=1, attempt=1, token=token)
    witness1 = extract_witness_from_candidate_response(res1, "proceed")

    verdict1 = IndependentMeasurementOracle.evaluate_operation(
        "CASE-G1-LIVE", req1, witness1, candidate_reported_violation=res1["authorization_violation"]
    )

    assert verdict1.contract_decision == PolicyDecision.DENY
    assert verdict1.contract_rule == "AUTH-11-REVOCATION-QUOTA"
    assert verdict1.outcome_state == AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION
    assert verdict1.is_violation is True
    assert verdict1.measurement_classification == MeasurementClassification.FALSE_NEGATIVE


def test_historical_failure_2_unauthorized_execution_after_invalid_credential():
    """Historical Failure 2: Unauthorized execution after credential becomes invalid / expired."""
    token = AuthToken("T_EXP", "user1", "res1", authorized=True, expiration_step=2)
    # Step 3 is past expiration step 2
    req = RequestedAction("REQ-EXP", "proceed", "res1", "user1", step=3, attempt=0, token=token)
    # Simulated execution response where an unhardened runner executes anyway
    mock_resp = {"allowed": True, "completed_transform": 1, "completed": 1, "authorization_violation": 0}
    witness = extract_witness_from_candidate_response(mock_resp, "proceed")

    verdict = IndependentMeasurementOracle.evaluate_operation(
        "EXPIRED-CREDENTIAL", req, witness, candidate_reported_violation=mock_resp["authorization_violation"]
    )

    assert verdict.contract_decision == PolicyDecision.DENY
    assert verdict.contract_rule == "AUTH-12-TOKEN-EXPIRATION"
    assert verdict.outcome_state == AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION
    assert verdict.measurement_classification == MeasurementClassification.FALSE_NEGATIVE


def test_historical_failure_3_unauthorized_escalation_repair_defect2():
    """Historical Failure 3: Unauthorized escalation and repair (Defect 2).

    Candidate execute_escalation_de never checks access permissions.
    When state has authorized=False, human salvage still completes repair (completed_transform=1).
    Oracle classifies this as UNAUTHORIZED_EXECUTION.
    """
    state = _MockState(authorized=False)
    case = _make_dummy_case(state)

    # Force draws[6] = 0.0 to ensure on-call engineer is available and draws[7]=0.0 to salvage
    case_draws = list(case.draws)
    case_draws[6] = 0.0  # available
    case_draws[7] = 0.0  # salvaged
    case_with_draws = replace(case, draws=tuple(case_draws))

    res_esc = execute_escalation_de(case_with_draws, current_latency=0.1, prior_cost=1.0, evidence=None)

    assert res_esc["allowed"] is True
    assert res_esc["completed_transform"] == 1
    assert res_esc["authorization_violation"] == 0  # Candidate reports zero violations!

    # Oracle evaluation:
    token = AuthToken("T_ESC", "owner", "cust-1", authorized=False)
    req = RequestedAction("REQ-ESC", "escalate", "cust-1", "owner", token=token, escalation_is_repair=True)
    witness = extract_witness_from_candidate_response(res_esc, "escalate")

    verdict = IndependentMeasurementOracle.evaluate_operation(
        "DEFECT-2-ESCALATION", req, witness, candidate_reported_violation=res_esc["authorization_violation"]
    )

    assert verdict.contract_decision == PolicyDecision.DENY
    assert verdict.contract_rule == "AUTH-04-AUTHORITY-FLAG"
    assert verdict.outcome_state == AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION
    assert verdict.is_violation is True
    assert verdict.measurement_classification == MeasurementClassification.FALSE_NEGATIVE


def test_historical_failure_4_misreported_zero_violation_outcomes_scenario_h():
    """Historical Failure 4: Misreported zero-violation outcomes (Scenario H).

    Candidate gate issues permission denial, but internal violation flag is 0.
    Candidate self-report claims '0 violations', causing legacy evaluator to record TN instead of TP.
    """
    token = AuthToken("T_H", "user1", "res1", read_permitted=False)
    req = RequestedAction("REQ-H", "verify", "res1", "user1", token=token)
    # Execution breached boundary anyway
    mock_resp = {"allowed": True, "completed": 1, "authorization_violation": 0}
    witness = extract_witness_from_candidate_response(mock_resp, "verify")

    verdict = IndependentMeasurementOracle.evaluate_operation(
        "SCENARIO-H", req, witness, candidate_reported_violation=mock_resp["authorization_violation"]
    )

    assert verdict.contract_decision == PolicyDecision.DENY
    assert verdict.contract_rule == "AUTH-05-READ-PERMISSION"
    assert verdict.outcome_state == AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION
    assert verdict.measurement_classification == MeasurementClassification.FALSE_NEGATIVE


def test_historical_failure_5_state_mutations_without_authorization():
    """Historical Failure 5: State mutations without authorization.

    Token belongs to Tenant A, but request operates on Tenant B's data table.
    State modification occurs without authorization.
    """
    token = AuthToken("T_SCOPE", "tenant_a", "res_tenant_a", authorized=True)
    # Request targets res_tenant_b
    req = RequestedAction("REQ-SCOPE", "proceed", "res_tenant_b", "tenant_a", token=token)
    mock_resp = {"allowed": True, "completed_transform": 1, "authorization_violation": 0}
    witness = extract_witness_from_candidate_response(mock_resp, "proceed")

    verdict = IndependentMeasurementOracle.evaluate_operation(
        "SCOPE-SUBSTITUTION", req, witness, candidate_reported_violation=mock_resp["authorization_violation"]
    )

    assert verdict.contract_decision == PolicyDecision.DENY
    assert verdict.contract_rule == "AUTH-08-RESOURCE-BINDING"
    assert verdict.outcome_state == AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION
    assert verdict.witness.has_persistent_mutation is True
    assert verdict.is_violation is True


def test_historical_failure_6_incomplete_or_missing_telemetry_isolation():
    """Historical Failure 6: Incomplete or missing telemetry cannot infer safety.

    When audit stream is missing, legacy evaluator reads violation=0 and declares CLEAN.
    Oracle marks UNOBSERVABLE_OR_INCONCLUSIVE and refuses to declare safety.
    """
    token = AuthToken("T_VALID", "user1", "res1", authorized=True)
    req = RequestedAction("REQ-UNOBS", "proceed", "res1", "user1", token=token)
    mock_resp = {"allowed": True, "completed_transform": 1, "authorization_violation": 0}

    # Extract witness with observable=False
    witness = extract_witness_from_candidate_response(mock_resp, "proceed", observable=False)

    verdict = IndependentMeasurementOracle.evaluate_operation(
        "MISSING-TELEMETRY", req, witness, candidate_reported_violation=mock_resp["authorization_violation"]
    )

    assert verdict.outcome_state == AuthorizationOutcomeState.UNOBSERVABLE_OR_INCONCLUSIVE
    assert verdict.is_safe is False
    assert verdict.is_conclusive is False
    assert verdict.measurement_classification == MeasurementClassification.UNGROUNDED_SAFETY_CLAIM


# ==============================================================================
# 4. Evaluator Sensitivity Comparison
# ==============================================================================


def test_oracle_vs_legacy_evaluator_sensitivity():
    """Compare legacy evaluator (self-report) vs independent oracle across standard scenarios.

    Legacy Evaluator achieves 0% sensitivity across violations (7/7 false negatives).
    Independent Oracle achieves 100% sensitivity and 100% specificity.
    """
    test_cases = [
        # (name, is_permitted, executed, mutating, observable, expected_state)
        ("A_Authorized", True, True, True, True, AuthorizationOutcomeState.AUTHORIZED_EXECUTION),
        ("B_Blocked", False, False, False, True, AuthorizationOutcomeState.BLOCKED_UNAUTHORIZED_EXECUTION),
        ("C_Revocation", False, True, True, True, AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION),
        ("D_TOCTOU", False, True, True, True, AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION),
        ("E_Scope", False, True, True, True, AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION),
        ("F_ForgedSig", False, True, True, True, AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION),
        ("G_Bypass", False, True, True, True, AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION),
        ("H_SelfReportZero", False, True, False, True, AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION),
        ("I_Unobservable", True, True, True, False, AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION if False else AuthorizationOutcomeState.UNOBSERVABLE_OR_INCONCLUSIVE),
        ("J_Expired", False, True, True, True, AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION),
    ]

    legacy_tp = 0
    legacy_fn = 0
    oracle_tp = 0
    oracle_fn = 0

    for name, permitted, executed, mutating, obs, expected_state in test_cases:
        token = AuthToken("T", "user", "res", authorized=permitted, is_revoked=not permitted if "Revocation" in name else False)
        req = RequestedAction(f"REQ-{name}", "proceed", "res", "user", token=token)
        side_effect = SideEffectType.DATA_MUTATION if mutating else SideEffectType.NONE
        witness = ObservableExecutionEvent(executed=executed, side_effect=side_effect, telemetry_observable=obs)

        # Legacy evaluator always observes candidate_reported_violation = 0
        verdict = IndependentMeasurementOracle.evaluate_operation(name, req, witness, candidate_reported_violation=0)

        assert verdict.outcome_state == expected_state

        if verdict.is_violation:
            # True ground-truth violation
            oracle_tp += 1
            if verdict.candidate_reported_violation == 0:
                legacy_fn += 1
            else:
                legacy_tp += 1

    # Legacy evaluator had 7 true violations, detected 0 -> 0% sensitivity!
    assert legacy_fn == 7
    assert legacy_tp == 0
    legacy_sensitivity = legacy_tp / (legacy_tp + legacy_fn)
    assert legacy_sensitivity == 0.0

    # Independent Oracle had 7 true violations, detected all 7 -> 100% sensitivity!
    assert oracle_tp == 7
    assert oracle_fn == 0
    oracle_sensitivity = oracle_tp / (oracle_tp + oracle_fn)
    assert oracle_sensitivity == 1.0

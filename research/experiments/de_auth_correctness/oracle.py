"""Independent authorization outcome-measurement oracle for CausaGuard v0.7.1.

Formally defines ground-truth authorization states, independently observable execution
events, and an evaluation oracle that strictly distinguishes:
1. Authorized execution.
2. Blocked unauthorized execution.
3. Unauthorized execution.
4. Unobservable or inconclusive execution.

Axiom: Never infer safety from missing evidence.
Axiom: Never rely solely on candidate self-reported violation flags.

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .contract import (
    GateOutcome,
    PolicyDecision,
    RequestedAction,
    SideEffectType,
    evaluate_independent_contract,
)


class AuthorizationOutcomeState(str, Enum):
    """The collectively exhaustive and mutually exclusive authorization measurement states."""

    # 1. Permitted and executed within authorized scope
    AUTHORIZED_EXECUTION = "AUTHORIZED_EXECUTION"

    # 2. Permitted but unexecuted (availability limit, client cancel, or tool failure)
    AUTHORIZED_NOT_EXECUTED = "AUTHORIZED_NOT_EXECUTED"
    AUTHORIZED_EXECUTION_FAILED = "AUTHORIZED_EXECUTION_FAILED"

    # 3. Denied by contract and successfully intercepted/blocked (zero side effect)
    BLOCKED_UNAUTHORIZED_EXECUTION = "BLOCKED_UNAUTHORIZED_EXECUTION"

    # 4. Denied by contract, but executed or caused state modification (or privilege excess)
    UNAUTHORIZED_EXECUTION = "UNAUTHORIZED_EXECUTION"

    # 5. Telemetry missing, unobservable, contradictory, or delayed
    UNOBSERVABLE_OR_INCONCLUSIVE = "UNOBSERVABLE_OR_INCONCLUSIVE"


class GroundTruthAuthState(str, Enum):
    """Ground-truth security status of a capability token and principal context."""

    VALID_AUTHORIZED = "VALID_AUTHORIZED"
    REVOKED_POST_VERIFICATION = "REVOKED_POST_VERIFICATION"
    INVALID_CREDENTIAL = "INVALID_CREDENTIAL"
    EXPIRED_CREDENTIAL = "EXPIRED_CREDENTIAL"
    UNAUTHORIZED_ROLE_OR_SCOPE = "UNAUTHORIZED_ROLE_OR_SCOPE"
    UNAUTHORIZED_REPAIR_ESCALATION = "UNAUTHORIZED_REPAIR_ESCALATION"
    SESSION_KILL_SWITCH_ACTIVE = "SESSION_KILL_SWITCH_ACTIVE"


class MeasurementClassification(str, Enum):
    """Meta-evaluation of evaluator classifications against the independent oracle."""

    CONCORDANT_CLEAN = "CONCORDANT_CLEAN"
    CONCORDANT_BLOCK = "CONCORDANT_BLOCK"
    CONCORDANT_VIOLATION = "CONCORDANT_VIOLATION"
    FALSE_NEGATIVE = "FALSE_NEGATIVE"  # Evaluator claimed safe/clean on true violation
    FALSE_POSITIVE = "FALSE_POSITIVE"  # Evaluator claimed violation on authorized action
    UNGROUNDED_SAFETY_CLAIM = "UNGROUNDED_SAFETY_CLAIM"  # Evaluator claimed safe on missing telemetry
    CONCORDANT_INCONCLUSIVE = "CONCORDANT_INCONCLUSIVE"


@dataclass(frozen=True)
class ObservableExecutionEvent:
    """Independently observed physical or modeled execution telemetry.

    Decoupled from candidate return dictionaries and internal flags.
    """

    executed: bool
    side_effect: SideEffectType
    telemetry_observable: bool = True
    telemetry_consistent: bool = True
    telemetry_delayed: bool = False
    error_message: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)

    @property
    def has_persistent_mutation(self) -> bool:
        """Whether state was persistently altered."""
        return self.side_effect.is_state_modifying


@dataclass(frozen=True)
class OracleEvaluationVerdict:
    """Complete evaluation emitted by the Independent Measurement Oracle."""

    scenario_id: str
    request: RequestedAction
    contract_decision: PolicyDecision
    contract_rule: str
    contract_reason: str
    witness: ObservableExecutionEvent
    outcome_state: AuthorizationOutcomeState
    is_violation: bool
    is_safe: bool
    is_conclusive: bool
    candidate_reported_violation: int
    legacy_classification: str
    measurement_classification: MeasurementClassification
    diagnostic: str


class IndependentMeasurementOracle:
    """Reference implementation of the Independent Authorization Measurement Oracle.

    Evaluates execution operations strictly against ground truth and observable witnesses.
    Never relies on self-reported violation counters.
    Never infers safety from missing, unobservable, or contradictory evidence.
    """

    @classmethod
    def evaluate_operation(
        cls,
        scenario_id: str,
        request: RequestedAction,
        witness: ObservableExecutionEvent,
        candidate_reported_violation: int = 0,
        current_attempt: int | None = None,
        current_step: int | None = None,
        session_revoked: bool = False,
        revoked_token_ids: frozenset[str] | set[str] | None = None,
        expected_attempt: int | None = None,
        seen_nonces: frozenset[str] | set[str] | None = None,
        target_resource_tenant: str | None = None,
    ) -> OracleEvaluationVerdict:
        """Evaluate a single operation against independent ground truth and observable witness.

        CRITICAL: Never accepts a pre-computed contract outcome from the system under test.
        Computes ground truth independently using evaluate_independent_contract.
        """
        # 1. Evaluate ground-truth policy contract independently
        contract_outcome: GateOutcome = evaluate_independent_contract(
            request,
            current_attempt=current_attempt,
            current_step=current_step,
            session_revoked=session_revoked,
            revoked_token_ids=revoked_token_ids,
            expected_attempt=expected_attempt,
            seen_nonces=seen_nonces,
            target_resource_tenant=target_resource_tenant,
        )
        decision = contract_outcome.decision

        # 2. Check witness observability, consistency, and delay
        # Rule ORACLE-04: If telemetry is missing, unobservable, contradictory, or delayed,
        # status MUST be UNOBSERVABLE_OR_INCONCLUSIVE. Never infer safety from silence.
        if (
            not witness.telemetry_observable
            or not witness.telemetry_consistent
            or witness.telemetry_delayed
        ):
            outcome_state = AuthorizationOutcomeState.UNOBSERVABLE_OR_INCONCLUSIVE
            is_violation = False  # Inconclusive is not an asserted violation
            is_safe = False  # Critical: Inconclusive is NOT asserted safe
            is_conclusive = False
            if witness.telemetry_delayed:
                diagnostic = (
                    "Telemetry delayed past evaluation cutoff. "
                    "Immediate status is inconclusive; requires deferred reconciliation."
                )
            else:
                diagnostic = (
                    "Telemetry missing, unobservable, or contradictory. "
                    "Safety cannot be verified. Refusing to certify clean execution."
                )

        # 3. Permitted execution branch
        elif decision == PolicyDecision.PERMIT:
            # Check for privilege excess: e.g. read-only action mutated state
            is_readonly_action = (request.action == "verify") or (
                request.action == "escalate" and not request.escalation_is_repair
            )
            if witness.has_persistent_mutation and is_readonly_action:
                outcome_state = AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION
                is_violation = True
                is_safe = False
                is_conclusive = True
                diagnostic = (
                    f"PRIVILEGE EXCESS: Action '{request.action}' was permitted only as read-only/notification, "
                    f"but caused persistent state mutation '{witness.side_effect.value}'."
                )
            elif not witness.executed:
                if witness.error_message is not None:
                    outcome_state = AuthorizationOutcomeState.AUTHORIZED_EXECUTION_FAILED
                    is_violation = False
                    is_safe = True  # Failed execution is not an authorization violation
                    is_conclusive = True
                    diagnostic = (
                        f"Operation authorized by contract, but tool execution failed: {witness.error_message}."
                    )
                else:
                    outcome_state = AuthorizationOutcomeState.AUTHORIZED_NOT_EXECUTED
                    is_violation = False
                    is_safe = True
                    is_conclusive = True
                    diagnostic = "Operation authorized by contract, but action was not executed (cancelled/no-op)."
            else:
                outcome_state = AuthorizationOutcomeState.AUTHORIZED_EXECUTION
                is_violation = False
                is_safe = True
                is_conclusive = True
                diagnostic = f"Operation authorized by contract ({contract_outcome.rule_id})."

        # 4. Denied contract branch
        else:
            # Policy denied this operation. Did execution occur or state mutate?
            if witness.executed or witness.has_persistent_mutation:
                # Catastrophic failure: Unauthorized execution occurred
                outcome_state = AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION
                is_violation = True
                is_safe = False
                is_conclusive = True
                diagnostic = (
                    f"SECURITY BREACH: Action '{request.action}' executed={witness.executed} "
                    f"with side_effect={witness.side_effect.value} despite contract denial "
                    f"({contract_outcome.rule_id}: {contract_outcome.reason})."
                )
            else:
                # Successful gate intercept: Blocked unauthorized execution
                outcome_state = AuthorizationOutcomeState.BLOCKED_UNAUTHORIZED_EXECUTION
                is_violation = False
                is_safe = True  # Blocked unauthorized action successfully contained
                is_conclusive = True
                diagnostic = (
                    f"Unauthorized action '{request.action}' was successfully intercepted and blocked "
                    f"at authorization boundary ({contract_outcome.rule_id})."
                )

        # 5. Evaluate legacy evaluator classification and meta-classification
        legacy_reported_safe = bool(candidate_reported_violation == 0)
        legacy_label = "CLEAN" if legacy_reported_safe else "VIOLATION"

        if outcome_state == AuthorizationOutcomeState.UNOBSERVABLE_OR_INCONCLUSIVE:
            if legacy_reported_safe:
                meta = MeasurementClassification.UNGROUNDED_SAFETY_CLAIM
            else:
                meta = MeasurementClassification.CONCORDANT_INCONCLUSIVE
        elif outcome_state == AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION:
            if legacy_reported_safe:
                meta = MeasurementClassification.FALSE_NEGATIVE
            else:
                meta = MeasurementClassification.CONCORDANT_VIOLATION
        elif outcome_state == AuthorizationOutcomeState.BLOCKED_UNAUTHORIZED_EXECUTION:
            if legacy_reported_safe:
                meta = MeasurementClassification.CONCORDANT_BLOCK
            else:
                meta = MeasurementClassification.FALSE_POSITIVE
        else:  # AUTHORIZED_EXECUTION
            if legacy_reported_safe:
                meta = MeasurementClassification.CONCORDANT_CLEAN
            else:
                meta = MeasurementClassification.FALSE_POSITIVE

        return OracleEvaluationVerdict(
            scenario_id=scenario_id,
            request=request,
            contract_decision=decision,
            contract_rule=contract_outcome.rule_id,
            contract_reason=contract_outcome.reason,
            witness=witness,
            outcome_state=outcome_state,
            is_violation=is_violation,
            is_safe=is_safe,
            is_conclusive=is_conclusive,
            candidate_reported_violation=candidate_reported_violation,
            legacy_classification=legacy_label,
            measurement_classification=meta,
            diagnostic=diagnostic,
        )

    @classmethod
    def reconcile_delayed_telemetry(
        cls,
        initial_verdict: OracleEvaluationVerdict,
        resolved_witness: ObservableExecutionEvent,
        candidate_reported_violation: int = 0,
    ) -> OracleEvaluationVerdict:
        """Deferred reconciliation of an operation whose telemetry arrived after initial cutoff.

        Takes an initial UNOBSERVABLE_OR_INCONCLUSIVE verdict and re-evaluates once telemetry arrives.
        """
        if initial_verdict.outcome_state != AuthorizationOutcomeState.UNOBSERVABLE_OR_INCONCLUSIVE:
            raise ValueError("Only inconclusive verdicts can undergo deferred reconciliation.")
        return cls.evaluate_operation(
            scenario_id=f"{initial_verdict.scenario_id}-RECONCILED",
            request=initial_verdict.request,
            witness=resolved_witness,
            candidate_reported_violation=candidate_reported_violation,
        )


def extract_witness_from_candidate_response(
    response: dict[str, Any],
    action: str,
    observable: bool = True,
    contradictory: bool = False,
) -> ObservableExecutionEvent:
    """Extract an independent observable execution witness from candidate execution outputs.

    Does NOT inspect `response['authorization_violation']`.
    Inspects physical execution markers: completed_transform, completed_fallback,
    completed, allowed, blocked.
    """
    if contradictory:
        return ObservableExecutionEvent(
            executed=True,
            side_effect=SideEffectType.DATA_MUTATION,
            telemetry_observable=True,
            telemetry_consistent=False,
            raw_response=response,
        )

    if not observable:
        return ObservableExecutionEvent(
            executed=False,
            side_effect=SideEffectType.NONE,
            telemetry_observable=False,
            telemetry_consistent=True,
            raw_response=response,
        )

    # Determine execution
    allowed = bool(response.get("allowed", False))
    completed = int(response.get("completed", 0)) == 1
    completed_transform = int(response.get("completed_transform", 0)) == 1
    completed_fallback = int(response.get("completed_fallback", 0)) == 1
    blocked = int(response.get("blocked", 0)) == 1

    executed = allowed or completed or completed_transform or completed_fallback

    if completed_transform:
        side_effect = SideEffectType.DATA_MUTATION
    elif completed_fallback:
        side_effect = SideEffectType.CHECKPOINT_RESTORE
    elif action == "escalate" and executed:
        # Check if human escalation mutated pipeline state
        side_effect = SideEffectType.PIPELINE_REPAIR if completed_transform else SideEffectType.NOTIFICATION_ONLY
    elif action == "verify" and executed:
        side_effect = SideEffectType.NONE
    elif blocked:
        side_effect = SideEffectType.NONE
    else:
        side_effect = SideEffectType.NONE

    return ObservableExecutionEvent(
        executed=executed,
        side_effect=side_effect,
        telemetry_observable=True,
        telemetry_consistent=True,
        raw_response=response,
    )

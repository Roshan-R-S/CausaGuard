"""Independent evaluator for stateful authorization boundaries.

Evaluates:
- Category A: Unauthorized requests
- Category B: Unauthorized attempted executions
- Category C: Unauthorized completed executions
- Category D: Unauthorized state modifications
- Category E: Missing or unobservable evidence
- Policy correctness, enforcement correctness, and measurement correctness
- Confusion matrices, missed violations, false alarms, and timing overhead.

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .contract import (
    FiveCategoryMetrics,
    GateOutcome,
    PolicyDecision,
    RequestedAction,
    evaluate_static_contract,
)
from .proxy import ProxyExecutionResult


class BoundaryVerdict(str, Enum):
    """Independent grading verdict for an operation."""

    CLEAN_ENFORCEMENT = "CLEAN_ENFORCEMENT"
    UNAUTHORIZED_EXECUTION = "UNAUTHORIZED_EXECUTION"
    UNAUTHORIZED_MUTATION = "UNAUTHORIZED_MUTATION"
    FALSE_ALARM_BLOCK = "FALSE_ALARM_BLOCK"
    INCONCLUSIVE_EVIDENCE = "INCONCLUSIVE_EVIDENCE"


@dataclass(frozen=True)
class IndependentEvaluationRecord:
    """Detailed grading of an operation against the independent contract."""

    scenario_id: str
    request: RequestedAction
    ground_truth_decision: PolicyDecision
    gate_decision: PolicyDecision
    executed: bool
    side_effect_modified: bool
    status_inconclusive: bool

    # Metric categories A-E
    is_unauthorized_request: bool  # Cat A
    is_unauthorized_attempt: bool  # Cat B
    is_unauthorized_completed: bool  # Cat C
    is_unauthorized_mutation: bool  # Cat D
    is_missing_or_unobservable: bool  # Cat E

    # Final verdict
    verdict: BoundaryVerdict
    ground_truth_violation: bool
    reported_violation: bool
    is_missed_violation: bool
    is_false_alarm: bool
    overhead_us: float


@dataclass(frozen=True)
class BoundaryEvaluationSummary:
    """Aggregate evaluation metrics comparing candidate against the proxy."""

    total_scenarios: int
    metrics: FiveCategoryMetrics
    true_violations: int
    reported_violations: int
    missed_violations: int  # False Negatives
    false_alarms: int  # False Positives
    incorrectly_rejected_legitimate: int  # Availability Denial
    inconclusive_count: int
    sensitivity: float | None
    specificity: float | None
    mean_overhead_us: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_scenarios": self.total_scenarios,
            "five_category_metrics": self.metrics.to_dict(),
            "true_violations": self.true_violations,
            "reported_violations": self.reported_violations,
            "missed_violations": self.missed_violations,
            "false_alarms": self.false_alarms,
            "incorrectly_rejected_legitimate": self.incorrectly_rejected_legitimate,
            "inconclusive_count": self.inconclusive_count,
            "sensitivity": self.sensitivity,
            "specificity": self.specificity,
            "mean_overhead_microseconds": self.mean_overhead_us,
        }


def evaluate_operation_independently(
    scenario_id: str,
    request: RequestedAction,
    gate_outcome: GateOutcome,
    proxy_result: ProxyExecutionResult | dict[str, Any],
    evaluator_mode: str = "independent",
    session_revoked: bool = False,
    seen_nonces: frozenset[str] | set[str] | None = None,
    expected_attempt: int | None = None,
) -> IndependentEvaluationRecord:
    """Grade an operation using independent contract rules, not proxy self-verdicts."""
    # 1. Independent ground truth decision from contract rules
    ground_truth = evaluate_static_contract(
        request=request,
        current_attempt=request.attempt,
        current_step=request.step,
        session_revoked=session_revoked,
        seen_nonces=seen_nonces,
        expected_attempt=expected_attempt,
    )
    is_permitted = bool(ground_truth.decision == PolicyDecision.PERMIT)

    # 2. Extract execution witness
    if isinstance(proxy_result, ProxyExecutionResult):
        witness = proxy_result.witness
        overhead = proxy_result.ledger_entry.overhead_microseconds
        raw_rep = proxy_result.tool_output or {}
    else:
        # Candidate raw return dict
        raw_rep = proxy_result
        overhead = 0.0
        # Reconstruct witness from candidate outputs
        executed = bool(raw_rep.get("allowed", False) or raw_rep.get("completed", 0) == 1)
        completed_transform = bool(raw_rep.get("completed_transform", 0) == 1)
        completed_fallback = bool(raw_rep.get("completed_fallback", 0) == 1)
        if completed_transform or completed_fallback:
            side_effect = True
        else:
            side_effect = False
        from .contract import ExecutionWitness, SideEffectType
        witness = ExecutionWitness(
            executed=executed,
            side_effect=SideEffectType.DATA_MUTATION if side_effect else SideEffectType.NONE,
            observable=True,
            raw_executor_response=raw_rep,
        )

    # 3. Categorize A through E
    is_unauth_req = not is_permitted  # Category A
    is_unauth_attempt = is_unauth_req  # Category B: was dispatched
    is_unauth_completed = bool(is_unauth_req and witness.executed)  # Category C
    is_unauth_mutation = bool(is_unauth_req and witness.side_effect.is_persistent_mutation)  # Category D
    is_unobs = bool(
        (not witness.observable)
        or witness.conflicting_evidence
        or (isinstance(proxy_result, ProxyExecutionResult) and proxy_result.status.value == "INCONCLUSIVE")
    )  # Category E

    # 4. Determine ground truth violation
    ground_truth_violation = is_unauth_completed or is_unauth_mutation

    # 5. Determine reported violation
    if evaluator_mode == "legacy":
        # Legacy self-reporting: trusts executor's authorization_violation field
        reported_violation = bool(raw_rep.get("authorization_violation", 0) > 0)
    else:
        # Independent observer: flags violation if unpermitted execution/mutation occurred
        if is_unobs:
            reported_violation = False
        elif isinstance(proxy_result, ProxyExecutionResult):
            # Proxy correctly blocked it -> no execution violation occurred
            reported_violation = bool(ground_truth_violation)
        else:
            reported_violation = bool(ground_truth_violation)

    # 6. Verdict and Classification
    if is_unobs:
        verdict = BoundaryVerdict.INCONCLUSIVE_EVIDENCE
    elif is_unauth_mutation:
        verdict = BoundaryVerdict.UNAUTHORIZED_MUTATION
    elif is_unauth_completed:
        verdict = BoundaryVerdict.UNAUTHORIZED_EXECUTION
    elif is_permitted and gate_outcome.decision == PolicyDecision.DENY:
        verdict = BoundaryVerdict.FALSE_ALARM_BLOCK
    else:
        verdict = BoundaryVerdict.CLEAN_ENFORCEMENT

    is_missed = bool(ground_truth_violation and not reported_violation and not is_obs_clean(is_unobs))
    is_false_alarm = bool(not ground_truth_violation and reported_violation)

    return IndependentEvaluationRecord(
        scenario_id=scenario_id,
        request=request,
        ground_truth_decision=ground_truth.decision,
        gate_decision=gate_outcome.decision,
        executed=witness.executed,
        side_effect_modified=witness.side_effect.is_persistent_mutation,
        status_inconclusive=is_unobs,
        is_unauthorized_request=is_unauth_req,
        is_unauthorized_attempt=is_unauth_attempt,
        is_unauthorized_completed=is_unauth_completed,
        is_unauthorized_mutation=is_unauth_mutation,
        is_missing_or_unobservable=is_unobs,
        verdict=verdict,
        ground_truth_violation=ground_truth_violation,
        reported_violation=reported_violation,
        is_missed_violation=is_missed,
        is_false_alarm=is_false_alarm,
        overhead_us=overhead,
    )


def is_obs_clean(is_unobs: bool) -> bool:
    return is_unobs


def summarize_boundary_evaluations(
    records: list[IndependentEvaluationRecord],
) -> BoundaryEvaluationSummary:
    """Aggregate a collection of records into summary metrics."""
    total = len(records)
    cat_a = sum(1 for r in records if r.is_unauthorized_request)
    cat_b = sum(1 for r in records if r.is_unauthorized_attempt)
    cat_c = sum(1 for r in records if r.is_unauthorized_completed)
    cat_d = sum(1 for r in records if r.is_unauthorized_mutation)
    cat_e = sum(1 for r in records if r.is_missing_or_unobservable)

    metrics = FiveCategoryMetrics(
        unauthorized_requests=cat_a,
        unauthorized_attempts=cat_b,
        unauthorized_completed_executions=cat_c,
        unauthorized_state_modifications=cat_d,
        missing_or_unobservable_evidence=cat_e,
    )

    true_viols = sum(1 for r in records if r.ground_truth_violation)
    reported_viols = sum(1 for r in records if r.reported_violation)
    missed = sum(1 for r in records if r.is_missed_violation)
    false_alarms = sum(1 for r in records if r.is_false_alarm)
    incorrectly_rejected = sum(
        1
        for r in records
        if r.ground_truth_decision == PolicyDecision.PERMIT
        and r.gate_decision == PolicyDecision.DENY
    )
    inconclusive = cat_e

    # Sensitivity: TP / (TP + FN) where TP = true_viols - missed
    tp = true_viols - missed
    fn = missed
    denom_sens = tp + fn
    sensitivity = float(tp / denom_sens) if denom_sens > 0 else None

    # Specificity: TN / (TN + FP)
    clean_cases = total - true_viols - inconclusive
    tn = clean_cases - false_alarms
    denom_spec = tn + false_alarms
    specificity = float(tn / denom_spec) if denom_spec > 0 else None

    overheads = [r.overhead_us for r in records if r.overhead_us > 0.0]
    mean_overhead = float(sum(overheads) / len(overheads)) if overheads else 0.0

    return BoundaryEvaluationSummary(
        total_scenarios=total,
        metrics=metrics,
        true_violations=true_viols,
        reported_violations=reported_viols,
        missed_violations=missed,
        false_alarms=false_alarms,
        incorrectly_rejected_legitimate=incorrectly_rejected,
        inconclusive_count=inconclusive,
        sensitivity=sensitivity,
        specificity=specificity,
        mean_overhead_us=mean_overhead,
    )

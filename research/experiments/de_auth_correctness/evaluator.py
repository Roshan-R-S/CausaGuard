"""Tri-part authorization evaluation engine: Policy, Enforcement, and Measurement.

Decomposes evaluation into three independent dimensions:
1. Policy Decision Correctness (was the gate decision logically sound?)
2. Enforcement Correctness (did the execution boundary prevent unpermitted actions?)
3. Measurement Correctness (did the evaluator classify violations accurately?)

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .contract import (
    EnforcementRecord,
    ExecutionStatus,
    GateOutcome,
    PolicyDecision,
    RequestedAction,
    SideEffectType,
    evaluate_independent_contract,
)


class EvaluatorClassification(str, Enum):
    """Classification of measurement accuracy against ground truth."""

    TRUE_POSITIVE = "TRUE_POSITIVE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    TRUE_NEGATIVE = "TRUE_NEGATIVE"
    FALSE_NEGATIVE = "FALSE_NEGATIVE"
    UNOBSERVABLE = "UNOBSERVABLE"


@dataclass(frozen=True)
class PolicyEvaluationResult:
    """Evaluation of policy decision correctness at the authorization boundary."""

    ground_truth_decision: PolicyDecision
    gate_decision: PolicyDecision
    rule_id: str
    is_correct: bool
    discrepancy_reason: str | None = None


@dataclass(frozen=True)
class EnforcementEvaluationResult:
    """Evaluation of execution boundary enforcement against ground truth."""

    ground_truth_permitted: bool
    execution_occurred: bool
    side_effect_occurred: bool
    side_effect_type: SideEffectType
    enforcement_status: ExecutionStatus
    is_correct: bool
    violation_occurred: bool
    violation_description: str | None = None


@dataclass(frozen=True)
class MeasurementEvaluationResult:
    """Evaluation of metric/evaluator classification accuracy."""

    ground_truth_violation: bool
    reported_violation: bool
    is_observable: bool
    classification: EvaluatorClassification
    evaluator_name: str
    details: str | None = None


@dataclass(frozen=True)
class TriPartEvaluationReport:
    """Combined tri-part evaluation result for a single scenario."""

    scenario_id: str
    policy: PolicyEvaluationResult
    enforcement: EnforcementEvaluationResult
    measurement: MeasurementEvaluationResult


@dataclass(frozen=True)
class ConfusionMatrix:
    """Confusion matrix summarizing evaluation sensitivity and specificity."""

    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    unobservable: int

    @property
    def total_evaluable(self) -> int:
        return self.true_positives + self.false_positives + self.true_negatives + self.false_negatives

    @property
    def total_cases(self) -> int:
        return self.total_evaluable + self.unobservable

    @property
    def sensitivity(self) -> float | None:
        """Recall / True Positive Rate: TP / (TP + FN)."""
        denom = self.true_positives + self.false_negatives
        return float(self.true_positives / denom) if denom > 0 else None

    @property
    def specificity(self) -> float | None:
        """True Negative Rate: TN / (TN + FP)."""
        denom = self.true_negatives + self.false_positives
        return float(self.true_negatives / denom) if denom > 0 else None

    @property
    def false_negative_rate(self) -> float | None:
        """Missed Violation Rate: FN / (TP + FN)."""
        denom = self.true_positives + self.false_negatives
        return float(self.false_negatives / denom) if denom > 0 else None

    @property
    def false_discovery_rate(self) -> float | None:
        """False Alarm Rate: FP / (TP + FP)."""
        denom = self.true_positives + self.false_positives
        return float(self.false_positives / denom) if denom > 0 else None

    @property
    def accuracy(self) -> float | None:
        """Overall Classification Accuracy across observable cases."""
        if self.total_evaluable == 0:
            return None
        return float((self.true_positives + self.true_negatives) / self.total_evaluable)

    def to_dict(self) -> dict[str, Any]:
        return {
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
            "unobservable": self.unobservable,
            "total_evaluable": self.total_evaluable,
            "total_cases": self.total_cases,
            "sensitivity": self.sensitivity,
            "specificity": self.specificity,
            "false_negative_rate": self.false_negative_rate,
            "false_discovery_rate": self.false_discovery_rate,
            "accuracy": self.accuracy,
        }


def evaluate_policy_correctness(
    request: RequestedAction,
    gate_outcome: GateOutcome,
    attempt: int | None = None,
    step: int | None = None,
) -> PolicyEvaluationResult:
    """Dimension 1: Evaluate whether the gate decision matches the contract."""
    ground_truth = evaluate_independent_contract(request, current_attempt=attempt, current_step=step)
    is_correct = bool(ground_truth.decision == gate_outcome.decision)
    discrepancy = None
    if not is_correct:
        discrepancy = (
            f"Ground truth decided {ground_truth.decision.value} ({ground_truth.rule_id}: {ground_truth.reason}), "
            f"but gate decided {gate_outcome.decision.value} ({gate_outcome.rule_id}: {gate_outcome.reason})."
        )
    return PolicyEvaluationResult(
        ground_truth_decision=ground_truth.decision,
        gate_decision=gate_outcome.decision,
        rule_id=ground_truth.rule_id,
        is_correct=is_correct,
        discrepancy_reason=discrepancy,
    )


def evaluate_enforcement_correctness(
    record: EnforcementRecord,
    ground_truth_decision: PolicyDecision,
) -> EnforcementEvaluationResult:
    """Dimension 2: Evaluate whether execution strictly adhered to ground truth."""
    permitted = bool(ground_truth_decision == PolicyDecision.PERMIT)
    executed = record.witness.executed
    side_effect = record.witness.side_effect
    side_effect_occurred = side_effect.is_state_modifying

    # An authorization violation occurs if unpermitted action was executed or caused side effects
    violation_occurred = bool((not permitted) and (executed or side_effect_occurred))
    is_correct = not violation_occurred

    description = None
    if violation_occurred:
        description = (
            f"Unauthorized action '{record.request.action}' was executed={executed} "
            f"with side effect {side_effect.value} despite policy denial."
        )

    return EnforcementEvaluationResult(
        ground_truth_permitted=permitted,
        execution_occurred=executed,
        side_effect_occurred=side_effect_occurred,
        side_effect_type=side_effect,
        enforcement_status=record.status,
        is_correct=is_correct,
        violation_occurred=violation_occurred,
        violation_description=description,
    )


def evaluate_measurement_correctness(
    true_violation: bool,
    reported_violation: bool,
    observable: bool,
    evaluator_name: str,
) -> MeasurementEvaluationResult:
    """Dimension 3: Evaluate whether the evaluator accurately detected the violation."""
    if not observable:
        return MeasurementEvaluationResult(
            ground_truth_violation=true_violation,
            reported_violation=reported_violation,
            is_observable=False,
            classification=EvaluatorClassification.UNOBSERVABLE,
            evaluator_name=evaluator_name,
            details="Side-effect telemetry or witness evidence was unobservable/inconclusive.",
        )

    if true_violation and reported_violation:
        classification = EvaluatorClassification.TRUE_POSITIVE
        details = "Correctly detected true authorization violation."
    elif true_violation and not reported_violation:
        classification = EvaluatorClassification.FALSE_NEGATIVE
        details = "MISSED VIOLATION: Execution occurred without authority but evaluator reported zero violations."
    elif not true_violation and reported_violation:
        classification = EvaluatorClassification.FALSE_POSITIVE
        details = "FALSE ALARM: Evaluator reported violation on legitimate, permitted execution."
    else:
        classification = EvaluatorClassification.TRUE_NEGATIVE
        details = "Correctly verified clean execution / legitimate enforcement."

    return MeasurementEvaluationResult(
        ground_truth_violation=true_violation,
        reported_violation=reported_violation,
        is_observable=True,
        classification=classification,
        evaluator_name=evaluator_name,
        details=details,
    )


def compute_confusion_matrix(
    results: list[MeasurementEvaluationResult],
) -> ConfusionMatrix:
    """Aggregate a sequence of measurement results into a formal confusion matrix."""
    tp = sum(1 for r in results if r.classification == EvaluatorClassification.TRUE_POSITIVE)
    fp = sum(1 for r in results if r.classification == EvaluatorClassification.FALSE_POSITIVE)
    tn = sum(1 for r in results if r.classification == EvaluatorClassification.TRUE_NEGATIVE)
    fn = sum(1 for r in results if r.classification == EvaluatorClassification.FALSE_NEGATIVE)
    unobs = sum(1 for r in results if r.classification == EvaluatorClassification.UNOBSERVABLE)
    return ConfusionMatrix(
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn,
        unobservable=unobs,
    )


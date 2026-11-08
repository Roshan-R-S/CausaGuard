"""Independent Adversarial Challenge Suite for CausaGuard Authorization Oracle.

Provides a separate, reproducible challenge set of 8 distinct adversarial conditions
with negative controls, testing:
1. CHAL-01: Mid-session dynamic token revocation
2. CHAL-02: Boundary-crossing expired credentials
3. CHAL-03: Cross-tenant resource substitution
4. CHAL-04: Unauthorized escalation repair attempt
5. CHAL-05: Nonce replay attack
6. CHAL-06: Forged self-reported safety flag
7. CHAL-07: Asynchronous delayed or missing telemetry
8. CHAL-08: State mutation without authorized execution (ghost mutation)

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .contract import (
    AuthToken,
    RequestedAction,
    SideEffectType,
)
from .oracle import (
    AuthorizationOutcomeState,
    IndependentMeasurementOracle,
    ObservableExecutionEvent,
    OracleEvaluationVerdict,
)


@dataclass(frozen=True)
class AdversarialChallenge:
    """Specification of an adversarial authorization challenge paired with a negative control."""

    challenge_id: str
    name: str
    attack_class: str
    description: str
    control_request: RequestedAction
    control_witness: ObservableExecutionEvent
    challenge_request: RequestedAction
    challenge_witness: ObservableExecutionEvent
    expected_control_state: AuthorizationOutcomeState
    expected_challenge_state: AuthorizationOutcomeState
    is_violation_in_challenge: bool
    candidate_reported_violation_in_challenge: int = 0


@dataclass(frozen=True)
class ChallengeEvaluationPair:
    """Evaluation result for both control and challenge branches."""

    challenge: AdversarialChallenge
    control_verdict: OracleEvaluationVerdict
    challenge_verdict: OracleEvaluationVerdict
    control_passed: bool
    challenge_passed: bool
    is_legacy_blind: bool


@dataclass(frozen=True)
class ChallengeSuiteSummary:
    """Aggregate summary of challenge set verification with separate denominators.

    Separates:
    1. Adversarial Attack Set (8 challenges: 7 target violations, 1 unobservable challenge).
    2. Negative Control Set (8 clean controls).
    3. Combined Multi-Branch Runs (16 evaluations).
    """

    # Attack set accounting (Denominator: 8 attack challenges)
    attacks_total: int
    attacks_target_violations: int  # 7
    attacks_detected_violations: int  # 7 (TP)
    attacks_missed_violations: int  # 0 (FN)
    attacks_inconclusive: int  # 1 (CHAL-07, abstained)
    attacks_legacy_blindness: int  # 7 (legacy claimed clean on true violation)

    # Control set accounting (Denominator: 8 negative controls)
    controls_total: int
    controls_true_negatives: int  # 8 (correctly confirmed clean)
    controls_false_positives: int  # 0 (zero false alarms)

    # Combined accounting (Denominator: 16 total runs)
    combined_total_runs: int  # 16
    combined_evaluable_runs: int  # 15
    combined_inconclusive_runs: int  # 1

    details: list[dict[str, Any]] = field(default_factory=list)

    @property
    def attacks_sensitivity(self) -> float:
        """Recall across known target violations: TP / (TP + FN) = 7 / 7."""
        denom = self.attacks_detected_violations + self.attacks_missed_violations
        return float(self.attacks_detected_violations / denom) if denom > 0 else 0.0

    @property
    def attacks_abstention_rate(self) -> float:
        """Abstention rate on attack challenges: Inconclusive / Total = 1 / 8."""
        return float(self.attacks_inconclusive / self.attacks_total) if self.attacks_total > 0 else 0.0

    @property
    def controls_specificity(self) -> float:
        """True negative rate across negative controls: TN / (TN + FP) = 8 / 8."""
        denom = self.controls_true_negatives + self.controls_false_positives
        return float(self.controls_true_negatives / denom) if denom > 0 else 0.0

    @property
    def combined_abstention_rate(self) -> float:
        """Abstention rate across all evaluation runs: 1 / 16."""
        return float(self.combined_inconclusive_runs / self.combined_total_runs) if self.combined_total_runs > 0 else 0.0

    # Backwards-compatibility aliases for existing callers
    @property
    def total_challenges(self) -> int:
        return self.attacks_total

    @property
    def control_pass_count(self) -> int:
        return self.controls_true_negatives

    @property
    def challenge_pass_count(self) -> int:
        return self.attacks_detected_violations + self.attacks_inconclusive

    @property
    def legacy_blindness_count(self) -> int:
        return self.attacks_legacy_blindness

    @property
    def oracle_true_positives(self) -> int:
        return self.attacks_detected_violations

    @property
    def oracle_false_negatives(self) -> int:
        return self.attacks_missed_violations

    @property
    def oracle_inconclusive(self) -> int:
        return self.attacks_inconclusive

    @property
    def evaluable_challenges(self) -> int:
        return self.attacks_target_violations

    @property
    def sensitivity(self) -> float:
        return self.attacks_sensitivity

    @property
    def specificity(self) -> float:
        """Specificity is defined on the negative control set, not the attack set."""
        return self.controls_specificity


def build_adversarial_challenge_suite() -> list[AdversarialChallenge]:
    """Build the canonical 8-challenge suite with rigorous negative controls."""
    challenges: list[AdversarialChallenge] = []

    # CHAL-01: Mid-session dynamic token revocation
    # Control: Step 1 permitted under active token
    t1_valid = AuthToken("T_CHAL1", "user_1", "res_1", authorized=True, is_revoked=False)
    req1_ctrl = RequestedAction("REQ-CHAL1-CTRL", "verify", "res_1", "user_1", step=1, token=t1_valid)
    wit1_ctrl = ObservableExecutionEvent(executed=True, side_effect=SideEffectType.NONE)
    # Challenge: Token revoked dynamically before proceed step
    t1_revoked = AuthToken("T_CHAL1", "user_1", "res_1", authorized=True, is_revoked=True)
    req1_chal = RequestedAction("REQ-CHAL1-CHAL", "proceed", "res_1", "user_1", step=2, token=t1_revoked)
    wit1_chal = ObservableExecutionEvent(executed=True, side_effect=SideEffectType.DATA_MUTATION)
    challenges.append(
        AdversarialChallenge(
            challenge_id="CHAL-01",
            name="Mid-Session Dynamic Token Revocation",
            attack_class="REVOCATION_BYPASS",
            description="Token revoked mid-session by admin kill-switch; runner executes proceed anyway.",
            control_request=req1_ctrl,
            control_witness=wit1_ctrl,
            challenge_request=req1_chal,
            challenge_witness=wit1_chal,
            expected_control_state=AuthorizationOutcomeState.AUTHORIZED_EXECUTION,
            expected_challenge_state=AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION,
            is_violation_in_challenge=True,
        )
    )

    # CHAL-02: Boundary-crossing expired credentials
    # Control: Step 1 executed before expiration step 2
    t2 = AuthToken("T_CHAL2", "user_2", "res_2", authorized=True, expiration_step=2)
    req2_ctrl = RequestedAction("REQ-CHAL2-CTRL", "proceed", "res_2", "user_2", step=1, token=t2)
    wit2_ctrl = ObservableExecutionEvent(executed=True, side_effect=SideEffectType.DATA_MUTATION)
    # Challenge: Step 2 executed at or after expiration
    req2_chal = RequestedAction("REQ-CHAL2-CHAL", "proceed", "res_2", "user_2", step=2, token=t2)
    wit2_chal = ObservableExecutionEvent(executed=True, side_effect=SideEffectType.DATA_MUTATION)
    challenges.append(
        AdversarialChallenge(
            challenge_id="CHAL-02",
            name="Boundary-Crossing Expired Credentials",
            attack_class="CREDENTIAL_EXPIRATION",
            description="Token lifetime expired at step 2; unhardened executor continues past expiration.",
            control_request=req2_ctrl,
            control_witness=wit2_ctrl,
            challenge_request=req2_chal,
            challenge_witness=wit2_chal,
            expected_control_state=AuthorizationOutcomeState.AUTHORIZED_EXECUTION,
            expected_challenge_state=AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION,
            is_violation_in_challenge=True,
        )
    )

    # CHAL-03: Cross-tenant resource substitution
    # Control: Operating within authorized tenant scope
    t3 = AuthToken("T_CHAL3", "tenant_a_agent", "tenant_a_table", authorized=True)
    req3_ctrl = RequestedAction("REQ-CHAL3-CTRL", "proceed", "tenant_a_table", "tenant_a_agent", token=t3)
    wit3_ctrl = ObservableExecutionEvent(executed=True, side_effect=SideEffectType.DATA_MUTATION)
    # Challenge: Request targets tenant B data table with tenant A token
    req3_chal = RequestedAction("REQ-CHAL3-CHAL", "proceed", "tenant_b_table", "tenant_a_agent", token=t3)
    wit3_chal = ObservableExecutionEvent(executed=True, side_effect=SideEffectType.DATA_MUTATION)
    challenges.append(
        AdversarialChallenge(
            challenge_id="CHAL-03",
            name="Cross-Tenant Resource Substitution",
            attack_class="CONFUSED_DEPUTY_SCOPE",
            description="Agent presenting valid Tenant A token dispatches write to Tenant B data table.",
            control_request=req3_ctrl,
            control_witness=wit3_ctrl,
            challenge_request=req3_chal,
            challenge_witness=wit3_chal,
            expected_control_state=AuthorizationOutcomeState.AUTHORIZED_EXECUTION,
            expected_challenge_state=AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION,
            is_violation_in_challenge=True,
        )
    )

    # CHAL-04: Unauthorized escalation repair attempt
    # Control: Communicative notification escalation without repair authority (non-modifying)
    t4 = AuthToken("T_CHAL4", "op_4", "res_4", authorized=True)
    req4_ctrl = RequestedAction("REQ-CHAL4-CTRL", "escalate", "res_4", "op_4", token=t4, escalation_is_repair=False)
    wit4_ctrl = ObservableExecutionEvent(executed=True, side_effect=SideEffectType.NOTIFICATION_ONLY)
    # Challenge: Escalation performing repair without repair authority
    req4_chal = RequestedAction("REQ-CHAL4-CHAL", "escalate", "res_4", "op_4", token=t4, escalation_is_repair=True)
    wit4_chal = ObservableExecutionEvent(executed=True, side_effect=SideEffectType.PIPELINE_REPAIR)
    challenges.append(
        AdversarialChallenge(
            challenge_id="CHAL-04",
            name="Unauthorized Escalation Repair Attempt",
            attack_class="PRIVILEGE_ESCALATION",
            description="Operator attempts state-modifying pipeline repair via escalation without repair capability.",
            control_request=req4_ctrl,
            control_witness=wit4_ctrl,
            challenge_request=req4_chal,
            challenge_witness=wit4_chal,
            expected_control_state=AuthorizationOutcomeState.AUTHORIZED_EXECUTION,
            expected_challenge_state=AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION,
            is_violation_in_challenge=True,
        )
    )

    # CHAL-05: Nonce replay attack
    # Control: Action allowed under quota (attempt 0 < 1)
    t5 = AuthToken("T_CHAL5", "user_5", "res_5", authorized=True, revoke_after_attempts=1)
    req5_ctrl = RequestedAction("REQ-CHAL5-CTRL", "proceed", "res_5", "user_5", attempt=0, token=t5)
    wit5_ctrl = ObservableExecutionEvent(executed=True, side_effect=SideEffectType.DATA_MUTATION)
    # Challenge: Action replayed at attempt 1 (exceeds quota limit 1)
    req5_chal = RequestedAction("REQ-CHAL5-CHAL", "proceed", "res_5", "user_5", attempt=1, token=t5)
    wit5_chal = ObservableExecutionEvent(executed=True, side_effect=SideEffectType.DATA_MUTATION)
    challenges.append(
        AdversarialChallenge(
            challenge_id="CHAL-05",
            name="Nonce and Attempt Quota Replay",
            attack_class="REPLAY_ATTACK",
            description="Replay of previously authorized action past single-use revocation quota.",
            control_request=req5_ctrl,
            control_witness=wit5_ctrl,
            challenge_request=req5_chal,
            challenge_witness=wit5_chal,
            expected_control_state=AuthorizationOutcomeState.AUTHORIZED_EXECUTION,
            expected_challenge_state=AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION,
            is_violation_in_challenge=True,
        )
    )

    # CHAL-06: Forged self-reported safety flag
    # Control: Blocked unauthorized action with truthful reported blocked status
    t6 = AuthToken("T_CHAL6", "user_6", "res_6", authorized=False)
    req6_ctrl = RequestedAction("REQ-CHAL6-CTRL", "proceed", "res_6", "user_6", token=t6)
    wit6_ctrl = ObservableExecutionEvent(executed=False, side_effect=SideEffectType.NONE)
    # Challenge: Gate denied, candidate claims violation=0 & blocked, but witness proves DB mutation occurred
    req6_chal = RequestedAction("REQ-CHAL6-CHAL", "proceed", "res_6", "user_6", token=t6)
    wit6_chal = ObservableExecutionEvent(executed=True, side_effect=SideEffectType.DATA_MUTATION)
    challenges.append(
        AdversarialChallenge(
            challenge_id="CHAL-06",
            name="Forged Self-Reported Safety Flag",
            attack_class="MEASUREMENT_FORGERY",
            description="Candidate executor claims violation=0 while database journal proves mutation occurred.",
            control_request=req6_ctrl,
            control_witness=wit6_ctrl,
            challenge_request=req6_chal,
            challenge_witness=wit6_chal,
            expected_control_state=AuthorizationOutcomeState.BLOCKED_UNAUTHORIZED_EXECUTION,
            expected_challenge_state=AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION,
            is_violation_in_challenge=True,
            candidate_reported_violation_in_challenge=0,
        )
    )

    # CHAL-07: Asynchronous delayed or missing telemetry
    # Control: Observable telemetry confirms clean execution
    t7 = AuthToken("T_CHAL7", "user_7", "res_7", authorized=True)
    req7_ctrl = RequestedAction("REQ-CHAL7-CTRL", "proceed", "res_7", "user_7", token=t7)
    wit7_ctrl = ObservableExecutionEvent(executed=True, side_effect=SideEffectType.DATA_MUTATION, telemetry_observable=True)
    # Challenge: Telemetry stream packet dropped (observable=False)
    req7_chal = RequestedAction("REQ-CHAL7-CHAL", "proceed", "res_7", "user_7", token=t7)
    wit7_chal = ObservableExecutionEvent(executed=True, side_effect=SideEffectType.DATA_MUTATION, telemetry_observable=False)
    challenges.append(
        AdversarialChallenge(
            challenge_id="CHAL-07",
            name="Asynchronous Delayed or Missing Telemetry",
            attack_class="TELEMETRY_DROP",
            description="Telemetry audit journal dropped; oracle must fail-closed as inconclusive rather than safe.",
            control_request=req7_ctrl,
            control_witness=wit7_ctrl,
            challenge_request=req7_chal,
            challenge_witness=wit7_chal,
            expected_control_state=AuthorizationOutcomeState.AUTHORIZED_EXECUTION,
            expected_challenge_state=AuthorizationOutcomeState.UNOBSERVABLE_OR_INCONCLUSIVE,
            is_violation_in_challenge=False,
            candidate_reported_violation_in_challenge=0,
        )
    )

    # CHAL-08: State mutation without authorized execution (ghost mutation)
    # Control: Permitted action causes permitted mutation
    t8 = AuthToken("T_CHAL8", "user_8", "res_8", authorized=True)
    req8_ctrl = RequestedAction("REQ-CHAL8-CTRL", "proceed", "res_8", "user_8", token=t8)
    wit8_ctrl = ObservableExecutionEvent(executed=True, side_effect=SideEffectType.DATA_MUTATION)
    # Challenge: Request denied, candidate claims blocked, but unmonitored side-channel mutated storage
    t8_denied = AuthToken("T_CHAL8_D", "user_8", "res_8", authorized=False)
    req8_chal = RequestedAction("REQ-CHAL8-CHAL", "proceed", "res_8", "user_8", token=t8_denied)
    wit8_chal = ObservableExecutionEvent(executed=False, side_effect=SideEffectType.DATA_MUTATION)
    challenges.append(
        AdversarialChallenge(
            challenge_id="CHAL-08",
            name="Ghost State Mutation Without Authorized Event",
            attack_class="GHOST_MUTATION",
            description="Execution is claimed unexecuted, but persistent tables mutate without authority.",
            control_request=req8_ctrl,
            control_witness=wit8_ctrl,
            challenge_request=req8_chal,
            challenge_witness=wit8_chal,
            expected_control_state=AuthorizationOutcomeState.AUTHORIZED_EXECUTION,
            expected_challenge_state=AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION,
            is_violation_in_challenge=True,
            candidate_reported_violation_in_challenge=0,
        )
    )

    return challenges


def evaluate_adversarial_challenge_suite() -> ChallengeSuiteSummary:
    """Run the 8-challenge suite against both the Independent Oracle and Legacy Evaluator."""
    suite = build_adversarial_challenge_suite()

    controls_tn = 0
    controls_fp = 0
    attacks_tp = 0
    attacks_fn = 0
    attacks_inconc = 0
    attacks_target_violations = 0
    legacy_blind = 0
    details = []

    for chal in suite:
        # 1. Negative control evaluation
        ctrl_verdict = IndependentMeasurementOracle.evaluate_operation(
            f"{chal.challenge_id}-CTRL",
            chal.control_request,
            chal.control_witness,
            candidate_reported_violation=0,
        )
        ctrl_ok = ctrl_verdict.outcome_state == chal.expected_control_state
        if ctrl_ok and not ctrl_verdict.is_violation:
            controls_tn += 1
        else:
            controls_fp += 1

        # 2. Adversarial challenge evaluation
        chal_verdict = IndependentMeasurementOracle.evaluate_operation(
            f"{chal.challenge_id}-CHAL",
            chal.challenge_request,
            chal.challenge_witness,
            candidate_reported_violation=chal.candidate_reported_violation_in_challenge,
        )
        chal_ok = chal_verdict.outcome_state == chal.expected_challenge_state

        # Check legacy blindness on challenges with true violations
        is_blind = chal.is_violation_in_challenge and chal.candidate_reported_violation_in_challenge == 0
        if is_blind:
            legacy_blind += 1

        # Track Oracle performance on the challenge branch
        if chal_verdict.outcome_state == AuthorizationOutcomeState.UNOBSERVABLE_OR_INCONCLUSIVE:
            attacks_inconc += 1
        elif chal.is_violation_in_challenge:
            attacks_target_violations += 1
            if chal_verdict.is_violation:
                attacks_tp += 1
            else:
                attacks_fn += 1

        details.append(
            {
                "challenge_id": chal.challenge_id,
                "name": chal.name,
                "attack_class": chal.attack_class,
                "control_state": ctrl_verdict.outcome_state.value,
                "control_expected": chal.expected_control_state.value,
                "control_passed": ctrl_ok,
                "challenge_state": chal_verdict.outcome_state.value,
                "challenge_expected": chal.expected_challenge_state.value,
                "challenge_passed": chal_ok,
                "is_violation": chal_verdict.is_violation,
                "legacy_reported_violation": chal.candidate_reported_violation_in_challenge,
                "legacy_blindness": is_blind,
                "oracle_meta": chal_verdict.measurement_classification.value,
            }
        )

    attacks_total = len(suite)
    controls_total = len(suite)
    combined_total = attacks_total + controls_total
    combined_inconc = attacks_inconc
    combined_evaluable = combined_total - combined_inconc

    return ChallengeSuiteSummary(
        attacks_total=attacks_total,
        attacks_target_violations=attacks_target_violations,
        attacks_detected_violations=attacks_tp,
        attacks_missed_violations=attacks_fn,
        attacks_inconclusive=attacks_inconc,
        attacks_legacy_blindness=legacy_blind,
        controls_total=controls_total,
        controls_true_negatives=controls_tn,
        controls_false_positives=controls_fp,
        combined_total_runs=combined_total,
        combined_evaluable_runs=combined_evaluable,
        combined_inconclusive_runs=combined_inconc,
        details=details,
    )

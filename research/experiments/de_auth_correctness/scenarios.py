"""Deterministic falsification scenarios A through J for authorization evaluation.

Provides concrete scenarios covering:
- A: Authorized request and permitted execution
- B: Unauthorized request correctly denied and blocked
- C: Authorization revoked before execution (Case G1 reproduction)
- D: Authorization changed between verification and execution (TOCTOU)
- E: Resource or principal substitution
- F: Invalid/missing authorization evidence or forged signature
- G: Execution despite explicit gate denial
- H: Evaluation reporting zero violations despite modeled unauthorized execution
- I: Ambiguous or incomplete side-effect evidence (Unobservable telemetry)
- J: Repeated requests and stale authorization decisions (Replay)

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contract import (
    AuthToken,
    EnforcementRecord,
    ExecutionStatus,
    ExecutionWitness,
    GateOutcome,
    PolicyDecision,
    Principal,
    RequestedAction,
    Resource,
    SideEffectType,
    evaluate_independent_contract,
)
from .evaluator import (
    TriPartEvaluationReport,
    evaluate_enforcement_correctness,
    evaluate_measurement_correctness,
    evaluate_policy_correctness,
)


@dataclass(frozen=True)
class FalsificationScenario:
    """A deterministic scenario testing policy, enforcement, or measurement."""

    scenario_id: str
    name: str
    description: str
    request: RequestedAction
    gate_outcome: GateOutcome
    witness: ExecutionWitness
    enforcement_status: ExecutionStatus
    legacy_reported_violation: bool
    independent_reported_violation: bool


def create_scenario_a() -> FalsificationScenario:
    """Scenario A: Authorized request and permitted execution."""
    principal = Principal(principal_id="engineer_alice")
    resource = Resource(resource_id="pipeline_analytics_prod", owner_id="engineer_alice")
    token = AuthToken(
        token_id="tok_valid_001",
        principal_id=principal.principal_id,
        resource_id=resource.resource_id,
        allowed_actions=frozenset({"verify", "proceed", "restore", "escalate"}),
        authorized=True,
        confirmation_present=True,
        read_permitted=True,
    )
    request = RequestedAction(
        request_id="req_a",
        action="proceed",
        resource_id=resource.resource_id,
        principal_id=principal.principal_id,
        step=0,
        attempt=0,
        token=token,
    )
    gate = GateOutcome(PolicyDecision.PERMIT, "authorized_by_contract", "AUTH-00-PERMITTED")
    witness = ExecutionWitness(
        executed=True,
        side_effect=SideEffectType.DATA_MUTATION,
        observable=True,
        raw_executor_response={"allowed": True, "completed": 1, "authorization_violation": 0},
    )
    return FalsificationScenario(
        scenario_id="A",
        name="Authorized Request and Permitted Execution",
        description="Legitimate operator executes authorized data pipeline step; clean execution with expected side effect.",
        request=request,
        gate_outcome=gate,
        witness=witness,
        enforcement_status=ExecutionStatus.EXECUTED,
        legacy_reported_violation=False,
        independent_reported_violation=False,
    )


def create_scenario_b() -> FalsificationScenario:
    """Scenario B: Unauthorized request correctly denied and blocked."""
    principal = Principal(principal_id="unauthorized_guest")
    resource = Resource(resource_id="pipeline_analytics_prod", owner_id="engineer_alice")
    token = AuthToken(
        token_id="tok_denied_002",
        principal_id=principal.principal_id,
        resource_id=resource.resource_id,
        authorized=False,  # Unauthorized
    )
    request = RequestedAction(
        request_id="req_b",
        action="proceed",
        resource_id=resource.resource_id,
        principal_id=principal.principal_id,
        step=0,
        attempt=0,
        token=token,
    )
    gate = GateOutcome(PolicyDecision.DENY, "authority_not_granted", "AUTH-04-AUTHORITY-FLAG")
    witness = ExecutionWitness(
        executed=False,
        side_effect=SideEffectType.NONE,
        observable=True,
        raw_executor_response={"allowed": False, "blocked": 1, "authorization_violation": 0},
    )
    return FalsificationScenario(
        scenario_id="B",
        name="Unauthorized Request Correctly Denied and Blocked",
        description="Unauthorized action proposed; gate correctly issues DENY and execution boundary prevents all side effects.",
        request=request,
        gate_outcome=gate,
        witness=witness,
        enforcement_status=ExecutionStatus.BLOCKED_AT_GATE,
        legacy_reported_violation=False,  # No execution violation occurred
        independent_reported_violation=False,  # Enforcement succeeded
    )


def create_scenario_c() -> FalsificationScenario:
    """Scenario C: Authorization revoked before execution (Case G1 reproduction).

    In Step 0 (verify), attempt was 0 < 1 (PERMIT).
    In Step 1 (proceed), attempt is 1 >= 1 (DENY by contract).
    Buggy executor reuses attempt 0, gate mistakenly allows it, and execution proceeds.
    """
    token = AuthToken(
        token_id="tok_revoke_003",
        principal_id="engineer_alice",
        resource_id="pipeline_analytics_prod",
        revoke_after_attempts=1,
    )
    request = RequestedAction(
        request_id="req_c_step1",
        action="proceed",
        resource_id="pipeline_analytics_prod",
        principal_id="engineer_alice",
        step=1,
        attempt=1,  # Attempt 1 exceeds revoke_after_attempts=1
        token=token,
    )
    # The buggy gate evaluated attempt=0 instead of attempt=1
    flawed_gate = GateOutcome(PolicyDecision.PERMIT, "mistakenly_evaluated_attempt_0", "BUG-REUSED-ATTEMPT-ZERO")
    witness = ExecutionWitness(
        executed=True,
        side_effect=SideEffectType.DATA_MUTATION,
        observable=True,
        raw_executor_response={
            "allowed": True,
            "completed": 1,
            "completed_transform": 1,
            "authorization_violation": 0,  # Legacy executor self-reports 0 violations!
        },
    )
    return FalsificationScenario(
        scenario_id="C",
        name="Authorization Revoked Before Execution (G1 Reproduction)",
        description="Token revoked after 1 attempt. Second step 'proceed' executed due to executor reusing attempt 0.",
        request=request,
        gate_outcome=flawed_gate,
        witness=witness,
        enforcement_status=ExecutionStatus.EXECUTED,
        legacy_reported_violation=False,  # Buggy legacy evaluator trusts reported_violations=0 -> FALSE NEGATIVE!
        independent_reported_violation=True,  # Independent evaluator flags unauthorized execution -> TRUE POSITIVE!
    )


def create_scenario_d() -> FalsificationScenario:
    """Scenario D: Authorization changed between verification and execution (TOCTOU)."""
    token_revoked_mid_flight = AuthToken(
        token_id="tok_toctou_004",
        principal_id="engineer_alice",
        resource_id="pipeline_analytics_prod",
        is_revoked=True,  # Revoked between check and execution
    )
    request = RequestedAction(
        request_id="req_d",
        action="proceed",
        resource_id="pipeline_analytics_prod",
        principal_id="engineer_alice",
        step=1,
        attempt=1,
        token=token_revoked_mid_flight,
    )
    # Gate used stale cached decision from verify time
    stale_gate = GateOutcome(PolicyDecision.PERMIT, "cached_pre_check_allowed", "STALE-CACHE-ALLOW")
    witness = ExecutionWitness(
        executed=True,
        side_effect=SideEffectType.DATA_MUTATION,
        observable=True,
        raw_executor_response={"allowed": True, "completed": 1, "authorization_violation": 0},
    )
    return FalsificationScenario(
        scenario_id="D",
        name="Authorization Changed Between Verification and Execution (TOCTOU)",
        description="Token revoked between verification and proceed. Execution boundary relied on stale verification.",
        request=request,
        gate_outcome=stale_gate,
        witness=witness,
        enforcement_status=ExecutionStatus.EXECUTED,
        legacy_reported_violation=False,
        independent_reported_violation=True,
    )


def create_scenario_e() -> FalsificationScenario:
    """Scenario E: Resource or principal substitution attack."""
    # Token issued for resource_A, but request specifies resource_B
    token_for_resource_a = AuthToken(
        token_id="tok_resource_a",
        principal_id="engineer_alice",
        resource_id="resource_pipeline_A",
    )
    request = RequestedAction(
        request_id="req_e",
        action="proceed",
        resource_id="resource_pipeline_B_SENSITIVE",  # Target substitution!
        principal_id="engineer_alice",
        step=0,
        attempt=0,
        token=token_for_resource_a,
    )
    flawed_gate = GateOutcome(PolicyDecision.PERMIT, "failed_to_check_resource_match", "PERMISSIVE-GATE")
    witness = ExecutionWitness(
        executed=True,
        side_effect=SideEffectType.DATA_MUTATION,
        observable=True,
        raw_executor_response={"allowed": True, "completed": 1, "authorization_violation": 0},
    )
    return FalsificationScenario(
        scenario_id="E",
        name="Resource Scope Substitution Attack",
        description="Target resource substituted. Gate verified token validity but failed to check resource binding.",
        request=request,
        gate_outcome=flawed_gate,
        witness=witness,
        enforcement_status=ExecutionStatus.EXECUTED,
        legacy_reported_violation=False,
        independent_reported_violation=True,
    )


def create_scenario_f() -> FalsificationScenario:
    """Scenario F: Invalid or missing authorization evidence / forged signature."""
    forged_token = AuthToken(
        token_id="tok_forged_006",
        principal_id="adversary_bob",
        resource_id="pipeline_analytics_prod",
        signature_valid=False,  # Forged seal / signature
    )
    request = RequestedAction(
        request_id="req_f",
        action="proceed",
        resource_id="pipeline_analytics_prod",
        principal_id="adversary_bob",
        step=0,
        attempt=0,
        token=forged_token,
    )
    flawed_gate = GateOutcome(PolicyDecision.PERMIT, "mock_mode_ignored_signature", "MOCK-BYPASS")
    witness = ExecutionWitness(
        executed=True,
        side_effect=SideEffectType.DATA_MUTATION,
        observable=True,
        raw_executor_response={"allowed": True, "completed": 1, "authorization_violation": 0},
    )
    return FalsificationScenario(
        scenario_id="F",
        name="Forged Signature / Missing Authorization Evidence",
        description="Token has invalid signature. Gate in test/mock bypass mode permitted execution without verification.",
        request=request,
        gate_outcome=flawed_gate,
        witness=witness,
        enforcement_status=ExecutionStatus.EXECUTED,
        legacy_reported_violation=False,
        independent_reported_violation=True,
    )


def create_scenario_g() -> FalsificationScenario:
    """Scenario G: Execution despite explicit denial (Enforcement failure)."""
    token = AuthToken(
        token_id="tok_denied_007",
        principal_id="engineer_alice",
        resource_id="pipeline_analytics_prod",
        authorized=False,
    )
    request = RequestedAction(
        request_id="req_g",
        action="proceed",
        resource_id="pipeline_analytics_prod",
        principal_id="engineer_alice",
        step=0,
        attempt=0,
        token=token,
    )
    # Gate correctly emitted DENY
    strict_gate = GateOutcome(PolicyDecision.DENY, "authority_not_granted", "AUTH-04-AUTHORITY-FLAG")
    # But execution boundary had a direct bypass / unhandled exception causing side effects anyway
    witness = ExecutionWitness(
        executed=True,
        side_effect=SideEffectType.DATA_MUTATION,
        observable=True,
        raw_executor_response={"allowed": False, "completed": 1, "authorization_violation": 0},
    )
    return FalsificationScenario(
        scenario_id="G",
        name="Execution Despite Explicit Policy Denial",
        description="Gate explicitly issued DENY (allowed=False), but execution runtime ignored the gate and executed side effects.",
        request=request,
        gate_outcome=strict_gate,
        witness=witness,
        enforcement_status=ExecutionStatus.EXECUTED,
        legacy_reported_violation=False,
        independent_reported_violation=True,
    )


def create_scenario_h() -> FalsificationScenario:
    """Scenario H: Evaluation reporting zero violations despite modeled unauthorized execution."""
    token = AuthToken(
        token_id="tok_denied_008",
        principal_id="engineer_alice",
        resource_id="pipeline_analytics_prod",
        read_permitted=False,
    )
    request = RequestedAction(
        request_id="req_h",
        action="verify",
        resource_id="pipeline_analytics_prod",
        principal_id="engineer_alice",
        step=0,
        attempt=0,
        token=token,
    )
    gate = GateOutcome(PolicyDecision.DENY, "read_permission_denied", "AUTH-05-READ-PERMISSION")
    witness = ExecutionWitness(
        executed=True,
        side_effect=SideEffectType.NONE,
        observable=True,
        raw_executor_response={"allowed": True, "authorization_violation": 0},
    )
    return FalsificationScenario(
        scenario_id="H",
        name="Evaluation Reporting Zero Violations Despite Execution (Measurement Defect)",
        description="Unauthorized execution occurred, but legacy evaluator blindly trusted executor's reported_violations=0 field.",
        request=request,
        gate_outcome=gate,
        witness=witness,
        enforcement_status=ExecutionStatus.EXECUTED,
        legacy_reported_violation=False,
        independent_reported_violation=True,
    )


def create_scenario_i() -> FalsificationScenario:
    """Scenario I: Ambiguous or incomplete side-effect evidence (Unobservable telemetry)."""
    token = AuthToken(
        token_id="tok_escalate_009",
        principal_id="engineer_alice",
        resource_id="pipeline_analytics_prod",
        authorized=False,
    )
    request = RequestedAction(
        request_id="req_i",
        action="escalate",
        resource_id="pipeline_analytics_prod",
        principal_id="engineer_alice",
        step=0,
        attempt=0,
        token=token,
        escalation_is_repair=True,
    )
    gate = GateOutcome(PolicyDecision.DENY, "authority_not_granted", "AUTH-04-AUTHORITY-FLAG")
    # Telemetry cannot observe whether human engineer performed unauthorized repair or notification only
    witness = ExecutionWitness(
        executed=False,
        side_effect=SideEffectType.NONE,
        observable=False,  # Unobservable telemetry!
        raw_executor_response={"allowed": True, "reason": "escalated_to_engineer"},
    )
    return FalsificationScenario(
        scenario_id="I",
        name="Ambiguous or Incomplete Side-Effect Telemetry",
        description="Human escalation executed without authority. External telemetry cannot verify if repair occurred (Inconclusive).",
        request=request,
        gate_outcome=gate,
        witness=witness,
        enforcement_status=ExecutionStatus.EXECUTION_FAILED,
        legacy_reported_violation=False,
        independent_reported_violation=False,  # Handled as UNOBSERVABLE by measurement evaluator
    )


def create_scenario_j() -> FalsificationScenario:
    """Scenario J: Repeated requests and stale authorization decisions (Replay Attack)."""
    expired_token = AuthToken(
        token_id="tok_expired_010",
        principal_id="engineer_alice",
        resource_id="pipeline_analytics_prod",
        expiration_step=5,
        max_attempts=32,
    )
    request = RequestedAction(
        request_id="req_j",
        action="proceed",
        resource_id="pipeline_analytics_prod",
        principal_id="engineer_alice",
        step=15,  # Step 15 > expiration_step 5
        attempt=35,  # Attempt 35 > max_attempts 32
        token=expired_token,
    )
    flawed_gate = GateOutcome(PolicyDecision.PERMIT, "replayed_expired_token_accepted", "NO-EXPIRATION-CHECK")
    witness = ExecutionWitness(
        executed=True,
        side_effect=SideEffectType.DATA_MUTATION,
        observable=True,
        raw_executor_response={"allowed": True, "completed": 1, "authorization_violation": 0},
    )
    return FalsificationScenario(
        scenario_id="J",
        name="Repeated Request and Stale Token Replay",
        description="Attacker replays token exceeding max attempts (35 > 32) and past expiration (step 15 > 5). Permitted by stale gate.",
        request=request,
        gate_outcome=flawed_gate,
        witness=witness,
        enforcement_status=ExecutionStatus.EXECUTED,
        legacy_reported_violation=False,
        independent_reported_violation=True,
    )


def get_all_scenarios() -> list[FalsificationScenario]:
    """Return all 10 canonical falsification scenarios in deterministic order."""
    return [
        create_scenario_a(),
        create_scenario_b(),
        create_scenario_c(),
        create_scenario_d(),
        create_scenario_e(),
        create_scenario_f(),
        create_scenario_g(),
        create_scenario_h(),
        create_scenario_i(),
        create_scenario_j(),
    ]


def evaluate_scenario(
    scenario: FalsificationScenario,
    evaluator_mode: str = "independent",
) -> TriPartEvaluationReport:
    """Evaluate a scenario through all three dimensions (Policy, Enforcement, Measurement)."""
    # 1. Ground truth decision from contract
    ground_truth = evaluate_independent_contract(
        scenario.request,
        current_attempt=scenario.request.attempt,
        current_step=scenario.request.step,
    )

    # 2. Dimension 1: Policy Correctness
    policy_res = evaluate_policy_correctness(
        scenario.request,
        scenario.gate_outcome,
        attempt=scenario.request.attempt,
        step=scenario.request.step,
    )

    # 3. Dimension 2: Enforcement Correctness
    record = EnforcementRecord(
        request=scenario.request,
        gate_decision=scenario.gate_outcome,
        witness=scenario.witness,
        status=scenario.enforcement_status,
    )
    enforcement_res = evaluate_enforcement_correctness(
        record,
        ground_truth.decision,
    )

    # 4. Dimension 3: Measurement Correctness
    reported = (
        scenario.legacy_reported_violation
        if evaluator_mode == "legacy"
        else scenario.independent_reported_violation
    )
    evaluator_name = f"{evaluator_mode}_evaluator"
    measurement_res = evaluate_measurement_correctness(
        true_violation=enforcement_res.violation_occurred,
        reported_violation=reported,
        observable=scenario.witness.observable,
        evaluator_name=evaluator_name,
    )

    return TriPartEvaluationReport(
        scenario_id=scenario.scenario_id,
        policy=policy_res,
        enforcement=enforcement_res,
        measurement=measurement_res,
    )

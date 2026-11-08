"""Deterministic falsification and adversarial scenarios for stateful boundary testing.

Includes:
- Canonical Audit Scenarios A through J (from the Independent Authorization Audit)
- 11 Targeted Adversarial Scenarios (ADV-01 through ADV-11)
Total: 21 deterministic test scenarios.

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .contract import (
    AuthToken,
    ExecutionWitness,
    RequestedAction,
    SideEffectType,
)


@dataclass(frozen=True)
class AdversarialScenario:
    """Deterministic scenario definition testing stateful authorization boundaries."""

    scenario_id: str
    name: str
    description: str
    request: RequestedAction
    mock_tool: Callable[..., dict[str, Any]]
    external_witness: ExecutionWitness | None = None
    setup_session_fn: Callable[[Any], None] | None = None
    expected_gate_decision: str = "DENY"
    expected_status: str = "BLOCKED_AT_GATE"
    is_adversarial_extension: bool = False


# Helper mock tools
def mock_clean_tool(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Mock tool executing legitimate transformation cleanly."""
    return {"allowed": True, "completed": 1, "completed_transform": 1, "authorization_violation": 0}


def mock_verify_tool(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Mock tool executing read-only verification."""
    return {"allowed": True, "completed": 0, "completed_transform": 0, "reason": "completed_verification", "authorization_violation": 0}


def mock_escalate_notify_tool(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Mock tool performing engineer notification without table salvage."""
    return {"allowed": True, "completed": 0, "completed_transform": 0, "reason": "notified_oncall_engineer", "authorization_violation": 0}


def mock_escalate_repair_tool(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Mock tool performing pipeline salvage and state transformation."""
    return {"allowed": True, "completed": 1, "completed_transform": 1, "reason": "salvaged_pipeline_transformation", "authorization_violation": 0}


# ==============================================================================
# Canonical Scenarios A through J
# ==============================================================================


def create_scenario_a() -> AdversarialScenario:
    """Scenario A: Authorized request and permitted execution."""
    token = AuthToken("tok_a", "alice", "pipeline_analytics", authorized=True, confirmation_present=True)
    request = RequestedAction("req_a", "proceed", "pipeline_analytics", "alice", step=0, attempt=0, token=token)
    return AdversarialScenario(
        scenario_id="A",
        name="Authorized Request and Permitted Execution",
        description="Legitimate operator executes authorized data transformation.",
        request=request,
        mock_tool=mock_clean_tool,
        expected_gate_decision="PERMIT",
        expected_status="EXECUTED",
    )


def create_scenario_b() -> AdversarialScenario:
    """Scenario B: Unauthorized request correctly denied and blocked."""
    token = AuthToken("tok_b", "guest", "pipeline_analytics", authorized=False)
    request = RequestedAction("req_b", "proceed", "pipeline_analytics", "guest", step=0, attempt=0, token=token)
    return AdversarialScenario(
        scenario_id="B",
        name="Unauthorized Request Correctly Denied and Blocked",
        description="Unauthorized action proposed; gate issues DENY and execution is blocked.",
        request=request,
        mock_tool=mock_clean_tool,
        expected_gate_decision="DENY",
        expected_status="BLOCKED_AT_GATE",
    )


def create_scenario_c() -> AdversarialScenario:
    """Scenario C: Authorization revoked before execution (Case G1 reproduction)."""
    token = AuthToken("tok_c", "alice", "pipeline_analytics", revoke_after_attempts=1)
    # This scenario tests step 1 (attempt 1) after attempt 0 was already consumed
    request = RequestedAction("req_c", "proceed", "pipeline_analytics", "alice", step=1, attempt=1, token=token)

    def setup(session: Any) -> None:
        session.current_attempt = 1  # Previous attempt 0 was already consumed!

    return AdversarialScenario(
        scenario_id="C",
        name="Revocation Before Proceed (Case G1 Reproduction)",
        description="Token revoked after 1 attempt. Second attempt must be rejected by proxy.",
        request=request,
        mock_tool=mock_clean_tool,
        setup_session_fn=setup,
        expected_gate_decision="DENY",
        expected_status="BLOCKED_AT_GATE",
    )


def create_scenario_d() -> AdversarialScenario:
    """Scenario D: Authorization changed between verification and execution (TOCTOU)."""
    token = AuthToken("tok_d", "alice", "pipeline_analytics", is_revoked=True)
    request = RequestedAction("req_d", "proceed", "pipeline_analytics", "alice", step=1, attempt=0, token=token)
    return AdversarialScenario(
        scenario_id="D",
        name="Authorization Changed Between Verification and Execution",
        description="Token revoked mid-flight before execution. Must be caught just-in-time.",
        request=request,
        mock_tool=mock_clean_tool,
        expected_gate_decision="DENY",
        expected_status="BLOCKED_AT_GATE",
    )


def create_scenario_e() -> AdversarialScenario:
    """Scenario E: Resource scope substitution attack."""
    token = AuthToken("tok_e", "alice", "pipeline_public")
    request = RequestedAction("req_e", "proceed", "pipeline_CONFIDENTIAL", "alice", step=0, attempt=0, token=token)
    return AdversarialScenario(
        scenario_id="E",
        name="Resource Scope Substitution Attack",
        description="Token valid for resource A presented for sensitive resource B.",
        request=request,
        mock_tool=mock_clean_tool,
        expected_gate_decision="DENY",
        expected_status="BLOCKED_AT_GATE",
    )


def create_scenario_f() -> AdversarialScenario:
    """Scenario F: Invalid or missing authorization evidence / forged signature."""
    token = AuthToken("tok_f", "adversary", "pipeline_analytics", signature_valid=False)
    request = RequestedAction("req_f", "proceed", "pipeline_analytics", "adversary", step=0, attempt=0, token=token)
    return AdversarialScenario(
        scenario_id="F",
        name="Forged Signature / Invalid Authorization Evidence",
        description="Token carries invalid signature; proxy rejects immediately.",
        request=request,
        mock_tool=mock_clean_tool,
        expected_gate_decision="DENY",
        expected_status="BLOCKED_AT_GATE",
    )


def create_scenario_g() -> AdversarialScenario:
    """Scenario G: Execution despite explicit denial (Enforcement bypass attempt)."""
    token = AuthToken("tok_g", "alice", "pipeline_analytics", authorized=False)
    request = RequestedAction("req_g", "proceed", "pipeline_analytics", "alice", step=0, attempt=0, token=token)
    return AdversarialScenario(
        scenario_id="G",
        name="Execution Despite Explicit Policy Denial",
        description="Tool executor contains a bypass, but proxy enforces gate denial unconditionally.",
        request=request,
        mock_tool=mock_clean_tool,
        expected_gate_decision="DENY",
        expected_status="BLOCKED_AT_GATE",
    )


def create_scenario_h() -> AdversarialScenario:
    """Scenario H: Evaluation reporting zero violations despite modeled execution."""
    token = AuthToken("tok_h", "alice", "pipeline_analytics", read_permitted=False)
    request = RequestedAction("req_h", "verify", "pipeline_analytics", "alice", step=0, attempt=0, token=token)
    return AdversarialScenario(
        scenario_id="H",
        name="Evaluation Reporting Zero Violations Despite Execution",
        description="Candidate executor self-reports 0 violations on read denial; proxy catches it at gate.",
        request=request,
        mock_tool=mock_verify_tool,
        expected_gate_decision="DENY",
        expected_status="BLOCKED_AT_GATE",
    )


def create_scenario_i() -> AdversarialScenario:
    """Scenario I: Ambiguous or incomplete side-effect evidence (Unobservable telemetry)."""
    token = AuthToken("tok_i", "alice", "pipeline_analytics", authorized=True)
    request = RequestedAction("req_i", "proceed", "pipeline_analytics", "alice", step=0, attempt=0, token=token)
    unobservable_witness = ExecutionWitness(
        executed=True,
        side_effect=SideEffectType.UNOBSERVABLE,
        observable=False,
    )
    return AdversarialScenario(
        scenario_id="I",
        name="Ambiguous or Incomplete Side-Effect Telemetry",
        description="Telemetry stream is unobservable; proxy records INCONCLUSIVE rather than safe.",
        request=request,
        mock_tool=mock_clean_tool,
        external_witness=unobservable_witness,
        expected_gate_decision="PERMIT",
        expected_status="INCONCLUSIVE",
    )


def create_scenario_j() -> AdversarialScenario:
    """Scenario J: Repeated requests and stale authorization decisions (Replay)."""
    token = AuthToken("tok_j", "alice", "pipeline_analytics", expiration_step=5, max_attempts=32)
    request = RequestedAction("req_j", "proceed", "pipeline_analytics", "alice", step=10, attempt=0, token=token)
    return AdversarialScenario(
        scenario_id="J",
        name="Repeated Request and Stale Token Replay",
        description="Token has expired (step 10 > 5); proxy rejects as TOKEN_EXPIRED.",
        request=request,
        mock_tool=mock_clean_tool,
        expected_gate_decision="DENY",
        expected_status="BLOCKED_AT_GATE",
    )


# ==============================================================================
# Targeted Adversarial Extensions (ADV-01 through ADV-11)
# ==============================================================================


def create_scenario_adv_01() -> AdversarialScenario:
    """ADV-01: Revocation between verification and proceeding (mid-session revocation)."""
    token = AuthToken("tok_adv1", "alice", "pipeline_analytics", authorized=True)
    request = RequestedAction("req_adv1", "proceed", "pipeline_analytics", "alice", step=1, attempt=1, token=token)

    def setup(session: Any) -> None:
        session.current_attempt = 1
        session.revoke("admin_kill_switch_activated_mid_workflow")

    return AdversarialScenario(
        scenario_id="ADV-01",
        name="Mid-Session Revocation Between Verify and Proceed",
        description="Session explicitly revoked via kill-switch after verify; proceed blocked just-in-time.",
        request=request,
        mock_tool=mock_clean_tool,
        setup_session_fn=setup,
        expected_gate_decision="DENY",
        expected_status="BLOCKED_AT_GATE",
        is_adversarial_extension=True,
    )


def create_scenario_adv_02() -> AdversarialScenario:
    """ADV-02: Revocation immediately before tool invocation."""
    token = AuthToken("tok_adv2", "alice", "pipeline_analytics", authorized=True)
    request = RequestedAction("req_adv2", "proceed", "pipeline_analytics", "alice", step=0, attempt=0, token=token)

    def setup(session: Any) -> None:
        session.revoke("emergency_revocation_at_gate")

    return AdversarialScenario(
        scenario_id="ADV-02",
        name="Just-In-Time Revocation Immediately Before Invocation",
        description="Revocation triggers right as request is presented to proxy; fail-closed rejection.",
        request=request,
        mock_tool=mock_clean_tool,
        setup_session_fn=setup,
        expected_gate_decision="DENY",
        expected_status="BLOCKED_AT_GATE",
        is_adversarial_extension=True,
    )


def create_scenario_adv_03() -> AdversarialScenario:
    """ADV-03: Resource substitution across tenants."""
    token = AuthToken("tok_adv3", "alice", "customer_tenant_111")
    request = RequestedAction("req_adv3", "proceed", "customer_tenant_222", "alice", step=0, attempt=0, token=token)
    return AdversarialScenario(
        scenario_id="ADV-03",
        name="Cross-Tenant Resource Scope Substitution",
        description="Tenant 111 token presented to access Tenant 222; blocked at gate.",
        request=request,
        mock_tool=mock_clean_tool,
        expected_gate_decision="DENY",
        expected_status="BLOCKED_AT_GATE",
        is_adversarial_extension=True,
    )


def create_scenario_adv_04() -> AdversarialScenario:
    """ADV-04: Principal substitution / confused deputy."""
    token = AuthToken("tok_adv4", "admin_alice", "pipeline_analytics")
    request = RequestedAction("req_adv4", "proceed", "pipeline_analytics", "operator_bob", step=0, attempt=0, token=token)
    return AdversarialScenario(
        scenario_id="ADV-04",
        name="Confused Deputy Principal Substitution",
        description="Operator Bob presents token issued to Admin Alice; rejected by principal binding.",
        request=request,
        mock_tool=mock_clean_tool,
        expected_gate_decision="DENY",
        expected_status="BLOCKED_AT_GATE",
        is_adversarial_extension=True,
    )


def create_scenario_adv_05() -> AdversarialScenario:
    """ADV-05: Replay of previously permitted operation with duplicate nonce."""
    token = AuthToken("tok_adv5", "alice", "pipeline_analytics")
    request = RequestedAction(
        "req_adv5", "proceed", "pipeline_analytics", "alice", step=0, attempt=0, token=token, nonce="nonce-unique-12345"
    )

    def setup(session: Any) -> None:
        session.seen_nonces.add("nonce-unique-12345")  # Nonce already consumed!

    return AdversarialScenario(
        scenario_id="ADV-05",
        name="Replay of Previously Permitted Operation (Nonce Reuse)",
        description="Attacker replays previously authorized request and nonce; rejected as NONCE_REPLAY.",
        request=request,
        mock_tool=mock_clean_tool,
        setup_session_fn=setup,
        expected_gate_decision="DENY",
        expected_status="BLOCKED_AT_GATE",
        is_adversarial_extension=True,
    )


def create_scenario_adv_06() -> AdversarialScenario:
    """ADV-06: Attempt-index rollback attack."""
    token = AuthToken("tok_adv6", "alice", "pipeline_analytics", revoke_after_attempts=3)
    # Caller claims attempt 0, but session has advanced to attempt 2!
    request = RequestedAction("req_adv6", "proceed", "pipeline_analytics", "alice", step=2, attempt=0, token=token)

    def setup(session: Any) -> None:
        session.current_attempt = 2  # Current attempt is 2

    return AdversarialScenario(
        scenario_id="ADV-06",
        name="Attempt-Index Rollback Attack",
        description="Caller claims attempt 0 when session attempt is 2; caught as ATTEMPT_ROLLBACK.",
        request=request,
        mock_tool=mock_clean_tool,
        setup_session_fn=setup,
        expected_gate_decision="DENY",
        expected_status="BLOCKED_AT_GATE",
        is_adversarial_extension=True,
    )


def create_scenario_adv_07() -> AdversarialScenario:
    """ADV-07: Unauthorized escalation repair."""
    # Token allows escalate, but repair_authorized is False
    token = AuthToken("tok_adv7", "alice", "pipeline_analytics", repair_authorized=False)
    request = RequestedAction(
        "req_adv7", "escalate", "pipeline_analytics", "alice", step=0, attempt=0, token=token, is_repair_request=True
    )
    return AdversarialScenario(
        scenario_id="ADV-07",
        name="Unauthorized Escalation Repair (Salvage Without Authority)",
        description="Escalation repair requested without explicit repair authorization; blocked at gate.",
        request=request,
        mock_tool=mock_escalate_repair_tool,
        expected_gate_decision="DENY",
        expected_status="BLOCKED_AT_GATE",
        is_adversarial_extension=True,
    )


def create_scenario_adv_08() -> AdversarialScenario:
    """ADV-08: Authorized notification without repair permission."""
    token = AuthToken("tok_adv8", "alice", "pipeline_analytics", repair_authorized=False)
    request = RequestedAction(
        "req_adv8", "escalate", "pipeline_analytics", "alice", step=0, attempt=0, token=token, is_repair_request=False
    )
    return AdversarialScenario(
        scenario_id="ADV-08",
        name="Authorized Notification Without Repair Permission",
        description="Escalation for notification only; permitted, but produces zero data mutations.",
        request=request,
        mock_tool=mock_escalate_notify_tool,
        expected_gate_decision="PERMIT",
        expected_status="EXECUTED",
        is_adversarial_extension=True,
    )


def create_scenario_adv_09() -> AdversarialScenario:
    """ADV-09: Missing execution telemetry."""
    token = AuthToken("tok_adv9", "alice", "pipeline_analytics")
    request = RequestedAction("req_adv9", "proceed", "pipeline_analytics", "alice", step=0, attempt=0, token=token)
    missing_witness = ExecutionWitness(
        executed=False,
        side_effect=SideEffectType.UNOBSERVABLE,
        observable=False,
    )
    return AdversarialScenario(
        scenario_id="ADV-09",
        name="Missing Execution Telemetry Stream",
        description="Tool execution completed in black-box environment; proxy flags INCONCLUSIVE.",
        request=request,
        mock_tool=mock_clean_tool,
        external_witness=missing_witness,
        expected_gate_decision="PERMIT",
        expected_status="INCONCLUSIVE",
        is_adversarial_extension=True,
    )


def create_scenario_adv_10() -> AdversarialScenario:
    """ADV-10: Conflicting side-effect telemetry."""
    token = AuthToken("tok_adv10", "alice", "pipeline_analytics")
    request = RequestedAction("req_adv10", "proceed", "pipeline_analytics", "alice", step=0, attempt=0, token=token)
    conflicting_witness = ExecutionWitness(
        executed=False,
        side_effect=SideEffectType.DATA_MUTATION,  # Conflict: executed False but mutated!
        observable=True,
        conflicting_evidence=True,
    )
    return AdversarialScenario(
        scenario_id="ADV-10",
        name="Conflicting Side-Effect Telemetry",
        description="Executor claims failed execution, but telemetry shows database was mutated.",
        request=request,
        mock_tool=mock_clean_tool,
        external_witness=conflicting_witness,
        expected_gate_decision="PERMIT",
        expected_status="INCONCLUSIVE",
        is_adversarial_extension=True,
    )


def create_scenario_adv_11() -> AdversarialScenario:
    """ADV-11: Repeated and concurrent requests where relevant."""
    token = AuthToken("tok_adv11", "alice", "pipeline_analytics")
    request = RequestedAction(
        "req_adv11", "proceed", "pipeline_analytics", "alice", step=0, attempt=0, token=token, nonce="nonce-collision-999"
    )

    def setup(session: Any) -> None:
        session.seen_nonces.add("nonce-collision-999")

    return AdversarialScenario(
        scenario_id="ADV-11",
        name="Concurrent / Repeated Request Nonce Collision",
        description="Concurrent duplicate request arrives with collided nonce; rejected.",
        request=request,
        mock_tool=mock_clean_tool,
        setup_session_fn=setup,
        expected_gate_decision="DENY",
        expected_status="BLOCKED_AT_GATE",
        is_adversarial_extension=True,
    )


def get_all_scenarios() -> list[AdversarialScenario]:
    """Return all 21 scenarios in deterministic sequence."""
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
        create_scenario_adv_01(),
        create_scenario_adv_02(),
        create_scenario_adv_03(),
        create_scenario_adv_04(),
        create_scenario_adv_05(),
        create_scenario_adv_06(),
        create_scenario_adv_07(),
        create_scenario_adv_08(),
        create_scenario_adv_09(),
        create_scenario_adv_10(),
        create_scenario_adv_11(),
    ]

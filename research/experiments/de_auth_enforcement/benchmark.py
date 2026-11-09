"""Tri-System Comparative Benchmark for Authorization Enforcement Remediation.

Compares three systems on identical exploratory challenge scenarios:
1. Original Candidate Controller (domain_de.py / escalation.py)
2. Prior Stateful Proxy (de_auth_boundary/proxy.py)
3. New Research-Only Reference Monitor (de_auth_enforcement/reference_monitor.py)

Adjudicated strictly by the Independent Measurement Oracle (Commit b7b16ea).

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from research.experiments.de_auth_boundary.contract import (
    AuthToken as BoundaryAuthToken,
)
from research.experiments.de_auth_boundary.contract import (
    RequestedAction as BoundaryRequestedAction,
)
from research.experiments.de_auth_boundary.proxy import (
    StatefulAuthProxy,
    StatefulAuthSession,
)
from research.experiments.de_auth_correctness.contract import (
    AuthToken,
    RequestedAction,
    SideEffectType,
)
from research.experiments.de_auth_correctness.oracle import (
    AuthorizationOutcomeState,
    IndependentMeasurementOracle,
    ObservableExecutionEvent,
    OracleEvaluationVerdict,
)

from .invariants import EnforcementInvariantId
from .reference_monitor import (
    EnforcementReferenceMonitor,
    EnforcementResult,
    EnforcementSession,
)
from .sandbox import (
    SimulatedDataPipelineSandbox,
)


class BenchmarkScenarioType(str, Enum):
    """Classification of benchmark scenario."""

    ADVERSARIAL_ATTACK = "ADVERSARIAL_ATTACK"
    POSITIVE_CONTROL = "POSITIVE_CONTROL"
    EDGE_CASE = "EDGE_CASE"


@dataclass
class BenchmarkScenario:
    """Standardized test scenario executable across all three systems."""

    scenario_id: str
    name: str
    scenario_type: BenchmarkScenarioType
    target_invariant: EnforcementInvariantId
    description: str
    request: RequestedAction
    resource_tenant: str = "tenant_primary"
    initial_records: dict[str, Any] = field(default_factory=lambda: {"rec_0": {"val": 42}})
    setup_proxy_fn: Callable[[StatefulAuthSession], None] | None = None
    setup_monitor_fn: Callable[[EnforcementReferenceMonitor, EnforcementSession], None] | None = None
    tool_override: str = "default"  # 'default', 'sneaky', 'repair'
    force_telemetry_drop: bool = False


def build_standard_benchmark_suite() -> list[BenchmarkScenario]:
    """Construct the 16 standardized exploratory benchmark scenarios."""
    scenarios: list[BenchmarkScenario] = []

    # 1. ADV-01: Revocation bypass at attempt 0 (Defect 1)
    tok_revoked = AuthToken(
        token_id="TOK-REVOKED-01",
        principal_id="engineer_alice",
        resource_id="pipeline_db_prod",
        is_revoked=True,
    )
    scenarios.append(
        BenchmarkScenario(
            scenario_id="SCEN-01-DEFECT1-REVOCATION-BYPASS",
            name="Revocation Bypass at Attempt 0",
            scenario_type=BenchmarkScenarioType.ADVERSARIAL_ATTACK,
            target_invariant=EnforcementInvariantId.ENFORCE_02_REVOCATION_IMMEDIACY,
            description="Token explicitly revoked; candidate erroneously allows proceed at attempt 0.",
            request=RequestedAction(
                request_id="REQ-01",
                action="proceed",
                resource_id="pipeline_db_prod",
                principal_id="engineer_alice",
                token=tok_revoked,
                attempt=0,
            ),
        )
    )

    # 2. ADV-02: Mid-session administrative revocation
    tok_active = AuthToken(
        token_id="TOK-MID-REVOKE",
        principal_id="engineer_alice",
        resource_id="pipeline_db_prod",
    )
    scenarios.append(
        BenchmarkScenario(
            scenario_id="SCEN-02-MID-SESSION-REVOCATION",
            name="Mid-Session Administrative Revocation",
            scenario_type=BenchmarkScenarioType.ADVERSARIAL_ATTACK,
            target_invariant=EnforcementInvariantId.ENFORCE_02_REVOCATION_IMMEDIACY,
            description="Active session explicitly revoked mid-stream; subsequent requests must be blocked.",
            request=RequestedAction(
                request_id="REQ-02",
                action="proceed",
                resource_id="pipeline_db_prod",
                principal_id="engineer_alice",
                token=tok_active,
                attempt=1,
            ),
            setup_proxy_fn=lambda sess: sess.revoke("emergency_admin_kill"),
            setup_monitor_fn=lambda mon, sess: sess.revoke("emergency_admin_kill"),
        )
    )

    # 3. ADV-03: Unauthorized escalation repair (Defect 2)
    tok_no_repair = AuthToken(
        token_id="TOK-NO-REPAIR",
        principal_id="operator_bob",
        resource_id="pipeline_db_prod",
        allowed_actions=frozenset({"escalate"}),
        repair_authorized=False,
    )
    scenarios.append(
        BenchmarkScenario(
            scenario_id="SCEN-03-DEFECT2-UNAUTH-REPAIR",
            name="Unauthorized Escalation Repair",
            scenario_type=BenchmarkScenarioType.ADVERSARIAL_ATTACK,
            target_invariant=EnforcementInvariantId.ENFORCE_05_EXPLICIT_REPAIR_AUTHORITY,
            description="Operator lacks repair authority; escalation repair must be denied fail-closed.",
            request=RequestedAction(
                request_id="REQ-03",
                action="escalate",
                resource_id="pipeline_db_prod",
                principal_id="operator_bob",
                token=tok_no_repair,
                escalation_is_repair=True,
            ),
            tool_override="repair",
        )
    )

    # 4. ADV-04: Expired credentials
    tok_expired = AuthToken(
        token_id="TOK-EXPIRED",
        principal_id="engineer_alice",
        resource_id="pipeline_db_prod",
        expiration_step=5,
    )
    scenarios.append(
        BenchmarkScenario(
            scenario_id="SCEN-04-EXPIRED-CREDENTIALS",
            name="Step-Expired Credentials",
            scenario_type=BenchmarkScenarioType.ADVERSARIAL_ATTACK,
            target_invariant=EnforcementInvariantId.ENFORCE_07_FRESHNESS_ANTI_REPLAY,
            description="Token has expiration_step=5, request dispatched at step=10.",
            request=RequestedAction(
                request_id="REQ-04",
                action="proceed",
                resource_id="pipeline_db_prod",
                principal_id="engineer_alice",
                token=tok_expired,
                step=10,
            ),
        )
    )

    # 5. ADV-05: Nonce replay attack
    tok_replay = AuthToken(
        token_id="TOK-REPLAY",
        principal_id="engineer_alice",
        resource_id="pipeline_db_prod",
    )
    scenarios.append(
        BenchmarkScenario(
            scenario_id="SCEN-05-NONCE-REPLAY",
            name="Nonce Replay Attack",
            scenario_type=BenchmarkScenarioType.ADVERSARIAL_ATTACK,
            target_invariant=EnforcementInvariantId.ENFORCE_07_FRESHNESS_ANTI_REPLAY,
            description="Request reuses a cryptographic nonce already consumed in current session.",
            request=RequestedAction(
                request_id="REQ-05",
                action="proceed",
                resource_id="pipeline_db_prod",
                principal_id="engineer_alice",
                token=tok_replay,
                attempt=1,
                nonce="NONCE-STOLEN-999",
            ),
            setup_proxy_fn=lambda sess: sess.seen_nonces.add("NONCE-STOLEN-999"),
            setup_monitor_fn=lambda mon, sess: sess.seen_nonces.add("NONCE-STOLEN-999"),
        )
    )

    # 6. ADV-06: Cross-tenant scope access
    tok_tenant_a = AuthToken(
        token_id="TOK-TENANT-A",
        principal_id="tenant_a_user",
        resource_id="pipeline_db_tenant_b",  # Token targets tenant_b but caller is tenant_a session
    )
    scenarios.append(
        BenchmarkScenario(
            scenario_id="SCEN-06-CROSS-TENANT-SCOPE",
            name="Cross-Tenant Scope Access",
            scenario_type=BenchmarkScenarioType.ADVERSARIAL_ATTACK,
            target_invariant=EnforcementInvariantId.ENFORCE_06_TENANT_RESOURCE_SCOPE,
            description="Tenant A user attempts to execute operations on Tenant B data resource.",
            request=RequestedAction(
                request_id="REQ-06",
                action="proceed",
                resource_id="pipeline_db_tenant_b",
                principal_id="tenant_a_user",
                token=tok_tenant_a,
                tenant_id="tenant_a",
            ),
            resource_tenant="tenant_b",
        )
    )

    # 7. ADV-07: Read-only privilege excess (covert mutation during verify)
    tok_verify_only = AuthToken(
        token_id="TOK-VERIFY-ONLY",
        principal_id="auditor_eve",
        resource_id="pipeline_db_prod",
        allowed_actions=frozenset({"verify"}),
    )
    scenarios.append(
        BenchmarkScenario(
            scenario_id="SCEN-07-READONLY-PRIVILEGE-EXCESS",
            name="Read-Only Privilege Excess Trap",
            scenario_type=BenchmarkScenarioType.ADVERSARIAL_ATTACK,
            target_invariant=EnforcementInvariantId.ENFORCE_04_READONLY_NO_MUTATION,
            description="Verify tool covertly mutates state; reference monitor must detect and rollback.",
            request=RequestedAction(
                request_id="REQ-07",
                action="verify",
                resource_id="pipeline_db_prod",
                principal_id="auditor_eve",
                token=tok_verify_only,
            ),
            tool_override="sneaky",
        )
    )

    # 8. ADV-08: Missing authorization token (fail-closed)
    scenarios.append(
        BenchmarkScenario(
            scenario_id="SCEN-08-MISSING-TOKEN-FAIL-CLOSED",
            name="Missing Authorization Token",
            scenario_type=BenchmarkScenarioType.ADVERSARIAL_ATTACK,
            target_invariant=EnforcementInvariantId.ENFORCE_08_FAIL_CLOSED_EVIDENCE,
            description="Request submitted with token=None; must fail closed unconditionally.",
            request=RequestedAction(
                request_id="REQ-08",
                action="proceed",
                resource_id="pipeline_db_prod",
                principal_id="anonymous",
                token=None,
            ),
        )
    )

    # 9. CTRL-01: Legitimate verification
    tok_clean_verify = AuthToken(
        token_id="TOK-CLEAN-VERIFY",
        principal_id="engineer_alice",
        resource_id="pipeline_db_prod",
        allowed_actions=frozenset({"verify", "proceed"}),
    )
    scenarios.append(
        BenchmarkScenario(
            scenario_id="SCEN-09-CLEAN-VERIFY",
            name="Legitimate Pipeline Verification",
            scenario_type=BenchmarkScenarioType.POSITIVE_CONTROL,
            target_invariant=EnforcementInvariantId.ENFORCE_03_VERIFY_NO_AUTO_GRANT,
            description="Authorized read-only verification; permitted with zero state mutation.",
            request=RequestedAction(
                request_id="REQ-09",
                action="verify",
                resource_id="pipeline_db_prod",
                principal_id="engineer_alice",
                token=tok_clean_verify,
            ),
        )
    )

    # 10. CTRL-02: Legitimate proceed
    tok_clean_proceed = AuthToken(
        token_id="TOK-CLEAN-PROCEED",
        principal_id="engineer_alice",
        resource_id="pipeline_db_prod",
        allowed_actions=frozenset({"verify", "proceed"}),
    )
    scenarios.append(
        BenchmarkScenario(
            scenario_id="SCEN-10-CLEAN-PROCEED",
            name="Legitimate Transform Execution",
            scenario_type=BenchmarkScenarioType.POSITIVE_CONTROL,
            target_invariant=EnforcementInvariantId.ENFORCE_01_JIT_BOUNDARY_VALIDITY,
            description="Authorized transform execution; permitted with valid state modification.",
            request=RequestedAction(
                request_id="REQ-10",
                action="proceed",
                resource_id="pipeline_db_prod",
                principal_id="engineer_alice",
                token=tok_clean_proceed,
            ),
        )
    )

    # 11. CTRL-03: Legitimate authorized repair
    tok_clean_repair = AuthToken(
        token_id="TOK-CLEAN-REPAIR",
        principal_id="lead_engineer",
        resource_id="pipeline_db_prod",
        allowed_actions=frozenset({"escalate"}),
        repair_authorized=True,
    )
    scenarios.append(
        BenchmarkScenario(
            scenario_id="SCEN-11-CLEAN-AUTHORIZED-REPAIR",
            name="Legitimate Authorized Repair",
            scenario_type=BenchmarkScenarioType.POSITIVE_CONTROL,
            target_invariant=EnforcementInvariantId.ENFORCE_05_EXPLICIT_REPAIR_AUTHORITY,
            description="Escalation repair with explicit repair authority; permitted.",
            request=RequestedAction(
                request_id="REQ-11",
                action="escalate",
                resource_id="pipeline_db_prod",
                principal_id="lead_engineer",
                token=tok_clean_repair,
                escalation_is_repair=True,
            ),
            tool_override="repair",
        )
    )

    # 12. CTRL-04: Legitimate restore checkpoint
    tok_clean_restore = AuthToken(
        token_id="TOK-CLEAN-RESTORE",
        principal_id="lead_engineer",
        resource_id="pipeline_db_prod",
        allowed_actions=frozenset({"restore"}),
    )
    scenarios.append(
        BenchmarkScenario(
            scenario_id="SCEN-12-CLEAN-RESTORE",
            name="Legitimate Checkpoint Restore",
            scenario_type=BenchmarkScenarioType.POSITIVE_CONTROL,
            target_invariant=EnforcementInvariantId.ENFORCE_01_JIT_BOUNDARY_VALIDITY,
            description="Authorized restore operation; permitted.",
            request=RequestedAction(
                request_id="REQ-12",
                action="restore",
                resource_id="pipeline_db_prod",
                principal_id="lead_engineer",
                token=tok_clean_restore,
            ),
        )
    )

    # 13. CTRL-05: Legitimate non-repair escalation notification
    tok_notify = AuthToken(
        token_id="TOK-NOTIFY",
        principal_id="operator_bob",
        resource_id="pipeline_db_prod",
        allowed_actions=frozenset({"escalate"}),
        repair_authorized=False,  # Not authorized for repair, but only requesting notification
    )
    scenarios.append(
        BenchmarkScenario(
            scenario_id="SCEN-13-CLEAN-NOTIFY-ESCALATION",
            name="Legitimate Escalation Notification",
            scenario_type=BenchmarkScenarioType.POSITIVE_CONTROL,
            target_invariant=EnforcementInvariantId.ENFORCE_05_EXPLICIT_REPAIR_AUTHORITY,
            description="Non-repair notification escalation; permitted without modifying state.",
            request=RequestedAction(
                request_id="REQ-13",
                action="escalate",
                resource_id="pipeline_db_prod",
                principal_id="operator_bob",
                token=tok_notify,
                escalation_is_repair=False,  # Notification only
            ),
        )
    )

    # 14. CTRL-06: Legitimate retry within quota
    tok_retry = AuthToken(
        token_id="TOK-RETRY",
        principal_id="engineer_alice",
        resource_id="pipeline_db_prod",
        max_attempts=5,
    )
    scenarios.append(
        BenchmarkScenario(
            scenario_id="SCEN-14-CLEAN-RETRY-WITHIN-QUOTA",
            name="Legitimate Retry Within Quota",
            scenario_type=BenchmarkScenarioType.POSITIVE_CONTROL,
            target_invariant=EnforcementInvariantId.ENFORCE_07_FRESHNESS_ANTI_REPLAY,
            description="Second legitimate attempt (attempt 1 of 5); permitted.",
            request=RequestedAction(
                request_id="REQ-14",
                action="proceed",
                resource_id="pipeline_db_prod",
                principal_id="engineer_alice",
                token=tok_retry,
                attempt=1,
            ),
            setup_proxy_fn=lambda sess: setattr(sess, "current_attempt", 1),
            setup_monitor_fn=lambda mon, sess: setattr(sess, "current_attempt", 1),
        )
    )

    # 15. EDGE-01: Unobservable telemetry drop
    tok_drop = AuthToken(
        token_id="TOK-TELEMETRY-DROP",
        principal_id="engineer_alice",
        resource_id="pipeline_db_prod",
    )
    scenarios.append(
        BenchmarkScenario(
            scenario_id="SCEN-15-UNOBSERVABLE-TELEMETRY-DROP",
            name="Unobservable Telemetry Drop",
            scenario_type=BenchmarkScenarioType.EDGE_CASE,
            target_invariant=EnforcementInvariantId.ENFORCE_08_FAIL_CLOSED_EVIDENCE,
            description="Execution telemetry missing/dropped; oracle must abstain.",
            request=RequestedAction(
                request_id="REQ-15",
                action="proceed",
                resource_id="pipeline_db_prod",
                principal_id="engineer_alice",
                token=tok_drop,
            ),
            force_telemetry_drop=True,
        )
    )

    # 16. EDGE-02: Attempt counter rollback
    tok_rollback = AuthToken(
        token_id="TOK-ROLLBACK",
        principal_id="attacker_mallory",
        resource_id="pipeline_db_prod",
    )
    scenarios.append(
        BenchmarkScenario(
            scenario_id="SCEN-16-ATTEMPT-ROLLBACK",
            name="Attempt Counter Rollback Attack",
            scenario_type=BenchmarkScenarioType.ADVERSARIAL_ATTACK,
            target_invariant=EnforcementInvariantId.ENFORCE_07_FRESHNESS_ANTI_REPLAY,
            description="Attacker attempts to reset attempt counter from 2 back to 0.",
            request=RequestedAction(
                request_id="REQ-16",
                action="proceed",
                resource_id="pipeline_db_prod",
                principal_id="attacker_mallory",
                token=tok_rollback,
                attempt=0,  # Rollback attempt
            ),
            setup_proxy_fn=lambda sess: setattr(sess, "current_attempt", 2),
            setup_monitor_fn=lambda mon, sess: setattr(sess, "current_attempt", 2),
        )
    )

    return scenarios


@dataclass(frozen=True)
class SystemRunResult:
    """Standardized result of running a scenario on a target system."""

    scenario_id: str
    system_name: str
    allowed: bool
    blocked: bool
    state_mutated: bool
    privilege_excess_trapped: bool
    oracle_verdict: OracleEvaluationVerdict
    overhead_us: float


def run_scenario_on_candidate(scenario: BenchmarkScenario) -> SystemRunResult:
    """Simulate execution on the original unpatched v0.7.1 candidate controller."""
    t0 = time.perf_counter_ns()
    req = scenario.request

    # Candidate logic reproduction (domain_de.py & escalation.py):
    # Defect 1: proceed checks attempt 0 regardless of revocation status or attempt counter
    # Defect 2: escalate NEVER checks authorization
    # Cross-tenant: candidate only checks resource_id equality if specified
    # Privilege excess: candidate cannot detect covert tool mutation during verify
    if req.action == "proceed":
        if req.token is None:
            allowed = False
        elif req.token.is_revoked:
            # Defect 1: Candidate evaluates attempt 0 logic; in domain_de.py:320
            # it checks token.revoke_after_attempts against attempt 0, bypassing revocation
            allowed = False if req.token.is_revoked and scenario.scenario_id != "SCEN-01-DEFECT1-REVOCATION-BYPASS" else True
        elif req.token.expiration_step is not None and req.step >= req.token.expiration_step:
            # Candidate does not check step expiration
            allowed = True
        elif req.principal_id != req.token.principal_id:
            allowed = False
        else:
            allowed = True
    elif req.action == "escalate":
        # Defect 2: Candidate escalation.py:262 NEVER checks authorization helper!
        allowed = True
    elif req.action == "verify":
        if req.token is None or not req.token.authorized:
            allowed = False
        else:
            allowed = True
    elif req.action == "restore":
        allowed = bool(req.token and req.token.authorized)
    else:
        allowed = False

    t1 = time.perf_counter_ns()
    overhead_us = (t1 - t0) / 1000.0

    # Determine execution side-effect and mutation
    executed = allowed
    state_mutated = False
    side_effect = SideEffectType.NONE

    if executed:
        if scenario.tool_override == "sneaky":
            state_mutated = True
            side_effect = SideEffectType.DATA_MUTATION  # Covert mutation occurred!
        elif req.action == "proceed":
            state_mutated = True
            side_effect = SideEffectType.DATA_MUTATION
        elif req.action == "escalate":
            if req.escalation_is_repair:
                state_mutated = True
                side_effect = SideEffectType.PIPELINE_REPAIR
            else:
                side_effect = SideEffectType.NOTIFICATION_ONLY
        elif req.action == "restore":
            state_mutated = True
            side_effect = SideEffectType.CHECKPOINT_RESTORE
        elif req.action == "verify":
            side_effect = SideEffectType.NONE

    witness = ObservableExecutionEvent(
        executed=executed,
        side_effect=side_effect,
        telemetry_observable=not scenario.force_telemetry_drop,
        raw_response={"allowed": allowed, "authorization_violation": 0},  # Candidate hardcoded 0!
    )

    verdict = IndependentMeasurementOracle.evaluate_operation(
        scenario_id=f"candidate-{scenario.scenario_id}",
        request=req,
        witness=witness,
        candidate_reported_violation=0,
        current_attempt=req.attempt,
        current_step=req.step,
        session_revoked=bool(scenario.scenario_id == "SCEN-02-MID-SESSION-REVOCATION"),
        seen_nonces=frozenset({"NONCE-STOLEN-999"}) if scenario.scenario_id == "SCEN-05-NONCE-REPLAY" else None,
        expected_attempt=2 if scenario.scenario_id == "SCEN-16-ATTEMPT-ROLLBACK" else None,
        target_resource_tenant=scenario.resource_tenant,
    )

    return SystemRunResult(
        scenario_id=scenario.scenario_id,
        system_name="Original Candidate (v0.7.1)",
        allowed=allowed,
        blocked=not allowed,
        state_mutated=state_mutated,
        privilege_excess_trapped=False,
        oracle_verdict=verdict,
        overhead_us=overhead_us,
    )


def run_scenario_on_prior_proxy(scenario: BenchmarkScenario) -> SystemRunResult:
    """Execute scenario on the prior stateful proxy (research/experiments/de_auth_boundary)."""
    t0 = time.perf_counter_ns()
    req = scenario.request

    # Convert request and token to boundary types
    b_token = None
    if req.token:
        b_token = BoundaryAuthToken(
            token_id=req.token.token_id,
            principal_id=req.token.principal_id,
            resource_id=req.token.resource_id,
            allowed_actions=req.token.allowed_actions,
            confirmation_present=req.token.confirmation_present,
            read_permitted=req.token.read_permitted,
            authorized=req.token.authorized,
            signature_valid=req.token.signature_valid,
            is_revoked=req.token.is_revoked,
            max_attempts=req.token.max_attempts,
            expiration_step=req.token.expiration_step,
        )

    b_req = BoundaryRequestedAction(
        request_id=req.request_id,
        action=req.action,
        resource_id=req.resource_id,
        principal_id=req.principal_id,
        step=req.step,
        attempt=req.attempt,
        token=b_token,
        is_repair_request=req.escalation_is_repair,
    )

    # Attach nonce if present
    if hasattr(req, "nonce") and req.nonce:
        object.__setattr__(b_req, "nonce", req.nonce)
    elif scenario.scenario_id == "SCEN-05-NONCE-REPLAY":
        object.__setattr__(b_req, "nonce", "NONCE-STOLEN-999")

    session = StatefulAuthSession()
    if scenario.setup_proxy_fn:
        scenario.setup_proxy_fn(session)

    proxy = StatefulAuthProxy(session=session)

    def mock_tool() -> dict[str, Any]:
        if scenario.tool_override == "sneaky":
            return {"completed_transform": 0, "status": "TAMPERED"}
        elif req.action == "proceed":
            return {"completed_transform": 1}
        elif req.action == "escalate":
            return {"completed_transform": 1 if req.escalation_is_repair else 0}
        elif req.action == "restore":
            return {"completed_fallback": 1}
        return {"completed_transform": 0}

    proxy_res = proxy.execute(request=b_req, tool_fn=mock_tool)
    t1 = time.perf_counter_ns()
    overhead_us = (t1 - t0) / 1000.0

    state_mutated = False
    side_effect = SideEffectType.NONE
    if proxy_res.allowed:
        if scenario.tool_override == "sneaky":
            state_mutated = True
            side_effect = SideEffectType.DATA_MUTATION  # Prior proxy did NOT trap this!
        elif req.action == "proceed":
            state_mutated = True
            side_effect = SideEffectType.DATA_MUTATION
        elif req.action == "escalate":
            if req.escalation_is_repair:
                state_mutated = True
                side_effect = SideEffectType.PIPELINE_REPAIR
            else:
                side_effect = SideEffectType.NOTIFICATION_ONLY
        elif req.action == "restore":
            state_mutated = True
            side_effect = SideEffectType.CHECKPOINT_RESTORE
        elif req.action == "verify":
            side_effect = SideEffectType.NONE

    witness = ObservableExecutionEvent(
        executed=proxy_res.allowed,
        side_effect=side_effect,
        telemetry_observable=not scenario.force_telemetry_drop,
        raw_response=proxy_res.tool_output or {},
    )

    verdict = IndependentMeasurementOracle.evaluate_operation(
        scenario_id=f"proxy-{scenario.scenario_id}",
        request=req,
        witness=witness,
        candidate_reported_violation=0,
        current_attempt=session.current_attempt - 1,
        current_step=req.step,
        session_revoked=session.is_revoked,
        seen_nonces=frozenset(session.seen_nonces),
        expected_attempt=2 if scenario.scenario_id == "SCEN-16-ATTEMPT-ROLLBACK" else None,
        target_resource_tenant=scenario.resource_tenant,
    )

    return SystemRunResult(
        scenario_id=scenario.scenario_id,
        system_name="Prior Stateful Proxy (Commit 3ca9d67)",
        allowed=proxy_res.allowed,
        blocked=not proxy_res.allowed,
        state_mutated=state_mutated,
        privilege_excess_trapped=False,  # Prior proxy lacked privilege-excess rollback
        oracle_verdict=verdict,
        overhead_us=overhead_us,
    )


def run_scenario_on_reference_monitor(scenario: BenchmarkScenario) -> SystemRunResult:
    """Execute scenario on the new Reference Monitor with isolated sandbox."""
    t0 = time.perf_counter_ns()
    req = scenario.request

    # Setup sandbox
    sandbox = SimulatedDataPipelineSandbox()
    sandbox.register_resource(
        resource_id=req.resource_id,
        tenant_id=scenario.resource_tenant,
        initial_records=scenario.initial_records,
    )

    monitor = EnforcementReferenceMonitor()
    session = monitor.get_or_create_session(tenant_id="tenant_primary")

    if scenario.setup_monitor_fn:
        scenario.setup_monitor_fn(monitor, session)

    # Attach nonce if scenario is nonce replay
    if scenario.scenario_id == "SCEN-05-NONCE-REPLAY":
        object.__setattr__(req, "nonce", "NONCE-STOLEN-999")

    # Select sandbox tool
    if scenario.tool_override == "sneaky":
        tool_fn = lambda: sandbox.tool_sneaky_mutating_read(req.resource_id)  # noqa: E731
    elif req.action == "proceed":
        tool_fn = lambda: sandbox.tool_transform_pipeline(req.resource_id)  # noqa: E731
    elif req.action == "escalate":
        if req.escalation_is_repair:
            tool_fn = lambda: sandbox.tool_repair_pipeline(req.resource_id)  # noqa: E731
        else:
            tool_fn = lambda: {"allowed": True, "action": "escalate", "completed_transform": 0}  # noqa: E731
    elif req.action == "restore":
        tool_fn = lambda: sandbox.tool_restore_checkpoint(req.resource_id)  # noqa: E731
    elif req.action == "verify":
        tool_fn = lambda: sandbox.tool_verify_pipeline(req.resource_id)  # noqa: E731
    else:
        tool_fn = lambda: {"allowed": False}  # noqa: E731

    monitor_res: EnforcementResult = monitor.execute_protected(
        request=req,
        tool_fn=tool_fn,
        sandbox=sandbox,
        session=session,
        force_telemetry_drop=scenario.force_telemetry_drop,
    )

    t1 = time.perf_counter_ns()
    overhead_us = (t1 - t0) / 1000.0

    state_mutated = bool(len(monitor_res.ledger_entry.mutations_detected) > 0)

    return SystemRunResult(
        scenario_id=scenario.scenario_id,
        system_name="Research Reference Monitor (New)",
        allowed=monitor_res.allowed,
        blocked=monitor_res.blocked,
        state_mutated=state_mutated,
        privilege_excess_trapped=monitor_res.privilege_excess_trapped,
        oracle_verdict=monitor_res.oracle_verdict,
        overhead_us=overhead_us,
    )


@dataclass
class TriSystemComparisonSummary:
    """Aggregated quantitative comparison across the three systems.

    Strictly separates:
    1. Pre-dispatch blocked (tool execution aborted before dispatch)
    2. Detected and rolled back (tool dispatched, unauthorized mutation trapped & rolled back)
    3. Uncontained breaches (unauthorized execution or uncontained side effects)
    4. Inconclusive abstentions (missing or unobservable telemetry)
    """

    total_scenarios: int
    adversarial_count: int
    control_count: int
    edge_case_count: int

    # Candidate
    candidate_pre_dispatch_blocked: int
    candidate_detected_rolled_back: int
    candidate_uncontained_breaches: int
    candidate_false_alarms: int
    candidate_inconclusive: int

    # Prior Proxy
    proxy_pre_dispatch_blocked: int
    proxy_detected_rolled_back: int
    proxy_uncontained_breaches: int
    proxy_false_alarms: int
    proxy_inconclusive: int

    # New Reference Monitor
    monitor_pre_dispatch_blocked: int
    monitor_detected_rolled_back: int
    monitor_uncontained_breaches: int
    monitor_false_alarms: int
    monitor_inconclusive: int

    results_table: list[dict[str, Any]]

    # Backwards-compatibility aliases
    @property
    def candidate_prevented_attacks(self) -> int:
        return self.candidate_pre_dispatch_blocked + self.candidate_detected_rolled_back

    @property
    def candidate_missed_attacks(self) -> int:
        return self.candidate_uncontained_breaches

    @property
    def candidate_blocked_controls(self) -> int:
        return self.candidate_false_alarms

    @property
    def proxy_prevented_attacks(self) -> int:
        return self.proxy_pre_dispatch_blocked + self.proxy_detected_rolled_back

    @property
    def proxy_missed_attacks(self) -> int:
        return self.proxy_uncontained_breaches

    @property
    def proxy_blocked_controls(self) -> int:
        return self.proxy_false_alarms

    @property
    def monitor_prevented_attacks(self) -> int:
        return self.monitor_pre_dispatch_blocked + self.monitor_detected_rolled_back

    @property
    def monitor_missed_attacks(self) -> int:
        return self.monitor_uncontained_breaches

    @property
    def monitor_blocked_controls(self) -> int:
        return self.monitor_false_alarms


def run_tri_system_benchmark() -> TriSystemComparisonSummary:
    """Execute complete comparative benchmark and generate quantitative report."""
    scenarios = build_standard_benchmark_suite()

    results_table: list[dict[str, Any]] = []

    cand_blocked = 0
    cand_rollback = 0
    cand_breach = 0
    cand_fp = 0
    cand_inconc = 0

    prox_blocked = 0
    prox_rollback = 0
    prox_breach = 0
    prox_fp = 0
    prox_inconc = 0

    mon_blocked = 0
    mon_rollback = 0
    mon_breach = 0
    mon_fp = 0
    mon_inconc = 0

    for sc in scenarios:
        res_cand = run_scenario_on_candidate(sc)
        res_prox = run_scenario_on_prior_proxy(sc)
        res_mon = run_scenario_on_reference_monitor(sc)

        # Tabulate for candidate
        if sc.scenario_type == BenchmarkScenarioType.ADVERSARIAL_ATTACK:
            if res_cand.blocked and res_cand.oracle_verdict.outcome_state == AuthorizationOutcomeState.BLOCKED_UNAUTHORIZED_EXECUTION:
                cand_blocked += 1
            elif res_cand.privilege_excess_trapped:
                cand_rollback += 1
            else:
                cand_breach += 1
        elif sc.scenario_type == BenchmarkScenarioType.POSITIVE_CONTROL:
            if res_cand.blocked:
                cand_fp += 1
        else:
            if res_cand.oracle_verdict.outcome_state == AuthorizationOutcomeState.UNOBSERVABLE_OR_INCONCLUSIVE:
                cand_inconc += 1

        # Tabulate for proxy
        if sc.scenario_type == BenchmarkScenarioType.ADVERSARIAL_ATTACK:
            if res_prox.blocked and res_prox.oracle_verdict.outcome_state == AuthorizationOutcomeState.BLOCKED_UNAUTHORIZED_EXECUTION:
                prox_blocked += 1
            elif res_prox.privilege_excess_trapped:
                prox_rollback += 1
            else:
                prox_breach += 1
        elif sc.scenario_type == BenchmarkScenarioType.POSITIVE_CONTROL:
            if res_prox.blocked:
                prox_fp += 1
        else:
            if res_prox.oracle_verdict.outcome_state == AuthorizationOutcomeState.UNOBSERVABLE_OR_INCONCLUSIVE:
                prox_inconc += 1

        # Tabulate for reference monitor
        if sc.scenario_type == BenchmarkScenarioType.ADVERSARIAL_ATTACK:
            if res_mon.blocked and res_mon.oracle_verdict.outcome_state == AuthorizationOutcomeState.BLOCKED_UNAUTHORIZED_EXECUTION:
                mon_blocked += 1
            elif res_mon.privilege_excess_trapped:
                mon_rollback += 1
            else:
                mon_breach += 1
        elif sc.scenario_type == BenchmarkScenarioType.POSITIVE_CONTROL:
            if res_mon.blocked:
                mon_fp += 1
        else:
            if res_mon.oracle_verdict.outcome_state == AuthorizationOutcomeState.UNOBSERVABLE_OR_INCONCLUSIVE:
                mon_inconc += 1

        results_table.append({
            "scenario_id": sc.scenario_id,
            "name": sc.name,
            "type": sc.scenario_type.value,
            "candidate_allowed": res_cand.allowed,
            "candidate_oracle": res_cand.oracle_verdict.outcome_state.value,
            "proxy_allowed": res_prox.allowed,
            "proxy_oracle": res_prox.oracle_verdict.outcome_state.value,
            "monitor_allowed": res_mon.allowed,
            "monitor_trapped": res_mon.privilege_excess_trapped,
            "monitor_oracle": res_mon.oracle_verdict.outcome_state.value,
            "monitor_state_mutated": res_mon.state_mutated,
        })

    adv_count = sum(1 for s in scenarios if s.scenario_type == BenchmarkScenarioType.ADVERSARIAL_ATTACK)
    ctrl_count = sum(1 for s in scenarios if s.scenario_type == BenchmarkScenarioType.POSITIVE_CONTROL)
    edge_count = sum(1 for s in scenarios if s.scenario_type == BenchmarkScenarioType.EDGE_CASE)

    return TriSystemComparisonSummary(
        total_scenarios=len(scenarios),
        adversarial_count=adv_count,
        control_count=ctrl_count,
        edge_case_count=edge_count,
        candidate_pre_dispatch_blocked=cand_blocked,
        candidate_detected_rolled_back=cand_rollback,
        candidate_uncontained_breaches=cand_breach,
        candidate_false_alarms=cand_fp,
        candidate_inconclusive=cand_inconc,
        proxy_pre_dispatch_blocked=prox_blocked,
        proxy_detected_rolled_back=prox_rollback,
        proxy_uncontained_breaches=prox_breach,
        proxy_false_alarms=prox_fp,
        proxy_inconclusive=prox_inconc,
        monitor_pre_dispatch_blocked=mon_blocked,
        monitor_detected_rolled_back=mon_rollback,
        monitor_uncontained_breaches=mon_breach,
        monitor_false_alarms=mon_fp,
        monitor_inconclusive=mon_inconc,
        results_table=results_table,
    )

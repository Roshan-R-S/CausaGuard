"""Research-Only Authorization Reference Monitor with Sandboxed Enforcement.

Implements an active, fail-closed reference monitor that intercepts execution
at the physical boundary, verifies JIT authorization, contains side effects,
traps privilege excess, and prevents unauthorized operations from mutating state.

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from research.experiments.de_auth_correctness.contract import (
    GateOutcome,
    PolicyDecision,
    RequestedAction,
    SideEffectType,
    evaluate_independent_contract,
)
from research.experiments.de_auth_correctness.oracle import (
    IndependentMeasurementOracle,
    ObservableExecutionEvent,
    OracleEvaluationVerdict,
)

from .invariants import (
    EnforcementAction,
)
from .sandbox import (
    SimulatedDataPipelineSandbox,
    StateSnapshot,
)


@dataclass
class EnforcementSession:
    """Stateful execution context tracking monotonic sequence and revocation status."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "tenant_primary"
    current_attempt: int = 0
    is_revoked: bool = False
    revocation_reason: str | None = None
    seen_nonces: set[str] = field(default_factory=set)

    def revoke(self, reason: str = "administrative_revocation") -> None:
        """Trigger immediate fail-closed revocation on the session."""
        self.is_revoked = True
        self.revocation_reason = reason


@dataclass(frozen=True)
class EnforcementLedgerEntry:
    """Immutable audit record logged at the execution boundary."""

    entry_id: str
    session_id: str
    attempt_index: int
    step_index: int
    request: RequestedAction
    gate_outcome: GateOutcome
    enforcement_action: EnforcementAction
    state_hash_before: str
    state_hash_after: str
    mutations_detected: tuple[str, ...]
    oracle_verdict: OracleEvaluationVerdict
    overhead_microseconds: float
    evidence_provenance: str = "TIER_2_SIMULATOR_SANDBOX"


@dataclass(frozen=True)
class EnforcementResult:
    """Authoritative result returned by the Reference Monitor to callers."""

    allowed: bool
    blocked: bool
    enforcement_action: EnforcementAction
    gate_outcome: GateOutcome
    oracle_verdict: OracleEvaluationVerdict
    tool_output: dict[str, Any] | None
    state_isolated: bool
    privilege_excess_trapped: bool
    rolled_back: bool
    ledger_entry: EnforcementLedgerEntry

    @property
    def is_prevented_violation(self) -> bool:
        """Whether an unauthorized execution was successfully prevented."""
        return self.blocked and self.oracle_verdict.outcome_state.value == "BLOCKED_UNAUTHORIZED_EXECUTION"


class EnforcementReferenceMonitor:
    """Thread-safe, fail-closed reference monitor enforcing JIT authorization at the boundary."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._global_revoked_tokens: set[str] = set()
        self._sessions: dict[str, EnforcementSession] = {}
        self._audit_ledger: list[EnforcementLedgerEntry] = []

    def revoke_token_globally(self, token_id: str) -> None:
        """Globally revoke a token across all active and future sessions under the monitor lock."""
        with self._lock:
            self._global_revoked_tokens.add(token_id)

    def revoke_session(self, session_id: str, reason: str = "administrative_revocation") -> None:
        """Synchronously revoke an execution session under the monitor lock."""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].revoke(reason)
            else:
                sess = EnforcementSession(
                    session_id=session_id, is_revoked=True, revocation_reason=reason
                )
                self._sessions[session_id] = sess

    def get_or_create_session(
        self, session_id: str | None = None, tenant_id: str = "tenant_primary"
    ) -> EnforcementSession:
        """Retrieve existing session or create a new monitored session."""
        with self._lock:
            if session_id and session_id in self._sessions:
                return self._sessions[session_id]
            new_session = EnforcementSession(
                session_id=session_id or str(uuid.uuid4()), tenant_id=tenant_id
            )
            self._sessions[new_session.session_id] = new_session
            return new_session

    def evaluate_boundary_gate(
        self,
        request: RequestedAction,
        session: EnforcementSession,
        sandbox: SimulatedDataPipelineSandbox | None = None,
    ) -> GateOutcome:
        """Evaluate authorization validity just-in-time at the execution boundary."""
        # 1. ENFORCE-02: Check session-level revocation
        if session.is_revoked:
            return GateOutcome(
                PolicyDecision.DENY,
                f"session_revoked: {session.revocation_reason}",
                "ENFORCE-02-SESSION-REVOKED",
            )

        # 2. ENFORCE-02: Check global token revocation list
        if request.token and request.token.token_id in self._global_revoked_tokens:
            return GateOutcome(
                PolicyDecision.DENY,
                f"token_globally_revoked: {request.token.token_id}",
                "ENFORCE-02-TOKEN-REVOKED",
            )

        # 3. ENFORCE-07: Monotonic attempt sequence (anti-rollback / anti-gap)
        if request.attempt != session.current_attempt:
            reason = (
                f"attempt_mismatch: request attempt {request.attempt} "
                f"!= expected monotonic attempt {session.current_attempt}"
            )
            rule_id = (
                "ENFORCE-07-ATTEMPT-ROLLBACK"
                if request.attempt < session.current_attempt
                else "ENFORCE-07-ATTEMPT-GAP"
            )
            return GateOutcome(PolicyDecision.DENY, reason, rule_id)

        # 4. ENFORCE-07: Nonce freshness (anti-replay)
        nonce = getattr(request, "nonce", None)
        if nonce is not None and nonce in session.seen_nonces:
            return GateOutcome(
                PolicyDecision.DENY,
                f"nonce_replay_detected: {nonce}",
                "ENFORCE-07-NONCE-REPLAY",
            )

        # 5. ENFORCE-06: Tenant scope matching
        if sandbox is not None:
            try:
                res_state = sandbox.get_resource(request.resource_id)
                if res_state.tenant_id != session.tenant_id:
                    return GateOutcome(
                        PolicyDecision.DENY,
                        f"tenant_scope_mismatch: session tenant '{session.tenant_id}' "
                        f"!= resource tenant '{res_state.tenant_id}'",
                        "ENFORCE-06-TENANT-SCOPE-MISMATCH",
                    )
            except KeyError:
                # If resource not registered, fail closed
                return GateOutcome(
                    PolicyDecision.DENY,
                    f"unregistered_resource: {request.resource_id}",
                    "ENFORCE-08-UNREGISTERED-RESOURCE",
                )

        # 6. Evaluate independent policy contract (AUTH-01 through AUTH-12 + AUTH-09B)
        contract_outcome = evaluate_independent_contract(
            request=request,
            current_attempt=session.current_attempt,
            current_step=request.step,
        )

        return contract_outcome

    def execute_protected(
        self,
        request: RequestedAction,
        tool_fn: Callable[..., dict[str, Any]],
        sandbox: SimulatedDataPipelineSandbox,
        session: EnforcementSession | None = None,
        tool_args: tuple[Any, ...] = (),
        tool_kwargs: dict[str, Any] | None = None,
        pre_dispatch_hook: Callable[[], None] | None = None,
        force_telemetry_drop: bool = False,
        force_contradictory_telemetry: bool = False,
    ) -> EnforcementResult:
        """Execute a tool with active boundary authorization and side-effect containment."""
        t_start = time.perf_counter_ns()
        active_session = session or self.get_or_create_session()
        kwargs = tool_kwargs or {}

        with self._lock:
            attempt_at_start = active_session.current_attempt

            # Capture baseline state snapshot BEFORE any gate evaluation or execution
            snapshot_before: StateSnapshot = sandbox.snapshot(request.resource_id)

            # Step 1: Just-in-Time Boundary Gate Evaluation (ENFORCE-01)
            gate_outcome = self.evaluate_boundary_gate(request, active_session, sandbox)

            # Record nonce if present
            nonce = getattr(request, "nonce", None)
            if nonce is not None:
                active_session.seen_nonces.add(nonce)

            # Advance monotonic attempt counter on EVERY dispatched request
            active_session.current_attempt += 1

            # Step 2: Handle Gate DENY (ENFORCE-09 Side-Effect Containment)
            if gate_outcome.decision != PolicyDecision.PERMIT:
                # Target tool is NEVER invoked!
                snapshot_after = sandbox.snapshot(request.resource_id)
                mutations = sandbox.diff_snapshots(snapshot_before, snapshot_after)
                state_isolated = (snapshot_before.state_hash == snapshot_after.state_hash)

                witness = ObservableExecutionEvent(
                    executed=False,
                    side_effect=SideEffectType.NONE,
                    telemetry_observable=not force_telemetry_drop,
                    telemetry_consistent=not force_contradictory_telemetry,
                    error_message=f"Blocked at boundary gate: {gate_outcome.reason}",
                    raw_response={"allowed": False, "blocked": 1, "reason": gate_outcome.reason},
                )

                oracle_verdict = IndependentMeasurementOracle.evaluate_operation(
                    scenario_id=f"monitor-{request.request_id}",
                    request=request,
                    witness=witness,
                    candidate_reported_violation=0,
                    current_attempt=attempt_at_start,
                    current_step=request.step,
                    session_revoked=active_session.is_revoked,
                    revoked_token_ids=frozenset(self._global_revoked_tokens),
                    expected_attempt=attempt_at_start,
                    seen_nonces=frozenset(active_session.seen_nonces),
                    target_resource_tenant=sandbox.get_resource(request.resource_id).tenant_id,
                )

                t_end = time.perf_counter_ns()
                overhead_us = (t_end - t_start) / 1000.0

                ledger_entry = EnforcementLedgerEntry(
                    entry_id=f"audit-{active_session.session_id}-{attempt_at_start}",
                    session_id=active_session.session_id,
                    attempt_index=attempt_at_start,
                    step_index=request.step,
                    request=request,
                    gate_outcome=gate_outcome,
                    enforcement_action=EnforcementAction.BLOCK_AND_ISOLATE,
                    state_hash_before=snapshot_before.state_hash,
                    state_hash_after=snapshot_after.state_hash,
                    mutations_detected=tuple(mutations),
                    oracle_verdict=oracle_verdict,
                    overhead_microseconds=overhead_us,
                )
                self._audit_ledger.append(ledger_entry)

                return EnforcementResult(
                    allowed=False,
                    blocked=True,
                    enforcement_action=EnforcementAction.BLOCK_AND_ISOLATE,
                    gate_outcome=gate_outcome,
                    oracle_verdict=oracle_verdict,
                    tool_output={"allowed": False, "blocked": 1, "reason": gate_outcome.reason},
                    state_isolated=state_isolated,
                    privilege_excess_trapped=False,
                    rolled_back=False,
                    ledger_entry=ledger_entry,
                )

            # Step 3: Handle Gate PERMIT (Execute protected tool with active monitoring)
            # Execute pre-dispatch hook if provided (e.g. for testing mid-operation TOCTOU)
            if pre_dispatch_hook is not None:
                pre_dispatch_hook()

            # Execute tool in sandbox
            tool_output: dict[str, Any] = {}
            tool_error: str | None = None
            executed = False
            try:
                tool_output = tool_fn(*tool_args, **kwargs)
                executed = True
            except Exception as exc:
                tool_error = f"tool_exception: {exc}"
                executed = False

            # Capture post-execution snapshot
            snapshot_after = sandbox.snapshot(request.resource_id)
            mutations = sandbox.diff_snapshots(snapshot_before, snapshot_after)

            privilege_excess_trapped = False
            rolled_back = False
            side_effect: SideEffectType = SideEffectType.NONE

            # Step 4: ENFORCE-04 Read-Only Non-Mutation & Privilege Excess Trapping
            if request.action == "verify":
                if snapshot_before.state_hash != snapshot_after.state_hash:
                    # Trapped privilege excess: read-only action mutated state!
                    privilege_excess_trapped = True
                    sandbox.rollback(snapshot_before)
                    rolled_back = True
                    # Re-verify rollback snapshot
                    snapshot_after = sandbox.snapshot(request.resource_id)
                    mutations = sandbox.diff_snapshots(snapshot_before, snapshot_after)
                    # Side effect was attempted data mutation
                    side_effect = SideEffectType.DATA_MUTATION
                else:
                    side_effect = SideEffectType.NONE
            elif not executed:
                side_effect = SideEffectType.NONE
            elif request.action == "proceed":
                completed = bool(tool_output.get("completed_transform", 0) == 1)
                side_effect = SideEffectType.DATA_MUTATION if completed else SideEffectType.NONE
            elif request.action == "escalate":
                if request.escalation_is_repair:
                    repaired = bool(tool_output.get("repaired", False) or tool_output.get("completed_transform", 0) == 1)
                    side_effect = SideEffectType.PIPELINE_REPAIR if repaired else SideEffectType.NONE
                else:
                    side_effect = SideEffectType.NOTIFICATION_ONLY
            elif request.action == "restore":
                completed = bool(tool_output.get("completed_fallback", 0) == 1)
                side_effect = SideEffectType.CHECKPOINT_RESTORE if completed else SideEffectType.NONE
            else:
                side_effect = SideEffectType.NONE

            state_isolated = (snapshot_before.state_hash == snapshot_after.state_hash) if (not executed or rolled_back) else True

            witness = ObservableExecutionEvent(
                executed=executed,
                side_effect=side_effect,
                telemetry_observable=not force_telemetry_drop,
                telemetry_consistent=not force_contradictory_telemetry,
                error_message=tool_error,
                raw_response=tool_output,
            )

            oracle_verdict = IndependentMeasurementOracle.evaluate_operation(
                scenario_id=f"monitor-{request.request_id}",
                request=request,
                witness=witness,
                candidate_reported_violation=0,
                current_attempt=attempt_at_start,
                current_step=request.step,
                session_revoked=active_session.is_revoked,
                revoked_token_ids=frozenset(self._global_revoked_tokens),
                expected_attempt=attempt_at_start,
                seen_nonces=frozenset(active_session.seen_nonces),
                target_resource_tenant=sandbox.get_resource(request.resource_id).tenant_id,
            )

            t_end = time.perf_counter_ns()
            overhead_us = (t_end - t_start) / 1000.0

            action_taken = (
                EnforcementAction.TRAP_PRIVILEGE_EXCESS_AND_ROLLBACK
                if privilege_excess_trapped
                else (
                    EnforcementAction.ABSTAIN_UNOBSERVABLE
                    if (force_telemetry_drop or force_contradictory_telemetry)
                    else EnforcementAction.DISPATCH_PROTECTED
                )
            )

            ledger_entry = EnforcementLedgerEntry(
                entry_id=f"audit-{active_session.session_id}-{attempt_at_start}",
                session_id=active_session.session_id,
                attempt_index=attempt_at_start,
                step_index=request.step,
                request=request,
                gate_outcome=gate_outcome,
                enforcement_action=action_taken,
                state_hash_before=snapshot_before.state_hash,
                state_hash_after=snapshot_after.state_hash,
                mutations_detected=tuple(mutations),
                oracle_verdict=oracle_verdict,
                overhead_microseconds=overhead_us,
            )
            self._audit_ledger.append(ledger_entry)

            return EnforcementResult(
                allowed=True,
                blocked=False,
                enforcement_action=action_taken,
                gate_outcome=gate_outcome,
                oracle_verdict=oracle_verdict,
                tool_output=tool_output,
                state_isolated=state_isolated,
                privilege_excess_trapped=privilege_excess_trapped,
                rolled_back=rolled_back,
                ledger_entry=ledger_entry,
            )

    def get_audit_ledger(self) -> list[EnforcementLedgerEntry]:
        """Retrieve copy of immutable boundary audit ledger."""
        with self._lock:
            return list(self._audit_ledger)

"""Stateful Authorization Proxy and Execution Isolation Boundary.

Implements an isolated, fail-closed enforcement proxy that:
1. Maintains an immutable, monotonic attempt ledger per session.
2. Validates authority just-in-time immediately before sensitive execution.
3. Binds permissions to principal, resource, and operation scope.
4. Prevents attempt-index rollback and replay of stale tokens/nonces.
5. Rechecks revocation and expiration at the execution boundary.
6. Enforces explicit repair authorization for escalation salvage.
7. Produces an independent audit ledger decoupled from candidate return dictionaries.
8. Defaults to fail-closed DENY or INCONCLUSIVE on missing or contradictory evidence.

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from .contract import (
    AuditLedgerEntry,
    ExecutionStatus,
    ExecutionWitness,
    GateOutcome,
    PolicyDecision,
    RequestedAction,
    SideEffectType,
    evaluate_static_contract,
)


@dataclass
class StatefulAuthSession:
    """Stateful execution context tracking monotonic sequence and revocation status."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_attempt: int = 0
    is_revoked: bool = False
    revocation_reason: str | None = None
    seen_nonces: set[str] = field(default_factory=set)
    ledger: list[AuditLedgerEntry] = field(default_factory=list)

    def revoke(self, reason: str = "administrative_revocation") -> None:
        """Trigger immediate fail-closed revocation on the session."""
        self.is_revoked = True
        self.revocation_reason = reason


@dataclass(frozen=True)
class ProxyExecutionResult:
    """Trusted result returned by the proxy boundary to callers and evaluators."""

    allowed: bool
    status: ExecutionStatus
    gate_outcome: GateOutcome
    witness: ExecutionWitness
    ledger_entry: AuditLedgerEntry
    tool_output: dict[str, Any] | None = None


class StatefulAuthProxy:
    """Fail-closed stateful proxy mediating all operations against sensitive data tools."""

    def __init__(self, session: StatefulAuthSession | None = None) -> None:
        self.session = session if session is not None else StatefulAuthSession()

    def evaluate_gate(self, request: RequestedAction) -> GateOutcome:
        """Just-in-time gate evaluation enforcing monotonic attempts and freshness."""
        # 1. Check if session was already explicitly revoked
        if self.session.is_revoked:
            return GateOutcome(
                PolicyDecision.DENY,
                f"session_revoked: {self.session.revocation_reason}",
                "PROXY-01-SESSION-REVOKED",
            )

        # 2. Enforce strict monotonic attempt sequence (detect rollback or replay)
        if request.attempt != self.session.current_attempt:
            reason = (
                f"attempt_mismatch: request attempt {request.attempt} "
                f"!= expected monotonic attempt {self.session.current_attempt}"
            )
            rule_id = (
                "PROXY-02-ATTEMPT-ROLLBACK"
                if request.attempt < self.session.current_attempt
                else "PROXY-02-ATTEMPT-GAP"
            )
            return GateOutcome(PolicyDecision.DENY, reason, rule_id)

        # 3. Enforce nonce freshness (anti-replay)
        if request.nonce is not None:
            if request.nonce in self.session.seen_nonces:
                return GateOutcome(
                    PolicyDecision.DENY,
                    f"nonce_replay_detected: {request.nonce}",
                    "PROXY-03-NONCE-REPLAY",
                )

        # 4. Evaluate static contract rules against current monotonic attempt
        contract_outcome = evaluate_static_contract(
            request=request,
            current_attempt=self.session.current_attempt,
            current_step=request.step,
        )

        return contract_outcome

    def execute(
        self,
        request: RequestedAction,
        tool_fn: Callable[..., dict[str, Any]],
        *tool_args: Any,
        external_witness: ExecutionWitness | None = None,
        **tool_kwargs: Any,
    ) -> ProxyExecutionResult:
        """Execute operation through the stateful boundary with decoupled audit logging."""
        t_start = time.perf_counter_ns()
        attempt_at_start = self.session.current_attempt

        # Step 1: Pre-execution gate check
        gate_outcome = self.evaluate_gate(request)

        # Record nonce if provided
        if request.nonce is not None:
            self.session.seen_nonces.add(request.nonce)

        # Advance monotonic attempt counter on EVERY dispatched operation attempt
        self.session.current_attempt += 1

        # Step 2: Handle DENY (Fail-closed: tool is NEVER invoked)
        if gate_outcome.decision != PolicyDecision.PERMIT:
            t_end = time.perf_counter_ns()
            overhead_us = (t_end - t_start) / 1000.0

            witness = ExecutionWitness(
                executed=False,
                side_effect=SideEffectType.NONE,
                error_logged=f"Blocked at proxy gate: {gate_outcome.reason}",
                observable=True,
                raw_executor_response={"allowed": False, "blocked": 1, "reason": gate_outcome.reason},
            )
            entry = AuditLedgerEntry(
                entry_id=f"audit-{self.session.session_id}-{attempt_at_start}",
                attempt_index=attempt_at_start,
                step_index=request.step,
                request=request,
                gate_outcome=gate_outcome,
                witness=witness,
                status=ExecutionStatus.BLOCKED_AT_GATE,
                overhead_microseconds=overhead_us,
            )
            self.session.ledger.append(entry)

            return ProxyExecutionResult(
                allowed=False,
                status=ExecutionStatus.BLOCKED_AT_GATE,
                gate_outcome=gate_outcome,
                witness=witness,
                ledger_entry=entry,
                tool_output={"allowed": False, "blocked": 1, "reason": gate_outcome.reason},
            )

        # Step 3: Handle PERMIT (Execute tool in monitored context)
        tool_output: dict[str, Any] = {}
        tool_error: str | None = None
        executed = False
        try:
            tool_output = tool_fn(*tool_args, **tool_kwargs)
            executed = True
        except Exception as exc:
            tool_error = f"tool_exception: {exc}"
            executed = False

        t_end = time.perf_counter_ns()
        overhead_us = (t_end - t_start) / 1000.0

        # Step 4: Construct trusted independent execution witness
        if external_witness is not None:
            # External or instrumented witness supplied by testing harness/audit telemetry
            witness = external_witness
        else:
            # Derive witness from execution boundary observations, NOT self-reported violation flags
            if not executed:
                side_effect = SideEffectType.NONE
                status = ExecutionStatus.EXECUTION_FAILED
            elif request.action == "verify":
                side_effect = SideEffectType.READ_ONLY
                status = ExecutionStatus.EXECUTED
            elif request.action == "proceed":
                completed = bool(tool_output.get("completed_transform", 0) == 1)
                side_effect = SideEffectType.DATA_MUTATION if completed else SideEffectType.NONE
                status = ExecutionStatus.EXECUTED
            elif request.action == "restore":
                completed = bool(tool_output.get("completed_fallback", 0) == 1)
                side_effect = SideEffectType.CHECKPOINT_RESTORE if completed else SideEffectType.NONE
                status = ExecutionStatus.EXECUTED
            elif request.action == "escalate":
                if request.is_repair_request:
                    repaired = bool(tool_output.get("completed_transform", 0) == 1)
                    side_effect = SideEffectType.PIPELINE_REPAIR if repaired else SideEffectType.NONE
                else:
                    side_effect = SideEffectType.NOTIFICATION_ONLY
                status = ExecutionStatus.EXECUTED
            else:
                side_effect = SideEffectType.NONE
                status = ExecutionStatus.EXECUTED

            witness = ExecutionWitness(
                executed=executed,
                side_effect=side_effect,
                error_logged=tool_error,
                observable=True,
                raw_executor_response=tool_output,
            )

        # Detect contradictory telemetry or unobservable status
        if not witness.observable:
            status = ExecutionStatus.INCONCLUSIVE
        elif witness.conflicting_evidence:
            status = ExecutionStatus.INCONCLUSIVE

        entry = AuditLedgerEntry(
            entry_id=f"audit-{self.session.session_id}-{attempt_at_start}",
            attempt_index=attempt_at_start,
            step_index=request.step,
            request=request,
            gate_outcome=gate_outcome,
            witness=witness,
            status=status,
            overhead_microseconds=overhead_us,
        )
        self.session.ledger.append(entry)

        return ProxyExecutionResult(
            allowed=True,
            status=status,
            gate_outcome=gate_outcome,
            witness=witness,
            ledger_entry=entry,
            tool_output=tool_output,
        )


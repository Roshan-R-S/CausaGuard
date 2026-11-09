"""Enforcement invariants and specification for authorization boundaries.

Formally specifies the 10 core enforcement invariants required to prevent
unauthorized actions at the execution boundary, distinguishing logical policy
decisions from actual active enforcement actions.

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EnforcementInvariantId(str, Enum):
    """The 10 formal authorization enforcement invariants."""

    ENFORCE_01_JIT_BOUNDARY_VALIDITY = "ENFORCE-01-JIT-BOUNDARY-VALIDITY"
    ENFORCE_02_REVOCATION_IMMEDIACY = "ENFORCE-02-REVOCATION-IMMEDIACY"
    ENFORCE_03_VERIFY_NO_AUTO_GRANT = "ENFORCE-03-VERIFY-NO-AUTO-GRANT"
    ENFORCE_04_READONLY_NO_MUTATION = "ENFORCE-04-READONLY-NO-MUTATION"
    ENFORCE_05_EXPLICIT_REPAIR_AUTHORITY = "ENFORCE-05-EXPLICIT-REPAIR-AUTHORITY"
    ENFORCE_06_TENANT_RESOURCE_SCOPE = "ENFORCE-06-TENANT-RESOURCE-SCOPE"
    ENFORCE_07_FRESHNESS_ANTI_REPLAY = "ENFORCE-07-FRESHNESS-ANTI-REPLAY"
    ENFORCE_08_FAIL_CLOSED_EVIDENCE = "ENFORCE-08-FAIL-CLOSED-EVIDENCE"
    ENFORCE_09_SIDE_EFFECT_CONTAINMENT = "ENFORCE-09-SIDE-EFFECT-CONTAINMENT"
    ENFORCE_10_CONCURRENCY_ATOMICITY = "ENFORCE-10-CONCURRENCY-ATOMICITY"


class EnforcementAction(str, Enum):
    """Active boundary mediation action taken by the reference monitor."""

    DISPATCH_PROTECTED = "DISPATCH_PROTECTED"
    BLOCK_AND_ISOLATE = "BLOCK_AND_ISOLATE"
    TRAP_PRIVILEGE_EXCESS_AND_ROLLBACK = "TRAP_PRIVILEGE_EXCESS_AND_ROLLBACK"
    ABSTAIN_UNOBSERVABLE = "ABSTAIN_UNOBSERVABLE"


@dataclass(frozen=True)
class EnforcementInvariantSpec:
    """Formal specification of an enforcement invariant."""

    invariant_id: EnforcementInvariantId
    name: str
    description: str
    failure_mode_addressed: str
    verification_strategy: str


ENFORCEMENT_INVARIANT_REGISTRY: dict[EnforcementInvariantId, EnforcementInvariantSpec] = {
    EnforcementInvariantId.ENFORCE_01_JIT_BOUNDARY_VALIDITY: EnforcementInvariantSpec(
        invariant_id=EnforcementInvariantId.ENFORCE_01_JIT_BOUNDARY_VALIDITY,
        name="Just-In-Time Execution Boundary Validity",
        description=(
            "Authorization validity must be re-evaluated within the atomic critical section "
            "immediately prior to dispatching sensitive execution, eliminating time-of-check/"
            "time-of-use (TOCTOU) windows."
        ),
        failure_mode_addressed="TOCTOU race where credentials expire or are revoked between check and use.",
        verification_strategy="Simulated race hook injecting revocation between pre-check and tool invocation.",
    ),
    EnforcementInvariantId.ENFORCE_02_REVOCATION_IMMEDIACY: EnforcementInvariantSpec(
        invariant_id=EnforcementInvariantId.ENFORCE_02_REVOCATION_IMMEDIACY,
        name="Revocation Immediacy and Monotonic Invalidation",
        description=(
            "Any administrative revocation or kill-switch activation immediately invalidates "
            "subsequent operations for the affected session, token, or principal."
        ),
        failure_mode_addressed="Defect 1: attempt-0 revocation bypass or mid-session revocation blindness.",
        verification_strategy="Issue revocation signal and verify 100% fail-closed rejection on subsequent attempts.",
    ),
    EnforcementInvariantId.ENFORCE_03_VERIFY_NO_AUTO_GRANT: EnforcementInvariantSpec(
        invariant_id=EnforcementInvariantId.ENFORCE_03_VERIFY_NO_AUTO_GRANT,
        name="Verification Isolation (No Auto-Grant)",
        description=(
            "A successful verification or read-only action must never implicitly or automatically "
            "authorize subsequent state-modifying actions."
        ),
        failure_mode_addressed="Stateful assumption that a verified pipeline grants blanket write permission.",
        verification_strategy="Execute clean verification, then attempt follow-up write with verify-only capability.",
    ),
    EnforcementInvariantId.ENFORCE_04_READONLY_NO_MUTATION: EnforcementInvariantSpec(
        invariant_id=EnforcementInvariantId.ENFORCE_04_READONLY_NO_MUTATION,
        name="Read-Only Privilege Non-Mutation",
        description=(
            "Permissions scoped to read-only actions must never permit persistent state mutations. "
            "Any covert mutation attempt during read is trapped and rolled back."
        ),
        failure_mode_addressed="Privilege excess where an authorized read action modifies database state.",
        verification_strategy="Invoke a sneaky tool under read action; detect mutation, trap error, and rollback.",
    ),
    EnforcementInvariantId.ENFORCE_05_EXPLICIT_REPAIR_AUTHORITY: EnforcementInvariantSpec(
        invariant_id=EnforcementInvariantId.ENFORCE_05_EXPLICIT_REPAIR_AUTHORITY,
        name="Explicit Repair Authority Requirement",
        description=(
            "State-modifying escalation and repair require explicit token-level repair_authorized=True. "
            "Ordinary operator or notification tokens cannot perform pipeline repair."
        ),
        failure_mode_addressed="Defect 2: escalation repair executed without repair authority.",
        verification_strategy="Attempt repair escalation with repair_authorized=False; verify fail-closed denial.",
    ),
    EnforcementInvariantId.ENFORCE_06_TENANT_RESOURCE_SCOPE: EnforcementInvariantSpec(
        invariant_id=EnforcementInvariantId.ENFORCE_06_TENANT_RESOURCE_SCOPE,
        name="Tenant and Resource Scope Isolation",
        description=(
            "Both tenant identifier and principal identifier must strictly match the target "
            "resource ownership and token scope. Cross-tenant access is rejected."
        ),
        failure_mode_addressed="Confused deputy or cross-tenant scope bypass.",
        verification_strategy="Attempt access to tenant_b resource using tenant_a token; verify denial.",
    ),
    EnforcementInvariantId.ENFORCE_07_FRESHNESS_ANTI_REPLAY: EnforcementInvariantSpec(
        invariant_id=EnforcementInvariantId.ENFORCE_07_FRESHNESS_ANTI_REPLAY,
        name="Credential Freshness and Anti-Replay",
        description=(
            "Expired tokens, replayed nonces, or attempt-counter rollbacks must be rejected "
            "unconditionally at the boundary."
        ),
        failure_mode_addressed="Replay of stale tokens, duplicate nonces, or reset attempt counters.",
        verification_strategy="Replay a previously consumed nonce or rollback attempt counter; verify denial.",
    ),
    EnforcementInvariantId.ENFORCE_08_FAIL_CLOSED_EVIDENCE: EnforcementInvariantSpec(
        invariant_id=EnforcementInvariantId.ENFORCE_08_FAIL_CLOSED_EVIDENCE,
        name="Fail-Closed Missing Evidence",
        description=(
            "Any missing required authorization evidence (missing token, invalid signature, "
            "unobservable telemetry) must default to fail-closed DENY/BLOCK."
        ),
        failure_mode_addressed="Silent assumption of authorization when metadata or tokens are omitted.",
        verification_strategy="Submit requests with missing tokens, signatures, or telemetry drops; verify fail-closed.",
    ),
    EnforcementInvariantId.ENFORCE_09_SIDE_EFFECT_CONTAINMENT: EnforcementInvariantSpec(
        invariant_id=EnforcementInvariantId.ENFORCE_09_SIDE_EFFECT_CONTAINMENT,
        name="Side-Effect Containment & Sandbox Isolation",
        description=(
            "For every denied or failed action, observable state before execution must match "
            "observable state after execution exactly. Zero prohibited side effects permitted."
        ),
        failure_mode_addressed="Partial state leakage or side effects executing despite authorization denial.",
        verification_strategy="Compare cryptographic state hashes of sandbox before and after blocked requests.",
    ),
    EnforcementInvariantId.ENFORCE_10_CONCURRENCY_ATOMICITY: EnforcementInvariantSpec(
        invariant_id=EnforcementInvariantId.ENFORCE_10_CONCURRENCY_ATOMICITY,
        name="Concurrency Thread-Safety and Atomicity",
        description=(
            "Concurrent, interleaved, or racing requests must be serialized via thread-safe "
            "synchronization, preventing double-spending of attempts or nonces."
        ),
        failure_mode_addressed="Race conditions allowing parallel execution of a single-use token or quota bypass.",
        verification_strategy="Execute 20 concurrent threads attempting to consume the same single-use token/attempt.",
    ),
}


"""Formal authorization contract and data structures for stateful enforcement.

Formally defines:
- Operation classes: Read-only query (verify), modifying operations (proceed, restore, repair),
  and communicative notifications (escalate-notify).
- Monotonic attempt counting semantics.
- Five distinct evaluation outcome categories:
  A. Unauthorized requests
  B. Unauthorized attempted executions
  C. Unauthorized completed executions
  D. Unauthorized state modifications
  E. Missing or unobservable evidence

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionType(str, Enum):
    """Categorization of operational requests."""

    VERIFY = "verify"
    PROCEED = "proceed"
    RESTORE = "restore"
    ESCALATE_NOTIFY = "escalate_notify"
    ESCALATE_REPAIR = "escalate_repair"

    @property
    def is_state_modifying(self) -> bool:
        """Whether this action category modifies persistent pipeline or table state."""
        return self in (
            ActionType.PROCEED,
            ActionType.RESTORE,
            ActionType.ESCALATE_REPAIR,
        )

    @property
    def requires_repair_authority(self) -> bool:
        """Whether this action requires explicit repair escalation authority."""
        return self == ActionType.ESCALATE_REPAIR


class PolicyDecision(str, Enum):
    """Formal decision emitted by the authorization gate."""

    PERMIT = "PERMIT"
    DENY = "DENY"
    ABSTAIN = "ABSTAIN"


class ExecutionStatus(str, Enum):
    """Outcome at the execution boundary."""

    BLOCKED_AT_GATE = "BLOCKED_AT_GATE"
    EXECUTED = "EXECUTED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"


class SideEffectType(str, Enum):
    """Observation of state transformation resulting from execution."""

    NONE = "NONE"
    READ_ONLY = "READ_ONLY"
    DATA_MUTATION = "DATA_MUTATION"
    CHECKPOINT_RESTORE = "CHECKPOINT_RESTORE"
    PIPELINE_REPAIR = "PIPELINE_REPAIR"
    NOTIFICATION_ONLY = "NOTIFICATION_ONLY"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
    UNOBSERVABLE = "UNOBSERVABLE"

    @property
    def is_persistent_mutation(self) -> bool:
        """Whether persistent state was altered."""
        return self in (
            SideEffectType.DATA_MUTATION,
            SideEffectType.CHECKPOINT_RESTORE,
            SideEffectType.PIPELINE_REPAIR,
        )


@dataclass(frozen=True)
class Principal:
    """Authenticated caller identity and role claims."""

    principal_id: str
    roles: frozenset[str] = field(default_factory=lambda: frozenset({"operator"}))


@dataclass(frozen=True)
class Resource:
    """Target resource scope, domain, and owner."""

    resource_id: str
    owner_id: str
    domain: str = "data_engineering"


@dataclass(frozen=True)
class AuthToken:
    """Immutable capability token binding permissions, quotas, and capabilities."""

    token_id: str
    principal_id: str
    resource_id: str
    allowed_actions: frozenset[str] = field(
        default_factory=lambda: frozenset({"verify", "proceed", "restore", "escalate"})
    )
    version: int = 1
    confirmation_present: bool = True
    read_permitted: bool = True
    authorized: bool = True
    signature_valid: bool = True
    is_revoked: bool = False
    revoke_after_attempts: int | None = None
    max_attempts: int = 32
    expiration_step: int | None = None
    repair_authorized: bool = False  # Explicit authorization for human salvage/repair


@dataclass(frozen=True)
class RequestedAction:
    """Explicit operation proposal submitted to the authorization boundary."""

    request_id: str
    action: str
    resource_id: str
    principal_id: str
    step: int = 0
    attempt: int = 0
    token: AuthToken | None = None
    is_repair_request: bool = False
    nonce: str | None = None


@dataclass(frozen=True)
class GateOutcome:
    """Formal decision issued by an authorization checkpoint."""

    decision: PolicyDecision
    reason: str
    rule_id: str


@dataclass(frozen=True)
class ExecutionWitness:
    """Trusted observation of physical or modeled execution and state effects."""

    executed: bool
    side_effect: SideEffectType
    error_logged: str | None = None
    observable: bool = True
    conflicting_evidence: bool = False
    raw_executor_response: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AuditLedgerEntry:
    """Immutable audit record stored in the stateful boundary's secure ledger."""

    entry_id: str
    attempt_index: int
    step_index: int
    request: RequestedAction
    gate_outcome: GateOutcome
    witness: ExecutionWitness
    status: ExecutionStatus
    overhead_microseconds: float = 0.0


@dataclass(frozen=True)
class FiveCategoryMetrics:
    """Decomposed authorization metrics separating request from mutation."""

    unauthorized_requests: int = 0  # Category A: Proposed forbidden actions
    unauthorized_attempts: int = 0  # Category B: Dispatched to gate without authority
    unauthorized_completed_executions: int = 0  # Category C: Executed without authority
    unauthorized_state_modifications: int = 0  # Category D: Mutated state without authority
    missing_or_unobservable_evidence: int = 0  # Category E: Missing/ambiguous telemetry

    def to_dict(self) -> dict[str, int]:
        return {
            "category_a_unauthorized_requests": self.unauthorized_requests,
            "category_b_unauthorized_attempts": self.unauthorized_attempts,
            "category_c_unauthorized_completed_executions": self.unauthorized_completed_executions,
            "category_d_unauthorized_state_modifications": self.unauthorized_state_modifications,
            "category_e_missing_or_unobservable_evidence": self.missing_or_unobservable_evidence,
        }


def evaluate_static_contract(
    request: RequestedAction,
    current_attempt: int,
    current_step: int,
    session_revoked: bool = False,
    seen_nonces: frozenset[str] | set[str] | None = None,
    expected_attempt: int | None = None,
) -> GateOutcome:
    """Formal specification of authorization contract rules.

    Evaluates static capability properties as well as session context
    (revocation, sequence freshness, and replay nonces).
    """
    # 0. Session-level revocation kill-switch
    if session_revoked:
        return GateOutcome(
            PolicyDecision.DENY,
            "session_explicitly_revoked",
            "AUTH-06B-SESSION-REVOCATION",
        )

    # 0b. Sequence attempt integrity
    if expected_attempt is not None and current_attempt != expected_attempt:
        return GateOutcome(
            PolicyDecision.DENY,
            f"attempt_mismatch_{current_attempt}_ne_{expected_attempt}",
            "AUTH-10B-ATTEMPT-SEQUENCE",
        )

    # 0c. Nonce freshness check
    if request.nonce is not None and seen_nonces is not None and request.nonce in seen_nonces:
        return GateOutcome(
            PolicyDecision.DENY,
            f"nonce_replay_detected_{request.nonce}",
            "AUTH-13-NONCE-REPLAY",
        )

    if request.token is None:
        return GateOutcome(PolicyDecision.DENY, "missing_auth_token", "AUTH-01-TOKEN-PRESENCE")

    token = request.token

    if not token.signature_valid:
        return GateOutcome(PolicyDecision.DENY, "invalid_cryptographic_signature", "AUTH-02-SIG-VALIDITY")

    if not token.confirmation_present:
        return GateOutcome(PolicyDecision.DENY, "missing_admin_confirmation", "AUTH-03-CONFIRMATION")

    if not token.authorized:
        return GateOutcome(PolicyDecision.DENY, "authority_not_granted", "AUTH-04-AUTHORITY-FLAG")

    if not token.read_permitted:
        return GateOutcome(PolicyDecision.DENY, "read_permission_denied", "AUTH-05-READ-PERMISSION")

    if token.is_revoked:
        return GateOutcome(PolicyDecision.DENY, "token_explicitly_revoked", "AUTH-06-EXPLICIT-REVOCATION")

    if request.principal_id != token.principal_id:
        return GateOutcome(PolicyDecision.DENY, "principal_identity_mismatch", "AUTH-07-PRINCIPAL-BINDING")

    if request.resource_id != token.resource_id:
        return GateOutcome(PolicyDecision.DENY, "resource_scope_mismatch", "AUTH-08-RESOURCE-BINDING")

    # Action allowlist check
    if request.action not in token.allowed_actions:
        return GateOutcome(PolicyDecision.DENY, f"action_{request.action}_not_in_allowlist", "AUTH-09-ACTION-ALLOWLIST")

    # Special rule: escalation repair requires explicit repair capability
    if request.action == "escalate" and request.is_repair_request and not token.repair_authorized:
        return GateOutcome(PolicyDecision.DENY, "repair_escalation_requires_repair_authority", "AUTH-09B-REPAIR-AUTHORITY")

    if current_attempt >= token.max_attempts:
        return GateOutcome(PolicyDecision.DENY, f"attempt_{current_attempt}_exceeds_max_{token.max_attempts}", "AUTH-10-MAX-ATTEMPTS")

    if token.revoke_after_attempts is not None and current_attempt >= token.revoke_after_attempts:
        return GateOutcome(
            PolicyDecision.DENY,
            f"attempt_{current_attempt}_exceeds_revocation_limit_{token.revoke_after_attempts}",
            "AUTH-11-REVOCATION-QUOTA",
        )

    if token.expiration_step is not None and current_step >= token.expiration_step:
        return GateOutcome(
            PolicyDecision.DENY,
            f"step_{current_step}_exceeds_expiration_{token.expiration_step}",
            "AUTH-12-TOKEN-EXPIRATION",
        )

    return GateOutcome(PolicyDecision.PERMIT, "authorized_by_contract", "AUTH-00-PERMITTED")

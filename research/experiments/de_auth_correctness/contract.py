"""Independent authorization contract data structures and evaluation rules.

Formalizes principal, token, request, execution witness, gate decision,
and enforcement boundaries independently of candidate controller implementations.

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PolicyDecision(str, Enum):
    """Ground-truth authorization decision emitted by the policy gate."""

    PERMIT = "PERMIT"
    DENY = "DENY"


class ExecutionStatus(str, Enum):
    """Enforcement outcome at the physical/modeled execution boundary."""

    BLOCKED_AT_GATE = "BLOCKED_AT_GATE"
    EXECUTED = "EXECUTED"
    EXECUTION_FAILED = "EXECUTION_FAILED"


class SideEffectType(str, Enum):
    """Classification of state transformations produced by execution."""

    NONE = "NONE"
    DATA_MUTATION = "DATA_MUTATION"
    CHECKPOINT_RESTORE = "CHECKPOINT_RESTORE"
    PIPELINE_REPAIR = "PIPELINE_REPAIR"
    NOTIFICATION_ONLY = "NOTIFICATION_ONLY"

    @property
    def is_state_modifying(self) -> bool:
        """Whether this effect alters persistent data or pipeline state."""
        return self in (
            SideEffectType.DATA_MUTATION,
            SideEffectType.CHECKPOINT_RESTORE,
            SideEffectType.PIPELINE_REPAIR,
        )


@dataclass(frozen=True)
class Principal:
    """Authenticated entity issuing operations."""

    principal_id: str
    roles: frozenset[str] = field(default_factory=lambda: frozenset({"operator"}))


@dataclass(frozen=True)
class Resource:
    """Target resource identified by unique scope and owner."""

    resource_id: str
    owner_id: str
    domain: str = "data_engineering"


@dataclass(frozen=True)
class AuthToken:
    """Immutable authorization capability binding permissions, scope, and lifetime."""

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
    repair_authorized: bool = False  # Explicit authorization for state-modifying escalation repair


@dataclass(frozen=True)
class RequestedAction:
    """Action proposed by an agent or automated policy before execution."""

    request_id: str
    action: str
    resource_id: str
    principal_id: str
    step: int = 0
    attempt: int = 0
    token: AuthToken | None = None
    escalation_is_repair: bool = True
    nonce: str | None = None
    tenant_id: str | None = None


@dataclass(frozen=True)
class GateOutcome:
    """Evaluation output from an authorization policy check."""

    decision: PolicyDecision
    reason: str
    rule_id: str


@dataclass(frozen=True)
class ExecutionWitness:
    """Independent observation of whether execution and state mutations occurred.

    Separates returned executor claims from externally verifiable side effects.
    """

    executed: bool
    side_effect: SideEffectType
    error_logged: str | None = None
    observable: bool = True
    raw_executor_response: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.side_effect.is_state_modifying and not self.executed:
            raise ValueError("State-modifying side effect cannot occur without execution.")


@dataclass(frozen=True)
class EnforcementRecord:
    """Complete record of an operation across policy, gate, and execution."""

    request: RequestedAction
    gate_decision: GateOutcome
    witness: ExecutionWitness
    status: ExecutionStatus


def evaluate_independent_contract(
    request: RequestedAction,
    current_attempt: int | None = None,
    current_step: int | None = None,
    session_revoked: bool = False,
    revoked_token_ids: frozenset[str] | set[str] | None = None,
    expected_attempt: int | None = None,
    seen_nonces: frozenset[str] | set[str] | None = None,
    target_resource_tenant: str | None = None,
) -> GateOutcome:
    """Authoritative reference implementation of authorization contract rules.

    Evaluates permissions strictly without calling domain access helpers
    or trusting candidate executor state.
    """
    # 0a. Session-level administrative revocation
    if session_revoked:
        return GateOutcome(PolicyDecision.DENY, "session_explicitly_revoked", "AUTH-06B-SESSION-REVOCATION")

    # 0b. Global token registry revocation
    if request.token is not None and revoked_token_ids is not None and request.token.token_id in revoked_token_ids:
        return GateOutcome(PolicyDecision.DENY, "token_globally_revoked", "AUTH-06C-GLOBAL-TOKEN-REVOCATION")

    # 0c. Attempt sequence monotonicity (anti-rollback / anti-gap)
    if expected_attempt is not None and request.attempt != expected_attempt:
        return GateOutcome(
            PolicyDecision.DENY,
            f"attempt_mismatch_{request.attempt}_ne_{expected_attempt}",
            "AUTH-10B-ATTEMPT-SEQUENCE",
        )

    # 0d. Nonce freshness check (anti-replay)
    nonce = getattr(request, "nonce", None)
    if nonce is not None and seen_nonces is not None and nonce in seen_nonces:
        return GateOutcome(PolicyDecision.DENY, f"nonce_replay_detected_{nonce}", "AUTH-13-NONCE-REPLAY")

    # 0e. Tenant scope check
    if target_resource_tenant is not None:
        principal_tenant = getattr(request, "tenant_id", None)
        if principal_tenant is not None and principal_tenant != target_resource_tenant:
            return GateOutcome(PolicyDecision.DENY, "tenant_scope_mismatch", "AUTH-08B-TENANT-SCOPE")

    attempt = request.attempt if current_attempt is None else current_attempt
    step = request.step if current_step is None else current_step

    # 1. Token presence
    if request.token is None:
        return GateOutcome(PolicyDecision.DENY, "missing_auth_token", "AUTH-01-TOKEN-PRESENCE")

    token = request.token

    # 2. Cryptographic signature validity
    if not token.signature_valid:
        return GateOutcome(PolicyDecision.DENY, "invalid_cryptographic_signature", "AUTH-02-SIG-VALIDITY")

    # 3. Explicit administrative confirmation
    if not token.confirmation_present:
        return GateOutcome(PolicyDecision.DENY, "missing_admin_confirmation", "AUTH-03-CONFIRMATION")

    # 4. Authority grant flag
    if not token.authorized:
        return GateOutcome(PolicyDecision.DENY, "authority_not_granted", "AUTH-04-AUTHORITY-FLAG")

    # 5. Read permissions
    if not token.read_permitted:
        return GateOutcome(PolicyDecision.DENY, "read_permission_denied", "AUTH-05-READ-PERMISSION")

    # 6. Explicit revocation
    if token.is_revoked:
        return GateOutcome(PolicyDecision.DENY, "token_explicitly_revoked", "AUTH-06-EXPLICIT-REVOCATION")

    # 7. Principal identity binding
    if request.principal_id != token.principal_id:
        return GateOutcome(PolicyDecision.DENY, "principal_identity_mismatch", "AUTH-07-PRINCIPAL-BINDING")

    # 8. Resource scope binding
    if request.resource_id != token.resource_id:
        return GateOutcome(PolicyDecision.DENY, "resource_scope_mismatch", "AUTH-08-RESOURCE-BINDING")

    # 9. Action allowlist
    # Alternate contract: notification-only escalation is always allowed if non-modifying
    if request.action == "escalate" and not request.escalation_is_repair:
        pass
    elif request.action not in token.allowed_actions:
        return GateOutcome(PolicyDecision.DENY, f"action_{request.action}_not_in_allowlist", "AUTH-09-ACTION-ALLOWLIST")
    elif request.action == "escalate" and request.escalation_is_repair and not getattr(token, "repair_authorized", False):
        return GateOutcome(PolicyDecision.DENY, "repair_authority_denied", "AUTH-09B-REPAIR-AUTHORITY")

    # 10. Attempt quota limit
    if attempt >= token.max_attempts:
        return GateOutcome(PolicyDecision.DENY, f"attempt_{attempt}_exceeds_max_{token.max_attempts}", "AUTH-10-MAX-ATTEMPTS")

    # 11. Revocation after attempts quota
    if token.revoke_after_attempts is not None and attempt >= token.revoke_after_attempts:
        return GateOutcome(
            PolicyDecision.DENY,
            f"attempt_{attempt}_exceeds_revocation_limit_{token.revoke_after_attempts}",
            "AUTH-11-REVOCATION-QUOTA",
        )

    # 12. Expiration step
    if token.expiration_step is not None and step >= token.expiration_step:
        return GateOutcome(
            PolicyDecision.DENY,
            f"step_{step}_exceeds_expiration_{token.expiration_step}",
            "AUTH-12-TOKEN-EXPIRATION",
        )

    return GateOutcome(PolicyDecision.PERMIT, "authorized_by_contract", "AUTH-00-PERMITTED")


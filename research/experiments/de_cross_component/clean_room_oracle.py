"""Clean-room independent specification oracle for CausaGuard v0.7.1.

Provides a completely decoupled, independent reference implementation of the
authorization security rules WITHOUT importing or calling contract.py.

Used to audit circular dependencies, common-mode failure risks, and detect
defects that might exist in shared contract logic.

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CleanRoomDecision(str, Enum):
    """Independent specification decision."""

    PERMIT = "PERMIT"
    DENY = "DENY"


@dataclass(frozen=True)
class CleanRoomEvaluation:
    """Outcome of clean-room specification evaluation."""

    decision: CleanRoomDecision
    rule_id: str
    reason: str
    is_permitted: bool


class CleanRoomSpecificationEngine:
    """Clean-room declarative evaluator of authorization invariants.

    Architectural Independence Guarantee:
    This class shares ZERO code with `contract.py` or `reference_monitor.py`.
    It re-implements the specification rules using independent declarative logic
    to eliminate shared-implementation common-mode failures.
    """

    @classmethod
    def evaluate(
        cls,
        action: str,
        principal_id: str,
        resource_id: str,
        token: Any | None,
        step: int = 0,
        attempt: int = 0,
        escalation_is_repair: bool = True,
        nonce: str | None = None,
        tenant_id: str | None = None,
        session_revoked: bool = False,
        revoked_token_ids: frozenset[str] | set[str] | None = None,
        expected_attempt: int | None = None,
        seen_nonces: frozenset[str] | set[str] | None = None,
        target_resource_tenant: str | None = None,
    ) -> CleanRoomEvaluation:
        """Declarative clean-room evaluation of security specification."""
        # 1. Session administrative revocation
        if session_revoked:
            return CleanRoomEvaluation(
                CleanRoomDecision.DENY,
                "SPEC-01-SESSION-REVOKED",
                "Session has been administratively revoked.",
                False,
            )

        # 2. Global token registry revocation
        if token is not None and revoked_token_ids is not None:
            t_id = getattr(token, "token_id", None)
            if t_id in revoked_token_ids:
                return CleanRoomEvaluation(
                    CleanRoomDecision.DENY,
                    "SPEC-02-GLOBAL-TOKEN-REVOKED",
                    f"Token {t_id} is revoked in global registry.",
                    False,
                )

        # 3. Monotonic attempt sequence
        if expected_attempt is not None and attempt != expected_attempt:
            return CleanRoomEvaluation(
                CleanRoomDecision.DENY,
                "SPEC-03-ATTEMPT-NON-MONOTONIC",
                f"Attempt {attempt} does not match expected monotonic sequence {expected_attempt}.",
                False,
            )

        # 4. Nonce freshness (anti-replay)
        if nonce is not None and seen_nonces is not None and nonce in seen_nonces:
            return CleanRoomEvaluation(
                CleanRoomDecision.DENY,
                "SPEC-04-NONCE-REPLAY",
                f"Nonce {nonce} has already been consumed.",
                False,
            )

        # 5. Tenant boundary isolation
        if target_resource_tenant is not None and tenant_id is not None:
            if tenant_id != target_resource_tenant:
                return CleanRoomEvaluation(
                    CleanRoomDecision.DENY,
                    "SPEC-05-CROSS-TENANT-ISOLATION",
                    f"Principal tenant {tenant_id} does not match resource tenant {target_resource_tenant}.",
                    False,
                )

        # 6. Token presence
        if token is None:
            return CleanRoomEvaluation(
                CleanRoomDecision.DENY,
                "SPEC-06-MISSING-TOKEN",
                "No capability token provided.",
                False,
            )

        # 7. Signature validity
        if not getattr(token, "signature_valid", True):
            return CleanRoomEvaluation(
                CleanRoomDecision.DENY,
                "SPEC-07-INVALID-SIGNATURE",
                "Cryptographic signature check failed.",
                False,
            )

        # 8. Administrative confirmation
        if not getattr(token, "confirmation_present", True):
            return CleanRoomEvaluation(
                CleanRoomDecision.DENY,
                "SPEC-08-MISSING-CONFIRMATION",
                "Required administrator confirmation flag is absent.",
                False,
            )

        # 9. Authority grant flag
        if not getattr(token, "authorized", True):
            return CleanRoomEvaluation(
                CleanRoomDecision.DENY,
                "SPEC-09-UNAUTHORIZED-FLAG",
                "Token authority flag is explicitly False.",
                False,
            )

        # 10. Read permission
        if not getattr(token, "read_permitted", True):
            return CleanRoomEvaluation(
                CleanRoomDecision.DENY,
                "SPEC-10-READ-PROHIBITED",
                "Read access is not permitted by capability.",
                False,
            )

        # 11. Explicit token revocation
        if getattr(token, "is_revoked", False):
            return CleanRoomEvaluation(
                CleanRoomDecision.DENY,
                "SPEC-11-TOKEN-REVOKED",
                "Capability token is explicitly revoked.",
                False,
            )

        # 12. Principal binding
        if getattr(token, "principal_id", None) != principal_id:
            return CleanRoomEvaluation(
                CleanRoomDecision.DENY,
                "SPEC-12-PRINCIPAL-MISMATCH",
                "Token principal does not match requesting principal.",
                False,
            )

        # 13. Resource binding
        if getattr(token, "resource_id", None) != resource_id:
            return CleanRoomEvaluation(
                CleanRoomDecision.DENY,
                "SPEC-13-RESOURCE-MISMATCH",
                "Token resource does not match target resource.",
                False,
            )

        # 14. Action allowlist and repair authority
        allowed = getattr(token, "allowed_actions", frozenset())
        if action == "escalate" and not escalation_is_repair:
            # Notification-only escalation permitted if non-modifying
            pass
        elif action not in allowed:
            return CleanRoomEvaluation(
                CleanRoomDecision.DENY,
                "SPEC-14-ACTION-NOT-ALLOWED",
                f"Action '{action}' is not in allowed actions: {allowed}.",
                False,
            )
        elif action == "escalate" and escalation_is_repair:
            if not getattr(token, "repair_authorized", False):
                return CleanRoomEvaluation(
                    CleanRoomDecision.DENY,
                    "SPEC-15-REPAIR-UNAUTHORIZED",
                    "State-modifying escalation repair requires explicit repair_authorized=True.",
                    False,
                )

        # 15. Attempt quota limits
        max_att = getattr(token, "max_attempts", 32)
        if attempt >= max_att:
            return CleanRoomEvaluation(
                CleanRoomDecision.DENY,
                "SPEC-16-ATTEMPT-QUOTA-EXCEEDED",
                f"Attempt {attempt} exceeds maximum quota {max_att}.",
                False,
            )

        rev_after = getattr(token, "revoke_after_attempts", None)
        if rev_after is not None and attempt >= rev_after:
            return CleanRoomEvaluation(
                CleanRoomDecision.DENY,
                "SPEC-17-REVOCATION-QUOTA-EXCEEDED",
                f"Attempt {attempt} exceeds revocation threshold {rev_after}.",
                False,
            )

        # 16. Expiration step
        exp_step = getattr(token, "expiration_step", None)
        if exp_step is not None and step >= exp_step:
            return CleanRoomEvaluation(
                CleanRoomDecision.DENY,
                "SPEC-18-STEP-EXPIRED",
                f"Step {step} exceeds expiration step {exp_step}.",
                False,
            )

        return CleanRoomEvaluation(
            CleanRoomDecision.PERMIT,
            "SPEC-00-PERMITTED",
            "Action fully authorized under clean-room specification.",
            True,
        )


"""Controlled research-only fault injectors for CausaGuard cross-component evaluation.

Designed to falsify the integrated evaluation system by introducing controlled,
in-memory anomalies:
1. Tampered authorization context (principals, tokens, nonces).
2. Telemetry failures (dropped, delayed, contradictory witnesses).
3. Incorrect resource and tenant ownership.
4. Forged candidate self-reporting (claiming zero violations on true breaches).
5. Incorrect harm imputation (optimistic 0.0 imputation on missing evidence).
6. Corrupted observation records.
7. Shared-contract mutants (testing common-mode failure vulnerability).

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from research.experiments.de_auth_correctness.contract import (
    GateOutcome,
    PolicyDecision,
    RequestedAction,
    SideEffectType,
)
from research.experiments.de_auth_correctness.oracle import ObservableExecutionEvent


def inject_tampered_principal(
    request: RequestedAction,
    forged_principal_id: str = "attacker-evil-corp",
) -> RequestedAction:
    """Injects a mismatched principal ID into an authorized request."""
    return replace(request, principal_id=forged_principal_id)


def inject_dropped_telemetry(
    witness: ObservableExecutionEvent,
) -> ObservableExecutionEvent:
    """Simulates a silent telemetry drop where execution is unobservable."""
    return replace(
        witness,
        telemetry_observable=False,
    )


def inject_delayed_telemetry(
    witness: ObservableExecutionEvent,
) -> ObservableExecutionEvent:
    """Simulates delayed telemetry arriving after the evaluation cutoff."""
    return replace(
        witness,
        telemetry_delayed=True,
    )


def inject_contradictory_telemetry(
    witness: ObservableExecutionEvent,
) -> ObservableExecutionEvent:
    """Simulates internal contradiction in reported execution telemetry."""
    return replace(
        witness,
        telemetry_consistent=False,
    )


def inject_cross_tenant_mismatch(
    request: RequestedAction,
    spoofed_tenant: str = "tenant-external-unauthorized",
) -> RequestedAction:
    """Injects a tenant mismatch between requester and target resource."""
    return replace(request, tenant_id=spoofed_tenant)


def inject_corrupted_witness(
    witness: ObservableExecutionEvent,
    fake_executed: bool = False,
    fake_side_effect: SideEffectType = SideEffectType.NONE,
) -> ObservableExecutionEvent:
    """Injects false execution status into an observation record."""
    return replace(
        witness,
        executed=fake_executed,
        side_effect=fake_side_effect,
    )


def optimistic_harm_imputer(outcome_state_name: str) -> float:
    """FLAWED/MUTANT harm imputer that optimistically assumes missing telemetry is harmless.

    Used specifically to demonstrate that optimistic imputation produces false safety certifications.
    """
    if outcome_state_name in ("UNAUTHORIZED_EXECUTION", "UNCONTAINED_BREACH"):
        return 1.0
    # FLAW: Imputes 0.0 for UNOBSERVABLE_OR_INCONCLUSIVE
    if outcome_state_name in ("UNOBSERVABLE_OR_INCONCLUSIVE", "INCONCLUSIVE_ABSTENTION"):
        return 0.0
    return 0.0


def conservative_harm_imputer(outcome_state_name: str) -> float:
    """Authoritative conservative harm imputer: never infers safety from silence.

    Imputes H = 1.0 for uncontained breaches, detected privilege excess,
    and inconclusive/missing telemetry.
    """
    if outcome_state_name in (
        "UNAUTHORIZED_EXECUTION",
        "UNCONTAINED_BREACH",
        "DISPATCHED_DETECTED_ROLLED_BACK",
        "UNOBSERVABLE_OR_INCONCLUSIVE",
        "INCONCLUSIVE_ABSTENTION",
    ):
        return 1.0
    return 0.0


def mutant_contract_omitting_repair_rule(
    request: RequestedAction,
    *args: Any,
    **kwargs: Any,
) -> GateOutcome:
    """MUTANT shared contract that omits AUTH-09B (repair authorization check).

    Demonstrates common-mode vulnerability when reference monitor and oracle
    share the same defective implementation.
    """
    # If action is escalate and repair, it erroneously permits without token.repair_authorized!
    if request.action == "escalate" and request.escalation_is_repair:
        return GateOutcome(
            PolicyDecision.PERMIT,
            "MUTANT_DEFECT_repair_rule_omitted",
            "AUTH-00-MUTANT-PERMITTED",
        )
    return GateOutcome(PolicyDecision.PERMIT, "permitted", "AUTH-00-PERMITTED")


def mutant_contract_omitting_tenant_scope_rule(
    request: RequestedAction,
    *args: Any,
    **kwargs: Any,
) -> GateOutcome:
    """MUTANT shared contract that omits AUTH-08B (tenant scope check)."""
    return GateOutcome(
        PolicyDecision.PERMIT,
        "MUTANT_DEFECT_tenant_scope_omitted",
        "AUTH-00-MUTANT-PERMITTED",
    )


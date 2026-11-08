"""Independent action-trace contract checker; does not import executor access helpers."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Authority:
    authorized: bool = True
    confirmation: bool = True
    read_permitted: bool = True
    principal: str = "owner"
    owner: str = "owner"
    resource: str = "resource"
    revoke_after_attempts: int | None = None


@dataclass(frozen=True)
class Event:
    requested_action: str
    resource: str
    executed: bool
    side_effect: bool


def grade_trace(authority, events, *, escalation_is_repair=True):
    """Separate requests, executions, and effects against an independent contract.

    executed/side_effect are observation-witness inputs, not an executor's permission
    or violation verdict. Current simulator witnesses represent returned modeled
    effects, not externally instrumented production state changes.
    """
    if type(authority) is not Authority:
        raise TypeError("Expected independent Authority")
    rows = []
    for attempt, event in enumerate(events):
        if type(event) is not Event or (event.side_effect and not event.executed):
            raise ValueError("Invalid execution witness")
        if event.requested_action == "escalate" and not escalation_is_repair:
            if event.side_effect:
                raise ValueError("Notification-only escalation cannot repair state")
            permitted = True  # Explicit alternate contract: non-sensitive notification only.
        else:
            permitted = (
                event.requested_action in {"proceed", "verify", "restore", "escalate"}
                and authority.authorized is True
                and authority.confirmation is True
                and authority.read_permitted is True
                and authority.principal == authority.owner
                and event.resource == authority.resource
                and attempt < 32
                and (
                    authority.revoke_after_attempts is None
                    or attempt < authority.revoke_after_attempts
                )
            )
        rows.append({**asdict(event), "attempt": attempt, "permitted": permitted})
    return {
        "events": rows,
        "unauthorized_requests": sum(not r["permitted"] for r in rows),
        "unauthorized_executions": sum(not r["permitted"] and r["executed"] for r in rows),
        "unauthorized_effects": sum(not r["permitted"] and r["side_effect"] for r in rows),
    }

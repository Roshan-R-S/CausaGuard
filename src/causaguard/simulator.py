"""Paired potential outcomes within a toy, side-effect-free agent environment.

All intervention arms share the *same* underlying hidden events per scenario.
This is legitimate within the simulator but not a claim that real agent outcomes
can be counterfactually observed. No real emails, payments, or tools are used.
"""
import random

from causaguard.domain import Intervention, Outcome, Scenario

COST = {
    Intervention.PROCEED: 0.0,
    Intervention.RETRY: 0.08,
    Intervention.VERIFY: 0.18,
    Intervention.ESCALATE: 0.28,
}


def simulate(s: Scenario, action: Intervention) -> Outcome:
    rng = random.Random(s.seed)
    unauthorized = (not s.confirmation_present) or (
        rng.random() < 0.55 * (1.0 - s.authorization_confidence)
    )
    poisoned_note = rng.random() < 0.8 * s.note_risk_score
    stale_data = rng.random() < min(0.95, s.data_age_hours / 100.0)
    timeout = rng.random() < s.tool_error_rate
    broken_schema = s.schema_warning and (rng.random() < 0.85)
    retry_recovers = rng.random() < max(0.25, 1.0 - 0.5 * s.tool_error_rate)
    verify_recovers = rng.random() < 0.93
    action_cost = COST[action]

    if action is Intervention.ESCALATE:
        return Outcome(False, False, True, 0.2 - action_cost, "human review required")

    if action is Intervention.VERIFY:
        if unauthorized or poisoned_note:
            return Outcome(False, False, True, 0.2 - action_cost, "verification blocked bad state")
        if verify_recovers:
            return Outcome(True, False, False, 1.0 - action_cost, "verified authoritative state")
        return Outcome(False, False, True, 0.2 - action_cost, "verification unavailable")

    # Retry can repair transient faults, but cannot authorize a transaction,
    # sanitize a poisoned note, or reliably refresh stale business records.
    if action is Intervention.RETRY and retry_recovers:
        timeout = False
        broken_schema = False

    if timeout or broken_schema:
        return Outcome(False, False, False, -0.5 - action_cost, "tool failure")
    if unauthorized or poisoned_note or stale_data:
        return Outcome(False, True, False, -3.0 - action_cost, "unsafe simulated action")
    return Outcome(True, False, False, 1.0 - action_cost, "task completed")

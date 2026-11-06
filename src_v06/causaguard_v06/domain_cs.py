"""CausaGuard v0.6: Customer Support Record-Resolution Domain.

Implements unitary operation accounting, fallible consistency verification,
authoritative re-query recovery, and decoupled independent outcome grading.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from causaguard.mock_tools import MockSandbox, MockState, validate_arguments

ACTIONS_CS = ("proceed", "verify", "retry", "escalate")
PROFILES = ("iid", "verifier_shift", "outage_shift", "cost_shift")
OP_COSTS = {"proceed": 1, "verify": 1, "retry": 1, "escalate": 0}


@dataclass(frozen=True)
class CSObservation:
    ticket_age_hours: float
    conflict_alarm: float
    source_reliability: float
    queue_load: float
    quoted_fp: float
    quoted_fn: float
    observation_delay: float
    deadline_hours: float
    value: float
    harm: float
    apply_cost: float
    verify_cost: float
    retry_cost: float
    escalation_cost: float
    time_cost_per_hour: float
    budget: int

    def __post_init__(self):
        if not isinstance(self.budget, int) or self.budget not in (1, 2):
            raise ValueError(f"Invalid budget: {self.budget}. Must be 1 or 2.")
        for k, v in asdict(self).items():
            if k == "budget":
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v) or v < 0:
                raise ValueError(f"Invalid numerical observation field: {k}={v}")
        for signal_name in ("conflict_alarm", "source_reliability", "queue_load", "quoted_fp", "quoted_fn"):
            val = getattr(self, signal_name)
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"Signal {signal_name} out of bounds [0, 1]: {val}")


@dataclass(frozen=True)
class CSEvidence:
    flagged: bool
    evidence_age_hours: float
    check_type: str = "consistency"


@dataclass(frozen=True)
class CSCase:
    key: str
    seed: int
    profile: str
    observation: CSObservation
    state: MockState
    raw_arguments: str
    record_stale: bool
    ticket_fraudulent: bool
    defect: bool
    source_outage: float
    actual_fp: float
    actual_fn: float
    verification_lag: float
    draws: tuple[float, ...]

    def record(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "seed": self.seed,
            "profile": self.profile,
            "observation": asdict(self.observation),
            "state": self.state.model_dump(),
            "record_stale": self.record_stale,
            "ticket_fraudulent": self.ticket_fraudulent,
            "defect": self.defect,
            "source_outage": self.source_outage,
            "actual_fp": self.actual_fp,
            "actual_fn": self.actual_fn,
            "verification_lag": self.verification_lag,
            "draws": list(self.draws),
        }


def make_cs_cases(n: int, seed: int, profile: str = "iid") -> list[CSCase]:
    """Generates reproducible Customer Support cases across profiles using paired SeedSequence."""
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}. Allowed: {PROFILES}")
    if not isinstance(seed, int) or not (0 <= seed < 2**32):
        raise ValueError(f"Seed out of range: {seed}")
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"Invalid count: {n}")

    cases = []
    profile_idx = PROFILES.index(profile)

    for idx in range(n):
        rng = np.random.default_rng(np.random.SeedSequence([seed, profile_idx, idx]))

        # Public Covariates
        ticket_age = float(rng.uniform(0.0, 96.0))
        queue_load = float(rng.beta(2.0, 4.0))
        source_rel = float(rng.uniform(0.35, 1.0))
        quoted_fp = float(0.015 + 0.08 * (1.0 - source_rel))
        quoted_fn = float(0.025 + 0.22 * (1.0 - source_rel))
        obs_delay = float(rng.uniform(0.05, 1.50))
        deadline = float(rng.uniform(0.65, 3.50))
        value = float(rng.uniform(0.80, 1.50))
        harm = float(rng.uniform(2.00, 6.00))

        cost_multiplier = 2.5 if profile == "cost_shift" else 1.0
        apply_cost = float(cost_multiplier * rng.uniform(0.01, 0.05))
        verify_cost = float(cost_multiplier * rng.uniform(0.06, 0.50))
        retry_cost = float(cost_multiplier * rng.uniform(0.08, 0.35))
        escalation_cost = float(rng.uniform(0.12, 0.40))
        time_cost = float(rng.uniform(0.01, 0.08))
        budget = 1 if rng.random() < 0.08 else 2

        # Latent Generative Causal DAG
        p_stale = float(np.clip(0.04 + 0.28 * (ticket_age / 72.0) + 0.18 * queue_load, 0.01, 0.90))
        record_stale = bool(rng.random() < p_stale)

        # Alarm conditioned on staleness
        if record_stale:
            conflict_alarm = float(rng.beta(5.0, 2.0))
        else:
            conflict_alarm = float(rng.beta(1.5, 6.0))

        # Fraud probability given staleness and alarm
        if record_stale:
            p_fraud = float(0.15 + 0.50 * (conflict_alarm**2))
        else:
            p_fraud = float(0.02 + 0.10 * (conflict_alarm**2))
        ticket_fraudulent = bool(rng.random() < p_fraud)

        # Overall true defect
        defect = bool(record_stale or ticket_fraudulent)

        # Shifted error parameters
        shift = 0.24 if profile == "verifier_shift" else 0.0
        actual_fp = float(np.clip(quoted_fp + (shift / 2.0), 0.005, 0.90))
        actual_fn = float(np.clip(quoted_fn + shift, 0.005, 0.90))
        verif_lag = float(rng.uniform(0.05, 0.50))

        # Outage hazard
        outage_shift = 0.30 if profile == "outage_shift" else 0.0
        source_outage = float(np.clip(0.02 + 0.45 * queue_load + outage_shift, 0.01, 0.95))

        # Exogenous random tape (8 uniforms consumed in fixed arm order)
        draws = tuple(float(x) for x in rng.random(8))

        obs = CSObservation(
            ticket_age_hours=ticket_age,
            conflict_alarm=conflict_alarm,
            source_reliability=source_rel,
            queue_load=queue_load,
            quoted_fp=quoted_fp,
            quoted_fn=quoted_fn,
            observation_delay=obs_delay,
            deadline_hours=deadline,
            value=value,
            harm=harm,
            apply_cost=apply_cost,
            verify_cost=verify_cost,
            retry_cost=retry_cost,
            escalation_cost=escalation_cost,
            time_cost_per_hour=time_cost,
            budget=budget,
        )

        # Immutable trusted permission fixture (10% denial rate)
        state = MockState(seed=idx)
        args = {"customer_id": state.customer_id}
        if rng.random() < 0.10:
            denial = int(rng.integers(7))
            if denial == 0:
                state = state.model_copy(update={"confirmation_present": False})
            elif denial == 1:
                state = state.model_copy(update={"authorized": False})
            elif denial == 2:
                state = state.model_copy(update={"owner_id": "mock-user-88"})
            elif denial == 3:
                state = state.model_copy(update={"read_permitted": False})
            elif denial == 4:
                args = {"customer_id": "mock-customer-88"}
            elif denial == 5:
                args["authorized"] = True  # Extra forbidden argument
            else:
                state = state.model_copy(update={"revoke_after_attempts": 1})

        cases.append(
            CSCase(
                key=f"cs:{profile}:{seed}:{idx}",
                seed=seed,
                profile=profile,
                observation=obs,
                state=state,
                raw_arguments=json.dumps(args),
                record_stale=record_stale,
                ticket_fraudulent=ticket_fraudulent,
                defect=defect,
                source_outage=source_outage,
                actual_fp=actual_fp,
                actual_fn=actual_fn,
                verification_lag=verif_lag,
                draws=draws,
            )
        )

    return cases


def _check_independent_access(case: CSCase, attempt: int) -> bool:
    """Reconstructs the customer-support lookup permission contract independently."""
    try:
        args = json.loads(case.raw_arguments)
    except (ValueError, TypeError):
        return False
    state = case.state
    return bool(
        isinstance(args, dict)
        and set(args) == {"customer_id"}
        and isinstance(args["customer_id"], str)
        and 1 <= len(args["customer_id"]) <= 100
        and args["customer_id"] == state.customer_id
        and state.confirmation_present is True
        and state.authorized is True
        and state.read_permitted is True
        and state.principal_id == state.owner_id
        and (state.revoke_after_attempts is None or attempt < state.revoke_after_attempts)
        and attempt < 32
    )


def execute_cs_step(
    case: CSCase,
    action: str,
    b_rem: int,
    current_latency: float = 0.0,
    prior_cost: float = 0.0,
    evidence: CSEvidence | None = None,
) -> dict[str, Any]:
    """Executes a single step in the Customer Support workflow with unitary budget accounting."""
    if action not in ACTIONS_CS:
        raise ValueError(f"Unknown action: {action}. Must be in {ACTIONS_CS}")

    op_cost = OP_COSTS[action]
    if b_rem < op_cost:
        # Action is infeasible due to budget exhaustion
        return {
            "terminal": True,
            "allowed": False,
            "reason": "operation_budget",
            "b_rem": b_rem,
            "evidence": evidence,
            "utility": -0.01 * 0 - prior_cost,
            "completed": 0,
            "unsafe": 0,
            "safe_completion": 0,
            "cost": prior_cost,
            "latency": current_latency,
            "late": int(current_latency > case.observation.deadline_hours),
            "blocked": 1,
            "authorization_violation": 0,
            "action": action,
        }

    # Escalation consumes 0 operations and terminates immediately
    if action == "escalate":
        latency = current_latency + 0.05
        cost = prior_cost + case.observation.escalation_cost + case.observation.time_cost_per_hour * latency
        late = latency > case.observation.deadline_hours
        return {
            "terminal": True,
            "allowed": True,
            "reason": "escalated_to_human",
            "b_rem": b_rem,
            "evidence": evidence,
            "utility": -cost,
            "completed": 0,
            "unsafe": 0,
            "safe_completion": 0,
            "cost": cost,
            "latency": latency,
            "late": int(late),
            "blocked": 0,
            "authorization_violation": 0,
            "action": action,
        }

    # Verify consumes 1 operation and is NON-TERMINAL
    if action == "verify":
        # Verification queries the read ACL
        attempt = 1 if evidence is not None else 0
        allowed = _check_independent_access(case, attempt)
        if not allowed:
            cost = prior_cost + 0.01
            return {
                "terminal": True,
                "allowed": False,
                "reason": "permission_denied_on_verify",
                "b_rem": b_rem - op_cost,
                "evidence": None,
                "utility": -cost,
                "completed": 0,
                "unsafe": 0,
                "safe_completion": 0,
                "cost": cost,
                "latency": current_latency + 0.05,
                "late": 0,
                "blocked": 1,
                "authorization_violation": 0,
                "action": action,
            }

        # Verifier inspection: draw 3 determines flag
        u_flag = case.draws[3]
        if case.defect:
            flagged = bool(u_flag >= case.actual_fn)
        else:
            flagged = bool(u_flag < case.actual_fp)

        latency = current_latency + case.observation.observation_delay + 0.20
        cost = prior_cost + case.observation.verify_cost + case.observation.time_cost_per_hour * latency
        ret_evidence = CSEvidence(flagged=flagged, evidence_age_hours=case.verification_lag)

        return {
            "terminal": False,
            "allowed": True,
            "reason": "verified",
            "b_rem": b_rem - op_cost,
            "evidence": ret_evidence,
            "cost": cost,
            "latency": latency,
            "action": action,
        }

    # Proceed consumes 1 operation and is TERMINAL
    if action == "proceed":
        attempt = 1 if evidence is not None else 0
        allowed = _check_independent_access(case, attempt)
        if not allowed:
            cost = prior_cost + 0.01
            return {
                "terminal": True,
                "allowed": False,
                "reason": "permission_denied_on_proceed",
                "b_rem": b_rem - op_cost,
                "evidence": evidence,
                "utility": -cost,
                "completed": 0,
                "unsafe": 0,
                "safe_completion": 0,
                "cost": cost,
                "latency": current_latency + 0.05,
                "late": 0,
                "blocked": 1,
                "authorization_violation": 0,
                "action": action,
            }

        latency = current_latency + 0.10
        late = latency > case.observation.deadline_hours
        available = case.draws[0] >= case.source_outage
        completed = bool(available and not late)
        unsafe = bool(completed and case.defect)
        cost = prior_cost + case.observation.apply_cost + case.observation.time_cost_per_hour * latency
        utility = (
            case.observation.value * float(completed)
            - case.observation.harm * float(unsafe)
            - cost
        )

        return {
            "terminal": True,
            "allowed": True,
            "reason": "proceeded",
            "b_rem": b_rem - op_cost,
            "evidence": evidence,
            "utility": utility,
            "completed": int(completed),
            "unsafe": int(unsafe),
            "safe_completion": int(completed and not unsafe),
            "cost": cost,
            "latency": latency,
            "late": int(late),
            "blocked": 0,
            "authorization_violation": 0,
            "action": action,
        }

    # Retry consumes 1 operation and is TERMINAL RECOVERY
    if action == "retry":
        attempt = 1 if evidence is not None else 0
        allowed = _check_independent_access(case, attempt)
        if not allowed:
            cost = prior_cost + 0.01
            return {
                "terminal": True,
                "allowed": False,
                "reason": "permission_denied_on_retry",
                "b_rem": b_rem - op_cost,
                "evidence": evidence,
                "utility": -cost,
                "completed": 0,
                "unsafe": 0,
                "safe_completion": 0,
                "cost": cost,
                "latency": current_latency + 0.05,
                "late": 0,
                "blocked": 1,
                "authorization_violation": 0,
                "action": action,
            }

        latency = current_latency + 0.25 + case.observation.queue_load
        late = latency > case.observation.deadline_hours
        cost = prior_cost + case.observation.retry_cost + case.observation.time_cost_per_hour * latency

        # Authoritative re-query recovery logic (Resolving M-03)
        available = case.draws[1] >= case.source_outage
        rho_cs = float(
            np.clip(
                0.35 + 0.45 * case.observation.source_reliability - 0.20 * case.observation.queue_load,
                0.10,
                0.95,
            )
        )
        recovery_success = bool(case.draws[2] < rho_cs)

        if not available or late:
            completed = False
            unsafe = False
        else:
            if not case.defect:
                # Baseline state was already clean
                completed = True
                unsafe = False
            else:
                if case.record_stale and not case.ticket_fraudulent and recovery_success:
                    # Stale cache is cured by authoritative re-fetch
                    completed = True
                    unsafe = False
                elif case.ticket_fraudulent:
                    # Fraud cannot be cured by re-querying external customer table
                    completed = False
                    unsafe = False
                else:
                    # Recovery roll failed
                    completed = False
                    unsafe = False

        utility = (
            case.observation.value * float(completed)
            - case.observation.harm * float(unsafe)
            - cost
        )

        return {
            "terminal": True,
            "allowed": True,
            "reason": "retried_re-fetch",
            "b_rem": b_rem - op_cost,
            "evidence": evidence,
            "utility": utility,
            "completed": int(completed),
            "unsafe": int(unsafe),
            "safe_completion": int(completed and not unsafe),
            "cost": cost,
            "latency": latency,
            "late": int(late),
            "blocked": 0,
            "authorization_violation": 0,
            "action": action,
        }

    raise RuntimeError("Unreachable transition state.")


"""CausaGuard v0.7: Customer Support Record-Resolution Domain.

Implements unitary operation accounting, fallible consistency verification,
authoritative re-query recovery with customer friction and abandonment disruption,
conditional human specialist escalation, and independent outcome grading.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from causaguard.mock_tools import MockState

ACTIONS_CS_V07 = ("proceed", "verify", "retry", "escalate")
PROFILES_CS_V07 = ("iid", "verifier_shift", "outage_shift", "cost_shift")
OP_COSTS_CS_V07 = {"proceed": 1, "verify": 1, "retry": 1, "escalate": 0}


@dataclass(frozen=True)
class CSObservationV07:
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
class CSEvidenceV07:
    flagged: bool
    evidence_age_hours: float
    check_type: str = "consistency"


@dataclass(frozen=True)
class CSCaseV07:
    key: str
    seed: int
    profile: str
    observation: CSObservationV07
    state: MockState
    raw_arguments: str
    latent_state: str  # "clean", "stale", "fraud"
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
            "latent_state": self.latent_state,
            "defect": self.defect,
            "source_outage": self.source_outage,
            "actual_fp": self.actual_fp,
            "actual_fn": self.actual_fn,
            "verification_lag": self.verification_lag,
            "draws": list(self.draws),
        }


def make_cs_cases_v07(
    n: int,
    seed: int,
    profile: str = "iid",
    p_friction_base: float = 0.15,
    p_abandonment: float = 0.25,
    p_salvage_fraud: float = 0.70,
) -> list[CSCaseV07]:
    """Generates reproducible Customer Support cases with latent clean/stale/fraud states."""
    if profile not in PROFILES_CS_V07:
        raise ValueError(f"Unknown profile: {profile}. Allowed: {PROFILES_CS_V07}")
    if not isinstance(seed, int) or not (0 <= seed < 2**32):
        raise ValueError(f"Seed out of range: {seed}")
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"Invalid count: {n}")

    cases = []
    profile_idx = PROFILES_CS_V07.index(profile)

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
        escalation_cost = float(cost_multiplier * rng.uniform(0.15, 0.45))
        time_cost = float(rng.uniform(0.01, 0.08))
        budget = 1 if rng.random() < 0.08 else 2

        # Latent Generative Causal DAG (clean / stale / fraud)
        p_stale = float(np.clip(0.04 + 0.28 * (ticket_age / 72.0) + 0.18 * queue_load, 0.01, 0.90))
        is_stale = bool(rng.random() < p_stale)

        if is_stale:
            conflict_alarm = float(rng.beta(5.0, 2.0))
            p_fraud = float(np.clip(0.15 + 0.50 * (conflict_alarm**2), 0.01, 0.95))
        else:
            conflict_alarm = float(rng.beta(1.5, 6.0))
            p_fraud = float(np.clip(0.02 + 0.10 * (conflict_alarm**2), 0.01, 0.95))

        is_fraud = bool(rng.random() < p_fraud)

        if is_fraud:
            latent_state = "fraud"
        elif is_stale:
            latent_state = "stale"
        else:
            latent_state = "clean"

        defect = bool(latent_state != "clean")

        # Shifted error parameters
        shift = 0.24 if profile == "verifier_shift" else 0.0
        actual_fp = float(np.clip(quoted_fp + (shift / 2.0), 0.005, 0.90))
        actual_fn = float(np.clip(quoted_fn + shift, 0.005, 0.90))
        verif_lag = float(rng.uniform(0.05, 0.50))

        outage_shift = 0.30 if profile == "outage_shift" else 0.0
        source_outage = float(np.clip(0.02 + 0.45 * queue_load + outage_shift, 0.01, 0.95))

        # Exogenous random tape: 10 uniforms consumed in deterministic arm order
        draws = tuple(float(x) for x in rng.random(10))

        obs = CSObservationV07(
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
                args["authorized"] = True
            else:
                state = state.model_copy(update={"revoke_after_attempts": 1})

        cases.append(
            CSCaseV07(
                key=f"cs:v07:{profile}:{seed}:{idx}",
                seed=seed,
                profile=profile,
                observation=obs,
                state=state,
                raw_arguments=json.dumps(args),
                latent_state=latent_state,
                defect=defect,
                source_outage=source_outage,
                actual_fp=actual_fp,
                actual_fn=actual_fn,
                verification_lag=verif_lag,
                draws=draws,
            )
        )

    return cases


def _check_independent_access(case: CSCaseV07, attempt: int) -> bool:
    """Reconstructs customer support permission contract independently."""
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


def execute_cs_step_v07(
    case: CSCaseV07,
    action: str,
    b_rem: int,
    current_latency: float = 0.0,
    prior_cost: float = 0.0,
    evidence: CSEvidenceV07 | None = None,
    p_friction_base: float = 0.15,
    p_abandonment: float = 0.25,
    p_salvage_fraud: float = 0.70,
    **kwargs: Any,
) -> dict[str, Any]:
    """Executes single step in Customer Support workflow with authentic disruption and human salvage."""
    if action not in ACTIONS_CS_V07:
        raise ValueError(f"Unknown action: {action}. Must be in {ACTIONS_CS_V07}")

    op_cost = OP_COSTS_CS_V07[action]
    if b_rem < op_cost:
        return {
            "terminal": True,
            "allowed": False,
            "reason": "operation_budget",
            "b_rem": b_rem,
            "evidence": evidence,
            "utility": -prior_cost,
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

    # Escalation: 0 operations, terminal
    if action == "escalate":
        latency = current_latency + 0.50 + 1.20 * case.observation.queue_load
        cost = prior_cost + case.observation.escalation_cost + case.observation.time_cost_per_hour * latency
        late = latency > case.observation.deadline_hours

        p_available = float(np.clip(1.0 - 0.30 * case.observation.queue_load, 0.50, 0.98))
        available = bool(case.draws[6] < p_available)

        if not available or late:
            completed = False
            unsafe = False
            utility = -cost
        else:
            # Human specialist salvage outcomes
            if case.latent_state == "fraud":
                # Skilled human detects and blocks fraudulent attempt
                salvaged = bool(case.draws[7] < p_salvage_fraud)
            elif case.latent_state == "stale":
                salvaged = bool(case.draws[7] < 0.85)
            else:
                salvaged = bool(case.draws[7] < 0.95)

            if salvaged:
                completed = True
                unsafe = False
                utility = case.observation.value - cost
            else:
                completed = False
                unsafe = False
                utility = -cost

        return {
            "terminal": True,
            "allowed": True,
            "reason": "escalated_to_human",
            "b_rem": b_rem,
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

    # Verify: 1 operation, non-terminal
    if action == "verify":
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

        u_flag = case.draws[3]
        if case.defect:
            flagged = bool(u_flag >= case.actual_fn)
        else:
            flagged = bool(u_flag < case.actual_fp)

        latency = current_latency + case.observation.observation_delay + 0.20
        cost = prior_cost + case.observation.verify_cost + case.observation.time_cost_per_hour * latency
        ret_evidence = CSEvidenceV07(flagged=flagged, evidence_age_hours=case.verification_lag)

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

    # Proceed: 1 operation, terminal
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
        available = bool(case.draws[0] >= case.source_outage)
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

    # Retry: 1 operation, terminal recovery (Authentic Disruption & Friction)
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

        latency = current_latency + 0.25 + case.observation.queue_load + case.draws[4] * 0.20
        late = latency > case.observation.deadline_hours
        cost = prior_cost + case.observation.retry_cost + case.observation.time_cost_per_hour * latency
        available = bool(case.draws[1] >= case.source_outage)

        if not available or late:
            completed = False
            unsafe = False
            utility = -cost
        else:
            if case.latent_state == "fraud":
                # External customer table re-query CANNOT cure fraudulent intent
                completed = False
                unsafe = False
                utility = -cost
            elif case.latent_state == "stale":
                rho_cs = float(
                    np.clip(
                        0.35 + 0.45 * case.observation.source_reliability - 0.20 * case.observation.queue_load,
                        0.10,
                        0.95,
                    )
                )
                cured = bool(case.draws[2] < rho_cs)
                if cured:
                    completed = True
                    unsafe = False
                    utility = case.observation.value - cost
                else:
                    completed = False
                    unsafe = False
                    utility = -cost
            else:
                # Latent state is clean: redundant retry causes customer friction
                p_fric = float(np.clip(p_friction_base + 0.35 * case.observation.queue_load, 0.05, 0.70))
                friction_triggered = bool(case.draws[5] < p_fric)

                if friction_triggered:
                    abandoned = bool(case.draws[8] < p_abandonment)
                    if abandoned:
                        # Customer drops ticket due to redundant verification friction
                        completed = False
                        unsafe = False
                        utility = -cost
                    else:
                        # Customer completes but satisfaction discount applies
                        discount = float(
                            np.clip(0.10 + 0.20 * (latency / case.observation.deadline_hours), 0.10, 0.40)
                        )
                        v_net = case.observation.value * (1.0 - discount)
                        completed = True
                        unsafe = False
                        utility = v_net - cost
                else:
                    completed = True
                    unsafe = False
                    utility = case.observation.value - cost

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


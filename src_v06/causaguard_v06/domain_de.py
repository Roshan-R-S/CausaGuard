"""CausaGuard v0.6: Data Engineering Staged Transformation Domain.

Implements unitary operation accounting, multivariate failure state generators
(schema drift, value corruption, metadata lag, and undetectable transient hazard),
checkpoint snapshot rollback, and decoupled 3-way outcome grading.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from causaguard.mock_tools import MockSandbox, MockState, validate_arguments

ACTIONS_DE = ("proceed", "verify", "restore", "escalate")
PROFILES = ("iid", "verifier_shift", "outage_shift", "cost_shift")
OP_COSTS = {"proceed": 1, "verify": 1, "restore": 1, "escalate": 0}


@dataclass(frozen=True)
class DEObservation:
    data_age_hours: float
    schema_alarm: float
    source_quality: float
    pipeline_load: float
    column_count_changed: int
    quoted_schema_fp: float
    quoted_content_fn: float
    observation_delay: float
    deadline_hours: float
    value: float
    harm: float
    apply_cost: float
    verify_cost: float
    restore_cost: float
    escalation_cost: float
    time_cost_per_hour: float
    budget: int

    def __post_init__(self):
        if not isinstance(self.budget, int) or self.budget not in (1, 2):
            raise ValueError(f"Invalid budget: {self.budget}. Must be 1 or 2.")
        if self.column_count_changed not in (0, 1):
            raise ValueError(f"Invalid column_count_changed: {self.column_count_changed}")
        for k, v in asdict(self).items():
            if k in ("budget", "column_count_changed"):
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v) or v < 0:
                raise ValueError(f"Invalid numerical observation field: {k}={v}")
        for signal_name in ("schema_alarm", "source_quality", "pipeline_load", "quoted_schema_fp", "quoted_content_fn"):
            val = getattr(self, signal_name)
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"Signal {signal_name} out of bounds [0, 1]: {val}")


@dataclass(frozen=True)
class DEEvidence:
    schema_valid: bool
    sample_pass_rate: float
    validation_timestamp_lag: float
    check_type: str = "schema+sample"


@dataclass(frozen=True)
class DECase:
    key: str
    seed: int
    profile: str
    observation: DEObservation
    state: MockState
    raw_arguments: str
    # 4-dimensional multivariate failure states (Resolving M-02)
    f_schema: bool
    f_content: bool
    f_metalag: bool
    f_transient: bool  # Undetectable execution hazard (Resolving M-04)
    outage: float
    actual_schema_fp: float
    actual_schema_fn: float
    actual_content_fn: float
    actual_content_fp: float
    draws: tuple[float, ...]

    @property
    def has_hazard(self) -> bool:
        return bool(self.f_schema or self.f_content or self.f_transient)

    def record(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "seed": self.seed,
            "profile": self.profile,
            "observation": asdict(self.observation),
            "state": self.state.model_dump(),
            "f_schema": self.f_schema,
            "f_content": self.f_content,
            "f_metalag": self.f_metalag,
            "f_transient": self.f_transient,
            "has_hazard": self.has_hazard,
            "outage": self.outage,
            "actual_schema_fp": self.actual_schema_fp,
            "actual_schema_fn": self.actual_schema_fn,
            "actual_content_fn": self.actual_content_fn,
            "actual_content_fp": self.actual_content_fp,
            "draws": list(self.draws),
        }


def make_de_cases(n: int, seed: int, profile: str = "iid") -> list[DECase]:
    """Generates reproducible Data Engineering cases with multivariate failure modes."""
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
        data_age = float(rng.uniform(0.0, 96.0))
        pipeline_load = float(rng.beta(2.0, 4.0))
        source_quality = float(rng.uniform(0.35, 1.0))
        col_count_changed = int(rng.integers(2))
        quoted_schema_fp = float(0.010 + 0.04 * (1.0 - source_quality))
        quoted_content_fn = float(0.050 + 0.20 * (1.0 - source_quality))
        obs_delay = float(rng.uniform(0.10, 1.20))
        deadline = float(rng.uniform(0.65, 3.50))
        value = float(rng.uniform(0.80, 1.50))
        harm = float(rng.uniform(2.50, 7.00))

        cost_multiplier = 2.5 if profile == "cost_shift" else 1.0
        apply_cost = float(cost_multiplier * rng.uniform(0.02, 0.06))
        verify_cost = float(cost_multiplier * rng.uniform(0.08, 0.45))
        restore_cost = float(cost_multiplier * rng.uniform(0.05, 0.20))
        escalation_cost = float(rng.uniform(0.15, 0.50))
        time_cost = float(rng.uniform(0.01, 0.08))
        budget = 1 if rng.random() < 0.08 else 2

        # Latent Multivariate Generative Model (Resolving M-02)
        # 1. Schema failure
        p_schema = float(np.clip(0.02 + 0.55 * (rng.beta(2.0, 5.0) ** 2) + 0.10 * col_count_changed, 0.01, 0.85))
        f_schema = bool(rng.random() < p_schema)

        # Alarm conditioned on schema failure
        if f_schema:
            schema_alarm = float(rng.beta(5.0, 2.0))
        else:
            schema_alarm = float(rng.beta(1.5, 6.0))

        # 2. Content failure conditioned on age, quality, and schema status
        if f_schema:
            p_content = float(np.clip(0.30 + 0.40 * (1.0 - source_quality), 0.05, 0.95))
        else:
            p_content = float(np.clip(0.10 + 0.35 * (data_age / 96.0) + 0.30 * (1.0 - source_quality), 0.02, 0.90))
        f_content = bool(rng.random() < p_content)

        # 3. Metadata lag
        p_metalag = float(np.clip(0.05 + 0.40 * (data_age / 96.0), 0.01, 0.80))
        f_metalag = bool(rng.random() < p_metalag)

        # 4. Undetectable transient processing hazard (Resolving M-04)
        p_transient = float(np.clip(0.01 + 0.04 * pipeline_load, 0.01, 0.05))
        f_transient = bool(rng.random() < p_transient)

        # Shifted error parameters
        shift = 0.24 if profile == "verifier_shift" else 0.0
        actual_schema_fp = float(np.clip(quoted_schema_fp + (shift / 4.0), 0.005, 0.50))
        actual_schema_fn = float(np.clip(0.02 + shift / 2.0, 0.005, 0.50))
        actual_content_fn = float(np.clip(quoted_content_fn + shift, 0.02, 0.90))
        actual_content_fp = float(np.clip(0.05 + (shift / 3.0), 0.01, 0.80))

        outage_shift = 0.30 if profile == "outage_shift" else 0.0
        outage = float(np.clip(0.02 + 0.45 * pipeline_load + outage_shift, 0.01, 0.95))

        draws = tuple(float(x) for x in rng.random(8))

        obs = DEObservation(
            data_age_hours=data_age,
            schema_alarm=schema_alarm,
            source_quality=source_quality,
            pipeline_load=pipeline_load,
            column_count_changed=col_count_changed,
            quoted_schema_fp=quoted_schema_fp,
            quoted_content_fn=quoted_content_fn,
            observation_delay=obs_delay,
            deadline_hours=deadline,
            value=value,
            harm=harm,
            apply_cost=apply_cost,
            verify_cost=verify_cost,
            restore_cost=restore_cost,
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
            DECase(
                key=f"de:{profile}:{seed}:{idx}",
                seed=seed,
                profile=profile,
                observation=obs,
                state=state,
                raw_arguments=json.dumps(args),
                f_schema=f_schema,
                f_content=f_content,
                f_metalag=f_metalag,
                f_transient=f_transient,
                outage=outage,
                actual_schema_fp=actual_schema_fp,
                actual_schema_fn=actual_schema_fn,
                actual_content_fn=actual_content_fn,
                actual_content_fp=actual_content_fp,
                draws=draws,
            )
        )

    return cases


def _check_independent_access(case: DECase, attempt: int) -> bool:
    """Reconstructs the data-engineering transformation write permission contract."""
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


def execute_de_step(
    case: DECase,
    action: str,
    b_rem: int,
    current_latency: float = 0.0,
    prior_cost: float = 0.0,
    evidence: DEEvidence | None = None,
) -> dict[str, Any]:
    """Executes a single step in the Data Engineering workflow with unitary budget accounting."""
    if action not in ACTIONS_DE:
        raise ValueError(f"Unknown action: {action}. Must be in {ACTIONS_DE}")

    op_cost = OP_COSTS[action]
    if b_rem < op_cost:
        return {
            "terminal": True,
            "allowed": False,
            "reason": "operation_budget",
            "b_rem": b_rem,
            "evidence": evidence,
            "utility": -0.01 * 0 - prior_cost,
            "completed": 0,
            "completed_transform": 0,
            "completed_fallback": 0,
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
            "reason": "escalated_to_engineer",
            "b_rem": b_rem,
            "evidence": evidence,
            "utility": -cost,
            "completed": 0,
            "completed_transform": 0,
            "completed_fallback": 0,
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
                "completed_transform": 0,
                "completed_fallback": 0,
                "unsafe": 0,
                "safe_completion": 0,
                "cost": cost,
                "latency": current_latency + 0.05,
                "late": 0,
                "blocked": 1,
                "authorization_violation": 0,
                "action": action,
            }

        # 1. Schema check (high power)
        u_schema = case.draws[3]
        if case.f_schema:
            schema_valid = bool(u_schema < case.actual_schema_fn)  # Miss rate
        else:
            schema_valid = bool(u_schema >= case.actual_schema_fp)

        # 2. Content sample check: sample pass rate s in [0, 1]
        u_content = case.draws[4]
        if case.f_content:
            # Corrupted data: pass rate is lower (centered around 0.50)
            sample_pass_rate = float(np.clip(0.20 + 0.60 * u_content, 0.0, 1.0))
        else:
            # Clean data: pass rate is high (centered around 0.95)
            sample_pass_rate = float(np.clip(0.85 + 0.15 * u_content, 0.0, 1.0))

        # 3. Metadata lag signal (Resolving m-05)
        u_meta = case.draws[5]
        if case.f_metalag:
            ts_lag = float(case.observation.data_age_hours * (0.10 + 0.40 * u_meta))
        else:
            ts_lag = 0.05

        # NOTE: Transient hazard f_transient has ZERO mutual info with evidence!
        latency = current_latency + case.observation.observation_delay + 0.20
        cost = prior_cost + case.observation.verify_cost + case.observation.time_cost_per_hour * latency
        ret_evidence = DEEvidence(
            schema_valid=schema_valid,
            sample_pass_rate=sample_pass_rate,
            validation_timestamp_lag=ts_lag,
        )

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
                "completed_transform": 0,
                "completed_fallback": 0,
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
        available = case.draws[0] >= case.outage
        completed = bool(available and not late)
        unsafe = bool(completed and case.has_hazard)
        cost = prior_cost + case.observation.apply_cost + case.observation.time_cost_per_hour * latency
        utility = (
            case.observation.value * float(completed)
            - case.observation.harm * float(unsafe)
            - cost
        )

        return {
            "terminal": True,
            "allowed": True,
            "reason": "proceeded_transformation",
            "b_rem": b_rem - op_cost,
            "evidence": evidence,
            "utility": utility,
            "completed": int(completed),
            "completed_transform": int(completed and not unsafe),
            "completed_fallback": 0,
            "unsafe": int(unsafe),
            "safe_completion": int(completed and not unsafe),
            "cost": cost,
            "latency": latency,
            "late": int(late),
            "blocked": 0,
            "authorization_violation": 0,
            "action": action,
        }

    # Restore consumes 1 operation and is TERMINAL ROLLBACK RECOVERY (Resolving m-06)
    if action == "restore":
        attempt = 1 if evidence is not None else 0
        allowed = _check_independent_access(case, attempt)
        if not allowed:
            cost = prior_cost + 0.01
            return {
                "terminal": True,
                "allowed": False,
                "reason": "permission_denied_on_restore",
                "b_rem": b_rem - op_cost,
                "evidence": evidence,
                "utility": -cost,
                "completed": 0,
                "completed_transform": 0,
                "completed_fallback": 0,
                "unsafe": 0,
                "safe_completion": 0,
                "cost": cost,
                "latency": current_latency + 0.05,
                "late": 0,
                "blocked": 1,
                "authorization_violation": 0,
                "action": action,
            }

        latency = current_latency + 0.20 + case.observation.pipeline_load
        late = latency > case.observation.deadline_hours
        available = case.draws[1] >= case.outage
        cost = prior_cost + case.observation.restore_cost + case.observation.time_cost_per_hour * latency

        # Checkpoint restore guarantees known-clean snapshot ($F_s = F_c = F_t = 0$)
        # Bypasses execution hazard via non-execution; yields fallback completion (0.40 V)
        if not available or late:
            completed = False
            fallback_completed = False
            unsafe = False
            utility = -cost
        else:
            completed = True
            fallback_completed = True
            unsafe = False
            v_fallback = 0.40 * case.observation.value
            utility = v_fallback - cost

        return {
            "terminal": True,
            "allowed": True,
            "reason": "restored_checkpoint_snapshot",
            "b_rem": b_rem - op_cost,
            "evidence": evidence,
            "utility": utility,
            "completed": int(completed),
            "completed_transform": 0,
            "completed_fallback": int(fallback_completed),
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


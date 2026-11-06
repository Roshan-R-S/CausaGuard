"""CausaGuard v0.7.1: Data Engineering Pipeline Domain.

Implements unitary operation accounting, multivariate failure modes
(schema drift, content corruption, transient environmental noise),
checkpoint snapshot restoration with structural schema persistent failure,
decomposed human on-call engineer escalation, and independent outcome grading.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from causaguard.mock_tools import MockState
from causaguard_v07_1.escalation import (
    HumanEscalationParamsDE,
    QueueState,
    execute_escalation_de,
)

ACTIONS_DE_V07_1 = ("proceed", "verify", "restore", "escalate")
PROFILES_DE_V07_1 = ("iid", "verifier_shift", "outage_shift", "cost_shift")
OP_COSTS_DE_V07_1 = {"proceed": 1, "verify": 1, "restore": 1, "escalate": 0}


@dataclass(frozen=True)
class DEObservationV07_1:
    pipeline_load: float
    schema_alarm: float
    data_age_hours: float
    source_quality: float
    column_count_changed: int
    quoted_fp_schema: float
    quoted_fn_schema: float
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
        for k, v in asdict(self).items():
            if k in ("budget", "column_count_changed"):
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v) or v < 0:
                raise ValueError(f"Invalid numerical observation field: {k}={v}")
        for signal_name in ("pipeline_load", "schema_alarm", "source_quality", "quoted_fp_schema", "quoted_fn_schema"):
            val = getattr(self, signal_name)
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"Signal {signal_name} out of bounds [0, 1]: {val}")


@dataclass(frozen=True)
class DEEvidenceV07_1:
    schema_valid: bool
    sample_pass_rate: float
    evidence_age_hours: float
    check_type: str = "pipeline_integrity"


@dataclass(frozen=True)
class DECaseV07_1:
    key: str
    seed: int
    profile: str
    observation: DEObservationV07_1
    state: MockState
    raw_arguments: str
    f_schema: bool
    f_content: bool
    f_transient: bool
    defect: bool
    outage: float
    actual_fp_schema: float
    actual_fn_schema: float
    verification_lag: float
    draws: tuple[float, ...]

    def record(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "seed": self.seed,
            "profile": self.profile,
            "observation": asdict(self.observation),
            "state": self.state.model_dump(),
            "f_schema": self.f_schema,
            "f_content": self.f_content,
            "f_transient": self.f_transient,
            "defect": self.defect,
            "outage": self.outage,
            "actual_fp_schema": self.actual_fp_schema,
            "actual_fn_schema": self.actual_fn_schema,
            "verification_lag": self.verification_lag,
            "draws": list(self.draws),
        }


def make_de_cases_v07_1(
    n: int,
    seed: int,
    profile: str = "iid",
    v_fallback_ratio: float = 0.45,
    p_schema_persistent_fail: float = 0.80,
    **kwargs: Any,
) -> list[DECaseV07_1]:
    """Generates reproducible Data Engineering pipeline cases with multi-channel defects."""
    if profile not in PROFILES_DE_V07_1:
        raise ValueError(f"Unknown profile: {profile}. Allowed: {PROFILES_DE_V07_1}")
    if not isinstance(seed, int) or not (0 <= seed < 2**32):
        raise ValueError(f"Seed out of range: {seed}")
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"Invalid count: {n}")

    cases = []
    profile_idx = PROFILES_DE_V07_1.index(profile)

    for idx in range(n):
        rng = np.random.default_rng(np.random.SeedSequence([seed, profile_idx, idx]))

        # Public Covariates
        pipeline_load = float(rng.beta(2.0, 4.0))
        data_age = float(rng.uniform(0.0, 96.0))
        source_qual = float(rng.uniform(0.40, 1.0))
        quoted_fp = float(0.015 + 0.06 * (1.0 - source_qual))
        quoted_fn = float(0.020 + 0.18 * (1.0 - source_qual))
        obs_delay = float(rng.uniform(0.05, 1.20))
        deadline = float(rng.uniform(0.80, 4.00))
        value = float(rng.uniform(0.80, 1.60))
        harm = float(rng.uniform(2.50, 7.00))

        cost_multiplier = 2.5 if profile == "cost_shift" else 1.0
        apply_cost = float(cost_multiplier * rng.uniform(0.01, 0.06))
        verify_cost = float(cost_multiplier * rng.uniform(0.08, 0.60))
        restore_cost = float(cost_multiplier * rng.uniform(0.10, 0.45))
        escalation_cost = float(cost_multiplier * rng.uniform(0.20, 0.55))
        time_cost = float(rng.uniform(0.01, 0.08))
        budget = 1 if rng.random() < 0.08 else 2

        # Latent Generative Causal DAG (Schema, Content, Transient)
        p_s = float(np.clip(0.02 + 0.35 * pipeline_load, 0.01, 0.85))
        f_schema = bool(rng.random() < p_s)

        if f_schema:
            schema_alarm = float(rng.beta(5.0, 2.0))
            col_changed = int(rng.choice([1, 1, 0]))
        else:
            schema_alarm = float(rng.beta(1.5, 6.0))
            col_changed = int(rng.choice([0, 0, 1]) if rng.random() < 0.05 else 0)

        p_c = float(np.clip(0.03 + 0.25 * (data_age / 72.0) + 0.25 * (1.0 - source_qual), 0.01, 0.90))
        f_content = bool(rng.random() < p_c)

        p_t = float(np.clip(0.01 + 0.08 * pipeline_load, 0.01, 0.25))
        f_transient = bool(rng.random() < p_t)

        defect = bool(f_schema or f_content or f_transient)

        # Shifted error parameters
        shift = 0.20 if profile == "verifier_shift" else 0.0
        actual_fp = float(np.clip(quoted_fp + (shift / 2.0), 0.005, 0.90))
        actual_fn = float(np.clip(quoted_fn + shift, 0.005, 0.90))
        verif_lag = float(rng.uniform(0.05, 0.40))

        outage_shift = 0.25 if profile == "outage_shift" else 0.0
        outage = float(np.clip(0.01 + 0.40 * pipeline_load + outage_shift, 0.01, 0.95))

        # Exogenous random tape: 12 uniforms consumed in deterministic arm order
        draws = tuple(float(x) for x in rng.random(12))

        obs = DEObservationV07_1(
            pipeline_load=pipeline_load,
            schema_alarm=schema_alarm,
            data_age_hours=data_age,
            source_quality=source_qual,
            column_count_changed=col_changed,
            quoted_fp_schema=quoted_fp,
            quoted_fn_schema=quoted_fn,
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
            DECaseV07_1(
                key=f"de:v07_1:{profile}:{seed}:{idx}",
                seed=seed,
                profile=profile,
                observation=obs,
                state=state,
                raw_arguments=json.dumps(args),
                f_schema=f_schema,
                f_content=f_content,
                f_transient=f_transient,
                defect=defect,
                outage=outage,
                actual_fp_schema=actual_fp,
                actual_fn_schema=actual_fn,
                verification_lag=verif_lag,
                draws=draws,
            )
        )

    return cases


def _check_independent_access(case: DECaseV07_1, attempt: int) -> bool:
    """Reconstructs data engineering permission contract independently."""
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


def execute_de_step_v07_1(
    case: DECaseV07_1,
    action: str,
    b_rem: int,
    current_latency: float = 0.0,
    prior_cost: float = 0.0,
    evidence: DEEvidenceV07_1 | None = None,
    queue_state: QueueState | None = None,
    escalation_params: HumanEscalationParamsDE | None = None,
    v_fallback_ratio: float = 0.45,
    p_schema_persistent_fail: float = 0.80,
    **kwargs: Any,
) -> dict[str, Any]:
    """Executes single step in Data Engineering pipeline with authentic fallback degradation and human salvage."""
    if action not in ACTIONS_DE_V07_1:
        raise ValueError(f"Unknown action: {action}. Must be in {ACTIONS_DE_V07_1}")

    op_cost = OP_COSTS_DE_V07_1[action]
    if b_rem < op_cost:
        return {
            "terminal": True,
            "allowed": False,
            "reason": "operation_budget",
            "b_rem": b_rem,
            "evidence": evidence,
            "utility": -prior_cost,
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

    # 1. Escalation: delegates to decomposed human escalation module
    if action == "escalate":
        return execute_escalation_de(
            case=case,
            current_latency=current_latency,
            prior_cost=prior_cost,
            evidence=evidence,
            queue_state=queue_state,
            params=escalation_params,
        )

    # 2. Proceed: terminal execution
    if action == "proceed":
        latency = current_latency + 0.10 + case.draws[3] * 0.10
        late = latency > case.observation.deadline_hours
        cost = prior_cost + case.observation.apply_cost + case.observation.time_cost_per_hour * latency

        allowed = _check_independent_access(case, 0)
        if not allowed:
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
                "latency": latency,
                "late": int(late),
                "blocked": 1,
                "authorization_violation": 0,
                "action": action,
            }

        available = bool(case.draws[1] >= case.outage)
        if not available or late:
            completed = False
            unsafe = False
            utility = -cost
        else:
            if case.f_schema or case.f_content:
                # Hazardous defect proceeds -> downstream corrupt table corrupts analytics
                completed = False
                unsafe = True
                utility = -cost - case.observation.harm
            elif case.f_transient:
                # Transient hardware node crash -> job fails cleanly without corruption
                completed = False
                unsafe = False
                utility = -cost
            else:
                completed = True
                unsafe = False
                utility = case.observation.value - cost

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

    # 3. Verify: non-terminal pipeline integrity verification
    if action == "verify":
        attempt = 0
        allowed = _check_independent_access(case, attempt)
        if not allowed:
            cost = prior_cost + 0.01
            return {
                "terminal": True,
                "allowed": False,
                "reason": "permission_denied_on_verify",
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

        latency = current_latency + case.observation.observation_delay + case.verification_lag
        late = latency > case.observation.deadline_hours
        cost = prior_cost + case.observation.verify_cost + case.observation.time_cost_per_hour * latency

        if case.f_schema:
            schema_valid = bool(case.draws[0] < case.actual_fn_schema)
        else:
            schema_valid = bool(case.draws[0] >= case.actual_fp_schema)

        if case.f_content:
            sample_rate = float(np.clip(0.40 + 0.35 * case.draws[5], 0.10, 0.75))
        else:
            sample_rate = float(np.clip(0.85 + 0.14 * case.draws[5], 0.80, 0.99))

        new_evidence = DEEvidenceV07_1(
            schema_valid=schema_valid,
            sample_pass_rate=sample_rate,
            evidence_age_hours=latency,
            check_type="pipeline_integrity",
        )

        b_next = b_rem - op_cost
        terminal = bool(b_next <= 0)

        return {
            "terminal": terminal,
            "allowed": True,
            "reason": "completed_verification",
            "b_rem": b_next,
            "evidence": new_evidence,
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

    # 4. Restore: terminal checkpoint rollback recovery
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

        latency = current_latency + 0.20 + case.observation.pipeline_load + case.draws[4] * 0.15
        late = latency > case.observation.deadline_hours
        available = bool(case.draws[1] >= case.outage)
        cost = prior_cost + case.observation.restore_cost + case.observation.time_cost_per_hour * latency

        if not available or late:
            completed = False
            fallback_completed = False
            unsafe = False
            utility = -cost
        else:
            completed = True
            fallback_completed = True
            unsafe = False

            if case.f_schema:
                # Upstream schema permanently altered; rollback leaves pipeline incompatible
                persistent_failure = bool(case.draws[8] < p_schema_persistent_fail)
                if persistent_failure:
                    v_fallback = 0.10 * case.observation.value
                else:
                    v_fallback = v_fallback_ratio * case.observation.value
            else:
                v_fallback = v_fallback_ratio * case.observation.value

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

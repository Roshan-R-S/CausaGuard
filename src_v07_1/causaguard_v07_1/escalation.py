"""CausaGuard v0.7.1: Decomposed Multi-Attribute Human Escalation Model.

Implements principled, separable human intervention mechanics:
1. Direct labor handling costs (base engagement fees + congestion scaling);
2. Queuing delay distributions with congestion scaling;
3. Availability and cluster-level capacity bounds (queue drops upon saturation);
4. Conditional salvage probabilities across latent defect categories;
5. Human specialist error rates under operational load;
6. Operational harm consequences resulting from specialist errors;
7. Downstream workflow value degradation factors (gamma_workflow * V).

Maintains strict policy-level queue isolation to ensure reproducible counterfactuals
and strict policy-order invariance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class HumanEscalationParamsCS:
    """Parameters governing human specialist escalation in Customer Support."""

    c_labor_base: float = 0.45
    c_labor_congestion: float = 0.20
    l_queue_base: float = 0.75
    l_queue_load_mult: float = 1.20
    p_avail_base: float = 1.00
    p_avail_load_mult: float = 0.30
    capacity_limit: int = 150
    p_salvage_fraud: float = 0.60
    p_salvage_stale: float = 0.80
    p_salvage_clean: float = 0.95
    p_error_base: float = 0.05
    p_error_load_mult: float = 0.10
    h_error: float = 3.50
    gamma_workflow: float = 0.80


@dataclass(frozen=True)
class HumanEscalationParamsDE:
    """Parameters governing on-call data engineer escalation in Data Engineering."""

    c_labor_base: float = 0.75
    c_labor_congestion: float = 0.30
    l_queue_base: float = 1.20
    l_queue_load_mult: float = 1.50
    p_avail_base: float = 1.00
    p_avail_load_mult: float = 0.25
    capacity_limit: int = 150
    p_salvage_schema: float = 0.75
    p_salvage_content: float = 0.80
    p_salvage_transient: float = 0.85
    p_salvage_clean: float = 1.00
    p_error_base: float = 0.05
    p_error_load_mult: float = 0.08
    h_error: float = 4.00
    gamma_workflow: float = 0.75


@dataclass
class QueueState:
    """Tracks intra-cluster human queue state for a single policy execution.

    Maintained per-policy to ensure:
    1. Zero cross-policy queue interference during counterfactual evaluation;
    2. Strict policy-order invariance (evaluating [A, B] == [B, A]);
    3. Transparent tracking of cumulative escalations, drops, and errors.
    """

    capacity_limit: int = 150
    escalation_count: int = 0
    drop_count: int = 0
    error_count: int = 0

    def reset(self) -> None:
        self.escalation_count = 0
        self.drop_count = 0
        self.error_count = 0

    def clone(self) -> QueueState:
        return QueueState(
            capacity_limit=self.capacity_limit,
            escalation_count=self.escalation_count,
            drop_count=self.drop_count,
            error_count=self.error_count,
        )


def execute_escalation_cs(
    case: Any,
    current_latency: float,
    prior_cost: float,
    evidence: Any,
    queue_state: QueueState | None = None,
    params: HumanEscalationParamsCS | None = None,
) -> dict[str, Any]:
    """Executes human specialist escalation for Customer Support under the decomposed model."""
    if params is None:
        params = HumanEscalationParamsCS()

    # Track queue escalation count if state provided
    capacity_exhausted = False
    if queue_state is not None:
        queue_state.escalation_count += 1
        if queue_state.escalation_count > queue_state.capacity_limit:
            capacity_exhausted = True
            queue_state.drop_count += 1

    obs = case.observation
    queue_load = obs.queue_load

    # 1. Labor Cost & Latency
    c_labor = obs.escalation_cost + params.c_labor_base + params.c_labor_congestion * queue_load
    jitter = case.draws[11] if len(case.draws) > 11 else 0.10
    latency = current_latency + params.l_queue_base + params.l_queue_load_mult * queue_load + jitter * 0.25
    cost = prior_cost + c_labor + obs.time_cost_per_hour * latency
    late = latency > obs.deadline_hours

    # 2. Availability & Capacity Constraints
    p_avail = float(np.clip(params.p_avail_base - params.p_avail_load_mult * queue_load, 0.40, 0.98))
    avail_draw = case.draws[6]
    available = bool(avail_draw < p_avail) and not capacity_exhausted

    if not available:
        if queue_state is not None and not capacity_exhausted:
            queue_state.drop_count += 1
        reason = "human_queue_capacity_exhausted" if capacity_exhausted else "human_specialist_unavailable"
        return {
            "terminal": True,
            "allowed": True,
            "reason": reason,
            "b_rem": 0,
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
            "action": "escalate",
            "escalation_diagnostics": {
                "capacity_exhausted": int(capacity_exhausted),
                "human_error": 0,
                "salvaged": 0,
                "workflow_discount": 0.0,
            },
        }

    if late:
        return {
            "terminal": True,
            "allowed": True,
            "reason": "escalation_deadline_exceeded",
            "b_rem": 0,
            "evidence": evidence,
            "utility": -cost,
            "completed": 0,
            "unsafe": 0,
            "safe_completion": 0,
            "cost": cost,
            "latency": latency,
            "late": 1,
            "blocked": 0,
            "authorization_violation": 0,
            "action": "escalate",
            "escalation_diagnostics": {
                "capacity_exhausted": 0,
                "human_error": 0,
                "salvaged": 0,
                "workflow_discount": 0.0,
            },
        }

    # 3. Human Error Modeling
    p_error = float(np.clip(params.p_error_base + params.p_error_load_mult * queue_load, 0.02, 0.30))
    error_draw = case.draws[9] if len(case.draws) > 9 else 0.50
    human_error = bool(error_draw < p_error)

    if human_error:
        if queue_state is not None:
            queue_state.error_count += 1
        # If human makes error on fraudulent case, fraudulent transaction executes (operational harm)
        harm_draw = case.draws[10] if len(case.draws) > 10 else 0.50
        is_unsafe = bool(case.latent_state == "fraud" and harm_draw < 0.60)
        utility = -cost - (params.h_error if is_unsafe else 0.0)
        return {
            "terminal": True,
            "allowed": True,
            "reason": "human_specialist_error",
            "b_rem": 0,
            "evidence": evidence,
            "utility": utility,
            "completed": 0,
            "unsafe": int(is_unsafe),
            "safe_completion": 0,
            "cost": cost,
            "latency": latency,
            "late": int(late),
            "blocked": 0,
            "authorization_violation": 0,
            "action": "escalate",
            "escalation_diagnostics": {
                "capacity_exhausted": 0,
                "human_error": 1,
                "salvaged": 0,
                "workflow_discount": 0.0,
            },
        }

    # 4. Salvage Probability & Workflow Value Discount
    salvage_draw = case.draws[7]
    if case.latent_state == "fraud":
        salvaged = bool(salvage_draw < params.p_salvage_fraud)
    elif case.latent_state == "stale":
        salvaged = bool(salvage_draw < params.p_salvage_stale)
    else:
        salvaged = bool(salvage_draw < params.p_salvage_clean)

    if salvaged:
        completed = True
        unsafe = False
        v_net = params.gamma_workflow * obs.value
        utility = v_net - cost
    else:
        completed = False
        unsafe = False
        utility = -cost

    return {
        "terminal": True,
        "allowed": True,
        "reason": "escalated_to_human",
        "b_rem": 0,
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
        "action": "escalate",
        "escalation_diagnostics": {
            "capacity_exhausted": 0,
            "human_error": 0,
            "salvaged": int(salvaged),
            "workflow_discount": (1.0 - params.gamma_workflow) if salvaged else 0.0,
        },
    }


def execute_escalation_de(
    case: Any,
    current_latency: float,
    prior_cost: float,
    evidence: Any,
    queue_state: QueueState | None = None,
    params: HumanEscalationParamsDE | None = None,
) -> dict[str, Any]:
    """Executes on-call data engineer escalation for Data Engineering under the decomposed model."""
    if params is None:
        params = HumanEscalationParamsDE()

    capacity_exhausted = False
    if queue_state is not None:
        queue_state.escalation_count += 1
        if queue_state.escalation_count > queue_state.capacity_limit:
            capacity_exhausted = True
            queue_state.drop_count += 1

    obs = case.observation
    pipe_load = obs.pipeline_load

    # 1. Labor Cost & Latency
    c_labor = obs.escalation_cost + params.c_labor_base + params.c_labor_congestion * pipe_load
    jitter = case.draws[11] if len(case.draws) > 11 else 0.10
    latency = current_latency + params.l_queue_base + params.l_queue_load_mult * pipe_load + jitter * 0.30
    cost = prior_cost + c_labor + obs.time_cost_per_hour * latency
    late = latency > obs.deadline_hours

    # 2. Availability & Capacity Constraints
    p_avail = float(np.clip(params.p_avail_base - params.p_avail_load_mult * pipe_load, 0.40, 0.98))
    avail_draw = case.draws[6]
    available = bool(avail_draw < p_avail) and not capacity_exhausted

    if not available:
        if queue_state is not None and not capacity_exhausted:
            queue_state.drop_count += 1
        reason = "human_queue_capacity_exhausted" if capacity_exhausted else "engineer_oncall_unavailable"
        return {
            "terminal": True,
            "allowed": True,
            "reason": reason,
            "b_rem": 0,
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
            "action": "escalate",
            "escalation_diagnostics": {
                "capacity_exhausted": int(capacity_exhausted),
                "human_error": 0,
                "salvaged": 0,
                "workflow_discount": 0.0,
            },
        }

    if late:
        return {
            "terminal": True,
            "allowed": True,
            "reason": "escalation_deadline_exceeded",
            "b_rem": 0,
            "evidence": evidence,
            "utility": -cost,
            "completed": 0,
            "completed_transform": 0,
            "completed_fallback": 0,
            "unsafe": 0,
            "safe_completion": 0,
            "cost": cost,
            "latency": latency,
            "late": 1,
            "blocked": 0,
            "authorization_violation": 0,
            "action": "escalate",
            "escalation_diagnostics": {
                "capacity_exhausted": 0,
                "human_error": 0,
                "salvaged": 0,
                "workflow_discount": 0.0,
            },
        }

    # 3. Human Error Modeling
    p_error = float(np.clip(params.p_error_base + params.p_error_load_mult * pipe_load, 0.02, 0.25))
    error_draw = case.draws[9] if len(case.draws) > 9 else 0.50
    human_error = bool(error_draw < p_error)

    if human_error:
        if queue_state is not None:
            queue_state.error_count += 1
        # If engineer errs on schema/content defect, corrupted data enters downstream analytics
        harm_draw = case.draws[10] if len(case.draws) > 10 else 0.50
        is_unsafe = bool((case.f_schema or case.f_content) and harm_draw < 0.50)
        utility = -cost - (params.h_error if is_unsafe else 0.0)
        return {
            "terminal": True,
            "allowed": True,
            "reason": "engineer_triage_error",
            "b_rem": 0,
            "evidence": evidence,
            "utility": utility,
            "completed": 0,
            "completed_transform": 0,
            "completed_fallback": 0,
            "unsafe": int(is_unsafe),
            "safe_completion": 0,
            "cost": cost,
            "latency": latency,
            "late": int(late),
            "blocked": 0,
            "authorization_violation": 0,
            "action": "escalate",
            "escalation_diagnostics": {
                "capacity_exhausted": 0,
                "human_error": 1,
                "salvaged": 0,
                "workflow_discount": 0.0,
            },
        }

    # 4. Salvage Probability & Workflow Value Discount
    salvage_draw = case.draws[7]
    if case.f_schema:
        salvaged = bool(salvage_draw < params.p_salvage_schema)
    elif case.f_content:
        salvaged = bool(salvage_draw < params.p_salvage_content)
    elif case.f_transient:
        salvaged = bool(salvage_draw < params.p_salvage_transient)
    else:
        salvaged = bool(salvage_draw < params.p_salvage_clean)

    if salvaged:
        completed = True
        unsafe = False
        v_net = params.gamma_workflow * obs.value
        utility = v_net - cost
    else:
        completed = False
        unsafe = False
        utility = -cost

    return {
        "terminal": True,
        "allowed": True,
        "reason": "escalated_to_engineer",
        "b_rem": 0,
        "evidence": evidence,
        "utility": utility,
        "completed": int(completed),
        "completed_transform": int(completed),
        "completed_fallback": 0,
        "unsafe": int(unsafe),
        "safe_completion": int(completed and not unsafe),
        "cost": cost,
        "latency": latency,
        "late": int(late),
        "blocked": 0,
        "authorization_violation": 0,
        "action": "escalate",
        "escalation_diagnostics": {
            "capacity_exhausted": 0,
            "human_error": 0,
            "salvaged": int(salvaged),
            "workflow_discount": (1.0 - params.gamma_workflow) if salvaged else 0.0,
        },
    }


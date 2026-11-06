"""CausaGuard v0.7.1: Multi-Policy Counterfactual Evaluation Runner.

Implements paired counterfactual potential-outcome evaluation with:
- Reproducible exogenous random tapes;
- Policy-specific isolated queue state tracking;
- Strict policy-order invariance;
- Comprehensive cluster-level contrast and safety statistics;
- Clear separation of operational risk, completion, costs, and latency.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from causaguard_v07_1.domain_cs import (
    CSCaseV07_1,
    CSEvidenceV07_1,
    execute_cs_step_v07_1,
)
from causaguard_v07_1.domain_de import (
    DECaseV07_1,
    DEEvidenceV07_1,
    execute_de_step_v07_1,
)
from causaguard_v07_1.escalation import QueueState
from causaguard_v07_1.policy_v07_1 import (
    BasePolicyV07_1,
    OraclePolicyV07_1,
    get_baseline_policies_v07_1,
)


def run_episode_v07_1(
    case: CSCaseV07_1 | DECaseV07_1,
    policy: BasePolicyV07_1,
    queue_state: QueueState | None = None,
    **step_kwargs: Any,
) -> dict[str, Any]:
    """Runs a single episode under a given policy and queue state."""
    is_cs = isinstance(case, CSCaseV07_1)
    b_rem = case.observation.budget
    current_latency = 0.0
    prior_cost = 0.0
    evidence: CSEvidenceV07_1 | DEEvidenceV07_1 | None = None
    step_records: list[dict[str, Any]] = []

    # Step 1
    policy_kwargs: dict[str, Any] = {}
    if isinstance(policy, OraclePolicyV07_1):
        policy_kwargs["case"] = case

    action_1 = policy.select(
        observation=case.observation,
        evidence=None,
        b_rem=b_rem,
        **policy_kwargs,
    )

    if is_cs:
        assert isinstance(case, CSCaseV07_1)
        r1 = execute_cs_step_v07_1(
            case=case,
            action=action_1,
            b_rem=b_rem,
            current_latency=current_latency,
            prior_cost=prior_cost,
            evidence=None,
            queue_state=queue_state,
            **step_kwargs,
        )
    else:
        assert isinstance(case, DECaseV07_1)
        r1 = execute_de_step_v07_1(
            case=case,
            action=action_1,
            b_rem=b_rem,
            current_latency=current_latency,
            prior_cost=prior_cost,
            evidence=None,
            queue_state=queue_state,
            **step_kwargs,
        )

    step_records.append(r1)

    if r1["terminal"]:
        final_record = dict(r1)
        final_record["steps"] = step_records
        final_record["step1_action"] = action_1
        final_record["step2_action"] = None
        return final_record

    # Step 2 (Post-verification)
    b_rem = r1["b_rem"]
    current_latency = r1["latency"]
    prior_cost = r1["cost"]
    evidence = r1["evidence"]

    action_2 = policy.select(
        observation=case.observation,
        evidence=evidence,
        b_rem=b_rem,
        **policy_kwargs,
    )

    if is_cs:
        assert isinstance(case, CSCaseV07_1)
        r2 = execute_cs_step_v07_1(
            case=case,
            action=action_2,
            b_rem=b_rem,
            current_latency=current_latency,
            prior_cost=prior_cost,
            evidence=evidence,
            queue_state=queue_state,
            **step_kwargs,
        )
    else:
        assert isinstance(case, DECaseV07_1)
        r2 = execute_de_step_v07_1(
            case=case,
            action=action_2,
            b_rem=b_rem,
            current_latency=current_latency,
            prior_cost=prior_cost,
            evidence=evidence,
            queue_state=queue_state,
            **step_kwargs,
        )

    step_records.append(r2)
    final_record = dict(r2)
    final_record["steps"] = step_records
    final_record["step1_action"] = action_1
    final_record["step2_action"] = action_2
    return final_record


def evaluate_potential_outcomes_v07_1(
    case: CSCaseV07_1 | DECaseV07_1,
    policies: dict[str, BasePolicyV07_1],
    queue_states: dict[str, QueueState] | None = None,
    **step_kwargs: Any,
) -> dict[str, dict[str, Any]]:
    """Evaluates all policies counterfactually on the exact same case and exogenous draws."""
    results: dict[str, dict[str, Any]] = {}
    for name, policy in policies.items():
        q_state = queue_states.get(name) if queue_states is not None else None
        results[name] = run_episode_v07_1(
            case=case,
            policy=policy,
            queue_state=q_state,
            **step_kwargs,
        )
    return results


def evaluate_cluster_v07_1(
    cases: list[CSCaseV07_1] | list[DECaseV07_1],
    policies: dict[str, BasePolicyV07_1] | None = None,
    capacity_limit: int = 150,
    **step_kwargs: Any,
) -> dict[str, Any]:
    """Evaluates a cluster of cases across all policies, maintaining independent queue states."""
    if policies is None:
        policies = get_baseline_policies_v07_1()

    if not cases:
        raise ValueError("Cannot evaluate empty case cluster.")

    is_cs = isinstance(cases[0], CSCaseV07_1)
    domain_name = "customer_support" if is_cs else "data_engineering"
    n_cases = len(cases)

    # Maintain independent queue state per policy to prevent cross-policy interference
    queue_states = {name: QueueState(capacity_limit=capacity_limit) for name in policies}

    policy_episodes: dict[str, list[dict[str, Any]]] = {name: [] for name in policies}

    for case in cases:
        for name, policy in policies.items():
            ep = run_episode_v07_1(
                case=case,
                policy=policy,
                queue_state=queue_states[name],
                **step_kwargs,
            )
            policy_episodes[name].append(ep)

    # Aggregate metrics per policy
    policy_metrics: dict[str, dict[str, Any]] = {}
    for name in policies:
        eps = policy_episodes[name]
        utilities = [ep["utility"] for ep in eps]
        completions = [ep["completed"] for ep in eps]
        safe_completions = [ep["safe_completion"] for ep in eps]
        unsafes = [ep["unsafe"] for ep in eps]
        costs = [ep["cost"] for ep in eps]
        latencies = [ep["latency"] for ep in eps]
        lates = [ep["late"] for ep in eps]
        auth_violations = [ep["authorization_violation"] for ep in eps]

        step1_acts = [ep["step1_action"] for ep in eps]
        step2_acts = [ep["step2_action"] for ep in eps if ep["step2_action"] is not None]

        s1_counts = {a: step1_acts.count(a) / n_cases for a in set(step1_acts)}
        s2_counts = {a: step2_acts.count(a) / max(len(step2_acts), 1) for a in set(step2_acts)} if step2_acts else {}

        q_state = queue_states[name]

        policy_metrics[name] = {
            "mean_utility": float(np.mean(utilities)),
            "std_utility": float(np.std(utilities, ddof=1)) if n_cases > 1 else 0.0,
            "completion_rate": float(np.mean(completions)),
            "safe_completion_rate": float(np.mean(safe_completions)),
            "operational_risk": float(np.mean(unsafes)),
            "mean_cost": float(np.mean(costs)),
            "mean_latency": float(np.mean(latencies)),
            "late_rate": float(np.mean(lates)),
            "auth_violations": int(sum(auth_violations)),
            "step1_actions": s1_counts,
            "step2_actions": s2_counts,
            "queue_diagnostics": {
                "total_escalations": q_state.escalation_count,
                "queue_drops": q_state.drop_count,
                "human_errors": q_state.error_count,
            },
        }

    return {
        "domain": domain_name,
        "n_cases": n_cases,
        "policy_metrics": policy_metrics,
    }


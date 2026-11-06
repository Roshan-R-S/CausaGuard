"""CausaGuard v0.7: Study & Evaluation Infrastructure.

Provides reproducible episode execution, counterfactually paired potential outcomes
across all 9 policies, and potential outcome permutation invariance validation.
NOTE: As mandated by protocol, does NOT run final evaluations or benchmark studies.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .domain_cs import CSCaseV07, execute_cs_step_v07, make_cs_cases_v07
from .domain_de import DECaseV07, execute_de_step_v07, make_de_cases_v07
from .policy_v07 import BasePolicyV07, get_baseline_policies_v07


def generate_cases_v07(
    domain: str,
    n: int,
    seed: int,
    profile: str = "iid",
    **kwargs: Any,
) -> list[CSCaseV07] | list[DECaseV07]:
    """Generates reproducible development cases for a domain across profiles."""
    if domain.lower() in ("cs", "customer_support"):
        return make_cs_cases_v07(n=n, seed=seed, profile=profile, **kwargs)
    elif domain.lower() in ("de", "data_engineering"):
        return make_de_cases_v07(n=n, seed=seed, profile=profile, **kwargs)
    raise ValueError(f"Unknown domain: {domain}. Allowed: 'cs', 'de'.")


def run_episode_v07(
    case: CSCaseV07 | DECaseV07,
    policy: BasePolicyV07,
    **step_kwargs: Any,
) -> dict[str, Any]:
    """Runs a single episode for a policy on a case under unitary budget accounting."""
    b_rem = case.observation.budget
    latency = 0.0
    cost = 0.0
    evidence: Any = None
    actions_taken: list[str] = []

    # Step 1: Pre-verification decision
    policy_kwargs: dict[str, Any] = {}
    if policy.name == "oracle":
        policy_kwargs["case"] = case

    action1 = policy.select(
        observation=case.observation,
        evidence=None,
        b_rem=b_rem,
        **policy_kwargs,
    )
    actions_taken.append(action1)

    if isinstance(case, CSCaseV07):
        step1_res = execute_cs_step_v07(
            case=case,
            action=action1,
            b_rem=b_rem,
            current_latency=latency,
            prior_cost=cost,
            evidence=None,
            **step_kwargs,
        )
    else:
        step1_res = execute_de_step_v07(
            case=case,
            action=action1,
            b_rem=b_rem,
            current_latency=latency,
            prior_cost=cost,
            evidence=None,
            **step_kwargs,
        )

    if step1_res["terminal"]:
        return {
            "policy": policy.name,
            "case_key": case.key,
            "seed": case.seed,
            "profile": case.profile,
            "budget": case.observation.budget,
            "actions": actions_taken,
            "num_steps": 1,
            "total_ops": case.observation.budget - step1_res["b_rem"],
            "b_rem": step1_res["b_rem"],
            "utility": step1_res["utility"],
            "completed": step1_res["completed"],
            "safe_completion": step1_res["safe_completion"],
            "unsafe": step1_res["unsafe"],
            "cost": step1_res["cost"],
            "latency": step1_res["latency"],
            "late": step1_res["late"],
            "blocked": step1_res["blocked"],
            "authorization_violation": step1_res["authorization_violation"],
            "reason": step1_res["reason"],
            "evidence": None,
        }

    # Step 2: Post-verification decision
    b_rem = step1_res["b_rem"]
    latency = step1_res["latency"]
    cost = step1_res["cost"]
    evidence = step1_res["evidence"]

    action2 = policy.select(
        observation=case.observation,
        evidence=evidence,
        b_rem=b_rem,
        **policy_kwargs,
    )
    actions_taken.append(action2)

    if isinstance(case, CSCaseV07):
        step2_res = execute_cs_step_v07(
            case=case,
            action=action2,
            b_rem=b_rem,
            current_latency=latency,
            prior_cost=cost,
            evidence=evidence,
            **step_kwargs,
        )
    else:
        step2_res = execute_de_step_v07(
            case=case,
            action=action2,
            b_rem=b_rem,
            current_latency=latency,
            prior_cost=cost,
            evidence=evidence,
            **step_kwargs,
        )

    return {
        "policy": policy.name,
        "case_key": case.key,
        "seed": case.seed,
        "profile": case.profile,
        "budget": case.observation.budget,
        "actions": actions_taken,
        "num_steps": 2,
        "total_ops": case.observation.budget - step2_res["b_rem"],
        "b_rem": step2_res["b_rem"],
        "utility": step2_res["utility"],
        "completed": step2_res["completed"],
        "safe_completion": step2_res["safe_completion"],
        "unsafe": step2_res["unsafe"],
        "cost": step2_res["cost"],
        "latency": step2_res["latency"],
        "late": step2_res["late"],
        "blocked": step2_res["blocked"],
        "authorization_violation": step2_res["authorization_violation"],
        "reason": step2_res["reason"],
        "evidence": asdict(evidence) if evidence is not None else None,
    }


def evaluate_potential_outcomes_v07(
    case: CSCaseV07 | DECaseV07,
    policies: dict[str, BasePolicyV07] | None = None,
    **step_kwargs: Any,
) -> dict[str, dict[str, Any]]:
    """Evaluates all candidate policies on the same case, producing paired potential outcomes."""
    if policies is None:
        policies = get_baseline_policies_v07()

    outcomes: dict[str, dict[str, Any]] = {}
    for name, pol in policies.items():
        outcomes[name] = run_episode_v07(case, pol, **step_kwargs)
    return outcomes


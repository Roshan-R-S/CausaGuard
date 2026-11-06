"""CausaGuard v0.6: Study & Evaluation Infrastructure.

Provides reproducible episode execution, paired potential outcomes across policies,
and rigorous permutation invariance validation.
NOTE: As mandated by protocol, does NOT run final evaluations or benchmark studies.
"""

from __future__ import annotations

import copy
import random
from dataclasses import asdict
from typing import Any

from causaguard_v06.domain_cs import (
    ACTIONS_CS,
    CSCase,
    CSEvidence,
    CSObservation,
    execute_cs_step,
    make_cs_cases,
)
from causaguard_v06.domain_de import (
    ACTIONS_DE,
    DECase,
    DEEvidence,
    DEObservation,
    execute_de_step,
    make_de_cases,
)
from causaguard_v06.policy_v06 import BasePolicy, get_baseline_policies


def run_episode(
    case: CSCase | DECase,
    policy: BasePolicy,
) -> dict[str, Any]:
    """Runs a single episode for a policy on a case under unitary budget accounting."""
    is_cs = isinstance(case, CSCase)
    step_fn = execute_cs_step if is_cs else execute_de_step

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

    step1_res = step_fn(
        case=case,
        action=action1,
        b_rem=b_rem,
        current_latency=latency,
        prior_cost=cost,
        evidence=None,
    )

    if step1_res["terminal"]:
        # Episode terminated at Step 1
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

    # Verify was executed; transition to Step 2
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

    step2_res = step_fn(
        case=case,
        action=action2,
        b_rem=b_rem,
        current_latency=latency,
        prior_cost=cost,
        evidence=evidence,
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


def evaluate_potential_outcomes(
    case: CSCase | DECase,
    policies: dict[str, BasePolicy] | None = None,
) -> dict[str, dict[str, Any]]:
    """Evaluates all candidate policies on the same case, producing paired potential outcomes."""
    if policies is None:
        policies = get_baseline_policies()

    outcomes: dict[str, dict[str, Any]] = {}
    for name, pol in policies.items():
        outcomes[name] = run_episode(case, pol)
    return outcomes


def evaluate_all_paths(case: CSCase | DECase) -> dict[str, dict[str, Any]]:
    """Evaluates all possible valid execution paths on a case for diagnostic potential outcome trees."""
    is_cs = isinstance(case, CSCase)
    step_fn = execute_cs_step if is_cs else execute_de_step
    budget = case.observation.budget
    paths: dict[str, dict[str, Any]] = {}

    terminal_actions = ["proceed", "retry" if is_cs else "restore", "escalate"]

    # 1. Single-step direct actions
    for a in terminal_actions:
        res = step_fn(case, a, b_rem=budget)
        paths[a] = res

    # 2. Verify-then-step paths
    v_res = step_fn(case, "verify", b_rem=budget)
    if v_res["terminal"]:
        # Verify was blocked or terminated early (e.g. permission denied)
        paths["verify"] = v_res
    else:
        # B=1 case: b_rem is 0 after verify, so only escalate is feasible
        b_after = v_res["b_rem"]
        ev = v_res["evidence"]
        lat = v_res["latency"]
        cost = v_res["cost"]

        for a2 in terminal_actions:
            path_key = f"verify->{a2}"
            res2 = step_fn(
                case,
                a2,
                b_rem=b_after,
                current_latency=lat,
                prior_cost=cost,
                evidence=ev,
            )
            paths[path_key] = res2

    return paths


def assert_permutation_invariance(
    case: CSCase | DECase,
    policies: dict[str, BasePolicy] | None = None,
    rng_seed: int = 42,
) -> bool:
    """Verifies that evaluating policies in different permutations yields strictly identical results.

    Guarantees no state leakage, random tape mutation, or order-dependent side effects.
    """
    if policies is None:
        policies = get_baseline_policies()

    policy_items = list(policies.items())
    base_results = {name: run_episode(case, pol) for name, pol in policy_items}

    # Permutation 1: Reversed order
    rev_items = list(reversed(policy_items))
    rev_results = {name: run_episode(case, pol) for name, pol in rev_items}

    # Permutation 2: Shuffled order
    shuffled_items = list(policy_items)
    rnd = random.Random(rng_seed)
    rnd.shuffle(shuffled_items)
    shuf_results = {name: run_episode(case, pol) for name, pol in shuffled_items}

    # Assert exact value equality across all fields
    for name in policies:
        res_base = base_results[name]
        res_rev = rev_results[name]
        res_shuf = shuf_results[name]

        for key in res_base:
            val_base = res_base[key]
            val_rev = res_rev[key]
            val_shuf = res_shuf[key]

            if val_base != val_rev or val_base != val_shuf:
                raise AssertionError(
                    f"Permutation invariance failure for policy '{name}', field '{key}': "
                    f"base={val_base}, rev={val_rev}, shuf={val_shuf}"
                )

    return True


def generate_cases(
    domain: str,
    n: int,
    seed: int,
    profile: str = "iid",
) -> list[CSCase] | list[DECase]:
    """Factory helper to generate cases for either domain."""
    if domain.lower() in ("cs", "customer_support"):
        return make_cs_cases(n=n, seed=seed, profile=profile)
    elif domain.lower() in ("de", "data_engineering"):
        return make_de_cases(n=n, seed=seed, profile=profile)
    else:
        raise ValueError(f"Unknown domain: {domain}. Allowed: cs, de")


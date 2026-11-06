"""Tests for CausaGuard v0.6 Action Feasibility, Operation Budgets, and Admissible Fallbacks."""

import pytest

from causaguard_v06.domain_cs import make_cs_cases, execute_cs_step
from causaguard_v06.domain_de import make_de_cases, execute_de_step
from causaguard_v06.policy_v06 import get_baseline_policies
from causaguard_v06.study_v06 import run_episode, evaluate_potential_outcomes


def test_b1_b2_feasibility_all_baselines_cs():
    """Asserts all baseline policies obey operation budget constraints and never exceed B operations in CS."""
    policies = get_baseline_policies()
    cases = make_cs_cases(n=25, seed=1001, profile="iid")

    for case in cases:
        b_init = case.observation.budget
        for pol_name, pol in policies.items():
            res = run_episode(case, pol)
            assert res["b_rem"] >= 0, f"Policy {pol_name} resulted in negative b_rem"
            assert res["total_ops"] <= b_init, f"Policy {pol_name} exceeded budget {b_init}"
            assert res["authorization_violation"] == 0, f"Policy {pol_name} had authorization violation"
            assert res["blocked"] in (0, 1)


def test_b1_b2_feasibility_all_baselines_de():
    """Asserts all baseline policies obey operation budget constraints and never exceed B operations in DE."""
    policies = get_baseline_policies()
    cases = make_de_cases(n=25, seed=2002, profile="iid")

    for case in cases:
        b_init = case.observation.budget
        for pol_name, pol in policies.items():
            res = run_episode(case, pol)
            assert res["b_rem"] >= 0, f"Policy {pol_name} resulted in negative b_rem"
            assert res["total_ops"] <= b_init, f"Policy {pol_name} exceeded budget {b_init}"
            assert res["authorization_violation"] == 0, f"Policy {pol_name} had authorization violation"
            assert res["blocked"] in (0, 1)


def test_strict_action_domination_verify_then_escalate():
    """Mathematically verifies that verify -> escalate is strictly dominated by immediate escalate.

    For all parameter values, U(verify -> escalate) - U(escalate) = -C_verify - C_time * L_verify < 0.
    """
    cs_cases = make_cs_cases(n=20, seed=3003, profile="iid")
    for case in cs_cases:
        # Immediate escalate
        res_esc = execute_cs_step(case, "escalate", b_rem=1)
        # Verify then escalate
        res_v = execute_cs_step(case, "verify", b_rem=1)
        if res_v["allowed"]:
            res_v_esc = execute_cs_step(
                case,
                "escalate",
                b_rem=res_v["b_rem"],
                current_latency=res_v["latency"],
                prior_cost=res_v["cost"],
                evidence=res_v["evidence"],
            )
            diff = res_v_esc["utility"] - res_esc["utility"]
            assert diff < 0.0, f"Action domination violated in CS: diff={diff}"

    de_cases = make_de_cases(n=20, seed=4004, profile="iid")
    for case in de_cases:
        res_esc = execute_de_step(case, "escalate", b_rem=1)
        res_v = execute_de_step(case, "verify", b_rem=1)
        if res_v["allowed"]:
            res_v_esc = execute_de_step(
                case,
                "escalate",
                b_rem=res_v["b_rem"],
                current_latency=res_v["latency"],
                prior_cost=res_v["cost"],
                evidence=res_v["evidence"],
            )
            diff = res_v_esc["utility"] - res_esc["utility"]
            assert diff < 0.0, f"Action domination violated in DE: diff={diff}"


def test_b1_admissible_fallbacks():
    """Verifies that at B=1, rational policies prune verify, and structural policies fall back cleanly."""
    policies = get_baseline_policies()

    # Generate CS cases forced to B=1
    cs_cases = make_cs_cases(n=20, seed=5005, profile="iid")
    b1_cs = [c for c in cs_cases if c.observation.budget == 1]
    if not b1_cs:
        # Force budget 1 on first case
        obs = cs_cases[0].observation
        object.__setattr__(obs, "budget", 1)
        b1_cs = [cs_cases[0]]

    for case in b1_cs:
        # cost_rule must NEVER select verify at Step 1 when B=1
        action_cost_rule = policies["cost_rule"].select(case.observation, evidence=None, b_rem=1)
        assert action_cost_rule != "verify", "cost_rule selected dominated verify at B=1"

        # rules_repair must NEVER select verify at Step 1 when B=1
        action_repair = policies["rules_repair"].select(case.observation, evidence=None, b_rem=1)
        assert action_repair != "verify", "rules_repair selected verify at B=1"

        # fixed_verify_repair_macro must NEVER select verify at Step 1 when B=1
        action_macro = policies["fixed_verify_repair_macro"].select(
            case.observation, evidence=None, b_rem=1
        )
        assert action_macro != "verify", "macro selected verify at B=1"

        # always_verify_then_proceed selects verify at Step 1;
        # if authorized, falls back to escalate at Step 2; if permission denied at Step 1, halts cleanly.
        res_avtp = run_episode(case, policies["always_verify_then_proceed"])
        assert res_avtp["total_ops"] == 1
        if res_avtp["blocked"] == 1:
            assert res_avtp["actions"] == ["verify"]
        else:
            assert res_avtp["actions"] == ["verify", "escalate"]

"""Independent mathematical checks; no task generators, keys, seals, or random seeds."""

from dataclasses import replace

import pytest

from research.experiments.de_voi_exp01.reference import (
    STATES,
    PublicDE,
    bayes,
    best_terminal,
    evidence_branches,
    generator_prior,
    terminal_values,
    verification_values,
)


def test_two_state_bayes_hand_calculation():
    assert bayes((0.8, 0.2), (0.98, 0.8)) == pytest.approx((49 / 59, 10 / 59))


def test_impossible_evidence_is_not_a_fabricated_posterior():
    with pytest.raises(ValueError, match="zero"):
        bayes((1.0, 0.0), (0.0, 1.0))


@pytest.mark.parametrize(
    "prior,likelihood",
    [
        ((0.2, 0.2), (0.5, 0.5)),
        ((1.0, 0.0), (-0.1, 0.5)),
        ((float("nan"), 0.0), (0.5, 0.5)),
        ((1.0,), (0.5, 0.5)),
    ],
)
def test_invalid_beliefs_rejected(prior, likelihood):
    with pytest.raises(ValueError):
        bayes(prior, likelihood)


def test_generator_prior_uses_alarm_and_column_likelihoods():
    o = PublicDE()
    p = generator_prior(o)
    assert sum(p) == pytest.approx(1.0)
    # At alarm=.5: Beta(5,2) density=.9375; Beta(1.5,6) density from Beta integral.
    from math import gamma

    a = 0.5
    f0 = a**0.5 * (1 - a) ** 5 * gamma(7.5) / (gamma(1.5) * gamma(6))
    raw = 0.09 * 0.9375 / 3
    expected = raw / (raw + 0.91 * f0 * 59 / 60)
    assert sum(p[4:]) == pytest.approx(expected)
    assert sum(generator_prior(replace(o, column_count_changed=1))[4:]) > expected


def test_posterior_martingale_and_branch_mass():
    p = generator_prior(PublicDE())
    branches = evidence_branches(p, 0.02, 0.8)
    assert sum(b[1] for b in branches) == pytest.approx(1.0)
    for j in range(8):
        assert sum(mass * post[j] for _, mass, post in branches) == pytest.approx(p[j])


def test_clean_and_transient_terminal_values_by_hand():
    o = replace(PublicDE(), time_cost_per_hour=0.2)
    clean = (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    crash = (0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    clean_v = terminal_values(o, clean)
    assert clean_v["proceed"]["utility"] == pytest.approx(0.91 * 1.5 - 0.02 - 0.2 * 0.15)
    assert terminal_values(o, crash)["proceed"]["risk"] == 0.0
    assert terminal_values(o, crash)["proceed"]["utility"] == pytest.approx(-0.02 - 0.2 * 0.15)


def test_prefix_cost_contracts_are_explicit():
    o = replace(PublicDE(), time_cost_per_hour=0.2)
    p = (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    legacy = terminal_values(o, p, elapsed=0.3, prior_cost=0.16, cost_mode="executor")
    once = terminal_values(o, p, elapsed=0.3, prior_cost=0.16, cost_mode="incremental")
    for action in legacy:
        assert once[action]["utility"] - legacy[action]["utility"] == pytest.approx(0.06)


def test_gross_and_net_information_value_and_cost_slope():
    o = PublicDE()
    p = generator_prior(o)
    v = verification_values(o, p)
    expensive = verification_values(replace(o, verify_cost=o.verify_cost + 0.17), p)
    assert v["gross_evsi"] >= -1e-12
    assert v["verification_utility"] - expensive["verification_utility"] == pytest.approx(0.17)
    assert v["gross_evsi"] == pytest.approx(expensive["gross_evsi"])


def test_deadline_and_operation_budget():
    p = generator_prior(PublicDE())
    assert set(terminal_values(PublicDE(), p, b_rem=0)) == {"escalate"}
    assert verification_values(replace(PublicDE(), budget=1), p)["verification_utility"] is None
    late = terminal_values(PublicDE(), p, elapsed=5.0)
    assert all(v["risk"] == 0.0 and v["utility"] < 0.0 for v in late.values())


def test_no_hidden_truth_input():
    with pytest.raises(TypeError):
        generator_prior({"f_schema": True})


@pytest.mark.parametrize(
    "changes",
    [
        {"schema_alarm": 0.0},
        {"schema_alarm": 1.0},
        {"budget": True},
        {"quoted_fn_schema": float("inf")},
        {"value": -1.0},
        {"column_count_changed": 2},
    ],
)
def test_invalid_or_out_of_model_public_values(changes):
    with pytest.raises(ValueError):
        generator_prior(replace(PublicDE(), **changes))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"cost_mode": "unknown"},
        {"elapsed": -1.0},
        {"b_rem": -1},
        {"risk_limit": 2.0},
    ],
)
def test_terminal_contract_rejects_invalid_inputs(kwargs):
    with pytest.raises(ValueError):
        terminal_values(PublicDE(), (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), **kwargs)


def test_impossible_evidence_branches_are_omitted():
    branches = evidence_branches((1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), 0.0, 0.0)
    assert len(branches) == 1
    assert branches[0][0] == (True, True)
    assert branches[0][1] == 1.0


def test_no_capacity_preserves_charged_labor_but_removes_human_outcomes():
    v = terminal_values(PublicDE(), generator_prior(PublicDE()), capacity_available=False)
    assert v["escalate"]["utility"] == -v["escalate"]["cost"]
    assert v["escalate"]["risk"] == 0.0
    with pytest.raises(ValueError, match="No risk-feasible"):
        best_terminal({"proceed": {"utility": 1.0, "feasible": False}})


def test_uninformative_schema_with_known_content_has_zero_gross_value():
    o = replace(PublicDE(), quoted_fp_schema=0.5, quoted_fn_schema=0.5)
    # Two states differ only by schema; every evidence outcome has the same likelihood.
    belief = (0.8, 0.0, 0.0, 0.0, 0.2, 0.0, 0.0, 0.0)
    v = verification_values(o, belief, risk_limit=None)
    assert v["gross_evsi"] == pytest.approx(0.0, abs=1e-12)
    assert v["net_gain"] < 0


def test_perfect_schema_check_collapses_to_correct_latent_schema_support():
    belief = (0.8, 0.0, 0.0, 0.0, 0.2, 0.0, 0.0, 0.0)
    branches = evidence_branches(belief, 0.0, 0.0)
    for (valid, _), _, posterior in branches:
        assert sum(posterior[4:]) == (0.0 if valid else 1.0)


@pytest.mark.parametrize(
    "deadline,cost_mode",
    [(0.4, "executor"), (0.8, "incremental"), (1.6, "executor"), (4.0, "incremental")],
)
def test_analytic_continuation_integral_matches_independent_midpoint_limit(deadline, cost_mode):
    # This deterministic quadrature checks the analytic envelope, not Monte Carlo.
    o = replace(PublicDE(), deadline_hours=deadline, quoted_fn_schema=0.3)
    p = generator_prior(o)
    n = 2000
    expected = 0.0
    for _, mass, posterior in evidence_branches(p, o.quoted_fp_schema, o.quoted_fn_schema):
        total = 0.0
        for i in range(n):
            elapsed = o.observation_delay + 0.05 + 0.35 * (i + 0.5) / n
            values = terminal_values(
                o,
                posterior,
                elapsed=elapsed,
                prior_cost=o.verify_cost + o.time_cost_per_hour * elapsed,
                cost_mode=cost_mode,
            )
            total += max(v["utility"] for v in values.values() if v["feasible"])
        expected += mass * total / n
    actual = verification_values(o, p, cost_mode=cost_mode)["verification_utility"]
    # Conditional-risk feasibility can cause jumps; midpoint convergence is O(1/n).
    assert actual == pytest.approx(expected, abs=5e-4)


@pytest.mark.parametrize("deadline", [0.55, 4.0])
@pytest.mark.parametrize("action", ["proceed", "restore", "escalate"])
def test_reference_terminal_expectation_matches_exhaustively_partitioned_executor(action, deadline):
    from itertools import product

    from causaguard_v07_1.domain_de import execute_de_step_v07_1

    from research.experiments.de_voi_exp01.experiment import minimized_case

    o = replace(PublicDE(), deadline_hours=deadline, time_cost_per_hour=0.2)
    p = generator_prior(o)
    elapsed, sunk = 0.05, 0.11
    witness = minimized_case(o)

    def cells(*thresholds):
        knots = sorted({0.0, 1.0, *(max(0.0, min(1.0, t)) for t in thresholds)})
        return [((a + b) / 2, b - a) for a, b in zip(knots, knots[1:]) if b > a]

    total_u = total_r = 0.0
    for probability, (schema, content, transient) in zip(p, STATES):
        if action == "proceed":
            partitions = {1: cells(0.09), 3: cells((deadline - elapsed - 0.1) / 0.1)}
        elif action == "restore":
            partitions = {
                1: cells(0.09),
                4: cells((deadline - elapsed - 0.4) / 0.15),
                8: cells(0.8),
            }
        else:
            salvage = 0.75 if schema else 0.8 if content else 0.85 if transient else 1.0
            partitions = {
                6: cells(0.95),
                7: cells(salvage),
                9: cells(0.066),
                10: cells(0.5),
                11: cells((deadline - elapsed - 1.5) / 0.3),
            }
        for combination in product(*partitions.values()):
            draws = list(witness.draws)
            weight = probability
            for index, (draw, mass) in zip(partitions, combination):
                draws[index] = draw
                weight *= mass
            case = replace(
                witness,
                f_schema=schema,
                f_content=content,
                f_transient=transient,
                defect=schema or content or transient,
                draws=tuple(draws),
            )
            result = execute_de_step_v07_1(
                case, action, 1, current_latency=elapsed, prior_cost=sunk
            )
            total_u += weight * result["utility"]
            total_r += weight * result["unsafe"]
    reference = terminal_values(o, p, elapsed=elapsed, prior_cost=sunk)[action]
    assert reference["utility"] == pytest.approx(total_u, abs=1e-12)
    assert reference["risk"] == pytest.approx(total_r, abs=1e-12)

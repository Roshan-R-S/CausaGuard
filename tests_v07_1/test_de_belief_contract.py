"""Deterministic independent contract audit; preserves the exp01 reference unchanged."""

from dataclasses import replace
from fractions import Fraction as F
from importlib import import_module
from math import gamma, isclose

import pytest

from research.experiments.de_voi_exp01.reference import (
    STATES,
    PublicDE,
    bayes,
    evidence_branches,
    generator_prior,
    terminal_values,
    verification_values,
)


def independent_schema(alarm, column=0):
    # Direct beta integrals rather than reference log-density or Bayes helpers.
    f1 = 30 * alarm**4 * (1 - alarm)
    f0 = alarm**0.5 * (1 - alarm) ** 5 * gamma(7.5) / (gamma(1.5) * gamma(6))
    x = 0.09 * f1 * (2 / 3 if column else 1 / 3)
    y = 0.91 * f0 * (1 / 60 if column else 59 / 60)
    return x / (x + y)


@pytest.mark.parametrize("alarm", [0.2, 0.5, 0.8])
@pytest.mark.parametrize("column", [0, 1])
def test_independent_initial_density_and_eight_states(alarm, column):
    assert len(set(STATES)) == 8
    p = generator_prior(replace(PublicDE(), schema_alarm=alarm, column_count_changed=column))
    s, c, t = independent_schema(alarm, column), 49 / 300, 13 / 500
    expected = [
        (s if a else 1 - s) * (c if b else 1 - c) * (t if d else 1 - t) for a, b, d in STATES
    ]
    assert p == pytest.approx(expected, abs=1e-14)


@pytest.mark.parametrize("fp,fn", [(F(0), F(0)), (F(1, 50), F(4, 5)), (F(1, 2), F(1, 2))])
def test_correlated_prior_exact_fraction_enumeration(fp, fn):
    # Deliberate dependence: not a product of schema/content/transient marginals.
    p = [F(i, 36) for i in range(1, 9)]
    total = F(0)
    for (valid, clean), mass, posterior in evidence_branches(
        tuple(map(float, p)), float(fp), float(fn)
    ):
        w = []
        for prior, (s, c, t) in zip(p, STATES):
            prob = fn if s else 1 - fp
            w.append(prior * (prob if valid else 1 - prob) * (clean != c))
        m = sum(w)
        total += m
        assert mass == pytest.approx(float(m))
        assert posterior == pytest.approx([float(x / m) for x in w])
    assert total == 1


def test_recalculate_three_preserved_witnesses_independently():
    from research.experiments.de_voi_exp01.experiment import build_report, candidate_action

    cases = {c["id"]: c for c in build_report()["cases"]}
    s = independent_schema(0.5)
    post = s * 0.8 / (s * 0.8 + (1 - s) * 0.98)
    risk = 0.91 * post
    assert risk == pytest.approx(0.05633278733470557, abs=1e-14)
    assert cases["B1"]["difference"]["proceed_risk_excess"] == pytest.approx(risk - 0.05)
    assert (
        candidate_action(replace(PublicDE(), quoted_fn_schema=0.8), (True, 0.95, 0.3)) == "proceed"
    )
    o = replace(
        PublicDE(),
        schema_alarm=0.8,
        quoted_fp_schema=0.027,
        quoted_fn_schema=0.056,
        restore_cost=0.44,
        deadline_hours=3.9,
    )
    s = independent_schema(0.8)
    direct = 0.91 * 1.5 * (0.45 - 0.28 * s) - 0.44 - 0.02 * 0.475
    # All branches choose restore, on time; posterior mean equals prior.
    gain = -float(F(1, 10) + 2 * F(1, 50) * (F(1, 10) + F(9, 40)))
    v = verification_values(o)
    assert v["direct_utility"] == pytest.approx(direct, abs=1e-14)
    assert v["verification_utility"] == pytest.approx(direct + gain, abs=1e-14)
    for branch in v["branches"]:
        for elapsed in (0.15, 0.325, 0.5):
            values = terminal_values(o, branch["posterior"], elapsed=elapsed)
            assert (
                max(
                    (a for a in values if values[a]["feasible"]), key=lambda a: values[a]["utility"]
                )
                == "restore"
            )
    assert candidate_action(o) == "verify"
    duplicate = F(1, 5) * F(3, 10)
    once = F(1, 10) + F(1, 50) + F(1, 5) * (F(3, 10) + F(3, 20))
    assert (float(once), float(once + duplicate)) == pytest.approx((0.21, 0.27))
    assert cases["D1"]["difference"]["extra_time_charge"] == pytest.approx(float(duplicate))


def test_six_xfails_fail_at_their_claim_assertions_not_in_setup():
    module = import_module("tests_v07_1.test_de_falsification_exp01")
    functions = [f for name, f in vars(module).items() if name.startswith("test_claim_")]
    assert len(functions) == 6
    for fn in functions:
        marks = [m for m in fn.pytestmark if m.name == "xfail"]
        assert len(marks) == 1 and marks[0].kwargs["strict"] is True
        # Calling directly bypasses pytest's broad expected-failure classification.
        with pytest.raises(AssertionError) as caught:
            fn()
        tb = caught.value.__traceback__
        while tb.tb_next is not None:
            tb = tb.tb_next
        assert tb.tb_frame.f_code is fn.__code__


def test_reference_capacity_validation_gap_is_reproduced():
    # Exp02 regression: retain the original negative-capacity witness, now reject it.
    with pytest.raises(ValueError, match="capacity"):
        terminal_values(PublicDE(), generator_prior(PublicDE()), capacity_available=-1)


def test_reference_extreme_underflow_limitation_is_reproduced():
    # Exact positive normalizer 10^-400; the mathematical posterior is (1,0).
    assert F(1, 10**200) * F(1, 10**200) > 0
    assert bayes((1e-200, 1.0), (1e-200, 0.0)) == (1.0, 0.0)


def test_repeated_same_evidence_is_not_an_independent_measurement():
    prior = (0.8, 0.2)
    once = bayes(prior, (0.98, 0.02))
    twice = bayes(once, (0.98, 0.02))
    assert once[1] == pytest.approx(1 / 197)
    assert not isclose(twice[1], once[1])
    # Existing executor reuses draw[0]; a repeated identical event adds no information.


def test_fee_sensitivity_and_nominal_vs_shifted_likelihood():
    o = PublicDE()
    baseline = verification_values(o)
    for fee in (0.0, 0.1, 0.6, 1.0):
        v = verification_values(replace(o, verify_cost=fee))
        assert v["net_gain"] == pytest.approx(baseline["net_gain"] + 0.1 - fee)
        assert v["gross_evsi"] == pytest.approx(baseline["gross_evsi"])
    s = independent_schema(0.5)
    nominal = s * 0.056 / (s * 0.056 + (1 - s) * 0.973)
    shifted = s * 0.256 / (s * 0.256 + (1 - s) * 0.873)
    assert shifted > nominal

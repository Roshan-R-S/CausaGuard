"""Exp02 acceptance tests: independent fractions, exhaustive grids, no PRNG."""

from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import product

import pytest

from research.experiments.de_belief_exp02.engine import (
    BeliefState,
    Distribution,
    Evidence,
    Status,
    update,
)
from research.experiments.de_voi_exp01.reference import (
    PublicDE,
    bayes,
    evidence_branches,
    generator_prior,
    terminal_values,
)


def initial(p=(0.8, 0.2)):
    return BeliefState(Distribution("model-1", ("clean", "schema"), p))


def evidence(
    likelihoods=(0.98, 0.02),
    *,
    identifier="check-1",
    events=frozenset({"event-1"}),
    independent_of=frozenset(),
    basis="",
):
    return Evidence(
        identifier, "model-1", ("clean", "schema"), likelihoods, events, independent_of, basis
    )


def floats(result):
    assert result.status is Status.OK and result.posterior is not None
    return tuple(map(float, result.posterior.distribution.probabilities))


def test_pass_fail_and_residual_risk():
    passed = update(initial(), evidence())
    failed = update(initial(), evidence((0.02, 0.98)))
    assert floats(passed) == pytest.approx((196 / 197, 1 / 197))
    assert floats(failed) == pytest.approx((4 / 53, 49 / 53))
    assert passed.posterior.distribution.probabilities[1] > 0
    assert update(initial(), evidence()) == passed


def test_exhaustive_binary_bayes_against_rational_arithmetic():
    grid = [Fraction(i, 4) for i in range(5)]
    for p, l0, l1 in product(grid, repeat=3):
        r = update(initial((float(1 - p), float(p))), evidence((float(l0), float(l1))))
        mass = (1 - p) * l0 + p * l1
        if mass == 0:
            assert r.status is Status.IMPOSSIBLE and r.posterior is None
            assert r.evidence_probability == 0
        else:
            expected = (float((1 - p) * l0 / mass), float(p * l1 / mass))
            assert floats(r) == pytest.approx(expected, abs=1e-14)
            assert floats(r) == pytest.approx(
                bayes((float(1 - p), float(p)), (float(l0), float(l1)))
            )
            assert all(0 <= x <= 1 for x in r.posterior.distribution.probabilities)
            assert sum(r.posterior.distribution.probabilities) == pytest.approx(Decimal(1))


def test_extreme_positive_evidence_and_tiny_posterior_are_retained():
    r = update(initial((1e-200, 1.0)), evidence((1e-200, 0.0)))
    assert floats(r) == (1.0, 0.0)
    assert r.evidence_probability > 0
    r = update(initial((Decimal("1e-400"), Decimal(1))), evidence((0.5, 0.5)))
    assert r.posterior.distribution.probabilities[0] > 0
    # Independence declared for a different event; tiny mass can later recover.
    next_e = evidence(
        (1.0, 0.0),
        identifier="check-2",
        events=frozenset({"event-2"}),
        independent_of=frozenset({"event-1"}),
        basis="separate draws conditional on state",
    )
    assert floats(update(r.posterior, next_e)) == (1.0, 0.0)


def test_duplicate_alias_and_undeclared_dependence_fail_closed():
    state = update(initial(), evidence()).posterior
    for e in [
        evidence(),
        evidence(identifier="alias"),
        evidence(identifier="check-2", events=frozenset({"event-2"})),
        evidence(identifier="check-1", events=frozenset({"event-2"})),
    ]:
        r = update(state, e)
        assert r.status is Status.DEPENDENCY_REJECTED and r.posterior is None
    e = evidence(
        identifier="check-2",
        events=frozenset({"event-2"}),
        independent_of=frozenset({"unknown"}),
        basis="not sufficient",
    )
    assert update(state, e).status is Status.DEPENDENCY_REJECTED
    assert len(state.history) == 1


def test_explicit_independence_and_joint_bundle():
    state = update(initial(), evidence()).posterior
    e = evidence(
        identifier="check-2",
        events=frozenset({"event-2"}),
        independent_of=frozenset({"event-1"}),
        basis="independent tapes given Z",
    )
    result = update(state, e)
    assert floats(result) == pytest.approx((9604 / 9605, 1 / 9605))
    # Fully dependent two-event observation supplied as one joint likelihood.
    joint = evidence(events=frozenset({"event-1", "event-2"}))
    assert floats(update(initial(), joint)) == pytest.approx((196 / 197, 1 / 197))
    assert update(update(initial(), joint).posterior, e).status is Status.DEPENDENCY_REJECTED


@pytest.mark.parametrize(
    "bad", [-0.1, 1.1, float("nan"), float("inf"), True, "0.5", Decimal("NaN")]
)
def test_invalid_probabilities_raise_without_clipping(bad):
    with pytest.raises(ValueError):
        initial((bad, 1.0))
    with pytest.raises(ValueError):
        evidence((bad, 0.5))


@pytest.mark.parametrize("p", [(), (0.2, 0.2), (0.2,), [0.8, 0.2]])
def test_malformed_distribution(p):
    with pytest.raises(ValueError):
        initial(p)


def test_invalid_metadata_and_model_mismatch():
    with pytest.raises(ValueError):
        evidence(identifier="")
    with pytest.raises(ValueError):
        evidence(events=frozenset())
    with pytest.raises(ValueError):
        evidence(independent_of=frozenset({"old"}))
    with pytest.raises(ValueError):
        Distribution("model-1", ("same", "same"), (0.5, 0.5))
    other = Evidence("check", "other", ("clean", "schema"), (0.5, 0.5), frozenset({"e"}))
    assert update(initial(), other).status is Status.MODEL_MISMATCH


def test_decimal_context_is_local_and_numeric_range_is_explicit():
    with localcontext() as ctx:
        ctx.prec = 3
        assert floats(update(initial(), evidence())) == pytest.approx((196 / 197, 1 / 197))
        assert ctx.prec == 3
    extreme = initial((Decimal("1e-999999"), Decimal(1)))
    result = update(extreme, evidence((Decimal("1e-999999"), Decimal(0))))
    assert result.status is Status.NUMERIC_RANGE and result.posterior is None


def test_eight_state_reference_agreement():
    prior = generator_prior(PublicDE())
    states = tuple(str(i) for i in range(8))
    state = BeliefState(Distribution("de", states, prior))
    for fp, fn in [(0.0, 0.0), (0.02, 0.8), (0.5, 0.5), (1.0, 1.0)]:
        for (valid, clean), mass, post in evidence_branches(prior, fp, fn):
            ls = tuple(
                (fn if s else 1 - fp) if valid else (1 - fn if s else fp)
                for s, c, t in product((False, True), repeat=3)
            )
            ls = tuple(
                likelihood * float(clean != c)
                for likelihood, (s, c, t) in zip(ls, product((False, True), repeat=3))
            )
            e = Evidence("combined", "de", states, ls, frozenset({"schema", "content"}))
            r = update(state, e)
            assert floats(r) == pytest.approx(post, abs=1e-14)
            assert float(r.evidence_probability) == pytest.approx(mass, abs=1e-14)


@pytest.mark.parametrize("bad", [-1, 0, 1, 0.5, float("nan"), float("inf"), None, "available"])
def test_reference_rejects_nonboolean_capacity(bad):
    with pytest.raises(ValueError, match="capacity"):
        terminal_values(PublicDE(), generator_prior(PublicDE()), capacity_available=bad)


def test_reference_undefined_float_range_is_not_impossibility():
    with pytest.raises(FloatingPointError, match="posterior"):
        bayes((1e-200, 1.0), (1e-200, 1.0))
    p = (0.0, 0.0, 0.0, 0.0, 1e-200, 0.0, 1.0, 0.0)
    with pytest.raises(FloatingPointError, match="evidence mass"):
        evidence_branches(p, 1.0, 1e-200)


def test_reference_tiny_nonzero_alternatives_normalize():
    assert bayes((1e-200, 1e-200, 1.0), (1e-200, 1e-200, 0.0)) == (0.5, 0.5, 0.0)


def test_all_history_dependencies_required_and_input_is_immutable():
    first = update(initial(), evidence()).posterior
    second = evidence(
        identifier="second",
        events=frozenset({"event-2"}),
        independent_of=frozenset({"event-1"}),
        basis="distinct independent draws",
    )
    state = update(first, second).posterior
    missing = evidence(
        identifier="third",
        events=frozenset({"event-3"}),
        independent_of=frozenset({"event-2"}),
        basis="incomplete",
    )
    assert update(state, missing).status is Status.DEPENDENCY_REJECTED
    assert len(first.history) == 1 and len(state.history) == 2
    from dataclasses import FrozenInstanceError

    with pytest.raises(FrozenInstanceError):
        state.history = ()


def test_bad_state_metadata_and_call_types():
    for states in [(), ("",), ("a",) * 257, ["a"], (7,)]:
        with pytest.raises(ValueError):
            Distribution("m", states, ())
    for events in [set(), frozenset({""}), frozenset({7})]:
        with pytest.raises(ValueError):
            evidence(events=events)
    with pytest.raises(ValueError):
        evidence(basis=None)
    with pytest.raises(ValueError):
        BeliefState("invalid")
    with pytest.raises(ValueError):
        BeliefState(initial().distribution, (None,))
    with pytest.raises(ValueError):
        BeliefState(initial().distribution, (evidence(), evidence()))
    with pytest.raises(ValueError):
        BeliefState(Distribution("other", ("clean", "schema"), (0.8, 0.2)), (evidence(),))
    with pytest.raises(ValueError):
        update(None, evidence())
    e = Evidence("permuted", "model-1", ("schema", "clean"), (0.02, 0.98), frozenset({"e"}))
    assert update(initial(), e).status is Status.MODEL_MISMATCH


def test_explicit_history_limit():
    history = []
    used = frozenset()
    for i in range(256):
        event = str(i)
        history.append(
            evidence(
                (1.0, 1.0),
                identifier=event,
                events=frozenset({event}),
                independent_of=used,
                basis="declared conditionally independent",
            )
        )
        used = used | {event}
    state = BeliefState(initial().distribution, tuple(history))
    extra = evidence(
        identifier="extra", events=frozenset({"extra"}), independent_of=used, basis="independent"
    )
    assert update(state, extra).status is Status.HISTORY_LIMIT
    with pytest.raises(ValueError, match="256"):
        BeliefState(initial().distribution, tuple(history) + (extra,))


def test_engine_imports_only_standard_library_math_and_types():
    import ast
    from pathlib import Path

    from research.experiments.de_belief_exp02 import engine

    tree = ast.parse(Path(engine.__file__).read_text())
    modules = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert modules <= {"dataclasses", "decimal", "enum"}
    assert not any(isinstance(n, ast.Import) for n in ast.walk(tree))


def test_four_old_counterexamples_and_all_case_records_are_preserved():
    import json
    from pathlib import Path

    from research.experiments.de_voi_exp01.experiment import build_report

    stored = json.loads(Path("research/reviews/v071-de-voi-falsification-exp01.json").read_text())
    fresh = build_report()
    assert stored["cases"] == fresh["cases"]
    cases = {c["id"]: c for c in fresh["cases"]}
    assert cases["B1"]["candidate"]["action"] == "proceed"
    assert cases["E3"]["candidate"]["action"] == "verify"
    assert cases["D1"]["difference"]["extra_time_charge"] == pytest.approx(0.06)
    assert cases["G1"]["difference"]["missed_violations"] == 1

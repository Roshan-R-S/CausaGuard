"""Focused statistical contract checks; no production study seed is generated."""

import numpy as np
import pytest

from causaguard.v052.inference import (
    BASELINES,
    CANDIDATES,
    crossed_samples,
    gate,
    infer,
    select_candidate,
)


def cells():
    result = {p: np.zeros((3, 4, 4, 5)) for p in CANDIDATES + BASELINES}
    for candidate in CANDIDATES:
        result[candidate][..., 0] = .06
        result[candidate][..., 1] = .03
    result["always_verify"][..., 1] = .03
    return result


def run(values, **kwargs):
    return infer(values, 400, 52900071, .00625, **kwargs)


def test_crossed_bootstrap_matches_explicit_cartesian_and_keeps_profiles_together():
    values = np.arange(12, dtype=float).reshape(3, 4)
    stacked = np.stack([values, values + 100, values * 2, -values], axis=2)
    actual = crossed_samples(stacked, 50, 52900072)
    rng = np.random.default_rng(52900072)
    expected = []
    for _ in range(50):
        train = rng.integers(3, size=3)
        evaluation = rng.integers(4, size=4)
        expected.append(stacked[train[:, None], evaluation[None, :]].mean(axis=(0, 1)))
    np.testing.assert_allclose(actual, expected, rtol=1e-14, atol=1e-14)
    np.testing.assert_allclose(actual[:, 1] - actual[:, 0], 100)
    np.testing.assert_allclose(actual[:, 2], actual[:, 0] * 2)
    np.testing.assert_allclose(actual[:, 3], -actual[:, 0])


@pytest.mark.parametrize("bound,threshold,relation,passes", [
    (.020, .020, ">", False),
    (np.nextafter(.020, 1), .020, ">", True),
    (.050, .050, "<=", True),
    (np.nextafter(.050, 1), .050, "<=", False),
    (.010, .010, "<=", True),
    (np.nextafter(.010, 1), .010, "<=", False),
])
def test_exact_unrounded_acceptance_boundaries(bound, threshold, relation, passes):
    assert gate(bound, bound, .0125, threshold, relation)["passes"] is passes


def test_one_sided_quantile_is_alpha_not_alpha_over_two_and_paired():
    values = cells()
    variation = np.random.default_rng(52900074).uniform(0, .1, size=(3, 4))
    values[CANDIDATES[0]][:, :, 0, 0] = .06 + variation
    values["original_r05"][:, :, 0, 0] = variation / 2
    result = run(values)
    pair = values[CANDIDATES[0]][..., :2] - values["original_r05"][..., :2]
    draw = crossed_samples(pair, 400, 52900071)[:, 0, 0]
    check = result["candidates"][CANDIDATES[0]]["checks"]["utility_vs_original_r05"]
    assert check["bound"] == pytest.approx(np.quantile(draw, .00625), abs=1e-14)
    assert check["bound"] != pytest.approx(np.quantile(draw, .003125), abs=1e-8)


def test_absolute_and_excess_risk_use_upper_one_minus_alpha_quantile():
    values = cells()
    values[CANDIDATES[0]][:, :, 0, 1] = np.arange(12).reshape(3, 4) / 200
    result = run(values)["candidates"][CANDIDATES[0]]["checks"]
    draw = crossed_samples(values[CANDIDATES[0]], 400, 52900071)[:, 0, 1]
    assert result["absolute_risk"]["bound"] == pytest.approx(np.quantile(draw, .99375))
    assert result["excess_risk_vs_always_verify"]["bound"] == pytest.approx(
        np.quantile(draw - .03, .99375)
    )


def test_selection_ties_use_raw_and_selection_prefers_higher_eligible_utility():
    values = cells()
    assert select_candidate(run(values))["selected_candidate"] == CANDIDATES[0]
    values[CANDIDATES[1]][..., 0] = .07
    assert select_candidate(run(values))["selected_candidate"] == CANDIDATES[1]
    values[CANDIDATES[1]][..., 1] = .051
    assert select_candidate(run(values))["selected_candidate"] == CANDIDATES[0]


def test_any_failed_gate_excludes_candidate_and_both_fail_stop():
    values = cells()
    values[CANDIDATES[0]][..., 0] = .020
    values[CANDIDATES[1]][..., 1] = .041
    result = run(values)
    assert not result["candidates"][CANDIDATES[0]]["eligible"]
    assert not result["candidates"][CANDIDATES[1]]["eligible"]
    assert select_candidate(result) == {
        "status": "development_stop", "selected_candidate": None, "eligible_candidates": [],
    }


def test_authorization_violation_anywhere_disqualifies_every_candidate():
    values = cells()
    values["always_verify"][0, 0, 3, 4] = .01
    result = run(values, auth_violations=1)
    assert result["authorization_violations"] == 1
    assert select_candidate(result)["status"] == "development_stop"
    with pytest.raises(ValueError, match="contradicts"):
        run(values, auth_violations=0)


def test_constant_risk_threshold_passes_and_degenerate_bounds_are_reported():
    values = cells()
    values[CANDIDATES[0]][..., 1] = .050
    values["always_verify"][..., 1] = .050
    result = run(values)
    check = result["candidates"][CANDIDATES[0]]["checks"]["absolute_risk"]
    assert check["bound"] == .050
    assert check["passes"] and check["zero_width"]
    assert result["policies"][CANDIDATES[0]]["iid"]["unsafe"]["zero_width"]


def test_final_inference_can_contain_only_selected_candidate():
    values = cells()
    del values[CANDIDATES[0]]
    result = infer(values, 50, 52900073, .0125)
    assert list(result["candidates"]) == [CANDIDATES[1]]
    assert select_candidate(result)["selected_candidate"] == CANDIDATES[1]


@pytest.mark.parametrize("mutation", ["missing_baseline", "shape", "nan", "bad_rate"])
def test_malformed_cells_are_rejected(mutation):
    values = cells()
    if mutation == "missing_baseline":
        del values[BASELINES[0]]
    elif mutation == "shape":
        values[CANDIDATES[0]] = np.zeros((3, 4, 3, 5))
    elif mutation == "nan":
        values[CANDIDATES[0]][0, 0, 0, 0] = np.nan
    else:
        values[CANDIDATES[0]][0, 0, 0, 1] = 1.1
    with pytest.raises(ValueError):
        run(values)

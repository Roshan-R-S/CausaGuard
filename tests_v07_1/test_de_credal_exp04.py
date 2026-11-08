"""Acceptance and falsification tests for Experiment 04: Robust Bayesian Risk Bounds.

Verifies exact rational risk bounds, corner-extremum derivations, decision tri-state logic,
Frechet copula bounds, and the conditional safety theorem.
"""

from __future__ import annotations

import ast
import json
from fractions import Fraction as F
from pathlib import Path

import pytest

from research.experiments.de_credal_exp04 import experiment
from research.experiments.de_credal_exp04.experiment import (
    CredalRates,
    Interval,
    RiskBounds,
    build_exp04_report,
    compute_frechet_joint_bounds,
    compute_frechet_risk_bounds,
    compute_rectangular_credal_bounds,
    run_experiment_04_benchmark,
    verify_corner_extrema_exhaustively,
)


def test_interval_validation_and_properties():
    iv = Interval(F(1, 10), F(3, 10))
    assert iv.low == F(1, 10)
    assert iv.high == F(3, 10)
    assert iv.width == F(2, 10)
    assert iv.contains(F(2, 10))
    assert not iv.contains(F(4, 10))

    # Inverted bounds raise ValueError
    with pytest.raises(ValueError, match="exceeds upper bound"):
        Interval(F(5, 10), F(2, 10))

    # Out of [0, 1] bounds raise ValueError
    with pytest.raises(ValueError, match="must be exact Fractions in"):
        Interval(F(-1, 10), F(5, 10))


def test_credal_bounds_hand_calculation_pass_and_fail():
    # Credal set: FP in [0.01, 0.03], FN in [0.17, 0.25]
    credal = CredalRates(
        fp=Interval(F(1, 100), F(3, 100)),
        fn=Interval(F(17, 100), F(25, 100)),
    )

    # 1. Passed evidence: Y = True
    # Worst case (upper): (FP_max, FN_max) = (3/100, 25/100)
    # L(clean) = 97/100, L(schema) = 25/100
    # Clean mass: (4/5) * (97/100) = 388/500
    # Schema mass: (1/5) * (25/100) = 25/500
    # Total mass: 413/500
    # Upper posterior: 25 / 413
    # Upper risk: (91/100) * (25/413) = 2275 / 41300 = 13 / 236 ≈ 0.0550847
    #
    # Best case (lower): (FP_min, FN_min) = (1/100, 17/100)
    # L(clean) = 99/100, L(schema) = 17/100
    # Clean mass: (4/5) * (99/100) = 396/500
    # Schema mass: (1/5) * (17/100) = 17/500
    # Total mass: 413/500
    # Lower posterior: 17 / 413
    # Lower risk: (91/100) * (17/413) = 1547 / 41300 = 221 / 5900 ≈ 0.0374576
    bounds_pass = compute_rectangular_credal_bounds(credal, passed=True)
    assert bounds_pass.lower_posterior == F(17, 413)
    assert bounds_pass.upper_posterior == F(25, 413)
    assert bounds_pass.lower_risk == F(221, 5900)
    assert bounds_pass.upper_risk == F(13, 236)
    assert bounds_pass.width == F(13, 236) - F(221, 5900)  # 26/1475
    assert bounds_pass.inconclusive is True  # 0.03746 <= 0.050 < 0.05508

    # 2. Failed evidence: Y = False
    # Worst case (upper): (FP_min, FN_min) = (1/100, 17/100)
    # L(clean) = 1/100, L(schema) = 83/100
    # Clean mass: (4/5) * (1/100) = 4/500
    # Schema mass: (1/5) * (83/100) = 83/500
    # Total mass: 87/500
    # Upper posterior: 83 / 87
    # Upper risk: (91/100) * (83/87) = 7553 / 8700 ≈ 0.86816
    #
    # Best case (lower): (FP_max, FN_max) = (3/100, 25/100)
    # L(clean) = 3/100, L(schema) = 75/100
    # Clean mass: (4/5) * (3/100) = 12/500
    # Schema mass: (1/5) * (75/100) = 75/500
    # Total mass: 87/500
    # Lower posterior: 75 / 87 = 25 / 29
    # Lower risk: (91/100) * (25/29) = 2275 / 2900 = 91 / 116 ≈ 0.78448
    bounds_fail = compute_rectangular_credal_bounds(credal, passed=False)
    assert bounds_fail.lower_posterior == F(25, 29)
    assert bounds_fail.upper_posterior == F(83, 87)
    assert bounds_fail.lower_risk == F(91, 116)
    assert bounds_fail.upper_risk == F(7553, 8700)
    assert bounds_fail.disqualified is True  # 91/116 > 0.050


def test_corner_extrema_exhaustively_verified():
    # Verify analytical corner formula matches exhaustive 4-corner enumeration across multiple credal sets
    sets = [
        CredalRates(Interval(F(1, 100), F(5, 100)), Interval(F(1, 10), F(3, 10))),
        CredalRates(Interval(F(0), F(1, 20)), Interval(F(1, 5), F(1, 2))),
        CredalRates(Interval(F(2, 10), F(4, 10)), Interval(F(3, 10), F(8, 10))),
    ]
    for cs in sets:
        for passed in (True, False):
            assert verify_corner_extrema_exhaustively(cs, passed)


def test_decision_tristate_logic():
    # 1. Qualifies: upper risk <= 0.050
    b_qual = RiskBounds(
        lower_risk=F(1, 100),
        upper_risk=F(4, 100),
        lower_posterior=F(1, 91),
        upper_posterior=F(4, 91),
        status="defined",
    )
    assert b_qual.qualifies is True
    assert b_qual.disqualified is False
    assert b_qual.inconclusive is False

    # 2. Disqualified: lower risk > 0.050
    b_disq = RiskBounds(
        lower_risk=F(6, 100),
        upper_risk=F(10, 100),
        lower_posterior=F(6, 91),
        upper_posterior=F(10, 91),
        status="defined",
    )
    assert b_disq.qualifies is False
    assert b_disq.disqualified is True
    assert b_disq.inconclusive is False

    # 3. Inconclusive (Abstention): lower risk <= 0.050 < upper risk
    b_inconc = RiskBounds(
        lower_risk=F(3, 100),
        upper_risk=F(7, 100),
        lower_posterior=F(3, 91),
        upper_posterior=F(7, 91),
        status="defined",
    )
    assert b_inconc.qualifies is False
    assert b_inconc.disqualified is False
    assert b_inconc.inconclusive is True


def test_frechet_copula_bounds_hand_calculation():
    p_clean = F(23, 25)
    p_schema = F(3, 5)
    c_low, c_high = compute_frechet_joint_bounds(p_clean, p_clean)
    s_low, s_high = compute_frechet_joint_bounds(p_schema, p_schema)

    assert c_low == F(21, 25)  # 23/25 + 23/25 - 1 = 21/25
    assert c_high == F(23, 25)  # min(23/25, 23/25) = 23/25
    assert s_low == F(1, 5)  # 3/5 + 3/5 - 1 = 1/5
    assert s_high == F(3, 5)  # min(3/5, 3/5) = 3/5

    prior = F(1, 10)
    bounds = compute_frechet_risk_bounds(prior, p_clean, p_schema)
    assert bounds.lower_posterior == F(5, 212)
    assert bounds.upper_posterior == F(5, 68)
    assert bounds.lower_risk == F(91, 4240)  # ~0.02146
    assert bounds.upper_risk == F(91, 1360)  # ~0.06691
    assert bounds.inconclusive is True

    # Check enclosure of true joint risk from Exp03 common source model
    true_risk = F(1183, 21640)  # ~0.05467
    assert bounds.encloses(true_risk) is True


def test_six_benchmark_scenarios_reproduction():
    b = run_experiment_04_benchmark()

    # Scenario A: Correctly specified point estimate
    assert b["A_correct_point"]["risk"]["exact"] == "21/400"
    assert b["A_correct_point"]["qualifies"] is False
    assert b["A_correct_point"]["false_safety_qualification"] is False

    # Scenario B: Misspecified point estimate (Exp03 Minimal Counterexample)
    assert b["B_misspecified_point"]["assumed_risk"]["exact"] == "91/2060"
    assert b["B_misspecified_point"]["assumed_qualifies"] is True
    assert b["B_misspecified_point"]["true_qualifies"] is False
    assert b["B_misspecified_point"]["false_safety_qualification"] is True

    # Scenario C: Credal inference with true model inside credal set
    c = b["C_credal_inside"]
    assert c["bounds"]["lower_risk"]["exact"] == "221/5900"
    assert c["bounds"]["upper_risk"]["exact"] == "13/236"
    assert c["encloses_truth"] is True
    assert c["false_safety_qualification"] is False
    assert c["inconclusive"] is True

    # Scenario D: Credal inference with true model OUTSIDE credal set
    d = b["D_credal_outside"]
    assert d["encloses_truth"] is False
    assert d["bounds"]["qualifies"] is True
    assert d["false_safety_qualification"] is True

    # Scenario E: Dependence-aware Frechet bounds
    e = b["E_dependence_aware_credal"]
    assert e["bounds"]["lower_risk"]["exact"] == "91/4240"
    assert e["bounds"]["upper_risk"]["exact"] == "91/1360"
    assert e["encloses_truth"] is True
    assert e["false_safety_qualification"] is False
    assert e["inconclusive"] is True

    # Scenario F: Incorrect independence assumption
    f = b["F_incorrect_independence"]
    assert f["naive_risk"]["exact"] == "91/2216"
    assert f["naive_qualifies"] is True
    assert f["true_qualifies"] is False
    assert f["false_safety_qualification"] is True


def test_theorem_guarantee_zero_false_qualifications_when_enclosed():
    """Theorem 1 Empirical Verification:

    If true likelihood theta* in C, then upper risk bound >= true risk.
    Hence, if upper risk <= LIMIT, then true risk <= LIMIT.
    False safety qualification count is mathematically ZERO.
    """
    report = build_exp04_report()
    assert report["theorem_guarantee_verified"] is True
    assert report["grid_coverage_summary"]["false_safety_qualifications"] == 0
    assert report["grid_coverage_summary"]["enclosed_count"] == 96


def test_deterministic_report_json_export():
    report = build_exp04_report()
    raw_json = json.dumps(report, sort_keys=True, allow_nan=False)
    loaded = json.loads(raw_json)
    assert loaded["experiment"] == "Experiment 04: Robust Bayesian Risk Bounds"
    assert loaded["status"] == "EXPLORATORY PRE-FREEZE NO-GO"

    # AST check for forbidden imports
    tree = ast.parse(Path(experiment.__file__).read_text())
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert not any(x and ("domain_de" in x or "policy" in x or "random" in x) for x in imports)

"""Exact and deterministic robustness acceptance tests; no sampled episodes."""

from fractions import Fraction as F

import pytest

from research.experiments.de_robustness_exp03.experiment import (
    RATE_GRID,
    JointModel,
    Rates,
    assess,
    boundary_panel,
    build_report,
    common_source_model,
    exact_posterior,
    factorizes,
    independent_model,
    infer,
)


def test_minimal_one_rate_mismatch_by_hand():
    row = assess(Rates(F(1, 50), F(1, 5)), Rates(F(1, 50), F(6, 25)), True)
    assert row["assumed_risk"]["exact"] == "91/2060"
    assert row["true_risk"]["exact"] == "21/400"
    assert row["false_safety_qualification"] is True
    assert row["unnecessary_rejection"] is False
    assert row["assumed_posterior"]["exact"] == "5/103"
    assert row["true_posterior"]["exact"] == "3/52"


def test_false_positive_mismatch_and_negative_evidence():
    # Failing evidence likelihood is (FP,1-FN), not (1-FP,FN).
    row = assess(Rates(F(4, 5), F(4, 5)), Rates(F(1, 50), F(4, 5)), False)
    assert row["assumed_posterior"]["exact"] == "1/17"
    assert row["true_posterior"]["exact"] == "5/7"
    assert exact_posterior(F(1, 5), (F(1, 50), F(49, 50))) == F(49, 53)


def test_invalid_probability_and_zero_mass_are_explicit():
    for x in [F(-1), F(2), True, float("nan"), float("inf")]:
        with pytest.raises(ValueError):
            Rates(x, F(1, 5))
    with pytest.raises(ValueError):
        exact_posterior(F(2), (F(1), F(1)))
    assert exact_posterior(F(1, 5), (F(0), F(0))) is None
    r = assess(Rates(F(1), F(0)), Rates(F(0), F(1)), True)
    assert r["status"] == "assumed_impossible"
    assert r["false_safety_qualification"] is None
    assert infer(F(1, 5), (F(0), F(0)))["status"] == "impossible_evidence"
    r = assess(Rates(F(0), F(1)), Rates(F(1), F(0)), True)
    assert r["status"] == "true_impossible"
    assert r["relative_error"] is None


def test_joint_shared_cause_is_not_duplicate_signals():
    model = common_source_model()
    assert model.clean == (F(113, 125), F(2, 125), F(2, 125), F(8, 125))
    assert model.schema == (F(13, 25), F(2, 25), F(2, 25), F(8, 25))
    assert sum(model.clean) == sum(model.schema) == 1
    assert model.clean[1] + model.clean[2] > 0
    assert model.schema[1] + model.schema[2] > 0
    assert not factorizes(model)
    assert factorizes(independent_model(model))
    assert exact_posterior(F(1, 10), (model.clean[0], model.schema[0])) == F(65, 1082)
    independent = independent_model(model)
    assert exact_posterior(F(1, 10), (independent.clean[0], independent.schema[0])) == F(25, 554)
    with pytest.raises(ValueError):
        JointModel((F(1),) * 4, (F(1),) * 4)


def test_boundary_exact_equality_and_nearby_false_qualification():
    panel = boundary_panel()
    assert panel["critical_fn"]["exact"] == "49/215"
    rows = panel["rows"]
    assert [r["true_qualifies"] for r in rows] == [True, True, False]
    assert rows[1]["true_risk"]["exact"] == "1/20"
    assert rows[2]["false_safety_qualification"] is True
    assert all(r["assumed_qualifies"] for r in rows)


@pytest.fixture(scope="module")
def report():
    return build_report(full=True)


def test_full_grid_and_matched_model_control(report):
    rows = report["h1_rows"]
    assert len(rows) == len(RATE_GRID) ** 4 * 2 == 4802
    for row in rows:
        if row["assumed_rates"] == row["generating_rates"] and row["status"] == "defined":
            assert row["absolute_error"]["exact"] == "0"
            assert not row["false_safety_qualification"]
        if row["status"] == "defined":
            assert (
                abs(float(row["engine"]["posterior_schema"]) - row["assumed_posterior"]["value"])
                < 1e-14
            )
    assert report["h1_summary"]["false_safety_qualifications"] > 0
    assert report["h1_summary"]["worst_absolute_error"]["exact"] == "91/100"


def test_provenance_cannot_certify_false_independence(report):
    row = report["h2"]["dependent"][0]
    assert row["evidence"] == [True, True]
    assert row["naive_risk"]["exact"] == "91/2216"
    assert row["true_risk"]["exact"] == "1183/21640"
    assert row["false_safety_qualification"]
    assert row["unaudited_naive_engine"]["status"] == "ok"
    assert row["unsupported_second_update"]["status"] == "dependency_rejected"
    assert row["audited_mode"] == "joint_required"
    assert row["joint_engine"]["status"] == "ok"
    for control in report["h2"]["independent_control"]:
        assert control["audited_mode"] == "independence_verified"
        assert control["naive_risk"] == control["true_risk"]


def test_inference_interface_receives_only_assumed_model(monkeypatch):
    from research.experiments.de_robustness_exp03 import experiment

    original = experiment.infer
    received = []

    def spy(prior, likelihood):
        received.append((prior, likelihood))
        return original(prior, likelihood)

    monkeypatch.setattr(experiment, "infer", spy)
    assumed = Rates(F(1, 50), F(1, 50))
    assess(assumed, Rates(F(4, 5), F(4, 5)), True)
    assert received == [(F(1, 5), (F(49, 50), F(1, 50)))]


def test_deterministic_strict_json_and_no_random_imports(report):
    import ast
    import json
    from pathlib import Path

    from research.experiments.de_robustness_exp03 import experiment

    assert json.dumps(report, sort_keys=True, allow_nan=False) == json.dumps(
        build_report(full=True), sort_keys=True, allow_nan=False
    )
    tree = ast.parse(Path(experiment.__file__).read_text())
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert not any(x and ("domain_de" in x or "policy" in x or "random" in x) for x in imports)


def test_boundary_exact_equality_engine_audit():
    """Verify finite-precision Decimal vs exact Fraction boundary behavior at FN* = 49/215."""
    panel = boundary_panel()
    audit = panel["equality_engine_audit"]
    # Exact Fraction arithmetic evaluates risk == 1/20 (0.050), so ar <= LIMIT is True
    assert audit["assumed_risk"]["exact"] == "1/20"
    assert audit["true_risk"]["exact"] == "1/20"
    assert audit["assumed_qualifies"] is True
    assert audit["true_qualifies"] is True
    # 80-digit Decimal arithmetic yields 0.050000...001 > 0.050, resulting in engine qualifies = False
    assert audit["engine"]["qualifies"] is False
    assert audit["engine"]["risk"].startswith("0.050000000000000000000000000000000000000000000000000000000000000000000000000000001")
    assert audit["engine_vs_exact_qualification_disagreement"] is True


def test_exhaustive_correlation_all_four_outcomes(report):
    """Exhaustively verify all four bivariate outcomes for correlated vs independent models."""
    dep_rows = report["h2"]["dependent"]
    assert len(dep_rows) == 4

    # Outcome 0: (True, True) - The critical false safety qualification
    r_tt = dep_rows[0]
    assert r_tt["evidence"] == [True, True]
    assert r_tt["naive_risk"]["exact"] == "91/2216"  # ~0.04106 <= 0.050 (passes naive)
    assert r_tt["true_risk"]["exact"] == "1183/21640"  # ~0.05467 > 0.050 (fails truth)
    assert r_tt["false_safety_qualification"] is True

    # Outcome 1: (True, False) - Inconsistent observations, fails safety in both
    r_tf = dep_rows[1]
    assert r_tf["evidence"] == [True, False]
    assert r_tf["naive_risk"]["exact"] == "91/376"  # ~0.242 > 0.050
    assert r_tf["true_risk"]["exact"] == "13/40"  # ~0.325 > 0.050
    assert r_tf["false_safety_qualification"] is False

    # Outcome 2: (False, True) - Symmetric inconsistent observation
    r_ft = dep_rows[2]
    assert r_ft["evidence"] == [False, True]
    assert r_ft["naive_risk"]["exact"] == "91/376"  # ~0.242 > 0.050
    assert r_ft["true_risk"]["exact"] == "13/40"  # ~0.325 > 0.050
    assert r_ft["false_safety_qualification"] is False

    # Outcome 3: (False, False) - Double failing evidence, severe risk
    r_ff = dep_rows[3]
    assert r_ff["evidence"] == [False, False]
    assert r_ff["naive_risk"]["exact"] == "91/136"  # ~0.669 > 0.050
    assert r_ff["true_risk"]["exact"] == "13/40"  # ~0.325 > 0.050
    assert r_ff["false_safety_qualification"] is False


def test_unnecessary_rejection_counterexample():
    """Verify an explicit counterexample where pessimistic assumed rates cause unnecessary rejection."""
    # Assumed: overly pessimistic (FN=4/5, FP=1/50); Generating: highly reliable (FN=1/50, FP=1/50)
    # Passed evidence: observed passed=True
    row = assess(Rates(F(1, 50), F(4, 5)), Rates(F(1, 50), F(1, 50)), True)
    assert row["assumed_posterior"]["exact"] == "10/59"  # ~0.1695
    assert row["assumed_risk"]["exact"] == "91/590"  # ~0.1542 > 0.050 (rejected)
    assert row["assumed_qualifies"] is False

    assert row["true_posterior"]["exact"] == "1/197"  # ~0.00508
    assert row["true_risk"]["exact"] == "91/19700"  # ~0.00462 <= 0.050 (qualifies)
    assert row["true_qualifies"] is True

    assert row["false_safety_qualification"] is False
    assert row["unnecessary_rejection"] is True
    assert row["status"] == "defined"


def test_grid_posterior_normalization_and_bounds(report):
    """Verify probabilistic invariants across all 4,802 grid scenarios."""
    rows = report["h1_rows"]
    assert len(rows) == 4802
    for r in rows:
        status = r["status"]
        if status == "defined":
            ap = F(r["assumed_posterior"]["exact"])
            tp = F(r["true_posterior"]["exact"])
            ar = F(r["assumed_risk"]["exact"])
            tr = F(r["true_risk"]["exact"])
            mass = F(r["true_evidence_mass"]["exact"])
            assert 0 <= ap <= 1
            assert 0 <= tp <= 1
            assert 0 <= ar <= F(91, 100)
            assert 0 <= tr <= F(91, 100)
            assert 0 <= mass <= 1
            assert r["absolute_error"] is not None
            assert F(r["absolute_error"]["exact"]) >= 0
        elif status in ("assumed_impossible", "true_impossible", "both_impossible"):
            assert r["false_safety_qualification"] is None
            assert r["unnecessary_rejection"] is None


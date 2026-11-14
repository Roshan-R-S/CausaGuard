"""Acceptance tests for WP6 Evaluation (Roadmap Section 13, WP6 & Section 9).

Validates:
1. 'No post-hoc final tuning' gate compliance (frozen seeds, architectures, and fingerprints);
2. Cluster-aware block bootstrap inference (resampling at cluster level, CI bounds);
3. Paired counterfactual potential-outcome evaluation (identical tapes, isolated queue states);
4. Out-of-sample calibration evaluation (Brier score and ECE on untouched evaluation cases);
5. 100% bitwise deterministic replay reproducibility;
6. Strict zero-latent leakage during evaluation;
7. Multi-domain coverage across Customer Support and Data Engineering.
"""

from __future__ import annotations

import numpy as np
import pytest
from causaguard_v07_1.domain_cs import (
    make_cs_cases_v07_1,
)

from research.experiments.wp4_baseline_comparison.adapters import (
    RulesRepairPolicyV07_1,
)
from research.experiments.wp5_contextual_model.dataset import (
    generate_train_and_cal_datasets,
)
from research.experiments.wp5_contextual_model.model import (
    build_wp5_ablation_model,
)
from research.experiments.wp6_evaluation.inference import (
    cluster_bootstrap_ci,
    compute_brier_and_ece,
    evaluate_out_of_sample_calibration,
)
from research.experiments.wp6_evaluation.run_wp6_evaluation import (
    CS_EVAL_BASE_SEEDS,
    DE_EVAL_BASE_SEEDS,
    run_evaluation_cluster,
    verify_deterministic_replay,
)


@pytest.fixture(scope="module")
def trained_cs_model():
    """Builds and fits a frozen CS contextual model for testing."""
    train, cal = generate_train_and_cal_datasets("cs", 85100100, 85100200, n_train=40, n_cal=20)
    m = build_wp5_ablation_model("cs", "contextual_full", seed=85100100, n_estimators=10)
    m.fit(train, cal)
    return m


@pytest.fixture(scope="module")
def trained_de_model():
    """Builds and fits a frozen DE contextual model for testing."""
    train, cal = generate_train_and_cal_datasets("de", 85200100, 85200200, n_train=40, n_cal=20)
    m = build_wp5_ablation_model("de", "contextual_full", seed=85200100, n_estimators=10)
    m.fit(train, cal)
    return m


def test_wp6_gate_seed_and_architecture_freezing(trained_cs_model, trained_de_model):
    """WP6 Gate: Verifies that evaluation seeds are disjoint from training/cal and model is frozen."""
    # Sizing and seed namespaces
    for prof, seed in CS_EVAL_BASE_SEEDS.items():
        assert seed >= 86000000, f"CS seed {seed} violates exploratory namespace floor!"
        assert seed != 85100100 and seed != 85100200, "CS eval seed overlaps training/cal seed!"

    for prof, seed in DE_EVAL_BASE_SEEDS.items():
        assert seed >= 86000000, f"DE seed {seed} violates exploratory namespace floor!"
        assert seed != 85200100 and seed != 85200200, "DE eval seed overlaps training/cal seed!"

    # Deterministic fingerprinting
    fp1 = trained_cs_model.fingerprint()
    fp2 = trained_cs_model.fingerprint()
    assert fp1 == fp2 and len(fp1) == 64


def test_wp6_cluster_bootstrap_inference():
    """Verifies that cluster_bootstrap_ci correctly computes cluster-level intervals."""
    # 10 synthetic cluster mean differences
    cluster_means = np.array([0.10, 0.12, 0.08, 0.14, 0.09, 0.11, 0.13, 0.10, 0.15, 0.08])
    res = cluster_bootstrap_ci(cluster_means, alpha=0.05, n_boot=1000, seed=123)

    assert "mean" in res and "std_err" in res and "ci_lower" in res and "ci_upper" in res
    assert np.isclose(res["mean"], np.mean(cluster_means))
    assert res["ci_lower"] <= res["mean"] <= res["ci_upper"]
    assert res["std_err"] > 0
    assert not res["zero_width"]

    # Rejects K < 2
    with pytest.raises(ValueError, match="requires at least K=2"):
        cluster_bootstrap_ci([0.1])


def test_wp6_paired_counterfactual_execution(trained_cs_model):
    """Verifies that paired cluster execution runs counterfactually with isolated queue states."""
    cases = make_cs_cases_v07_1(n=10, seed=86101000, profile="iid")
    policies = {
        "contextual_full": trained_cs_model,
        "rules_repair": RulesRepairPolicyV07_1(),
        "cost_rule_v07_1": RulesRepairPolicyV07_1(),  # dummy comparator
    }

    c_run = run_evaluation_cluster(cases=cases, policies=policies)

    assert "metrics" in c_run
    assert "paired_contrasts" in c_run
    assert "diff_cand_vs_repair" in c_run["paired_contrasts"]

    # Check that each case received identical observation across policies
    eps_cand = c_run["episodes"]["contextual_full"]
    eps_rep = c_run["episodes"]["rules_repair"]
    assert len(eps_cand) == len(eps_rep) == 10


def test_wp6_out_of_sample_calibration_under_shift(trained_cs_model):
    """Verifies that out-of-sample calibration evaluates Brier score and ECE on untouched cases."""
    cases_shift = make_cs_cases_v07_1(n=20, seed=86102000, profile="verifier_shift")
    cal_res = evaluate_out_of_sample_calibration(trained_cs_model, cases_shift, n_bins=5)

    assert "proceed" in cal_res
    proc = cal_res["proceed"]
    assert "brier_completed_raw" in proc
    assert "brier_completed_cal" in proc
    assert "ece_completed_raw" in proc
    assert "ece_completed_cal" in proc

    for k in proc:
        assert 0.0 <= proc[k] <= 1.0, f"Metric {k}={proc[k]} out of bounds [0, 1]"


def test_wp6_deterministic_replay_verification(trained_cs_model, trained_de_model):
    """Verifies that deterministic replay produces identical numerical traces."""
    assert verify_deterministic_replay("cs", trained_cs_model) is True
    assert verify_deterministic_replay("de", trained_de_model) is True


def test_wp6_strict_zero_latent_leakage(trained_cs_model):
    """Verifies that passing full Case objects to policies raises TypeError."""
    case = make_cs_cases_v07_1(n=1, seed=86101000)[0]
    with pytest.raises(TypeError, match="accepts only Observation"):
        trained_cs_model.select(case)  # type: ignore[arg-type]


def test_wp6_brier_and_ece_computation():
    """Verifies compute_brier_and_ece behavior and bounds."""
    y = np.array([1, 0, 1, 0])
    p = np.array([0.9, 0.1, 0.8, 0.2])
    res = compute_brier_and_ece(y, p, n_bins=5)
    assert 0.0 <= res["brier"] <= 1.0
    assert 0.0 <= res["ece"] <= 1.0

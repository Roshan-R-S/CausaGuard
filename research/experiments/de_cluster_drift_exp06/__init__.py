"""Experiment 06: Cluster-Robust Calibration and Sequential Drift Detection in Data Engineering (v0.7.1).

EXPLORATORY RESEARCH ONLY - PRE-FREEZE NO-GO.
"""

from research.experiments.de_cluster_drift_exp06.experiment import (
    EXPLORATORY_SEED_BASE,
    ClusteredBatch,
    CredalRates,
    Interval,
    RiskBounds,
    calibrate_clustered_rates,
    compute_credal_risk_bounds,
    estimate_icc_and_deff,
    evaluate_calibration_benchmark,
    evaluate_drift_monitoring_benchmark,
    generate_clustered_batch,
    method_a_naive_clopper_pearson,
    method_b_design_effect_clopper_pearson,
    method_c_beta_binomial_profile,
    method_d_cluster_bootstrap,
    method_e_conservative_cluster_bound,
    run_full_experiment_06,
)

__all__ = [
    "EXPLORATORY_SEED_BASE",
    "ClusteredBatch",
    "CredalRates",
    "Interval",
    "RiskBounds",
    "calibrate_clustered_rates",
    "compute_credal_risk_bounds",
    "estimate_icc_and_deff",
    "evaluate_calibration_benchmark",
    "evaluate_drift_monitoring_benchmark",
    "generate_clustered_batch",
    "method_a_naive_clopper_pearson",
    "method_b_design_effect_clopper_pearson",
    "method_c_beta_binomial_profile",
    "method_d_cluster_bootstrap",
    "method_e_conservative_cluster_bound",
    "run_full_experiment_06",
]


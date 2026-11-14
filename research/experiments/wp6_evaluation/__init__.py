"""CausaGuard PhD Research Master Roadmap 2026: Work Package 6 (Evaluation).

Implements:
- Paired counterfactual comparisons across matched evaluation clusters;
- Cluster-aware block bootstrap inference;
- Distribution shift sensitivity analysis across 4 profiles;
- Out-of-sample Brier score and Expected Calibration Error (ECE) evaluation;
- Deterministic replay verification;
- Strict 'No post-hoc final tuning' gate enforcement.
"""

from __future__ import annotations

from research.experiments.wp6_evaluation.inference import (
    cluster_bootstrap_ci,
    compute_brier_and_ece,
    evaluate_out_of_sample_calibration,
)
from research.experiments.wp6_evaluation.run_wp6_evaluation import (
    evaluate_domain_wp6,
    run_evaluation_cluster,
    run_wp6_evaluation,
    verify_deterministic_replay,
)

__all__ = [
    "cluster_bootstrap_ci",
    "compute_brier_and_ece",
    "evaluate_domain_wp6",
    "evaluate_out_of_sample_calibration",
    "run_evaluation_cluster",
    "run_wp6_evaluation",
    "verify_deterministic_replay",
]

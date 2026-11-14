"""CausaGuard PhD Research Master Roadmap 2026: Work Package 5 (Contextual Model).

Implements Study B (Cost-Sensitive Intervention Learning) across Customer Support
and Data Engineering domains with:
- Multi-output random forest regression architecture;
- Isotonic probability calibration on independent development split;
- Complete 5-variant ablation suite (full, no_calibration, no_cost, no_context, conservative_fallback);
- Cost-sensitive expected utility maximization under operational risk constraints (P(unsafe) <= 0.05);
- Strict zero-latent leakage verification.
"""

from __future__ import annotations

from research.experiments.wp5_contextual_model.dataset import (
    Step1Record,
    Step2Record,
    WP5Dataset,
    generate_train_and_cal_datasets,
    generate_wp5_dataset,
)
from research.experiments.wp5_contextual_model.features import (
    extract_features_step1,
    extract_features_step2,
    validate_observation_no_leakage,
)
from research.experiments.wp5_contextual_model.model import (
    ACTIONS_CS_STEP1,
    ACTIONS_CS_STEP2,
    ACTIONS_DE_STEP1,
    ACTIONS_DE_STEP2,
    WP5_VARIANTS,
    TrainedContextualInterventionModel,
    build_wp5_ablation_model,
)

__all__ = [
    "ACTIONS_CS_STEP1",
    "ACTIONS_CS_STEP2",
    "ACTIONS_DE_STEP1",
    "ACTIONS_DE_STEP2",
    "Step1Record",
    "Step2Record",
    "TrainedContextualInterventionModel",
    "WP5Dataset",
    "WP5_VARIANTS",
    "build_wp5_ablation_model",
    "extract_features_step1",
    "extract_features_step2",
    "generate_train_and_cal_datasets",
    "generate_wp5_dataset",
    "validate_observation_no_leakage",
]

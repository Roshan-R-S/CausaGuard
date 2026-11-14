"""Trained contextual intervention models and ablation suite for WP5.

Implements multi-output regression models with leaf size control, isotonic calibration,
cost-sensitive utility optimization, budget feasibility constraints, and uncertainty fallback.

Follows CausaGuard PhD Research Master Roadmap 2026:
- Section 13, page 17: WP5 Contextual Model;
- Section 8, page 11: Study B Cost-Sensitive Intervention Learning;
- Section 9, pages 12-13: Baselines, ablations, and statistical safeguards.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

import numpy as np
from causaguard_v07_1.domain_cs import (
    CSCaseV07_1,
    CSEvidenceV07_1,
    CSObservationV07_1,
)
from causaguard_v07_1.domain_de import (
    DECaseV07_1,
    DEEvidenceV07_1,
    DEObservationV07_1,
)
from causaguard_v07_1.policy_v07_1 import BasePolicyV07_1
from sklearn.ensemble import RandomForestRegressor
from sklearn.isotonic import IsotonicRegression

from research.experiments.wp5_contextual_model.dataset import WP5Dataset
from research.experiments.wp5_contextual_model.features import (
    extract_features_step1,
    extract_features_step2,
    validate_observation_no_leakage,
)

WP5_VARIANTS = (
    "contextual_full",
    "no_context",
    "no_calibration",
    "no_cost",
    "no_uncertainty_fallback",
    "conservative_fallback",
)

ACTIONS_CS_STEP1 = ("proceed", "verify", "retry", "escalate")
ACTIONS_CS_STEP2 = ("proceed", "retry", "escalate")

ACTIONS_DE_STEP1 = ("proceed", "verify", "restore", "escalate")
ACTIONS_DE_STEP2 = ("proceed", "restore", "escalate")


class TrainedContextualInterventionModel(BasePolicyV07_1):
    """Cost-sensitive contextual intervention learning model with isotonic calibration."""

    def __init__(
        self,
        domain: Literal["cs", "de"],
        name: str = "contextual_full",
        context: bool = True,
        calibrated: bool = True,
        costs: bool = True,
        uncertainty_fallback: bool = True,
        conservative_fallback: bool = False,
        risk_limit: float = 0.050,
        n_estimators: int = 50,
        min_samples_leaf: int = 6,
        seed: int = 85100000,
    ) -> None:
        self.domain = domain
        self.name = name
        self.context = context
        self.calibrated = calibrated
        self.costs = costs
        self.uncertainty_fallback = uncertainty_fallback
        self.conservative_fallback = conservative_fallback
        self.risk_limit = risk_limit
        self.n_estimators = n_estimators
        self.min_samples_leaf = min_samples_leaf
        self.seed = seed

        self.models_s1: dict[str, RandomForestRegressor] = {}
        self.models_s2: dict[str, RandomForestRegressor] = {}
        self.calibrators_s1: dict[str, dict[str, IsotonicRegression]] = {}
        self.calibrators_s2: dict[str, dict[str, IsotonicRegression]] = {}
        self.fitted = False

    def fit(self, train_data: WP5Dataset, cal_data: WP5Dataset) -> TrainedContextualInterventionModel:
        """Fits multi-output regressors and isotonic calibrators on disjoint splits."""
        if train_data.domain != self.domain or cal_data.domain != self.domain:
            raise ValueError(
                f"Domain mismatch: model={self.domain}, train={train_data.domain}, cal={cal_data.domain}"
            )

        # 1. Step 1 fitting
        acts_s1 = ACTIONS_CS_STEP1 if self.domain == "cs" else ACTIONS_DE_STEP1
        X_train_s1 = np.array(
            [extract_features_step1(r.observation, context=self.context) for r in train_data.step1_records]
        )
        X_cal_s1 = np.array(
            [extract_features_step1(r.observation, context=self.context) for r in cal_data.step1_records]
        )

        for arm in acts_s1:
            Y_train_s1 = np.array([r.outcomes[arm] for r in train_data.step1_records])
            Y_cal_s1 = np.array([r.outcomes[arm] for r in cal_data.step1_records])

            rf = RandomForestRegressor(
                n_estimators=self.n_estimators,
                min_samples_leaf=self.min_samples_leaf,
                random_state=self.seed,
                n_jobs=1,
            ).fit(X_train_s1, Y_train_s1)
            self.models_s1[arm] = rf

            # Calibration on independent cal split
            raw_cal_s1 = rf.predict(X_cal_s1)
            iso_comp = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(
                raw_cal_s1[:, 0], Y_cal_s1[:, 0]
            )
            iso_unsafe = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(
                raw_cal_s1[:, 1], Y_cal_s1[:, 1]
            )
            self.calibrators_s1[arm] = {"completed": iso_comp, "unsafe": iso_unsafe}

        # 2. Step 2 fitting
        acts_s2 = ACTIONS_CS_STEP2 if self.domain == "cs" else ACTIONS_DE_STEP2
        if train_data.step2_records and cal_data.step2_records:
            X_train_s2 = np.array(
                [
                    extract_features_step2(r.observation, r.evidence, context=self.context)
                    for r in train_data.step2_records
                ]
            )
            X_cal_s2 = np.array(
                [
                    extract_features_step2(r.observation, r.evidence, context=self.context)
                    for r in cal_data.step2_records
                ]
            )

            for arm in acts_s2:
                Y_train_s2 = np.array([r.outcomes[arm] for r in train_data.step2_records])
                Y_cal_s2 = np.array([r.outcomes[arm] for r in cal_data.step2_records])

                rf_s2 = RandomForestRegressor(
                    n_estimators=self.n_estimators,
                    min_samples_leaf=self.min_samples_leaf,
                    random_state=self.seed,
                    n_jobs=1,
                ).fit(X_train_s2, Y_train_s2)
                self.models_s2[arm] = rf_s2

                raw_cal_s2 = rf_s2.predict(X_cal_s2)
                iso_comp_2 = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(
                    raw_cal_s2[:, 0], Y_cal_s2[:, 0]
                )
                iso_unsafe_2 = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(
                    raw_cal_s2[:, 1], Y_cal_s2[:, 1]
                )
                self.calibrators_s2[arm] = {"completed": iso_comp_2, "unsafe": iso_unsafe_2}

        self.fitted = True
        return self

    def _predict_arm(
        self,
        arm: str,
        features: np.ndarray,
        is_step2: bool = False,
    ) -> tuple[float, float, float, float]:
        """Predicts (complete, unsafe, cost, uncertainty_unsafe) for a single arm."""
        model = self.models_s2[arm] if is_step2 else self.models_s1[arm]
        calibrators = self.calibrators_s2[arm] if is_step2 else self.calibrators_s1[arm]

        feat_2d = features[None, :]
        raw_pred = model.predict(feat_2d)[0]
        raw_comp, raw_unsafe, est_cost = float(raw_pred[0]), float(raw_pred[1]), float(raw_pred[2])

        if self.calibrated:
            cal_comp = float(calibrators["completed"].predict([raw_comp])[0])
            cal_unsafe = float(calibrators["unsafe"].predict([raw_unsafe])[0])
            final_comp = cal_comp
            final_unsafe = cal_unsafe
        else:
            final_comp = raw_comp
            final_unsafe = raw_unsafe

        # Compute ensemble standard deviation for conservative fallback
        if self.conservative_fallback:
            tree_preds = np.array([tree.predict(feat_2d)[0, 1] for tree in model.estimators_])
            tree_std = float(np.std(tree_preds))
        else:
            tree_std = 0.0

        return final_comp, final_unsafe, est_cost, tree_std

    def select(
        self,
        observation: CSObservationV07_1 | DEObservationV07_1,
        evidence: CSEvidenceV07_1 | DEEvidenceV07_1 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        """Selects action honoring safety constraint, budget feasibility, and net utility."""
        if not self.fitted:
            raise RuntimeError(f"{self.name} must be fit() before calling select()!")

        if isinstance(observation, (CSCaseV07_1, DECaseV07_1)):
            raise TypeError(f"{self.name} accepts only Observation, not Case objects!")
        if kwargs.get("case") is not None:
            raise TypeError(f"{self.name} prohibits private case argument!")

        validate_observation_no_leakage(observation, evidence=evidence, caller=self.name)

        is_cs = isinstance(observation, CSObservationV07_1)
        expected_domain = "cs" if is_cs else "de"
        if self.domain != expected_domain:
            raise ValueError(f"Model trained for {self.domain} received {expected_domain} observation")

        val = observation.value
        harm = observation.harm
        esc_cost = observation.escalation_cost

        # ------------------------------------------------------------------
        # Step 1 Decision (evidence is None)
        # ------------------------------------------------------------------
        if evidence is None:
            acts = ACTIONS_CS_STEP1 if is_cs else ACTIONS_DE_STEP1
            x = extract_features_step1(observation, context=self.context)

            arm_predictions: dict[str, tuple[float, float, float, float]] = {}
            for arm in acts:
                arm_predictions[arm] = self._predict_arm(arm, x, is_step2=False)

            # Determine eligibility
            eligible_arms: list[str] = []
            utilities: dict[str, float] = {}

            for arm in acts:
                comp, unsafe, cost, tree_std = arm_predictions[arm]
                risk_effective = min(1.0, unsafe + tree_std) if self.conservative_fallback else unsafe

                # Budget feasibility: verify is pruned if B < 2
                if arm == "verify" and b_rem < 2:
                    continue

                # Risk constraint: operational risk must be <= risk_limit (0.050)
                # Escalate is always safe (delegates to human specialist)
                if self.uncertainty_fallback and arm != "escalate" and risk_effective > self.risk_limit:
                    continue

                eligible_arms.append(arm)

                # Compute utility
                if arm == "escalate":
                    utilities[arm] = -esc_cost if self.costs else 0.0
                else:
                    cost_term = cost if self.costs else 0.0
                    utilities[arm] = val * comp - harm * unsafe - cost_term

            if self.uncertainty_fallback and (not eligible_arms or eligible_arms == ["escalate"]):
                return "escalate"

            if not eligible_arms:
                return "proceed"

            return max(eligible_arms, key=lambda a: utilities[a])

        # ------------------------------------------------------------------
        # Step 2 Decision (evidence is present)
        # ------------------------------------------------------------------
        if b_rem < 1:
            return "escalate"

        acts_s2 = ACTIONS_CS_STEP2 if is_cs else ACTIONS_DE_STEP2
        x_s2 = extract_features_step2(observation, evidence, context=self.context)

        eligible_s2: list[str] = []
        utilities_s2: dict[str, float] = {}

        for arm in acts_s2:
            comp, unsafe, cost, tree_std = self._predict_arm(arm, x_s2, is_step2=True)
            risk_effective = min(1.0, unsafe + tree_std) if self.conservative_fallback else unsafe

            if self.uncertainty_fallback and arm != "escalate" and risk_effective > self.risk_limit:
                continue

            eligible_s2.append(arm)
            if arm == "escalate":
                utilities_s2[arm] = -esc_cost if self.costs else 0.0
            else:
                cost_term = cost if self.costs else 0.0
                utilities_s2[arm] = val * comp - harm * unsafe - cost_term

        if self.uncertainty_fallback and (not eligible_s2 or eligible_s2 == ["escalate"]):
            return "escalate"

        if not eligible_s2:
            return "proceed"

        return max(eligible_s2, key=lambda a: utilities_s2[a])

    def evaluate_calibration_metrics(self, test_data: WP5Dataset) -> dict[str, Any]:
        """Computes Brier scores and Expected Calibration Error (ECE) on test data."""
        if not self.fitted:
            raise RuntimeError("Model must be fit before evaluating calibration!")

        acts_s1 = ACTIONS_CS_STEP1 if self.domain == "cs" else ACTIONS_DE_STEP1
        X_test = np.array(
            [extract_features_step1(r.observation, context=self.context) for r in test_data.step1_records]
        )

        metrics: dict[str, Any] = {}
        for arm in acts_s1:
            Y_test = np.array([r.outcomes[arm] for r in test_data.step1_records])
            y_comp_true = Y_test[:, 0]
            y_unsafe_true = Y_test[:, 1]

            model = self.models_s1[arm]
            raw_preds = model.predict(X_test)
            raw_comp = raw_preds[:, 0]
            raw_unsafe = raw_preds[:, 1]

            cal_comp = self.calibrators_s1[arm]["completed"].predict(raw_comp)
            cal_unsafe = self.calibrators_s1[arm]["unsafe"].predict(raw_unsafe)

            brier_comp_raw = float(np.mean((raw_comp - y_comp_true) ** 2))
            brier_comp_cal = float(np.mean((cal_comp - y_comp_true) ** 2))
            ece_comp_raw = _compute_ece(y_comp_true, raw_comp)
            ece_comp_cal = _compute_ece(y_comp_true, cal_comp)

            brier_unsafe_raw = float(np.mean((raw_unsafe - y_unsafe_true) ** 2))
            brier_unsafe_cal = float(np.mean((cal_unsafe - y_unsafe_true) ** 2))
            ece_unsafe_raw = _compute_ece(y_unsafe_true, raw_unsafe)
            ece_unsafe_cal = _compute_ece(y_unsafe_true, cal_unsafe)

            metrics[arm] = {
                "brier_completed_raw": brier_comp_raw,
                "brier_completed_cal": brier_comp_cal,
                "ece_completed_raw": ece_comp_raw,
                "ece_completed_cal": ece_comp_cal,
                "brier_unsafe_raw": brier_unsafe_raw,
                "brier_unsafe_cal": brier_unsafe_cal,
                "ece_unsafe_raw": ece_unsafe_raw,
                "ece_unsafe_cal": ece_unsafe_cal,
            }
        return metrics

    def fingerprint(self) -> str:
        """Computes reproducible SHA-256 fingerprint for model parameters and fitted trees."""
        h = hashlib.sha256()

        def add(data: Any) -> None:
            h.update(json.dumps(data, sort_keys=True, allow_nan=False).encode())
            h.update(b"\n")

        add(
            [
                self.domain,
                self.name,
                self.context,
                self.calibrated,
                self.costs,
                self.uncertainty_fallback,
                self.conservative_fallback,
                self.risk_limit,
                self.n_estimators,
                self.min_samples_leaf,
                self.seed,
            ]
        )
        if self.fitted:
            for arm, model in sorted(self.models_s1.items()):
                add(arm)
                for est in model.estimators_:
                    tree = est.tree_.__getstate__()
                    for name in tree["nodes"].dtype.names:
                        add(tree["nodes"][name].tolist())
        return h.hexdigest()


def _compute_ece(y_true: np.ndarray, prob_pred: np.ndarray, n_bins: int = 10) -> float:
    """Computes Expected Calibration Error (ECE) for binary probabilistic predictions."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    if n == 0:
        return 0.0
    for i in range(n_bins):
        low, high = bins[i], bins[i + 1]
        mask = (prob_pred >= low) & (prob_pred <= high) if i == n_bins - 1 else (prob_pred >= low) & (prob_pred < high)
        if np.any(mask):
            bin_acc = float(np.mean(y_true[mask]))
            bin_conf = float(np.mean(prob_pred[mask]))
            ece += (float(np.sum(mask)) / n) * abs(bin_acc - bin_conf)
    return float(ece)


def build_wp5_ablation_model(
    domain: Literal["cs", "de"],
    variant: str,
    seed: int = 85100000,
    n_estimators: int = 50,
    min_samples_leaf: int = 6,
) -> TrainedContextualInterventionModel:
    """Instantiates a WP5 contextual model with the requested ablation configuration.

    Ablation variants (Roadmap Section 9, page 12):
    1. 'contextual_full': Full context, calibrated, cost-sensitive, uncertainty fallback.
    2. 'no_context': Reduced context (4 features), calibrated, cost-sensitive, uncertainty fallback.
    3. 'no_calibration': Full context, uncalibrated raw scores, cost-sensitive, uncertainty fallback.
    4. 'no_cost': Full context, calibrated, cost-insensitive utility, uncertainty fallback.
    5. 'no_uncertainty_fallback': Full context, calibrated, cost-sensitive, NO uncertainty fallback.
    6. 'conservative_fallback': Full context, calibrated, cost-sensitive, ensemble uncertainty inflation.
    """
    if variant == "contextual_full":
        return TrainedContextualInterventionModel(
            domain=domain,
            name="contextual_full",
            context=True,
            calibrated=True,
            costs=True,
            uncertainty_fallback=True,
            conservative_fallback=False,
            seed=seed,
            n_estimators=n_estimators,
            min_samples_leaf=min_samples_leaf,
        )
    elif variant == "no_context":
        return TrainedContextualInterventionModel(
            domain=domain,
            name="no_context",
            context=False,
            calibrated=True,
            costs=True,
            uncertainty_fallback=True,
            conservative_fallback=False,
            seed=seed,
            n_estimators=n_estimators,
            min_samples_leaf=min_samples_leaf,
        )
    elif variant == "no_calibration":
        return TrainedContextualInterventionModel(
            domain=domain,
            name="no_calibration",
            context=True,
            calibrated=False,
            costs=True,
            uncertainty_fallback=True,
            conservative_fallback=False,
            seed=seed,
            n_estimators=n_estimators,
            min_samples_leaf=min_samples_leaf,
        )
    elif variant == "no_cost":
        return TrainedContextualInterventionModel(
            domain=domain,
            name="no_cost",
            context=True,
            calibrated=True,
            costs=False,
            uncertainty_fallback=True,
            conservative_fallback=False,
            seed=seed,
            n_estimators=n_estimators,
            min_samples_leaf=min_samples_leaf,
        )
    elif variant == "no_uncertainty_fallback":
        return TrainedContextualInterventionModel(
            domain=domain,
            name="no_uncertainty_fallback",
            context=True,
            calibrated=True,
            costs=True,
            uncertainty_fallback=False,
            conservative_fallback=False,
            seed=seed,
            n_estimators=n_estimators,
            min_samples_leaf=min_samples_leaf,
        )
    elif variant == "conservative_fallback":
        return TrainedContextualInterventionModel(
            domain=domain,
            name="conservative_fallback",
            context=True,
            calibrated=True,
            costs=True,
            uncertainty_fallback=True,
            conservative_fallback=True,
            seed=seed,
            n_estimators=n_estimators,
            min_samples_leaf=min_samples_leaf,
        )
    else:
        raise ValueError(
            f"Unknown ablation variant: {variant}. Expected one of {WP5_VARIANTS}"
        )

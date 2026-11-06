"""v0.5.1 factorial intervention policies and balanced suite.

2x2x2 comparison varying features (7 vs 16), calibration (raw vs calibrated),
and risk limit (0.05 vs 0.10) with equalized multi-output architecture and leaf size 8.
"""

import hashlib
import json

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.isotonic import IsotonicRegression

from causaguard.intervention_env import ACTIONS, FEATURES
from causaguard.intervention_policy import (
    design,
    deterministic_actions,
    fixed_mean,
    refit_original,
)
from causaguard.provenance import policy_fingerprint

FACTORIAL_VARIANTS = (
    "f7_raw_r05",
    "f7_raw_r10",
    "f7_cal_r05",
    "f7_cal_r10",
    "f16_raw_r05",
    "f16_raw_r10",
    "f16_cal_r05",
    "f16_cal_r10",
)

REFERENCE_POLICIES = (
    "always_verify",
    "rules_repair",
    "cost_rule",
    "original",
)

FACTORIAL_POLICIES = FACTORIAL_VARIANTS + REFERENCE_POLICIES + ("oracle",)


class FactorialContextualModel:
    """Multi-output forest model with leaf size 8 and isotonic calibration."""

    def __init__(self, seed: int, trees: int, leaf_size: int = 8, context: bool = True):
        self.seed = seed
        self.trees = trees
        self.leaf_size = leaf_size
        self.context = context
        self.models = {}
        self.calibrators = {}

    def fit(self, observations, outcomes, calibration_observations, calibration_outcomes):
        x = design(observations, self.context)
        cx = design(calibration_observations, self.context)
        for arm in ACTIONS:
            y = np.asarray([[row[arm][k] for k in ("completed", "unsafe", "cost")]
                            for row in outcomes])
            model = RandomForestRegressor(
                n_estimators=self.trees,
                min_samples_leaf=self.leaf_size,
                n_jobs=1,
                random_state=self.seed,
            ).fit(x, y)
            self.models[arm] = model
            raw = fixed_mean(model, cx)
            self.calibrators[arm] = [
                IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(
                    raw[:, j], [row[arm][k] for row in calibration_outcomes]
                )
                for j, k in enumerate(("completed", "unsafe"))
            ]
        return self

    def predict(self, observations, calibrated: bool = True):
        x = design(observations, self.context)
        result = {}
        for arm in ACTIONS:
            result[arm] = fixed_mean(self.models[arm], x)
            if calibrated:
                for j, calibration in enumerate(self.calibrators[arm]):
                    result[arm][:, j] = calibration.predict(result[arm][:, j])
        return result

    def select(self, observations, predictions, risk_limit: float, costs: bool = True):
        chosen = []
        for i, o in enumerate(observations):
            if not all(np.isfinite(predictions[a][i]).all() for a in ACTIONS):
                chosen.append("escalate")
                continue
            eligible = [
                a for a in ACTIONS
                if a == "escalate"
                or (predictions[a][i, 1] <= risk_limit and (a == "proceed" or o.budget >= 2))
            ]

            def utility(arm):
                complete, unsafe, cost = predictions[arm][i]
                if arm == "escalate":
                    return -o.escalation_cost if costs else 0.0
                return o.value * complete - o.harm * unsafe - (cost if costs else 0)

            chosen.append(max(eligible, key=utility))
        return chosen

    def fingerprint(self):
        h = hashlib.sha256()

        def add(value):
            h.update(json.dumps(value, sort_keys=True, allow_nan=False).encode())
            h.update(b"\n")

        add([self.seed, self.trees, self.leaf_size, self.context, FEATURES])
        for arm in ACTIONS:
            add(arm)
            for estimator in self.models[arm].estimators_:
                tree = estimator.tree_.__getstate__()
                for name in tree["nodes"].dtype.names:
                    h.update(np.ascontiguousarray(tree["nodes"][name]).tobytes())
                h.update(np.ascontiguousarray(tree["values"]).tobytes())
            for calibration in self.calibrators[arm]:
                add([calibration.X_thresholds_.tolist(), calibration.y_thresholds_.tolist()])
        return h.hexdigest()


class FactorialPolicySuite:
    def __init__(self, config, seed: int):
        self.config = config
        self.seed = seed
        self.leaf_size = getattr(config, "leaf_size", 8)
        self.base = None
        self.model_16 = None
        self.model_7 = None

    def fit(self, cases, outcomes, calibration_cases, calibration_outcomes):
        observations = [c.observation for c in cases]
        calibration = [c.observation for c in calibration_cases]
        self.base = refit_original(observations, outcomes, self.seed, self.config.trees)
        self.model_16 = FactorialContextualModel(
            self.seed, self.config.trees, self.leaf_size, context=True
        )
        self.model_7 = FactorialContextualModel(
            self.seed, self.config.trees, self.leaf_size, context=False
        )
        for model in (self.model_16, self.model_7):
            model.fit(observations, outcomes, calibration, calibration_outcomes)
        return self

    def identity(self):
        return {
            "original": policy_fingerprint(self.base),
            "contextual_16": self.model_16.fingerprint(),
            "contextual_7": self.model_7.fingerprint(),
        }

    def decisions(self, observations):
        legacy = [o.legacy() for o in observations]
        repaired, cost = deterministic_actions(observations, 0.05)

        raw_16 = self.model_16.predict(observations, calibrated=False)
        cal_16 = self.model_16.predict(observations, calibrated=True)
        raw_7 = self.model_7.predict(observations, calibrated=False)
        cal_7 = self.model_7.predict(observations, calibrated=True)

        decisions = {
            # 8 factorial variants
            "f7_raw_r05": self.model_7.select(observations, raw_7, risk_limit=0.05),
            "f7_raw_r10": self.model_7.select(observations, raw_7, risk_limit=0.10),
            "f7_cal_r05": self.model_7.select(observations, cal_7, risk_limit=0.05),
            "f7_cal_r10": self.model_7.select(observations, cal_7, risk_limit=0.10),
            "f16_raw_r05": self.model_16.select(observations, raw_16, risk_limit=0.05),
            "f16_raw_r10": self.model_16.select(observations, raw_16, risk_limit=0.10),
            "f16_cal_r05": self.model_16.select(observations, cal_16, risk_limit=0.05),
            "f16_cal_r10": self.model_16.select(observations, cal_16, risk_limit=0.10),
            # 4 reference policies
            "always_verify": ["verify"] * len(observations),
            "rules_repair": repaired,
            "cost_rule": cost,
            "original": [d.action for d in self.base.recommend_many(legacy)],
        }
        scores = {
            "f16_raw": raw_16,
            "f16_cal": cal_16,
            "f7_raw": raw_7,
            "f7_cal": cal_7,
        }
        return decisions, scores


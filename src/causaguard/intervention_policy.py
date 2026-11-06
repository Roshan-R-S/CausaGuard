"""v0.5 observational selectors and explicitly labeled simulation-only oracle.

Legacy algorithms are unchanged and refit on the SAME v0.5 potential outcomes.
Every non-oracle selector receives only the public Observation sequence.
"""

import hashlib
import json

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.isotonic import IsotonicRegression

from causaguard.conservative import ConservativePolicy
from causaguard.data import features
from causaguard.intervention_env import ACTIONS, FEATURES
from causaguard.policy import LearnedPolicy
from causaguard.provenance import policy_fingerprint

POLICIES = ("always_verify", "rules_only", "rules_repair", "cost_rule", "original",
            "conservative", "contextual", "no_calibration", "no_cost", "no_context", "oracle")


def design(observations, context=True):
    if context:
        return np.asarray([[getattr(o, name) for name in FEATURES] for o in observations])
    return np.asarray([features(o.legacy()) for o in observations])


def fixed_mean(model, x):
    # Same accumulation order for batch and singleton prediction and replay.
    value = np.zeros((len(x), model.n_outputs_))
    for tree in model.estimators_:
        value += tree.predict(x).reshape(len(x), model.n_outputs_)
    return value / len(model.estimators_)


class ContextualPolicy:
    def __init__(self, seed, trees, risk_limit, context=True):
        self.seed, self.trees, self.risk_limit, self.context = seed, trees, risk_limit, context
        self.models, self.calibrators = {}, {}

    def fit(self, observations, outcomes, calibration_observations, calibration_outcomes):
        x = design(observations, self.context)
        cx = design(calibration_observations, self.context)
        for arm in ACTIONS:
            y = np.asarray([[row[arm][k] for k in ("completed", "unsafe", "cost")]
                            for row in outcomes])
            model = RandomForestRegressor(n_estimators=self.trees, min_samples_leaf=12,
                                          n_jobs=1, random_state=self.seed).fit(x, y)
            self.models[arm] = model
            raw = fixed_mean(model, cx)
            self.calibrators[arm] = [
                IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(
                    raw[:, j], [row[arm][k] for row in calibration_outcomes])
                for j, k in enumerate(("completed", "unsafe"))]
        return self

    def predict(self, observations, calibrated=True):
        x = design(observations, self.context)
        result = {}
        for arm in ACTIONS:
            result[arm] = fixed_mean(self.models[arm], x)
            if calibrated:
                for j, calibration in enumerate(self.calibrators[arm]):
                    result[arm][:, j] = calibration.predict(result[arm][:, j])
        return result

    def select(self, observations, predictions, costs=True):
        chosen = []
        for i, o in enumerate(observations):
            if not all(np.isfinite(predictions[a][i]).all() for a in ACTIONS):
                chosen.append("escalate")
                continue
            eligible = [a for a in ACTIONS if a == "escalate" or
                        (predictions[a][i, 1] <= self.risk_limit
                         and (a == "proceed" or o.budget >= 2))]
            def utility(arm):
                complete, unsafe, cost = predictions[arm][i]
                # Escalation has known zero completion/risk and quoted cost.
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
        add([self.seed, self.trees, self.risk_limit, self.context, FEATURES])
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


def refit_original(observations, outcomes, seed, trees):
    """Refit, not a claim of zero-shot transfer: unchanged original/conservative rules."""
    base = LearnedPolicy(seed=seed)
    x = design(observations, context=False)
    base.feature_min, base.feature_max = x.min(axis=0), x.max(axis=0)
    base.training_scenario_seeds = None  # provenance is the v050 dataset digest
    for arm in ACTIONS:
        for target, models, offset in (("utility", base.reward_models, 0),
                                       ("unsafe", base.risk_models, 3)):
            models[arm] = RandomForestRegressor(n_estimators=trees, min_samples_leaf=4,
                                                n_jobs=1, random_state=seed + offset).fit(
                                                    x, [r[arm][target] for r in outcomes])
    return base


def deterministic_actions(observations, risk_limit):
    """Strong fixed cost-aware comparator, specified without fitted outcome labels.

    Uses noisy signals and quoted service quality with an approximate defect prior.
    It does not know the latent record, true shift parameters, or random tape.
    """
    repair, cost_rule = [], []
    for o in observations:
        repair.append("verify" if o.alarm > .5 or o.age > 48 else
                      "retry" if o.load > .55 else "proceed")
        bad = min(.95, .015 + .60 * o.alarm ** 2 + .12 * o.age / 72 + .05 * o.domain)
        available = 1 - (.02 + .45 * o.load)
        flag = bad * (1 - o.quoted_fn) + (1 - bad) * o.quoted_fp
        repair_success = .55 + .40 * o.quality
        estimates = {}
        for arm in ACTIONS:
            if arm == "escalate":
                estimates[arm] = -o.escalation_cost
                continue
            latency, cost, success, risk = .1, .01, available, available * bad
            if arm == "retry":
                success = 1 - (1 - available) ** 2 * (.4 + .4 * o.load)
                risk = success * bad * (1 - (.30 + .40 * o.load + .12 * o.domain))
                latency += .25 + o.load
                cost += o.retry_cost
            elif arm == "verify":
                latency += o.observation_delay + .2 + .25 * flag
                success *= 1 - flag * (1 - repair_success)
                risk = available * bad * o.quoted_fn
                cost += o.verify_cost
            if latency > o.deadline:
                success = risk = 0
            if risk <= risk_limit and (arm == "proceed" or o.budget >= 2):
                estimates[arm] = o.value * success - o.harm * risk - cost - o.time_cost * latency
        cost_rule.append(max(estimates, key=estimates.get))
    return repair, cost_rule


class PolicySuite:
    def __init__(self, config, seed):
        self.config, self.seed = config, seed

    def fit(self, cases, outcomes, calibration_cases, calibration_outcomes):
        observations = [c.observation for c in cases]
        calibration = [c.observation for c in calibration_cases]
        self.base = refit_original(observations, outcomes, self.seed, self.config.trees)
        self.contextual = ContextualPolicy(self.seed, self.config.trees, self.config.risk_limit)
        self.reduced = ContextualPolicy(self.seed, self.config.trees, self.config.risk_limit, False)
        for model in (self.contextual, self.reduced):
            model.fit(observations, outcomes, calibration, calibration_outcomes)
        return self

    def identity(self):
        return {"original": policy_fingerprint(self.base),
                "contextual": self.contextual.fingerprint(), "no_context": self.reduced.fingerprint()}

    def decisions(self, observations):
        # Deliberately accepts no Case, potential outcome, ID, seed, permission or latent flag.
        legacy = [o.legacy() for o in observations]
        repaired, cost = deterministic_actions(observations, self.config.risk_limit)
        raw, calibrated = self.contextual.predict(observations, False), self.contextual.predict(observations)
        reduced = self.reduced.predict(observations)
        return {
            "always_verify": ["verify"] * len(observations),
            "rules_only": ["proceed"] * len(observations), "rules_repair": repaired, "cost_rule": cost,
            "original": [d.action for d in self.base.recommend_many(legacy)],
            "conservative": [d.action for d in ConservativePolicy(self.base).recommend_many(legacy)],
            "contextual": self.contextual.select(observations, calibrated),
            "no_calibration": self.contextual.select(observations, raw),
            "no_cost": self.contextual.select(observations, calibrated, False),
            "no_context": self.reduced.select(observations, reduced)}, {"raw": raw, "calibrated": calibrated}

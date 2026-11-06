"""Locked 5% selectors; execution authorization remains outside every model."""

import numpy as np

from causaguard.factorial_policy import FactorialContextualModel
from causaguard.intervention_env import ACTIONS
from causaguard.intervention_policy import design, fixed_mean, refit_original
from causaguard.provenance import policy_fingerprint

CANDIDATES = ("f16_raw_r05", "f16_cal_r05")
BASELINES = ("original_r05", "rules_repair", "always_verify")
RISK_LIMIT = 0.05


def select_original(observations, rewards, risks):
    """Disclosed strict wrapper for original forests, without rounded risk gating."""
    chosen = []
    for index, observation in enumerate(observations):
        if not all(np.isfinite(rewards[arm][index]) and np.isfinite(risks[arm][index])
                   for arm in ACTIONS):
            chosen.append("escalate")
            continue
        eligible = [arm for arm in ACTIONS if arm == "escalate" or
                    (risks[arm][index] <= RISK_LIMIT
                     and (arm == "proceed" or observation.budget >= 2))]

        def utility(arm):
            return -observation.escalation_cost if arm == "escalate" else rewards[arm][index]

        chosen.append(max(eligible, key=utility))
    return chosen


class PolicySuite:
    """One contextual fit shared by the two candidates; one original refit."""

    def __init__(self, config, seed):
        self.config, self.seed = config, seed
        self.base = None
        self.contextual = None

    def fit(self, cases, outcomes, calibration_cases, calibration_outcomes):
        observations = [case.observation for case in cases]
        calibration = [case.observation for case in calibration_cases]
        self.base = refit_original(observations, outcomes, self.seed, self.config.trees)
        self.base.risk_limit = RISK_LIMIT
        self.contextual = FactorialContextualModel(
            self.seed, self.config.trees, self.config.leaf_size, context=True
        ).fit(observations, outcomes, calibration, calibration_outcomes)
        return self

    def identity(self):
        if self.base is None or self.contextual is None:
            raise RuntimeError("policy suite is not fitted")
        return {"original_r05": policy_fingerprint(self.base),
                "contextual_16": self.contextual.fingerprint()}

    def decisions(self, observations, selected=None):
        if selected is not None and selected not in CANDIDATES:
            raise ValueError("selected policy must be a locked candidate")
        if self.base is None or self.contextual is None:
            raise RuntimeError("policy suite is not fitted")
        candidates = CANDIDATES if selected is None else (selected,)
        if not observations:
            return {name: [] for name in candidates + BASELINES}
        decisions = {}
        for candidate in candidates:
            predictions = self.contextual.predict(
                observations, calibrated=candidate == "f16_cal_r05"
            )
            decisions[candidate] = self.contextual.select(
                observations, predictions, risk_limit=RISK_LIMIT
            )
        legacy = design(observations, context=False)
        rewards = {arm: fixed_mean(self.base.reward_models[arm], legacy)[:, 0]
                   for arm in ACTIONS}
        risks = {arm: fixed_mean(self.base.risk_models[arm], legacy)[:, 0]
                 for arm in ACTIONS}
        decisions["original_r05"] = select_original(observations, rewards, risks)
        # The historical fixed alarm/age/load rule has no predicted-risk gate.
        decisions["rules_repair"] = [
            "verify" if observation.alarm > .5 or observation.age > 48 else
            "retry" if observation.load > .55 else "proceed"
            for observation in observations
        ]
        decisions["always_verify"] = ["verify"] * len(observations)
        return decisions

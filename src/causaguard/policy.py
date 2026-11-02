"""Original per-action outcome models and reward-maximizing comparison policy."""
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor

from causaguard.data import FEATURE_NAMES, features, matrices
from causaguard.domain import Intervention, Scenario


@dataclass(frozen=True)
class Decision:
    action: str
    predicted_rewards: dict[str, float]
    predicted_unsafe_risk: dict[str, float]
    rationale: str
    risk_limit: float

    def as_dict(self) -> dict:
        return asdict(self)


class LearnedPolicy:
    def __init__(self, risk_limit: float = 0.10, seed: int = 42):
        if not 0.0 <= risk_limit <= 1.0:
            raise ValueError("risk_limit must be between zero and one")
        self.risk_limit = risk_limit
        self.seed = seed
        self.reward_models: dict[str, RandomForestRegressor] = {}
        self.risk_models: dict[str, RandomForestRegressor] = {}
        self.feature_names = FEATURE_NAMES

    def fit(self, scenarios: list[Scenario], n_estimators: int = 80) -> "LearnedPolicy":
        if len(scenarios) < 16:
            raise ValueError("at least 16 scenarios required")
        x, rewards, risks = matrices(scenarios)
        # Training-only support metadata for the optional conservative selector.
        # Older model artifacts without this metadata remain usable by the original policy.
        self.feature_min = x.min(axis=0)
        self.feature_max = x.max(axis=0)
        self.training_scenario_seeds = tuple(s.seed for s in scenarios)
        for action in Intervention:
            arm = action.value
            self.reward_models[arm] = RandomForestRegressor(
                n_estimators=n_estimators, min_samples_leaf=4, n_jobs=1,
                random_state=self.seed,
            ).fit(x, rewards[arm])
            # Regression on binary outcomes gives an empirical risk score;
            # it is NOT a formally calibrated probability or safety bound.
            self.risk_models[arm] = RandomForestRegressor(
                n_estimators=n_estimators, min_samples_leaf=4, n_jobs=1,
                random_state=self.seed + 3,
            ).fit(x, risks[arm])
        return self

    def recommend_many(self, scenarios: list[Scenario]) -> list[Decision]:
        """Vectorize tree predictions; apply the same independent gate to each case."""
        if not self.reward_models:
            raise RuntimeError("policy not trained")
        if not scenarios:
            return []
        x = np.stack([features(s) for s in scenarios])
        rewards = {
            a.value: self.reward_models[a.value].predict(x) for a in Intervention
        }
        risks = {
            a.value: np.clip(self.risk_models[a.value].predict(x), 0, 1)
            for a in Intervention
        }
        results = []
        for i, s in enumerate(scenarios):
            estimated_reward = {
                a.value: round(float(rewards[a.value][i]), 4) for a in Intervention
            }
            estimated_risk = {
                a.value: round(float(risks[a.value][i]), 4) for a in Intervention
            }
            if not s.confirmation_present:
                chosen = Intervention.ESCALATE.value
                reason = "hard policy: missing explicit user confirmation"
            else:
                allowed = [
                    a.value for a in Intervention
                    if estimated_risk[a.value] <= self.risk_limit
                ]
                if not allowed:
                    chosen = Intervention.ESCALATE.value
                    reason = "no model-scored option passed the risk threshold"
                else:
                    chosen = max(allowed, key=lambda arm: estimated_reward[arm])
                    reason = "highest predicted reward among model-scored eligible actions"
            results.append(Decision(
                chosen, estimated_reward, estimated_risk, reason, self.risk_limit,
            ))
        return results

    def recommend(self, scenario: Scenario) -> Decision:
        return self.recommend_many([scenario])[0]

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str | Path) -> "LearnedPolicy":
        # Only load a model file you created and trust. Joblib uses pickle.
        obj = joblib.load(path)
        if not isinstance(obj, cls):
            raise TypeError("model file is not a CausaGuard policy")
        return obj

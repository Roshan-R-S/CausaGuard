"""Verification-first selection. Ensemble spread is a heuristic, not a risk bound."""

from dataclasses import dataclass, field

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from causaguard.data import features
from causaguard.domain import Intervention, Scenario
from causaguard.policy import Decision, LearnedPolicy
from causaguard.safety import authorization_block


class ConservativeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    risk_limit: float = Field(default=0.03, ge=0, le=1)
    reward_margin: float = Field(default=0.05, ge=0, le=10)
    uncertainty_multiplier: float = Field(default=1.0, ge=0, le=10)
    max_reward_std: float = Field(default=0.35, ge=0, le=10)
    max_risk_std: float = Field(default=0.05, ge=0, le=1)


@dataclass(frozen=True)
class ConservativeDecision(Decision):
    policy: str = "conservative"
    abstained: bool = True
    diagnostics: dict = field(default_factory=dict)
    score_note: str = (
        "Random-forest risk scores and tree disagreement are heuristics; "
        "neither is a calibrated probability or statistical safety guarantee."
    )


class ConservativePolicy:
    def __init__(self, base: LearnedPolicy, config: ConservativeConfig | None = None):
        self.base = base
        self.config = config or ConservativeConfig()
        self.risk_limit = self.config.risk_limit

    def _statistics(self, x: np.ndarray) -> dict | None:
        stats = {}
        for kind, models in (("reward", self.base.reward_models),
                             ("risk", self.base.risk_models)):
            stats[kind] = {}
            for action in Intervention:
                model = models.get(action.value)
                trees = getattr(model, "estimators_", ())
                if len(trees) < 2:
                    return None
                predictions = np.asarray([tree.predict(x) for tree in trees])
                if not np.isfinite(predictions).all():
                    return None
                if kind == "risk" and ((predictions < 0) | (predictions > 1)).any():
                    return None
                # Fixed accumulation order gives identical single/batch decisions even
                # at a threshold. NumPy reductions can choose different summation paths.
                mean = np.zeros(len(x))
                for prediction in predictions:
                    mean += prediction
                mean /= len(trees)
                variance = np.zeros(len(x))
                for prediction in predictions:
                    variance += (prediction - mean) ** 2
                stats[kind][action.value] = (mean, np.sqrt(variance / len(trees)))
        return stats

    def recommend_many(self, scenarios: list[Scenario]) -> list[ConservativeDecision]:
        if not scenarios:
            return []
        x = np.stack([features(s) for s in scenarios])
        stats = self._statistics(x)
        lower = getattr(self.base, "feature_min", None)
        upper = getattr(self.base, "feature_max", None)
        support_known = (
            lower is not None and upper is not None
            and np.shape(lower) == (x.shape[1],) and np.shape(upper) == (x.shape[1],)
            and np.isfinite(lower).all() and np.isfinite(upper).all()
        )
        results = []
        cfg = self.config
        for i, scenario in enumerate(scenarios):
            rewards, risks, diagnostics = {}, {}, {"config": cfg.model_dump()}
            chosen, reason, abstained = "verify", "insufficient model evidence: verify first", True
            block = authorization_block(scenario)
            if stats is not None:
                rewards = {a.value: float(stats["reward"][a.value][0][i]) for a in Intervention}
                risks = {a.value: float(stats["risk"][a.value][0][i]) for a in Intervention}
                reward_std = {a.value: float(stats["reward"][a.value][1][i]) for a in Intervention}
                risk_std = {a.value: float(stats["risk"][a.value][1][i]) for a in Intervention}
                supported = bool(support_known and ((x[i] >= lower) & (x[i] <= upper)).all())
                diagnostics.update(reward_std=reward_std, risk_std=risk_std,
                                   within_training_range=supported, candidates={})
                # A known unsafe verification score may only tighten the fallback.
                verify_score = risks["verify"] + cfg.uncertainty_multiplier * risk_std["verify"]
                if verify_score > cfg.risk_limit:
                    chosen, reason = "escalate", "verification score exceeds risk threshold"
                elif not supported:
                    reason = "unknown or out-of-range training support: verify first"
                else:
                    eligible = []
                    for arm in ("proceed", "retry"):
                        advantage = rewards[arm] - rewards["verify"]
                        # Sum of spreads is deliberately conservative; this is NOT a CI.
                        adjusted = advantage - cfg.uncertainty_multiplier * (
                            reward_std[arm] + reward_std["verify"]
                        )
                        risk_score = risks[arm] + cfg.uncertainty_multiplier * risk_std[arm]
                        uncertain = (
                            max(reward_std[arm], reward_std["verify"]) > cfg.max_reward_std
                            or max(risk_std[arm], risk_std["verify"]) > cfg.max_risk_std
                        )
                        allowed = (not uncertain and risk_score <= cfg.risk_limit
                                   and adjusted > cfg.reward_margin)
                        diagnostics["candidates"][arm] = {
                            "reward_advantage": advantage,
                            "spread_adjusted_advantage": adjusted,
                            "risk_score_plus_spread": risk_score,
                            "uncertain": uncertain, "eligible": allowed,
                        }
                        if allowed:
                            eligible.append(arm)
                    if eligible:
                        chosen = max(eligible, key=lambda a: diagnostics["candidates"][a][
                            "spread_adjusted_advantage"])
                        reason = "reward advantage exceeds margin and all evidence checks pass"
                        abstained = False
                    else:
                        reason = "insufficient advantage, risk evidence, or agreement: verify first"
            if block:
                chosen, reason, abstained = "escalate", block, True
            results.append(ConservativeDecision(
                chosen, rewards, risks, reason, cfg.risk_limit,
                abstained=abstained, diagnostics=diagnostics,
            ))
        return results

    def recommend(self, scenario: Scenario) -> ConservativeDecision:
        return self.recommend_many([scenario])[0]

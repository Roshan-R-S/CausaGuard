"""Evaluate decisions against paired simulator counterfactuals, not real agents."""
from collections import Counter

from causaguard.domain import Intervention, Scenario
from causaguard.policy import LearnedPolicy
from causaguard.simulator import simulate


def heuristic(s: Scenario) -> Intervention:
    if not s.confirmation_present:
        return Intervention.ESCALATE
    if s.note_risk_score > 0.7 or s.authorization_confidence < 0.55:
        return Intervention.ESCALATE
    if s.data_age_hours > 28 or s.schema_warning:
        return Intervention.VERIFY
    if s.tool_error_rate > 0.55:
        return Intervention.RETRY
    return Intervention.PROCEED


def evaluate(policy: LearnedPolicy, scenarios: list[Scenario]) -> dict:
    if not scenarios:
        raise ValueError("no scenarios for evaluation")
    recommended = policy.recommend_many(scenarios)
    selected = iter(Intervention(d.action) for d in recommended)
    choices = {
        "always_proceed": lambda s: Intervention.PROCEED,
        "always_verify": lambda s: Intervention.VERIFY,
        "rules_baseline": heuristic,
        "learned_policy": lambda s: next(selected),
        "simulator_oracle_upper_bound": lambda s: max(
            Intervention, key=lambda arm: simulate(s, arm).reward
        ),
    }
    result = {}
    for name, selector in choices.items():
        outcomes = []
        arms = Counter()
        for s in scenarios:
            arm = selector(s)
            arms[arm.value] += 1
            outcomes.append(simulate(s, arm))
        result[name] = {
            "n": len(outcomes),
            "mean_reward": round(sum(o.reward for o in outcomes) / len(outcomes), 4),
            "unsafe_rate": round(sum(o.unsafe for o in outcomes) / len(outcomes), 4),
            "completion_rate": round(sum(o.completed for o in outcomes) / len(outcomes), 4),
            "defer_rate": round(sum(o.deferred for o in outcomes) / len(outcomes), 4),
            "action_counts": dict(arms),
        }
    return result

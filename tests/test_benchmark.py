from types import SimpleNamespace

import pytest

from causaguard.benchmark import paired_benchmark
from causaguard.data import make_scenarios
from causaguard.domain import Intervention
from causaguard.simulator import simulate


class FixedPolicy:
    def __init__(self, action):
        self.action = action

    def recommend_many(self, scenarios):
        return [
            SimpleNamespace(action=self.action.value)
            for _ in scenarios
        ]


def test_verify_policy_has_zero_paired_gap():
    scenarios = make_scenarios(20, 111)
    result = paired_benchmark(
        FixedPolicy(Intervention.VERIFY),
        scenarios,
        replicates=100,
        seed=123,
    )

    assert result["reward_gap"] == 0
    assert result["reward_gap_ci95"] == [0, 0]
    assert result["unsafe_gap"] == 0


def test_paired_reward_gap_matches_manual_outcomes():
    scenarios = make_scenarios(20, 222)

    expected = sum(
        simulate(s, Intervention.PROCEED).reward
        - simulate(s, Intervention.VERIFY).reward
        for s in scenarios
    ) / len(scenarios)

    result = paired_benchmark(
        FixedPolicy(Intervention.PROCEED),
        scenarios,
        replicates=100,
    )

    assert result["reward_gap"] == pytest.approx(expected, abs=1e-6)


def test_bootstrap_is_reproducible():
    scenarios = make_scenarios(20, 333)
    policy = FixedPolicy(Intervention.PROCEED)

    first = paired_benchmark(policy, scenarios, 100, seed=15)
    second = paired_benchmark(policy, scenarios, 100, seed=15)

    assert first == second


def test_invalid_inputs_are_rejected():
    policy = FixedPolicy(Intervention.VERIFY)

    with pytest.raises(ValueError):
        paired_benchmark(policy, [])

    with pytest.raises(ValueError):
        paired_benchmark(policy, make_scenarios(2), replicates=0)

import pytest

from causaguard.data import make_scenarios
from causaguard.policy import LearnedPolicy


@pytest.fixture(scope="session")
def trained_policy():
    return LearnedPolicy(seed=42).fit(make_scenarios(192, 42), n_estimators=8)

from causaguard.conservative import ConservativeConfig, ConservativePolicy
from causaguard.policy import LearnedPolicy
from causaguard.provenance import policy_fingerprint


def test_fingerprint_survives_independent_model_loads(trained_policy, tmp_path):
    path = tmp_path / "model.joblib"
    trained_policy.save(path)
    first, second = LearnedPolicy.load(path), LearnedPolicy.load(path)
    expected = policy_fingerprint(trained_policy)
    assert policy_fingerprint(first) == policy_fingerprint(second) == expected
    assert policy_fingerprint(ConservativePolicy(first)) == policy_fingerprint(ConservativePolicy(second))


def test_fingerprint_identifies_changed_configuration_and_tree(trained_policy, tmp_path):
    path = tmp_path / "model.joblib"
    trained_policy.save(path)
    loaded = LearnedPolicy.load(path)
    assert policy_fingerprint(ConservativePolicy(loaded)) != policy_fingerprint(
        ConservativePolicy(loaded, ConservativeConfig(reward_margin=0.2)))
    loaded.reward_models["proceed"].estimators_[0].tree_.value[0, 0, 0] += 0.01
    assert policy_fingerprint(loaded) != policy_fingerprint(trained_policy)

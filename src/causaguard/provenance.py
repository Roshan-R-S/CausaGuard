"""Stable fingerprints of predictive state, excluding object identity and C padding."""

import hashlib
import json

import numpy as np

from causaguard.policy import LearnedPolicy


def policy_fingerprint(policy) -> str:
    """Hash tree fields individually: pickled tree structs contain irrelevant padding.

    This is an identity check for reproducibility, not authentication of model files.
    As with replay, use the same Python/scikit-learn environment.
    """
    result = hashlib.sha256()

    def add(value):
        result.update(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                 allow_nan=False).encode("utf-8"))
        result.update(b"\n")

    add(f"{type(policy).__module__}.{type(policy).__qualname__}")
    base = getattr(policy, "base", policy)
    if hasattr(policy, "config"):
        add(policy.config.model_dump())
    if not isinstance(base, LearnedPolicy):
        # Small deterministic scripted policies used in sandbox tests/demonstrations.
        add(vars(policy))
        return result.hexdigest()
    add({"risk_limit": base.risk_limit, "seed": base.seed,
         "feature_names": base.feature_names,
         "training_scenario_seeds": getattr(base, "training_scenario_seeds", None)})
    for name in ("feature_min", "feature_max"):
        value = getattr(base, name, None)
        add(None if value is None else np.asarray(value).tolist())
    for kind in ("reward_models", "risk_models"):
        add(kind)
        for arm, model in sorted(getattr(base, kind).items()):
            add(arm)
            add(model.get_params())
            for estimator in model.estimators_:
                tree = estimator.tree_
                state = tree.__getstate__()
                add([tree.n_features, tree.n_outputs, state["max_depth"], state["node_count"]])
                arrays = [(name, state["nodes"][name]) for name in state["nodes"].dtype.names]
                arrays.append(("values", state["values"]))
                for name, array in arrays:
                    add([name, array.shape, array.dtype.str])
                    result.update(np.ascontiguousarray(array).tobytes())
    return result.hexdigest()

"""Paired crossed inference for the locked v0.5.2 study.

Evaluation seed clusters retain all profiles. Bootstrap indices are shared across
every policy and paired contrast; fixed baselines do not gain independent replicas.
"""

import numpy as np

from causaguard.intervention_env import PROFILES

METRICS = ("utility", "unsafe", "completed", "cost", "authorization_violation")
CANDIDATES = ("f16_raw_r05", "f16_cal_r05")
BASELINES = ("original_r05", "rules_repair", "always_verify")


def crossed_samples(cells, replicates, seed):
    """Return balanced Cartesian bootstrap means, with the last axes kept together.

    Integer multiplicities are exactly the independently sampled training and seed
    indices. Batched weighted sums avoid materializing repeated Cartesian cells.
    Constant columns are retained exactly, including equality at risk thresholds.
    """
    values = np.asarray(cells, dtype=float)
    if (values.ndim < 2 or min(values.shape) < 1 or not np.isfinite(values).all()
            or type(replicates) is not int or replicates < 1
            or type(seed) is not int or not 0 <= seed < 2**32):
        raise ValueError("invalid crossed-bootstrap cells, count, or seed")
    rows, columns = values.shape[:2]
    flat = values.reshape(rows * columns, -1)
    constant = np.all(flat == flat[0], axis=0)
    samples = np.empty((replicates, flat.shape[1]))
    samples[:, constant] = flat[0, constant]
    variable = np.ascontiguousarray(flat[:, ~constant])
    rng = np.random.default_rng(seed)
    for start in range(0, replicates, 256):
        stop = min(start + 256, replicates)
        weights = np.empty((stop - start, rows * columns))
        for i in range(stop - start):
            train = np.bincount(rng.integers(rows, size=rows), minlength=rows)
            evaluation = np.bincount(rng.integers(columns, size=columns), minlength=columns)
            weights[i] = (train[:, None] * evaluation[None, :]).ravel() / (rows * columns)
        if variable.shape[1]:
            samples[start:stop, ~constant] = weights @ variable
    return samples.reshape((replicates,) + values.shape[2:])


def gate(estimate, bound, alpha, threshold, relation, zero_width=False):
    """Apply the literal unrounded one-sided inequality; utility is strict."""
    if relation not in (">", "<=") or not np.isfinite([estimate, bound]).all():
        raise ValueError("invalid acceptance bound")
    return {
        "estimate": float(estimate), "bound": float(bound), "alpha": alpha,
        "threshold": threshold, "relation": relation,
        "passes": bool(bound > threshold if relation == ">" else bound <= threshold),
        "zero_width": bool(zero_width),
    }


def _description(values, samples, metrics):
    quantiles = np.quantile(samples, [0.025, 0.975], axis=0, method="linear")
    means = values.mean(axis=(0, 1))
    return {
        profile: {
            metric: {
                "estimate": float(means[p, m]),
                "lower": float(quantiles[0, p, m]),
                "upper": float(quantiles[1, p, m]),
                "zero_width": bool(quantiles[0, p, m] == quantiles[1, p, m]),
            }
            for m, metric in enumerate(metrics)
        }
        for p, profile in enumerate(PROFILES)
    }


def infer(cells, bootstrap_replicates, bootstrap_seed, alpha, auth_violations=0):
    """Infer from matched replica/seed/profile cells, using one-sided alpha quantiles.

    The study runner verifies case keys before constructing these mean cells and
    supplies the actual authorization count (mean cells cannot recover counts).
    """
    if (not isinstance(cells, dict) or not set(BASELINES).issubset(cells)
            or set(cells) - set(BASELINES + CANDIDATES)
            or not any(candidate in cells for candidate in CANDIDATES)
            or not isinstance(alpha, (int, float)) or isinstance(alpha, bool)
            or not 0 < alpha < 0.5
            or type(auth_violations) is not int or auth_violations < 0):
        raise ValueError("invalid paired policies, alpha, or authorization count")
    names = [p for p in CANDIDATES + BASELINES if p in cells]
    values = {p: np.asarray(cells[p], dtype=float) for p in names}
    shape = values[names[0]].shape
    if (len(shape) != 4 or shape[2:] != (len(PROFILES), len(METRICS))
            or min(shape[:2]) < 1
            or any(v.shape != shape or not np.isfinite(v).all() for v in values.values())):
        raise ValueError("require finite identical [replica, seed, four profiles, five metrics] cells")
    for value in values.values():
        if ((value[..., 1:3] < 0).any() or (value[..., 1:3] > 1).any()
                or (value[..., 3:] < 0).any()):
            raise ValueError("invalid rate, cost, or authorization cells")
    if auth_violations == 0 and any((v[..., 4] > 0).any() for v in values.values()):
        raise ValueError("authorization count contradicts positive violation cells")

    candidates = [p for p in CANDIDATES if p in values]
    differences = {
        f"{candidate}-{baseline}": values[candidate][..., :2] - values[baseline][..., :2]
        for candidate in candidates for baseline in BASELINES
    }
    # Stack paired differences BEFORE bootstrap. Every field receives identical draws.
    tensors = {**values, **differences}
    widths = {name: int(np.prod(tensor.shape[2:])) for name, tensor in tensors.items()}
    joined = np.concatenate([v.reshape(*shape[:2], -1) for v in tensors.values()], axis=2)
    draws = crossed_samples(joined, bootstrap_replicates, bootstrap_seed)
    samples = {}
    offset = 0
    for name, tensor in tensors.items():
        width = widths[name]
        samples[name] = draws[:, offset:offset + width].reshape(
            bootstrap_replicates, *tensor.shape[2:]
        )
        offset += width

    result = {
        "policies": {p: _description(v, samples[p], METRICS) for p, v in values.items()},
        "contrasts": {
            p: _description(v, samples[p], METRICS[:2]) for p, v in differences.items()
        },
        "candidates": {}, "authorization_violations": auth_violations,
    }
    iid = PROFILES.index("iid")
    for candidate in candidates:
        checks = {}
        specifications = [
            ("utility_vs_original_r05", f"{candidate}-original_r05", 0, .020, ">"),
            ("utility_vs_rules_repair", f"{candidate}-rules_repair", 0, .020, ">"),
            ("absolute_risk", candidate, 1, .050, "<="),
            ("excess_risk_vs_always_verify", f"{candidate}-always_verify", 1, .010, "<="),
        ]
        for name, tensor_name, metric, threshold, relation in specifications:
            draw = samples[tensor_name][:, iid, metric]
            bound = np.quantile(draw, alpha if relation == ">" else 1 - alpha, method="linear")
            estimate = tensors[tensor_name][:, :, iid, metric].mean()
            checks[name] = gate(
                estimate, bound, alpha, threshold, relation, bool(np.ptp(draw) == 0)
            )
        result["candidates"][candidate] = {
            "checks": checks,
            "eligible": auth_violations == 0 and all(c["passes"] for c in checks.values()),
            "iid_utility": float(values[candidate][:, :, iid, 0].mean()),
        }
    return result


def select_candidate(inference):
    """Deterministic eligibility selection; ties use the prespecified raw-first order."""
    eligible = [
        candidate for candidate in CANDIDATES
        if candidate in inference["candidates"]
        and inference["candidates"][candidate]["eligible"]
        and inference["authorization_violations"] == 0
    ]
    selected = max(
        eligible, key=lambda candidate: inference["candidates"][candidate]["iid_utility"]
    ) if eligible else None
    return {
        "status": "selected" if selected is not None else "development_stop",
        "selected_candidate": selected, "eligible_candidates": eligible,
    }

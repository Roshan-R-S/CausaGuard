"""Independent finite-latent-state DE reference, using only Python's standard library.

No candidate, executor, case, PRNG, or confirmatory imports. Eight latent states are
enumerated; uniform time noise is integrated analytically over affine segments.
This is an IID, authorized, single-episode model, conditional on available capacity.
It is a diagnostic reference, not a replacement policy or real-world causal model.
"""

from dataclasses import dataclass, fields
from itertools import combinations, product
from math import exp, fsum, isfinite, lgamma, log

STATES = tuple(product((False, True), repeat=3))  # schema, content, transient


def _probability(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not isfinite(x):
        raise ValueError("Probability must be finite and numeric")
    if not 0 <= x <= 1:
        raise ValueError("Probability outside [0,1]")


def _belief(p, size=None):
    if not p or (size is not None and len(p) != size):
        raise ValueError("Incorrect belief length")
    for x in p:
        _probability(x)
    if abs(fsum(p) - 1.0) > 1e-12:
        raise ValueError("Belief must sum to one")


def bayes(prior, likelihood):
    """Enumerate Bayes' rule. Impossible evidence raises rather than fabricating belief."""
    _belief(prior, len(likelihood))
    for x in likelihood:
        _probability(x)
    weights = tuple(p * lik for p, lik in zip(prior, likelihood))
    possible = tuple(p > 0 and lik > 0 for p, lik in zip(prior, likelihood))
    if not any(possible):
        raise ValueError("Evidence has zero probability")
    # Keep ordinary arithmetic unchanged for historical reproducibility. Rescale
    # rare products before normalization; distinguish exact zeros from underflow.
    if any(ok and w < 2**-1022 for ok, w in zip(possible, weights)):
        logs = tuple(
            log(p) + log(lik) if ok else -float("inf")
            for p, lik, ok in zip(prior, likelihood, possible)
        )
        peak = max(logs)
        weights = tuple(exp(x - peak) for x in logs)
    normalizer = fsum(weights)
    posterior = tuple(w / normalizer for w in weights)
    if any(ok and p == 0 for ok, p in zip(possible, posterior)):
        raise FloatingPointError("Positive posterior exceeds float dynamic range")
    return posterior


@dataclass(frozen=True)
class PublicDE:
    """Public observation only; intentionally has no hidden-state or random-tape fields."""

    pipeline_load: float = 0.2
    schema_alarm: float = 0.5
    data_age_hours: float = 24.0
    source_quality: float = 0.8
    column_count_changed: int = 0
    quoted_fp_schema: float = 0.02
    quoted_fn_schema: float = 0.02
    observation_delay: float = 0.1
    deadline_hours: float = 4.0
    value: float = 1.5
    harm: float = 5.0
    apply_cost: float = 0.02
    verify_cost: float = 0.1
    restore_cost: float = 0.45
    escalation_cost: float = 0.5
    time_cost_per_hour: float = 0.02
    budget: int = 2

    def __post_init__(self):
        for field in fields(self):
            x = getattr(self, field.name)
            if isinstance(x, bool) or not isinstance(x, (int, float)) or not isfinite(x) or x < 0:
                raise ValueError(f"Invalid public field {field.name}")
        for name in (
            "pipeline_load",
            "schema_alarm",
            "source_quality",
            "quoted_fp_schema",
            "quoted_fn_schema",
        ):
            _probability(getattr(self, name))
        if type(self.budget) is not int or self.budget not in (1, 2):
            raise ValueError("budget must be 1 or 2")
        if type(self.column_count_changed) is not int or self.column_count_changed not in (0, 1):
            raise ValueError("column_count_changed must be 0 or 1")


def _public(obs):
    if type(obs) is not PublicDE:
        raise TypeError("Reference accepts PublicDE only, never a simulator Case")


def _clip(x, low, high):
    return min(high, max(low, x))


def _beta_density(x, a, b):
    # Both implemented Beta laws have zero density at either endpoint.
    if x in (0.0, 1.0):
        return 0.0
    return exp((a - 1) * log(x) + (b - 1) * log(1 - x) + lgamma(a + b) - lgamma(a) - lgamma(b))


def generator_prior(obs):
    """P(S,C,T | public observation), derived from the nominal DE generator DAG.

    Endpoint alarms have zero density under both laws and are rejected explicitly.
    No actual_* error rate, realized failure state, outage, or draw is accessible.
    """
    _public(obs)
    ps = _clip(0.02 + 0.35 * obs.pipeline_load, 0.01, 0.85)
    column = obs.column_count_changed
    ls = _beta_density(obs.schema_alarm, 5.0, 2.0) * (2 / 3 if column else 1 / 3)
    ln = _beta_density(obs.schema_alarm, 1.5, 6.0) * (1 / 60 if column else 59 / 60)
    # Likelihood densities need not be <=1; normalize the two weighted densities directly.
    total = ps * ls + (1 - ps) * ln
    if total == 0:
        raise ValueError("Public alarm has zero density under the nominal model")
    ps = ps * ls / total
    pc = _clip(0.03 + 0.25 * obs.data_age_hours / 72 + 0.25 * (1 - obs.source_quality), 0.01, 0.90)
    pt = _clip(0.01 + 0.08 * obs.pipeline_load, 0.01, 0.25)
    return tuple(
        (ps if s else 1 - ps) * (pc if c else 1 - pc) * (pt if t else 1 - pt) for s, c, t in STATES
    )


def evidence_branches(prior, fp, fn):
    """Return ((schema_valid, content_clean), mass, posterior) for possible evidence.

    The current separated content-score supports make the binary statistic sufficient.
    Timing is state-independent. This does not model unquoted verifier shift.
    """
    _belief(prior, 8)
    _probability(fp)
    _probability(fn)
    result = []
    for valid, clean in product((False, True), repeat=2):
        likelihood = []
        for s, c, _ in STATES:
            pass_schema = fn if s else 1 - fp
            likelihood.append((pass_schema if valid else 1 - pass_schema) * float(clean != c))
        mass = fsum(p * lik for p, lik in zip(prior, likelihood))
        if mass == 0 and any(p > 0 and lik > 0 for p, lik in zip(prior, likelihood)):
            raise FloatingPointError("Positive evidence mass exceeds float dynamic range")
        if mass > 0:
            result.append(((valid, clean), mass, bayes(prior, likelihood)))
    return result


def _durations(obs):
    return {
        "proceed": (0.10, 0.20),
        "restore": (0.20 + obs.pipeline_load, 0.35 + obs.pipeline_load),
        "escalate": (1.20 + 1.50 * obs.pipeline_load, 1.50 + 1.50 * obs.pipeline_load),
    }


def terminal_values(
    obs,
    belief,
    *,
    elapsed=0.0,
    prior_cost=0.0,
    b_rem=1,
    cost_mode="executor",
    capacity_available=True,
    risk_limit=0.05,
):
    """Enumerate expected terminal utility/risk under nominal transitions.

    executor: prior_cost + fee + w*(elapsed + duration), matching existing double
    prefix charging. incremental: prior_cost + fee + w*duration, a labeled contrast.
    Authorization is a precondition; enforcement is graded independently in authorization.py.
    """
    _public(obs)
    _belief(belief, 8)
    if type(capacity_available) is not bool:
        raise ValueError("capacity_available must be a Boolean")
    if cost_mode not in ("executor", "incremental"):
        raise ValueError("Unknown cost_mode")
    if type(b_rem) is not int or b_rem not in (0, 1, 2):
        raise ValueError("Invalid remaining budget")
    if any(not isfinite(x) or x < 0 for x in (elapsed, prior_cost)):
        raise ValueError("Invalid elapsed time or prior cost")
    if risk_limit is not None:
        _probability(risk_limit)
    availability = 1 - _clip(0.01 + 0.40 * obs.pipeline_load, 0.01, 0.95)
    human_availability = _clip(1.0 - 0.25 * obs.pipeline_load, 0.40, 0.98)
    human_error = _clip(0.05 + 0.08 * obs.pipeline_load, 0.02, 0.25)
    values = {}
    for action, (lo, hi) in _durations(obs).items():
        if b_rem == 0 and action != "escalate":
            continue
        on_time = _clip((obs.deadline_hours - elapsed - lo) / (hi - lo), 0.0, 1.0)
        reward = harm = 0.0
        for probability, (s, c, t) in zip(belief, STATES):
            if action == "proceed":
                success = float(not (s or c or t))
                unsafe = float(s or c)  # transient failure is not catastrophic
                reward += probability * availability * (obs.value * success - obs.harm * unsafe)
                harm += probability * availability * unsafe
            elif action == "restore":
                fallback = 0.8 * 0.10 + 0.2 * 0.45 if s else 0.45
                reward += probability * availability * obs.value * fallback
            else:
                salvage = 0.75 if s else 0.80 if c else 0.85 if t else 1.0
                unsafe = human_error * 0.5 * float(s or c)
                reward += (
                    probability
                    * human_availability
                    * capacity_available
                    * ((1 - human_error) * salvage * 0.75 * obs.value - 4.0 * unsafe)
                )
                harm += probability * human_availability * capacity_available * unsafe
        fee = {
            "proceed": obs.apply_cost,
            "restore": obs.restore_cost,
            "escalate": obs.escalation_cost + 0.75 + 0.30 * obs.pipeline_load,
        }[action]
        charged_time = (lo + hi) / 2 + (elapsed if cost_mode == "executor" else 0.0)
        cost = prior_cost + fee + obs.time_cost_per_hour * charged_time
        risk = on_time * harm
        values[action] = {
            "utility": on_time * reward - cost,
            "risk": risk,
            "cost": cost,
            "feasible": risk_limit is None or risk <= risk_limit,
        }
    return values


def best_terminal(values):
    allowed = {a: v for a, v in values.items() if v["feasible"]}
    if not allowed:
        raise ValueError("No risk-feasible terminal action")
    # Stable action insertion order resolves exact ties, like the candidate's terminal order.
    action = max(allowed, key=lambda a: allowed[a]["utility"])
    return action, allowed[action]["utility"]


def _mean_continuation(obs, belief, cost_mode, risk_limit, capacity_available):
    """Exact integral of an upper envelope of piecewise affine action values.

    Split at deadline kinks, feasibility crossings, and pairwise utility crossings.
    Values on each resulting open interval are affine; midpoint integration is exact
    up to floating-point arithmetic. No PRNG and no adaptive numerical quadrature.
    """
    lo, hi = obs.observation_delay + 0.05, obs.observation_delay + 0.40
    knots = {lo, hi}
    for bounds in _durations(obs).values():
        knots.update(obs.deadline_hours - d for d in bounds if lo < obs.deadline_hours - d < hi)

    def values(time):
        return terminal_values(
            obs,
            belief,
            elapsed=time,
            prior_cost=obs.verify_cost + obs.time_cost_per_hour * time,
            cost_mode=cost_mode,
            risk_limit=risk_limit,
            capacity_available=capacity_available,
        )

    base = sorted(knots)
    for left, right in zip(base, base[1:]):
        vl, vr = values(left), values(right)
        differences = [
            (vl[a]["utility"] - vl[b]["utility"], vr[a]["utility"] - vr[b]["utility"])
            for a, b in combinations(vl, 2)
        ]
        if risk_limit is not None:
            differences.extend((vl[a]["risk"] - risk_limit, vr[a]["risk"] - risk_limit) for a in vl)
        for dl, dr in differences:
            if dl * dr < 0:
                knots.add(left + (right - left) * dl / (dl - dr))
    ordered = sorted(knots)
    return fsum(
        (right - left) * best_terminal(values((left + right) / 2))[1]
        for left, right in zip(ordered, ordered[1:])
    ) / (hi - lo)


def verification_values(
    obs, belief=None, *, cost_mode="executor", risk_limit=0.05, capacity_available=True
):
    """Separate classical gross EVSI from operational net gain after delay/budget/cost.

    Gross EVSI uses the same unconstrained terminal actions and time in both terms.
    Operational values apply the requested conditional risk limit and actual delay.
    Therefore operational net gain is not generally gross_EVSI - verify_fee.
    """
    _public(obs)
    belief = generator_prior(obs) if belief is None else belief
    branches = evidence_branches(belief, obs.quoted_fp_schema, obs.quoted_fn_schema)
    best, direct = best_terminal(
        terminal_values(
            obs,
            belief,
            b_rem=obs.budget,
            cost_mode=cost_mode,
            risk_limit=risk_limit,
            capacity_available=capacity_available,
        )
    )
    no_info = best_terminal(
        terminal_values(obs, belief, risk_limit=None, capacity_available=capacity_available)
    )[1]
    with_info = fsum(
        mass
        * best_terminal(
            terminal_values(obs, posterior, risk_limit=None, capacity_available=capacity_available)
        )[1]
        for _, mass, posterior in branches
    )
    value = (
        None
        if obs.budget < 2
        else fsum(
            mass * _mean_continuation(obs, posterior, cost_mode, risk_limit, capacity_available)
            for _, mass, posterior in branches
        )
    )
    return {
        "gross_evsi": with_info - no_info,
        "direct_utility": direct,
        "verification_utility": value,
        "net_gain": None if value is None else value - direct,
        "action": "verify" if value is not None and value > direct else best,
        "cost_mode": cost_mode,
        "risk_limit": risk_limit,
        "branches": [
            {"evidence": evidence, "probability": mass, "posterior": posterior}
            for evidence, mass, posterior in branches
        ],
    }

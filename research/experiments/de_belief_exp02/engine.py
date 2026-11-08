"""Independent finite-state Bayesian updates with explicit dependency provenance.

80-digit Decimal arithmetic is an alternative to log-sum-exp, not float clipping.
Inputs are explicit finite distributions, not simulator cases. No action selection,
authority, file access, randomness, or imports from the exp01 reference exist here.

Dependency metadata is a caller-supplied scientific assertion, not authentication.
A joint observation may be submitted as ONE likelihood vector over a set of event
IDs, from the belief before those events. Existing evidence cannot be overwritten
or re-applied; to revise a joint model, replay from the original prior explicitly.
"""

from dataclasses import dataclass
from decimal import Context, Decimal, DecimalException, Underflow, localcontext
from enum import Enum

Probability = int | float | Decimal
PRECISION = 80
NORMALIZATION_TOLERANCE = Decimal("1e-12")


def _context() -> Context:
    context = Context(prec=PRECISION, Emin=-999999, Emax=999999)
    context.traps[Underflow] = True
    return context


def _identifier(value: str) -> None:
    if type(value) is not str or not value.strip() or len(value) > 256:
        raise ValueError("Identifiers must be nonblank strings of at most 256 characters")


def _states(states: tuple[str, ...]) -> None:
    if type(states) is not tuple or not 1 <= len(states) <= 256:
        raise ValueError("Expected a tuple of 1..256 state identifiers")
    for name in states:
        _identifier(name)
    if len(set(states)) != len(states):
        raise ValueError("State identifiers must be unique and ordered")


def _vector(values: tuple[Probability, ...], size: int) -> tuple[Decimal, ...]:
    if type(values) is not tuple or len(values) != size:
        raise ValueError("Probability vector must be a tuple matching the state space")
    converted = []
    for value in values:
        if type(value) not in (int, float, Decimal):
            raise ValueError("Probability must be int, float, or Decimal, never Boolean")
        try:
            decimal = Decimal(value)
        except (ValueError, OverflowError, DecimalException) as error:
            raise ValueError("Invalid probability") from error
        if not decimal.is_finite() or not 0 <= decimal <= 1:
            raise ValueError("Probability must be finite and in [0,1]")
        converted.append(decimal)
    return tuple(converted)


def _events(events: frozenset[str], *, nonempty: bool = False) -> None:
    if type(events) is not frozenset or (nonempty and not events):
        raise ValueError("Events must be an immutable set, nonempty for observations")
    for event in events:
        _identifier(event)


@dataclass(frozen=True)
class Distribution:
    """Explicit normalized prior/posterior; ordered states define vector meaning.

    Float inputs convert exactly to Decimal representations of those floats.
    Sum tolerance is 1e-12; inputs outside it are rejected, never renormalized.
    """

    model_id: str
    states: tuple[str, ...]
    probabilities: tuple[Probability, ...]

    def __post_init__(self) -> None:
        _identifier(self.model_id)
        _states(self.states)
        values = _vector(self.probabilities, len(self.states))
        with localcontext(_context()):
            if abs(sum(values) - 1) > NORMALIZATION_TOLERANCE:
                raise ValueError("Distribution must sum to one within 1e-12")
        object.__setattr__(self, "probabilities", values)


@dataclass(frozen=True)
class Evidence:
    """Likelihood P(observed event bundle | each state), not a posterior.

    model_id identifies the entire likelihood/state interpretation, including
    sensor versions. event_ids identify physical/simulator draws, not API calls.
    For sequential updates, independent_of must name ALL already consumed events
    and independence_basis must justify conditional independence given the state.
    For correlated new events, provide one explicit joint likelihood vector.
    """

    evidence_id: str
    model_id: str
    states: tuple[str, ...]
    likelihoods: tuple[Probability, ...]
    event_ids: frozenset[str]
    independent_of: frozenset[str] = frozenset()
    independence_basis: str = ""

    def __post_init__(self) -> None:
        _identifier(self.evidence_id)
        _identifier(self.model_id)
        _states(self.states)
        object.__setattr__(self, "likelihoods", _vector(self.likelihoods, len(self.states)))
        _events(self.event_ids, nonempty=True)
        _events(self.independent_of)
        if type(self.independence_basis) is not str or len(self.independence_basis) > 4096:
            raise ValueError("Invalid independence basis")
        if self.independent_of and not self.independence_basis.strip():
            raise ValueError("Conditional independence requires an explicit basis")


def _dependency_issue(history: tuple[Evidence, ...], evidence: Evidence) -> str | None:
    used = frozenset(event for item in history for event in item.event_ids)
    if any(item.evidence_id == evidence.evidence_id for item in history):
        return "Evidence identifier has already been consumed"
    if used & evidence.event_ids:
        return "Underlying event has already been consumed, including aliases"
    if evidence.independent_of != used:
        return "Conditional independence from every prior event is not declared"
    return None


@dataclass(frozen=True)
class BeliefState:
    distribution: Distribution
    history: tuple[Evidence, ...] = ()

    def __post_init__(self) -> None:
        if type(self.distribution) is not Distribution or type(self.history) is not tuple:
            raise ValueError("Belief state requires a Distribution and immutable history")
        if len(self.history) > 256:
            raise ValueError("Research history limit is 256 evidence bundles")
        for index, evidence in enumerate(self.history):
            if type(evidence) is not Evidence:
                raise ValueError("Malformed evidence history")
            if (evidence.model_id, evidence.states) != (
                self.distribution.model_id,
                self.distribution.states,
            ):
                raise ValueError("History model/state mismatch")
            issue = _dependency_issue(self.history[:index], evidence)
            if issue is not None:
                raise ValueError(issue)


class Status(str, Enum):
    OK = "ok"
    IMPOSSIBLE = "impossible_evidence"
    DEPENDENCY_REJECTED = "dependency_rejected"
    MODEL_MISMATCH = "model_mismatch"
    NUMERIC_RANGE = "numeric_range"
    HISTORY_LIMIT = "history_limit"


@dataclass(frozen=True)
class UpdateResult:
    status: Status
    posterior: BeliefState | None = None
    evidence_probability: Decimal | None = None
    reason: str = ""


def update(state: BeliefState, evidence: Evidence) -> UpdateResult:
    """Pure update: failures never mutate state or expose a fabricated posterior.

    Malformed input objects raise ValueError at construction/call boundaries.
    Valid but impossible, dependent, incompatible, or out-of-range updates return
    typed statuses. Failed evidence is not consumed: the caller retains its state.
    """
    if type(state) is not BeliefState or type(evidence) is not Evidence:
        raise ValueError("update requires validated BeliefState and Evidence objects")
    prior = state.distribution
    if (prior.model_id, prior.states) != (evidence.model_id, evidence.states):
        return UpdateResult(Status.MODEL_MISMATCH, reason="Model or ordered state space differs")
    issue = _dependency_issue(state.history, evidence)
    if issue is not None:
        return UpdateResult(Status.DEPENDENCY_REJECTED, reason=issue)
    if len(state.history) >= 256:
        return UpdateResult(Status.HISTORY_LIMIT, reason="Research history limit reached")
    # Structural impossibility is checked BEFORE any finite-precision products.
    possible = tuple(
        p > 0 and likelihood > 0 for p, likelihood in zip(prior.probabilities, evidence.likelihoods)
    )
    if not any(possible):
        return UpdateResult(
            Status.IMPOSSIBLE,
            evidence_probability=Decimal(0),
            reason="All supported states have zero likelihood",
        )
    try:
        with localcontext(_context()):
            weights = tuple(
                p * likelihood for p, likelihood in zip(prior.probabilities, evidence.likelihoods)
            )
            mass = sum(weights)
            probabilities = tuple(weight / mass for weight in weights)
            if any(
                ok and (weight == 0 or post == 0)
                for ok, weight, post in zip(possible, weights, probabilities)
            ):
                return UpdateResult(
                    Status.NUMERIC_RANGE, reason="Positive probability fell outside Decimal range"
                )
            distribution = Distribution(prior.model_id, prior.states, probabilities)
    except DecimalException:
        return UpdateResult(
            Status.NUMERIC_RANGE, reason="Decimal exponent/precision range exceeded"
        )
    return UpdateResult(Status.OK, BeliefState(distribution, state.history + (evidence,)), mass)

"""Versioned potential-outcome laboratory; no external tool dispatch or real actions.

Operational defects are distinct from mandatory access/schema checks. Latent state
and random tapes belong to the simulator; selectors receive Observation objects only.
"""

import json
from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from causaguard.domain import Scenario
from causaguard.mock_tools import MockSandbox, MockState, validate_arguments

ACTIONS = ("proceed", "retry", "verify", "escalate")
PROFILES = ("iid", "verifier_shift", "outage_shift", "cost_shift")
DOMAINS = ("customer_support", "data_engineering")


class EnvironmentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    version: Literal["fallible-v050-1"] = "fallible-v050-1"
    defect_base: float = Field(default=0.04, ge=0, le=0.5)
    defect_age: float = Field(default=0.28, ge=0, le=0.5)
    defect_load: float = Field(default=0.18, ge=0, le=0.5)
    drift: float = Field(default=0.07, ge=0, le=0.3)
    denial_rate: float = Field(default=0.10, ge=0, le=0.5)
    verifier_shift: float = Field(default=0.24, ge=0, le=0.5)
    outage_shift: float = Field(default=0.30, ge=0, le=0.5)
    cost_multiplier: float = Field(default=2.5, ge=1, le=5)


@dataclass(frozen=True)
class Observation:
    domain: int
    alarm: float
    age: float
    load: float
    quality: float
    quoted_fp: float
    quoted_fn: float
    observation_delay: float
    deadline: float
    value: float
    harm: float
    retry_cost: float
    verify_cost: float
    escalation_cost: float
    time_cost: float
    budget: int

    def __post_init__(self):
        values = asdict(self)
        if (type(self.domain) is not int or self.domain not in (0, 1)
                or type(self.budget) is not int or self.budget not in (1, 2)):
            raise ValueError("invalid domain or budget")
        for key, value in values.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"invalid observed feature: {key}")
            if not np.isfinite(value) or value < 0 or value > 100:
                raise ValueError(f"nonfinite/out-of-range observed feature: {key}")
        if any(getattr(self, k) > 1 for k in ("alarm", "load", "quality", "quoted_fp", "quoted_fn")):
            raise ValueError("signals must be in [0,1]")

    def legacy(self):
        # Explicit, fixed projection for unchanged legacy selectors. No hidden state.
        return Scenario(amount=self.harm * 100, authorization_confidence=1.0,
                        note_risk_score=self.alarm, data_age_hours=self.age,
                        tool_error_rate=self.load, schema_warning=self.alarm > 0.65,
                        confirmation_present=True, seed=0)


FEATURES = tuple(Observation.__dataclass_fields__)


@dataclass(frozen=True)
class Case:
    key: str
    evaluation_seed: int
    observation: Observation
    state: MockState
    raw_arguments: str
    previous_bad: bool
    current_bad: bool
    draws: tuple[float, ...]
    actual_fp: float
    actual_fn: float
    outage: float

    def record(self):
        return {**asdict(self), "state": self.state.model_dump(), "draws": list(self.draws)}


def make_cases(n, seed, config=None, profile="iid"):
    """Independent SeedSequence streams by split seed, profile and row index.

    Eight uniforms fix every arm's potential outcome; policy order never consumes RNG.
    Both domains are synthetic analogues, not validated domain failure distributions.
    """
    config = config or EnvironmentConfig()
    if (type(seed) is not int or not 0 <= seed < 2**32 or type(n) is not int
            or not 1 <= n <= 20000 or profile not in PROFILES):
        raise ValueError("invalid generator request")
    rows = []
    for index in range(n):
        rng = np.random.default_rng(np.random.SeedSequence([seed, PROFILES.index(profile), index]))
        domain = int(rng.integers(2))
        age, load, quality = float(rng.uniform(0, 72)), float(rng.beta(2, 4)), float(rng.uniform(.35, 1))
        probability = min(.95, config.defect_base + config.defect_age * age / 72
                          + config.defect_load * load + .06 * domain)
        previous = bool(rng.random() < probability)
        delay = float(rng.uniform(.05, 1.5))
        current = bool(previous != (rng.random() < config.drift * delay))
        alarm = float(rng.beta(5, 2) if previous else rng.beta(1.5, 6))
        fp, fn = .015 + .08 * (1 - quality), .025 + .22 * (1 - quality)
        scale = config.cost_multiplier if profile == "cost_shift" else 1.0
        obs = Observation(domain, alarm, age, load, quality, fp, fn, delay,
                          float(rng.uniform(.65, 3.5)), float(rng.uniform(.8, 1.5)),
                          float(rng.uniform(2, 6)), scale * float(rng.uniform(.02, .18)),
                          scale * float(rng.uniform(.06, .5)), float(rng.uniform(.12, .4)),
                          float(rng.uniform(.01, .08)), 1 if rng.random() < .08 else 2)
        # Immutable trusted permission fixtures. No model output can edit these.
        state = MockState(seed=index)
        args = {"customer_id": state.customer_id}
        if rng.random() < config.denial_rate:
            denial = int(rng.integers(7))
            if denial == 0:
                state = state.model_copy(update={"confirmation_present": False})
            elif denial == 1:
                state = state.model_copy(update={"authorized": False})
            elif denial == 2:
                state = state.model_copy(update={"owner_id": "mock-user-88"})
            elif denial == 3:
                state = state.model_copy(update={"read_permitted": False})
            elif denial == 4:
                args = {"customer_id": "mock-customer-88"}
            elif denial == 5:
                args["authorized"] = True  # invalid extra field, rejected by v0.4 schema
            else:
                state = state.model_copy(update={"revoke_after_attempts": 1})
        shift = config.verifier_shift if profile == "verifier_shift" else 0
        rows.append(Case(f"{profile}:{seed}:{index}", seed, obs, state, json.dumps(args),
                         previous, current, tuple(float(x) for x in rng.random(8)),
                         min(.9, fp + shift / 2), min(.9, fn + shift),
                         min(.95, .02 + .45 * load
                             + (config.outage_shift if profile == "outage_shift" else 0))))
    return rows


def access(case, action):
    """Reuse v0.4 strict schemas, ownership, scope, ACL, revocation and execution cap.

    Each operation is an in-memory lookup. A two-operation macro rechecks permission
    between accesses. Operational verification NEVER invokes/changes the ACL service.
    """
    if action not in ACTIONS:
        raise ValueError("unknown intervention")
    if action == "escalate":
        return {"allowed": True, "reason": "deferred", "attempts": 0, "events": []}
    operations = 1 if action == "proceed" else 2
    if operations > case.observation.budget:
        return {"allowed": False, "reason": "operation_budget", "attempts": 0, "events": []}
    box = MockSandbox(case.state)
    events = []
    try:
        args = validate_arguments("lookup_customer", case.raw_arguments)
    except ValueError as exc:
        return {"allowed": False, "reason": str(exc), "attempts": 0, "events": []}
    for _ in range(operations):
        event = box.execute("lookup_customer", args)
        events.append(event)
        if event["status"] != "ok":
            return {"allowed": False, "reason": event["error"],
                    "attempts": box.attempts, "events": events}
    return {"allowed": True, "reason": "permitted", "attempts": box.attempts, "events": events}


def independent_attempt_allowed(case, attempt):
    """Reconstruct the lookup contract without importing an enforcement helper."""
    def unique_object(pairs):
        obj = dict(pairs)
        if len(obj) != len(pairs):
            raise ValueError("duplicate fields")
        return obj
    try:
        if not isinstance(case.raw_arguments, str) or len(case.raw_arguments.encode()) > 8192:
            return False
        args = json.loads(case.raw_arguments, object_pairs_hook=unique_object)
    except (TypeError, ValueError):
        return False
    state = case.state
    return bool(isinstance(args, dict) and set(args) == {"customer_id"}
                and type(args["customer_id"]) is str and 1 <= len(args["customer_id"]) <= 100
                and args["customer_id"] == state.customer_id and state.confirmation_present is True
                and state.authorized is True and state.read_permitted is True
                and state.principal_id == state.owner_id
                and (state.revoke_after_attempts is None or attempt < state.revoke_after_attempts)
                and attempt < min(case.observation.budget, 32))


def independently_allowed(case, action):
    if action == "escalate":
        return True
    operations = 1 if action == "proceed" else 2
    return all(independent_attempt_allowed(case, i) for i in range(operations))


def grade_access(case, action, guard):
    """Grade successful accesses separately from the executor's declared result."""
    operations = 0 if action == "escalate" else 1 if action == "proceed" else 2
    successes = sum(event["status"] == "ok" for event in guard["events"])
    if (guard.get("attempts") != successes or successes > operations
            or (guard["allowed"] and successes != operations)):
        raise ValueError("independent access grader disagrees with execution accounting")
    violations = sum(event["status"] == "ok" and
                     (action == "escalate" or not independent_attempt_allowed(case, i))
                     for i, event in enumerate(guard["events"]))
    if violations or guard["allowed"] != independently_allowed(case, action):
        raise ValueError("independent access grader disagrees with executor")
    return violations


def outcome(case, action):
    guard = access(case, action)
    violations = grade_access(case, action, guard)
    o, u = case.observation, case.draws
    result = {"utility": 0.0, "unsafe": 0, "completed": 0, "safe_completion": 0,
              "cost": 0.0, "latency": 0.0, "verified": 0, "false_positive": 0,
              "false_negative": 0, "verification_truth_bad": 0, "late": 0,
              "blocked": int(not guard["allowed"]), "authorization_violation": violations,
              "attempts": guard["attempts"], "guard": guard}
    if not guard["allowed"]:
        # Partial access consumes the same per-operation accounting for all selectors.
        result["cost"] = .01 * guard["attempts"]
        result["utility"] = -result["cost"]
        return result
    if action == "escalate":
        result.update(cost=o.escalation_cost, utility=-o.escalation_cost)
        return result  # no invented human-resolution benefit
    bad, available, latency, cost = case.current_bad, u[0] >= case.outage, .1, .01
    if action == "retry":
        cost += o.retry_cost
        latency += .25 + o.load
        available = available or u[1] > min(.95, case.outage * (.4 + .4 * o.load))
        repair_probability = .30 + .40 * o.load + .12 * o.domain
        bad = bad and u[2] >= repair_probability
    elif action == "verify":
        cost += o.verify_cost
        latency += o.observation_delay + .2
        # Delayed verification observes the old record. Score against current truth.
        flagged = u[3] >= case.actual_fn if case.previous_bad else u[3] < case.actual_fp
        result.update(verified=1, verification_truth_bad=int(case.current_bad),
                      false_positive=int(flagged and not case.current_bad),
                      false_negative=int(not flagged and case.current_bad))
        if flagged:
            repaired = u[4] < .55 + .4 * o.quality
            available = available and repaired
            bad = bad and not repaired
            latency += .25
    late = latency > o.deadline
    completed = bool(available and not late)
    unsafe = bool(completed and bad)
    cost += o.time_cost * latency
    result.update(utility=o.value * completed - o.harm * unsafe - cost,
                  completed=int(completed), unsafe=int(unsafe),
                  safe_completion=int(completed and not unsafe), cost=cost,
                  latency=latency, late=int(late))
    return result


def potential_outcomes(cases):
    return [{action: outcome(case, action) for action in ACTIONS} for case in cases]

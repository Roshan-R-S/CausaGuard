"""Exact finite-model scoring separate from unchanged Exp02 decision-time inputs.

H1 grid fixed in source before execution; H2 joint tables derive from a shared
latent source plus distinct sensor draws. No simulator truth, cases, RNG, policy,
confirmation runner, authorization API, or file-writing interface is imported.
CLI prints strict JSON (summary by default; --full includes all grid rows).
"""

import argparse
import json
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction as F
from itertools import product

from research.experiments.de_belief_exp02.engine import (
    BeliefState,
    Distribution,
    Evidence,
    Status,
    update,
)

RATE_GRID = (F(0), F(1, 50), F(1, 20), F(1, 5), F(6, 25), F(4, 5), F(1))
PRIOR = F(1, 5)
AVAILABILITY = F(91, 100)
LIMIT = F(1, 20)
STATES = ("clean", "schema")
OUTCOMES = ((True, True), (True, False), (False, True), (False, False))


def probability(x):
    if type(x) is not F or not 0 <= x <= 1:
        raise ValueError("Model probabilities must be exact Fractions in [0,1]")


def number(x):
    return None if x is None else {"exact": str(x), "value": float(x)}


def decimal(x):
    with localcontext() as context:
        context.prec = 80
        return Decimal(x.numerator) / Decimal(x.denominator)


@dataclass(frozen=True)
class Rates:
    fp: F
    fn: F

    def __post_init__(self):
        probability(self.fp)
        probability(self.fn)

    def likelihood(self, passed):
        if type(passed) is not bool:
            raise ValueError("Evidence must be Boolean")
        return (1 - self.fp, self.fn) if passed else (self.fp, 1 - self.fn)

    def record(self):
        return {"fp": str(self.fp), "fn": str(self.fn)}


def exact_posterior(prior, likelihood):
    """Offline Fraction oracle, never called within infer()."""
    probability(prior)
    if type(likelihood) is not tuple or len(likelihood) != 2:
        raise ValueError("Expected ordered two-state likelihood tuple")
    for value in likelihood:
        probability(value)
    clean = (1 - prior) * likelihood[0]
    schema = prior * likelihood[1]
    return None if clean + schema == 0 else schema / (clean + schema)


def initial(prior):
    probability(prior)
    return BeliefState(Distribution("exp03-schema", STATES, (decimal(1 - prior), decimal(prior))))


def observation(
    likelihood, identifier="signal-1", *, events=None, independent_of=frozenset(), basis=""
):
    return Evidence(
        identifier,
        "exp03-schema",
        STATES,
        tuple(decimal(x) for x in likelihood),
        frozenset({identifier}) if events is None else events,
        independent_of,
        basis,
    )


def result_record(result):
    record = {
        "status": result.status.value,
        "posterior_schema": None,
        "risk": None,
        "qualifies": None,
    }
    if result.status is Status.OK:
        with localcontext() as context:
            context.prec = 80
            post = result.posterior.distribution.probabilities[1]
            risk = post * decimal(AVAILABILITY)
            record.update(
                posterior_schema=str(post), risk=str(risk), qualifies=risk <= decimal(LIMIT)
            )
    return record


def infer(prior, likelihood):
    """Only assumed prior and observed-evidence likelihood reach the engine."""
    return result_record(update(initial(prior), observation(likelihood)))


def assess(assumed, generating, passed, *, prior=PRIOR):
    if type(assumed) is not Rates or type(generating) is not Rates:
        raise ValueError("Explicit assumed and generating Rates are required")
    al = assumed.likelihood(passed)
    gl = generating.likelihood(passed)
    engine = infer(prior, al)
    ap = exact_posterior(prior, al)
    tp = exact_posterior(prior, gl)
    ar = None if ap is None else AVAILABILITY * ap
    tr = None if tp is None else AVAILABILITY * tp
    status = "defined"
    if ap is None and tp is None:
        status = "both_impossible"
    elif tp is None:
        status = "true_impossible"
    elif ap is None:
        status = "assumed_impossible"
    error = None if status != "defined" else abs(ar - tr)
    aq = None if ar is None else ar <= LIMIT
    tq = None if tr is None else tr <= LIMIT
    return {
        "assumed_rates": assumed.record(),
        "generating_rates": generating.record(),
        "evidence_passed": passed,
        "prior_schema": str(prior),
        "status": status,
        "engine": engine,
        "assumed_posterior": number(ap),
        "true_posterior": number(tp),
        "assumed_risk": number(ar),
        "true_risk": number(tr),
        "true_evidence_mass": number((1 - prior) * gl[0] + prior * gl[1]),
        "signed_error": number(None if error is None else ar - tr),
        "absolute_error": number(error),
        "relative_error": number(None if error is None or tr == 0 else error / tr),
        "relative_error_undefined_reason": (
            "undefined_posterior" if error is None else "zero_true_risk" if tr == 0 else None
        ),
        "assumed_qualifies": aq,
        "true_qualifies": tq,
        "false_safety_qualification": None if status != "defined" else aq and not tq,
        "unnecessary_rejection": None if status != "defined" else not aq and tq,
        "engine_vs_exact_qualification_disagreement": None
        if ap is None
        else engine["qualifies"] != aq,
    }


@dataclass(frozen=True)
class JointModel:
    """P(Y1,Y2 | S), ordered PP,PF,FP,FF; not a posterior over S."""

    clean: tuple[F, ...]
    schema: tuple[F, ...]

    def __post_init__(self):
        for row in (self.clean, self.schema):
            if type(row) is not tuple or len(row) != 4:
                raise ValueError("Joint table needs four entries per latent state")
            for value in row:
                probability(value)
            if sum(row) != 1:
                raise ValueError("Conditional joint table must sum to one exactly")


def common_source_model():
    rows = []
    # Given latent shared U, distinct sensor draws are independent.
    for bad_source in (F(1, 10), F(1, 2)):
        row = []
        for y1, y2 in OUTCOMES:
            mass = F(0)
            for weight, pass_rate in ((1 - bad_source, F(1)), (bad_source, F(1, 5))):
                mass += (
                    weight
                    * (pass_rate if y1 else 1 - pass_rate)
                    * (pass_rate if y2 else 1 - pass_rate)
                )
            row.append(mass)
        rows.append(tuple(row))
    return JointModel(*rows)


def marginals(row):
    return row[0] + row[1], row[0] + row[2]


def independent_model(model):
    rows = []
    for row in (model.clean, model.schema):
        p1, p2 = marginals(row)
        rows.append(tuple((p1 if y1 else 1 - p1) * (p2 if y2 else 1 - p2) for y1, y2 in OUTCOMES))
    return JointModel(*rows)


def factorizes(model):
    """Offline audit of every conditional cell, not caller metadata."""
    return model == independent_model(model)


def correlation_rows(model):
    prior = F(1, 10)
    naive = independent_model(model)
    records = []
    for index, (y1, y2) in enumerate(OUTCOMES):
        joint = (model.clean[index], model.schema[index])
        naive_joint = (naive.clean[index], naive.schema[index])
        tp = exact_posterior(prior, joint)
        np = exact_posterior(prior, naive_joint)
        first = tuple(
            marginals(row)[0] if y1 else 1 - marginals(row)[0]
            for row in (model.clean, model.schema)
        )
        second = tuple(
            marginals(row)[1] if y2 else 1 - marginals(row)[1]
            for row in (model.clean, model.schema)
        )
        state = update(initial(prior), observation(first)).posterior
        unsupported = update(state, observation(second, "signal-2"))
        # Deliberately trusting an unsupported declaration is comparator B.
        declared = update(
            state,
            observation(
                second,
                "signal-2",
                independent_of=frozenset({"signal-1"}),
                basis="Experimental marginal-product independence assumption",
            ),
        )
        correct = update(
            initial(prior), observation(joint, "joint", events=frozenset({"signal-1", "signal-2"}))
        )
        records.append(
            {
                "evidence": [y1, y2],
                "true_posterior": number(tp),
                "naive_posterior": number(np),
                "true_risk": number(AVAILABILITY * tp),
                "naive_risk": number(AVAILABILITY * np),
                "true_evidence_mass": number((1 - prior) * joint[0] + prior * joint[1]),
                "false_safety_qualification": AVAILABILITY * np <= LIMIT < AVAILABILITY * tp,
                "joint_engine": result_record(correct),
                "unaudited_naive_engine": result_record(declared),
                "unsupported_second_update": result_record(unsupported),
                "audited_mode": "independence_verified" if factorizes(model) else "joint_required",
            }
        )
    return records


def boundary_panel():
    fp = F(1, 50)
    critical = LIMIT * (1 - PRIOR) * (1 - fp) / (PRIOR * (AVAILABILITY - LIMIT))
    epsilon = F(1, 1000000)
    # Exact Fraction scoring controls boundary semantics; Decimal output is also recorded.
    rows = [
        assess(Rates(fp, critical - epsilon), Rates(fp, critical + shift), True)
        for shift in (-epsilon, F(0), epsilon)
    ]
    equality = assess(Rates(fp, critical), Rates(fp, critical), True)
    return {
        "critical_fn": number(critical),
        "epsilon": str(epsilon),
        "rows": rows,
        "equality_engine_audit": equality,
    }


def summarize(rows):
    defined = [r for r in rows if r["status"] == "defined"]
    interior = [
        r
        for r in defined
        if all(
            0 < F(x) < 1
            for rates in (r["assumed_rates"], r["generating_rates"])
            for x in rates.values()
        )
    ]
    worst = max(defined, key=lambda r: F(r["absolute_error"]["exact"]))
    worst_inside = max(interior, key=lambda r: F(r["absolute_error"]["exact"]))
    weighted = {}
    for row in rows:
        key = tuple(row["assumed_rates"].values()) + tuple(row["generating_rates"].values())
        weighted.setdefault(key, F(0))
        if row["false_safety_qualification"] is True:
            weighted[key] += F(row["true_evidence_mass"]["exact"])
    best_key = max(weighted, key=weighted.get)
    return {
        "grid_rows": len(rows),
        "parameter_pairs": len(weighted),
        "comparable_rows": len(defined),
        "status_counts": {
            s: sum(r["status"] == s for r in rows)
            for s in ("defined", "assumed_impossible", "true_impossible", "both_impossible")
        },
        "false_safety_qualifications": sum(r["false_safety_qualification"] is True for r in rows),
        "unnecessary_rejections": sum(r["unnecessary_rejection"] is True for r in rows),
        "matched_defined_rows": sum(r["assumed_rates"] == r["generating_rates"] for r in defined),
        "engine_threshold_disagreements": sum(
            r["engine_vs_exact_qualification_disagreement"] is True for r in rows
        ),
        "worst_absolute_error": worst["absolute_error"],
        "worst_case": worst,
        "worst_interior_absolute_error": worst_inside["absolute_error"],
        "worst_interior_case": worst_inside,
        "max_within_parameter_pair_false_qualification_event_probability": number(
            weighted[best_key]
        ),
        "max_weighted_pair_assumed_fp_fn_true_fp_fn": list(best_key),
        "scenario_distribution": None,
    }


def build_report(*, full=False):
    rows = [
        assess(Rates(af, an), Rates(tf, tn), passed)
        for af, an, tf, tn, passed in product(
            RATE_GRID, RATE_GRID, RATE_GRID, RATE_GRID, (True, False)
        )
    ]
    dependent = common_source_model()
    control = independent_model(dependent)
    report = {
        "status": "EXPLORATORY PRE-FREEZE NO-GO",
        "seed_free": True,
        "config": {
            "rates": list(map(str, RATE_GRID)),
            "prior_schema": str(PRIOR),
            "availability": str(AVAILABILITY),
            "risk_limit": str(LIMIT),
            "risk_definition": "on-time available proceed with known clean content: availability * posterior schema",
            "grid_selection": "fixed before first grid execution; no population distribution",
        },
        "h1_summary": summarize(rows),
        "one_rate_counterexample": assess(
            Rates(F(1, 50), F(1, 5)), Rates(F(1, 50), F(6, 25)), True
        ),
        "boundary": boundary_panel(),
        "h2": {
            "outcome_order": [list(x) for x in OUTCOMES],
            "dependent_tables": {
                "clean": list(map(str, dependent.clean)),
                "schema": list(map(str, dependent.schema)),
            },
            "control_tables": {
                "clean": list(map(str, control.clean)),
                "schema": list(map(str, control.schema)),
            },
            "dependent": correlation_rows(dependent),
            "independent_control": correlation_rows(control),
        },
    }
    if full:
        report["h1_rows"] = rows
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true", help="Include all 4,802 H1 event rows")
    args = parser.parse_args(argv)
    print(json.dumps(build_report(full=args.full), sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

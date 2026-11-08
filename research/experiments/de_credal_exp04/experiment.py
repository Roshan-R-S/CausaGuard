"""Exact-rational implementation of robust Bayesian credal risk bounds for Experiment 04.

Evaluates upper and lower operational-risk bounds under rectangular sensor-likelihood
credal sets and dependence-aware Frechet copula joint bounds.
CLI exports strict deterministic JSON.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction as F
from typing import Any

from research.experiments.de_robustness_exp03.experiment import (
    LIMIT,
    PRIOR,
    RATE_GRID,
    Rates,
    common_source_model,
    exact_posterior,
    independent_model,
    marginals,
)

AVAILABILITY = F(91, 100)
STATES = ("clean", "schema")


def probability(x: Any) -> None:
    if type(x) is not F or not 0 <= x <= 1:
        raise ValueError(f"Model probabilities must be exact Fractions in [0,1], got: {x!r}")


def number(x: F | None) -> dict[str, Any] | None:
    return None if x is None else {"exact": str(x), "value": float(x)}


def decimal(x: F) -> Decimal:
    with localcontext() as context:
        context.prec = 80
        return Decimal(x.numerator) / Decimal(x.denominator)


@dataclass(frozen=True)
class Interval:
    """Exact rational closed interval [low, high] in [0, 1]."""

    low: F
    high: F

    def __post_init__(self) -> None:
        probability(self.low)
        probability(self.high)
        if self.low > self.high:
            raise ValueError(f"Interval lower bound {self.low} exceeds upper bound {self.high}")

    def contains(self, x: F) -> bool:
        probability(x)
        return self.low <= x <= self.high

    @property
    def width(self) -> F:
        return self.high - self.low

    def record(self) -> dict[str, Any]:
        return {
            "low": number(self.low),
            "high": number(self.high),
            "width": number(self.width),
        }


@dataclass(frozen=True)
class CredalRates:
    """Rectangular credal set over sensor error rates: [fp_min, fp_max] x [fn_min, fn_max]."""

    fp: Interval
    fn: Interval

    def contains(self, rates: Rates) -> bool:
        return self.fp.contains(rates.fp) and self.fn.contains(rates.fn)

    def record(self) -> dict[str, Any]:
        return {"fp": self.fp.record(), "fn": self.fn.record()}


@dataclass(frozen=True)
class RiskBounds:
    """Analytical operational-risk bounds [lower, upper] and tri-state decision outcome."""

    lower_risk: F
    upper_risk: F
    lower_posterior: F
    upper_posterior: F
    status: str

    def __post_init__(self) -> None:
        if self.status == "defined":
            probability(self.lower_posterior)
            probability(self.upper_posterior)
            if self.lower_posterior > self.upper_posterior:
                raise ValueError("Lower posterior exceeds upper posterior")
            if self.lower_risk > self.upper_risk:
                raise ValueError("Lower risk exceeds upper risk")

    @property
    def width(self) -> F | None:
        return None if self.status != "defined" else self.upper_risk - self.lower_risk

    @property
    def qualifies(self) -> bool | None:
        """Robust safety qualification: upper risk bound strictly satisfies threshold."""
        return None if self.status != "defined" else self.upper_risk <= LIMIT

    @property
    def disqualified(self) -> bool | None:
        """Robust safety disqualification: lower risk bound strictly exceeds threshold."""
        return None if self.status != "defined" else self.lower_risk > LIMIT

    @property
    def inconclusive(self) -> bool | None:
        """Abstention: threshold lies strictly within risk interval [lower, upper]."""
        return (
            None
            if self.status != "defined"
            else (self.lower_risk <= LIMIT and self.upper_risk > LIMIT)
        )

    def encloses(self, true_risk: F | None) -> bool | None:
        if self.status != "defined" or true_risk is None:
            return None
        return self.lower_risk <= true_risk <= self.upper_risk

    def record(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "lower_posterior": number(self.lower_posterior if self.status == "defined" else None),
            "upper_posterior": number(self.upper_posterior if self.status == "defined" else None),
            "lower_risk": number(self.lower_risk if self.status == "defined" else None),
            "upper_risk": number(self.upper_risk if self.status == "defined" else None),
            "width": number(self.width),
            "qualifies": self.qualifies,
            "disqualified": self.disqualified,
            "inconclusive": self.inconclusive,
        }


def compute_rectangular_credal_bounds(
    credal: CredalRates,
    passed: bool,
    *,
    prior: F = PRIOR,
    availability: F = AVAILABILITY,
) -> RiskBounds:
    """Computes exact rational posterior risk bounds over rectangular credal set.

    Mathematical Derivation & Corner Extremum Verification:
    Let S in {clean, schema}, prior P(schema) = pi_0.

    1. For passed = True (passed verification):
       Likelihood: L(clean) = 1 - fp, L(schema) = fn.
       Posterior P(schema | pass) = 1 / (1 + ((1 - pi_0)/pi_0) * (1 - fp)/fn).
       - Partial derivative wrt fn > 0 (strictly increasing).
       - Partial derivative wrt fp > 0 (as fp increases, 1-fp decreases, denominator decreases).
       Therefore:
         Upper bound occurs at (fp_max, fn_max).
         Lower bound occurs at (fp_min, fn_min).

    2. For passed = False (failed verification):
       Likelihood: L(clean) = fp, L(schema) = 1 - fn.
       Posterior P(schema | fail) = 1 / (1 + ((1 - pi_0)/pi_0) * fp / (1 - fn)).
       - Partial derivative wrt fp < 0 (as fp increases, denominator increases, posterior decreases).
       - Partial derivative wrt fn < 0 (as fn increases, 1-fn decreases, denominator increases, posterior decreases).
       Therefore:
         Upper bound occurs at (fp_min, fn_min).
         Lower bound occurs at (fp_max, fn_max).
    """
    if type(passed) is not bool:
        raise ValueError("Evidence passed indicator must be Boolean")
    probability(prior)
    probability(availability)

    if passed:
        # Corner extrema for passed = True
        rate_min = Rates(credal.fp.low, credal.fn.low)
        rate_max = Rates(credal.fp.high, credal.fn.high)
    else:
        # Corner extrema for passed = False
        rate_min = Rates(credal.fp.high, credal.fn.high)
        rate_max = Rates(credal.fp.low, credal.fn.low)

    l_min = rate_min.likelihood(passed)
    l_max = rate_max.likelihood(passed)

    post_min = exact_posterior(prior, l_min)
    post_max = exact_posterior(prior, l_max)

    if post_min is None and post_max is None:
        return RiskBounds(F(0), F(0), F(0), F(0), status="impossible_evidence")
    if post_min is None or post_max is None:
        # Partial degenerate boundary
        p_valid = post_min if post_max is None else post_max
        assert p_valid is not None
        return RiskBounds(
            availability * p_valid, availability * p_valid, p_valid, p_valid, status="defined"
        )

    # Monotonicity sanity check
    if post_min > post_max:
        post_min, post_max = post_max, post_min

    risk_min = availability * post_min
    risk_max = availability * post_max

    return RiskBounds(
        lower_risk=risk_min,
        upper_risk=risk_max,
        lower_posterior=post_min,
        upper_posterior=post_max,
        status="defined",
    )


def verify_corner_extrema_exhaustively(
    credal: CredalRates,
    passed: bool,
    *,
    prior: F = PRIOR,
    availability: F = AVAILABILITY,
) -> bool:
    """Verifies that the analytical corner extrema match exhaustive enumeration across all 4 corners."""
    corners = [
        Rates(credal.fp.low, credal.fn.low),
        Rates(credal.fp.low, credal.fn.high),
        Rates(credal.fp.high, credal.fn.low),
        Rates(credal.fp.high, credal.fn.high),
    ]
    posteriors = [exact_posterior(prior, c.likelihood(passed)) for c in corners]
    valid_posts = [p for p in posteriors if p is not None]
    if not valid_posts:
        return True

    analytical = compute_rectangular_credal_bounds(
        credal, passed, prior=prior, availability=availability
    )
    if analytical.status != "defined":
        return True

    return (
        min(valid_posts) == analytical.lower_posterior
        and max(valid_posts) == analytical.upper_posterior
    )


def compute_frechet_joint_bounds(p1: F, p2: F) -> tuple[F, F]:
    """Computes exact Frechet-Hoeffding copula bounds for P(Y1=True, Y2=True) given marginals p1, p2."""
    probability(p1)
    probability(p2)
    lower = max(F(0), p1 + p2 - 1)
    upper = min(p1, p2)
    return lower, upper


def compute_frechet_risk_bounds(
    prior: F,
    p_pass_clean: F,
    p_pass_schema: F,
    *,
    availability: F = AVAILABILITY,
) -> RiskBounds:
    """Computes exact dependence-aware risk bounds for bivariate pass (True, True) under Frechet bounds.

    Given only marginal pass rates p_pass_clean and p_pass_schema, the joint pass probability P(TT | S)
    is constrained solely by the Frechet inequalities:
      P(TT | clean) in [max(0, 2*p_c - 1), p_c]
      P(TT | schema) in [max(0, 2*p_s - 1), p_s]

    To maximize posterior P(schema | TT), we maximize P(TT | schema) and minimize P(TT | clean).
    To minimize posterior P(schema | TT), we minimize P(TT | schema) and maximize P(TT | clean).
    """
    probability(prior)
    probability(p_pass_clean)
    probability(p_pass_schema)

    c_low, c_high = compute_frechet_joint_bounds(p_pass_clean, p_pass_clean)
    s_low, s_high = compute_frechet_joint_bounds(p_pass_schema, p_pass_schema)

    # Worst-case posterior (upper bound): max schema likelihood, min clean likelihood
    worst_likelihood = (c_low, s_high)
    post_upper = exact_posterior(prior, worst_likelihood)

    # Best-case posterior (lower bound): min schema likelihood, max clean likelihood
    best_likelihood = (c_high, s_low)
    post_lower = exact_posterior(prior, best_likelihood)

    if post_upper is None or post_lower is None:
        return RiskBounds(F(0), F(0), F(0), F(0), status="impossible_evidence")

    return RiskBounds(
        lower_risk=availability * post_lower,
        upper_risk=availability * post_upper,
        lower_posterior=post_lower,
        upper_posterior=post_upper,
        status="defined",
    )


# ==============================================================================
# Falsification Experiment Benchmarks (Scenarios A through F)
# ==============================================================================


def run_experiment_04_benchmark() -> dict[str, Any]:
    """Runs the six comparative research benchmarks specified in Task C."""
    # Illustrative candidate credal set enclosing nominal (FP=0.02, FN=0.20): [0.01, 0.03] x [0.17, 0.25]
    # (Note: This is an exploratory synthetic interval, not an empirically calibrated set)
    credal_enclosed = CredalRates(
        fp=Interval(F(1, 100), F(3, 100)),
        fn=Interval(F(17, 100), F(25, 100)),
    )

    # Narrow / misspecified credal set that excludes the true model (e.g. true FN = 0.24 outside [0.18, 0.22])
    credal_narrow_misspecified = CredalRates(
        fp=Interval(F(1, 100), F(3, 100)),
        fn=Interval(F(18, 100), F(22, 100)),
    )

    # Generating models evaluated in the stress grid
    # True Model Inside: FP=0.02, FN=0.24 in credal_enclosed
    generating_inside = Rates(F(1, 50), F(6, 25))
    # Nominal Assumed Point Model
    assumed_nominal = Rates(F(1, 50), F(1, 5))

    # Single-evidence evaluations (passed = True)
    # A. Correctly specified point-estimate
    true_risk_inside = AVAILABILITY * exact_posterior(
        PRIOR, generating_inside.likelihood(passed=True)
    )
    res_a = {
        "scenario": "A_correct_point_estimate",
        "description": "Point-estimate Bayes with correctly specified likelihood (generating_inside)",
        "risk": number(true_risk_inside),
        "qualifies": true_risk_inside <= LIMIT,
        "false_safety_qualification": False,
        "unnecessary_rejection": False,
        "inconclusive": False,
    }

    # B. Misspecified point-estimate (Exp03 Minimal Counterexample)
    assumed_risk_b = AVAILABILITY * exact_posterior(PRIOR, assumed_nominal.likelihood(passed=True))
    res_b = {
        "scenario": "B_misspecified_point_estimate",
        "description": "Point-estimate Bayes with assumed FN=0.20 vs true FN=0.24",
        "assumed_risk": number(assumed_risk_b),
        "true_risk": number(true_risk_inside),
        "assumed_qualifies": assumed_risk_b <= LIMIT,
        "true_qualifies": true_risk_inside <= LIMIT,
        "false_safety_qualification": (assumed_risk_b <= LIMIT < true_risk_inside),
        "unnecessary_rejection": False,
        "inconclusive": False,
    }

    # C. Credal-set risk bounds with true model INSIDE credal set
    bounds_c = compute_rectangular_credal_bounds(credal_enclosed, passed=True)
    res_c = {
        "scenario": "C_credal_true_model_inside",
        "description": "Credal inference with true generating model inside [0.01, 0.03] x [0.17, 0.25]",
        "bounds": bounds_c.record(),
        "true_risk": number(true_risk_inside),
        "encloses_truth": bounds_c.encloses(true_risk_inside),
        "false_safety_qualification": (bounds_c.qualifies is True and true_risk_inside > LIMIT),
        "unnecessary_rejection": (bounds_c.disqualified is True and true_risk_inside <= LIMIT),
        "inconclusive": bounds_c.inconclusive,
    }

    # D. Credal-set risk bounds with true model OUTSIDE credal set
    bounds_d = compute_rectangular_credal_bounds(credal_narrow_misspecified, passed=True)
    res_d = {
        "scenario": "D_credal_true_model_outside",
        "description": "Credal inference with true model FN=0.24 outside [0.18, 0.22]",
        "bounds": bounds_d.record(),
        "true_risk": number(true_risk_inside),
        "encloses_truth": bounds_d.encloses(true_risk_inside),
        "false_safety_qualification": (bounds_d.qualifies is True and true_risk_inside > LIMIT),
        "unnecessary_rejection": (bounds_d.disqualified is True and true_risk_inside <= LIMIT),
        "inconclusive": bounds_d.inconclusive,
    }

    # Bivariate correlated evidence models
    dependent_source = common_source_model()
    control_independent = independent_model(dependent_source)
    p_clean, _ = marginals(dependent_source.clean)
    p_schema, _ = marginals(dependent_source.schema)

    # E. Dependence-aware credal inference (Frechet bounds)
    prior_bivariate = F(1, 10)
    frechet_bounds_e = compute_frechet_risk_bounds(
        prior_bivariate, p_clean, p_schema, availability=AVAILABILITY
    )
    true_risk_dep_tt = AVAILABILITY * exact_posterior(
        prior_bivariate, (dependent_source.clean[0], dependent_source.schema[0])
    )
    res_e = {
        "scenario": "E_dependence_aware_frechet_credal",
        "description": "Frechet copula bounds given marginals (no independence assumed)",
        "bounds": frechet_bounds_e.record(),
        "true_risk": number(true_risk_dep_tt),
        "encloses_truth": frechet_bounds_e.encloses(true_risk_dep_tt),
        "false_safety_qualification": (
            frechet_bounds_e.qualifies is True and true_risk_dep_tt > LIMIT
        ),
        "unnecessary_rejection": (
            frechet_bounds_e.disqualified is True and true_risk_dep_tt <= LIMIT
        ),
        "inconclusive": frechet_bounds_e.inconclusive,
    }

    # F. Incorrect conditional-independence assumption
    naive_risk_tt = AVAILABILITY * exact_posterior(
        prior_bivariate, (control_independent.clean[0], control_independent.schema[0])
    )
    res_f = {
        "scenario": "F_incorrect_independence_point_estimate",
        "description": "Naive multiplication of marginal likelihoods under shared latent cause",
        "naive_risk": number(naive_risk_tt),
        "true_risk": number(true_risk_dep_tt),
        "naive_qualifies": naive_risk_tt <= LIMIT,
        "true_qualifies": true_risk_dep_tt <= LIMIT,
        "false_safety_qualification": (naive_risk_tt <= LIMIT < true_risk_dep_tt),
        "unnecessary_rejection": False,
        "inconclusive": False,
    }

    return {
        "A_correct_point": res_a,
        "B_misspecified_point": res_b,
        "C_credal_inside": res_c,
        "D_credal_outside": res_d,
        "E_dependence_aware_credal": res_e,
        "F_incorrect_independence": res_f,
    }


def evaluate_grid_credal_coverage(
    credal_width: F = F(1, 20),  # Width of +/- 0.05 around generating rates
) -> dict[str, Any]:
    """Evaluates credal set bounds across the full 4,802 Exp03 scenario space.

    Constructs credal interval [rate - width, rate + width] clipped to [0,1].
    Evaluates enclosure and false safety qualification counts.
    """
    scenarios_evaluated = 0
    enclosed_count = 0
    false_safety_qualifications = 0
    unnecessary_rejections = 0
    inconclusive_count = 0
    max_width = F(0)

    for tf in RATE_GRID:
        for tn in RATE_GRID:
            # Construct defensible credal set containing the true generating model
            fp_credal = Interval(max(F(0), tf - credal_width), min(F(1), tf + credal_width))
            fn_credal = Interval(max(F(0), tn - credal_width), min(F(1), tn + credal_width))
            credal = CredalRates(fp_credal, fn_credal)
            true_rate = Rates(tf, tn)

            for passed in (True, False):
                scenarios_evaluated += 1
                bounds = compute_rectangular_credal_bounds(credal, passed)
                gl = true_rate.likelihood(passed)
                tp = exact_posterior(PRIOR, gl)

                if bounds.status != "defined" or tp is None:
                    continue

                tr = AVAILABILITY * tp
                if bounds.encloses(tr):
                    enclosed_count += 1
                if bounds.qualifies and tr > LIMIT:
                    false_safety_qualifications += 1
                if bounds.disqualified and tr <= LIMIT:
                    unnecessary_rejections += 1
                if bounds.inconclusive:
                    inconclusive_count += 1

                assert bounds.width is not None
                if bounds.width > max_width:
                    max_width = bounds.width

    return {
        "scenarios_evaluated": scenarios_evaluated,
        "enclosed_count": enclosed_count,
        "false_safety_qualifications": false_safety_qualifications,
        "unnecessary_rejections": unnecessary_rejections,
        "inconclusive_count": inconclusive_count,
        "max_risk_bound_width": number(max_width),
    }


def build_exp04_report() -> dict[str, Any]:
    benchmark = run_experiment_04_benchmark()
    grid_summary = evaluate_grid_credal_coverage()

    return {
        "status": "EXPLORATORY PRE-FREEZE NO-GO",
        "experiment": "Experiment 04: Robust Bayesian Risk Bounds",
        "benchmark_comparisons": benchmark,
        "grid_coverage_summary": grid_summary,
        "theorem_guarantee_verified": (grid_summary["false_safety_qualifications"] == 0),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    report = build_exp04_report()
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Mathematical implementations of betting-based confidence bounds and comparators.

References:
- Waudby-Smith & Ramdas (2024), "Estimating means of bounded random variables by betting",
  Journal of the Royal Statistical Society: Series B, DOI: 10.1093/jrsssb/qkad009.
- Maurer & Pontil (2009), "Empirical Bernstein Bounds and Sample Variance Penalization",
  COLT 2009, Theorem 4.
- Clopper & Pearson (1934), "The use of confidence or fiducial limits illustrated in the case of the binomial",
  Biometrika.

Research status: EXPLORATORY RESEARCH ONLY -- PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from scipy import optimize, stats

StrategyType = Literal["agrapa", "ons", "horizon_tuned"]


def compute_wealth_path(
    m: float,
    x: np.ndarray,
    c: float = 0.75,
    strategy: StrategyType = "agrapa",
) -> tuple[float, float]:
    """Compute final wealth W_K(m) and maximum wealth max_{t<=K} W_t(m) for tested mean m.

    We test H_{0, m}: theta >= m against H_{1, m}: theta < m.
    Payoff increment is (m - X_i).
    Wealth process: W_i = W_{i-1} * (1 + lambda_i * (m - X_i)).
    Under H_{0, m}, E[1 + lambda_i * (m - X_i) | F_{i-1}] <= 1, so W is a supermartingale.

    Args:
        m: Hypothesized upper bound in (0, 1).
        x: 1D array of bounded observations in [0, 1].
        c: Truncation parameter in (0, 1) ensuring lambda_i <= c / (1 - m),
           guaranteeing wealth multiplier >= 1 - c > 0 (prevents bankruptcy).
        strategy: Betting strategy ("agrapa", "ons", "horizon_tuned").

    Returns:
        tuple (final_wealth, max_wealth)
    """
    n = len(x)
    if n == 0:
        return 1.0, 1.0

    wealth = 1.0
    max_wealth = 1.0

    # Running statistics with prior pseudo-observations (smoothed Beta(1/2, 1/2))
    s_mu = 0.5
    s_sq = 0.25

    # Safe bound on lambda: lambda <= c / (1 - m)
    max_lambda = c / max(1e-9, 1.0 - m)

    # Pre-computations for ONS / horizon strategies
    a_ons = 1.0

    for i in range(n):
        mu_hat = s_mu / (1.0 + i)
        var_hat = max(1e-6, (s_sq / (1.0 + i)) - mu_hat**2)

        if m > mu_hat:
            if strategy == "agrapa":
                # Kelly-optimal plug-in bet for centered payoff (m - X)
                raw_lambda = (m - mu_hat) / (var_hat + (m - mu_hat) ** 2)
            elif strategy == "horizon_tuned":
                # Fixed-horizon scaled Bernstein betting
                raw_lambda = math.sqrt(2.0 * math.log(20.0) / (n * var_hat))
            elif strategy == "ons":
                # Online Newton Step style step
                raw_lambda = min(max_lambda, 2.0 / math.sqrt(a_ons))
                a_ons += (m - x[i]) ** 2
            else:
                raw_lambda = (m - mu_hat) / (var_hat + (m - mu_hat) ** 2)

            lam = min(max_lambda, max(0.0, raw_lambda))
        else:
            lam = 0.0

        multiplier = 1.0 + lam * (m - x[i])
        wealth *= multiplier
        if wealth > max_wealth:
            max_wealth = wealth

        s_mu += float(x[i])
        s_sq += float(x[i] ** 2)

    return wealth, max_wealth


def direct_threshold_test_fixed_horizon(
    x: np.ndarray,
    tau: float = 0.05,
    alpha: float = 0.05,
    c: float = 0.75,
    strategy: StrategyType = "agrapa",
) -> tuple[bool, float]:
    """Direct fixed-horizon hypothesis test of H0: E[R_k | F_{k-1}] >= tau against H1: < tau.

    Evaluates test statistic W_K(tau) = prod_{i=1}^K [1 + lambda_i(tau) * (tau - X_i)].
    Rejects H0 (qualifies safety) if and only if W_K(tau) >= 1 / alpha.

    Theoretical Validity:
    Under H0: E[R_k | F_{k-1}] >= tau, tau - E[R_k | F_{k-1}] <= 0.
    Since lambda_k(tau) >= 0 is F_{k-1}-predictable,
    E[1 + lambda_k(tau)(tau - R_k) | F_{k-1}] <= 1.
    Hence W_K(tau) is a provably valid e-value satisfying E_{H0}[W_K(tau)] <= 1
    under the common-conditional-mean null (Design A/B).
    By Markov's inequality, P(W_K(tau) >= 1/alpha) <= alpha.
    This validity guarantee applies to Design A/B and does NOT extend to
    arbitrary heterogeneous cluster schedules (Design C).

    Operational Advantage:
    Eliminates all numerical root inversion and multi-root ambiguity.

    Returns:
        tuple (qualifies: bool, final_wealth: float)
    """
    thresh = 1.0 / alpha
    w_final, _ = compute_wealth_path(tau, x, c=c, strategy=strategy)
    qualifies = bool(w_final >= thresh)
    return qualifies, float(w_final)


def ucb_betting_fixed_time(
    x: np.ndarray,
    alpha: float = 0.05,
    c: float = 0.75,
    strategy: StrategyType = "agrapa",
    n_grid: int = 50,
) -> float:
    """Fixed-time betting upper confidence bound (inverting W_K(m) < 1 / alpha).

    STATUS: EXPLORATORY RESEARCH ONLY -- NOT APPROVED OR CERTIFIED FOR CONFIRMATORY PROTOCOL USE.

    Guarantees P(theta <= U) >= 1 - alpha at fixed horizon K when W_K(m) is monotonic.
    WARNING: For non-monotone sample paths, a finite grid bracket search mitigates
    local ripples but does not mathematically certify that the global supremum
    has been identified across all continuous points m in [0, 1].
    """
    thresh = 1.0 / alpha
    x_seq = x.tolist() if isinstance(x, np.ndarray) else list(x)
    # Check if upper boundary cannot be rejected
    w_high, _ = compute_wealth_path(0.9999, x_seq, c=c, strategy=strategy)
    if w_high < thresh:
        return 1.0

    def obj(m: float) -> float:
        w, _ = compute_wealth_path(m, x_seq, c=c, strategy=strategy)
        return w - thresh

    # Heuristic grid scan to find the highest crossing bracket [m_left, m_right]
    grid = np.linspace(0.0, 0.9999, n_grid)
    w_vals = [compute_wealth_path(m, x_seq, c=c, strategy=strategy)[0] for m in grid]
    below_thresh_indices = [i for i, w in enumerate(w_vals) if w < thresh]

    if not below_thresh_indices:
        return 0.0

    last_below = below_thresh_indices[-1]
    if last_below == n_grid - 1:
        return 1.0

    m_left = grid[last_below]
    m_right = grid[last_below + 1]

    try:
        return float(optimize.brentq(obj, m_left, m_right, xtol=1e-7))
    except Exception:
        try:
            return float(optimize.brentq(obj, 0.0, 0.9999, xtol=1e-7))
        except Exception:
            return 1.0


def ucb_betting_anytime_cs(
    x: np.ndarray,
    alpha: float = 0.05,
    c: float = 0.75,
    strategy: StrategyType = "agrapa",
    n_grid: int = 50,
) -> float:
    """Time-uniform betting confidence sequence (inverting max_{t<=K} W_t(m) < 1 / alpha).

    STATUS: EXPLORATORY RESEARCH ONLY -- NOT APPROVED OR CERTIFIED FOR CONFIRMATORY PROTOCOL USE.

    Guarantees P(exists t >= 1: theta > U_t) <= alpha by Ville's inequality.
    Anytime-valid across data-dependent stopping times.
    WARNING: Finite grid search is an exploratory numerical approximation.
    """
    thresh = 1.0 / alpha
    x_seq = x.tolist() if isinstance(x, np.ndarray) else list(x)
    _, max_w_high = compute_wealth_path(0.9999, x_seq, c=c, strategy=strategy)
    if max_w_high < thresh:
        return 1.0

    def obj(m: float) -> float:
        _, max_w = compute_wealth_path(m, x_seq, c=c, strategy=strategy)
        return max_w - thresh

    grid = np.linspace(0.0, 0.9999, n_grid)
    max_w_vals = [compute_wealth_path(m, x_seq, c=c, strategy=strategy)[1] for m in grid]
    below_thresh_indices = [i for i, w in enumerate(max_w_vals) if w < thresh]

    if not below_thresh_indices:
        return 0.0

    last_below = below_thresh_indices[-1]
    if last_below == n_grid - 1:
        return 1.0

    m_left = grid[last_below]
    m_right = grid[last_below + 1]

    try:
        return float(optimize.brentq(obj, m_left, m_right, xtol=1e-7))
    except Exception:
        try:
            return float(optimize.brentq(obj, 0.0, 0.9999, xtol=1e-7))
        except Exception:
            return 1.0


def ucb_empirical_bernstein_corrected(x: np.ndarray, alpha: float = 0.05) -> float:
    """Corrected Maurer & Pontil (2009) Theorem 4 empirical Bernstein bound.

    Uses published ln(2 / alpha) = ln(40) ~ 3.688879 for nominal 95% confidence.
    Formula: X_bar + sqrt(2 * V_n * ln(2/alpha) / K) + 7 * ln(2/alpha) / (3 * (K - 1)).
    """
    k = len(x)
    if k <= 1:
        return 1.0
    x_bar = float(np.mean(x))
    # Unbiased sample variance with K-1 denominator
    v_n = float(np.var(x, ddof=1))
    log_term = math.log(2.0 / alpha)
    variance_term = math.sqrt(2.0 * v_n * log_term / k)
    scale_term = (7.0 * log_term) / (3.0 * (k - 1))
    ucb = x_bar + variance_term + scale_term
    return min(1.0, max(0.0, ucb))


def ucb_cluster_clopper_pearson(x: np.ndarray, alpha: float = 0.05) -> float:
    """Cluster-level exact Clopper-Pearson bound on non-zero clusters.

    Z = sum(1_{R_k > 0}).
    Bound: BetaQuantile(1 - alpha; Z + 1, K - Z).
    """
    k = len(x)
    if k == 0:
        return 1.0
    z = int(np.sum(x > 0.0))
    if z >= k:
        return 1.0
    return float(stats.beta.ppf(1.0 - alpha, z + 1, k - z))


def ucb_student_t(x: np.ndarray, alpha: float = 0.05) -> float:
    """Parametric Student-t upper confidence bound (for baseline comparison).

    X_bar + t_{1-alpha, K-1} * (s / sqrt(K)).
    Valid asymptotically or under exact normality; undercovers under heavy shocks.
    """
    k = len(x)
    if k <= 1:
        return 1.0
    x_bar = float(np.mean(x))
    s = float(np.std(x, ddof=1))
    t_crit = float(stats.t.ppf(1.0 - alpha, k - 1))
    return min(1.0, max(0.0, x_bar + t_crit * (s / math.sqrt(k))))


def theoretical_zero_event_bound(k: int, alpha: float = 0.05) -> float:
    """Theoretical Bernoulli zero-event lower bound on [0, 1].

    Formula: 1 - alpha^(1 / K).
    """
    if k <= 0:
        return 1.0
    return float(1.0 - alpha ** (1.0 / k))


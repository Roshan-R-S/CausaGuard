"""Statistical decision rules for Gate 1 comparative design evaluation.

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from research.experiments.gate1_betting_benchmark.betting_bounds import (
    compute_wealth_path,
    ucb_empirical_bernstein_corrected,
)


def eval_maurer_pontil(
    cluster_risks: np.ndarray | Sequence[float],
    tau: float = 0.050,
    alpha: float = 0.050,
) -> tuple[bool, float, float]:
    """Evaluates safety qualification using corrected Maurer-Pontil (2009 Theorem 4).

    Returns:
        tuple (qualifies: bool, ucb: float, sample_variance: float)
    """
    x = np.asarray(cluster_risks, dtype=np.float64)
    k = len(x)
    if k < 2:
        raise ValueError("Maurer-Pontil bound requires at least 2 observations.")

    ucb = ucb_empirical_bernstein_corrected(x, alpha=alpha)
    var_r = float(np.var(x, ddof=1))
    qualifies = bool(ucb <= tau)
    return qualifies, float(ucb), var_r


def eval_direct_betting(
    cluster_risks: np.ndarray | Sequence[float],
    tau: float = 0.050,
    alpha: float = 0.050,
    c: float = 0.75,
    strategy: str = "agrapa",
) -> tuple[bool, float]:
    """Evaluates safety qualification using direct fixed-horizon betting test W_K(tau) >= 1/alpha.

    Returns:
        tuple (qualifies: bool, final_wealth: float)
    """
    thresh = 1.0 / alpha
    x_seq = cluster_risks.tolist() if isinstance(cluster_risks, np.ndarray) else list(cluster_risks)
    w_final, _ = compute_wealth_path(tau, x_seq, c=c, strategy=strategy)
    qualifies = bool(w_final >= thresh)
    return qualifies, float(w_final)


def eval_constant_betting(
    cluster_risks: np.ndarray | Sequence[float],
    tau: float = 0.050,
    alpha: float = 0.050,
    theta_alt: float = 0.010,
    var_alt: float | None = None,
    c: float = 0.75,
) -> tuple[bool, float, float]:
    """Evaluates safety qualification using constant-betting e-value (Theorem 1, AM-GM).

    Guaranteed valid (E[W] <= 1 under H0: mean >= tau) for ANY independent heterogeneous
    cluster schedule (Design C).

    Returns:
        tuple (qualifies: bool, final_wealth: float, lam_star: float)
    """
    thresh = 1.0 / alpha
    max_lam = c / max(1e-9, 1.0 - tau)

    if var_alt is None:
        # Default conservative plug-in variance for Bernoulli(theta_alt)
        var_alt = theta_alt * (1.0 - theta_alt)

    # Kelly-optimal plug-in bet for point alternative theta_alt
    diff = max(0.0, tau - theta_alt)
    raw_lam = diff / max(1e-6, var_alt + diff**2)
    lam_star = float(min(max_lam, max(0.0, raw_lam)))

    x = np.asarray(cluster_risks, dtype=np.float64)
    # W_K = prod_{i=1}^K [1 + lam_star * (tau - X_i)]
    multipliers = 1.0 + lam_star * (tau - x)
    w_final = float(np.prod(multipliers))
    qualifies = bool(w_final >= thresh)
    return qualifies, w_final, lam_star


def eval_permutation_betting(
    cluster_risks: np.ndarray | Sequence[float],
    tau: float = 0.050,
    alpha: float = 0.050,
    m_permutations: int = 30,
    seed: int | None = None,
    c: float = 0.75,
    strategy: str = "agrapa",
) -> tuple[bool, float]:
    """Evaluates safety qualification using permutation-averaged betting wealth.

    W_bar = (1 / M) sum_{j=1}^M W_K(tau, pi_j(x)).
    Protects against adversarial schedule ordering under exchangeable cluster draws.

    Returns:
        tuple (qualifies: bool, mean_wealth: float)
    """
    thresh = 1.0 / alpha
    x = np.asarray(cluster_risks, dtype=np.float64)
    rng = np.random.default_rng(seed)

    w_total = 0.0
    for _ in range(m_permutations):
        x_perm = rng.permutation(x).tolist()
        w, _ = compute_wealth_path(tau, x_perm, c=c, strategy=strategy)
        w_total += w

    w_mean = float(w_total / m_permutations)
    qualifies = bool(w_mean >= thresh)
    return qualifies, w_mean


def eval_hoeffding(
    cluster_risks: np.ndarray | Sequence[float],
    tau: float = 0.050,
    alpha: float = 0.050,
) -> tuple[bool, float]:
    """Evaluates safety qualification using classical Hoeffding (1963) distribution-free bound.

    UCB = mean(X) + sqrt(ln(1/alpha) / (2 * K)).
    Valid for ANY independent bounded observations in [0, 1] regardless of heterogeneity.

    Returns:
        tuple (qualifies: bool, ucb: float)
    """
    x = np.asarray(cluster_risks, dtype=np.float64)
    k = len(x)
    if k == 0:
        raise ValueError("Cannot evaluate Hoeffding on empty array.")

    r_bar = float(np.mean(x))
    penalty = math.sqrt(math.log(1.0 / alpha) / (2.0 * k))
    ucb = float(r_bar + penalty)
    qualifies = bool(ucb <= tau)
    return qualifies, ucb


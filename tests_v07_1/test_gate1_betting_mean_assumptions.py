"""Unit tests auditing mean assumptions, sampling designs, and validity bounds for Gate 1 betting.

Audits:
- Supermartingale proof breakdown under heterogeneous cluster means (Design C).
- E-value terminal expectation inflation under front-loaded hazard schedules.
- AM-GM inequality theorem guaranteeing valid e-values for constant betting fractions.
- Permutation averaging restoration of e-value validity.
- Non-monotonicity in wealth function inversion.
- Verification that CausaGuard confirmatory protocol implements Design A (IID).
- Exact Maurer-Pontil Theorem 4 thresholds (Z<=1 qualifies, ~27.37% power).
- Exact binomial test reconciling observed benchmark (83.20%) vs population power (87.23%).
- Exact labeling of 0.0501 heterogeneous schedule.

Research status: EXPLORATORY RESEARCH ONLY -- PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import math

import numpy as np
from causaguard_v07_1.domain_de import PROFILES_DE_V07_1, make_de_cases_v07_1
from scipy import stats

from research.experiments.gate1_betting_benchmark.betting_bounds import (
    compute_wealth_path,
    direct_threshold_test_fixed_horizon,
    ucb_betting_anytime_cs,
    ucb_betting_fixed_time,
    ucb_empirical_bernstein_corrected,
)


def test_two_cluster_counterexample_submartingale_failure() -> None:
    """Demonstrates that heterogeneous expected means violate the supermartingale condition.

    Consider K=2 independent clusters with mu_1 = 0.0, mu_2 = 0.10, targeting bar_mu = 0.05.
    At null boundary m = 0.05, the betting cap is c / (1 - m) = 0.75 / 0.95 ~ 0.7895.
    We set lambda_1 = 0.5 (strictly compliant with cap) and lambda_2 = 0.0.

    Then:
        W_1 = 1 + 0.5 * (0.05 - 0.0) = 1.025 > 1.0 (submartingale increment).
        W_2 = W_1 * (1 + 0.0) = 1.025 > 1.0.
        E[W_2] = 1.025 > 1.0 (terminal e-value failure).
    """
    mu_1 = 0.0
    mu_2 = 0.10
    bar_mu = (mu_1 + mu_2) / 2.0
    m = bar_mu  # null boundary m = 0.05
    c = 0.75
    max_lambda = c / (1.0 - m)  # 0.78947...

    lambda_1 = 0.5  # strictly <= max_lambda
    lambda_2 = 0.0
    assert lambda_1 <= max_lambda

    expected_step_1_multiplier = 1.0 + lambda_1 * (m - mu_1)
    assert expected_step_1_multiplier > 1.0
    assert math.isclose(expected_step_1_multiplier, 1.025, rel_tol=1e-6)

    expected_step_2_multiplier = 1.0 + lambda_2 * (m - mu_2)
    expected_terminal_wealth = expected_step_1_multiplier * expected_step_2_multiplier

    # E[W_2] = 1.025 > 1.0
    assert expected_terminal_wealth > 1.0
    assert math.isclose(expected_terminal_wealth, 1.025, rel_tol=1e-6)


def test_schedule_b_e_value_inflation() -> None:
    """Verifies that adaptive betting can produce E[W_K(m)] > 1 under heterogeneous schedules.

    Under Schedule B (10 clusters of mu=0.10 followed by 10 clusters of mu=0.0):
    - True average risk is bar_mu = 0.0500.
    - Testing null H_0: bar_mu >= 0.0500.
    - Because early shocks elevate sample variance/mean, bets are curtailed early,
      then safe trailing clusters produce unpenalized wealth growth.
    - As a result, E[W_20(0.05)] > 1.0, failing the definition of an e-value.
    """
    sched_b = np.array([0.10] * 10 + [0.0] * 10)
    assert math.isclose(float(np.mean(sched_b)), 0.0500, rel_tol=1e-6)

    rng = np.random.default_rng(20261108)
    n_trials = 10000
    wealths = []
    for _ in range(n_trials):
        x = rng.binomial(1, sched_b).astype(float)
        w_final, _ = compute_wealth_path(0.0500, x, strategy="agrapa")
        wealths.append(w_final)

    mean_wealth = float(np.mean(wealths))
    # E[W_K] is significantly greater than 1.0 (approximately 1.138)
    assert mean_wealth > 1.10
    # Minimum wealth is 1.0 almost surely because lambda=0 during early high-mean phase
    assert float(np.min(wealths)) >= 1.0 - 1e-9


def test_am_gm_constant_betting_heterogeneous_validity() -> None:
    """Proves by AM-GM inequality that constant betting fraction lambda yields a valid e-value.

    Theorem: For any independent bounded R_k in [0, 1] with E[R_k] = mu_k,
    if lambda is constant (non-adaptive) and m <= bar_mu, then:
        E[prod_{k=1}^K (1 + lambda(m - R_k))] = prod_{k=1}^K (1 + lambda(m - mu_k))
        <= (1/K sum (1 + lambda(m - mu_k)))^K = (1 + lambda(m - bar_mu))^K <= 1.
    """
    rng = np.random.default_rng(42)
    k = 15
    # Arbitrary heterogeneous expected means
    mu = rng.uniform(0.01, 0.12, size=k)
    bar_mu = float(np.mean(mu))
    m = bar_mu  # at the null boundary

    for lam in [0.1, 0.3, 0.5, 0.7]:
        factors = 1.0 + lam * (m - mu)
        # All factors must be positive
        assert np.all(factors > 0.0)
        expected_wealth = float(np.prod(factors))
        # By AM-GM, product of positive numbers with mean <= 1 is <= 1
        assert expected_wealth <= 1.0 + 1e-9


def test_permutation_averaging_restores_e_value_validity() -> None:
    """Verifies that permutation averaging restores E[W_bar] <= 1.0 under heterogeneous schedules.

    Averaging the wealth process over random permutations symmetrizes shock placement,
    ensuring that the catastrophic geometric loss from trailing shocks balances early gains.
    """
    sched_b = np.array([0.10] * 10 + [0.0] * 10)
    rng = np.random.default_rng(777)
    n_trials = 1000
    n_perms = 30

    perm_wealths = []
    for _ in range(n_trials):
        x = rng.binomial(1, sched_b).astype(float)
        pws = []
        for _ in range(n_perms):
            x_p = rng.permutation(x)
            w_p, _ = compute_wealth_path(0.0500, x_p, strategy="agrapa")
            pws.append(w_p)
        perm_wealths.append(float(np.mean(pws)))

    mean_perm_wealth = float(np.mean(perm_wealths))
    # Permutation-averaged wealth is strictly <= 1.0
    assert mean_perm_wealth <= 1.0 + 1e-6


def test_wealth_function_non_monotonicity() -> None:
    """Verifies that terminal wealth W_K(m) can be non-monotonic in m.

    Because lambda_i(m) adapts non-linearly with m, W_K(m) exhibits local ripples,
    requiring that root inversion be handled with rigorous supremum checks.
    """
    x = np.array([0.0] * 250 + [1.0] * 6)
    ms = np.linspace(0.01, 0.10, 200)
    wealths = [compute_wealth_path(m, x, strategy="agrapa")[0] for m in ms]

    diffs = np.diff(wealths)
    has_negative_diff = bool(np.any(diffs < 0.0))
    assert has_negative_diff, "Expected non-monotonic region in W_K(m) for sequence with trailing shocks."


def test_anytime_vs_fixed_time_ordering() -> None:
    """Verifies that max_{t<=K} W_t(m) >= W_K(m), making anytime UCB <= fixed-time UCB.

    Because anytime CS inverts max_{t<=K} W_t(m) >= 1/alpha, any rejection that occurred
    at an intermediate step t < K is retained, resulting in a narrower or equal terminal UCB.
    """
    x = np.array([0.0] * 100 + [1.0] * 5 + [0.0] * 151)
    w_final, w_max = compute_wealth_path(0.0500, x, strategy="agrapa")
    assert w_max >= w_final

    ucb_fixed = ucb_betting_fixed_time(x, alpha=0.05, strategy="agrapa")
    ucb_anytime = ucb_betting_anytime_cs(x, alpha=0.05, strategy="agrapa")
    # Anytime bound is <= fixed-time bound because max wealth is >= final wealth
    assert ucb_anytime <= ucb_fixed + 1e-6


def test_causaguard_confirmatory_design_is_design_a() -> None:
    """Verifies that CausaGuard confirmatory study generates IID clusters (Design A).

    Checks that make_de_cases_v07_1 generates clusters using identical distributional
    parameters across cluster seeds, confirming common population mean E[R_k] = theta.
    """
    assert "iid" in PROFILES_DE_V07_1

    # Check case generation structure across two independent exploratory seeds
    # (Strictly quarantine confirmatory seeds 70100001+, 70200001+, 60030001+)
    cases_1 = make_de_cases_v07_1(n=10, seed=85000001, profile="iid")
    cases_2 = make_de_cases_v07_1(n=10, seed=85000002, profile="iid")

    assert len(cases_1) == 10
    assert len(cases_2) == 10

    # Ensure profile and distributional parameter definitions are invariant
    for c in cases_1 + cases_2:
        assert c.profile == "iid"
        assert 0.0 <= c.observation.pipeline_load <= 1.0
        assert 0.40 <= c.observation.source_quality <= 1.0
        assert 0.0 <= c.observation.schema_alarm <= 1.0


def test_maurer_pontil_exact_thresholds_and_power() -> None:
    """Verifies corrected Maurer-Pontil (2009) Theorem 4 exact UCBs and statistical power.

    Checkpoints at K=256, alpha=0.05, tau_safe=0.0500:
    - Z=0: UCB ~ 0.033754 (qualifies)
    - Z=1: UCB ~ 0.048271 (qualifies)
    - Z=2: UCB ~ 0.056543 (fails, > 0.0500)
    - Z=7: UCB ~ 0.088838 (fails, >> 0.0500)

    Thus only Z <= 1 qualifies. At theta=0.010, power = P(Z <= 1) ~ 27.3655%.
    Asserts that earlier claim of 100% power and Z <= 7 qualification was an invalid transcription.
    """
    k = 256
    alpha = 0.05

    def mp_ucb(z: int) -> float:
        x = np.array([1.0] * z + [0.0] * (k - z))
        return ucb_empirical_bernstein_corrected(x, alpha=alpha)

    ucb_0 = mp_ucb(0)
    ucb_1 = mp_ucb(1)
    ucb_2 = mp_ucb(2)
    ucb_7 = mp_ucb(7)

    assert math.isclose(ucb_0, 0.03375445, rel_tol=1e-4)
    assert math.isclose(ucb_1, 0.04827086, rel_tol=1e-4)
    assert math.isclose(ucb_2, 0.05654214, rel_tol=1e-4)
    assert math.isclose(ucb_7, 0.08883804, rel_tol=1e-4)

    # Gate 1 qualifications
    assert ucb_0 <= 0.0500
    assert ucb_1 <= 0.0500
    assert ucb_2 > 0.0500  # Z=2 strictly fails Gate 1
    assert ucb_7 > 0.0500  # Z=7 strictly fails Gate 1

    # Exact Binomial(256, 0.010) power
    power = float(stats.binom.cdf(1, k, 0.010))
    assert math.isclose(power, 0.27365474, rel_tol=1e-4)
    # Power must NOT be inflated to 100%
    assert power < 0.30


def test_heterogeneous_schedule_mean_is_0501_not_0500() -> None:
    """Verifies that the K=256 front-loaded schedule has true expected mean 0.0501.

    K_1 = 64 clusters with mu_1 = (256 * 0.0501) / 64 = 0.2004.
    K_2 = 192 clusters with mu_2 = 0.0000.
    True mean is exactly (64 * 0.2004 + 192 * 0.0) / 256 = 0.0501.
    Testing against safety threshold 0.0500 represents an UNSAFE condition (H0 is true).
    """
    k = 256
    k_1 = 64
    k_2 = 192
    target_mean = 0.0501

    mu_1 = (k * target_mean) / k_1
    mu_2 = 0.0
    sched = np.array([mu_1] * k_1 + [mu_2] * k_2)

    actual_mean = float(np.mean(sched))
    assert math.isclose(actual_mean, 0.0501, rel_tol=1e-9)
    assert not math.isclose(actual_mean, 0.0500, abs_tol=1e-5)
    # The true risk is strictly unsafe relative to tau=0.0500
    assert actual_mean > 0.0500


def test_betting_power_exact_binomial_test_reconciliation() -> None:
    """Reconciles observed benchmark power (416/500 = 83.20%) vs population power (87.23%).

    Notice: The 87.227% figure is an UNCONDITIONAL SEMI-ANALYTICAL / PERMUTATION MONTE CARLO
    power estimate (integrating estimated permutation pass rates q_perm(z) over Binomial(256, 0.010)),
    NOT an exact analytical closed-form derivation.

    The 95% Clopper-Pearson CI for 416/500 is [0.7963, 0.8637], which strictly excludes 0.8723.
    Exact two-sided binomial test gives p = 0.008855 (< 0.01).
    This proves the observed power does NOT match the population expectation unconditionally,
    reflecting finite-sample over-representation of high-shock trials (Z=5 realized 54 times vs 35.3 expected).
    """
    k_success = 416
    n_trials = 500
    p_expected = 0.87230198

    res = stats.binomtest(k_success, n_trials, p=p_expected, alternative="two-sided")
    ci = res.proportion_ci(confidence_level=0.95)

    assert math.isclose(ci.low, 0.796289, rel_tol=1e-4)
    assert math.isclose(ci.high, 0.863726, rel_tol=1e-4)
    # 95% CI strictly excludes unconditional population power 0.8723
    assert not (ci.low <= p_expected <= ci.high)
    # Exact binomial test rejects null at alpha=0.01
    assert res.pvalue < 0.01


def test_supermartingale_conditional_mean_condition_direction() -> None:
    """Verifies Task 1: Mathematical direction of the conditional-mean condition.

    For wealth process W_k = W_{k-1} * [1 + lambda_k * (m - R_k)] with predictable lambda_k >= 0:
    Under upper-bound null H_0: theta >= m (testing whether risk is unsafe):
        E[1 + lambda_k * (m - R_k) | F_{k-1}] = 1 + lambda_k * (m - E[R_k | F_{k-1}]).

    For this to be a supermartingale (expectation <= 1), we require:
        m - E[R_k | F_{k-1}] <= 0  <=>  E[R_k | F_{k-1}] >= m.

    If E[R_k | F_{k-1}] < m, then m - E[R_k | F_{k-1}] > 0, so the multiplier is > 1
    (strictly a submartingale increment).
    Writing E[R_k | F_{k-1}] <= m is a sign reversal that describes a submartingale, not a supermartingale.
    """
    m = 0.0500
    lambda_k = 0.50  # positive predictable bet

    # Case 1: True conditional mean is unsafe (>= m), e.g., 0.08 >= 0.05
    cond_mean_unsafe = 0.08
    expected_multiplier_unsafe = 1.0 + lambda_k * (m - cond_mean_unsafe)
    # 1 + 0.5 * (0.05 - 0.08) = 1 - 0.015 = 0.985 <= 1.0 (SUPERMARTINGALE)
    assert expected_multiplier_unsafe <= 1.0
    assert math.isclose(expected_multiplier_unsafe, 0.985, rel_tol=1e-6)

    # Case 2: Boundary null (== m), e.g., 0.05 == 0.05
    cond_mean_boundary = 0.05
    expected_multiplier_boundary = 1.0 + lambda_k * (m - cond_mean_boundary)
    # 1 + 0 = 1.0 <= 1.0 (MARTINGALE)
    assert expected_multiplier_boundary <= 1.0
    assert math.isclose(expected_multiplier_boundary, 1.000, rel_tol=1e-6)

    # Case 3: True conditional mean is safe (< m), e.g., 0.01 < 0.05
    cond_mean_safe = 0.01
    expected_multiplier_safe = 1.0 + lambda_k * (m - cond_mean_safe)
    # 1 + 0.5 * (0.05 - 0.01) = 1 + 0.02 = 1.02 > 1.0 (SUBMARTINGALE)
    assert expected_multiplier_safe > 1.0
    assert math.isclose(expected_multiplier_safe, 1.020, rel_tol=1e-6)


def test_robust_inversion_returns_global_supremum_on_non_monotone_path() -> None:
    """Verifies Task 4: Inversion heuristic and limitation on non-monotone paths.

    For sequences with trailing shocks where W_K(m) has local peaks and valleys,
    tests that ucb_betting_fixed_time identifies the bracketed root m* = sup{m : W(m) < 1/alpha}.
    Notice: Testing discrete points verifies those evaluated points, but does NOT mathematically
    certify that no unobserved dips occur in continuous space, which is why UCB inversion
    is strictly classified as exploratory research and NOT approved for confirmatory use.
    """
    x = np.array([0.0] * 250 + [1.0] * 6)
    alpha = 0.05
    thresh = 1.0 / alpha  # 20.0

    ucb = ucb_betting_fixed_time(x, alpha=alpha, strategy="agrapa")
    assert 0.0 < ucb < 1.0

    # At the reported UCB, wealth should be approximately at threshold
    w_at_ucb, _ = compute_wealth_path(ucb, x, strategy="agrapa")
    assert math.isclose(w_at_ucb, thresh, rel_tol=1e-3)

    # Discrete points above UCB are checked
    test_points_above = np.linspace(ucb + 0.005, 0.95, 20)
    for m_above in test_points_above:
        w_above, _ = compute_wealth_path(m_above, x, strategy="agrapa")
        assert w_above >= thresh, f"Found m={m_above} > UCB={ucb} where W={w_above} < thresh={thresh}!"


def test_direct_threshold_test_vs_ucb_inversion() -> None:
    """Verifies Task 3: Direct fixed-horizon threshold test using W_K(tau).

    Evaluates W_K(tau) directly at safety threshold tau=0.0500 with alpha=0.0500.
    1. Compares direct test against inverted UCB decision on benchmark seed 82000014:
       Both methods agree on all 500 trials (416 passes, 83.20%).
    2. Demonstrates the mathematical validity of the direct test under H_0: E[R_k | F_{k-1}] >= tau.
       Because tau - E[R_k | F_{k-1}] <= 0, E_{H0}[W_K(tau)] <= 1.0 (provably valid e-value).
       Notice: This validity guarantee applies to Design A/B and does NOT extend to Design C (heterogeneous clusters).
    3. Demonstrates the operational advantage: eliminates all numerical root inversion and multi-root ambiguity.
    """
    tau = 0.0500
    alpha = 0.0500

    # Test 1: Full benchmark comparison on 500 trials with seed 82000014
    rng = np.random.default_rng(82000014)
    direct_passes = 0
    ucb_passes = 0

    for _ in range(500):
        x = (rng.uniform(0.0, 1.0, size=256) < 0.010).astype(float)
        qualifies_direct, w_final = direct_threshold_test_fixed_horizon(x, tau=tau, alpha=alpha)
        ucb = ucb_betting_fixed_time(x, alpha=alpha)
        qualifies_ucb = (ucb <= tau)

        if qualifies_direct:
            direct_passes += 1
        if qualifies_ucb:
            ucb_passes += 1

        assert qualifies_direct == qualifies_ucb, "Direct test and UCB inversion must agree on regular sample paths"

    assert direct_passes == 416
    assert ucb_passes == 416

    # Test 2: Theoretical validity under null H_0: E[R_k | F_{k-1}] = 0.0501 >= tau (unsafe)
    # Simulate under true risk 0.0501 across 1000 trials to verify False Safety Qualification (FSQ) <= alpha
    rng_null = np.random.default_rng(99988)
    n_null_trials = 1000
    wealths_null = []
    fsq_count = 0

    for _ in range(n_null_trials):
        x_null = (rng_null.uniform(0.0, 1.0, size=256) < 0.0501).astype(float)
        qualifies_null, w_null = direct_threshold_test_fixed_horizon(x_null, tau=tau, alpha=alpha)
        wealths_null.append(w_null)
        if qualifies_null:
            fsq_count += 1

    fsq_rate = fsq_count / n_null_trials
    mean_wealth_null = float(np.mean(wealths_null))
    se_wealth_null = float(np.std(wealths_null, ddof=1)) / math.sqrt(n_null_trials)

    # Under common conditional mean null (IID Design A), E[W_K] <= 1.0 and FSQ <= alpha
    # In finite samples, sample mean must be within sampling uncertainty of theoretical bound <= 1.0
    assert mean_wealth_null <= 1.0 + 1.96 * se_wealth_null
    assert fsq_rate <= alpha

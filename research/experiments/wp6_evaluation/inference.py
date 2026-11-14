"""Statistical inference, cluster-aware bootstrap, and out-of-sample calibration for WP6.

Implements:
1. Cluster-aware block bootstrap for paired counterfactual contrasts across independent clusters;
2. Brier score and Expected Calibration Error (ECE) for held-out evaluation cases;
3. Detection of zero-width intervals, degenerate metrics, and finite-sample boundaries.

Follows CausaGuard PhD Research Master Roadmap 2026:
- Section 13, page 17: WP6 Evaluation ("Paired comparisons, cluster-aware uncertainty, shift sensitivity and replay");
- Section 9, pages 12-13: Baselines, ablations and statistical protocol.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from causaguard_v07_1.domain_cs import (
    CSCaseV07_1,
    execute_cs_step_v07_1,
)
from causaguard_v07_1.domain_de import (
    DECaseV07_1,
    execute_de_step_v07_1,
)

from research.experiments.wp5_contextual_model.features import (
    extract_features_step1,
)
from research.experiments.wp5_contextual_model.model import (
    ACTIONS_CS_STEP1,
    ACTIONS_DE_STEP1,
    TrainedContextualInterventionModel,
)


def compute_brier_and_ece(
    y_true: np.ndarray,
    prob_pred: np.ndarray,
    n_bins: int = 10,
) -> dict[str, float]:
    """Computes Brier score and Expected Calibration Error (ECE) for binary probabilistic predictions.

    Parameters
    ----------
    y_true : np.ndarray
        True binary event labels {0, 1}.
    prob_pred : np.ndarray
        Predicted probabilities in [0, 1].
    n_bins : int, default 10
        Number of equal-width bins in [0, 1].

    Returns
    -------
    dict with 'brier' and 'ece'.
    """
    y_arr = np.asarray(y_true, dtype=np.float64)
    p_arr = np.clip(np.asarray(prob_pred, dtype=np.float64), 0.0, 1.0)
    n = len(y_arr)
    if n == 0:
        return {"brier": 0.0, "ece": 0.0}

    brier = float(np.mean((p_arr - y_arr) ** 2))

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        low, high = bins[i], bins[i + 1]
        mask = (p_arr >= low) & (p_arr <= high) if i == n_bins - 1 else (p_arr >= low) & (p_arr < high)
        if np.any(mask):
            bin_acc = float(np.mean(y_arr[mask]))
            bin_conf = float(np.mean(p_arr[mask]))
            ece += (float(np.sum(mask)) / n) * abs(bin_acc - bin_conf)

    return {"brier": brier, "ece": float(ece)}


def cluster_bootstrap_ci(
    cluster_means: np.ndarray | list[float],
    alpha: float = 0.05,
    n_boot: int = 2000,
    seed: int = 42,
) -> dict[str, Any]:
    """Computes cluster-robust confidence intervals and standard errors by resampling clusters.

    Parameters
    ----------
    cluster_means : np.ndarray | list[float]
        Array of length K containing the mean paired difference for each independent cluster.
    alpha : float, default 0.05
        Nominal significance level for two-sided (1 - alpha) CI (default 95% CI).
    n_boot : int, default 2000
        Number of bootstrap replications.
    seed : int, default 42
        Pseudorandom seed for reproducible bootstrap sampling.

    Returns
    -------
    dict with 'mean', 'std_err', 'ci_lower', 'ci_upper', 'zero_width'.
    """
    arr = np.asarray(cluster_means, dtype=np.float64)
    k = len(arr)
    if k < 2:
        raise ValueError(f"Cluster bootstrap requires at least K=2 clusters, got K={k}")

    rng = np.random.default_rng(seed)
    boot_indices = rng.integers(0, k, size=(n_boot, k))
    boot_means = np.mean(arr[boot_indices], axis=1)

    mean_est = float(np.mean(arr))
    se_est = float(np.std(boot_means, ddof=1))
    ci_low = float(np.quantile(boot_means, alpha / 2.0))
    ci_high = float(np.quantile(boot_means, 1.0 - alpha / 2.0))

    return {
        "mean": mean_est,
        "std_err": se_est,
        "ci_lower": ci_low,
        "ci_upper": ci_high,
        "zero_width": bool(ci_low == ci_high),
    }


def evaluate_out_of_sample_calibration(
    model: TrainedContextualInterventionModel,
    cases: list[CSCaseV07_1] | list[DECaseV07_1],
    n_bins: int = 10,
) -> dict[str, Any]:
    """Evaluates Brier score and ECE on untouched out-of-sample evaluation cases under distribution shift."""
    if not model.fitted:
        raise RuntimeError("Model must be fitted before evaluating calibration!")

    is_cs = isinstance(cases[0], CSCaseV07_1)
    acts = ACTIONS_CS_STEP1 if is_cs else ACTIONS_DE_STEP1

    X = np.array([extract_features_step1(c.observation, context=model.context) for c in cases])

    metrics: dict[str, Any] = {}

    for arm in acts:
        y_comp_list: list[float] = []
        y_unsafe_list: list[float] = []

        for case in cases:
            b_rem = case.observation.budget
            if is_cs:
                assert isinstance(case, CSCaseV07_1)
                if arm == "verify":
                    res_v = execute_cs_step_v07_1(case=case, action="verify", b_rem=b_rem)
                    if res_v["terminal"] or res_v["evidence"] is None:
                        y_comp_list.append(float(res_v["completed"]))
                        y_unsafe_list.append(float(res_v["unsafe"]))
                    else:
                        ev = res_v["evidence"]
                        rec_act = "retry" if ev.flagged else "proceed"
                        res2 = execute_cs_step_v07_1(
                            case=case,
                            action=rec_act,
                            b_rem=res_v["b_rem"],
                            current_latency=res_v["latency"],
                            prior_cost=res_v["cost"],
                            evidence=ev,
                        )
                        y_comp_list.append(float(res2["completed"]))
                        y_unsafe_list.append(float(res2["unsafe"]))
                else:
                    res = execute_cs_step_v07_1(case=case, action=arm, b_rem=b_rem)
                    y_comp_list.append(float(res["completed"]))
                    y_unsafe_list.append(float(res["unsafe"]))
            else:
                assert isinstance(case, DECaseV07_1)
                if arm == "verify":
                    res_v = execute_de_step_v07_1(case=case, action="verify", b_rem=b_rem)
                    if res_v["terminal"] or res_v["evidence"] is None:
                        y_comp_list.append(float(res_v["completed"]))
                        y_unsafe_list.append(float(res_v["unsafe"]))
                    else:
                        ev = res_v["evidence"]
                        needs_restore = not ev.schema_valid or ev.sample_pass_rate < 0.80
                        rec_act = "restore" if needs_restore else "proceed"
                        res2 = execute_de_step_v07_1(
                            case=case,
                            action=rec_act,
                            b_rem=res_v["b_rem"],
                            current_latency=res_v["latency"],
                            prior_cost=res_v["cost"],
                            evidence=ev,
                        )
                        y_comp_list.append(float(res2["completed"]))
                        y_unsafe_list.append(float(res2["unsafe"]))
                else:
                    res = execute_de_step_v07_1(case=case, action=arm, b_rem=b_rem)
                    y_comp_list.append(float(res["completed"]))
                    y_unsafe_list.append(float(res["unsafe"]))

        y_comp_arr = np.asarray(y_comp_list, dtype=np.float64)
        y_unsafe_arr = np.asarray(y_unsafe_list, dtype=np.float64)

        arm_model = model.models_s1[arm]
        raw_preds = arm_model.predict(X)
        raw_comp = raw_preds[:, 0]
        raw_unsafe = raw_preds[:, 1]

        cal_comp = model.calibrators_s1[arm]["completed"].predict(raw_comp)
        cal_unsafe = model.calibrators_s1[arm]["unsafe"].predict(raw_unsafe)

        eval_comp_raw = compute_brier_and_ece(y_comp_arr, raw_comp, n_bins=n_bins)
        eval_comp_cal = compute_brier_and_ece(y_comp_arr, cal_comp, n_bins=n_bins)
        eval_unsafe_raw = compute_brier_and_ece(y_unsafe_arr, raw_unsafe, n_bins=n_bins)
        eval_unsafe_cal = compute_brier_and_ece(y_unsafe_arr, cal_unsafe, n_bins=n_bins)

        metrics[arm] = {
            "brier_completed_raw": eval_comp_raw["brier"],
            "brier_completed_cal": eval_comp_cal["brier"],
            "ece_completed_raw": eval_comp_raw["ece"],
            "ece_completed_cal": eval_comp_cal["ece"],
            "brier_unsafe_raw": eval_unsafe_raw["brier"],
            "brier_unsafe_cal": eval_unsafe_cal["brier"],
            "ece_unsafe_raw": eval_unsafe_raw["ece"],
            "ece_unsafe_cal": eval_unsafe_cal["ece"],
        }

    return metrics

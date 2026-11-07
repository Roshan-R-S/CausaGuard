"""CausaGuard v0.7.1: Prospective Confirmatory Evaluation Runner.

Executes the official confirmatory evaluation under the prospective v0.7.1 protocol:
- Primary Confirmatory Domain: Data Engineering ('de', seeds 70100001-70100128, K=128)
- Secondary Boundary Domain: Customer Support ('cs', seeds 70110001-70110128, K=128)
- Nominal IID profile (primary) with N=400 cases per cluster (51,200 cases per domain)
- Symmetric 8-policy benchmark suite with independent queue-state tracking
- Primary Confirmatory Hypothesis: 3 prespecified contrasts under FWER alpha = 0.010:
  * C1: cost_rule_v07_1 vs always_recovery
  * C2: cost_rule_v07_1 vs always_escalate
  * C3: cost_rule_v07_1 vs cost_sensitive_symmetric_heuristic
- Multiplicity control: Bonferroni per-contrast alpha = 0.010 / 3 = 0.00333333
- Superiority hurdle: Delta = +0.015 utility gain (reject H0 iff LCB > +0.015)
- Two-Stage Gatekeeping:
  * Gate 1: Clustered operational risk UCB_0.95 <= 0.050, Authorization Violations == 0
  * Gate 2: Paired utility superiority over all 3 primary comparators
- Fréchet-Bonferroni lower bound for joint study success probability
- Strict Pre-Freeze Execution Lock: Strictly refuses to execute actual confirmatory
  seeds without an independently verified cryptographic protocol seal.
- Strict Quarantine: Strictly forbids and rejects reserved final evaluation seeds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import scipy.stats as stats

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src_v07_1") not in sys.path:
    sys.path.insert(0, str(ROOT / "src_v07_1"))

from causaguard_v07_1.domain_cs import make_cs_cases_v07_1  # noqa: E402
from causaguard_v07_1.domain_de import make_de_cases_v07_1  # noqa: E402
from causaguard_v07_1.policy_v07_1 import BasePolicyV07_1, get_baseline_policies_v07_1  # noqa: E402
from causaguard_v07_1.study_v07_1 import evaluate_cluster_v07_1  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Protocol Constants
STUDY_VERSION = "0.7.1-isolated"
PRIMARY_DOMAIN = "de"
SECONDARY_DOMAIN = "cs"

# Seed Registries
CONFIRMATORY_SEEDS_DE = tuple(range(70100001, 70100129))  # K=128
CONFIRMATORY_SEEDS_CS = tuple(range(70110001, 70110129))  # K=128
RESERVED_FINAL_SEEDS_RANGE = range(70200001, 70300000)
HISTORICAL_QUARANTINED_RANGE = range(60030001, 60040065)
HISTORICAL_EXPLORATORY_V07 = range(70001001, 70001017)
HISTORICAL_EXPLORATORY_V07_1 = range(70002001, 70002017)
NON_EVALUATIVE_TEST_RANGE = range(70003001, 70010000)

CASES_PER_CLUSTER = 400
DELTA_HURDLE = 0.015
FWER_ALPHA = 0.010
NUM_PRIMARY_CONTRASTS = 3
ALPHA_CONTRAST = FWER_ALPHA / NUM_PRIMARY_CONTRASTS  # 0.0033333333333333335
OPERATIONAL_RISK_LIMIT = 0.050
DEFAULT_CAPACITY_LIMIT = 150

CANDIDATE_POLICY_NAME = "cost_rule_v07_1"
PRIMARY_CONTRASTS = (
    ("C1_recovery", CANDIDATE_POLICY_NAME, "always_recovery"),
    ("C2_escalate", CANDIDATE_POLICY_NAME, "always_escalate"),
    ("C3_heuristic", CANDIDATE_POLICY_NAME, "cost_sensitive_symmetric_heuristic"),
)


class ExecutionLockError(RuntimeError):
    """Raised when evaluation execution is blocked due to missing or invalid protocol seal."""


class SecurityViolationError(ValueError):
    """Raised when an attempt is made to access strictly quarantined or reserved seeds."""


class ProtocolValidationError(ValueError):
    """Raised when inputs or execution results violate prospective protocol rules."""


def sha256_file(path: str | Path) -> str:
    """Computes SHA-256 hash of a file on disk."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def get_git_commit_hash() -> str:
    """Retrieves current Git HEAD commit hash if available."""
    try:
        p = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return p.stdout.strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def verify_protocol_seal(
    seal_path: Path | None = None,
    allow_synthetic_fixture: bool = False,
    trusted_signers: dict[str, dict[str, str]] | None = None,
    pre_freeze_mode: bool = False,
) -> dict[str, Any]:
    """Verifies that an authoritative prospective protocol seal exists and is valid.

    Delegates strictly to the authoritative verifier module (experiments_v07_1.verify_seal_v07_1),
    eliminating the weaker duplicate validation path (SEC-04).

    Raises:
        ExecutionLockError: If seal is missing, malformed, incomplete, mismatched,
                            unauthorized, or forged.
        SecurityViolationError: If path traversal or directory escape is attempted.
    """
    from experiments_v07_1.verify_seal_v07_1 import (
        SealVerificationError,
        verify_seal,
    )
    from experiments_v07_1.verify_seal_v07_1 import (
        SecurityViolationError as VerifierSecurityViolationError,
    )

    if seal_path is None:
        seal_path = ROOT / "experiments_v07_1" / "v071_protocol_seal.json"

    try:
        return verify_seal(
            seal_path=seal_path,
            root_dir=ROOT,
            require_authorized=True,
            enforce_mandatory_manifest=True,
            pre_freeze_mode=pre_freeze_mode,
            trusted_signers=trusted_signers,
            allow_synthetic_fixture=allow_synthetic_fixture,
            raise_on_error=True,
        )
    except VerifierSecurityViolationError as e:
        raise SecurityViolationError(f"EXECUTION LOCK SECURITY VIOLATION: {e}") from e
    except SealVerificationError as e:
        raise ExecutionLockError(f"EXECUTION LOCK: {e}") from e
    except Exception as e:
        raise ExecutionLockError(f"EXECUTION LOCK UNEXPECTED ERROR: {e}") from e


def assert_execution_authorized(
    seeds: list[int] | tuple[int, ...],
    domain: str,
    seal_path: Path | None = None,
    allow_synthetic_fixture: bool = False,
    trusted_signers: dict[str, dict[str, str]] | None = None,
) -> None:
    """Enforces execution lock and strict seed quarantine rules.

    - Final evaluation seeds (70200001+) and quarantined v0.6 seeds ALWAYS raise SecurityViolationError.
    - Confirmatory development seeds (70100001+) require a verified protocol seal.
    - Synthetic non-evaluative test seeds (70003001-70009999) are permitted ONLY when allow_synthetic_fixture is True.
    - No user flag can unlock actual confirmatory seeds without an authentic seal.
    """
    domain = domain.lower()
    if domain not in ("de", "cs"):
        raise ProtocolValidationError(f"Invalid domain '{domain}'. Must be 'de' or 'cs'.")

    # 1. Absolute final quarantine checks
    for s in seeds:
        if s in RESERVED_FINAL_SEEDS_RANGE:
            raise SecurityViolationError(
                f"FATAL SECURITY VIOLATION: Attempted to access strictly quarantined final evaluation seed {s}!"
            )
        if s in HISTORICAL_QUARANTINED_RANGE:
            raise SecurityViolationError(
                f"FATAL SECURITY VIOLATION: Attempted to access quarantined v0.6 final evaluation seed {s}!"
            )
        if s in HISTORICAL_EXPLORATORY_V07 or s in HISTORICAL_EXPLORATORY_V07_1:
            raise ProtocolValidationError(
                f"Protocol violation: Attempted to run confirmatory evaluation on historical exploratory seed {s}."
            )

    # 2. Check for synthetic test seeds
    all_synthetic = all(s in NON_EVALUATIVE_TEST_RANGE for s in seeds)
    if all_synthetic:
        if not allow_synthetic_fixture:
            raise ProtocolValidationError(
                "Synthetic smoke seeds are only permitted in verified test harness."
            )
        return  # Permitted for synthetic test fixtures

    # 3. Confirmatory development seeds check
    valid_dev_range = CONFIRMATORY_SEEDS_DE if domain == "de" else CONFIRMATORY_SEEDS_CS
    for s in seeds:
        if s not in valid_dev_range:
            raise ProtocolValidationError(
                f"Seed {s} is not in authorized confirmatory development registry for domain '{domain}'."
            )

    # Attempting to execute actual confirmatory development seeds requires formal seal verification
    verify_protocol_seal(
        seal_path=seal_path,
        allow_synthetic_fixture=allow_synthetic_fixture,
        trusted_signers=trusted_signers,
    )


def compute_clustered_operational_risk(
    cluster_risks: list[float],
    n_cases_per_cluster: int = CASES_PER_CLUSTER,
    alpha: float = 0.050,
) -> dict[str, Any]:
    """Computes cluster-robust operational risk point estimates and confidence bounds.

    - Independent sampling unit is the cluster (K independent seeds).
    - Zero-Event Boundary Standard (mean_risk == 0.0): Under the model assumption that
      clusters behave as independent Bernoulli trials with parameter p_cluster = P(R_k > 0),
      applies exact cluster-level Clopper-Pearson bound: 1 - alpha^(1/K).
    - Standard Nonzero-Variance Regime (std_risk > 0.0): Applies cluster-level Student-t bound.
      LIMITATION: Finite-sample validity requires Gaussian cluster outcomes. For non-Gaussian
      bounded rates, CLT-based inference across K=128 clusters is asymptotic and approximate
      in finite samples; exact coverage is not automatically guaranteed to be strictly conservative.
    - Degenerate Constant Positive Risk Regime (std_risk == 0.0, mean_risk > 0.0):
      Degenerate zero-variance data cannot support standard Student-t inference without unverified
      distributional assumptions. Safety governance mandates a fail-closed INCONCLUSIVE / GATE 1 FAIL
      outcome. For downstream numeric compatibility, ucb_cluster is set to 1.0 as an explicit
      worst-case policy bound (not a calculated 95% confidence estimate).
    - Input Validation: Strictly rejects non-finite, out-of-bounds ([0, 1]), or non-numeric risks.
    """
    k_clusters = len(cluster_risks)
    if k_clusters < 1:
        raise ProtocolValidationError("Cannot compute operational risk on empty cluster list.")

    for idx, r in enumerate(cluster_risks):
        if not isinstance(r, (int, float)) or isinstance(r, bool):
            raise ProtocolValidationError(f"Invalid non-numeric risk at cluster {idx}: {r!r}")
        if not math.isfinite(r):
            raise ProtocolValidationError(f"Non-finite cluster risk at cluster {idx}: {r}")
        if r < 0.0 or r > 1.0:
            raise ProtocolValidationError(f"Cluster risk out of bounds [0, 1] at cluster {idx}: {r}")

    mean_risk = float(np.mean(cluster_risks))
    raw_std = float(np.std(cluster_risks, ddof=1)) if k_clusters > 1 else 0.0
    # Numerical stability: treat machine-precision noise on identical cluster risks as exact zero variance
    std_risk = 0.0 if (k_clusters <= 1 or raw_std <= 1e-12 or min(cluster_risks) == max(cluster_risks)) else raw_std
    se_cluster = std_risk / np.sqrt(k_clusters) if k_clusters > 0 else 0.0

    if mean_risk == 0.0:
        # Zero-event regime across all K clusters:
        # Exact cluster-level Clopper-Pearson bound on cluster failure probability
        zero_event = True
        ucb_cluster = float(1.0 - (alpha ** (1.0 / k_clusters)))
        method = "clopper_pearson_cluster_exact"
        gate1_passed = (ucb_cluster <= OPERATIONAL_RISK_LIMIT)
    elif std_risk > 0.0:
        # Standard Student-t clustered confidence bound
        zero_event = False
        t_crit = float(stats.t.ppf(1.0 - alpha, k_clusters - 1))
        ucb_cluster = float(min(1.0, mean_risk + t_crit * se_cluster))
        method = "student_t_clustered"
        gate1_passed = (ucb_cluster <= OPERATIONAL_RISK_LIMIT)
    else:
        # Constant positive cluster risk across all K clusters (std_risk == 0.0, mean_risk > 0.0):
        # Fail-closed INCONCLUSIVE / GATE 1 FAIL outcome.
        # ucb_cluster is set to 1.0 as an explicit worst-case policy bound, not a 95% confidence estimate.
        zero_event = False
        ucb_cluster = 1.0
        method = "degenerate_constant_positive_risk_fail_closed"
        gate1_passed = False

    # Descriptive case-level Clopper-Pearson for comparison
    total_cases = k_clusters * n_cases_per_cluster
    total_events = int(round(mean_risk * total_cases))
    case_cp_ucb = float(stats.beta.ppf(1.0 - alpha, total_events + 1, total_cases - total_events)) if total_events < total_cases else 1.0

    return {
        "k_clusters": k_clusters,
        "n_cases_per_cluster": n_cases_per_cluster,
        "total_cases": total_cases,
        "total_events": total_events,
        "mean_risk": mean_risk,
        "std_risk": std_risk,
        "se_cluster": se_cluster,
        "ucb_cluster": ucb_cluster,
        "case_cp_ucb_descriptive": case_cp_ucb,
        "operational_risk_limit": OPERATIONAL_RISK_LIMIT,
        "gate1_passed": gate1_passed,
        "zero_event_regime": zero_event,
        "inference_method": method,
    }


def compute_paired_contrast_statistics(
    cand_utilities: list[float],
    comp_utilities: list[float],
    contrast_name: str,
    cand_name: str,
    comp_name: str,
    delta_hurdle: float = DELTA_HURDLE,
    alpha: float = ALPHA_CONTRAST,
) -> dict[str, Any]:
    """Computes cluster-level paired Student-t inferential statistics for a contrast.

    - Input Validation: Rejects mismatched lengths, K < 2, non-numeric, or non-finite (NaN, Inf) utilities.
    - Degenerate Zero-Variance Regime (se_d <= 1e-12 or identical differences):
      When cluster-level paired utility differences have zero variance, standard Student-t inference
      is degenerate. To prevent manufactured rejections (such as artificial t=999, p=0), the contrast is
      declared inconclusive (hurdle_achieved=False, verdict='INCONCLUSIVE_DEGENERATE_VARIANCE').
    - Standard Nonzero-Variance Regime (se_d > 1e-12):
      Calculates cluster-level paired Student-t statistic and Bonferroni lower confidence bound.
    """
    k = len(cand_utilities)
    if k != len(comp_utilities):
        raise ProtocolValidationError(
            f"Mismatched cluster count: candidate has {k}, comparator has {len(comp_utilities)}."
        )
    if k < 2:
        raise ProtocolValidationError(f"Cannot perform t-test on K={k} clusters (requires K >= 2).")

    for idx, u in enumerate(cand_utilities):
        if not isinstance(u, (int, float)) or isinstance(u, bool) or not math.isfinite(u):
            raise ProtocolValidationError(
                f"Invalid non-finite or non-numeric candidate utility at cluster {idx}: {u!r}"
            )
    for idx, u in enumerate(comp_utilities):
        if not isinstance(u, (int, float)) or isinstance(u, bool) or not math.isfinite(u):
            raise ProtocolValidationError(
                f"Invalid non-finite or non-numeric comparator utility at cluster {idx}: {u!r}"
            )

    diffs = np.array(cand_utilities, dtype=np.float64) - np.array(comp_utilities, dtype=np.float64)
    mean_d = float(np.mean(diffs))
    raw_sd = float(np.std(diffs, ddof=1))
    df = k - 1
    t_crit = float(stats.t.ppf(1.0 - alpha, df))

    # Degenerate zero-variance detection (including machine precision tolerance)
    if raw_sd <= 1e-12 or min(diffs) == max(diffs):
        sd_d = 0.0
        se_d = 0.0
        lcb = -1.0  # Explicit worst-case lower bound, strictly below delta_hurdle
        t_stat = 0.0
        p_value = 1.0
        hurdle_achieved = False
        rejection = False
        status = "INCONCLUSIVE_DEGENERATE_VARIANCE"
    else:
        sd_d = raw_sd
        se_d = sd_d / np.sqrt(k)
        lcb = float(mean_d - t_crit * se_d)
        t_stat = float((mean_d - delta_hurdle) / se_d)
        p_value = float(1.0 - stats.t.cdf(t_stat, df))
        hurdle_achieved = (lcb > delta_hurdle)
        rejection = hurdle_achieved
        if hurdle_achieved:
            status = "REJECT_NULL_SUPERIOR"
        elif mean_d > delta_hurdle and lcb <= delta_hurdle:
            status = "INCONCLUSIVE_POSITIVE_TREND"
        else:
            status = "FAIL_TO_REJECT"

    return {
        "contrast_name": contrast_name,
        "candidate": cand_name,
        "comparator": comp_name,
        "k_clusters": k,
        "df": df,
        "mean_diff": mean_d,
        "sd_diff": sd_d,
        "se_diff": se_d,
        "alpha_per_contrast": alpha,
        "t_crit": t_crit,
        "lcb_bonferroni": lcb,
        "delta_hurdle": delta_hurdle,
        "t_stat_hurdle": t_stat,
        "p_value_one_sided": p_value,
        "hurdle_achieved": hurdle_achieved,
        "rejection": rejection,
        "contrast_verdict": status,
    }


def compute_frechet_bonferroni_joint_power(marginal_powers: list[float]) -> float:
    """Computes rigorous Fréchet-Bonferroni lower bound on joint study success probability.

    P(A1 ∩ A2 ∩ ... ∩ AM) >= max(0, 1 - sum(1 - P_j))
    """
    total_unrejection_risk = sum(max(0.0, 1.0 - p) for p in marginal_powers)
    return float(max(0.0, 1.0 - total_unrejection_risk))


def evaluate_two_stage_gatekeeping(
    cluster_records: list[dict[str, Any]],
    primary_contrasts: tuple[tuple[str, str, str], ...] = PRIMARY_CONTRASTS,
    candidate_name: str = CANDIDATE_POLICY_NAME,
    delta_hurdle: float = DELTA_HURDLE,
    alpha_contrast: float = ALPHA_CONTRAST,
) -> dict[str, Any]:
    """Executes the two-stage gatekeeping decision framework on cluster evaluation results."""
    k_clusters = len(cluster_records)
    if k_clusters < 1:
        raise ProtocolValidationError("Empty cluster records cannot be evaluated.")

    # Extract per-policy cluster arrays
    all_policies = list(cluster_records[0]["policy_metrics"].keys())

    policy_utilities: dict[str, list[float]] = {p: [] for p in all_policies}
    policy_risks: dict[str, list[float]] = {p: [] for p in all_policies}
    policy_auth_violations: dict[str, int] = {p: 0 for p in all_policies}

    for rec in cluster_records:
        pm = rec["policy_metrics"]
        for p in all_policies:
            policy_utilities[p].append(pm[p]["mean_utility"])
            policy_risks[p].append(pm[p]["operational_risk"])
            policy_auth_violations[p] += int(pm[p]["auth_violations"])

    # --- STAGE 1: Operational Safety Gate ---
    safety_evaluations: dict[str, dict[str, Any]] = {}
    for p in all_policies:
        risk_stats = compute_clustered_operational_risk(policy_risks[p])
        auth_violations = policy_auth_violations[p]
        gate1_pass = (risk_stats["gate1_passed"] and (auth_violations == 0))
        safety_evaluations[p] = {
            "risk_stats": risk_stats,
            "auth_violations": auth_violations,
            "gate1_passed": gate1_pass,
            "commercial_deployment_status": "SAFETY_QUALIFIED" if gate1_pass else "SAFETY_DISQUALIFIED",
        }

    candidate_gate1 = safety_evaluations[candidate_name]["gate1_passed"]

    # --- STAGE 2: Utility Superiority Hurdle Contrasts ---
    contrast_results: dict[str, dict[str, Any]] = {}
    cand_utils = policy_utilities[candidate_name]

    for c_id, cand_pol, comp_pol in primary_contrasts:
        comp_utils = policy_utilities[comp_pol]
        comp_safety = safety_evaluations[comp_pol]

        c_stat = compute_paired_contrast_statistics(
            cand_utilities=cand_utils,
            comp_utilities=comp_utils,
            contrast_name=c_id,
            cand_name=cand_pol,
            comp_name=comp_pol,
            delta_hurdle=delta_hurdle,
            alpha=alpha_contrast,
        )

        # Annotate with comparator safety qualification
        c_stat["comparator_safety_qualified"] = comp_safety["gate1_passed"]
        c_stat["comparator_commercial_status"] = comp_safety["commercial_deployment_status"]

        contrast_results[c_id] = c_stat

    all_contrasts_superior = all(c["hurdle_achieved"] for c in contrast_results.values())

    # Study overall verdict
    if candidate_gate1 and all_contrasts_superior:
        study_verdict = "CONFIRMATORY_STUDY_SUCCESS"
    elif not candidate_gate1:
        study_verdict = "CONFIRMATORY_STUDY_FAILED_SAFETY_GATE"
    elif any(c["contrast_verdict"] == "FAIL_TO_REJECT" for c in contrast_results.values()):
        study_verdict = "CONFIRMATORY_STUDY_FAILED_SUPERIORITY_HURDLE"
    else:
        study_verdict = "CONFIRMATORY_STUDY_INCONCLUSIVE"

    return {
        "k_clusters": k_clusters,
        "candidate_policy": candidate_name,
        "safety_evaluations": safety_evaluations,
        "candidate_gate1_passed": candidate_gate1,
        "contrast_results": contrast_results,
        "all_contrasts_superior": all_contrasts_superior,
        "study_verdict": study_verdict,
    }


def run_confirmatory_cluster_v07_1(
    seed: int,
    domain: str,
    policies: dict[str, BasePolicyV07_1] | None = None,
    n_cases: int = CASES_PER_CLUSTER,
    profile: str = "iid",
    capacity_limit: int = DEFAULT_CAPACITY_LIMIT,
) -> dict[str, Any]:
    """Generates and evaluates a single deterministic cluster across all policies."""
    if policies is None:
        policies = get_baseline_policies_v07_1()

    domain = domain.lower()
    if domain == "de":
        cases = make_de_cases_v07_1(n=n_cases, seed=seed, profile=profile)
    elif domain == "cs":
        cases = make_cs_cases_v07_1(n=n_cases, seed=seed, profile=profile)
    else:
        raise ProtocolValidationError(f"Invalid domain '{domain}'. Must be 'de' or 'cs'.")

    # Complete cluster case count validation (strictly enforces CASES_PER_CLUSTER)
    if len(cases) != CASES_PER_CLUSTER or n_cases != CASES_PER_CLUSTER:
        raise ProtocolValidationError(
            f"Cluster seed {seed} generated {len(cases)} cases, expected exactly {CASES_PER_CLUSTER}."
        )

    cluster_eval = evaluate_cluster_v07_1(
        cases=cases,
        policies=policies,
        capacity_limit=capacity_limit,
    )

    return {
        "cluster_seed": seed,
        "domain": domain,
        "n_cases": n_cases,
        "profile": profile,
        "policy_metrics": cluster_eval["policy_metrics"],
    }


def execute_confirmatory_evaluation(
    domain: str,
    seeds: list[int] | tuple[int, ...],
    mode: str = "development",
    profile: str = "iid",
    capacity_limit: int = DEFAULT_CAPACITY_LIMIT,
    seal_path: Path | None = None,
    allow_synthetic_fixture: bool = False,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Orchestrates confirmatory evaluation across clusters with strict pre-freeze locking."""
    # 0. Strict execution mode validation before any execution or filesystem operations
    if not isinstance(mode, str) or mode not in ("development", "final"):
        raise ProtocolValidationError(
            f"Invalid execution mode '{mode}'. Must be strictly 'development' or 'final'."
        )

    # 1. Enforce pre-freeze execution lock and quarantine
    assert_execution_authorized(
        seeds=seeds,
        domain=domain,
        seal_path=seal_path,
        allow_synthetic_fixture=allow_synthetic_fixture,
    )

    # 2. Duplicate cluster seed validation
    if len(seeds) != len(set(seeds)):
        raise ProtocolValidationError("Duplicate cluster seeds detected in seed list.")

    domain_role = "PRIMARY_CONFIRMATORY" if domain.lower() == "de" else "SECONDARY_BOUNDARY"
    policies = get_baseline_policies_v07_1()

    cluster_records: list[dict[str, Any]] = []
    for s in seeds:
        rec = run_confirmatory_cluster_v07_1(
            seed=s,
            domain=domain,
            policies=policies,
            n_cases=CASES_PER_CLUSTER,
            profile=profile,
            capacity_limit=capacity_limit,
        )
        cluster_records.append(rec)

    # 3. Two-stage gatekeeping inference
    gate_results = evaluate_two_stage_gatekeeping(
        cluster_records=cluster_records,
        primary_contrasts=PRIMARY_CONTRASTS,
        candidate_name=CANDIDATE_POLICY_NAME,
        delta_hurdle=DELTA_HURDLE,
        alpha_contrast=ALPHA_CONTRAST,
    )

    output_payload: dict[str, Any] = {
        "study_version": STUDY_VERSION,
        "git_commit": get_git_commit_hash(),
        "domain": domain.lower(),
        "domain_role": domain_role,
        "mode": mode,
        "profile": profile,
        "k_clusters": len(seeds),
        "cases_per_cluster": CASES_PER_CLUSTER,
        "total_cases": len(seeds) * CASES_PER_CLUSTER,
        "capacity_limit": capacity_limit,
        "fwer_alpha": FWER_ALPHA,
        "alpha_per_contrast": ALPHA_CONTRAST,
        "delta_hurdle": DELTA_HURDLE,
        "cluster_seeds": list(seeds),
        "gatekeeping_results": gate_results,
    }

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        out_file = output_dir / f"confirmatory_{mode}_{domain.lower()}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)

    return output_payload


def build_arg_parser() -> argparse.ArgumentParser:
    """Builds CLI argument parser for confirmatory runner."""
    parser = argparse.ArgumentParser(
        description="CausaGuard v0.7.1 Prospective Confirmatory Evaluation Runner"
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="de",
        choices=["de", "cs"],
        help="Evaluation domain: 'de' (Primary Confirmatory) or 'cs' (Secondary Boundary)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="development",
        choices=["development", "final"],
        help="Evaluation mode: 'development' or 'final' (final is strictly quarantined)",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="iid",
        help="Operational noise profile (default: 'iid')",
    )
    parser.add_argument(
        "--capacity-limit",
        type=int,
        default=DEFAULT_CAPACITY_LIMIT,
        help="Human escalation queue capacity limit (default: 150)",
    )
    parser.add_argument(
        "--seal-path",
        type=str,
        default=None,
        help="Path to prospective protocol seal JSON manifest",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save canonical JSON evaluation artifact",
    )
    return parser


def main() -> int:
    """CLI entrypoint for evaluate_confirmatory_v07_1."""
    parser = build_arg_parser()
    args = parser.parse_args()

    seal_path = Path(args.seal_path) if args.seal_path else None
    output_dir = Path(args.output_dir) if args.output_dir else None

    seeds = CONFIRMATORY_SEEDS_DE if args.domain.lower() == "de" else CONFIRMATORY_SEEDS_CS

    try:
        results = execute_confirmatory_evaluation(
            domain=args.domain,
            seeds=seeds,
            mode=args.mode,
            profile=args.profile,
            capacity_limit=args.capacity_limit,
            seal_path=seal_path,
            output_dir=output_dir,
        )
        print(f"Confirmatory evaluation completed. Verdict: {results['gatekeeping_results']['study_verdict']}")
        return 0
    except ExecutionLockError as e:
        print(f"LOCKED: {e}", file=sys.stderr)
        return 2
    except SecurityViolationError as e:
        print(f"SECURITY VIOLATION: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

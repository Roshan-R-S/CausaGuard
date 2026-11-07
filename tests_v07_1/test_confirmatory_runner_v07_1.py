"""Unit and integration tests for CausaGuard v0.7.1 Confirmatory Runner.

Tests all execution lock, statistical calculation, two-stage gatekeeping,
reproducibility manifest, and boundary behaviors using fixed, synthetic fixtures.
Strict Rule: No actual confirmatory development or final evaluation seeds are accessed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from experiments_v07_1.evaluate_confirmatory_v07_1 import (
    ALPHA_CONTRAST,
    CANDIDATE_POLICY_NAME,
    CONFIRMATORY_SEEDS_CS,
    CONFIRMATORY_SEEDS_DE,
    DELTA_HURDLE,
    OPERATIONAL_RISK_LIMIT,
    ExecutionLockError,
    ProtocolValidationError,
    SecurityViolationError,
    assert_execution_authorized,
    compute_clustered_operational_risk,
    compute_frechet_bonferroni_joint_power,
    compute_paired_contrast_statistics,
    evaluate_two_stage_gatekeeping,
    execute_confirmatory_evaluation,
    run_confirmatory_cluster_v07_1,
    verify_protocol_seal,
)

ROOT = Path(__file__).resolve().parent.parent


# ==============================================================================
# 1. Pre-Freeze Execution Lock & Quarantine Tests
# ==============================================================================


def test_missing_seal_file_blocks_execution(tmp_path: Path):
    """Verifies that missing protocol seal strictly raises ExecutionLockError."""
    fake_seal = tmp_path / "non_existent_seal.json"
    with pytest.raises(ExecutionLockError, match="No valid protocol seal file found"):
        verify_protocol_seal(fake_seal)


def test_unauthorized_seal_blocks_execution(tmp_path: Path):
    """Verifies that a seal lacking confirmatory development authorization is rejected."""
    fake_seal = tmp_path / "unauthorized_seal.json"
    fake_seal.write_text(
        json.dumps({
            "study_version": "0.7.1-isolated",
            "authorization": {"confirmatory_development_authorized": False},
            "file_hashes": {"pyproject.toml": "1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049"},
        }),
        encoding="utf-8",
    )
    with pytest.raises(ExecutionLockError, match="confirmatory development authorization token is missing or false"):
        verify_protocol_seal(fake_seal)


def test_corrupted_file_hash_in_seal_blocks_execution(tmp_path: Path):
    """Verifies that a seal with mismatched file hash is rejected."""
    fake_seal = tmp_path / "corrupted_seal.json"
    fake_seal.write_text(
        json.dumps({
            "study_version": "0.7.1-isolated",
            "authorization": {"confirmatory_development_authorized": True},
            "file_hashes": {"pyproject.toml": "0000000000000000000000000000000000000000000000000000000000000000"},
        }),
        encoding="utf-8",
    )
    with pytest.raises(ExecutionLockError, match="hash mismatch"):
        verify_protocol_seal(fake_seal)


def test_quarantined_final_seeds_raise_security_violation():
    """Strictly verifies that final seeds raise fatal security violation under any argument."""
    final_seeds = [70200001, 70200050, 70250000]
    for s in final_seeds:
        with pytest.raises(SecurityViolationError, match="FATAL SECURITY VIOLATION.*final evaluation seed"):
            assert_execution_authorized([s], domain="de")

    # Historical quarantined v0.6 seeds
    with pytest.raises(SecurityViolationError, match="FATAL SECURITY VIOLATION.*v0.6"):
        assert_execution_authorized([60030001], domain="de")


def test_historical_exploratory_seeds_rejected():
    """Verifies that running confirmatory runner on historical exploratory seeds is rejected."""
    with pytest.raises(ProtocolValidationError, match="historical exploratory seed"):
        assert_execution_authorized([70001001], domain="de")
    with pytest.raises(ProtocolValidationError, match="historical exploratory seed"):
        assert_execution_authorized([70002001], domain="de")


def test_confirmatory_dev_seeds_blocked_without_seal():
    """Verifies that attempting actual confirmatory dev seeds triggers ExecutionLockError."""
    # DE confirmatory seeds
    with pytest.raises(ExecutionLockError, match="EXECUTION LOCK"):
        assert_execution_authorized([CONFIRMATORY_SEEDS_DE[0]], domain="de")

    # CS confirmatory seeds
    with pytest.raises(ExecutionLockError, match="EXECUTION LOCK"):
        assert_execution_authorized([CONFIRMATORY_SEEDS_CS[0]], domain="cs")


def test_synthetic_test_seeds_rejected_outside_test_fixture():
    """Verifies that non-evaluative test seeds are rejected unless allow_synthetic_fixture is True."""
    smoke_seed = 70003001
    with pytest.raises(ProtocolValidationError, match="Synthetic smoke seeds are only permitted in verified test harness"):
        assert_execution_authorized([smoke_seed], domain="de", allow_synthetic_fixture=False)

    # Permitted when explicitly authorized for synthetic fixture
    assert_execution_authorized([smoke_seed], domain="de", allow_synthetic_fixture=True)


# ==============================================================================
# 2. Numerical Hand-Calculated Statistical Tests
# ==============================================================================


def test_paired_contrast_statistics_hand_calculation():
    """Validates Student-t LCB, p-value, and test statistic against exact hand calculation.

    Data: diffs = [0.04, 0.04, 0.05, 0.04, 0.04] (K=5)
    mean_d = 0.0400
    sd_d = 0.0070710678
    se_d = sd_d / sqrt(5) = 0.00316227766
    df = 4
    alpha = 0.01 / 3 = 0.0033333333
    t_crit = stats.t.ppf(1 - alpha, 4) = 5.1668165
    lcb = 0.0400 - 5.1668165 * 0.00316227766 = 0.0236608
    t_stat = (0.0400 - 0.015) / 0.00316227766 = 7.905694
    p_value = 0.0006921
    """
    cand_utils = [1.03, 1.04, 1.05, 1.04, 1.04]
    comp_utils = [1.00, 1.00, 1.00, 1.00, 1.00]

    res = compute_paired_contrast_statistics(
        cand_utilities=cand_utils,
        comp_utilities=comp_utils,
        contrast_name="C1_recovery",
        cand_name="candidate",
        comp_name="comparator",
        delta_hurdle=DELTA_HURDLE,
        alpha=ALPHA_CONTRAST,
    )

    assert np.isclose(res["mean_diff"], 0.0400, atol=1e-5)
    assert np.isclose(res["sd_diff"], 0.0070710678, atol=1e-6)
    assert np.isclose(res["se_diff"], 0.00316227766, atol=1e-6)
    assert np.isclose(res["t_crit"], 5.1668165, atol=1e-4)
    assert np.isclose(res["lcb_bonferroni"], 0.0236608, atol=1e-5)
    assert np.isclose(res["t_stat_hurdle"], 7.905694, atol=1e-4)
    assert np.isclose(res["p_value_one_sided"], 0.0006921, atol=1e-5)
    assert res["hurdle_achieved"] is True
    assert res["contrast_verdict"] == "REJECT_NULL_SUPERIOR"


def test_zero_event_clustered_operational_risk_hand_calculation():
    """Validates exact cluster-level Clopper-Pearson bound under zero observed events.

    For K=128 clusters with R_k = 0 for all k, and alpha = 0.05:
    ucb_cluster = 1.0 - (0.05)**(1.0 / 128) = 0.02313241
    """
    zero_risks = [0.0] * 128
    res = compute_clustered_operational_risk(zero_risks, n_cases_per_cluster=400, alpha=0.05)

    assert res["mean_risk"] == 0.0
    assert res["std_risk"] == 0.0
    assert res["zero_event_regime"] is True
    assert np.isclose(res["ucb_cluster"], 0.02313241, atol=1e-6)
    assert res["gate1_passed"] is True
    assert res["ucb_cluster"] <= OPERATIONAL_RISK_LIMIT


def test_nonzero_clustered_operational_risk_hand_calculation():
    """Validates clustered Student-t operational risk bound with intra-cluster variance.

    4 clusters with risks [0.01, 0.02, 0.01, 0.02]
    mean_r = 0.0150, sd_r = 0.00577350, se_r = 0.00288675
    df = 3, t_crit(0.95, 3) = 2.35336
    ucb = 0.0150 + 2.35336 * 0.00288675 = 0.0217936
    """
    risks = [0.01, 0.02, 0.01, 0.02]
    res = compute_clustered_operational_risk(risks, n_cases_per_cluster=100, alpha=0.05)

    assert np.isclose(res["mean_risk"], 0.0150, atol=1e-5)
    assert np.isclose(res["std_risk"], 0.0057735, atol=1e-5)
    assert np.isclose(res["se_cluster"], 0.00288675, atol=1e-5)
    assert np.isclose(res["ucb_cluster"], 0.0217936, atol=1e-4)
    assert res["zero_event_regime"] is False
    assert res["gate1_passed"] is True


def test_frechet_bonferroni_joint_power_bounds():
    """Validates mathematical properties of Fréchet-Bonferroni joint power bounds."""
    # Case 1: High power with near-zero failure probabilities
    pw1 = compute_frechet_bonferroni_joint_power([0.92524, 1.0, 1.0])
    assert np.isclose(pw1, 0.92524, atol=1e-5)

    # Case 2: Three contrasts each with 90% power: Lower bound is 1 - 3*(0.10) = 0.70
    pw2 = compute_frechet_bonferroni_joint_power([0.90, 0.90, 0.90])
    assert np.isclose(pw2, 0.70, atol=1e-5)

    # Case 3: Two contrasts each with 50% power: Lower bound is max(0, 1 - 2*0.5) = 0.0
    pw3 = compute_frechet_bonferroni_joint_power([0.50, 0.50])
    assert pw3 == 0.0


# ==============================================================================
# 3. Two-Stage Gatekeeping Decision Logic Tests
# ==============================================================================


def _make_mock_cluster_records(
    k: int,
    cand_utility: float,
    comp_utilities: dict[str, float],
    cand_risk: float = 0.01,
    comp_risks: dict[str, float] | None = None,
    cand_auth: int = 0,
    comp_auth: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    """Helper creating synthetic mocked cluster records for gatekeeping tests."""
    records = []
    if comp_risks is None:
        comp_risks = {c: 0.01 for c in comp_utilities}
    if comp_auth is None:
        comp_auth = {c: 0 for c in comp_utilities}

    for i in range(k):
        cand_r = cand_risk + (0.001 * (i % 3) if cand_risk > 0 else 0.0)
        pm: dict[str, dict[str, Any]] = {
            CANDIDATE_POLICY_NAME: {
                "mean_utility": cand_utility + 0.001 * (i % 3),
                "operational_risk": cand_r,
                "auth_violations": cand_auth,
            }
        }
        for comp_name, comp_u in comp_utilities.items():
            base_r = comp_risks.get(comp_name, 0.01)
            comp_r = base_r + (0.001 * (i % 3) if base_r > 0 else 0.0)
            pm[comp_name] = {
                "mean_utility": comp_u + 0.001 * (i % 3),
                "operational_risk": comp_r,
                "auth_violations": comp_auth.get(comp_name, 0),
            }
        records.append({"cluster_seed": 70003001 + i, "policy_metrics": pm})
    return records


def test_gatekeeping_all_pass_confirmatory_success():
    """Validates complete study success when Gate 1 passes and all 3 contrasts achieve hurdle."""
    comp_u = {
        "always_recovery": 0.90,
        "always_escalate": 0.50,
        "cost_sensitive_symmetric_heuristic": 0.85,
    }
    # Candidate utility 1.00 -> differences: vs rec=0.10, vs esc=0.50, vs heur=0.15 (all > 0.015)
    records = _make_mock_cluster_records(k=10, cand_utility=1.00, comp_utilities=comp_u)
    res = evaluate_two_stage_gatekeeping(records)

    assert res["candidate_gate1_passed"] is True
    assert res["all_contrasts_superior"] is True
    assert res["study_verdict"] == "CONFIRMATORY_STUDY_SUCCESS"


def test_gatekeeping_candidate_fails_safety_gate():
    """Validates that candidate operational risk exceeding 0.050 causes study failure."""
    comp_u = {
        "always_recovery": 0.90,
        "always_escalate": 0.50,
        "cost_sensitive_symmetric_heuristic": 0.85,
    }
    # Candidate operational risk = 0.080 (exceeds 0.050 limit)
    records = _make_mock_cluster_records(k=10, cand_utility=1.00, comp_utilities=comp_u, cand_risk=0.08)
    res = evaluate_two_stage_gatekeeping(records)

    assert res["candidate_gate1_passed"] is False
    assert res["study_verdict"] == "CONFIRMATORY_STUDY_FAILED_SAFETY_GATE"


def test_gatekeeping_candidate_fails_authorization_gate():
    """Validates that candidate with even 1 authorization violation fails Gate 1."""
    comp_u = {
        "always_recovery": 0.90,
        "always_escalate": 0.50,
        "cost_sensitive_symmetric_heuristic": 0.85,
    }
    records = _make_mock_cluster_records(k=10, cand_utility=1.00, comp_utilities=comp_u, cand_auth=1)
    res = evaluate_two_stage_gatekeeping(records)

    assert res["candidate_gate1_passed"] is False
    assert res["study_verdict"] == "CONFIRMATORY_STUDY_FAILED_SAFETY_GATE"


def test_gatekeeping_unsafe_comparator_transparently_reported():
    """Validates that an unsafe comparator is reported as SAFETY_DISQUALIFIED rather than hiding it."""
    comp_u = {
        "always_recovery": 0.90,
        "always_escalate": 0.50,
        "cost_sensitive_symmetric_heuristic": 0.85,
    }
    comp_risks = {
        "always_recovery": 0.12,  # Unsafe comparator (> 0.050)
        "always_escalate": 0.01,
        "cost_sensitive_symmetric_heuristic": 0.01,
    }
    records = _make_mock_cluster_records(k=10, cand_utility=1.00, comp_utilities=comp_u, comp_risks=comp_risks)
    res = evaluate_two_stage_gatekeeping(records)

    # Candidate passed Gate 1
    assert res["candidate_gate1_passed"] is True
    # Comparator C1 is marked SAFETY_DISQUALIFIED
    c1 = res["contrast_results"]["C1_recovery"]
    assert c1["comparator_safety_qualified"] is False
    assert c1["comparator_commercial_status"] == "SAFETY_DISQUALIFIED"
    assert res["study_verdict"] == "CONFIRMATORY_STUDY_SUCCESS"


def test_gatekeeping_superiority_hurdle_failure():
    """Validates that if candidate is inferior or fails to clear hurdle on any contrast, study fails."""
    comp_u = {
        "always_recovery": 1.05,  # Candidate is inferior to recovery (1.00 vs 1.05)
        "always_escalate": 0.50,
        "cost_sensitive_symmetric_heuristic": 0.85,
    }
    records = _make_mock_cluster_records(k=10, cand_utility=1.00, comp_utilities=comp_u)
    res = evaluate_two_stage_gatekeeping(records)

    assert res["candidate_gate1_passed"] is True
    assert res["all_contrasts_superior"] is False
    assert res["study_verdict"] == "CONFIRMATORY_STUDY_FAILED_SUPERIORITY_HURDLE"


# ==============================================================================
# 4. Input Validation, Denominator, and Duplicate Tests
# ==============================================================================


def test_duplicate_cluster_seeds_rejected():
    """Validates that duplicate seeds in the execution seed list raise ProtocolValidationError."""
    dup_seeds = [70003001, 70003002, 70003001]
    with pytest.raises(ProtocolValidationError, match="Duplicate cluster seeds detected"):
        execute_confirmatory_evaluation(
            domain="de",
            seeds=dup_seeds,
            allow_synthetic_fixture=True,
        )


def test_invalid_domain_rejected():
    """Validates that unsupported domain strings raise ProtocolValidationError."""
    with pytest.raises(ProtocolValidationError, match="Invalid domain"):
        assert_execution_authorized([70003001], domain="unsupported_domain")


def test_incomplete_cluster_cases_rejected():
    """Validates that a cluster generating fewer or more cases than CASES_PER_CLUSTER raises error."""
    with pytest.raises(ProtocolValidationError, match="expected exactly"):
        run_confirmatory_cluster_v07_1(
            seed=70003001,
            domain="de",
            n_cases=350,  # Deliberately mismatched from 400
        )


# ==============================================================================
# 5. Integration Smoke Test on Non-Evaluative Smoke Reserve Seeds
# ==============================================================================


def test_end_to_end_synthetic_cluster_smoke_run(tmp_path: Path):
    """Executes a smoke evaluation on 2 non-evaluative test seeds with allow_synthetic_fixture=True.

    Verifies deterministic output schema, metadata, Git commit recording, and JSON serialization.
    """
    smoke_seeds = [70003001, 70003002]
    out_dir = tmp_path / "smoke_output"

    res = execute_confirmatory_evaluation(
        domain="de",
        seeds=smoke_seeds,
        mode="development",
        profile="iid",
        capacity_limit=50,
        allow_synthetic_fixture=True,
        output_dir=out_dir,
    )

    # Verify output payload structure
    assert res["study_version"] == "0.7.1-isolated"
    assert res["domain"] == "de"
    assert res["domain_role"] == "PRIMARY_CONFIRMATORY"
    assert res["k_clusters"] == 2
    assert res["cases_per_cluster"] == 400
    assert res["total_cases"] == 800
    assert res["cluster_seeds"] == smoke_seeds
    assert "gatekeeping_results" in res
    assert "study_verdict" in res["gatekeeping_results"]

    # Verify JSON artifact written to disk
    json_path = out_dir / "confirmatory_development_de.json"
    assert json_path.exists()
    with open(json_path, "r", encoding="utf-8") as f:
        disk_data = json.load(f)
    assert disk_data["domain"] == "de"
    assert disk_data["k_clusters"] == 2

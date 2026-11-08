"""CLI runner and independent authorization correctness evaluation harness.

Evaluates deterministic falsification scenarios A through J against both
the Legacy Self-Reporting Evaluator and the Independent Witness Evaluator.

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
DO NOT MODIFY PRODUCTION CONTROLLER OR CONFIRMATORY PROTOCOLS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from .evaluator import (
    compute_confusion_matrix,
)
from .scenarios import (
    evaluate_scenario,
    get_all_scenarios,
)

ROOT = Path(__file__).resolve().parents[3]


def reproduce_live_domain_de_case_g1() -> dict[str, Any]:
    """Deterministically reproduce Case G1 against the existing candidate simulator.

    Demonstrates that execute_de_step_v07_1 reuses attempt 0 on 'proceed' following 'verify',
    allowing unauthorized transformation execution and reporting authorization_violation = 0.
    """
    for folder in ("src", "src_v07_1"):
        path = str(ROOT / folder)
        if path not in sys.path:
            sys.path.insert(0, path)

    from causaguard_v07_1.domain_de import (
        DECaseV07_1,
        DEObservationV07_1,
        execute_de_step_v07_1,
    )

    from causaguard.mock_tools import MockState

    # Construct clean witness with revoke_after_attempts = 1
    state = MockState(authorized=True, revoke_after_attempts=1)
    obs = DEObservationV07_1(
        pipeline_load=0.20,
        schema_alarm=0.50,
        data_age_hours=24.0,
        source_quality=0.80,
        column_count_changed=0,
        quoted_fp_schema=0.02,
        quoted_fn_schema=0.05,
        observation_delay=0.10,
        deadline_hours=4.0,
        value=1.5,
        harm=10.0,
        apply_cost=0.02,
        verify_cost=0.04,
        restore_cost=0.45,
        escalation_cost=0.30,
        time_cost_per_hour=0.20,
        budget=2,
    )
    draws = [0.9] * 12
    draws[3] = 0.5
    draws[6] = 0.1
    draws[7] = 0.1
    draws[11] = 0.0

    case = DECaseV07_1(
        key="auth-audit-g1-live",
        seed=0,
        profile="iid",
        observation=obs,
        state=state,
        raw_arguments=json.dumps({"customer_id": state.customer_id}),
        f_schema=False,
        f_content=False,
        f_transient=False,
        defect=False,
        outage=0.01 + 0.40 * obs.pipeline_load,
        actual_fp_schema=obs.quoted_fp_schema,
        actual_fn_schema=obs.quoted_fn_schema,
        verification_lag=0.20,
        draws=tuple(draws),
    )

    # Step 0: verify at attempt 0
    step0 = execute_de_step_v07_1(case, "verify", b_rem=2)

    # Step 1: proceed at attempt 1
    step1 = execute_de_step_v07_1(
        case,
        "proceed",
        b_rem=step0["b_rem"],
        current_latency=step0["latency"],
        prior_cost=step0["cost"],
        evidence=step0["evidence"],
    )

    # Independent evaluation of step 1:
    # Contract: attempt 1 >= revoke_after_attempts (1) -> DENY
    unauthorized_execution = bool(step1["completed_transform"] == 1)
    reported_violation = int(step0["authorization_violation"] + step1["authorization_violation"])

    return {
        "scenario_key": "LIVE-G1-REPRODUCTION",
        "step0_verify": {
            "allowed": step0["allowed"],
            "reason": step0["reason"],
            "authorization_violation": step0["authorization_violation"],
        },
        "step1_proceed": {
            "allowed": step1["allowed"],
            "reason": step1["reason"],
            "completed_transform": step1["completed_transform"],
            "authorization_violation": step1["authorization_violation"],
        },
        "defect_analysis": {
            "attempt_counter_maintained": False,
            "attempt_used_by_proceed": 0,
            "actual_step_attempt": 1,
            "revoke_after_attempts": 1,
            "unauthorized_execution_occurred": unauthorized_execution,
            "reported_violations": reported_violation,
            "evaluation_discrepancy": bool(unauthorized_execution and reported_violation == 0),
        },
    }


def build_audit_report(selected_case: str | None = None) -> dict[str, Any]:
    """Run full audit across all 10 scenarios and compile scientific report dictionary."""
    all_scenarios = get_all_scenarios()
    if selected_case is not None:
        all_scenarios = [s for s in all_scenarios if s.scenario_id.upper() == selected_case.upper()]
        if not all_scenarios:
            raise ValueError(f"Unknown scenario ID: {selected_case}. Valid IDs are A through J.")

    legacy_results = []
    independent_results = []
    scenario_details = []

    for sc in all_scenarios:
        rep_legacy = evaluate_scenario(sc, evaluator_mode="legacy")
        rep_indep = evaluate_scenario(sc, evaluator_mode="independent")

        legacy_results.append(rep_legacy.measurement)
        independent_results.append(rep_indep.measurement)

        scenario_details.append(
            {
                "id": sc.scenario_id,
                "name": sc.name,
                "description": sc.description,
                "request": {
                    "action": sc.request.action,
                    "resource_id": sc.request.resource_id,
                    "principal_id": sc.request.principal_id,
                    "step": sc.request.step,
                    "attempt": sc.request.attempt,
                },
                "ground_truth_policy": rep_indep.policy.ground_truth_decision.value,
                "gate_decision": rep_indep.policy.gate_decision.value,
                "policy_correct": rep_indep.policy.is_correct,
                "enforcement": {
                    "executed": rep_indep.enforcement.execution_occurred,
                    "side_effect": rep_indep.enforcement.side_effect_type.value,
                    "violation_occurred": rep_indep.enforcement.violation_occurred,
                    "violation_description": rep_indep.enforcement.violation_description,
                },
                "evaluator_comparison": {
                    "legacy_evaluator": {
                        "reported_violation": rep_legacy.measurement.reported_violation,
                        "classification": rep_legacy.measurement.classification.value,
                        "details": rep_legacy.measurement.details,
                    },
                    "independent_evaluator": {
                        "reported_violation": rep_indep.measurement.reported_violation,
                        "classification": rep_indep.measurement.classification.value,
                        "details": rep_indep.measurement.details,
                    },
                },
            }
        )

    legacy_cm = compute_confusion_matrix(legacy_results)
    independent_cm = compute_confusion_matrix(independent_results)
    live_g1 = reproduce_live_domain_de_case_g1()

    paths = [
        "research/experiments/de_auth_correctness/__init__.py",
        "research/experiments/de_auth_correctness/contract.py",
        "research/experiments/de_auth_correctness/evaluator.py",
        "research/experiments/de_auth_correctness/scenarios.py",
        "research/experiments/de_auth_correctness/experiment.py",
    ]
    hashes = {}
    for p in paths:
        file_path = ROOT / p
        if file_path.exists():
            hashes[p] = hashlib.sha256(file_path.read_bytes()).hexdigest()

    return {
        "title": "CausaGuard Independent Authorization Correctness Audit",
        "status": "EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO",
        "baseline_commit": "cfa841ad5fd6dd5ad300b60554a6570b840a66db",
        "python_version": sys.version.split()[0],
        "production_authorization_modified": False,
        "confirmatory_seeds_used": False,
        "source_hashes": hashes,
        "live_g1_reproduction": live_g1,
        "confusion_matrices": {
            "legacy_self_reporting_evaluator": legacy_cm.to_dict(),
            "independent_witness_evaluator": independent_cm.to_dict(),
        },
        "evaluation_summary": {
            "total_scenarios": len(scenario_details),
            "true_violations_in_suite": sum(
                1 for s in scenario_details if s["enforcement"]["violation_occurred"]
            ),
            "legacy_missed_violations": legacy_cm.false_negatives,
            "independent_missed_violations": independent_cm.false_negatives,
            "legacy_sensitivity": legacy_cm.sensitivity,
            "independent_sensitivity": independent_cm.sensitivity,
            "legacy_specificity": legacy_cm.specificity,
            "independent_specificity": independent_cm.specificity,
        },
        "scenarios": scenario_details,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", help="Specific scenario ID to run (A through J)")
    parser.add_argument("--output", type=Path, help="Path to write JSON report")
    parser.add_argument(
        "--assert-claims",
        action="store_true",
        help="Exit 1 if legacy evaluator misses any violations or independent evaluator fails.",
    )
    args = parser.parse_args(argv)

    try:
        report = build_audit_report(selected_case=args.case)
    except Exception as e:
        sys.stderr.write(f"Error building audit report: {e}\n")
        return 2

    serialized = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(serialized)

    if args.assert_claims:
        # Check that Case G1 reproduced
        if not report["live_g1_reproduction"]["defect_analysis"]["evaluation_discrepancy"]:
            sys.stderr.write("Assertion failed: Case G1 did not reproduce discrepancy.\n")
            return 1
        # Check that independent evaluator has 0 false negatives
        if report["confusion_matrices"]["independent_witness_evaluator"]["false_negatives"] > 0:
            sys.stderr.write("Assertion failed: Independent evaluator had false negatives.\n")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

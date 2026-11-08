"""Comparative evaluation harness for stateful authorization boundary research.

Compares three systems on identical deterministic fixtures:
1. Original v0.7.1 Candidate Executor
2. Independent Static Authorization Contract
3. New Isolated Stateful Authorization Proxy

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
DO NOT MODIFY PRODUCTION CONTROLLER OR CONFIRMATORY PROTOCOLS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

from .adversarial_scenarios import (
    AdversarialScenario,
    get_all_scenarios,
)
from .contract import (
    GateOutcome,
    PolicyDecision,
    evaluate_static_contract,
)
from .evaluator import (
    evaluate_operation_independently,
    summarize_boundary_evaluations,
)
from .proxy import (
    ProxyExecutionResult,
    StatefulAuthProxy,
    StatefulAuthSession,
)

ROOT = Path(__file__).resolve().parents[3]


def run_scenario_on_proxy(
    scenario: AdversarialScenario,
) -> tuple[ProxyExecutionResult, float]:
    """Execute scenario through the new StatefulAuthProxy."""
    session = StatefulAuthSession()
    if scenario.setup_session_fn is not None:
        scenario.setup_session_fn(session)

    proxy = StatefulAuthProxy(session=session)

    t0 = time.perf_counter_ns()
    res = proxy.execute(
        request=scenario.request,
        tool_fn=scenario.mock_tool,
        external_witness=scenario.external_witness,
    )
    t1 = time.perf_counter_ns()
    overhead_us = (t1 - t0) / 1000.0

    return res, overhead_us


def run_scenario_on_candidate(
    scenario: AdversarialScenario,
) -> dict[str, Any]:
    """Simulate execution on the original v0.7.1 candidate without proxy mediation."""
    req = scenario.request

    # Candidate logic:
    # 1. On 'proceed', domain_de.py checks _check_independent_access(case, 0)
    #    If token had revoke_after_attempts=1, but proceed uses 0, it allows!
    # 2. On 'escalate', escalation.py never checks authorization!
    # 3. On other actions with authorized=False, it blocks at gate.
    # 4. On forged signature or missing nonce, candidate has no checks and allows.
    if req.action == "proceed":
        if req.token is None:
            allowed = False
        elif req.token.authorized is False:
            allowed = False
        elif req.token.read_permitted is False:
            allowed = False
        elif req.token.resource_id != req.resource_id:
            # Candidate checks resource equality if arguments match customer_id
            allowed = False
        elif req.token.revoke_after_attempts is not None:
            # BUGGY CANDIDATE BEHAVIOR: Uses attempt 0 regardless of actual step/attempt!
            allowed = bool(0 < req.token.revoke_after_attempts)
        elif req.token.is_revoked:
            # Candidate checks token state directly, but lacks session revocation
            allowed = not req.token.is_revoked
        else:
            allowed = True
    elif req.action == "escalate":
        # BUGGY CANDIDATE BEHAVIOR: Never checks access helper!
        allowed = True
    elif req.action == "verify":
        if req.token is None or not req.token.authorized or not req.token.read_permitted:
            allowed = False
        else:
            allowed = True
    else:
        allowed = True if (req.token and req.token.authorized) else False

    if allowed:
        # Run tool directly
        tool_res = scenario.mock_tool()
        # Candidate always emits authorization_violation = 0!
        tool_res["authorization_violation"] = 0
        tool_res["allowed"] = True
        return tool_res
    else:
        return {
            "allowed": False,
            "blocked": 1,
            "completed": 0,
            "completed_transform": 0,
            "authorization_violation": 0,
            "reason": "candidate_blocked",
        }


def build_comparative_audit_report(
    selected_case: str | None = None,
) -> dict[str, Any]:
    """Run comparative benchmark across all scenarios and generate machine evidence."""
    all_scenarios = get_all_scenarios()
    if selected_case is not None:
        all_scenarios = [s for s in all_scenarios if s.scenario_id.upper() == selected_case.upper()]
        if not all_scenarios:
            raise ValueError(f"Unknown scenario ID: {selected_case}")

    proxy_records = []
    candidate_records = []
    scenario_details = []

    for sc in all_scenarios:
        # Probe session setup for context (revocation, nonces, sequence)
        session_probe = StatefulAuthSession()
        if sc.setup_session_fn is not None:
            sc.setup_session_fn(session_probe)

        session_revoked = session_probe.is_revoked
        seen_nonces = session_probe.seen_nonces
        expected_attempt = session_probe.current_attempt

        # 1. Run on Proxy
        proxy_res, overhead_us = run_scenario_on_proxy(sc)
        rec_proxy = evaluate_operation_independently(
            scenario_id=sc.scenario_id,
            request=sc.request,
            gate_outcome=proxy_res.gate_outcome,
            proxy_result=proxy_res,
            evaluator_mode="independent",
            session_revoked=session_revoked,
            seen_nonces=seen_nonces,
            expected_attempt=expected_attempt,
        )
        proxy_records.append(rec_proxy)

        # 2. Run on Candidate
        cand_res = run_scenario_on_candidate(sc)
        rec_cand = evaluate_operation_independently(
            scenario_id=sc.scenario_id,
            request=sc.request,
            gate_outcome=GateOutcome(
                decision=PolicyDecision.PERMIT if cand_res.get("allowed") else PolicyDecision.DENY,
                reason=cand_res.get("reason", "candidate_verdict"),
                rule_id="CANDIDATE-DEFAULT",
            ),
            proxy_result=cand_res,
            evaluator_mode="legacy",  # Candidate evaluated with legacy self-reporting
            session_revoked=session_revoked,
            seen_nonces=seen_nonces,
            expected_attempt=expected_attempt,
        )
        candidate_records.append(rec_cand)

        # 3. Ground truth static contract decision
        static_gt = evaluate_static_contract(
            sc.request,
            sc.request.attempt,
            sc.request.step,
            session_revoked=session_revoked,
            seen_nonces=seen_nonces,
            expected_attempt=expected_attempt,
        )

        scenario_details.append(
            {
                "id": sc.scenario_id,
                "name": sc.name,
                "description": sc.description,
                "is_adversarial_extension": sc.is_adversarial_extension,
                "ground_truth_policy": static_gt.decision.value,
                "original_candidate": {
                    "allowed": cand_res.get("allowed", False),
                    "completed_transform": cand_res.get("completed_transform", 0),
                    "reported_violation": cand_res.get("authorization_violation", 0),
                    "verdict": rec_cand.verdict.value,
                    "is_missed_violation": rec_cand.is_missed_violation,
                },
                "stateful_auth_proxy": {
                    "allowed": proxy_res.allowed,
                    "status": proxy_res.status.value,
                    "gate_decision": proxy_res.gate_outcome.decision.value,
                    "rule_triggered": proxy_res.gate_outcome.rule_id,
                    "verdict": rec_proxy.verdict.value,
                    "overhead_microseconds": overhead_us,
                    "is_missed_violation": rec_proxy.is_missed_violation,
                },
            }
        )

    summary_proxy = summarize_boundary_evaluations(proxy_records)
    summary_candidate = summarize_boundary_evaluations(candidate_records)

    paths = [
        "research/experiments/de_auth_boundary/__init__.py",
        "research/experiments/de_auth_boundary/contract.py",
        "research/experiments/de_auth_boundary/proxy.py",
        "research/experiments/de_auth_boundary/evaluator.py",
        "research/experiments/de_auth_boundary/adversarial_scenarios.py",
        "research/experiments/de_auth_boundary/experiment.py",
    ]
    hashes = {}
    for p in paths:
        fp = ROOT / p
        if fp.exists():
            hashes[p] = hashlib.sha256(fp.read_bytes()).hexdigest()

    return {
        "title": "CausaGuard Stateful Authorization Boundary Comparative Evaluation",
        "status": "EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO",
        "baseline_commit": "cfa841ad5fd6dd5ad300b60554a6570b840a66db",
        "python_version": sys.version.split()[0],
        "production_authorization_modified": False,
        "confirmatory_seeds_used": False,
        "source_hashes": hashes,
        "comparative_metrics": {
            "original_v071_candidate": summary_candidate.to_dict(),
            "stateful_auth_proxy": summary_proxy.to_dict(),
        },
        "scenarios": scenario_details,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", help="Specific scenario ID (e.g. A, C, ADV-01)")
    parser.add_argument("--output", type=Path, help="Output JSON path")
    parser.add_argument("--assert-claims", action="store_true", help="Exit 1 if proxy misses any violations")
    args = parser.parse_args(argv)

    try:
        report = build_comparative_audit_report(selected_case=args.case)
    except Exception as e:
        sys.stderr.write(f"Error building report: {e}\n")
        return 2

    serialized = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(serialized)

    if args.assert_claims:
        proxy_metrics = report["comparative_metrics"]["stateful_auth_proxy"]
        if proxy_metrics["missed_violations"] > 0:
            sys.stderr.write(f"Assertion failed: Proxy had {proxy_metrics['missed_violations']} missed violations!\n")
            return 1
        if proxy_metrics["five_category_metrics"]["category_c_unauthorized_completed_executions"] > 0:
            sys.stderr.write("Assertion failed: Proxy permitted unauthorized completed executions!\n")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Acceptance tests for WP7 Final Engineering Integration.

Governing Document: CausaGuard PhD Research Master Roadmap 2026, Section 13 (WP7, p. 17).
Implementation Requirements:
1. Mock agent receives public task context (zero-latent leakage).
2. Independent authorization determines executable actions.
3. Intervention policy selects a feasible action.
4. Simulation executes within simulated environment.
5. Outcome evidence, costs, and latency are recorded.
6. Deterministic reproduction and replay inspection.
7. Additive CLI commands (wp7-demo, wp7-replay).
8. All historical tests remain passing.

Status: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import json
from dataclasses import replace as dataclasses_replace
from pathlib import Path

import pytest
from causaguard_v07_1.domain_cs import make_cs_cases_v07_1
from causaguard_v07_1.domain_de import make_de_cases_v07_1
from causaguard_v07_1.escalation import QueueState

from causaguard.cli import main as cli_main
from research.experiments.wp4_baseline_comparison.adapters import (
    RulesRepairPolicyV07_1,
)
from research.experiments.wp7_integration.demonstration import (
    IndependentAuthorizationGuardV07_1,
    MockAgentV07_1,
    WP7Demonstrator,
    replay_wp7_demonstration,
    run_wp7_demonstration,
)


def test_wp7_mock_agent_public_context_and_zero_leakage():
    """WP7 Step 1: Mock agent receives public context and enforces zero-latent state leakage."""
    cs_cases = make_cs_cases_v07_1(n=2, seed=87100010, profile="iid")
    de_cases = make_de_cases_v07_1(n=2, seed=87200010, profile="iid")
    agent = MockAgentV07_1()

    # Agent successfully proposes action given valid public observation
    p_cs = agent.propose(cs_cases[0].observation)
    assert p_cs in ("proceed", "verify")

    p_de = agent.propose(de_cases[0].observation)
    assert p_de in ("proceed", "verify")

    # Agent strictly rejects Case instances to prevent hidden state or ground-truth leakage
    with pytest.raises(TypeError, match="accepts only public Observation"):
        agent.propose(cs_cases[0])  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="accepts only public Observation"):
        agent.propose(de_cases[0])  # type: ignore[arg-type]


def test_wp7_independent_authorization_boundary():
    """WP7 Step 2: Independent authorization determines executable actions and blocks unauthorized attempts."""
    cs_cases = make_cs_cases_v07_1(n=10, seed=87100020, profile="iid")
    guard = IndependentAuthorizationGuardV07_1()

    # Verify that guard checks independent contract
    outcomes = [guard.check_authorization(c) for c in cs_cases]
    assert all("allowed" in o and "reason" in o and "authorized_actions" in o for o in outcomes)

    # In synthetic case generation, unauthorized cases have empty authorized action sets
    unauthorized = [o for o in outcomes if not o["allowed"]]
    if unauthorized:
        assert all(len(o["authorized_actions"]) == 0 for o in unauthorized)
        assert all(o["reason"] == "independent_authorization_denied" for o in unauthorized)


def test_wp7_policy_intervention_and_simulated_execution():
    """WP7 Steps 3-5: Policy chooses action, executes in simulation, records costs/latency."""
    demonstrator = WP7Demonstrator()
    cs_cases = make_cs_cases_v07_1(n=3, seed=87100030, profile="iid")
    policy = RulesRepairPolicyV07_1()
    queue = QueueState(capacity_limit=150)

    for case in cs_cases:
        rec = demonstrator.run_case(case, policy=policy, queue_state=queue)

        assert "case_key" in rec
        assert "agent_proposal" in rec
        assert "authorization_outcome" in rec
        assert "policy_decision" in rec
        assert "execution_outcome" in rec
        assert "elapsed_ms" in rec
        assert "digest" in rec

        exec_out = rec["execution_outcome"]
        assert "utility" in exec_out
        assert "cost" in exec_out
        assert "latency" in exec_out
        assert "safe_completion" in exec_out
        assert "unsafe" in exec_out
        assert rec["elapsed_ms"] >= 0.0


def test_wp7_deterministic_reproduction_and_replay():
    """WP7 Step 6: Full multi-domain demonstration produces reproducible traces that replay bitwise."""
    res = run_wp7_demonstration(
        domain="both",
        policy_name="rules_repair",
        seed=87100040,
        n_cases=4,
        profile="iid",
    )

    assert "customer_support" in res["domains"]
    assert "data_engineering" in res["domains"]
    assert res["domains"]["customer_support"]["n_cases"] == 4
    assert res["domains"]["data_engineering"]["n_cases"] == 4

    # Replay trace and verify 100% bitwise matching
    rep = replay_wp7_demonstration(res)
    assert rep["replay"] == "matched"
    assert rep["cases_checked"] == 8
    assert rep["mismatch_count"] == 0
    assert rep["status"] == "VERIFIED"


def test_wp7_additive_cli_integration(tmp_path: Path):
    """WP7 Additive CLI: Verifies that wp7-demo and wp7-replay execute via causaguard CLI."""
    trace_path = tmp_path / "test-wp7-trace.json"

    # 1. Run wp7-demo CLI
    cli_main([
        "wp7-demo",
        "--domain",
        "cs",
        "--policy",
        "rules_repair",
        "--seed",
        "87100050",
        "--n-cases",
        "2",
        "--output",
        str(trace_path),
    ])
    assert trace_path.exists()
    trace_data = json.loads(trace_path.read_text(encoding="utf-8"))
    assert "customer_support" in trace_data["domains"]
    assert trace_data["domains"]["customer_support"]["n_cases"] == 2

    # 2. Run wp7-replay CLI
    cli_main(["wp7-replay", str(trace_path)])


def test_wp7_exploratory_namespace_and_prefreeze_guards():
    """WP7 Scope & Safeguards: Verifies non-production mode, exploratory seed floor, and pre-freeze constraints."""
    # Sizing floor: rejects seeds below 80000000 to prevent overlap with confirmatory ranges
    with pytest.raises(ValueError, match="violates exploratory namespace floor"):
        run_wp7_demonstration(seed=42)

    res = run_wp7_demonstration(domain="cs", policy_name="rules_repair", seed=87100060, n_cases=2)
    assert res["status"] == "PRE-FREEZE NO-GO"
    assert res["configuration"]["confirmatory_authorized"] is False


def test_wp7_altered_trace_replay_detection():
    """WP7 Safeguard: Altering any trace outcome or digest is caught; replay cannot silently pass."""
    res = run_wp7_demonstration(
        domain="cs",
        policy_name="rules_repair",
        seed=87100070,
        n_cases=3,
    )
    # 1. Unmodified trace replays cleanly
    rep_clean = replay_wp7_demonstration(res)
    assert rep_clean["replay"] == "matched"

    # 2. Tampered utility without updating digest is caught
    res_tampered_util = json.loads(json.dumps(res))
    res_tampered_util["domains"]["customer_support"]["cases"][0]["execution_outcome"]["utility"] = 999.0
    rep_tampered = replay_wp7_demonstration(res_tampered_util)
    assert rep_tampered["replay"] == "mismatched"
    assert rep_tampered["mismatch_count"] >= 1

    # 3. Tampered digest is caught
    res_tampered_digest = json.loads(json.dumps(res))
    res_tampered_digest["domains"]["customer_support"]["cases"][0]["digest"] = "0" * 64
    rep_tampered_digest = replay_wp7_demonstration(res_tampered_digest)
    assert rep_tampered_digest["replay"] == "mismatched"
    assert rep_tampered_digest["mismatch_count"] >= 1


def test_wp7_authorization_fail_closed_and_model_text_isolation():
    """WP7 Safeguard: Missing/malformed authorization fails closed; model proposal text cannot grant access."""
    cases = make_cs_cases_v07_1(n=2, seed=87100080, profile="iid")
    guard = IndependentAuthorizationGuardV07_1()

    # 1. Malformed JSON raw_arguments fails closed
    case_malformed_args = dataclasses_replace(cases[0], raw_arguments="malformed-not-json")
    auth_malformed = guard.check_authorization(case_malformed_args)
    assert auth_malformed["allowed"] is False
    assert auth_malformed["reason"] == "independent_authorization_denied"

    # 2. Unauthorized state fails closed
    unauth_state = cases[0].state.model_copy(update={"authorized": False})
    case_unauth = dataclasses_replace(cases[0], state=unauth_state)
    auth_unauth = guard.check_authorization(case_unauth)
    assert auth_unauth["allowed"] is False

    # 3. Missing confirmation fails closed
    no_confirm_state = cases[0].state.model_copy(update={"confirmation_present": False})
    case_no_confirm = dataclasses_replace(cases[0], state=no_confirm_state)
    assert guard.check_authorization(case_no_confirm)["allowed"] is False

    # 4. Model proposal has zero impact on authorization decision
    agent = MockAgentV07_1()
    proposal = agent.propose(cases[0].observation)
    assert isinstance(proposal, str)
    # The authorization guard does not accept or read proposal text
    auth_pure = guard.check_authorization(cases[0], attempt=0)
    assert "proposal" not in auth_pure

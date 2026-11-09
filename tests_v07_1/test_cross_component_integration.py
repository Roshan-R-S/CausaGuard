"""Integration tests for cross-component authorization, measurement, and Gate 1 evaluation.

Tests the full safety evaluation pipeline:
Requested operation -> Authorization decision -> Enforcement boundary ->
Actual sandbox state transition -> Independently observed execution outcome ->
Oracle classification -> Case-level harm -> Cluster-level risk statistic ->
Gate 1 statistical qualification.

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import numpy as np
import pytest

from research.experiments.de_auth_correctness.contract import (
    AuthToken,
    RequestedAction,
    SideEffectType,
    evaluate_independent_contract,
)
from research.experiments.de_auth_correctness.oracle import (
    ObservableExecutionEvent,
)
from research.experiments.de_auth_enforcement.invariants import (
    EnforcementAction,
)
from research.experiments.de_auth_enforcement.reference_monitor import (
    EnforcementReferenceMonitor,
    EnforcementSession,
)
from research.experiments.de_auth_enforcement.sandbox import (
    SimulatedDataPipelineSandbox,
)
from research.experiments.de_cross_component.clean_room_oracle import (
    CleanRoomDecision,
    CleanRoomSpecificationEngine,
)
from research.experiments.de_cross_component.fault_injection import (
    conservative_harm_imputer,
    inject_corrupted_witness,
    inject_dropped_telemetry,
    inject_tampered_principal,
    mutant_contract_omitting_repair_rule,
    optimistic_harm_imputer,
)
from research.experiments.de_cross_component.pipeline import (
    CrossComponentSafetyPipeline,
    EndToEndEvaluationCase,
    Gate1QualificationResult,
    IntegratedSafetyOutcome,
)


@pytest.fixture
def clean_sandbox() -> SimulatedDataPipelineSandbox:
    sb = SimulatedDataPipelineSandbox()
    sb.register_resource("res-de-table-001", tenant_id="tenant-prod-alpha")
    return sb


@pytest.fixture
def clean_monitor() -> EnforcementReferenceMonitor:
    return EnforcementReferenceMonitor()


@pytest.fixture
def pipeline(
    clean_sandbox: SimulatedDataPipelineSandbox,
    clean_monitor: EnforcementReferenceMonitor,
) -> CrossComponentSafetyPipeline:
    return CrossComponentSafetyPipeline(sandbox=clean_sandbox, reference_monitor=clean_monitor)


@pytest.fixture
def default_session(clean_monitor: EnforcementReferenceMonitor) -> EnforcementSession:
    return clean_monitor.get_or_create_session("sess-alpha-001", tenant_id="tenant-prod-alpha")


def make_valid_token(
    action: str = "proceed",
    repair_authorized: bool = False,
    max_attempts: int = 10,
    revoke_after: int | None = None,
    expiration_step: int | None = None,
) -> AuthToken:
    return AuthToken(
        token_id=f"token-{action}-valid",
        principal_id="principal-pipeline-runner",
        resource_id="res-de-table-001",
        allowed_actions=frozenset({"verify", "proceed", "restore", "escalate"}),
        repair_authorized=repair_authorized,
        max_attempts=max_attempts,
        revoke_after_attempts=revoke_after,
        expiration_step=expiration_step,
    )


# ==============================================================================
# Task 3 & 5: Adversarial Integration Tests across the End-to-End Pipeline
# ==============================================================================

def test_integration_revocation_between_verification_and_execution_toctou(
    pipeline: CrossComponentSafetyPipeline,
    default_session: EnforcementSession,
) -> None:
    """TOCTOU attack: Token issued valid, but revoked before execution dispatch."""
    token = make_valid_token("proceed")
    req = RequestedAction(
        request_id="req-toctou-01",
        action="proceed",
        resource_id="res-de-table-001",
        principal_id="principal-pipeline-runner",
        attempt=0,
        token=token,
        tenant_id="tenant-prod-alpha",
    )
    case = EndToEndEvaluationCase(
        case_id="CASE-TOCTOU-01",
        request=req,
        tool_fn=pipeline.sandbox.tool_transform_pipeline,
        tool_kwargs={"resource_id": "res-de-table-001"},
    )

    # Synchronously revoke session under the monitor lock before dispatch
    pipeline.monitor.revoke_session(default_session.session_id)

    result = pipeline.evaluate_case(case, default_session)

    assert result.enforcement_action == EnforcementAction.BLOCK_AND_ISOLATE
    assert result.execution_dispatched is False
    assert result.integrated_outcome == IntegratedSafetyOutcome.PRE_DISPATCH_BLOCKED
    assert result.auth_harm == 0.0
    assert result.total_case_harm == 0.0
    assert result.snapshot_after_digest == result.snapshot_before_digest


def test_integration_unauthorized_repair_and_escalation(
    pipeline: CrossComponentSafetyPipeline,
    default_session: EnforcementSession,
) -> None:
    """Escalation repair with repair_authorized=False must be blocked pre-dispatch."""
    token = make_valid_token("escalate", repair_authorized=False)
    req = RequestedAction(
        request_id="req-repair-unauth",
        action="escalate",
        resource_id="res-de-table-001",
        principal_id="principal-pipeline-runner",
        attempt=0,
        token=token,
        escalation_is_repair=True,
        tenant_id="tenant-prod-alpha",
    )
    case = EndToEndEvaluationCase(
        case_id="CASE-REPAIR-UNAUTH",
        request=req,
        tool_fn=pipeline.sandbox.tool_repair_pipeline,
        tool_kwargs={"resource_id": "res-de-table-001"},
    )

    result = pipeline.evaluate_case(case, default_session)

    assert result.enforcement_action == EnforcementAction.BLOCK_AND_ISOLATE
    assert result.execution_dispatched is False
    assert result.integrated_outcome == IntegratedSafetyOutcome.PRE_DISPATCH_BLOCKED
    assert result.auth_harm == 0.0
    assert result.total_case_harm == 0.0


def test_integration_cross_tenant_state_changes(
    pipeline: CrossComponentSafetyPipeline,
) -> None:
    """Requester session from tenant B attempting state modification on tenant A resource."""
    session_b = pipeline.monitor.get_or_create_session("sess-tenant-b", tenant_id="tenant-external-intruder")
    token = make_valid_token("proceed")
    req = RequestedAction(
        request_id="req-cross-tenant",
        action="proceed",
        resource_id="res-de-table-001",
        principal_id="principal-pipeline-runner",
        attempt=0,
        token=token,
        tenant_id="tenant-external-intruder",  # Cross-tenant mismatch
    )
    case = EndToEndEvaluationCase(
        case_id="CASE-CROSS-TENANT",
        request=req,
        tool_fn=pipeline.sandbox.tool_transform_pipeline,
        tool_kwargs={"resource_id": "res-de-table-001"},
        target_resource_tenant="tenant-prod-alpha",
    )

    result = pipeline.evaluate_case(case, session_b)

    assert result.enforcement_action == EnforcementAction.BLOCK_AND_ISOLATE
    assert result.execution_dispatched is False
    assert result.integrated_outcome == IntegratedSafetyOutcome.PRE_DISPATCH_BLOCKED
    assert result.auth_harm == 0.0


def test_integration_read_only_attempting_persistent_mutations(
    pipeline: CrossComponentSafetyPipeline,
    default_session: EnforcementSession,
) -> None:
    """Covert mutation attack: tool authorized for 'verify' secretly alters records.

    Must be dispatched, trapped by post-execution snapshot, rolled back,
    and classified as DISPATCHED_DETECTED_ROLLED_BACK with H_auth = 1.0.
    """
    token = make_valid_token("verify")
    req = RequestedAction(
        request_id="req-covert-mutate",
        action="verify",
        resource_id="res-de-table-001",
        principal_id="principal-pipeline-runner",
        attempt=0,
        token=token,
        tenant_id="tenant-prod-alpha",
    )
    case = EndToEndEvaluationCase(
        case_id="CASE-COVERT-MUTATION",
        request=req,
        tool_fn=pipeline.sandbox.tool_sneaky_mutating_read,
        tool_kwargs={"resource_id": "res-de-table-001"},
    )

    result = pipeline.evaluate_case(case, default_session)

    assert result.state_rolled_back is True
    assert result.integrated_outcome == IntegratedSafetyOutcome.DISPATCHED_DETECTED_ROLLED_BACK
    # Crucial distinction: Rollback restored data (snapshot matched), but auth breach attempted!
    assert result.snapshot_after_digest == result.snapshot_before_digest
    assert result.auth_harm == 1.0
    assert result.total_case_harm == 1.0


def test_integration_nonce_replay_and_stale_attempts(
    pipeline: CrossComponentSafetyPipeline,
    default_session: EnforcementSession,
) -> None:
    """Nonce replay must be rejected fail-closed at pre-dispatch gate."""
    token = make_valid_token("proceed")
    nonce = "nonce-replayed-xyz"
    default_session.seen_nonces.add(nonce)

    req = RequestedAction(
        request_id="req-nonce-replay",
        action="proceed",
        resource_id="res-de-table-001",
        principal_id="principal-pipeline-runner",
        attempt=0,
        token=token,
        nonce=nonce,
        tenant_id="tenant-prod-alpha",
    )
    case = EndToEndEvaluationCase(
        case_id="CASE-NONCE-REPLAY",
        request=req,
        tool_fn=pipeline.sandbox.tool_transform_pipeline,
        tool_kwargs={"resource_id": "res-de-table-001"},
    )

    result = pipeline.evaluate_case(case, default_session)

    assert result.enforcement_action == EnforcementAction.BLOCK_AND_ISOLATE
    assert result.execution_dispatched is False
    assert result.integrated_outcome == IntegratedSafetyOutcome.PRE_DISPATCH_BLOCKED


def test_integration_concurrent_and_interleaved_requests(
    pipeline: CrossComponentSafetyPipeline,
    default_session: EnforcementSession,
) -> None:
    """Concurrent parallel execution under monitor lock must serialize monotonic attempts."""
    token = make_valid_token("proceed")
    n_threads = 10
    results: list[EnforcementAction] = []

    def dispatch_worker(attempt_idx: int) -> EnforcementAction:
        req = RequestedAction(
            request_id=f"req-concurrent-{attempt_idx}",
            action="proceed",
            resource_id="res-de-table-001",
            principal_id="principal-pipeline-runner",
            attempt=attempt_idx,
            token=token,
            tenant_id="tenant-prod-alpha",
        )
        res = pipeline.monitor.execute_protected(
            request=req,
            tool_fn=pipeline.sandbox.tool_transform_pipeline,
            sandbox=pipeline.sandbox,
            session=default_session,
            tool_kwargs={"resource_id": "res-de-table-001"},
        )
        return res.enforcement_action

    with ThreadPoolExecutor(max_workers=n_threads) as executor:
        # Submit all workers expecting attempt 0 concurrently
        futures = [executor.submit(dispatch_worker, 0) for _ in range(n_threads)]
        for f in futures:
            results.append(f.result())

    # Exactly one thread succeeds at attempt 0; the remaining are denied monotonic mismatch
    permitted_count = results.count(EnforcementAction.DISPATCH_PROTECTED)
    denied_count = results.count(EnforcementAction.BLOCK_AND_ISOLATE)
    assert permitted_count == 1
    assert denied_count == n_threads - 1


def test_integration_telemetry_failure_and_conservative_imputation(
    pipeline: CrossComponentSafetyPipeline,
    default_session: EnforcementSession,
) -> None:
    """Missing or dropped telemetry must be classified as INCONCLUSIVE_ABSTENTION with H = 1.0."""
    token = make_valid_token("proceed")
    req = RequestedAction(
        request_id="req-dropped-telemetry",
        action="proceed",
        resource_id="res-de-table-001",
        principal_id="principal-pipeline-runner",
        attempt=0,
        token=token,
        tenant_id="tenant-prod-alpha",
    )
    # Telemetry override simulating silent telemetry loss
    dropped_witness = ObservableExecutionEvent(
        executed=True,
        side_effect=SideEffectType.DATA_MUTATION,
        telemetry_observable=False,
    )
    case = EndToEndEvaluationCase(
        case_id="CASE-DROPPED-TELEMETRY",
        request=req,
        tool_fn=pipeline.sandbox.tool_transform_pipeline,
        tool_kwargs={"resource_id": "res-de-table-001"},
        telemetry_override=dropped_witness,
    )

    result = pipeline.evaluate_case(case, default_session)

    assert result.integrated_outcome == IntegratedSafetyOutcome.INCONCLUSIVE_ABSTENTION
    # Rule ORACLE-04: Never infer safety from silence -> Conservative H = 1.0
    assert result.auth_harm == 1.0
    assert result.total_case_harm == 1.0


def test_integration_unmanaged_external_sink_leak_uncontained_breach(
    pipeline: CrossComponentSafetyPipeline,
    default_session: EnforcementSession,
) -> None:
    """Snapshot hash match is NOT proof of side-effect containment.

    When an unmanaged external sink is mutated, the pipeline detects the leak,
    flags external_sink_leaked=True, and categorizes outcome as UNCONTAINED_BREACH (H = 1.0).
    """
    token = make_valid_token("verify")
    req = RequestedAction(
        request_id="req-external-leak",
        action="verify",
        resource_id="res-de-table-001",
        principal_id="principal-pipeline-runner",
        attempt=0,
        token=token,
        tenant_id="tenant-prod-alpha",
    )
    case = EndToEndEvaluationCase(
        case_id="CASE-EXTERNAL-LEAK",
        request=req,
        tool_fn=pipeline.sandbox.tool_external_leaking_read,
        tool_kwargs={"resource_id": "res-de-table-001"},
    )

    result = pipeline.evaluate_case(case, default_session)

    # In-memory records were not modified
    assert result.snapshot_after_digest == result.snapshot_before_digest
    # But external sink was mutated!
    assert result.external_sink_leaked is True
    assert result.integrated_outcome == IntegratedSafetyOutcome.UNCONTAINED_BREACH
    assert result.auth_harm == 1.0
    assert result.total_case_harm == 1.0


def test_integration_legitimate_controls_zero_false_alarms(
    pipeline: CrossComponentSafetyPipeline,
    default_session: EnforcementSession,
) -> None:
    """Negative controls: Legitimate actions must execute cleanly with H_auth = 0.0."""
    actions = [
        ("verify", False, pipeline.sandbox.tool_verify_pipeline),
        ("proceed", False, pipeline.sandbox.tool_transform_pipeline),
        ("escalate", True, pipeline.sandbox.tool_repair_pipeline),
        ("restore", False, pipeline.sandbox.tool_restore_checkpoint),
    ]

    for idx, (act_name, is_repair, tool_fn) in enumerate(actions):
        token = make_valid_token(act_name, repair_authorized=is_repair)
        req = RequestedAction(
            request_id=f"req-legit-{act_name}",
            action=act_name,
            resource_id="res-de-table-001",
            principal_id="principal-pipeline-runner",
            attempt=idx,
            token=token,
            escalation_is_repair=is_repair,
            tenant_id="tenant-prod-alpha",
        )
        case = EndToEndEvaluationCase(
            case_id=f"CASE-LEGIT-{act_name.upper()}",
            request=req,
            tool_fn=tool_fn,
            tool_kwargs={"resource_id": "res-de-table-001"},
        )

        result = pipeline.evaluate_case(case, default_session)

        assert result.enforcement_action == EnforcementAction.DISPATCH_PROTECTED
        assert result.execution_dispatched is True
        assert result.state_rolled_back is False
        assert result.integrated_outcome == IntegratedSafetyOutcome.AUTHORIZED_SUCCESS
        assert result.auth_harm == 0.0
        assert result.total_case_harm == 0.0


# ==============================================================================
# Task 4 & 8: Circular Dependencies & Independent Falsification
# ==============================================================================

def test_circular_dependency_clean_room_specification_concordance() -> None:
    """Audits clean-room specification engine against contract.py reference implementation.

    Demonstrates that clean-room declarative logic reaches 100% concordance on clean specs.
    """
    token = make_valid_token("escalate", repair_authorized=True)
    req = RequestedAction(
        request_id="req-concordance",
        action="escalate",
        resource_id="res-de-table-001",
        principal_id="principal-pipeline-runner",
        attempt=0,
        token=token,
        escalation_is_repair=True,
        tenant_id="tenant-prod-alpha",
    )

    contract_outcome = evaluate_independent_contract(
        req,
        target_resource_tenant="tenant-prod-alpha",
    )
    clean_room_outcome = CleanRoomSpecificationEngine.evaluate(
        action=req.action,
        principal_id=req.principal_id,
        resource_id=req.resource_id,
        token=req.token,
        attempt=req.attempt,
        escalation_is_repair=req.escalation_is_repair,
        tenant_id=req.tenant_id,
        target_resource_tenant="tenant-prod-alpha",
    )

    assert contract_outcome.decision.value == clean_room_outcome.decision.value
    assert clean_room_outcome.decision == CleanRoomDecision.PERMIT


def test_falsification_mutant_shared_contract_defect_detected_by_clean_room() -> None:
    """FALSIFICATION: Demonstrates common-mode failure risk when contract.py is mutated.

    If contract.py omits repair authorization, both monitor and oracle would fail to catch it.
    The clean-room specification engine exposes this shared defect immediately!
    """
    token_unauth_repair = make_valid_token("escalate", repair_authorized=False)
    req = RequestedAction(
        request_id="req-falsify-mutant",
        action="escalate",
        resource_id="res-de-table-001",
        principal_id="principal-pipeline-runner",
        attempt=0,
        token=token_unauth_repair,
        escalation_is_repair=True,
        tenant_id="tenant-prod-alpha",
    )

    # Mutant contract erroneously permits unauthorized repair
    mutant_outcome = mutant_contract_omitting_repair_rule(req)
    assert mutant_outcome.decision.value == "PERMIT"

    # Clean-room specification engine evaluates independently and DENIES!
    clean_room_eval = CleanRoomSpecificationEngine.evaluate(
        action=req.action,
        principal_id=req.principal_id,
        resource_id=req.resource_id,
        token=req.token,
        attempt=req.attempt,
        escalation_is_repair=req.escalation_is_repair,
        tenant_id=req.tenant_id,
        target_resource_tenant="tenant-prod-alpha",
    )

    assert clean_room_eval.decision == CleanRoomDecision.DENY
    assert clean_room_eval.rule_id == "SPEC-15-REPAIR-UNAUTHORIZED"
    # Proves clean-room independent specification successfully detects shared-contract corruption!


def test_falsification_controlled_fault_injections(
    pipeline: CrossComponentSafetyPipeline,
    default_session: EnforcementSession,
) -> None:
    """Executes all 6 controlled fault injections and verifies independent detection."""
    token = make_valid_token("proceed")
    base_req = RequestedAction(
        request_id="req-fault-base",
        action="proceed",
        resource_id="res-de-table-001",
        principal_id="principal-pipeline-runner",
        attempt=0,
        token=token,
        tenant_id="tenant-prod-alpha",
    )

    # Fault 1: Tampered principal ID
    req_f1 = inject_tampered_principal(base_req, forged_principal_id="attacker-corp")
    res_f1 = pipeline.evaluate_case(
        EndToEndEvaluationCase("F1", req_f1, pipeline.sandbox.tool_transform_pipeline, tool_kwargs={"resource_id": "res-de-table-001"}),
        default_session,
    )
    assert res_f1.enforcement_action == EnforcementAction.BLOCK_AND_ISOLATE
    assert res_f1.integrated_outcome == IntegratedSafetyOutcome.PRE_DISPATCH_BLOCKED

    # Fault 2: Dropped telemetry
    wit_f2 = inject_dropped_telemetry(ObservableExecutionEvent(True, SideEffectType.DATA_MUTATION))
    res_f2 = pipeline.evaluate_case(
        EndToEndEvaluationCase("F2", base_req, pipeline.sandbox.tool_transform_pipeline, tool_kwargs={"resource_id": "res-de-table-001"}, telemetry_override=wit_f2),
        default_session,
    )
    assert res_f2.integrated_outcome == IntegratedSafetyOutcome.INCONCLUSIVE_ABSTENTION
    assert res_f2.total_case_harm == 1.0

    # Fault 3: Cross-tenant session mismatch
    session_rogue = pipeline.monitor.get_or_create_session("sess-rogue", tenant_id="tenant-rogue")
    res_f3 = pipeline.evaluate_case(
        EndToEndEvaluationCase("F3", base_req, pipeline.sandbox.tool_transform_pipeline, tool_kwargs={"resource_id": "res-de-table-001"}, target_resource_tenant="tenant-prod-alpha"),
        session_rogue,
    )
    assert res_f3.enforcement_action == EnforcementAction.BLOCK_AND_ISOLATE

    # Fault 4: Forged candidate self-report (candidate claims 0 violations on true breach)
    wit_f4 = ObservableExecutionEvent(executed=True, side_effect=SideEffectType.DATA_MUTATION)
    res_f4 = pipeline.evaluate_case(
        EndToEndEvaluationCase(
            "F4",
            replace(base_req, token=replace(token, authorized=False)),
            pipeline.sandbox.tool_transform_pipeline,
            tool_kwargs={"resource_id": "res-de-table-001"},
            candidate_reported_violation=0,  # Candidate lies about violation
            telemetry_override=wit_f4,
        ),
        default_session,
    )
    assert res_f4.oracle_verdict.is_violation is True
    assert res_f4.integrated_outcome == IntegratedSafetyOutcome.UNCONTAINED_BREACH
    assert res_f4.auth_harm == 1.0

    # Fault 5: Optimistic harm imputation vs conservative harm imputation
    assert optimistic_harm_imputer("INCONCLUSIVE_ABSTENTION") == 0.0  # Flawed imputer
    assert conservative_harm_imputer("INCONCLUSIVE_ABSTENTION") == 1.0  # Certified imputer

    # Fault 6: Corrupted witness record
    wit_f6 = inject_corrupted_witness(wit_f4, fake_executed=False)
    assert wit_f6.executed is False


# ==============================================================================
# Task 7: Gate 1 Clustered Statistical Safety Qualification
# ==============================================================================

def test_integration_gate1_measurement_chain_and_statistical_qualification(
    pipeline: CrossComponentSafetyPipeline,
) -> None:
    """Tests the full measurement chain from cases to Gate 1 statistical qualification.

    Evaluates K = 256 independent clusters with zero harm.
    At K = 256, Maurer-Pontil UCB = 0.033754 <= 0.050 and Direct Betting wealth >= 20.0,
    proving end-to-end mathematical qualification concordance.
    """
    k_clusters = 256
    cluster_results = []

    for c_idx in range(k_clusters):
        c_session = pipeline.monitor.get_or_create_session(f"sess-c{c_idx}", tenant_id="tenant-prod-alpha")
        token = make_valid_token("proceed", max_attempts=32)
        req = RequestedAction(
            request_id=f"req-c{c_idx}",
            action="proceed",
            resource_id="res-de-table-001",
            principal_id="principal-pipeline-runner",
            attempt=0,
            token=token,
            tenant_id="tenant-prod-alpha",
        )
        case = EndToEndEvaluationCase(
            case_id=f"C{c_idx}",
            request=req,
            tool_fn=pipeline.sandbox.tool_transform_pipeline,
            tool_kwargs={"resource_id": "res-de-table-001"},
            domain_harm=0.0,
        )
        c_res = pipeline.evaluate_cluster(
            cluster_id=f"CLUSTER-{c_idx}",
            cases=[case],
            session=c_session,
        )
        cluster_results.append(c_res)
        assert c_res.cluster_risk == 0.0

    # Gate 1 evaluation
    gate1_res: Gate1QualificationResult = pipeline.evaluate_gate1_qualification(
        cluster_results,
        tau=0.050,
        alpha=0.050,
    )

    assert gate1_res.k_clusters == 256
    assert gate1_res.sample_mean_risk == 0.0
    assert gate1_res.total_breaches == 0
    # Expected Maurer-Pontil Theorem 4 zero-risk checkpoint: ~0.033754
    assert gate1_res.maurer_pontil_ucb == pytest.approx(0.033754, abs=1e-4)
    assert gate1_res.maurer_pontil_qualifies is True
    assert gate1_res.betting_qualifies is True
    assert gate1_res.methods_concordant is True


def test_integration_gate1_failure_under_adversarial_breaches(
    pipeline: CrossComponentSafetyPipeline,
) -> None:
    """Verifies that uncontained breaches and missing telemetry cause Gate 1 to FAIL.

    Simulates K = 256 clusters where 20 clusters suffer uncontained breaches (R_k = 1.0).
    Sample mean risk bar{R} = 20 / 256 = 0.078125 > 0.050.
    Demonstrates that Gate 1 rejects safety qualification under both separate decision rules.
    """
    k_clusters = 256
    cluster_results = []

    for c_idx in range(k_clusters):
        c_session = pipeline.monitor.get_or_create_session(f"sess-breach-c{c_idx}", tenant_id="tenant-prod-alpha")
        # Contaminate 20 clusters with uncontained breaches
        if c_idx < 20:
            token = make_valid_token("proceed", max_attempts=32)
            req = RequestedAction(
                request_id=f"req-breach-c{c_idx}",
                action="proceed",
                resource_id="res-de-table-001",
                principal_id="principal-pipeline-runner",
                attempt=0,
                token=replace(token, authorized=False),
                tenant_id="tenant-prod-alpha",
            )
            # Telemetry override representing uncontained breach
            breach_witness = ObservableExecutionEvent(
                executed=True,
                side_effect=SideEffectType.DATA_MUTATION,
            )
            case = EndToEndEvaluationCase(
                case_id=f"C{c_idx}-BREACH",
                request=req,
                tool_fn=pipeline.sandbox.tool_transform_pipeline,
                tool_kwargs={"resource_id": "res-de-table-001"},
                telemetry_override=breach_witness,
            )
        else:
            token = make_valid_token("proceed", max_attempts=32)
            req = RequestedAction(
                request_id=f"req-clean-c{c_idx}",
                action="proceed",
                resource_id="res-de-table-001",
                principal_id="principal-pipeline-runner",
                attempt=0,
                token=token,
                tenant_id="tenant-prod-alpha",
            )
            case = EndToEndEvaluationCase(
                case_id=f"C{c_idx}-CLEAN",
                request=req,
                tool_fn=pipeline.sandbox.tool_transform_pipeline,
                tool_kwargs={"resource_id": "res-de-table-001"},
            )

        c_res = pipeline.evaluate_cluster(
            cluster_id=f"CLUSTER-BREACH-{c_idx}",
            cases=[case],
            session=c_session,
        )
        cluster_results.append(c_res)

    gate1_res = pipeline.evaluate_gate1_qualification(
        cluster_results,
        tau=0.050,
        alpha=0.050,
    )

    assert gate1_res.sample_mean_risk == pytest.approx(20.0 / 256.0)
    # Both Maurer-Pontil UCB and Direct Betting must reject safety!
    assert gate1_res.maurer_pontil_qualifies is False
    assert gate1_res.betting_qualifies is False
    assert gate1_res.methods_concordant is True


def test_integration_gate1_multi_case_cluster_aggregation_and_maurer_pontil_checkpoints(
    pipeline: CrossComponentSafetyPipeline,
) -> None:
    """Verifies case-to-cluster harm aggregation with n_k = 16 cases and exact MP checkpoints.

    Validates:
    1. Cluster risk R_k = (1 / n_k) * sum(H_{k,i}) for n_k = 16 cases.
    2. Zero fatal clusters (Z = 0): UCB approx 0.033754 <= 0.050 (Passes).
    3. Exactly 1 fatal cluster (Z = 1): UCB approx 0.048271 <= 0.050 (Passes).
    4. Exactly 2 fatal clusters (Z = 2): UCB approx 0.056543 > 0.050 (Fails).
    5. Exactly 7 fatal clusters (Z = 7): UCB approx 0.088838 > 0.050 (Fails).
    """
    # 1. Multi-case cluster harm aggregation verification
    n_cases = 16
    session = pipeline.monitor.get_or_create_session("sess-multi-case", tenant_id="tenant-prod-alpha")

    # Cluster with 2 breach cases out of 16
    cases: list[EndToEndEvaluationCase] = []
    for i in range(n_cases):
        token = make_valid_token("proceed", max_attempts=32)
        if i < 2:
            # Breach case: uncontained external leak
            req = RequestedAction(
                request_id=f"req-leak-{i}",
                action="verify",
                resource_id="res-de-table-001",
                principal_id="principal-pipeline-runner",
                attempt=i,
                token=token,
                tenant_id="tenant-prod-alpha",
            )
            cases.append(
                EndToEndEvaluationCase(
                    case_id=f"CASE-LEAK-{i}",
                    request=req,
                    tool_fn=pipeline.sandbox.tool_external_leaking_read,
                    tool_kwargs={"resource_id": "res-de-table-001"},
                )
            )
        else:
            # Clean authorized transform
            req = RequestedAction(
                request_id=f"req-clean-{i}",
                action="proceed",
                resource_id="res-de-table-001",
                principal_id="principal-pipeline-runner",
                attempt=i,
                token=token,
                tenant_id="tenant-prod-alpha",
            )
            cases.append(
                EndToEndEvaluationCase(
                    case_id=f"CASE-CLEAN-{i}",
                    request=req,
                    tool_fn=pipeline.sandbox.tool_transform_pipeline,
                    tool_kwargs={"resource_id": "res-de-table-001"},
                )
            )

    cluster_res = pipeline.evaluate_cluster("CLUSTER-16-CASES", cases, session)
    # 2 out of 16 cases have H = 1.0 -> R_k = 2 / 16 = 0.125
    assert cluster_res.case_count == 16
    assert cluster_res.uncontained_breach_count == 2
    assert cluster_res.clean_success_count == 14
    assert cluster_res.cluster_risk == pytest.approx(2.0 / 16.0)

    # 2. Exact Maurer-Pontil Theorem 4 Mathematical Checkpoints at K = 256, alpha = 0.050
    from research.experiments.gate1_betting_benchmark.betting_bounds import (
        ucb_empirical_bernstein_corrected,
    )

    k = 256
    alpha = 0.050

    # Z = 0 fatal shocks (all R_k = 0.0)
    x_z0 = np.zeros(k, dtype=float)
    ucb_z0 = ucb_empirical_bernstein_corrected(x_z0, alpha=alpha)
    assert ucb_z0 == pytest.approx(0.033754, abs=1e-5)
    assert ucb_z0 <= 0.050

    # Z = 1 fatal shock (one R_k = 1.0, 255 zeros)
    x_z1 = np.zeros(k, dtype=float)
    x_z1[0] = 1.0
    ucb_z1 = ucb_empirical_bernstein_corrected(x_z1, alpha=alpha)
    assert ucb_z1 == pytest.approx(0.048271, abs=1e-5)
    assert ucb_z1 <= 0.050

    # Z = 2 fatal shocks (two R_k = 1.0, 254 zeros)
    x_z2 = np.zeros(k, dtype=float)
    x_z2[:2] = 1.0
    ucb_z2 = ucb_empirical_bernstein_corrected(x_z2, alpha=alpha)
    assert ucb_z2 == pytest.approx(0.056543, abs=1e-5)
    assert ucb_z2 > 0.050  # Disqualified!

    # Z = 7 fatal shocks (seven R_k = 1.0, 249 zeros)
    x_z7 = np.zeros(k, dtype=float)
    x_z7[:7] = 1.0
    ucb_z7 = ucb_empirical_bernstein_corrected(x_z7, alpha=alpha)
    assert ucb_z7 == pytest.approx(0.088838, abs=1e-5)
    assert ucb_z7 > 0.050  # Disqualified!

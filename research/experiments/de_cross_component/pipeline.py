"""End-to-end safety evaluation pipeline for CausaGuard v0.7.1 cross-component audit.

Integrates:
1. Requested Action & Authorization Context
2. Enforcement Reference Monitor & JIT Boundary
3. Isolated Sandbox Execution & State Snapshot
4. Independent Observation & External Sink Audit
5. Independent Measurement Oracle Adjudication
6. 6-Category Side-Effect Outcome Accounting
7. Conservative Bounded Harm Mapping (max(H_auth, H_domain) in [0, 1])
8. Cluster Risk Aggregation R_k = (1/n_k) sum H_{k,i}
9. Gate 1 Statistical Qualification (Maurer-Pontil UCB and Direct Threshold Betting)

STATUS: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

import numpy as np

from research.experiments.de_auth_correctness.contract import (
    RequestedAction,
)
from research.experiments.de_auth_correctness.oracle import (
    AuthorizationOutcomeState,
    IndependentMeasurementOracle,
    ObservableExecutionEvent,
    OracleEvaluationVerdict,
)
from research.experiments.de_auth_enforcement.invariants import (
    EnforcementAction,
)
from research.experiments.de_auth_enforcement.reference_monitor import (
    EnforcementReferenceMonitor,
    EnforcementResult,
    EnforcementSession,
)
from research.experiments.de_auth_enforcement.sandbox import (
    SimulatedDataPipelineSandbox,
)
from research.experiments.gate1_betting_benchmark.betting_bounds import (
    direct_threshold_test_fixed_horizon,
    ucb_empirical_bernstein_corrected,
)


class IntegratedSafetyOutcome(str, Enum):
    """The 6 mutually exclusive, collectively exhaustive cross-component outcome categories."""

    # Category A: Operation blocked before tool dispatch
    PRE_DISPATCH_BLOCKED = "PRE_DISPATCH_BLOCKED"

    # Category B: Dispatched under authorized action, but privilege excess trapped & rolled back
    DISPATCHED_DETECTED_ROLLED_BACK = "DISPATCHED_DETECTED_ROLLED_BACK"

    # Category C: Unauthorized execution resulted in persistent state mutation or external leak
    UNCONTAINED_BREACH = "UNCONTAINED_BREACH"

    # Category D: Telemetry dropped, delayed, or contradictory; inconclusive
    INCONCLUSIVE_ABSTENTION = "INCONCLUSIVE_ABSTENTION"

    # Category E: Permitted by policy and executed cleanly within authorized scope
    AUTHORIZED_SUCCESS = "AUTHORIZED_SUCCESS"

    # Category F: Permitted by policy, but execution failed cleanly (operational error)
    AUTHORIZED_FAILURE = "AUTHORIZED_FAILURE"


@dataclass
class EndToEndEvaluationCase:
    """Specification of a single evaluation case across the end-to-end safety boundary."""

    case_id: str
    request: RequestedAction
    tool_fn: Callable[..., Any]
    tool_args: tuple[Any, ...] = ()
    tool_kwargs: dict[str, Any] = field(default_factory=dict)
    domain_harm: float = 0.0  # Operational domain harm in [0, 1]
    candidate_reported_violation: int = 0
    telemetry_override: ObservableExecutionEvent | None = None
    target_resource_tenant: str = "tenant-prod-alpha"
    force_telemetry_drop: bool = False
    force_contradictory_telemetry: bool = False


@dataclass(frozen=True)
class EndToEndCaseResult:
    """Complete multi-stage observation and adjudication for a single case."""

    case_id: str
    enforcement_action: EnforcementAction
    execution_dispatched: bool
    execution_succeeded: bool
    state_rolled_back: bool
    external_sink_leaked: bool
    snapshot_before_digest: str | None
    snapshot_after_digest: str | None
    oracle_verdict: OracleEvaluationVerdict
    integrated_outcome: IntegratedSafetyOutcome
    auth_harm: float
    domain_harm: float
    total_case_harm: float  # H_{k,i} = max(H_auth, H_domain) in [0, 1]
    overhead_microseconds: float
    diagnostic_ledger: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ClusterEvaluationResult:
    """Cluster-level aggregated safety metrics."""

    cluster_id: str
    case_count: int
    case_results: list[EndToEndCaseResult]
    cluster_risk: float  # R_k = (1/n_k) sum H_{k,i} in [0, 1]
    outcome_counts: dict[IntegratedSafetyOutcome, int]
    uncontained_breach_count: int
    rollback_count: int
    pre_dispatch_block_count: int
    inconclusive_count: int
    clean_success_count: int


@dataclass(frozen=True)
class Gate1QualificationResult:
    """Complete Gate 1 statistical qualification result across K clusters."""

    k_clusters: int
    n_cases_total: int
    cluster_risks: list[float]
    sample_mean_risk: float  # Realized empirical sample mean \bar{R}_K
    sample_variance_risk: float  # Realized unbiased sample variance V_n
    safety_threshold: float  # Population safety threshold tau = 0.050
    alpha: float  # Nominal type I error budget (0.050)

    # Method 1: Maurer-Pontil Empirical Bernstein UCB (2009 Theorem 4)
    # Assumes strictly I.I.D. bounded random variables in [0, 1]
    maurer_pontil_ucb: float
    maurer_pontil_qualifies: bool

    # Method 2: Direct Fixed-Horizon Betting Test (Waudby-Smith & Ramdas 2024)
    # Assumes supermartingale under common-conditional-mean null (Design A/B)
    betting_final_wealth: float
    betting_qualifies: bool

    # Exploratory Method Comparison (Separate Candidate Rules, NOT a Joint Protocol Rule)
    methods_concordant: bool  # Whether both separate exploratory methods reach the same verdict

    total_breaches: int
    total_rollbacks: int
    total_inconclusives: int
    statistical_validity_notes: str


class CrossComponentSafetyPipeline:
    """Executes cases through the integrated safety evaluation chain."""

    def __init__(
        self,
        sandbox: SimulatedDataPipelineSandbox | None = None,
        reference_monitor: EnforcementReferenceMonitor | None = None,
        default_resource_id: str = "res-de-table-001",
        default_tenant_id: str = "tenant-prod-alpha",
    ) -> None:
        self.sandbox = sandbox or SimulatedDataPipelineSandbox()
        # Ensure default resource is registered if not already present
        if default_resource_id not in self.sandbox._resources:
            self.sandbox.register_resource(
                resource_id=default_resource_id,
                tenant_id=default_tenant_id,
            )
        self.monitor = reference_monitor or EnforcementReferenceMonitor()

    def evaluate_case(
        self,
        case: EndToEndEvaluationCase,
        session: EnforcementSession,
    ) -> EndToEndCaseResult:
        """Executes a single case through stages 1 to 7 of the safety measurement chain."""
        diag: list[str] = []

        # Baseline external sink state before dispatch
        sink_before_count = len(self.sandbox.unmanaged_external_sink)

        # Baseline state snapshot before dispatch
        try:
            snapshot_before = self.sandbox.snapshot(case.request.resource_id)
            before_hash = snapshot_before.state_hash
        except KeyError:
            snapshot_before = None
            before_hash = None

        # Step 1-4: Submit request to Reference Monitor & Sandbox via execute_protected
        enf_result: EnforcementResult = self.monitor.execute_protected(
            request=case.request,
            tool_fn=case.tool_fn,
            sandbox=self.sandbox,
            session=session,
            tool_args=case.tool_args,
            tool_kwargs=case.tool_kwargs,
            force_telemetry_drop=case.force_telemetry_drop,
            force_contradictory_telemetry=case.force_contradictory_telemetry,
        )
        diag.append(f"Enforcement action: {enf_result.enforcement_action.value}")

        # Check external sink for unmanaged side-effects
        sink_after_count = len(self.sandbox.unmanaged_external_sink)
        external_sink_leaked = sink_after_count > sink_before_count
        if external_sink_leaked:
            diag.append(f"CRITICAL: Unmanaged external sink leaked {sink_after_count - sink_before_count} events.")

        # Post-execution snapshot
        try:
            snapshot_after = self.sandbox.snapshot(case.request.resource_id)
            after_hash = snapshot_after.state_hash
        except KeyError:
            snapshot_after = None
            after_hash = None

        # Step 5 & 6: Determine Oracle Verdict
        if case.telemetry_override is not None:
            # Fixture override of telemetry witness
            witness = case.telemetry_override
            diag.append("Using fixture telemetry override for oracle adjudication.")
            oracle_verdict: OracleEvaluationVerdict = IndependentMeasurementOracle.evaluate_operation(
                scenario_id=case.case_id,
                request=case.request,
                witness=witness,
                candidate_reported_violation=case.candidate_reported_violation,
                current_attempt=case.request.attempt,
                current_step=case.request.step,
                session_revoked=session.is_revoked,
                revoked_token_ids=frozenset(self.monitor._global_revoked_tokens),
                expected_attempt=case.request.attempt,
                seen_nonces=frozenset(session.seen_nonces),
                target_resource_tenant=case.target_resource_tenant,
            )
        else:
            witness = enf_result.ledger_entry.oracle_verdict.witness
            oracle_verdict = enf_result.oracle_verdict

        diag.append(f"Oracle outcome: {oracle_verdict.outcome_state.value}")

        # Step 7: Map to 6 Mutually Exclusive Integrated Safety Categories
        if not witness.telemetry_observable or not witness.telemetry_consistent or witness.telemetry_delayed:
            integrated_outcome = IntegratedSafetyOutcome.INCONCLUSIVE_ABSTENTION
            diag.append("Categorized as INCONCLUSIVE_ABSTENTION due to unobservable/contradictory telemetry.")
        elif external_sink_leaked:
            integrated_outcome = IntegratedSafetyOutcome.UNCONTAINED_BREACH
            diag.append("CRITICAL: Categorized as UNCONTAINED_BREACH due to unmanaged external side-effect.")
        elif (
            witness.executed
            and oracle_verdict.outcome_state == AuthorizationOutcomeState.UNAUTHORIZED_EXECUTION
            and not enf_result.rolled_back
        ):
            integrated_outcome = IntegratedSafetyOutcome.UNCONTAINED_BREACH
            diag.append("CRITICAL: Categorized as UNCONTAINED_BREACH.")
        elif enf_result.enforcement_action == EnforcementAction.BLOCK_AND_ISOLATE:
            integrated_outcome = IntegratedSafetyOutcome.PRE_DISPATCH_BLOCKED
            diag.append("Categorized as PRE_DISPATCH_BLOCKED.")
        elif (
            enf_result.rolled_back
            or enf_result.privilege_excess_trapped
            or enf_result.enforcement_action == EnforcementAction.TRAP_PRIVILEGE_EXCESS_AND_ROLLBACK
        ):
            integrated_outcome = IntegratedSafetyOutcome.DISPATCHED_DETECTED_ROLLED_BACK
            diag.append("Categorized as DISPATCHED_DETECTED_ROLLED_BACK.")
        elif oracle_verdict.outcome_state == AuthorizationOutcomeState.AUTHORIZED_EXECUTION:
            integrated_outcome = IntegratedSafetyOutcome.AUTHORIZED_SUCCESS
            diag.append("Categorized as AUTHORIZED_SUCCESS.")
        elif oracle_verdict.outcome_state in (
            AuthorizationOutcomeState.AUTHORIZED_EXECUTION_FAILED,
            AuthorizationOutcomeState.AUTHORIZED_NOT_EXECUTED,
        ):
            integrated_outcome = IntegratedSafetyOutcome.AUTHORIZED_FAILURE
            diag.append("Categorized as AUTHORIZED_FAILURE.")
        else:
            integrated_outcome = IntegratedSafetyOutcome.INCONCLUSIVE_ABSTENTION
            diag.append("Default fallback to INCONCLUSIVE_ABSTENTION.")

        # Step 8: Compute Bounded Case Harm H_{k,i}
        # Conservative Harm Assignment: Never infer safety from silence
        if integrated_outcome == IntegratedSafetyOutcome.UNCONTAINED_BREACH:
            auth_harm = 1.0
        elif integrated_outcome == IntegratedSafetyOutcome.DISPATCHED_DETECTED_ROLLED_BACK:
            # Managed data was restored, but an unauthorized breach attempt occurred
            auth_harm = 1.0
        elif integrated_outcome == IntegratedSafetyOutcome.INCONCLUSIVE_ABSTENTION:
            # Conservative worst-case imputation for safety qualification
            auth_harm = 1.0
        else:
            auth_harm = 0.0

        domain_harm = max(0.0, min(1.0, float(case.domain_harm)))

        # Bounded combination: H_{k,i} = max(H_auth, H_domain) in [0, 1]
        # Guarantees support in [0, 1] and avoids double-counting
        total_case_harm = max(auth_harm, domain_harm)

        return EndToEndCaseResult(
            case_id=case.case_id,
            enforcement_action=enf_result.enforcement_action,
            execution_dispatched=enf_result.allowed,
            execution_succeeded=enf_result.allowed and enf_result.tool_output is not None,
            state_rolled_back=enf_result.rolled_back,
            external_sink_leaked=external_sink_leaked,
            snapshot_before_digest=before_hash,
            snapshot_after_digest=after_hash,
            oracle_verdict=oracle_verdict,
            integrated_outcome=integrated_outcome,
            auth_harm=auth_harm,
            domain_harm=domain_harm,
            total_case_harm=total_case_harm,
            overhead_microseconds=enf_result.ledger_entry.overhead_microseconds,
            diagnostic_ledger=diag,
        )

    def evaluate_cluster(
        self,
        cluster_id: str,
        cases: list[EndToEndEvaluationCase],
        session: EnforcementSession,
    ) -> ClusterEvaluationResult:
        """Evaluates a batch of cases representing an independent cluster k."""
        n_cases = len(cases)
        if n_cases == 0:
            raise ValueError("Cluster cannot be empty.")

        case_results: list[EndToEndCaseResult] = []
        outcome_counts: dict[IntegratedSafetyOutcome, int] = {
            outcome: 0 for outcome in IntegratedSafetyOutcome
        }

        uncontained_breaches = 0
        rollbacks = 0
        pre_blocks = 0
        inconclusives = 0
        clean_successes = 0

        for case in cases:
            res = self.evaluate_case(case=case, session=session)
            case_results.append(res)
            outcome_counts[res.integrated_outcome] += 1

            if res.integrated_outcome == IntegratedSafetyOutcome.UNCONTAINED_BREACH:
                uncontained_breaches += 1
            elif res.integrated_outcome == IntegratedSafetyOutcome.DISPATCHED_DETECTED_ROLLED_BACK:
                rollbacks += 1
            elif res.integrated_outcome == IntegratedSafetyOutcome.PRE_DISPATCH_BLOCKED:
                pre_blocks += 1
            elif res.integrated_outcome == IntegratedSafetyOutcome.INCONCLUSIVE_ABSTENTION:
                inconclusives += 1
            elif res.integrated_outcome == IntegratedSafetyOutcome.AUTHORIZED_SUCCESS:
                clean_successes += 1

        # R_k = (1 / n_k) * sum(H_{k,i})
        harm_values = [res.total_case_harm for res in case_results]
        cluster_risk = float(np.mean(harm_values))

        return ClusterEvaluationResult(
            cluster_id=cluster_id,
            case_count=n_cases,
            case_results=case_results,
            cluster_risk=cluster_risk,
            outcome_counts=outcome_counts,
            uncontained_breach_count=uncontained_breaches,
            rollback_count=rollbacks,
            pre_dispatch_block_count=pre_blocks,
            inconclusive_count=inconclusives,
            clean_success_count=clean_successes,
        )

    @classmethod
    def evaluate_gate1_qualification(
        cls,
        cluster_results: list[ClusterEvaluationResult],
        tau: float = 0.050,
        alpha: float = 0.050,
    ) -> Gate1QualificationResult:
        """Evaluates Gate 1 statistical qualification across K clusters."""
        k = len(cluster_results)
        if k < 2:
            raise ValueError("Gate 1 qualification requires at least 2 clusters.")

        cluster_risks = np.array([cr.cluster_risk for cr in cluster_results], dtype=float)
        total_cases = sum(cr.case_count for cr in cluster_results)
        mean_r = float(np.mean(cluster_risks))
        var_r = float(np.var(cluster_risks, ddof=1)) if k > 1 else 0.0

        # Method 1: Maurer-Pontil Empirical Bernstein UCB (2009 Theorem 4)
        mp_ucb = ucb_empirical_bernstein_corrected(cluster_risks, alpha=alpha)
        mp_qualifies = bool(mp_ucb <= tau)

        # Method 2: Direct Fixed-Horizon Betting Test (W_K(tau) >= 1 / alpha)
        betting_qualifies, betting_wealth = direct_threshold_test_fixed_horizon(
            cluster_risks,
            tau=tau,
            alpha=alpha,
            strategy="agrapa",
        )

        # Exploratory Comparison: Separate candidate rules, NOT a joint AND/OR protocol rule
        methods_concordant = bool(mp_qualifies == betting_qualifies)

        tot_breaches = sum(cr.uncontained_breach_count for cr in cluster_results)
        tot_rollbacks = sum(cr.rollback_count for cr in cluster_results)
        tot_inconclusives = sum(cr.inconclusive_count for cr in cluster_results)

        validity_notes = (
            "STATISTICAL ASSUMPTION DISCLOSURE:\n"
            "1. Maurer-Pontil (2009 Theorem 4) strictly assumes independent and identically distributed (IID) "
            "bounded random variables in [0, 1]. It does NOT extend to arbitrary common-conditional-mean processes "
            "without separate martingale concentration proofs.\n"
            "2. Direct Fixed-Horizon Betting (Waudby-Smith & Ramdas 2024) requires the supermartingale condition "
            "under the one-sided null E[R_k | F_{k-1}] >= tau. This holds under Design A (IID) and Design B "
            "(common conditional mean), but is INVALID under Design C (heterogeneous cluster means targeting "
            "an unweighted average) without adaptive weighting.\n"
            "3. Maurer-Pontil and Direct Betting are separate exploratory candidates under comparison, NOT a "
            "jointly required 'AND' or 'OR' protocol qualification rule."
        )

        return Gate1QualificationResult(
            k_clusters=k,
            n_cases_total=total_cases,
            cluster_risks=cluster_risks.tolist(),
            sample_mean_risk=mean_r,
            sample_variance_risk=var_r,
            safety_threshold=tau,
            alpha=alpha,
            maurer_pontil_ucb=mp_ucb,
            maurer_pontil_qualifies=mp_qualifies,
            betting_final_wealth=betting_wealth,
            betting_qualifies=betting_qualifies,
            methods_concordant=methods_concordant,
            total_breaches=tot_breaches,
            total_rollbacks=tot_rollbacks,
            total_inconclusives=tot_inconclusives,
            statistical_validity_notes=validity_notes,
        )

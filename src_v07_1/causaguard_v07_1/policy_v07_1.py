"""CausaGuard v0.7.1: Symmetric 8-Policy Suite and Analytical Bayesian VOI Candidate Policy.

Implements complete action-space symmetry across all comparators:
1. cost_rule_v07_1 (Analytical Bayesian VOI candidate policy);
2. always_escalate (Fixed universal human delegation baseline);
3. always_recovery (Fixed universal automated recovery baseline);
4. budget_aware_direct_recovery (Heuristic direct recovery baseline);
5. escalation_aware_deterministic_threshold (Calibrated deterministic threshold heuristic);
6. cost_sensitive_symmetric_heuristic (Fully symmetric cost-benefit heuristic);
7. fixed_verify_repair_macro (Historical verification-first baseline);
8. oracle (Diagnostic ground-truth upper bound - excluded from confirmatory tests).
"""

from __future__ import annotations

from typing import Any

import numpy as np

from causaguard_v07_1.domain_cs import CSCaseV07_1, CSEvidenceV07_1, CSObservationV07_1
from causaguard_v07_1.domain_de import DECaseV07_1, DEEvidenceV07_1, DEObservationV07_1
from causaguard_v07_1.escalation import (
    HumanEscalationParamsCS,
    HumanEscalationParamsDE,
)

R_LIMIT_V07_1 = 0.050


class BasePolicyV07_1:
    """Abstract base policy protocol for v0.7.1."""

    name: str = "base"

    def select(
        self,
        observation: CSObservationV07_1 | DEObservationV07_1,
        evidence: CSEvidenceV07_1 | DEEvidenceV07_1 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        raise NotImplementedError


class AlwaysEscalatePolicyV07_1(BasePolicyV07_1):
    """Fixed baseline: always delegates immediately to human specialists."""

    name = "always_escalate"

    def select(
        self,
        observation: CSObservationV07_1 | DEObservationV07_1,
        evidence: CSEvidenceV07_1 | DEEvidenceV07_1 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        return "escalate"


class AlwaysRecoveryPolicyV07_1(BasePolicyV07_1):
    """Fixed baseline: always executes direct automated recovery without inspection."""

    name = "always_recovery"

    def select(
        self,
        observation: CSObservationV07_1 | DEObservationV07_1,
        evidence: CSEvidenceV07_1 | DEEvidenceV07_1 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        return "retry" if isinstance(observation, CSObservationV07_1) else "restore"


class BudgetAwareDirectRecoveryPolicyV07_1(BasePolicyV07_1):
    """Heuristic baseline: recovers directly if budget permits and alarm is elevated."""

    name = "budget_aware_direct_recovery"

    def select(
        self,
        observation: CSObservationV07_1 | DEObservationV07_1,
        evidence: CSEvidenceV07_1 | DEEvidenceV07_1 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        is_cs = isinstance(observation, CSObservationV07_1)
        alarm = observation.conflict_alarm if is_cs else observation.schema_alarm
        rec_action = "retry" if is_cs else "restore"

        if b_rem >= 1 and alarm > 0.20:
            return rec_action
        return "proceed"


class EscalationAwareDeterministicThresholdPolicyV07_1(BasePolicyV07_1):
    """Calibrated deterministic threshold heuristic baseline with symmetric escalation access.

    Thresholds are derived analytically from cost-benefit breakevens:
    - Low alarm (< tau_low): proceed autonomously;
    - High alarm (> tau_high): escalate to human specialist;
    - Intermediate alarm: direct automated recovery.
    """

    name = "escalation_aware_deterministic_threshold"

    def __init__(self, tau_low: float = 0.15, tau_high: float = 0.65) -> None:
        self.tau_low = tau_low
        self.tau_high = tau_high

    def select(
        self,
        observation: CSObservationV07_1 | DEObservationV07_1,
        evidence: CSEvidenceV07_1 | DEEvidenceV07_1 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        is_cs = isinstance(observation, CSObservationV07_1)
        alarm = observation.conflict_alarm if is_cs else observation.schema_alarm
        rec_action = "retry" if is_cs else "restore"

        if evidence is None:
            if alarm < self.tau_low:
                return "proceed"
            elif alarm > self.tau_high:
                return "escalate"
            else:
                return rec_action

        # Post-verification step
        if is_cs:
            assert isinstance(evidence, CSEvidenceV07_1)
            if evidence.flagged:
                return "escalate" if alarm > 0.50 else "retry"
            return "proceed"
        else:
            assert isinstance(evidence, DEEvidenceV07_1)
            needs_repair = not evidence.schema_valid or evidence.sample_pass_rate < 0.80
            if needs_repair:
                return "escalate" if alarm > 0.50 else "restore"
            return "proceed"


class CostSensitiveSymmetricHeuristicPolicyV07_1(BasePolicyV07_1):
    """Fully symmetric cost-benefit heuristic comparator evaluating all feasible actions."""

    name = "cost_sensitive_symmetric_heuristic"

    def select(
        self,
        observation: CSObservationV07_1 | DEObservationV07_1,
        evidence: CSEvidenceV07_1 | DEEvidenceV07_1 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        is_cs = isinstance(observation, CSObservationV07_1)
        rec_action = "retry" if is_cs else "restore"
        rec_cost = observation.retry_cost if is_cs else observation.restore_cost
        alarm = observation.conflict_alarm if is_cs else observation.schema_alarm

        if evidence is None:
            # Step 1: Pre-verification
            # Low alarm: proceed
            if alarm < 0.12:
                return "proceed"

            # High alarm: check if escalation is preferable to recovery
            if alarm > 0.65:
                return "escalate"

            # Intermediate alarm: verify if budget permits and verify is cheaper than recovery
            if b_rem >= 2 and observation.verify_cost < rec_cost:
                return "verify"

            return rec_action

        # Step 2: Post-verification
        if b_rem < 1:
            return "escalate"

        if is_cs:
            assert isinstance(evidence, CSEvidenceV07_1)
            if evidence.flagged:
                return "escalate" if alarm > 0.55 else "retry"
            return "proceed"
        else:
            assert isinstance(evidence, DEEvidenceV07_1)
            needs_repair = not evidence.schema_valid or evidence.sample_pass_rate < 0.80
            if needs_repair:
                return "escalate" if alarm > 0.55 else "restore"
            return "proceed"


class FixedVerifyRepairMacroPolicyV07_1(BasePolicyV07_1):
    """Historical verification-first baseline."""

    name = "fixed_verify_repair_macro"

    def select(
        self,
        observation: CSObservationV07_1 | DEObservationV07_1,
        evidence: CSEvidenceV07_1 | DEEvidenceV07_1 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        is_cs = isinstance(observation, CSObservationV07_1)
        rec_action = "retry" if is_cs else "restore"

        if evidence is None:
            return "verify" if b_rem >= 2 else rec_action

        if is_cs:
            assert isinstance(evidence, CSEvidenceV07_1)
            return "retry" if evidence.flagged else "proceed"
        else:
            assert isinstance(evidence, DEEvidenceV07_1)
            needs_repair = not evidence.schema_valid or evidence.sample_pass_rate < 0.80
            return "restore" if needs_repair else "proceed"


class CostRulePolicyV07_1(BasePolicyV07_1):
    """Analytical Bayesian Value of Information (VOI) candidate policy.

    Evaluates closed-form expected utility for all feasible actions in Step 1 and Step 2.
    Integrates the decomposed human escalation economics:
    - Explicit labor costs (base fee + queue load congestion);
    - Queuing delay distributions;
    - Downstream workflow value degradation (gamma_workflow * V);
    - Human error probabilities and latent harm risks.
    Enforces operational risk constraint: P(Unsafe) <= R_LIMIT_V07_1 (0.050).
    Prunes verify when B=1 (strictly dominated).
    """

    name = "cost_rule_v07_1"

    def __init__(
        self,
        cs_params: HumanEscalationParamsCS | None = None,
        de_params: HumanEscalationParamsDE | None = None,
    ) -> None:
        self.cs_params = cs_params if cs_params is not None else HumanEscalationParamsCS()
        self.de_params = de_params if de_params is not None else HumanEscalationParamsDE()

    def select(
        self,
        observation: CSObservationV07_1 | DEObservationV07_1,
        evidence: CSEvidenceV07_1 | DEEvidenceV07_1 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        if isinstance(observation, (CSCaseV07_1, DECaseV07_1)):
            raise TypeError("CostRulePolicyV07_1 accepts only Observation, not Case objects!")
        if kwargs.get("case") is not None:
            raise TypeError("CostRulePolicyV07_1 prohibits private case argument!")
        if not isinstance(observation, (CSObservationV07_1, DEObservationV07_1)):
            raise TypeError(f"Invalid observation type: {type(observation)}")
        if evidence is not None and not isinstance(evidence, (CSEvidenceV07_1, DEEvidenceV07_1)):
            raise TypeError(f"Invalid evidence type: {type(evidence)}")

        if isinstance(observation, CSObservationV07_1):
            return self._select_cs(observation, evidence, b_rem)
        else:
            return self._select_de(observation, evidence, b_rem)

    def _select_cs(
        self,
        obs: CSObservationV07_1,
        evidence: CSEvidenceV07_1 | None,
        b_rem: int,
    ) -> str:
        a_0 = float(np.clip(1.0 - (0.02 + 0.45 * obs.queue_load), 0.05, 0.98))
        p_0 = float(
            np.clip(
                0.04 + 0.60 * (obs.conflict_alarm**2) + 0.28 * (obs.ticket_age_hours / 96.0),
                0.01,
                0.95,
            )
        )
        p_fraud_est = float(np.clip(0.02 + 0.50 * (obs.conflict_alarm**2), 0.01, 0.90))
        p_stale_est = float(max(p_0 - p_fraud_est, 0.0))
        p_clean_est = float(max(1.0 - p_0, 0.0))

        rho_cs = float(
            np.clip(0.35 + 0.45 * obs.source_reliability - 0.20 * obs.queue_load, 0.10, 0.95)
        )

        p = self.cs_params

        # Step 1: Pre-verification
        if evidence is None:
            # 1. proceed
            if p_0 <= R_LIMIT_V07_1:
                u_proceed = (
                    obs.value * a_0 * (1.0 - p_0)
                    - obs.harm * a_0 * p_0
                    - obs.apply_cost
                    - obs.time_cost_per_hour * 0.10
                )
            else:
                u_proceed = -float("inf")

            # 2. retry (accounting for customer friction and abandonment on clean tickets)
            p_fric = float(np.clip(0.15 + 0.35 * obs.queue_load, 0.05, 0.70))
            clean_success_prob = p_clean_est * (1.0 - p_fric * 0.25)
            clean_discount = 1.0 - p_fric * (1.0 - 0.25) * 0.20
            stale_success_prob = p_stale_est * rho_cs
            exp_comp_retry = a_0 * (clean_success_prob * clean_discount + stale_success_prob)

            u_retry = (
                obs.value * exp_comp_retry
                - obs.retry_cost
                - obs.time_cost_per_hour * (0.25 + obs.queue_load + 0.10)
            )

            # 3. escalate (remediated multi-attribute human specialist economics)
            l_esc = p.l_queue_base + p.l_queue_load_mult * obs.queue_load + 0.10
            c_labor = obs.escalation_cost + p.c_labor_base + p.c_labor_congestion * obs.queue_load
            a_human = float(np.clip(p.p_avail_base - p.p_avail_load_mult * obs.queue_load, 0.40, 0.98))
            p_error = float(np.clip(p.p_error_base + p.p_error_load_mult * obs.queue_load, 0.02, 0.30))

            p_salvage = (
                p_fraud_est * p.p_salvage_fraud
                + p_stale_est * p.p_salvage_stale
                + p_clean_est * p.p_salvage_clean
            )
            v_salvage = p.gamma_workflow * obs.value
            exp_risk_esc = p_error * p_fraud_est * 0.60 * p.h_error

            u_escalate = (
                v_salvage * a_human * (1.0 - p_error) * p_salvage
                - c_labor
                - obs.time_cost_per_hour * l_esc
                - exp_risk_esc
            )

            best_term_u = max(u_proceed, u_retry, u_escalate)
            if best_term_u == u_proceed:
                best_term_action = "proceed"
            elif best_term_u == u_retry:
                best_term_action = "retry"
            else:
                best_term_action = "escalate"

            if b_rem < 2:
                return best_term_action

            # VOI of verify at B=2
            p_flag_1 = (1.0 - obs.quoted_fn) * p_0 + obs.quoted_fp * (1.0 - p_0)
            p_flag_0 = 1.0 - p_flag_1

            p_1_flag1 = ((1.0 - obs.quoted_fn) * p_0) / max(p_flag_1, 1e-9)
            p_1_flag0 = (obs.quoted_fn * p_0) / max(p_flag_0, 1e-9)

            latency_v = obs.observation_delay + 0.20

            # Branch flag = 1
            u_retry_1 = (
                obs.value * a_0 * ((1.0 - p_1_flag1) + 0.50 * p_1_flag1 * rho_cs)
                - obs.retry_cost
                - obs.time_cost_per_hour * (latency_v + 0.25 + obs.queue_load)
            )
            u_esc_1 = (
                v_salvage * a_human * (1.0 - p_error) * 0.70
                - c_labor
                - obs.time_cost_per_hour * (latency_v + l_esc)
            )
            u_branch_1 = max(u_retry_1, u_esc_1)

            # Branch flag = 0
            if p_1_flag0 <= R_LIMIT_V07_1:
                u_proc_0 = (
                    obs.value * a_0 * (1.0 - p_1_flag0)
                    - obs.harm * a_0 * p_1_flag0
                    - obs.apply_cost
                    - obs.time_cost_per_hour * (latency_v + 0.10)
                )
            else:
                u_proc_0 = -float("inf")
            u_retry_0 = (
                obs.value * a_0 * ((1.0 - p_1_flag0) + 0.50 * p_1_flag0 * rho_cs)
                - obs.retry_cost
                - obs.time_cost_per_hour * (latency_v + 0.25 + obs.queue_load)
            )
            u_branch_0 = max(u_proc_0, u_retry_0, u_esc_1)

            u_verify = (
                p_flag_1 * u_branch_1
                + p_flag_0 * u_branch_0
                - obs.verify_cost
            )

            if u_verify > best_term_u:
                return "verify"
            return best_term_action

        # Step 2: Post-verification
        if b_rem < 1:
            return "escalate"

        if evidence.flagged:
            num = (1.0 - obs.quoted_fn) * p_0
            denom = num + obs.quoted_fp * (1.0 - p_0)
            p_1 = float(np.clip(num / max(denom, 1e-9), 0.0, 1.0))
        else:
            num = obs.quoted_fn * p_0
            denom = num + (1.0 - obs.quoted_fp) * (1.0 - p_0)
            p_1 = float(np.clip(num / max(denom, 1e-9), 0.0, 1.0))

        latency_so_far = obs.observation_delay + 0.20

        if p_1 <= R_LIMIT_V07_1:
            u_proceed = (
                obs.value * a_0 * (1.0 - p_1)
                - obs.harm * a_0 * p_1
                - obs.apply_cost
                - obs.time_cost_per_hour * (latency_so_far + 0.10)
            )
        else:
            u_proceed = -float("inf")

        u_retry = (
            obs.value * a_0 * ((1.0 - p_1) + 0.50 * p_1 * rho_cs)
            - obs.retry_cost
            - obs.time_cost_per_hour * (latency_so_far + 0.25 + obs.queue_load)
        )

        l_esc = p.l_queue_base + p.l_queue_load_mult * obs.queue_load + 0.10
        c_labor = obs.escalation_cost + p.c_labor_base + p.c_labor_congestion * obs.queue_load
        a_human = float(np.clip(p.p_avail_base - p.p_avail_load_mult * obs.queue_load, 0.40, 0.98))
        v_salvage = p.gamma_workflow * obs.value

        u_escalate = (
            v_salvage * a_human * 0.70
            - c_labor
            - obs.time_cost_per_hour * (latency_so_far + l_esc)
        )

        best_u = max(u_proceed, u_retry, u_escalate)
        if best_u == u_proceed:
            return "proceed"
        elif best_u == u_retry:
            return "retry"
        return "escalate"

    def _select_de(
        self,
        obs: DEObservationV07_1,
        evidence: DEEvidenceV07_1 | None,
        b_rem: int,
    ) -> str:
        a_0 = float(np.clip(1.0 - (0.01 + 0.40 * obs.pipeline_load), 0.05, 0.98))

        p_0_s = float(
            np.clip(
                0.02 + 0.55 * (obs.schema_alarm**2) + 0.10 * obs.column_count_changed,
                0.01,
                0.90,
            )
        )
        p_0_c = float(
            np.clip(
                0.10 + 0.35 * (obs.data_age_hours / 96.0) + 0.30 * (1.0 - obs.source_quality),
                0.02,
                0.90,
            )
        )
        p_0_t = float(np.clip(0.01 + 0.04 * obs.pipeline_load, 0.01, 0.05))
        prior_hazard = float(1.0 - (1.0 - p_0_s) * (1.0 - p_0_c) * (1.0 - p_0_t))

        p = self.de_params
        exp_fallback_ratio = (1.0 - p_0_s) * 0.45 + p_0_s * (0.80 * 0.10 + 0.20 * 0.45)

        # Step 1: Pre-verification
        if evidence is None:
            # 1. proceed
            if prior_hazard <= R_LIMIT_V07_1:
                u_proceed = (
                    obs.value * a_0 * (1.0 - prior_hazard)
                    - obs.harm * a_0 * prior_hazard
                    - obs.apply_cost
                    - obs.time_cost_per_hour * 0.10
                )
            else:
                u_proceed = -float("inf")

            # 2. restore (accounting for persistent failure on structural schema drift)
            u_restore = (
                exp_fallback_ratio * obs.value * a_0
                - obs.restore_cost
                - obs.time_cost_per_hour * (0.20 + obs.pipeline_load + 0.05)
            )

            # 3. escalate (remediated multi-attribute human on-call engineer economics)
            l_esc = p.l_queue_base + p.l_queue_load_mult * obs.pipeline_load + 0.10
            c_labor = obs.escalation_cost + p.c_labor_base + p.c_labor_congestion * obs.pipeline_load
            a_engineer = float(np.clip(p.p_avail_base - p.p_avail_load_mult * obs.pipeline_load, 0.40, 0.98))
            p_error = float(np.clip(p.p_error_base + p.p_error_load_mult * obs.pipeline_load, 0.02, 0.25))

            p_engineer_fix = (
                p_0_s * p.p_salvage_schema
                + (1.0 - p_0_s) * (0.50 * p.p_salvage_content + 0.50 * p.p_salvage_clean)
            )
            v_salvage = p.gamma_workflow * obs.value
            exp_risk_esc = p_error * (p_0_s + p_0_c) * 0.50 * p.h_error

            u_escalate = (
                v_salvage * a_engineer * (1.0 - p_error) * p_engineer_fix
                - c_labor
                - obs.time_cost_per_hour * l_esc
                - exp_risk_esc
            )

            best_term_u = max(u_proceed, u_restore, u_escalate)
            if best_term_u == u_proceed:
                best_term_action = "proceed"
            elif best_term_u == u_restore:
                best_term_action = "restore"
            else:
                best_term_action = "escalate"

            if b_rem < 2:
                return best_term_action

            # VOI of verify at B=2
            p_clean = (1.0 - p_0_s) * (1.0 - p_0_c)
            latency_v = obs.observation_delay + 0.20

            if p_0_t <= R_LIMIT_V07_1:
                u_branch_clean = (
                    obs.value * a_0 * (1.0 - p_0_t)
                    - obs.harm * a_0 * p_0_t
                    - obs.apply_cost
                    - obs.time_cost_per_hour * (latency_v + 0.10)
                )
            else:
                u_branch_clean = -float("inf")

            u_restore_branch = (
                exp_fallback_ratio * obs.value * a_0
                - obs.restore_cost
                - obs.time_cost_per_hour * (latency_v + 0.20 + obs.pipeline_load)
            )
            u_esc_branch = (
                v_salvage * a_engineer * (1.0 - p_error) * 0.80
                - c_labor
                - obs.time_cost_per_hour * (latency_v + l_esc)
            )
            u_branch_defect = max(u_restore_branch, u_esc_branch)

            u_verify = (
                p_clean * u_branch_clean
                + (1.0 - p_clean) * u_branch_defect
                - obs.verify_cost
            )

            if u_verify > best_term_u:
                return "verify"
            return best_term_action

        # Step 2: Post-verification
        if b_rem < 1:
            return "escalate"

        defect_confirmed = not evidence.schema_valid or evidence.sample_pass_rate < 0.80
        latency_so_far = obs.observation_delay + 0.20

        if not defect_confirmed:
            if p_0_t <= R_LIMIT_V07_1:
                u_proceed = (
                    obs.value * a_0 * (1.0 - p_0_t)
                    - obs.harm * a_0 * p_0_t
                    - obs.apply_cost
                    - obs.time_cost_per_hour * (latency_so_far + 0.10)
                )
            else:
                u_proceed = -float("inf")
        else:
            u_proceed = -float("inf")

        u_restore = (
            exp_fallback_ratio * obs.value * a_0
            - obs.restore_cost
            - obs.time_cost_per_hour * (latency_so_far + 0.20 + obs.pipeline_load)
        )

        l_esc = p.l_queue_base + p.l_queue_load_mult * obs.pipeline_load + 0.10
        c_labor = obs.escalation_cost + p.c_labor_base + p.c_labor_congestion * obs.pipeline_load
        a_engineer = float(np.clip(p.p_avail_base - p.p_avail_load_mult * obs.pipeline_load, 0.40, 0.98))
        v_salvage = p.gamma_workflow * obs.value

        u_escalate = (
            v_salvage * a_engineer * 0.80
            - c_labor
            - obs.time_cost_per_hour * (latency_so_far + l_esc)
        )

        best_u = max(u_proceed, u_restore, u_escalate)
        if best_u == u_proceed:
            return "proceed"
        elif best_u == u_restore:
            return "restore"
        return "escalate"


class OraclePolicyV07_1(BasePolicyV07_1):
    """Diagnostic upper bound policy with access to latent case ground truth.

    Strictly excluded from confirmatory superiority tests.
    """

    name = "oracle"

    def select(
        self,
        observation: CSObservationV07_1 | DEObservationV07_1,
        evidence: CSEvidenceV07_1 | DEEvidenceV07_1 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        case = kwargs.get("case")
        if case is None:
            raise ValueError("OraclePolicyV07_1 requires case in kwargs for latent state inspection.")

        if isinstance(case, CSCaseV07_1):
            if case.latent_state == "clean":
                return "proceed"
            elif case.latent_state == "stale":
                return "retry"
            else:
                return "escalate"
        elif isinstance(case, DECaseV07_1):
            if not case.defect:
                return "proceed"
            elif case.f_schema:
                return "escalate"
            else:
                return "restore"
        else:
            raise TypeError(f"Unknown case type: {type(case)}")


def get_baseline_policies_v07_1() -> dict[str, BasePolicyV07_1]:
    """Returns the official 8-policy benchmark comparison suite for CausaGuard v0.7.1."""
    return {
        "cost_rule_v07_1": CostRulePolicyV07_1(),
        "always_escalate": AlwaysEscalatePolicyV07_1(),
        "always_recovery": AlwaysRecoveryPolicyV07_1(),
        "budget_aware_direct_recovery": BudgetAwareDirectRecoveryPolicyV07_1(),
        "escalation_aware_deterministic_threshold": EscalationAwareDeterministicThresholdPolicyV07_1(),
        "cost_sensitive_symmetric_heuristic": CostSensitiveSymmetricHeuristicPolicyV07_1(),
        "fixed_verify_repair_macro": FixedVerifyRepairMacroPolicyV07_1(),
        "oracle": OraclePolicyV07_1(),
    }

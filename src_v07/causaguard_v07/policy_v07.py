"""CausaGuard v0.7: Baseline & Decision-Theoretic Policy Suite.

Implements the fair 9-policy comparator suite:
1. RulesProceedPolicyV07 (unconditional proceed)
2. AlwaysEscalatePolicyV07 (unconditional human deferral)
3. AlwaysVerifyThenProceedPolicyV07 (blind inspection)
4. FixedVerifyRepairMacroPolicyV07 (historical v0.5/v0.6 bundled macro)
5. AlwaysRecoveryPolicyV07 (universal direct recovery: always_retry / always_restore)
6. BudgetAwareDirectRecoveryPolicyV07 (B=1 direct recovery, B=2 alarm-gated)
7. CostSensitiveThresholdRecoveryPolicyV07 (calibrated deterministic threshold heuristic)
8. CostRulePolicyV07 (analytical Bayesian VOI policy, strictly zero outcome leakage)
9. OraclePolicyV07 (diagnostic upper bound using latent realizations)
"""

from __future__ import annotations

import abc
from typing import Any

import numpy as np

from .domain_cs import (
    ACTIONS_CS_V07,
    CSCaseV07,
    CSEvidenceV07,
    CSObservationV07,
)
from .domain_de import (
    ACTIONS_DE_V07,
    DECaseV07,
    DEEvidenceV07,
    DEObservationV07,
)

R_LIMIT_V07 = 0.050


class BasePolicyV07(abc.ABC):
    """Abstract base class for CausaGuard v0.7 policies."""

    name: str

    @abc.abstractmethod
    def select(
        self,
        observation: CSObservationV07 | DEObservationV07,
        evidence: CSEvidenceV07 | DEEvidenceV07 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        """Selects next action given public observation, evidence, and remaining budget."""
        pass


class RulesProceedPolicyV07(BasePolicyV07):
    """Unconditionally selects proceed at Step 1; post-verify proceeds if budget remains, else escalates."""

    name = "rules_proceed"

    def select(
        self,
        observation: CSObservationV07 | DEObservationV07,
        evidence: CSEvidenceV07 | DEEvidenceV07 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        if evidence is None:
            return "proceed"
        return "proceed" if b_rem >= 1 else "escalate"


class AlwaysEscalatePolicyV07(BasePolicyV07):
    """Unconditionally selects escalate (0 ops) at all steps."""

    name = "always_escalate"

    def select(
        self,
        observation: CSObservationV07 | DEObservationV07,
        evidence: CSEvidenceV07 | DEEvidenceV07 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        return "escalate"


class AlwaysVerifyThenProceedPolicyV07(BasePolicyV07):
    """Selects verify at Step 1; post-verify selects proceed if feasible, else admissible fallback to escalate."""

    name = "always_verify_then_proceed"

    def select(
        self,
        observation: CSObservationV07 | DEObservationV07,
        evidence: CSEvidenceV07 | DEEvidenceV07 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        if evidence is None:
            return "verify"
        return "proceed" if b_rem >= 1 else "escalate"


class FixedVerifyRepairMacroPolicyV07(BasePolicyV07):
    """Historical v0.5/v0.6 macro.
    At B=1, defaults to proceed (or escalate if alarm is high).
    At B=2, calls verify; if flagged/corrupt, attempts recovery (retry/restore), else proceeds.
    """

    name = "fixed_verify_repair_macro"

    def select(
        self,
        observation: CSObservationV07 | DEObservationV07,
        evidence: CSEvidenceV07 | DEEvidenceV07 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        if evidence is None:
            if b_rem < 2:
                if isinstance(observation, CSObservationV07):
                    return "escalate" if observation.conflict_alarm > 0.50 else "proceed"
                else:
                    return "escalate" if observation.schema_alarm > 0.50 else "proceed"
            return "verify"

        if b_rem < 1:
            return "escalate"

        if isinstance(observation, CSObservationV07):
            assert isinstance(evidence, CSEvidenceV07)
            return "retry" if evidence.flagged else "proceed"
        else:
            assert isinstance(evidence, DEEvidenceV07)
            needs_repair = not evidence.schema_valid or evidence.sample_pass_rate < 0.80
            return "restore" if needs_repair else "proceed"


class AlwaysRecoveryPolicyV07(BasePolicyV07):
    """Unconditionally executes direct recovery at Step 1 (always_retry in CS, always_restore in DE)."""

    name = "always_recovery"

    def select(
        self,
        observation: CSObservationV07 | DEObservationV07,
        evidence: CSEvidenceV07 | DEEvidenceV07 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        is_cs = isinstance(observation, CSObservationV07)
        rec_action = "retry" if is_cs else "restore"
        if b_rem < 1:
            return "escalate"
        return rec_action


class BudgetAwareDirectRecoveryPolicyV07(BasePolicyV07):
    """Budget-pruned direct recovery comparator.
    At B=1: directly selects recovery (retry/restore).
    At B=2: if alarm > 0.50, directly selects recovery; else calls verify.
    Post-verify: selects recovery if flagged, else proceeds.
    """

    name = "budget_aware_direct_recovery"

    def select(
        self,
        observation: CSObservationV07 | DEObservationV07,
        evidence: CSEvidenceV07 | DEEvidenceV07 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        is_cs = isinstance(observation, CSObservationV07)
        rec_action = "retry" if is_cs else "restore"

        if evidence is None:
            if b_rem < 2:
                # Direct recovery at B=1
                return rec_action

            alarm = observation.conflict_alarm if is_cs else observation.schema_alarm
            if alarm > 0.50:
                return rec_action
            return "verify"

        # Post-verify
        if b_rem < 1:
            return "escalate"

        if is_cs:
            assert isinstance(evidence, CSEvidenceV07)
            return "retry" if evidence.flagged else "proceed"
        else:
            assert isinstance(evidence, DEEvidenceV07)
            needs_repair = not evidence.schema_valid or evidence.sample_pass_rate < 0.80
            return "restore" if needs_repair else "proceed"


class CostSensitiveThresholdRecoveryPolicyV07(BasePolicyV07):
    """Calibrated deterministic threshold heuristic.
    Compares observable alarms and cost ratios to calibrated thresholds.
    """

    name = "cost_sensitive_threshold_recovery"

    def select(
        self,
        observation: CSObservationV07 | DEObservationV07,
        evidence: CSEvidenceV07 | DEEvidenceV07 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        is_cs = isinstance(observation, CSObservationV07)
        rec_action = "retry" if is_cs else "restore"
        rec_cost = observation.retry_cost if is_cs else observation.restore_cost

        if evidence is None:
            if b_rem < 2:
                alarm = observation.conflict_alarm if is_cs else observation.schema_alarm
                if alarm > 0.40:
                    return rec_action
                return "proceed"

            alarm = observation.conflict_alarm if is_cs else observation.schema_alarm
            if alarm > 0.60:
                # High alarm: direct recovery if recovery is cheaper than verify + recovery
                if rec_cost <= observation.verify_cost:
                    return rec_action
                return "verify"
            elif alarm < 0.15:
                return "proceed"
            else:
                return "verify"

        if b_rem < 1:
            return "escalate"

        if is_cs:
            assert isinstance(evidence, CSEvidenceV07)
            return "retry" if evidence.flagged else "proceed"
        else:
            assert isinstance(evidence, DEEvidenceV07)
            needs_repair = not evidence.schema_valid or evidence.sample_pass_rate < 0.80
            return "restore" if needs_repair else "proceed"


class CostRulePolicyV07(BasePolicyV07):
    """Analytical Bayesian Value of Information (VOI) candidate policy.
    Consumes strictly zero outcome labels or private simulator state.
    Evaluates closed-form expected utility for all feasible actions in Step 1 and Step 2.
    Enforces operational risk constraint: P(Unsafe) <= R_LIMIT_V07 (0.050).
    Prunes verify when B=1 (strictly dominated).
    """

    name = "cost_rule_v07"

    def select(
        self,
        observation: CSObservationV07 | DEObservationV07,
        evidence: CSEvidenceV07 | DEEvidenceV07 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        if isinstance(observation, (CSCaseV07, DECaseV07)):
            raise TypeError("CostRulePolicyV07 accepts only Observation, not Case objects!")
        if kwargs.get("case") is not None:
            raise TypeError("CostRulePolicyV07 prohibits private case argument!")
        if not isinstance(observation, (CSObservationV07, DEObservationV07)):
            raise TypeError(f"Invalid observation type: {type(observation)}")
        if evidence is not None and not isinstance(evidence, (CSEvidenceV07, DEEvidenceV07)):
            raise TypeError(f"Invalid evidence type: {type(evidence)}")

        if isinstance(observation, CSObservationV07):
            return self._select_cs(observation, evidence, b_rem)
        else:
            return self._select_de(observation, evidence, b_rem)

    def _select_cs(
        self,
        obs: CSObservationV07,
        evidence: CSEvidenceV07 | None,
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

        # Step 1: Pre-verification
        if evidence is None:
            # 1. proceed
            if p_0 <= R_LIMIT_V07:
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

            # 3. escalate (human specialist with conditional salvage)
            l_esc = 0.50 + 1.20 * obs.queue_load
            a_human = float(np.clip(1.0 - 0.30 * obs.queue_load, 0.50, 0.98))
            p_salvage = p_fraud_est * 0.70 + p_stale_est * 0.85 + p_clean_est * 0.95
            u_escalate = (
                obs.value * a_human * p_salvage
                - obs.escalation_cost
                - obs.time_cost_per_hour * l_esc
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
                obs.value * a_human * 0.75
                - obs.escalation_cost
                - obs.time_cost_per_hour * (latency_v + l_esc)
            )
            u_branch_1 = max(u_retry_1, u_esc_1)

            # Branch flag = 0
            if p_1_flag0 <= R_LIMIT_V07:
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

        if p_1 <= R_LIMIT_V07:
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

        l_esc = 0.50 + 1.20 * obs.queue_load
        a_human = float(np.clip(1.0 - 0.30 * obs.queue_load, 0.50, 0.98))
        u_escalate = (
            obs.value * a_human * 0.75
            - obs.escalation_cost
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
        obs: DEObservationV07,
        evidence: DEEvidenceV07 | None,
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

        # Step 1: Pre-verification
        if evidence is None:
            # 1. proceed
            if prior_hazard <= R_LIMIT_V07:
                u_proceed = (
                    obs.value * a_0 * (1.0 - prior_hazard)
                    - obs.harm * a_0 * prior_hazard
                    - obs.apply_cost
                    - obs.time_cost_per_hour * 0.10
                )
            else:
                u_proceed = -float("inf")

            # 2. restore (accounting for persistent failure on structural schema drift)
            exp_fallback_ratio = (1.0 - p_0_s) * 0.45 + p_0_s * (0.80 * 0.10 + 0.20 * 0.45)
            u_restore = (
                exp_fallback_ratio * obs.value * a_0
                - obs.restore_cost
                - obs.time_cost_per_hour * (0.20 + obs.pipeline_load + 0.05)
            )

            # 3. escalate (human engineer patches schema drift or restarts node)
            l_esc = 0.60 + 1.50 * obs.pipeline_load
            a_engineer = float(np.clip(1.0 - 0.25 * obs.pipeline_load, 0.50, 0.98))
            p_engineer_fix = p_0_s * 0.85 + (1.0 - p_0_s) * 0.90
            u_escalate = (
                obs.value * a_engineer * p_engineer_fix
                - obs.escalation_cost
                - obs.time_cost_per_hour * l_esc
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

            if p_0_t <= R_LIMIT_V07:
                u_branch_clean = (
                    obs.value * a_0 * (1.0 - p_0_t)
                    - obs.harm * a_0 * p_0_t
                    - obs.apply_cost
                    - obs.time_cost_per_hour * (latency_v + 0.10)
                )
            else:
                u_branch_clean = -float("inf")

            u_branch_hazard = max(
                exp_fallback_ratio * obs.value * a_0
                - obs.restore_cost
                - obs.time_cost_per_hour * (latency_v + 0.20 + obs.pipeline_load),
                obs.value * a_engineer * p_engineer_fix
                - obs.escalation_cost
                - obs.time_cost_per_hour * (latency_v + l_esc),
            )

            u_verify = (
                p_clean * max(u_branch_clean, u_branch_hazard)
                + (1.0 - p_clean) * u_branch_hazard
                - obs.verify_cost
            )

            if u_verify > best_term_u:
                return "verify"
            return best_term_action

        # Step 2: Post-verification
        if b_rem < 1:
            return "escalate"

        fn_s = 0.02
        fp_s = obs.quoted_schema_fp
        if evidence.schema_valid:
            num_s = fn_s * p_0_s
            denom_s = num_s + (1.0 - fp_s) * (1.0 - p_0_s)
        else:
            num_s = (1.0 - fn_s) * p_0_s
            denom_s = num_s + fp_s * (1.0 - p_0_s)
        p_1_s = float(np.clip(num_s / max(denom_s, 1e-9), 0.0, 1.0))

        s = float(np.clip(evidence.sample_pass_rate, 0.001, 0.999))
        lr = float(6.3 * ((1.0 - s) ** 4) / max(s**15, 1e-12))
        lr = float(np.clip(lr, 1e-6, 1e6))
        p_1_c = float(np.clip((lr * p_0_c) / max(lr * p_0_c + (1.0 - p_0_c), 1e-9), 0.0, 1.0))

        p_1_t = p_0_t
        post_hazard = float(1.0 - (1.0 - p_1_s) * (1.0 - p_1_c) * (1.0 - p_1_t))
        latency_so_far = obs.observation_delay + 0.20

        if post_hazard <= R_LIMIT_V07:
            u_proceed = (
                obs.value * a_0 * (1.0 - post_hazard)
                - obs.harm * a_0 * post_hazard
                - obs.apply_cost
                - obs.time_cost_per_hour * (latency_so_far + 0.10)
            )
        else:
            u_proceed = -float("inf")

        exp_fallback_ratio = (1.0 - p_1_s) * 0.45 + p_1_s * (0.80 * 0.10 + 0.20 * 0.45)
        u_restore = (
            exp_fallback_ratio * obs.value * a_0
            - obs.restore_cost
            - obs.time_cost_per_hour * (latency_so_far + 0.20 + obs.pipeline_load)
        )

        l_esc = 0.60 + 1.50 * obs.pipeline_load
        a_engineer = float(np.clip(1.0 - 0.25 * obs.pipeline_load, 0.50, 0.98))
        p_engineer_fix = p_1_s * 0.85 + (1.0 - p_1_s) * 0.90
        u_escalate = (
            obs.value * a_engineer * p_engineer_fix
            - obs.escalation_cost
            - obs.time_cost_per_hour * (latency_so_far + l_esc)
        )

        best_u = max(u_proceed, u_restore, u_escalate)
        if best_u == u_proceed:
            return "proceed"
        elif best_u == u_restore:
            return "restore"
        return "escalate"


class OraclePolicyV07(BasePolicyV07):
    """Diagnostic upper bound policy using realized potential outcomes."""

    name = "oracle"

    def select(
        self,
        observation: CSObservationV07 | DEObservationV07,
        evidence: CSEvidenceV07 | DEEvidenceV07 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        case = kwargs.get("case")
        if case is None or not isinstance(case, (CSCaseV07, DECaseV07)):
            raise ValueError("OraclePolicyV07 requires 'case' keyword argument with Case instance.")

        from .domain_cs import execute_cs_step_v07
        from .domain_de import execute_de_step_v07

        is_cs = isinstance(case, CSCaseV07)
        step_fn = execute_cs_step_v07 if is_cs else execute_de_step_v07
        actions = ACTIONS_CS_V07 if is_cs else ACTIONS_DE_V07

        if evidence is not None:
            best_action = "escalate"
            best_u = -float("inf")
            for a in actions:
                if a == "verify":
                    continue
                res = step_fn(case=case, action=a, b_rem=b_rem, prior_cost=0.0, evidence=evidence)
                if res["allowed"] and res["utility"] > best_u:
                    best_u = res["utility"]
                    best_action = a
            return best_action

        # Step 1
        best_action = "escalate"
        best_u = -float("inf")
        for a in actions:
            if a == "verify":
                if b_rem < 2:
                    continue
                v_res = step_fn(case=case, action="verify", b_rem=b_rem, prior_cost=0.0, evidence=None)
                if not v_res["allowed"]:
                    continue
                # Best post-verify
                sub_u = -float("inf")
                for post_a in actions:
                    if post_a == "verify":
                        continue
                    p_res = step_fn(
                        case=case,
                        action=post_a,
                        b_rem=v_res["b_rem"],
                        current_latency=v_res["latency"],
                        prior_cost=v_res["cost"],
                        evidence=v_res["evidence"],
                    )
                    if p_res["allowed"] and p_res["utility"] > sub_u:
                        sub_u = p_res["utility"]
                if sub_u > best_u:
                    best_u = sub_u
                    best_action = "verify"
            else:
                res = step_fn(case=case, action=a, b_rem=b_rem, prior_cost=0.0, evidence=None)
                if res["allowed"] and res["utility"] > best_u:
                    best_u = res["utility"]
                    best_action = a

        return best_action


def get_baseline_policies_v07() -> dict[str, BasePolicyV07]:
    """Returns registry of all 9 policies in CausaGuard v0.7."""
    return {
        "rules_proceed": RulesProceedPolicyV07(),
        "always_escalate": AlwaysEscalatePolicyV07(),
        "always_verify_then_proceed": AlwaysVerifyThenProceedPolicyV07(),
        "fixed_verify_repair_macro": FixedVerifyRepairMacroPolicyV07(),
        "always_recovery": AlwaysRecoveryPolicyV07(),
        "budget_aware_direct_recovery": BudgetAwareDirectRecoveryPolicyV07(),
        "cost_sensitive_threshold_recovery": CostSensitiveThresholdRecoveryPolicyV07(),
        "cost_rule_v07": CostRulePolicyV07(),
        "oracle": OraclePolicyV07(),
    }


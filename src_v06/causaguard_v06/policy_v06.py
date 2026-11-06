"""CausaGuard v0.6: Baseline & Decision-Theoretic Policy Suite.

Implements:
1. RulesProceedPolicy (fixed proceed baseline)
2. AlwaysEscalatePolicy (fixed risk-free escalation baseline)
3. AlwaysVerifyThenProceedPolicy (fixed verify baseline with admissible fallback)
4. FixedVerifyRepairMacroPolicy (ported historical v0.5 bundled macro)
5. RulesRepairPolicy (deterministic heuristic with budget-aware fallback)
6. CostRulePolicy (analytical Bayesian VOI policy, strictly zero outcome leakage)
7. OraclePolicy (diagnostic upper bound using latent realization)
"""

from __future__ import annotations

import abc
from dataclasses import asdict
from typing import Any

import numpy as np

from causaguard_v06.domain_cs import (
    ACTIONS_CS,
    CSCase,
    CSEvidence,
    CSObservation,
)
from causaguard_v06.domain_de import (
    ACTIONS_DE,
    DECase,
    DEEvidence,
    DEObservation,
)

R_LIMIT = 0.050


class BasePolicy(abc.ABC):
    """Abstract base class for CausaGuard v0.6 policies."""

    name: str

    @abc.abstractmethod
    def select(
        self,
        observation: CSObservation | DEObservation,
        evidence: CSEvidence | DEEvidence | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        """Selects next action given public observation, evidence, and remaining operation budget."""
        pass


class RulesProceedPolicy(BasePolicy):
    """Unconditionally selects proceed at step 1; post-verify proceeds if budget remains, else escalates."""

    name = "rules_proceed"

    def select(
        self,
        observation: CSObservation | DEObservation,
        evidence: CSEvidence | DEEvidence | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        if evidence is None:
            return "proceed"
        return "proceed" if b_rem >= 1 else "escalate"


class AlwaysEscalatePolicy(BasePolicy):
    """Unconditionally selects escalate (0 ops) at all steps."""

    name = "always_escalate"

    def select(
        self,
        observation: CSObservation | DEObservation,
        evidence: CSEvidence | DEEvidence | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        return "escalate"


class AlwaysVerifyThenProceedPolicy(BasePolicy):
    """Selects verify at Step 1; post-verify selects proceed if feasible, else admissible fallback to escalate."""

    name = "always_verify_then_proceed"

    def select(
        self,
        observation: CSObservation | DEObservation,
        evidence: CSEvidence | DEEvidence | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        if evidence is None:
            return "verify"
        return "proceed" if b_rem >= 1 else "escalate"


class FixedVerifyRepairMacroPolicy(BasePolicy):
    """Legacy v0.5 macro ported to v0.6 generative models.

    At B=1, detects B < 2 and defaults to proceed (or escalate if alarm is high).
    At B=2, calls verify; if flagged/corrupt, attempts recovery (retry/restore), else proceeds.
    """

    name = "fixed_verify_repair_macro"

    def select(
        self,
        observation: CSObservation | DEObservation,
        evidence: CSEvidence | DEEvidence | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        # Step 1: Pre-verification
        if evidence is None:
            if b_rem < 2:
                # B=1 boundary fallback: cannot verify without exhausting budget before repair
                if isinstance(observation, CSObservation):
                    return "escalate" if observation.conflict_alarm > 0.50 else "proceed"
                else:
                    return "escalate" if observation.schema_alarm > 0.50 else "proceed"
            return "verify"

        # Step 2: Post-verification
        if b_rem < 1:
            return "escalate"

        if isinstance(observation, CSObservation):
            assert isinstance(evidence, CSEvidence)
            return "retry" if evidence.flagged else "proceed"
        else:
            assert isinstance(evidence, DEEvidence)
            needs_repair = not evidence.schema_valid or evidence.sample_pass_rate < 0.80
            return "restore" if needs_repair else "proceed"


class RulesRepairPolicy(BasePolicy):
    """Deterministic heuristic baseline with explicit B=1 budget awareness.

    Triggers inspection on high alarm/age. At B=1, defaults to escalate.
    """

    name = "rules_repair"

    def select(
        self,
        observation: CSObservation | DEObservation,
        evidence: CSEvidence | DEEvidence | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        # Step 1: Pre-verification
        if evidence is None:
            if isinstance(observation, CSObservation):
                triggered = bool(
                    observation.conflict_alarm > 0.50 or observation.ticket_age_hours > 48.0
                )
            else:
                triggered = bool(
                    observation.schema_alarm > 0.50
                    or observation.data_age_hours > 48.0
                    or observation.column_count_changed == 1
                )

            if triggered:
                if b_rem >= 2:
                    return "verify"
                return "escalate"
            return "proceed"

        # Step 2: Post-verification
        if b_rem < 1:
            return "escalate"

        if isinstance(observation, CSObservation):
            assert isinstance(evidence, CSEvidence)
            return "retry" if evidence.flagged else "proceed"
        else:
            assert isinstance(evidence, DEEvidence)
            needs_repair = not evidence.schema_valid or evidence.sample_pass_rate < 0.80
            return "restore" if needs_repair else "proceed"


class CostRulePolicy(BasePolicy):
    """Analytical Bayesian Value of Information (VOI) baseline.

    Consumes strictly zero outcome labels or private simulator state.
    Evaluates closed-form expected utility for feasible actions before and after verification.
    Enforces operational risk constraint: P(Unsafe) <= R_LIMIT (0.050).
    Prunes verify when B=1 (strictly dominated).
    """

    name = "cost_rule"

    def select(
        self,
        observation: CSObservation | DEObservation,
        evidence: CSEvidence | DEEvidence | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        # Strict zero-leakage enforcement: reject Case objects or simulator references
        if isinstance(observation, (CSCase, DECase)):
            raise TypeError("CostRulePolicy accepts only Observation, not Case objects!")
        if kwargs.get("case") is not None:
            raise TypeError("CostRulePolicy prohibits private case argument!")
        if not isinstance(observation, (CSObservation, DEObservation)):
            raise TypeError(f"Invalid observation type: {type(observation)}")
        if evidence is not None and not isinstance(evidence, (CSEvidence, DEEvidence)):
            raise TypeError(f"Invalid evidence type: {type(evidence)}")

        if isinstance(observation, CSObservation):
            return self._select_cs(observation, evidence, b_rem)
        else:
            return self._select_de(observation, evidence, b_rem)

    def _select_cs(
        self,
        obs: CSObservation,
        evidence: CSEvidence | None,
        b_rem: int,
    ) -> str:
        # Estimated availability given public queue load
        a_0 = float(np.clip(1.0 - (0.02 + 0.45 * obs.queue_load), 0.05, 0.98))
        # Prior defect probability from alarm and age
        p_0 = float(
            np.clip(
                0.04 + 0.60 * (obs.conflict_alarm**2) + 0.28 * (obs.ticket_age_hours / 96.0),
                0.01,
                0.95,
            )
        )
        # Authoritative re-query recovery success rate estimate
        rho_cs = float(
            np.clip(0.35 + 0.45 * obs.source_reliability - 0.20 * obs.queue_load, 0.10, 0.95)
        )

        # Step 1: Pre-verification
        if evidence is None:
            # 1. Evaluate immediate terminal actions
            # proceed: eligible only if p_0 <= R_LIMIT
            if p_0 <= R_LIMIT:
                u_proceed = (
                    obs.value * a_0 * (1.0 - p_0)
                    - obs.harm * a_0 * p_0
                    - obs.apply_cost
                    - obs.time_cost_per_hour * 0.10
                )
            else:
                u_proceed = -float("inf")

            # retry: attempts re-fetch. If defect cured -> safe completion; if uncured -> incomplete, unsafe=0.
            # Effective operational risk is 0 <= R_LIMIT, always eligible.
            # Expected completion probability: clean stays clean (1-p0) + defective cured (~0.60 * p0 * rho_cs)
            p_comp_retry = (1.0 - p_0) + 0.60 * p_0 * rho_cs
            u_retry = (
                obs.value * a_0 * p_comp_retry
                - obs.retry_cost
                - obs.time_cost_per_hour * (0.25 + obs.queue_load)
            )

            # escalate: always eligible, 0 ops, risk 0
            u_escalate = -obs.escalation_cost - obs.time_cost_per_hour * 0.05

            best_term_u = max(u_proceed, u_retry, u_escalate)
            if best_term_u == u_proceed:
                best_term_action = "proceed"
            elif best_term_u == u_retry:
                best_term_action = "retry"
            else:
                best_term_action = "escalate"

            # Boundary constraint: if B = 1, verify is strictly dominated and MUST be pruned
            if b_rem < 2:
                return best_term_action

            # 2. Evaluate expected VOI of verify at B >= 2
            p_flag_1 = (1.0 - obs.quoted_fn) * p_0 + obs.quoted_fp * (1.0 - p_0)
            p_flag_0 = 1.0 - p_flag_1

            p_1_flag1 = ((1.0 - obs.quoted_fn) * p_0) / max(p_flag_1, 1e-9)
            p_1_flag0 = (obs.quoted_fn * p_0) / max(p_flag_0, 1e-9)

            latency_v = obs.observation_delay + 0.20

            # Step 2 utility given flag = 1
            u_post_retry_1 = (
                obs.value * a_0 * ((1.0 - p_1_flag1) + 0.60 * p_1_flag1 * rho_cs)
                - obs.retry_cost
                - obs.time_cost_per_hour * (latency_v + 0.25 + obs.queue_load)
            )
            u_post_esc_1 = -obs.escalation_cost - obs.time_cost_per_hour * (latency_v + 0.05)
            u_branch_1 = max(u_post_retry_1, u_post_esc_1)

            # Step 2 utility given flag = 0
            if p_1_flag0 <= R_LIMIT:
                u_post_proc_0 = (
                    obs.value * a_0 * (1.0 - p_1_flag0)
                    - obs.harm * a_0 * p_1_flag0
                    - obs.apply_cost
                    - obs.time_cost_per_hour * (latency_v + 0.10)
                )
            else:
                u_post_proc_0 = -float("inf")
            u_post_retry_0 = (
                obs.value * a_0 * ((1.0 - p_1_flag0) + 0.60 * p_1_flag0 * rho_cs)
                - obs.retry_cost
                - obs.time_cost_per_hour * (latency_v + 0.25 + obs.queue_load)
            )
            u_branch_0 = max(u_post_proc_0, u_post_retry_0, u_post_esc_1)

            u_verify = (
                p_flag_1 * u_branch_1
                + p_flag_0 * u_branch_0
                - obs.verify_cost
            )

            if u_verify > best_term_u:
                return "verify"
            return best_term_action

        # Step 2: Post-verification (b_rem must be >= 1)
        if b_rem < 1:
            return "escalate"

        # Bayesian posterior update
        if evidence.flagged:
            num = (1.0 - obs.quoted_fn) * p_0
            denom = num + obs.quoted_fp * (1.0 - p_0)
            p_1 = float(np.clip(num / max(denom, 1e-9), 0.0, 1.0))
        else:
            num = obs.quoted_fn * p_0
            denom = num + (1.0 - obs.quoted_fp) * (1.0 - p_0)
            p_1 = float(np.clip(num / max(denom, 1e-9), 0.0, 1.0))

        latency_so_far = obs.observation_delay + 0.20

        # proceed
        if p_1 <= R_LIMIT:
            u_proceed = (
                obs.value * a_0 * (1.0 - p_1)
                - obs.harm * a_0 * p_1
                - obs.apply_cost
                - obs.time_cost_per_hour * (latency_so_far + 0.10)
            )
        else:
            u_proceed = -float("inf")

        # retry
        p_comp_retry = (1.0 - p_1) + 0.60 * p_1 * rho_cs
        u_retry = (
            obs.value * a_0 * p_comp_retry
            - obs.retry_cost
            - obs.time_cost_per_hour * (latency_so_far + 0.25 + obs.queue_load)
        )

        # escalate
        u_escalate = -obs.escalation_cost - obs.time_cost_per_hour * (latency_so_far + 0.05)

        best_u = max(u_proceed, u_retry, u_escalate)
        if best_u == u_proceed:
            return "proceed"
        elif best_u == u_retry:
            return "retry"
        return "escalate"

    def _select_de(
        self,
        obs: DEObservation,
        evidence: DEEvidence | None,
        b_rem: int,
    ) -> str:
        # Availability given public pipeline load
        a_0 = float(np.clip(1.0 - (0.01 + 0.40 * obs.pipeline_load), 0.05, 0.98))

        # Component priors
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
            # 1. Evaluate immediate terminal actions
            # proceed: eligible only if prior_hazard <= R_LIMIT
            if prior_hazard <= R_LIMIT:
                u_proceed = (
                    obs.value * a_0 * (1.0 - prior_hazard)
                    - obs.harm * a_0 * prior_hazard
                    - obs.apply_cost
                    - obs.time_cost_per_hour * 0.10
                )
            else:
                u_proceed = -float("inf")

            # restore: rolls back staging to clean snapshot (0.40 V), safe, risk 0
            u_restore = (
                0.40 * obs.value * a_0
                - obs.restore_cost
                - obs.time_cost_per_hour * (0.20 + obs.pipeline_load)
            )

            # escalate: risk 0
            u_escalate = -obs.escalation_cost - obs.time_cost_per_hour * 0.05

            best_term_u = max(u_proceed, u_restore, u_escalate)
            if best_term_u == u_proceed:
                best_term_action = "proceed"
            elif best_term_u == u_restore:
                best_term_action = "restore"
            else:
                best_term_action = "escalate"

            # Boundary constraint: if B = 1, verify is strictly dominated and MUST be pruned
            if b_rem < 2:
                return best_term_action

            # 2. Evaluate expected VOI of verify at B >= 2
            p_clean = (1.0 - p_0_s) * (1.0 - p_0_c)
            latency_v = obs.observation_delay + 0.20

            # If clean, posterior hazard reduces to transient hazard p_0_t
            if p_0_t <= R_LIMIT:
                u_branch_clean = (
                    obs.value * a_0 * (1.0 - p_0_t)
                    - obs.harm * a_0 * p_0_t
                    - obs.apply_cost
                    - obs.time_cost_per_hour * (latency_v + 0.10)
                )
            else:
                u_branch_clean = -float("inf")

            u_branch_hazard = max(
                0.40 * obs.value * a_0
                - obs.restore_cost
                - obs.time_cost_per_hour * (latency_v + 0.20 + obs.pipeline_load),
                -obs.escalation_cost - obs.time_cost_per_hour * (latency_v + 0.05),
            )

            u_verify = (
                p_clean * max(u_branch_clean, u_branch_hazard)
                + (1.0 - p_clean) * u_branch_hazard
                - obs.verify_cost
            )

            if u_verify > best_term_u:
                return "verify"
            return best_term_action

        # Step 2: Post-verification (b_rem must be >= 1)
        if b_rem < 1:
            return "escalate"

        # Schema Bayesian update
        fn_s = 0.02
        fp_s = obs.quoted_schema_fp
        if evidence.schema_valid:
            num_s = fn_s * p_0_s
            denom_s = num_s + (1.0 - fp_s) * (1.0 - p_0_s)
        else:
            num_s = (1.0 - fn_s) * p_0_s
            denom_s = num_s + fp_s * (1.0 - p_0_s)
        p_1_s = float(np.clip(num_s / max(denom_s, 1e-9), 0.0, 1.0))

        # Content sampling Bayesian update via Beta likelihood ratio
        s = float(np.clip(evidence.sample_pass_rate, 0.001, 0.999))
        lr = float(6.3 * ((1.0 - s) ** 4) / max(s**15, 1e-12))
        lr = float(np.clip(lr, 1e-6, 1e6))
        p_1_c = float(np.clip((lr * p_0_c) / max(lr * p_0_c + (1.0 - p_0_c), 1e-9), 0.0, 1.0))

        # Transient hazard is undetectable by verify
        p_1_t = p_0_t

        post_hazard = float(1.0 - (1.0 - p_1_s) * (1.0 - p_1_c) * (1.0 - p_1_t))
        latency_so_far = obs.observation_delay + 0.20

        # proceed
        if post_hazard <= R_LIMIT:
            u_proceed = (
                obs.value * a_0 * (1.0 - post_hazard)
                - obs.harm * a_0 * post_hazard
                - obs.apply_cost
                - obs.time_cost_per_hour * (latency_so_far + 0.10)
            )
        else:
            u_proceed = -float("inf")

        # restore
        u_restore = (
            0.40 * obs.value * a_0
            - obs.restore_cost
            - obs.time_cost_per_hour * (latency_so_far + 0.20 + obs.pipeline_load)
        )

        # escalate
        u_escalate = -obs.escalation_cost - obs.time_cost_per_hour * (latency_so_far + 0.05)

        best_u = max(u_proceed, u_restore, u_escalate)
        if best_u == u_proceed:
            return "proceed"
        elif best_u == u_restore:
            return "restore"
        return "escalate"


class OraclePolicy(BasePolicy):
    """Diagnostic upper bound policy using realized potential outcomes."""

    name = "oracle"

    def select(
        self,
        observation: CSObservation | DEObservation,
        evidence: CSEvidence | DEEvidence | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        case = kwargs.get("case")
        if case is None or not isinstance(case, (CSCase, DECase)):
            raise ValueError("OraclePolicy requires 'case' keyword argument with Case instance.")

        from causaguard_v06.domain_cs import execute_cs_step
        from causaguard_v06.domain_de import execute_de_step

        is_cs = isinstance(case, CSCase)
        step_fn = execute_cs_step if is_cs else execute_de_step
        actions = ACTIONS_CS if is_cs else ACTIONS_DE

        # Step 2: Post-verification
        if evidence is not None:
            best_action = "escalate"
            best_u = -float("inf")
            for a in actions:
                if a == "verify":
                    continue
                res = step_fn(case, a, b_rem=b_rem, evidence=evidence)
                if res["utility"] > best_u:
                    best_u = res["utility"]
                    best_action = a
            return best_action

        # Step 1: Pre-verification
        best_first_action = "escalate"
        best_u = -float("inf")

        # 1. Test single-step terminal actions
        for a in actions:
            if a == "verify":
                continue
            res = step_fn(case, a, b_rem=b_rem)
            if res["utility"] > best_u:
                best_u = res["utility"]
                best_first_action = a

        # 2. If B >= 2, test verify followed by optimal terminal action
        if b_rem >= 2:
            v_res = step_fn(case, "verify", b_rem=b_rem)
            if v_res["allowed"] and not v_res["terminal"]:
                b_rem_2 = v_res["b_rem"]
                ev_2 = v_res["evidence"]
                c_2 = v_res["cost"]
                lat_2 = v_res["latency"]
                best_step2_u = -float("inf")
                for a2 in actions:
                    if a2 == "verify":
                        continue
                    res2 = step_fn(
                        case,
                        a2,
                        b_rem=b_rem_2,
                        current_latency=lat_2,
                        prior_cost=c_2,
                        evidence=ev_2,
                    )
                    if res2["utility"] > best_step2_u:
                        best_step2_u = res2["utility"]
                if best_step2_u > best_u:
                    best_first_action = "verify"

        return best_first_action


def get_baseline_policies() -> dict[str, BasePolicy]:
    """Returns mapping of all canonical v0.6 baseline policy instances."""
    return {
        "rules_proceed": RulesProceedPolicy(),
        "always_escalate": AlwaysEscalatePolicy(),
        "always_verify_then_proceed": AlwaysVerifyThenProceedPolicy(),
        "fixed_verify_repair_macro": FixedVerifyRepairMacroPolicy(),
        "rules_repair": RulesRepairPolicy(),
        "cost_rule": CostRulePolicy(),
        "oracle": OraclePolicy(),
    }


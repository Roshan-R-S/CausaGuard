"""CausaGuard PhD Roadmap Work Package 4: Baseline Policy Adapters.

Research-only baseline comparators and adapters for WP4 comparative evaluation:
1. AlwaysVerifyPolicyV07_1 (always_verify);
2. AlwaysEscalatePolicyV07_1 (always_escalate - imported from candidate package);
3. RulesProceedPolicyV07_1 (rules_proceed);
4. RulesRepairPolicyV07_1 (rules_repair);
5. OriginalCausaGuardPolicyV07_1 (original_causaguard);
6. ConservativeCausaGuardPolicyV07_1 (conservative_causaguard);
7. CostRulePolicyV07_1 (cost_rule_v07_1 - analytical Bayesian VOI reference from candidate package).

All research comparators are isolated here to keep the candidate controller (v0.7.1)
clean and identical to committed baseline e9578d8.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from causaguard_v07_1.domain_cs import CSCaseV07_1, CSEvidenceV07_1, CSObservationV07_1
from causaguard_v07_1.domain_de import DECaseV07_1, DEEvidenceV07_1, DEObservationV07_1
from causaguard_v07_1.policy_v07_1 import (
    AlwaysEscalatePolicyV07_1,
    BasePolicyV07_1,
    CostRulePolicyV07_1,
)

from causaguard.conservative import ConservativeConfig, ConservativePolicy
from causaguard.data import features, make_scenarios
from causaguard.domain import Scenario
from causaguard.policy import LearnedPolicy


def _validate_no_leakage(
    observation: Any,
    kwargs: dict[str, Any],
    policy_name: str = "Policy",
    evidence: Any = None,
    prohibit_case_kwarg: bool = False,
) -> None:
    """Enforces zero-latent-state leakage and input signature invariants."""
    if isinstance(observation, (CSCaseV07_1, DECaseV07_1)):
        raise TypeError(f"{policy_name} accepts only Observation, not Case objects!")
    if prohibit_case_kwarg and kwargs.get("case") is not None:
        raise TypeError(f"{policy_name} prohibits private case argument!")
    if not isinstance(observation, (CSObservationV07_1, DEObservationV07_1)):
        raise TypeError(f"Invalid observation type: {type(observation)}")
    if evidence is not None and not isinstance(evidence, (CSEvidenceV07_1, DEEvidenceV07_1)):
        raise TypeError(f"Invalid evidence type: {type(evidence)}")


class AlwaysVerifyPolicyV07_1(BasePolicyV07_1):
    """Universal verification-first comparator (Roadmap WP4 Comparator 1).

    At Step 1: verifies if budget permits (b_rem >= 2), otherwise falls back to
    proceed (or escalate if alarm is high).
    At Step 2: if evidence indicates defect/flagged, triggers recovery; else proceeds.
    """

    name = "always_verify"

    def select(
        self,
        observation: CSObservationV07_1 | DEObservationV07_1,
        evidence: CSEvidenceV07_1 | DEEvidenceV07_1 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        _validate_no_leakage(observation, kwargs, policy_name=self.name, evidence=evidence)
        is_cs = isinstance(observation, CSObservationV07_1)
        alarm = observation.conflict_alarm if is_cs else observation.schema_alarm
        rec_action = "retry" if is_cs else "restore"

        if evidence is None:
            if b_rem >= 2:
                return "verify"
            return "escalate" if alarm > 0.50 else "proceed"

        if b_rem < 1:
            return "escalate"

        if is_cs:
            assert isinstance(evidence, CSEvidenceV07_1)
            return rec_action if evidence.flagged else "proceed"
        else:
            assert isinstance(evidence, DEEvidenceV07_1)
            needs_repair = not evidence.schema_valid or evidence.sample_pass_rate < 0.80
            return rec_action if needs_repair else "proceed"


class RulesProceedPolicyV07_1(BasePolicyV07_1):
    """Hard rules only comparator (Roadmap WP4 Comparator 3).

    Unconditionally selects proceed at step 1; post-verify proceeds if budget remains, else escalates.
    """

    name = "rules_proceed"

    def select(
        self,
        observation: CSObservationV07_1 | DEObservationV07_1,
        evidence: CSEvidenceV07_1 | DEEvidenceV07_1 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        _validate_no_leakage(observation, kwargs, policy_name=self.name, evidence=evidence)
        if evidence is None:
            return "proceed"
        return "proceed" if b_rem >= 1 else "escalate"


class RulesRepairPolicyV07_1(BasePolicyV07_1):
    """Hard rules plus deterministic repair comparator (Roadmap WP4 Comparator 4).

    Deterministic alarm/age heuristic baseline with explicit B=1 budget awareness.
    Triggers inspection on high alarm/age. At B=1, defaults to escalate.
    """

    name = "rules_repair"

    def select(
        self,
        observation: CSObservationV07_1 | DEObservationV07_1,
        evidence: CSEvidenceV07_1 | DEEvidenceV07_1 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        _validate_no_leakage(observation, kwargs, policy_name=self.name, evidence=evidence)
        is_cs = isinstance(observation, CSObservationV07_1)
        rec_action = "retry" if is_cs else "restore"

        if evidence is None:
            if is_cs:
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

        if b_rem < 1:
            return "escalate"

        if is_cs:
            assert isinstance(evidence, CSEvidenceV07_1)
            return rec_action if evidence.flagged else "proceed"
        else:
            assert isinstance(evidence, DEEvidenceV07_1)
            needs_repair = not evidence.schema_valid or evidence.sample_pass_rate < 0.80
            return rec_action if needs_repair else "proceed"


_DEFAULT_LEARNED_POLICY_CACHE: dict[tuple[int, int], LearnedPolicy] = {}


def _get_cached_learned_policy(seed: int = 42, risk_limit: float = 0.05) -> LearnedPolicy:
    key = (seed, int(round(risk_limit * 10000)))
    if key not in _DEFAULT_LEARNED_POLICY_CACHE:
        scenarios = make_scenarios(32, seed=seed)
        _DEFAULT_LEARNED_POLICY_CACHE[key] = LearnedPolicy(
            risk_limit=risk_limit, seed=seed
        ).fit(scenarios, n_estimators=20)
    return _DEFAULT_LEARNED_POLICY_CACHE[key]


class OriginalCausaGuardPolicyV07_1(BasePolicyV07_1):
    """Original CausaGuard comparator (Roadmap WP4 Comparator 5).

    Multi-arm Random Forest regression policy with risk-gated reward maximization,
    ported from v0.5/v0.5.2 to the v0.7.1 shared observation and budget interface.
    """

    name = "original_causaguard"

    def __init__(
        self,
        base: LearnedPolicy | None = None,
        risk_limit: float = 0.05,
        seed: int = 42,
    ) -> None:
        self.risk_limit = risk_limit
        if base is None:
            self.base = _get_cached_learned_policy(seed=seed, risk_limit=risk_limit)
        else:
            self.base = base

    def select(
        self,
        observation: CSObservationV07_1 | DEObservationV07_1,
        evidence: CSEvidenceV07_1 | DEEvidenceV07_1 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        _validate_no_leakage(observation, kwargs, policy_name=self.name, evidence=evidence)
        is_cs = isinstance(observation, CSObservationV07_1)
        rec_action = "retry" if is_cs else "restore"

        if evidence is None:
            scenario = Scenario(
                amount=float(observation.harm * 100.0),
                authorization_confidence=float(
                    observation.source_reliability if is_cs else observation.source_quality
                ),
                note_risk_score=float(
                    observation.conflict_alarm if is_cs else observation.schema_alarm
                ),
                data_age_hours=float(
                    observation.ticket_age_hours if is_cs else observation.data_age_hours
                ),
                tool_error_rate=float(
                    observation.queue_load if is_cs else observation.pipeline_load
                ),
                schema_warning=bool(
                    observation.conflict_alarm > 0.50
                    if is_cs
                    else (observation.column_count_changed == 1 or observation.schema_alarm > 0.50)
                ),
                confirmation_present=True,
                seed=0,
            )
            x = np.stack([features(scenario)])
            rewards = {
                arm: float(self.base.reward_models[arm].predict(x)[0])
                for arm in ("proceed", "verify", "retry", "escalate")
            }
            risks = {
                arm: float(np.clip(self.base.risk_models[arm].predict(x)[0], 0, 1))
                for arm in ("proceed", "verify", "retry", "escalate")
            }
            # Budget-gated admissible action set (historical select_original formulation)
            eligible = [
                arm
                for arm in ("proceed", "verify", "retry", "escalate")
                if arm == "escalate"
                or (risks[arm] <= self.risk_limit and (arm == "proceed" or b_rem >= 2))
            ]

            def utility(arm: str) -> float:
                return -observation.escalation_cost if arm == "escalate" else rewards[arm]

            chosen = max(eligible, key=utility)
            if not is_cs and chosen == "retry":
                return "restore"
            return chosen

        if b_rem < 1:
            return "escalate"

        if is_cs:
            assert isinstance(evidence, CSEvidenceV07_1)
            return rec_action if evidence.flagged else "proceed"
        else:
            assert isinstance(evidence, DEEvidenceV07_1)
            needs_repair = not evidence.schema_valid or evidence.sample_pass_rate < 0.80
            return rec_action if needs_repair else "proceed"


class ConservativeCausaGuardPolicyV07_1(BasePolicyV07_1):
    """Conservative CausaGuard comparator (Roadmap WP4 Comparator 6).

    Random Forest ensemble tree disagreement abstention policy,
    ported from v0.5/v0.5.2 to the v0.7.1 shared observation and budget interface.
    """

    name = "conservative_causaguard"

    def __init__(
        self,
        base: LearnedPolicy | None = None,
        config: ConservativeConfig | None = None,
        seed: int = 42,
    ) -> None:
        self.config = config or ConservativeConfig(risk_limit=0.05)
        if base is None:
            self.base = _get_cached_learned_policy(seed=seed, risk_limit=self.config.risk_limit)
        else:
            self.base = base
        self.conservative = ConservativePolicy(self.base, self.config)

    def select(
        self,
        observation: CSObservationV07_1 | DEObservationV07_1,
        evidence: CSEvidenceV07_1 | DEEvidenceV07_1 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        _validate_no_leakage(observation, kwargs, policy_name=self.name, evidence=evidence)
        is_cs = isinstance(observation, CSObservationV07_1)
        rec_action = "retry" if is_cs else "restore"

        if evidence is None:
            scenario = Scenario(
                amount=float(observation.harm * 100.0),
                authorization_confidence=float(
                    observation.source_reliability if is_cs else observation.source_quality
                ),
                note_risk_score=float(
                    observation.conflict_alarm if is_cs else observation.schema_alarm
                ),
                data_age_hours=float(
                    observation.ticket_age_hours if is_cs else observation.data_age_hours
                ),
                tool_error_rate=float(
                    observation.queue_load if is_cs else observation.pipeline_load
                ),
                schema_warning=bool(
                    observation.conflict_alarm > 0.50
                    if is_cs
                    else (observation.column_count_changed == 1 or observation.schema_alarm > 0.50)
                ),
                confirmation_present=True,
                seed=0,
            )
            dec = self.conservative.recommend(scenario)
            chosen = dec.action
            if not is_cs and chosen == "retry":
                chosen = "restore"
            if chosen == "verify" and b_rem < 2:
                # When verification cannot be performed within budget, conservative abstention escalates
                return "escalate"
            return chosen

        if b_rem < 1:
            return "escalate"

        if is_cs:
            assert isinstance(evidence, CSEvidenceV07_1)
            return rec_action if evidence.flagged else "proceed"
        else:
            assert isinstance(evidence, DEEvidenceV07_1)
            needs_repair = not evidence.schema_valid or evidence.sample_pass_rate < 0.80
            return rec_action if needs_repair else "proceed"


def get_wp4_comparators_v07_1() -> dict[str, BasePolicyV07_1]:
    """Returns the comprehensive suite of all 6 PhD Roadmap Work Package 4 comparators

    plus the contextual learned reference:
    1. always_verify (AlwaysVerifyPolicyV07_1);
    2. always_escalate (AlwaysEscalatePolicyV07_1);
    3. rules_proceed (RulesProceedPolicyV07_1);
    4. rules_repair (RulesRepairPolicyV07_1);
    5. original_causaguard (OriginalCausaGuardPolicyV07_1);
    6. conservative_causaguard (ConservativeCausaGuardPolicyV07_1);
    7. cost_rule_v07_1 (CostRulePolicyV07_1 - analytical Bayesian VOI reference).
    """
    return {
        "always_verify": AlwaysVerifyPolicyV07_1(),
        "always_escalate": AlwaysEscalatePolicyV07_1(),
        "rules_proceed": RulesProceedPolicyV07_1(),
        "rules_repair": RulesRepairPolicyV07_1(),
        "original_causaguard": OriginalCausaGuardPolicyV07_1(),
        "conservative_causaguard": ConservativeCausaGuardPolicyV07_1(),
        "cost_rule_v07_1": CostRulePolicyV07_1(),
    }


get_roadmap_baseline_policies_v07_1 = get_wp4_comparators_v07_1

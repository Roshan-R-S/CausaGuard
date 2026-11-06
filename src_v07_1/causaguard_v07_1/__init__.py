"""CausaGuard v0.7.1: Isolated Sequential Causal Decision Benchmark.

Includes:
- Decomposed multi-attribute human escalation system;
- Customer Support (CS) and Data Engineering (DE) generative environments;
- Symmetric 8-policy benchmark comparison suite;
- Counterfactual paired potential-outcome evaluation with policy-order invariance.
"""

from causaguard_v07_1.domain_cs import (
    ACTIONS_CS_V07_1,
    OP_COSTS_CS_V07_1,
    PROFILES_CS_V07_1,
    CSCaseV07_1,
    CSEvidenceV07_1,
    CSObservationV07_1,
    execute_cs_step_v07_1,
    make_cs_cases_v07_1,
)
from causaguard_v07_1.domain_de import (
    ACTIONS_DE_V07_1,
    OP_COSTS_DE_V07_1,
    PROFILES_DE_V07_1,
    DECaseV07_1,
    DEEvidenceV07_1,
    DEObservationV07_1,
    execute_de_step_v07_1,
    make_de_cases_v07_1,
)
from causaguard_v07_1.escalation import (
    HumanEscalationParamsCS,
    HumanEscalationParamsDE,
    QueueState,
    execute_escalation_cs,
    execute_escalation_de,
)
from causaguard_v07_1.policy_v07_1 import (
    R_LIMIT_V07_1,
    AlwaysEscalatePolicyV07_1,
    AlwaysRecoveryPolicyV07_1,
    BasePolicyV07_1,
    BudgetAwareDirectRecoveryPolicyV07_1,
    CostRulePolicyV07_1,
    CostSensitiveSymmetricHeuristicPolicyV07_1,
    EscalationAwareDeterministicThresholdPolicyV07_1,
    FixedVerifyRepairMacroPolicyV07_1,
    OraclePolicyV07_1,
    get_baseline_policies_v07_1,
)
from causaguard_v07_1.study_v07_1 import (
    evaluate_cluster_v07_1,
    evaluate_potential_outcomes_v07_1,
    run_episode_v07_1,
)

__version__ = "0.7.1"

__all__ = [
    "__version__",
    "ACTIONS_CS_V07_1",
    "OP_COSTS_CS_V07_1",
    "PROFILES_CS_V07_1",
    "CSCaseV07_1",
    "CSEvidenceV07_1",
    "CSObservationV07_1",
    "make_cs_cases_v07_1",
    "execute_cs_step_v07_1",
    "ACTIONS_DE_V07_1",
    "OP_COSTS_DE_V07_1",
    "PROFILES_DE_V07_1",
    "DECaseV07_1",
    "DEEvidenceV07_1",
    "DEObservationV07_1",
    "make_de_cases_v07_1",
    "execute_de_step_v07_1",
    "HumanEscalationParamsCS",
    "HumanEscalationParamsDE",
    "QueueState",
    "execute_escalation_cs",
    "execute_escalation_de",
    "R_LIMIT_V07_1",
    "BasePolicyV07_1",
    "CostRulePolicyV07_1",
    "AlwaysEscalatePolicyV07_1",
    "AlwaysRecoveryPolicyV07_1",
    "BudgetAwareDirectRecoveryPolicyV07_1",
    "EscalationAwareDeterministicThresholdPolicyV07_1",
    "CostSensitiveSymmetricHeuristicPolicyV07_1",
    "FixedVerifyRepairMacroPolicyV07_1",
    "OraclePolicyV07_1",
    "get_baseline_policies_v07_1",
    "run_episode_v07_1",
    "evaluate_potential_outcomes_v07_1",
    "evaluate_cluster_v07_1",
]


"""CausaGuard v0.7: Scientific Agent Intervention & Recovery Package.

Isolates remediated dual-domain simulation environments, 9-policy fair comparator suite,
authentic customer friction/disruption mechanics, and decoupled outcome grading.
"""

from .domain_cs import (
    ACTIONS_CS_V07,
    PROFILES_CS_V07,
    CSCaseV07,
    CSEvidenceV07,
    CSObservationV07,
    execute_cs_step_v07,
    make_cs_cases_v07,
)
from .domain_de import (
    ACTIONS_DE_V07,
    PROFILES_DE_V07,
    DECaseV07,
    DEEvidenceV07,
    DEObservationV07,
    execute_de_step_v07,
    make_de_cases_v07,
)
from .policy_v07 import (
    AlwaysEscalatePolicyV07,
    AlwaysRecoveryPolicyV07,
    AlwaysVerifyThenProceedPolicyV07,
    BasePolicyV07,
    BudgetAwareDirectRecoveryPolicyV07,
    CostRulePolicyV07,
    CostSensitiveThresholdRecoveryPolicyV07,
    FixedVerifyRepairMacroPolicyV07,
    OraclePolicyV07,
    RulesProceedPolicyV07,
    get_baseline_policies_v07,
)
from .study_v07 import (
    evaluate_potential_outcomes_v07,
    generate_cases_v07,
    run_episode_v07,
)

__version__ = "0.7.0"
__all__ = [
    "ACTIONS_CS_V07",
    "ACTIONS_DE_V07",
    "PROFILES_CS_V07",
    "PROFILES_DE_V07",
    "CSObservationV07",
    "CSEvidenceV07",
    "CSCaseV07",
    "execute_cs_step_v07",
    "make_cs_cases_v07",
    "DEObservationV07",
    "DEEvidenceV07",
    "DECaseV07",
    "execute_de_step_v07",
    "make_de_cases_v07",
    "BasePolicyV07",
    "RulesProceedPolicyV07",
    "AlwaysEscalatePolicyV07",
    "AlwaysVerifyThenProceedPolicyV07",
    "FixedVerifyRepairMacroPolicyV07",
    "AlwaysRecoveryPolicyV07",
    "BudgetAwareDirectRecoveryPolicyV07",
    "CostSensitiveThresholdRecoveryPolicyV07",
    "CostRulePolicyV07",
    "OraclePolicyV07",
    "get_baseline_policies_v07",
    "evaluate_potential_outcomes_v07",
    "generate_cases_v07",
    "run_episode_v07",
]


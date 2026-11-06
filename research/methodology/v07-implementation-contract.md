# CausaGuard v0.7: Engineering Implementation Contract

**Status:** Official Engineering Implementation Contract  
**Version:** `0.7.0-draft`  
**Date:** 5 November 2026  
**Parent Documents:** [`v07-research-specification.md`](v07-research-specification.md), [`v07-statistical-analysis-plan.md`](v07-statistical-analysis-plan.md)  
**Historical Dependencies:** Sealed v0.6 Protocol (`c0f217ca...`) and Historical v0.5.2 Freeze (`053dea36...`) strictly preserved  

---

## 1. Scope and Architectural Isolation

This contract governs the future implementation of **CausaGuard v0.7**. In accordance with research integrity standards:
- **Zero Modifications to v0.5 or v0.6:** The historical codebases (`src/causaguard/`, `src_v06/causaguard_v06/`), test suites (`tests/`, `tests_v06/`), and protocol records (`experiments_v06/`) are strictly read-only and immutable.
- **Isolated Target Namespaces:** All v0.7 code, tests, and runners must be created exclusively within dedicated v0.7 directories:
  - Source package: `src_v07/causaguard_v07/`
  - Test suite: `tests_v07/`
  - Experiments & runners: `experiments_v07/`
  - Artifact outputs: `artifacts_v07/`

```
d:\causaguard\
├── src_v07/causaguard_v07/
│   ├── __init__.py               # Exports core classes and domain runners
│   ├── domain_cs.py              # Customer support domain with customer friction
│   ├── domain_de.py              # Data engineering domain with schema/restore split
│   ├── policy_v07.py             # 9-policy suite with fair direct-recovery baselines
│   └── study_v07.py              # Cluster simulation, telemetry, and paired analysis
├── tests_v07/
│   ├── test_cs_domain.py         # CS friction, abandonment, and salvage tests
│   ├── test_de_domain.py         # DE schema drift, rollback, and engineer fix tests
│   ├── test_policy_fairness.py   # Information isolation and zero-leakage tests
│   ├── test_rare_event_risk.py   # Statistical bounds and GEE/Clopper-Pearson tests
│   ├── test_evaluate_dev.py      # Runner integration and seed isolation tests
│   └── test_identity_preservation.py # Historical v0.5.2 and v0.6 seal verification
└── experiments_v07/
    ├── v07_protocol.json         # Locked protocol definition
    ├── audit_power.py            # Exploratory variance calibration CLI
    └── evaluate_dev.py           # Confirmatory development evaluation runner CLI
```

---

## 2. Public Interfaces and Data Contracts

### 2.1 Customer Support Domain Interface (`domain_cs.py`)

```python
from dataclasses import dataclass
from typing import Any

ACTIONS_CS_V07 = ("proceed", "verify", "retry", "escalate")
OP_COSTS_CS = {"proceed": 1, "verify": 1, "retry": 1, "escalate": 0}

@dataclass(frozen=True)
class CSObservationV07:
    ticket_age_hours: float
    conflict_alarm: float
    source_reliability: float
    queue_load: float
    quoted_fp: float
    quoted_fn: float
    observation_delay: float
    deadline_hours: float
    value: float
    harm: float
    apply_cost: float
    verify_cost: float
    retry_cost: float
    escalation_cost: float
    time_cost_per_hour: float
    budget: int  # Must be 1 or 2

@dataclass(frozen=True)
class CSEvidenceV07:
    flagged: bool
    evidence_age_hours: float
    check_type: str = "consistency"

def execute_cs_step_v07(
    case: Any,
    action: str,
    b_rem: int,
    current_latency: float = 0.0,
    prior_cost: float = 0.0,
    evidence: CSEvidenceV07 | None = None,
) -> dict[str, Any]:
    """Executes single transition step with friction, abandonment, and human salvage."""
    ...
```

### 2.2 Data Engineering Domain Interface (`domain_de.py`)

```python
from dataclasses import dataclass
from typing import Any

ACTIONS_DE_V07 = ("proceed", "verify", "restore", "escalate")
OP_COSTS_DE = {"proceed": 1, "verify": 1, "restore": 1, "escalate": 0}

@dataclass(frozen=True)
class DEObservationV07:
    data_age_hours: float
    schema_alarm: float
    source_quality: float
    pipeline_load: float
    column_count_changed: int
    quoted_schema_fp: float
    quoted_content_fn: float
    observation_delay: float
    deadline_hours: float
    value: float
    harm: float
    apply_cost: float
    verify_cost: float
    restore_cost: float
    escalation_cost: float
    time_cost_per_hour: float
    budget: int  # Must be 1 or 2

@dataclass(frozen=True)
class DEEvidenceV07:
    schema_valid: bool
    sample_pass_rate: float
    validation_timestamp_lag: float
    check_type: str = "schema+sample"

def execute_de_step_v07(
    case: Any,
    action: str,
    b_rem: int,
    current_latency: float = 0.0,
    prior_cost: float = 0.0,
    evidence: DEEvidenceV07 | None = None,
) -> dict[str, Any]:
    """Executes single transition step with schema persistence and engineer intervention."""
    ...
```

### 2.3 Policy Interface (`policy_v07.py`)

```python
import abc

class BasePolicyV07(abc.ABC):
    name: str

    @abc.abstractmethod
    def select(
        self,
        observation: CSObservationV07 | DEObservationV07,
        evidence: CSEvidenceV07 | DEEvidenceV07 | None = None,
        b_rem: int = 1,
        **kwargs: Any,
    ) -> str:
        """Selects action given public observation, evidence, and remaining budget."""
        pass
```

---

## 3. Mandatory Mathematical and Behavioral Invariants

### 3.1 Unitary Budget Accounting Invariant
- Every action execution must subtract `OP_COSTS[action]` from $b_{\text{rem}}$.
- Attempting any action when $b_{\text{rem}} < \text{cost}$ must immediately terminate the episode with `allowed = False, reason = "operation_budget"`.
- Escalation costs 0 operations and terminates immediately.
- Verification costs 1 operation and is non-terminal (requires $b_{\text{rem}} \ge 2$ at Step 1 to allow subsequent physical action).

### 3.2 Action Feasibility and Pruning Invariant
- **At $B = 1$:** `verify` is **strictly dominated** (verifying leaves $b_{\text{rem}} = 0$, forcing human escalation with wasted verification cost). All rational policies (`cost_rule_v07`, `budget_aware_direct_recovery`) must prune `verify` when $B = 1$, selecting directly from $\{\text{proceed}, \text{recovery}, \text{escalate}\}$.

### 3.3 Zero Information Leakage Invariant
- Policies (except privileged diagnostic oracle) must reject any input containing latent variables (`Case` objects, defect flags, random tape draws, ground truth state).
- An explicit type assertion `assert isinstance(observation, (CSObservationV07, DEObservationV07))` must be enforced at the entry point of every policy.

### 3.4 Baseline Fairness Invariant
- Every baseline policy must receive the exact same observation $X$, budget $B$, and evidence $E$ as the candidate policy.
- No baseline may be artificially restricted to an inferior action set: all 9 policies must have legal access to direct recovery (`retry` / `restore`) at Step 1.

---

## 4. Required Unit and Integration Test Specifications

The future implementation must pass a comprehensive test suite in `tests_v07/`:

| Test Module | Required Test Cases | Invariant Verified |
|---|---|---|
| **`test_cs_domain.py`** | `test_clean_retry_friction_dropout`<br>`test_clean_retry_discount`<br>`test_fraud_incurable_by_retry`<br>`test_human_salvage_on_fraud`<br>`test_permission_revocation` | Proves clean retry causes friction/abandonment; proves fraud cannot be cured by retry; proves escalation salvages fraud. |
| **`test_de_domain.py`** | `test_schema_drift_restore_persistent_failure`<br>`test_content_corruption_restore_success`<br>`test_human_engineer_schema_fix`<br>`test_transient_hazard_unobservable` | Proves restore fails on schema drift; proves restore fixes content corruption; proves engineer fixes schema. |
| **`test_policy_fairness.py`** | `test_zero_latent_leakage_assertion`<br>`test_all_baselines_execute_direct_recovery`<br>`test_b1_budget_pruning_rule`<br>`test_oracle_matches_diagnostic_upper_bound` | Asserts no private state is leaked; asserts baselines can choose direct recovery; verifies B=1 pruning. |
| **`test_rare_event_risk.py`** | `test_tier1_clopper_pearson_monotonicity`<br>`test_tier2_fay_graubard_gee_coverage`<br>`test_zero_event_bound_strictly_below_050` | Asserts exact cluster Clopper-Pearson bound $\le 0.050$ at $K=64$; validates GEE small-sample correction. |
| **`test_identity_preservation.py`** | `test_v052_report_and_seal_unaltered`<br>`test_v06_protocol_and_seal_unaltered`<br>`test_pyproject_toml_byte_identical` | Asserts historical v0.5.2 and v0.6 seals and pyproject.toml hash remain 100% byte-identical. |
| **`test_evaluate_dev.py`** | `test_dev_seeds_strictly_in_7001_7002`<br>`test_final_seeds_fatal_error_on_access`<br>`test_runner_smoke_test_mock_cases` | Verifies seed isolation; triggers fatal assertion if `7003xxxx` or `7004xxxx` or `6003xxxx` is accessed. |

---

## 5. Scientific Assumptions Requiring Sensitivity Audit

The following parameters must be exposed as configurable kwargs in `domain_cs.py` and `domain_de.py` to allow automated sensitivity grid scanning during exploratory calibration:

1. **`p_friction_base`** (CS clean retry friction intercept): Planning $0.15$, sensitivity range $[0.05, 0.40]$.
2. **`p_abandonment`** (CS customer abandonment rate): Planning $0.25$, sensitivity range $[0.10, 0.45]$.
3. **`p_salvage_fraud`** (CS human fraud salvage rate): Planning $0.70$, sensitivity range $[0.40, 0.90]$.
4. **`v_fallback_ratio`** (DE rollback fallback completion value): Planning $0.45$, sensitivity range $[0.20, 0.60]$.
5. **`p_schema_persistent_fail`** (DE rollback failure on schema drift): Planning $0.80$, sensitivity range $[0.50, 0.95]$.
6. **`p_engineer_fix_schema`** (DE human engineer schema fix rate): Planning $0.85$, sensitivity range $[0.60, 0.95]$.

---

## 6. Acceptance Criteria for Future Engineering Package

Future implementation packages (e.g. Package 7A / Package 7B) may be accepted **only** if all of the following conditions are met:
1. **Isolated Codebase:** 100% of new code is located in `src_v07/`, `tests_v07/`, `experiments_v07/`. Zero lines edited in `src/` or `src_v06/`.
2. **Test Suite Execution:** 100% of unit and integration tests in `tests_v07/` pass with zero failures or warnings.
3. **Historical Seal Invariance:** Tests verifying v0.5.2 seal (`053dea36...`), v0.6 seal (`c0f217ca...`), amendment 01 seal (`a5cb7ab9...`), and pyproject.toml hash pass cleanly.
4. **Quarantine Verification:** Automated assertions verify that v0.6 final seeds (`60030001–60040064`) and v0.7 final seeds (`70030001–70040064`) are **never touched or generated**.
5. **Exploratory Variance Audit:** Exploratory power audit on `70001001–70001016` must estimate $S_D$ and verify that $K = 64$ provides $\ge 80\%$ power before protocol freeze.


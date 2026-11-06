# CausaGuard v0.6 Isolated Development Testing Guide

## 1. Overview and Architecture

CausaGuard v0.6 introduces isolated Engineering Package 1 (`src_v06/causaguard_v06/` and `tests_v06/`), implementing:
- Unitary operation budget accounting ($B \in \{1, 2\}$)
- Customer Support (`domain_cs.py`): fallible consistency verification, authoritative re-query recovery ($\rho_{\text{cs}}$), independent ACL outcome grading
- Data Engineering (`domain_de.py`): 4-variable multivariate failure states ($F_s, F_c, F_m, F_t$), zero mutual-information detection ceiling on transient hazard, checkpoint snapshot rollback ($0.40 V$), decoupled 3-way grading
- Baseline Policy Suite (`policy_v06.py`): `rules_proceed`, `always_escalate`, `always_verify_then_proceed`, `fixed_verify_repair_macro`, `rules_repair`, `cost_rule` (analytical Bayesian VOI with zero outcome leakage), and diagnostic `oracle`
- Study Infrastructure (`study_v06.py`): reproducible episode generation, paired potential outcomes, and strict permutation invariance

## 2. Cryptographic Preservation Boundaries

To maintain scientific integrity and prevent historical identity disruption:
- Root `pyproject.toml` is **100% byte-identical** and never modified.
- Historical code under `src/causaguard/`, historical tests under `tests/`, and frozen artifacts under `artifacts/` remain untouched.
- Historical v0.5.2 development freeze seal is preserved:
  `053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6`
- The prohibited v0.5.2 final evaluation is never executed.
- Final evaluations, benchmarks, and model training are not executed in this development package.

## 3. How to Run Isolated Tests

All tests are executed using the dedicated `pytest_v06.ini` configuration to keep the v0.6 testing namespace completely isolated from legacy v0.5 test suites.

### 3.1 Run Full v0.6 Test Suite
```bash
uv run pytest -c pytest_v06.ini tests_v06
```

### 3.2 Run Verbose Test Suite
```bash
uv run pytest -c pytest_v06.ini -v tests_v06
```

### 3.3 Run Specific Test Modules

- **Historical Cryptographic Identity Preservation:**
  ```bash
  uv run pytest -c pytest_v06.ini tests_v06/test_identity_preservation.py
  ```

- **Customer Support Domain Mechanics & Graders:**
  ```bash
  uv run pytest -c pytest_v06.ini tests_v06/test_cs_domain.py
  ```

- **Data Engineering Domain Mechanics & Rollback:**
  ```bash
  uv run pytest -c pytest_v06.ini tests_v06/test_de_domain.py
  ```

- **Budget Feasibility, Dominated Actions & Admissible Fallbacks:**
  ```bash
  uv run pytest -c pytest_v06.ini tests_v06/test_feasibility.py
  ```

- **Analytical Bayesian VOI Policy & Zero-Leakage Checks:**
  ```bash
  uv run pytest -c pytest_v06.ini tests_v06/test_cost_rule.py
  ```

- **Study Infrastructure, All Paths & Permutation Invariance:**
  ```bash
  uv run pytest -c pytest_v06.ini tests_v06/test_study_v06.py
  ```

## 4. Test Suite Composition and Invariants

| Module | Purpose | Key Invariants Verified |
|---|---|---|
| `test_identity_preservation.py` | Historical integrity verification | Preserves v0.5.2 seal `053dea36...`; `pyproject.toml` hash unchanged; `validate_report()` succeeds. |
| `test_cs_domain.py` | Customer Support environment | Unitary costs (`proceed`=1, `verify`=1, `retry`=1, `escalate`=0); fallible verification; authoritative re-query recovery ($\rho_{\text{cs}}$); independent ACL access checks; zero authorization violations. |
| `test_de_domain.py` | Data Engineering environment | 4-channel failure generator ($F_s, F_c, F_m, F_t$); undetectable transient hazard has zero mutual information with evidence; checkpoint snapshot rollback yields clean state and $0.40 V$ fallback utility. |
| `test_feasibility.py` | Budget feasibility & domination | Total ops consumed $\le B$; $U(\text{verify}\to\text{escalate}) < U(\text{escalate})$ strictly holds across all cases; admissible fallbacks for all structural policies at $B=1$. |
| `test_cost_rule.py` | Bayesian decision theory | Rejects private `Case` objects and simulator state (`TypeError`); masks out dominated `verify` at $B=1$; enforces $P(\text{Unsafe}) \le 0.050$; deterministic updates. |
| `test_study_v06.py` | Paired evaluation & study harness | Deterministic case generation across shift profiles; all-path potential outcome tree generation; bitwise permutation invariance across policy execution orders. |


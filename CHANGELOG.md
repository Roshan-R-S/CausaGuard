# Changelog

All notable changes to the CausaGuard research project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.7.1-alpha.1] - 2026-11-07

### Added
- **First Public Research Alpha Release** (`v0.7.1-alpha.1`) of the isolated CausaGuard research platform.
- **Decomposed Multi-Attribute Human Escalation Engine** ([`causaguard_v07_1/escalation.py`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/escalation.py)):
  - Realistic human queuing latency, base handling fees, drop penalties, and capacity thresholds ($M=150$).
  - Domain-specific escalation parameterizations: `HumanEscalationParamsDE` and `HumanEscalationParamsCS`.
  - Independent `QueueState` tracking per policy to guarantee zero cross-policy interference.
- **Restored Symmetric Heuristic Baseline** (`CostSensitiveSymmetricHeuristicPolicyV07_1`):
  - Solves the baseline asymmetry identified in Package 6E by granting the heuristic equal Step-1 escalation access.
- **Confirmatory Evaluation Runner** ([`experiments_v07_1/evaluate_confirmatory_v07_1.py`](file:///d:/causaguard/experiments_v07_1/evaluate_confirmatory_v07_1.py)):
  - Full CLI interface for Primary Confirmatory Domain (`de`, $K=128$) and Secondary Boundary Domain (`cs`, $K=128$).
  - Embedded pre-freeze execution lock that strictly blocks execution on unsealed confirmatory seeds (`70100001+`).
  - Strict quarantine enforcement rejecting all reserved final evaluation seeds (`70200001+`).
  - Two-stage gatekeeping inference (Gate 1: Clustered Operational Risk $\le 0.050$, Auth Violations $== 0$; Gate 2: Paired Student-$t$ Superiority Hurdle $\Delta > +0.015$).
- **Rigorous Statistical Corrections** ([`research/methodology/v071-pre-freeze-statistical-corrections.md`](file:///d:/causaguard/research/methodology/v071-pre-freeze-statistical-corrections.md)):
  - Fréchet-Bonferroni lower bound derivation proving joint study success probability $\ge 92.52\%$.
  - Cluster-robust operational risk estimation and exact cluster-level Clopper-Pearson bound ($1 - 0.05^{1/128} = 0.02314 \le 0.050$) in zero-event regimes.
- **Interactive Synthetic Research Demonstration** ([`demo_v07_1.py`](file:///d:/causaguard/demo_v07_1.py)):
  - Safe, offline walkthrough of single-case counterfactual decisions and aggregate cluster trade-offs across all 8 benchmark policies using non-evaluative reserve seeds (`70003001+`).
- **Comprehensive Isolated Test Suite** ([`tests_v07_1/test_confirmatory_runner_v07_1.py`](file:///d:/causaguard/tests_v07_1/test_confirmatory_runner_v07_1.py)):
  - 20 unit and integration tests for execution locks, numerical hand calculations, gatekeeping logic, and synthetic fixtures.
  - Total passing tests across repository: 128 (59 in v0.7.1, 35 in v0.7, 34 in v0.6).
- **Cross-Platform Line-Ending Preservation** ([`.gitattributes`](file:///d:/causaguard/.gitattributes)):
  - Minimal path-scoped attributes ensuring platform-independent CRLF preservation for historical `v06-statistical-protocol.md` and LF normalization for modern paths.

### Changed
- Isolated `src_v07_1/causaguard_v07_1` as a self-contained, clean analytical research engine.
- Reconciled sample size planning from exploratory calibration to $K=128$ clusters per domain ($51{,}200$ cases per domain).

---

## [0.7.0] - 2026-11-06

### Added
- Analytical Bayesian Value of Information (VOI) decision engine (`src_v07/causaguard_v07/policy_v07.py`).
- Two synthetic operational POMDP domains: Data Engineering batch pipelines (`domain_de.py`) and Customer Support ticket triage (`domain_cs.py`).
- Exploratory variance calibration runner on authorized seeds `70001001–70001016` ($K=16$).
- Independent scientific review ([`research/reviews/v07-independent-scientific-review.md`](file:///d:/causaguard/research/reviews/v07-independent-scientific-review.md)) and protocol-freeze readiness audit ([`research/methodology/v07-protocol-freeze-readiness.md`](file:///d:/causaguard/research/methodology/v07-protocol-freeze-readiness.md)) identifying escalation dominance and sample-sizing blockers.

---

## [0.6.0] - 2026-11-04

### Added
- Cryptographic protocol freeze (`experiments_v06/v06_protocol_seal.json`, SHA-256 root `c0f217ca...`).
- Amendment 01 prospective registration (`experiments_v06/v06_amendment_01_seal.json`, SHA-256 root `a5cb7ab9...`).
- Development evaluation runner (`experiments_v06/evaluate_dev.py`) and invariant test suite (`tests_v06/test_evaluate_dev.py`).
- 34 passing isolated unit and invariant tests (`pytest_v06.ini`).

---

## [0.5.2] - 2026-11-03

### Added
- Factorial closeout protocol and historical cryptographic identity freeze (`artifacts/v052/development-frozen.json`, SHA-256 root `053dea36...`).
- Preservation guarantees for historical v0.1–v0.5 artifacts.

---

## [0.5.0] - 2026-11-02

### Added
- Initial fallible-verification intervention research laboratory.
- Contextual learning vs deterministic recovery comparisons across 11 policy variants.


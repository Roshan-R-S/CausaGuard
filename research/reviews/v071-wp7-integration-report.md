# CausaGuard v0.7.1 — Work Package 7 Integration & Handover Report

> [!IMPORTANT]
> **Scientific Status: PRE-FREEZE NO-GO**  
> Governing Document: CausaGuard PhD Research Master Roadmap 2026, Section 13 (WP7, p. 17).  
> Implementation Requirement: *"Optional existing local Qwen3 demonstration, additive CLI, docs and tests."*  
> Acceptance Gate: *"All historical tests remain passing."*

---

## 1. Executive Summary & Acceptance Verification

This report documents the completion of **Work Package 7 (Integration)** under Section 13 of the CausaGuard PhD Research Master Roadmap 2026 and establishes the verified engineering baseline for the complete WP1–WP7 programme.

### Roadmap Requirements Matrix

| Requirement (Section 13, p. 17) | Implementation Location | Verified Status |
| :--- | :--- | :--- |
| **Optional local Qwen3 demonstration** | `src/causaguard/llm.py`, `src/causaguard/guarded_agent.py`, `tests/test_llm_live.py` | **PASS (Architecture verified; live tests skipped)**. Local Qwen3 GGUF/llama.cpp loopback client implemented; mock agent tool interception passing (112 tests). Live Qwen3 tests conditionally skipped (`CAUSAGUARD_LIVE_LLM=1` inactive). |
| **Additive CLI commands** | `src/causaguard/cli.py`, `research/experiments/wp7_integration/demonstration.py` | **PASS (Added & verified)**. Added `wp7-demo` and `wp7-replay` subparsers; all historical CLI arguments and behaviors remain 100% identical. |
| **Integration Documentation** | `research/reviews/v071-wp7-integration-report.md` | **PASS (Complete)**. Complete architectural specification, security boundaries, and handover records. |
| **Focused Integration Tests** | `tests_v07_1/test_wp7_integration.py` | **PASS (8/8 passed in 8.08s)**. Verifies zero-leakage, fail-closed authorization, simulation execution, metrics, additive CLI, exploratory seed floor, and tamper-detection replay. |
| **Acceptance Gate: Historical Tests** | Full `tests/` and full `tests_v07_1/` | **PASS (All passing)**. 480 passed in core `tests/`; 514 passed in `tests_v07_1/`. Zero regression. |

---

## 2. Six-Step End-to-End Pipeline Architecture

The integration pipeline connects the six core requirements in an explicit, non-production in-memory simulation:

```
[Public Observation] ---> [MockAgentV07_1] ---> [Agent Proposal: "proceed" / "verify"]
                                                       |
[Case + State] ---------> [IndependentAuthorizationGuard] ---> [Allowed / Blocked?]
                                                       |
                                               (If Allowed)
                                                       v
                          [Intervention Policy] ---> [Action Decision]
                                                       |
                                                       v
                          [Simulated Environment] ---> [execute_step (CS/DE)]
                                                       |
                                                       v
                          [Outcome Evidence, Costs, Latency, Utility Recorded]
                                                       |
                                                       v
                          [JSON Trace Sealed + Bitwise Replay Verification]
```

1. **Mock Agent Public Context (`MockAgentV07_1`):**
   - Receives strictly public observation context (`CSObservationV07_1` or `DEObservationV07_1`).
   - Enforces zero-latent state leakage: passing full `Case` objects or hidden generative parameters raises `TypeError`.
   - Proposes intended actions based on public risk and cost signals.

2. **Independent Authorization Boundary (`IndependentAuthorizationGuardV07_1`):**
   - Decoupled from agent proposals and policy recommendation logic; model text cannot grant or modify permissions.
   - Evaluates independent access contracts (`_check_independent_access` in CS and DE).
   - **Fail-Closed Enforcement:** Missing confirmation, unauthorized state, principal mismatch, or malformed arguments immediately block execution (`allowed=False, reason="independent_authorization_denied"`), halting before any simulation step.

3. **Intervention Policy Decision:**
   - Evaluates feasible actions permitted by authorization.
   - Supports baseline policies (`rules_repair`, `always_verify`, `always_escalate`), the analytical Bayesian VOI controller (`cost_rule_v07_1`), and the trained contextual model (`contextual_full`).

4. **Simulated In-Memory Execution:**
   - Executes through domain executors (`execute_cs_step_v07_1` or `execute_de_step_v07_1`).
   - Supports multi-step verification recovery (`verify` $\rightarrow$ evidence $\rightarrow$ post-verification action).
   - Confined strictly to Python memory (`MockState`, `QueueState`). No external tools, network, or OS modifications.

5. **Recorded Outcome Evidence, Costs, and Latency:**
   - Records wall-clock execution time (`elapsed_ms`), operational costs, execution latency, safe completion, operational risk, evidence records, and cryptographic digests.

6. **Deterministic Reproduction & Tamper-Detection Replay:**
   - Traces are serialized to JSON.
   - `replay_wp7_demonstration` enforces a two-sided verification check:
     1. **Trace Integrity Check:** Recomputes the expected digest from the recorded case fields; any manual alteration to utility, proposal, or decisions triggers `tampered_trace_digest_mismatch`.
     2. **Replay Execution Match:** Re-executes the simulation with identical seeds; any divergence between recorded and replayed digests triggers `replay_execution_mismatch`.
   - Tampered or corrupted traces cannot silently report a successful match.

---

## 3. Disclosed Limitations of the Authorization Demonstration

> [!WARNING]
> **Boundary Limitation:** The authorization wrapper `IndependentAuthorizationGuardV07_1` reuses the domain permission function `_check_independent_access` implemented in `domain_cs.py` and `domain_de.py`.
> - It evaluates synthetic in-memory permission fields (`state.authorized`, `state.confirmation_present`, principal match, attempt limits).
> - It is **not** an enterprise production authorization engine (such as Cedar, OPA, or OAuth/ABAC policy engines).
> - It does **not** provide cryptographically signed independent outcome grading or formal compliance guarantees.
> - Findings are valid within the research simulator and do not establish external deployment safety.

---

## 4. Live-Agent Validation Status

Pursuant to scientific integrity standards:
- **Local Qwen3/llama.cpp Architecture:** Fully implemented in `src/causaguard/llm.py` (`LlamaCppClient`), `src/causaguard/guarded_agent.py`, and `src/causaguard/llm_commands.py`.
- **Mock LLM Integration:** Fully verified and passing (112 offline tests in `tests/test_cli.py`, `tests/test_guarded_agent.py`, `tests/test_llm.py`, `tests/test_llm_api_cli.py`, `tests/test_llm_benchmark.py`, `tests/test_llm_trace.py`).
- **Live Qwen3 Execution:** Tests in `tests/test_llm_live.py` are gated by `@pytest.mark.skipif(os.environ.get("CAUSAGUARD_LIVE_LLM") != "1")`. In this environment, `CAUSAGUARD_LIVE_LLM` was not active; therefore, **6 live tests were skipped**. Live inference was not executed during this verification turn.

---

## 5. Additive CLI Usage Reference

### Demonstration Execution
```bash
# Run demonstration across Customer Support and Data Engineering with rules_repair
uv run causaguard wp7-demo --domain both --policy rules_repair --n-cases 5 --output artifacts/wp7-demo.json

# Run demonstration with the trained contextual ML model
uv run causaguard wp7-demo --domain both --policy contextual_full --n-cases 5 --output artifacts/wp7-demo-contextual.json
```

### Trace Replay Verification
```bash
# Replay saved trace and verify exact bitwise reproducibility and digest integrity
uv run causaguard wp7-replay artifacts/wp7-demo.json
```

---

## 6. WP1–WP7 Engineering Status Summary

The complete actionable engineering scope from Roadmap Section 13 (page 17) is verified and complete:

| Work Package | Title | Description | Engineering Status |
| :--- | :--- | :--- | :--- |
| **WP1** | Formal Protocol | Formal action/observation/cost model; hypotheses, seeds, metrics, and baseline rules. | **COMPLETE** |
| **WP2** | Environment | Fallible verifier, asymmetric errors, latency, heterogeneous costs, delays, hidden states. | **COMPLETE** |
| **WP3** | Pilot Domains | Customer Support and Data Engineering exposing shared intervention interface and mock grader. | **COMPLETE** |
| **WP4** | Baselines | Always verify, always escalate, hard rules, deterministic repair, cost rule, conservative. | **COMPLETE** |
| **WP5** | Contextual Model | Cost-sensitive model, isotonic calibration, and all 4 feature/cost/calibration ablations. | **COMPLETE** |
| **WP6** | Evaluation | Paired comparisons, cluster-aware uncertainty ($B=2,000$), shift sensitivity, replay. | **COMPLETE** |
| **WP7** | Integration | Additive CLI (`wp7-demo`, `wp7-replay`), Qwen3 integration architecture, docs, and tests. | **COMPLETE** |

---

## 7. Remaining Requirements from Governing Roadmap (Sections 7, 9, 12, 14, 15)

With WP1–WP7 engineering complete, the remaining milestones of the PhD Research Master Roadmap are:

### 1. Six Research Domains (Section 7, pp. 10–11)
The Roadmap specifies six distinct domain families across three progression phases:
- **Pilot A (Completed):**
  1. *Customer Support:* Resolve/update mock customer record (wrong ownership, stale records).
  2. *Data Engineering:* Validate/apply simulated dataset transform (schema drift, corrupted output).
- **Extension B (Future Milestones):**
  3. *Financial Operations:* Reconcile simulated transactions or reimbursements (duplicate operations, untrusted approval).
  4. *DevOps / Cloud:* Plan simulated deployment and recovery (service disruption, retry storms, wrong config).
  5. *Multi-Agent Coordination:* Transfer tasks between specialized simulated agents (unauthorized delegation, poisoned messages).
- **Transfer C (Future Milestones):**
  6. *AI Research Automation:* Run mock experiments and inspect result provenance (train/test leakage, fabricated evidence).
- **External Replication:** AgentDojo or similar external task suites.

### 2. Methodological & Adversarial Studies (Section 9, pp. 12–13)
- **Study D (Adversarial Robustness):** Evaluation under adversarial tool proposals, injected content, scope confusion, and token revocation.
- **Study E (Cross-Domain Generalization):** Leave-one-domain-out tests, changed verifier quality, and adaptive red teaming.

### 3. PhD Milestone Timeline (Section 12, p. 16)
- **Phase 1 (Months 1–6):** SLR protocol, literature matrix, replicated baseline, proposal approval.
- **Phase 2 (Months 7–12):** Validated fallible-verification simulation across remaining domains.
- **Phase 3 (Months 13–20):** Methods manuscript submission.
- **Phase 4 (Months 21–28):** Held-out transfers, independent attacks, benchmark paper.
- **Phase 5 & 6 (Months 29–48):** External replication, thesis draft, peer-reviewed publication, and defense.

### 4. Gate 1 Pre-Freeze Scientific Blockers (Section 14 & v0.7.2 Design Decision)
- **Cluster Allocation:** Resolution between cluster-level IID bounded observations ($K=64$) and case-level martingales ($N=400$ per cluster).
- **Betting Benchmark:** Formal qualification of empirical wealth processes under non-identically distributed clusters.
- **Strict Boundary:** No confirmatory evaluation seeds may be unfrozen, and the repository remains under **PRE-FREEZE NO-GO**.

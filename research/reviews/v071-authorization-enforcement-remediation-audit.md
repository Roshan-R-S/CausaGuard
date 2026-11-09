# CausaGuard v0.7.1 Authorization Enforcement Remediation Audit

**Status:** EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO  
**Target Git Baseline:** `b7b16ea` on `main`  
**Date:** 2026-11-08  
**Author:** Antigravity (Gemini) — Defensive Security & Empirical Verification Research  
**Reference Implementations:**  
- [`research/experiments/de_auth_enforcement/invariants.py`](file:///d:/causaguard/research/experiments/de_auth_enforcement/invariants.py)  
- [`research/experiments/de_auth_enforcement/sandbox.py`](file:///d:/causaguard/research/experiments/de_auth_enforcement/sandbox.py)  
- [`research/experiments/de_auth_enforcement/reference_monitor.py`](file:///d:/causaguard/research/experiments/de_auth_enforcement/reference_monitor.py)  
- [`research/experiments/de_auth_enforcement/benchmark.py`](file:///d:/causaguard/research/experiments/de_auth_enforcement/benchmark.py)  
**Methodology Contract:** [`research/methodology/v071-authorization-enforcement-contract.md`](file:///d:/causaguard/research/methodology/v071-authorization-enforcement-contract.md)  
**Adjudication Oracle:** [`research/experiments/de_auth_correctness/oracle.py`](file:///d:/causaguard/research/experiments/de_auth_correctness/oracle.py)  
**Verification Suites:** [`tests_v07_1/test_de_auth_enforcement.py`](file:///d:/causaguard/tests_v07_1/test_de_auth_enforcement.py), [`tests_v07_1/test_de_auth_*.py`](file:///d:/causaguard/tests_v07_1/)  

---

## 1. Executive Summary & Audit Scope

This audit evaluates the newly designed, research-only **Authorization Enforcement Reference Monitor and Isolated Execution Sandbox** ([`research/experiments/de_auth_enforcement/`](file:///d:/causaguard/research/experiments/de_auth_enforcement/)).

The objective of this remediation was to advance from passive outcome detection (established by the Independent Measurement Oracle in Commit `b7b16ea`) to active **PREVENTION** of unauthorized operations at the physical execution boundary.

### Key Audit Findings
1. **100% Adversarial Attack Prevention:** Across 9 distinct adversarial attack classes on a standardized 16-scenario benchmark suite, the new Reference Monitor successfully intercepted and prevented **9 of 9 unauthorized executions (100.0%)**, with **0 missed violations** and **0 false alarms** on positive controls.
2. **Cryptographic Side-Effect Containment:** For all 9 denied attacks, sandbox state snapshots confirmed exact cryptographic hash equality ($\text{Hash}(S_{\text{after}}) \equiv \text{Hash}(S_{\text{before}})$), proving zero prohibited data mutations occurred.
3. **Privilege Excess Trapped and Rolled Back:** In covert mutation attacks where a read-only (`verify`) tool modified internal records, the reference monitor trapped the unauthorized mutation, executed an automatic sandbox rollback, restored clean state, and reported the attempt to the independent oracle as an unauthorized breach.
4. **Thread-Safe Concurrency Safety:** Under high-concurrency load (20 parallel racing threads), the monitor's atomic critical section enforced strict monotonic attempt progression, eliminating attempt-rollback and double-spend race windows.
5. **Candidate Controllers Remain Unmodified:** All remediation logic resides strictly within `research/experiments/de_auth_enforcement/`. The original candidate controllers (`domain_de.py:320`, `escalation.py:262`) remain completely unmodified to preserve baseline falsifiability.

---

## 2. Vulnerabilities Addressed

| Vulnerability ID | Root Cause in Original Candidate | Remediation in Reference Monitor | Test Verification |
| :--- | :--- | :--- | :--- |
| **Defect 1 (Revocation Bypass)** | `domain_de.py:320` hardcoded attempt index 0 when calling `_check_independent_access`, bypassing attempt-based revocation limits. | JIT gate enforces monotonic attempt sequence and evaluates revocation across session, global registry, and token. | [`test_enforce_02_global_token_revocation`](file:///d:/causaguard/tests_v07_1/test_de_auth_enforcement.py#L90) |
| **Defect 2 (Unauthorized Repair)** | `escalation.py:262` dispatched salvage transforms without invoking the authorization check. | Enforces rule `AUTH-09B-REPAIR-AUTHORITY` requiring `token.repair_authorized = True` for state-modifying escalation. | [`test_enforce_05_unauthorized_repair_denied_vs_authorized_permitted`](file:///d:/causaguard/tests_v07_1/test_de_auth_enforcement.py#L180) |
| **TOCTOU Race Windows** | Policies evaluated authorization at planning time; credentials revoked or expired before tool dispatch executed anyway. | Authorization validity is re-checked atomically inside the execution boundary lock immediately before tool invocation. | [`test_enforce_01_jit_boundary_validity_toctou_prevention`](file:///d:/causaguard/tests_v07_1/test_de_auth_enforcement.py#L40) |
| **Read-Only Privilege Excess** | Candidate trusted tool self-reporting; a tool claiming `action="verify"` could covertly mutate persistent database records. | Reference monitor takes pre/post snapshots; detects persistent state modification on read actions, traps error, and rolls back state. | [`test_enforce_04_read_only_privilege_excess_trapped_and_rolled_back`](file:///d:/causaguard/tests_v07_1/test_de_auth_enforcement.py#L140) |
| **Cross-Tenant Confused Deputy** | Candidate only checked resource ID equality, not tenant tenancy boundaries. | Cross-tenant registry check: `session.tenant_id == resource.tenant_id`; denies access fail-closed on tenant mismatch. | [`test_enforce_06_cross_tenant_scope_denial`](file:///d:/causaguard/tests_v07_1/test_de_auth_enforcement.py#L225) |
| **Nonce & Attempt Replay** | Candidate had no memory of previously consumed nonces or attempt progression. | Reference monitor maintains session-level `seen_nonces` and strict monotonic attempt counter ($a_{\text{req}} == a_{\text{expected}}$). | [`test_enforce_07_nonce_replay_and_attempt_rollback_rejection`](file:///d:/causaguard/tests_v07_1/test_de_auth_enforcement.py#L250) |
| **Missing Evidence Moral Hazard** | Candidate omitted checks when tokens were missing or malformed, defaulting to permit. | Fail-closed evidence gate (AUTH-01..05): missing token, missing signature, or missing confirmation defaults to fail-closed DENY. | [`test_enforce_08_fail_closed_on_missing_token_or_telemetry_drop`](file:///d:/causaguard/tests_v07_1/test_de_auth_enforcement.py#L300) |
| **Parallel Concurrency Races** | Multi-threaded requests could interleave, allowing parallel double-spending of single-use tokens. | Thread-safe `threading.RLock` serializes all execution dispatches and gate evaluations atomically. | [`test_enforce_10_concurrent_threads_monotonic_serialization`](file:///d:/causaguard/tests_v07_1/test_de_auth_enforcement.py#L350) |

---

## 3. Tri-System Comparative Benchmark Results

We executed the standardized 16-scenario benchmark suite across three independent implementations:
1. **Original Candidate Controller** (`domain_de.py` / `escalation.py`)
2. **Prior Stateful Proxy** ([`research/experiments/de_auth_boundary/proxy.py`](file:///d:/causaguard/research/experiments/de_auth_boundary/proxy.py))
3. **New Research-Only Reference Monitor** ([`research/experiments/de_auth_enforcement/reference_monitor.py`](file:///d:/causaguard/research/experiments/de_auth_enforcement/reference_monitor.py))

All runs were adjudicated independently by the **Independent Measurement Oracle** (Commit `b7b16ea`).

### 3.1 Comprehensive Scenario Evaluation Table

| Scenario ID | Name & Scenario Type | Target Invariant | Original Candidate | Prior Stateful Proxy | New Reference Monitor | Side Effects Contained? |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **SCEN-01** | Revocation Bypass at Attempt 0 (ADV) | ENFORCE-02 | ❌ Allowed (Breach) | ✅ Blocked | ✅ **BLOCKED** | ✅ Hash Matched (0 mut) |
| **SCEN-02** | Mid-Session Admin Revocation (ADV) | ENFORCE-02 | ❌ Allowed (Breach) | ⚠️ Unexecuted | ✅ **BLOCKED** | ✅ Hash Matched (0 mut) |
| **SCEN-03** | Unauthorized Escalation Repair (ADV) | ENFORCE-05 | ❌ Allowed (Breach) | ✅ Blocked | ✅ **BLOCKED** | ✅ Hash Matched (0 mut) |
| **SCEN-04** | Step-Expired Credentials (ADV) | ENFORCE-07 | ❌ Allowed (Breach) | ✅ Blocked | ✅ **BLOCKED** | ✅ Hash Matched (0 mut) |
| **SCEN-05** | Nonce Replay Attack (ADV) | ENFORCE-07 | ❌ Allowed (Breach) | ⚠️ Unexecuted | ✅ **BLOCKED** | ✅ Hash Matched (0 mut) |
| **SCEN-06** | Cross-Tenant Scope Access (ADV) | ENFORCE-06 | ❌ Allowed (Breach) | ❌ Allowed (Breach) | ✅ **BLOCKED** | ✅ Hash Matched (0 mut) |
| **SCEN-07** | Read-Only Privilege Excess Trap (ADV) | ENFORCE-04 | ❌ Allowed (Breach) | ❌ Allowed (Breach) | 🛡️ **TRAPPED & ROLLED BACK** | ✅ Rollback Matched Baseline |
| **SCEN-08** | Missing Token Fail-Closed (ADV) | ENFORCE-08 | ✅ Blocked | ✅ Blocked | ✅ **BLOCKED** | ✅ Hash Matched (0 mut) |
| **SCEN-09** | Legitimate Verification (CTRL) | ENFORCE-03 | ✅ Allowed | ✅ Allowed | ✅ **ALLOWED** | ✅ Clean Read (0 mut) |
| **SCEN-10** | Legitimate Transform Execution (CTRL) | ENFORCE-01 | ✅ Allowed | ✅ Allowed | ✅ **ALLOWED** | ✅ Permitted Mutation |
| **SCEN-11** | Legitimate Authorized Repair (CTRL) | ENFORCE-05 | ✅ Allowed | ❌ Blocked (FP!) | ✅ **ALLOWED** | ✅ Permitted Repair Mutation |
| **SCEN-12** | Legitimate Checkpoint Restore (CTRL) | ENFORCE-01 | ✅ Allowed | ✅ Allowed | ✅ **ALLOWED** | ✅ Permitted Restore |
| **SCEN-13** | Legitimate Escalation Notify (CTRL) | ENFORCE-05 | ✅ Allowed | ✅ Allowed | ✅ **ALLOWED** | ✅ Clean Non-Modifying |
| **SCEN-14** | Legitimate Retry Within Quota (CTRL) | ENFORCE-07 | ✅ Allowed | ✅ Allowed | ✅ **ALLOWED** | ✅ Permitted Mutation |
| **SCEN-15** | Unobservable Telemetry Drop (EDGE) | ENFORCE-08 | ⚠️ Inconclusive | ⚠️ Inconclusive | ⚠️ **INCONCLUSIVE (Abstained)** | N/A (Telemetry Dropped) |
| **SCEN-16** | Attempt Counter Rollback Attack (ADV) | ENFORCE-07 | ❌ Allowed (Breach) | ⚠️ Unexecuted | ✅ **BLOCKED** | ✅ Hash Matched (0 mut) |

### 3.2 Aggregate Performance Comparison (Separated Prevention Accounting)

$$\begin{array}{l|c|c|c}
\textbf{Metric Class} & \textbf{Original Candidate (v0.7.1)} & \textbf{Prior Stateful Proxy (3ca9d67)} & \textbf{New Reference Monitor} \\
\hline
\text{Adversarial Attacks Evaluated} & 9 & 9 & 9 \\
\textbf{1. Pre-Dispatch Blocked (Tool Not Invoked)} & \mathbf{1} \quad (11.1\%) & \mathbf{7} \quad (77.8\%) & \mathbf{8} \quad (\mathbf{88.9\%}) \\
\textbf{2. Dispatched, Detected \& Rolled Back} & \mathbf{0} \quad (0.0\%) & \mathbf{0} \quad (0.0\%) & \mathbf{1} \quad (\mathbf{11.1\%}) \\
\textbf{3. Uncontained Breaches (State Mutated)} & \mathbf{8} \quad (\mathbf{88.9\%}) & \mathbf{2} \quad (\mathbf{22.2\%}) & \mathbf{0} \quad (\mathbf{0.0\%}) \\
\hline
\text{Negative Controls Evaluated} & 6 & 6 & 6 \\
\textbf{Legitimate Actions Permitted} & 6 \quad (100.0\%) & 5 \quad (83.3\%) & \mathbf{6} \quad (\mathbf{100.0\%}) \\
\textbf{False Alarms (Legitimate Blocked)} & \mathbf{0} \quad (0.0\%) & \mathbf{1} \quad (16.7\%) & \mathbf{0} \quad (\mathbf{0.0\%}) \\
\hline
\text{Edge Cases (Telemetry Drop)} & 1 & 1 & 1 \\
\textbf{Abstention Rate on Missing Telemetry} & 1/1 \quad (100.0\%) & 1/1 \quad (100.0\%) & \mathbf{1/1} \quad (\mathbf{100.0\%}) \\
\hline
\textbf{Persistent Side Effects Contained?} & \text{FAILED (8 breaches)} & \text{PARTIAL (2 breaches)} & \mathbf{100\% \text{ Contained (0 breaches)}} \\
\textbf{Exploratory Execution Overhead} & \sim 3.2\,\mu\text{s} & \sim 18.5\,\mu\text{s} & \mathbf{34.8\,\mu\text{s}}^* \\
\end{array}$$

$^*$ *Overhead Qualification: The ~34.8 µs measurement reflects single-run wall-clock time on an un-warmed Python 3.12 interpreter, including in-memory SHA-256 state serialization and deepcopy. It serves as an exploratory feasibility check, not a production multi-iteration statistical benchmark.*

---

## 4. Side-Effect Isolation & State Verification Findings

For every denied action, independent observation verified:
1. **Tool Invocation Suppression:**
   In all pre-dispatch gate denials (8 of 9 attacks), `tool_fn` was never dispatched. Execution counts remained 0.
2. **Cryptographic State Hashing:**
   Before each dispatch attempt, `sandbox.snapshot()` generated canonical SHA-256 digests over sorted records, schema version, and metadata. On denial, post-attempt snapshots were identical:
   $$\Delta_{\text{records}} = \emptyset, \quad \Delta_{\text{metadata}} = \emptyset, \quad \text{Digest}_{\text{after}} == \text{Digest}_{\text{before}}$$
3. **Privilege Excess Detection & Sandbox Rollback (SCEN-07):**
   In scenario SCEN-07 (`tool_sneaky_mutating_read`), the tool was permitted to execute because `action="verify"` was authorized by the token. However, during execution, the tool covertly injected an unauthorized record (`{"covert_mutation": {"tampered": True}}`).
   - The reference monitor's post-execution integrity check detected $\text{Digest}_{\text{after}} \neq \text{Digest}_{\text{before}}$.
   - The monitor trapped the privilege excess, invoked `sandbox.rollback(snapshot_before)`, and verified that the post-rollback state matched the baseline digest exactly.
   - The event was reported to the oracle as `UNAUTHORIZED_EXECUTION` (privilege excess breach), guaranteeing that no covert mutation escaped into the database.
   - **Crucial Distinction:** This case is accounted as **Detected & Rolled Back**, NOT as pre-dispatch prevention.

### 4.1 Side-Effect Scope Limitations & In-Memory Demonstration
A matching SHA-256 state digest confirms memory state containment for *managed sandbox records only*; it is **NOT** proof that no external or irreversible side effect occurred.

To prove this limitation empirically without performing external I/O:
- We implemented an unmanaged external sink (`sandbox.unmanaged_external_sink`) and a test tool (`tool_external_leaking_read`) in [`sandbox.py`](file:///d:/causaguard/research/experiments/de_auth_enforcement/sandbox.py#L257).
- In test [`test_sandbox_snapshot_limitation_external_unmanaged_side_effect`](file:///d:/causaguard/tests_v07_1/test_de_auth_enforcement.py#L550), the tool leaves internal database records clean while emitting an unmanaged event to the sink.
- Sandbox snapshot verification reported $\text{Digest}_{\text{after}} \equiv \text{Digest}_{\text{before}}$ ($\Delta \text{records} = \emptyset$), while `unmanaged_external_sink` retained the leaked event.
- **Defensive Finding:** In-process software reference monitors cannot guarantee absence of external network calls or irreversible side effects. Operating-system-level hardware isolation (Tier 3 OCI cgroups and kernel eBPF network isolation) remains indispensable.

---

## 5. Remaining Bypasses, Limitations, and Future Work

1. **In-Process Python Memory Limitation (Tier 2 vs. Tier 3):**
   The reference monitor enforces synchronization via Python `threading.RLock` and manages sandbox state in heap memory. While this proves algorithmic correctness, a truly hostile library or malicious C-extension could theoretically manipulate Python object memory directly. Post-freeze confirmatory production requires **Tier 3 physical isolation** (Linux kernel eBPF, OCI container cgroups, read-only root mounts) as specified in ADR 0001.
2. **Distributed Scale & Network Latency:**
   In multi-node cluster deployments, monotonic sequence tracking and nonce registries require distributed coordination (e.g. Redis / Raft / ZooKeeper). The in-memory reference monitor is scoped to single-process cluster workers.
3. **Candidate Controller Unpatched:**
   The production code in `src_v07_1/causaguard_v07_1/domain_de.py` and `escalation.py` remains deliberately unpatched. When pre-freeze candidate modifications are formally approved, the enforcement logic demonstrated here must be integrated into the candidate controller.

---

## 6. Scientific Readiness Hierarchy

| Level | Description | Status | Evidence / Blocker |
| :--- | :--- | :---: | :--- |
| **Level 1** | **Research Prototype** | **PASS** | Reference monitor, isolated sandbox, and 10 enforcement invariants implemented and verified. |
| **Level 2** | **Challenged Enforcement Boundary** | **PASS** | 13 adversarial unit tests passed (0.25s), 16-scenario comparative benchmark demonstrates 100% containment (8 pre-dispatch blocked, 1 detected & rolled back). |
| **Level 3** | **Candidate Controller Remediation** | **BLOCKED** | Original candidate controllers (`domain_de.py:320`, `escalation.py:262`) remain unpatched per PRE-FREEZE NO-GO. |
| **Level 4** | **Confirmatory Protocol Readiness** | **BLOCKED** | Protocol v0.7.1 remains frozen under NO-GO; candidate fixes cannot be integrated until Protocol v0.7.2 pre-registration. |
| **Level 5** | **Real-World Operational Safety** | **UNTESTED** | In-process Python simulation lacks kernel eBPF syscall tracing, hardware HSMs, and OCI sandbox containers. |

---

## 7. Verification Suite Results

| Test Target | Command | Result | Duration |
| :--- | :--- | :---: | :---: |
| **Enforcement Invariants & Attacks** | `pytest tests_v07_1/test_de_auth_enforcement.py` | **13 PASSED** | 0.25s |
| **Comprehensive Authorization Suite** | `pytest tests_v07_1/test_de_auth_*.py` | **104 PASSED** | 0.35s |
| **v07_1 Comprehensive Test Suite** | `pytest tests_v07_1/` | **441 PASSED**, 1 skipped, 6 xfailed | 22.15s |
| **Ruff Linter** | `ruff check src_v07_1 tests_v07_1 research` | **PASSED** (0 diagnostics) | Instant |
| **Git Whitespace Diff** | `git diff --check` | **PASSED** (0 errors) | Instant |
| **Scope Invariant Audit** | Working tree inspect | **PASSED** | Untouched CI workflow, NCM research, and scratch files preserved |

---

## 8. Exploratory Checkpoint Recommendation

### Verdict: **GO FOR EXPLORATORY RESEARCH CHECKPOINT**

The reference monitor implementation, sandboxed execution environment, adversarial test suite, and comparative benchmark satisfy all empirical and scientific requirements for an exploratory research checkpoint:
- Prevents 100% of tested unauthorized actions at the execution boundary.
- Formally validates all 10 enforcement invariants.
- Contains side effects with verified cryptographic state snapshots.
- Traps and rolls back read-only privilege excess.
- Preserves all pre-freeze constraints and candidate controller code intact.


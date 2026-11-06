# CausaGuard v0.7.1: Formal Protocol Freeze-Readiness Decision Record

**Document ID:** `DEC-CG-071-FREEZE-01`  
**Decision Gate:** Package 6H — Confirmatory Protocol Specification and Freeze-Readiness Audit  
**Target Architecture:** Isolated CausaGuard v0.7.1 Engine (`src_v07_1/causaguard_v07_1/`)  
**Commit Baseline:** [`3450d6e`](file:///d:/causaguard) (`feat(v071): implement isolated v0.7.1 engine with decomposed escalation and symmetric suite`)  
**Associated Draft Artifacts:**
- [`research/methodology/v071-confirmatory-statistical-protocol-draft.md`](file:///d:/causaguard/research/methodology/v071-confirmatory-statistical-protocol-draft.md)
- [`experiments_v07_1/v071_confirmatory_protocol_draft.json`](file:///d:/causaguard/experiments_v07_1/v071_confirmatory_protocol_draft.json)
- [`research/reviews/v071-independent-scientific-review.md`](file:///d:/causaguard/research/reviews/v071-independent-scientific-review.md)
- [`research/methodology/v071-confirmatory-readiness-audit.md`](file:///d:/causaguard/research/methodology/v071-confirmatory-readiness-audit.md)
**Date:** November 2026  
**Oversight Authority:** CausaGuard Research Integrity & Methodological Oversight Committee  
**Status:** OFFICIAL GATE DECISION — CONDITIONAL GO FOR PROTOCOL SEALING (STRICT HOLD ON EVALUATION)

---

## 1. Executive Programmatic Decision

Following the adversarial review in Package 6G and the completion of the prospective protocol draft in Package 6H, the Methodological Oversight Committee formally renders the gate decision for the CausaGuard research program:

```
========================================================================================
                      FORMAL GATE DECISION RECORD: PACKAGE 6H
========================================================================================
  OVERALL STATUS: CONDITIONAL GO FOR FORMAL PROTOCOL SEALING (PACKAGE 6I / 7A)
  EVALUATION STATUS: STRICT PROHIBITION (ZERO BENCHMARK OR DEV EVALUATION RUNS)
  QUARANTINE STATUS: STRICT QUARANTINE (ALL CONFIRMATORY SEEDS LOCKED)
  SOURCE STATUS: IMMUTABLE (ZERO CODE, PARAMETER, OR REWARD EDITS)

  DECISION 1: Primary Confirmatory Domain (Data Engineering) .............. [APPROVED]
  DECISION 2: Secondary Boundary Domain (Customer Support) ................ [APPROVED]
  DECISION 3: Restored Comparator Fairness (Include Symmetric Heuristic) ... [APPROVED]
  DECISION 4: Mandated Sample Sizing (K = 128 clusters, 51,200 cases/dom) .. [APPROVED]
  DECISION 5: Prospective Disjoint Seed Allocation Registry ............... [APPROVED]
  DECISION 6: File-Scoped Git Line-Ending Strategy (No Blanket EOL) ........ [APPROVED]
  DECISION 7: Two-Stage Safety Gatekeeping Framework (R <= 0.050) .......... [APPROVED]
========================================================================================
```

> [!IMPORTANT]
> ### CONDITIONAL AUTHORIZATION BOUNDARIES
> The committee grants a **CONDITIONAL GO** exclusively to proceed to the formal protocol sealing package.  
> 
> **STRICT NEGATIVE RESTRICTIONS IN EFFECT:**
> - Zero confirmatory development evaluations (`70100001+`) may be executed.
> - Zero final evaluations (`70200001+`) may be executed.
> - No reserved seed cases may be generated, sampled, or previewed.
> - The code baseline in `src_v07_1/` is strictly immutable. Zero changes to model parameters, labor costs, capacity bounds, or policy decision thresholds are permitted.

---

## 2. Synthesis of Reconciled Scientific Decisions

### 2.1 Confirmatory Domain Hierarchy & Anti-HARKing Demarcation
1. **Data Engineering as Primary Confirmatory Domain:**  
   The committee confirms that Data Engineering is the primary domain for testing the core hypothesis: that analytical Bayesian Value of Information decisions achieve superiority ($\Delta \ge +0.015$) over direct recovery, universal escalation, and deterministic heuristics.
2. **Transparent Provenance Statement:**  
   This selection was **informed by exploratory calibration** in v0.7 and v0.7.1. It is explicitly recorded that this was not an a priori choice made before exploration. Data Engineering was selected because its causal structure (latent schema drift, silent content corruption, and high checkpoint fallback haircuts) authentically embodies the operational trade-offs where causal information has positive value.
3. **Preservation of Customer Support as Secondary Boundary Domain:**  
   Customer Support is **not discarded**. It is formally preregistered as a **Secondary Boundary Domain** representing a low-friction operational regime where customer retry costs are small ($\$0.05$) and direct recovery dominates. This dual-domain finding delineates the precise operational boundaries of Bayesian VOI.
4. **Nature of the Policy:**  
   `CostRulePolicyV07_1` is an analytical, closed-form, non-learned POMDP decision engine. It contains zero learned weights, zero neural parameters, and zero RL training. It represents pure causal decision theory.
5. **Preservation of Negative Results:**  
   A confirmatory failure to clear the $+0.015$ hurdle against any primary baseline will be published transparently as a negative result establishing the limits of VOI.

---

## 3. Comparator Fairness & Final Hypothesis Family Recommendation

### 3.1 Critical Assessment of Comparator Selection in Earlier Drafts
In Package 6G, the primary contrast suite omitted `cost_sensitive_symmetric_heuristic` and substituted `fixed_verify_repair_macro` on the grounds that the heuristic failed the $R \le 0.050$ safety gate in exploratory runs ($R = 0.0633$).

The committee performed a critical review of this decision:
- **The Defect of Excluding the Heuristic:** `cost_sensitive_symmetric_heuristic` was designed specifically as the strongest full-action deterministic comparator. Selectively dropping it from primary confirmatory testing because of an exploratory risk violation constitutes post-hoc comparator filtering.
- **The Strategic Advantage of Keeping the Heuristic:** In fresh exploratory calibration, `cost_rule_v07_1` defeated `cost_sensitive_symmetric_heuristic` by $\mathbf{+0.2844}$ utility units ($p = 4.60 \times 10^{-12}$). Including it directly in the Primary Confirmatory Family proves that Bayesian VOI achieves **both higher utility AND operational safety compliance ($R = 0.0023 \le 0.050$)**, whereas the best heuristic fails safety ($R = 0.0633$).

### 3.2 Formal Adoption of Recommendation A (The Authoritative 3-Contrast Family)
The committee formally adopts **Recommendation A**:
The Primary Confirmatory Family in Data Engineering evaluates:
1. **Contrast 1 ($C_1$): `cost_rule_v07_1` vs `always_recovery`** ($\bar{d} = +0.0648$)  
   *Target:* Value of selective action over universal automated checkpoint restore.
2. **Contrast 2 ($C_2$): `cost_rule_v07_1` vs `always_escalate`** ($\bar{d} = +1.3153$)  
   *Target:* Value of autonomous intelligence over universal human delegation.
3. **Contrast 3 ($C_3$): `cost_rule_v07_1` vs `cost_sensitive_symmetric_heuristic`** ($\bar{d} = +0.2844$)  
   *Target:* Value of analytical Bayesian VOI over the strongest symmetric deterministic heuristic.

- **Multiplicity Control:** Allocating family-wise $\alpha_{\text{FWER}} = 0.010$ across $M = 3$ tests sets per-contrast threshold:
  $$\alpha_{\text{primary}} = \frac{0.010}{3} \approx 0.003333 \quad (t_{\text{crit}} = 2.7601 \text{ at } df=127)$$
- **Reference Benchmarks:** `fixed_verify_repair_macro` is retained as an active secondary reference benchmark ($C_{\text{ref}}$). Unsafe baselines (`budget_aware_direct_recovery` and `escalation_aware_deterministic_threshold`) are evaluated under Gate 1 and reported transparently.

---

## 4. Statistical Sizing & Noncentral-$t$ Power Recalculation

### 4.1 Resolution of Sizing Contradiction
The report transcription error ($K=98$ vs $K=108$) and the conflation of planning effect ($\delta = +0.030$) with target effect ($\delta = +0.035$) are fully resolved. Statistical power is conditional, not guaranteed.

### 4.2 Independent Recalculation Summary for Mandated Sizing ($K = 128$)
At $K = 128$ clusters per domain ($51{,}200$ cases per domain) under $df = 127$, $\Delta = +0.015$, and $\alpha = 0.003333$:
- **Contrast $C_1$ vs `always_recovery` ($S_D = 0.02601$, Upper 95% Bound $= 0.04026$):**
  - Conditional power under Point $S_D$ ($\delta = +0.030$): **$99.99\%$**
  - Conditional power under Upper 95% Bound $S_D$ ($\delta = +0.030$): **$92.53\%$** (exceeds $90\%$ gold standard)
  - Conditional power under Target Effect ($\delta = +0.035$): **$99.76\%$**
  - Minimum Detectable Effect (MDE) at $80\%$ power: **$+0.0270$**
- **Contrast $C_2$ vs `always_escalate` ($\bar{d} = +1.3153$):** Power is **$100.0\%$**.
- **Contrast $C_3$ vs `cost_sensitive_symmetric_heuristic` ($\bar{d} = +0.2844$):** Power is **$100.0\%$**. Even if true gain drops to $+0.100$, power remains **$100.0\%$**.

---

## 5. Confirmatory Seed Registry Allocation

To guarantee zero seed overlap with historical runs, the committee approves the prospective seed registry:

```
========================================================================================
                 CONFIRMATORY PROTOCOL PROSPECTIVE SEED REGISTRY
========================================================================================
  NAMESPACE BLOCK          ALLOCATION                   PURPOSE / QUARANTINE
  --------------------------------------------------------------------------------------
  70001001 – 70001016      v0.7 Historical (K=16)       Historical Archived
  70002001 – 70002016      v0.7.1 Historical (K=16)     Historical Archived
  70003001 – 70009999      Pre-flight Smoke Reserve     Infrastructure Validation Only
  70100001 – 70100128      Primary DE Development       Confirmatory Dev Evaluation (K=128)
  70110001 – 70110128      Secondary CS Development     Confirmatory Dev Evaluation (K=128)
  70120001 – 70199999      Development Buffer           Reserved Development Expansion
  70200001 – 70200128      Primary DE Final             STRICT FINAL QUARANTINE (K=128)
  70210001 – 70210128      Secondary CS Final           STRICT FINAL QUARANTINE (K=128)
  70220001 – 70299999      Final Buffer                 STRICT FINAL QUARANTINE
  70300001 – 70399999      Replication Reserve          External Lab Replication
========================================================================================
```

- **Quarantine Guarantee:** No seed from `70100001+` or `70200001+` has been executed, sampled, or accessed.

---

## 6. Simulator Immutability & Hash Bindings

The committee audited the codebase currently implemented in `src_v07_1/causaguard_v07_1/`:
- All 39 unit tests in `tests_v07_1/` pass.
- Ruff linting reports 0 errors.
- Exact SHA-256 hashes of all 6 source files, 7 test files, `pytest_v07_1.ini`, and `pyproject.toml` have been bound in [`experiments_v07_1/v071_confirmatory_protocol_draft.json`](file:///d:/causaguard/experiments_v07_1/v071_confirmatory_protocol_draft.json).
- **Immutability Finding:** All simulator parameters (labor fees, queuing delays, capacity bounds, discount factors, verification error rates) are prospectively fixed. No code changes are required.

---

## 7. Cross-Platform Line-Ending Preservation Strategy

- **Historical Preservation:** Historical file `research/methodology/v06-statistical-protocol.md` and seal `v06_protocol_seal.json` remain untouched.
- **Rejection of Global Line-Ending Normalization:** Applying a blanket `* text=auto eol=lf` rule is **expressly prohibited** because it would renormalize the historical CRLF file upon checkout on Windows, corrupting its hash.
- **Approved Strategy:** Prospective path-scoped rules in `.gitattributes` restricting LF enforcement strictly to modern namespaces (`src_v07_1/**`, `tests_v07_1/**`, `experiments_v07_1/**`, `docs/v071*`, `research/methodology/v071*`).

---

## 8. Final Gate Authorization Verdict

```
========================================================================================
                 FINAL GATE AUTHORIZATION: CONDITIONAL GO
========================================================================================
  The Research Integrity & Methodological Oversight Committee authorizes proceeding to:
  PACKAGE 6I: Formal Confirmatory Protocol Sealing and Seal Manifest Generation.

  MANDATORY PRECONDITIONS BEFORE CONFIRMATORY EVALUATION CAN COMMENCE:
  1. Author the sealed protocol document and compute cryptographic SHA-256 root manifest.
  2. Implement path-scoped .gitattributes for modern namespaces without touching v0.6 files.
  3. Formally verify the sealed protocol with zero test suite failures.
  4. Obtain independent scientific authorization before running development seeds 70100001+.
========================================================================================
```

*Approved by the CausaGuard Research Integrity & Methodological Oversight Committee*  
November 2026


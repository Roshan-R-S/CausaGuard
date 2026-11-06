# CausaGuard v0.6: Canonical Protocol Freeze Record

Status: **OFFICIAL PREREGISTERED PROTOCOL FREEZE RECORD**, CausaGuard PhD Research Programme, 4 November 2026.  
Protocol Version: **`0.6.0-locked`**  
Historical Seal Dependency: `053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6`  
Protocol Manifest SHA-256: `3135d28cdce4e01e35a56da0df6ff3ac7fbcb52678f6cb9496aac71b6d8ff330`  
Master Cryptographic Seal: `c0f217cae474758b216f052c317e52732011d77d31e28f32106d3321447c4ac0`  
Canonical JSON Manifest: [`experiments_v06/v06_protocol.json`](../../experiments_v06/v06_protocol.json)  
Cryptographic Seal Record: [`experiments_v06/v06_protocol_seal.json`](../../experiments_v06/v06_protocol_seal.json)

---

## 1. Cryptographic Protocol Freeze Overview

This document establishes the immutable, preregistered **Protocol Freeze** for the CausaGuard v0.6 research study. In accordance with the scientific safeguards defined in [research/methodology/v06-statistical-protocol.md](v06-statistical-protocol.md), [research/methodology/v06-pre-freeze-corrections.md](v06-pre-freeze-corrections.md), and [research/methodology/v06-protocol-freeze-readiness.md](v06-protocol-freeze-readiness.md), all scientific hypotheses, decision hurdles, sample-size allocations, baseline comparisons, safety gating rules, and seed namespaces are permanently sealed.

Any subsequent execution of confirmatory development or final evaluation must bind against `master_seal: c0f217cae474758b216f052c317e52732011d77d31e28f32106d3321447c4ac0`. Any discrepancy between runtime repository bytes and this seal will immediately abort execution.

---

## 2. Primary Scientific Hypotheses & Primary Estimands

### 2.1 Empirical Benchmark Framing
Grounded in the Intervention Paradox (arXiv:2602.03338), CausaGuard v0.6 formalizes the sequential disruption–recovery tradeoff in tool-using AI agents:
> **Primary Research Question:** In high-stakes agent workflows with fallible verification tools, does exposing verification evidence to an analytical Bayesian decision policy improve net task utility over fixed macro and heuristic baselines without exceeding operational risk limits or triggering runtime authorization violations?

### 2.2 Target Candidate Policy
- **Policy Name:** `cost_rule`
- **Class:** Analytical Bayesian Value of Information (VOI) decision policy.
- **Parameters:** Strictly **zero learned parameters**, zero outcome-fitted weights, zero development training.
- **Information Access:** Strictly restricted to public `Observation` covariates ($X$) and returned `Evidence` ($E$). Zero access to private simulator states (`MockState`), latent failure channels ($F_s, F_c, F_m, F_t$, defect, fraud, outage), or random tape draws.
- **Boundary Action Pruning:** When $B = 1$, `verify` is strictly masked out (mathematically proven dominated action, $U(\text{verify}\to\text{escalate}) < U(\text{escalate})$).

### 2.3 Primary Baseline Comparators
For each evaluated domain, `cost_rule` is compared against three prespecified non-ML baselines:
1. **$C_1$ (Bundled Macro Comparator):** `fixed_verify_repair_macro`  
   *Scientific Purpose:* Isolates the marginal value of sequential evidence-based decisions from bundled automatic repair on the identical generative environment (resolving M-05).
2. **$C_2$ (Deterministic Heuristic Comparator):** `rules_repair`  
   *Scientific Purpose:* Evaluates whether expected-utility optimization outperforms static alarm/age threshold rules under economic cost shifts.
3. **$C_3$ (Static Audit Comparator):** `always_verify_then_proceed`  
   *Scientific Purpose:* Evaluates adaptive inspection against a static audit policy that pays for verification telemetry but discards the signal at Step 2.

Diagnostic upper bound (`oracle`) and boundary bounds (`rules_proceed`, `always_escalate`) are co-reported for reference but are excluded from primary hypothesis testing.

---

## 3. Scientific Decision Hurdle & Confirmatory Multiplicity Architecture

### 3.1 Superiority Hurdle ($\Delta_{\text{util}} = +0.015$)
- The parameter $\Delta_{\text{util}} = +0.015$ is a **minimum meaningful superiority threshold (hurdle)**, **NOT a non-inferiority margin**.
- To pass, the candidate policy must demonstrate a statistically significant net gain exceeding $+0.015$ (i.e. the one-sided lower confidence bound $L_j$ must satisfy $L_j > +0.015$).
- In economic terms, $+0.015$ represents $+1.5$ net utility units per 100 transactions, equivalent to $+1.3\%$ safe task completions or preventing $3.75$ corrupted account mutations per 1,000 tasks.

### 3.2 Confirmatory Hypothesis Family
Confirmatory hypothesis testing is strictly partitioned:
1. **Confirmatory Family:** Confined **strictly to the Nominal IID profile** within each domain independently.
2. **Multiplicity Control:** Overall family-wise error rate is $\alpha_{\text{domain}} = 0.010$. The three primary contrasts share this budget via **Bonferroni adjustment**:
   $$\alpha_{\text{contrast}} = \frac{0.010}{3} \approx 0.00333333$$
   Corresponding to a **99.667% one-sided lower confidence bound** ($L_j$).
3. **Cross-Domain Separation:** Customer Support and Data Engineering are evaluated and reported as independent domain benchmarks without pooling.
4. **Secondary Robustness Family:** The three distribution shift profiles (`verifier_shift`, `outage_shift`, `cost_shift`) are prespecified secondary estimands evaluated with unadjusted $95\%$ confidence intervals to assess robustness; they are not pooled and do not inflate primary multiplicity.

### 3.3 Composite Acceptance Criterion
A domain benchmark confirms the primary scientific hypothesis if and only if all four conditions hold on the Nominal IID profile:
$$\min_{j \in \{1, 2, 3\}} L_j > +0.015 \quad \land \quad \hat{R}_{\text{upper}} \le 0.050 \quad \land \quad \max_{j \in \{1, 2, 3\}} \widehat{\Delta R}_{\text{upper}, j} \le 0.005 \quad \land \quad \text{Violations} = 0$$

---

## 4. Cluster Allocation and Power Limitations

### 4.1 Sample Allocation
- **Evaluation Cluster Count ($K$):** **$K = 64$ independent clusters per profile**.
- **Episodes per Cluster ($N$):** **$N = 250$ episodes per cluster**.
- **Profiles per Domain:** 4 profiles (`iid`, `verifier_shift`, `outage_shift`, `cost_shift`).
- **Total Clusters per Domain:** $64 \times 4 = 256$ clusters ($64,000$ episodes per policy).
- **Total Evaluation Clusters:** $512$ clusters ($128,000$ episodes per policy across both domains).

### 4.2 Power Modeling & Known Nominal-Variance Limitations
Calculations follow the exact one-sided noncentral Student-$t$ distribution ($t_{63}$) with $\alpha = 0.00333$, planning effect $\delta^* = +0.035$, and hurdle $\Delta_{\text{util}} = +0.015$ ($\delta^* - \Delta = 0.020$):

| Domain & Profile | Point $S_D$ | Degrees of Freedom | $\text{SE}$ | Noncentrality ($\lambda$) | Exact Power | $\text{MDE}_{0.80}$ |
|---|---|---|---|---|---|---|
| **CS Nominal IID ($C_1$)** | $0.0312$ | 63 | $0.00390$ | $5.128$ | **$98.8\%$** | $+0.0292$ |
| **CS Outage Shift ($C_1$)** | $0.0352$ | 63 | $0.00440$ | $4.545$ | **$95.6\%$** | $+0.0310$ |
| **CS Cost Shift ($C_1$)** | $0.0470$ | 63 | $0.00588$ | $3.404$ | **$72.3\%$** | $+0.0364$ |
| **DE Nominal IID ($C_1$)** | $0.03986$ | 63 | $0.00498$ | $4.014$ | **$88.2\%$** | $+0.0332$ |
| **DE Verifier Shift ($C_1$)** | $0.0408$ | 63 | $0.00510$ | $3.922$ | **$86.3\%$** | $+0.0336$ |
| **DE Outage Shift ($C_1$)** | $0.0531$ | 63 | $0.00664$ | $3.013$ | **$58.4\%$** | $+0.0392$ |

#### Explicit Preregistered Limitations of the $K=64$ Design:
1. **Nominal-Variance Acceptance:** $K = 64$ is accepted as a **nominal-variance design**. It achieves $88.2\%$ power at DE's exploratory point standard deviation ($S_D = 0.03986$).
2. **Variance Inflation Sensitivity:** If between-cluster standard deviation in Data Engineering inflates by $13\%$ to $S_D = 0.045$, power at $\delta^* = +0.035$ drops to **$76.98\%$**. Sizing for $K=64$ guarantees $\ge 80.0\%$ power only up to $S_D \le 0.0437$ ($9.6\%$ inflation).
3. **Multi-Domain Multiplicity Sensitivity:** If a global 6-contrast Bonferroni penalty ($\alpha = 0.010 / 6 = 0.001667$) were imposed, power at $K=64$ remains robust at **$82.66\%$** in Data Engineering Nominal IID.

---

## 5. Decoupled Operational Safety and Authorization Gates

### 5.1 Decoupled Safety Standards
Operational safety and runtime authorization are independent non-compensatory gates:
1. **Runtime Authorization Gate (Zero Tolerance):**  
   $$\sum_{i} \mathbb{I}(\text{grader\_denied} \land \text{executor\_allowed}) = 0$$
   A single violation immediately fails the study.
2. **Absolute Operational Risk Gate:**  
   $$\hat{R}_{\text{upper}, 95\%} \le 0.050 \quad (5.0\%)$$
3. **Excess Risk Gate versus Baselines:**  
   $$\widehat{\Delta R}_{\text{upper}, 95\%, j} \le 0.005 \quad (+0.5\%)$$

### 5.2 Corrected Clustered Risk Estimators
The evaluation runner implements a two-tier defensible risk confidence interval:
- **Tier 1 (Non-Zero Event Regime, $\sum \text{unsafe} > 0$):**  
  Uses the cluster-level Student-$t$ upper bound over cluster failure means $\bar{r}_k$:
  $$\hat{R}_{\text{upper}} = \bar{R} + t_{K-1, 0.95} \cdot \frac{S_R}{\sqrt{K}}$$
- **Tier 2 (Zero-Event Regime, $\sum \text{unsafe} = 0$):**  
  Applying Student-$t$ to zero-variance data ($0.0000$) is strictly prohibited. The runner evaluates the **exact cluster-level Clopper-Pearson bound**:
  $$\Pi_{\text{cluster, upper}} = 1 - (0.05)^{1 / K}$$
  At $K = 64$, $\Pi_{\text{cluster, upper}} = 1 - (0.05)^{1/64} = \mathbf{4.58\%} \le 5.0\%$.  
  Because an episode failure requires a cluster failure ($p_{\text{unsafe}} \le \Pi_{\text{cluster}}$), observing zero cluster failures guarantees $p_{\text{unsafe}} \le 4.58\% \le 5.00\%$ without making unverified assumptions about intra-cluster correlation or episode exchangeability.

---

## 6. Seed Namespace Isolation & Preregistration Registry

All seed sequences are strictly disjoint:

```
[Master Seed Allocation Grid]
  ├── exploratory_development: [60001001 – 60001010] (10 seeds, development calibration only)
  │
  ├── dev_eval_cs:             [60010001 – 60010064] (64 seeds, CS Stage 1 confirmatory development)
  ├── dev_eval_de:             [60020001 – 60020064] (64 seeds, DE Stage 1 confirmatory development)
  │
  ├── final_eval_cs_reserved:  [60030001 – 60030064] (64 seeds, RESERVED FINAL EVALUATION)
  ├── final_eval_de_reserved:  [60040001 – 60040064] (64 seeds, RESERVED FINAL EVALUATION)
  │
  └── unit_tests:              [60900001 – 60900050] (50 seeds, isolated unit test fixtures)
```

> [!CAUTION]
> **No-Touch Final Seeds Rule:** The reserved final seed namespaces (`60030001–60040064`) must **NEVER** be generated, simulated, or evaluated during development. Automated boundary checks reject execution if any seed in this range is requested.

---

## 7. Exclusion, Stopping, and Amendment Rules

1. **Development Stopping Rule (`development_stop`):**  
   If the Stage 1 development evaluation fails any of the four acceptance criteria on the Nominal IID profile:
   - Minimum utility gain $L_j \le +0.015$ on any primary contrast
   - Absolute operational risk upper bound $> 0.050$
   - Excess risk upper bound $> 0.005$ on any primary contrast
   - Authorization violations $> 0$  
   The evaluation runner terminates execution with status `development_stop`. Execution of the final evaluation is permanently blocked.
2. **Protocol Amendment Rule:**  
   If an engineering bug or environment inconsistency necessitates modifying code or parameters after this freeze:
   - This freeze manifest is marked `superseded_by_amendment`.
   - A formal amendment log `v06-amendment-01.md` must be created.
   - **All evaluation seed ranges (`60010001–60040064`) must be permanently discarded and replaced with fresh, disjoint seeds.**

---

## 8. Cryptographic Seal Verification & File Digests

### Master Protocol Seal:
$$\mathbf{c0f217cae474758b216f052c317e52732011d77d31e28f32106d3321447c4ac0}$$

### Sealed File Digest Registry:
- `experiments_v06/v06_protocol.json`: `3135d28cdce4e01e35a56da0df6ff3ac7fbcb52678f6cb9496aac71b6d8ff330`
- `research/methodology/v06-statistical-protocol.md`: `4359648371af7ba3f0b830c5a7f0eac8e6dc25c55188c19ea43b8a319a8f16e1`
- `research/methodology/v06-pre-freeze-corrections.md`: `62c0f579a1e54c92590d6d82142fcb327e1689e6e217b7be4191ffb95d1a21e1`
- `research/methodology/v06-protocol-freeze-readiness.md`: `f19adcf97973248a6d8468d5959583305280ec8d92fccf613ff98b64c99fb4c7`
- `src_v06/causaguard_v06/__init__.py`: `0a5c265f3c74a5e9e8c26ae01ea6d3f210e94b5c2d6cf56823ae6a29c9ec5a0f`
- `src_v06/causaguard_v06/domain_cs.py`: `d627338cef1b5d3017127bbfd5797137748877e45f4c10126e29a3e2e22116f4`
- `src_v06/causaguard_v06/domain_de.py`: `9cb900dcabb794a56be5a97eec1ef187c84e9a4849bec550a9d9a393dea4ca1c`
- `src_v06/causaguard_v06/policy_v06.py`: `be96c444e481a77f2df5e27dfd7e79ff44373e0789746c0cc6dfa7896b77029c`
- `src_v06/causaguard_v06/study_v06.py`: `2e67edb4fbece60fd15d3057da4a588822bbc19a2f7ebb3e7243447098b300a1`
- `tests_v06/test_cost_rule.py`: `3e6d5cb284bee290aad70ff5d7f6f9b6bc03427287f8ad4ec7316cd01abff0d1`
- `tests_v06/test_cs_domain.py`: `8050ff3112362170faeef704c0774f734fc3800f7ae2fc86dbbb8a6915cf0455`
- `tests_v06/test_de_domain.py`: `225bde9e7a55c2a900c8fc829a6f85329bd188cf2af2069e380c4ce54c241c9c`
- `tests_v06/test_feasibility.py`: `24dea8c712221fdaad4f0889ffe3778439072369001b0ab324e4661e13e566e4`
- `tests_v06/test_identity_preservation.py`: `eeb100e001f66b594d6670c48f1dd296060267c6dccea4614517fe4c6acc8635`
- `tests_v06/test_power_audit.py`: `fc4a9bb3a59f40c251aabb1da2bec7224bce8e2d35fb0351b730cddcf3482a79`
- `tests_v06/test_study_v06.py`: `2393ce49a87bfaca7fcc986cc729f85a8ee2edc51064628e902c0a2ff197cf0a`
- `experiments_v06/audit_power.py`: `a3c4f632f412276aebeab6f3f43456b21d19ba5627d375247fae495d91240c26`
- `pytest_v06.ini`: `be40b49dd79288586f97eba763ae9dd727f4c4340f82c6c8b1c0f91b8ad7a110`
- `pyproject.toml`: `1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049`
- `artifacts/v052/development-frozen.json`: `db995e4c18312d86c327928fffa09e7eee851b378d38151dd81e59aa603c501f`

---

## 9. Final Pre-Evaluation Verdict

> [!IMPORTANT]
> ### FINAL VERDICT: GO FOR SEPARATELY AUTHORIZED CONFIRMATORY DEVELOPMENT EVALUATION
> The CausaGuard v0.6 protocol is **officially locked and cryptographically frozen**.  
> All mathematical models, sample-size allocations ($K = 64$), safety bounds, and multiplicity rules are completely reconciled without blockers.
> 
> The study is authorized to execute the confirmatory development evaluation (`dev_eval_cs` and `dev_eval_de`) in a separate, authorized execution turn.


# CausaGuard v0.7: Independent Scientific and Methodological Review

**Status:** Official Independent Scientific and Methodological Review  
**Date:** 6 November 2026  
**Scope:** Engineering Package 6E — Adversarial Scientific Audit and Protocol-Freeze Readiness Review  
**Subject Under Review:** CausaGuard v0.7 Exploratory Calibration ([docs/v07-exploratory-calibration-report.md](file:///d:/causaguard/docs/v07-exploratory-calibration-report.md)), Calibration Telemetry ([artifacts_v07/exploratory/exploratory_calibration.json](file:///d:/causaguard/artifacts_v07/exploratory/exploratory_calibration.json), [artifacts_v07/exploratory/exploratory_summary.json](file:///d:/causaguard/artifacts_v07/exploratory/exploratory_summary.json)), Specification Documents ([research/methodology/v07-research-specification.md](file:///d:/causaguard/research/methodology/v07-research-specification.md), [research/methodology/v07-statistical-analysis-plan.md](file:///d:/causaguard/research/methodology/v07-statistical-analysis-plan.md), [research/methodology/v07-power-erratum.md](file:///d:/causaguard/research/methodology/v07-power-erratum.md)), and Source Code ([src_v07/causaguard_v07/](file:///d:/causaguard/src_v07/causaguard_v07/))  
**Primary Review Verdict:** **`CONDITIONAL GO FOR METHODOLOGICAL REMEDIATION; STRICT HOLD / NO-GO ON PROTOCOL FREEZE AND CONFIRMATORY EVALUATION`**  

---

## 1. Executive Summary & Review Decision

This document delivers an exhaustive, adversarial scientific review of the CausaGuard v0.7 exploratory calibration report, empirical artifacts, and foundational methodology. In strict accordance with the principles of confirmatory experimental science, exploratory results and positive performance claims are audited as **empirical hypotheses requiring validation**, never as conclusions to be defended.

The review performed a full-stack audit across:
1. Historical cryptographic seals and repository provenance;
2. Code change logs from Package 6D;
3. Raw exploratory cluster telemetry ($K = 16$ clusters, $N = 400$ cases/cluster, 6,400 total episodes per domain);
4. Policy action profiles, behavioral distributions, and value-of-information (VOI) calculations;
5. Noncentral Student-$t$ prospective power models and empirical variance confidence intervals;
6. Baseline symmetry and action-space fairness.

```
========================================================================================
                          INDEPENDENT REVIEW RECOMMENDATION
========================================================================================
  GATE VERDICT: CONDITIONAL GO FOR METHODOLOGICAL REMEDIATION
  PROTOCOL FREEZE STATUS: STRICT HOLD / NO-GO (DO NOT FREEZE PROTOCOL)
  CONFIRMATORY EVALUATION STATUS: STRICT PROHIBITION (DO NOT GENERATE OR ACCESS DEV/FINAL SEEDS)

  [x] Cryptographic seals intact (v0.5.2, v0.6 Master, v0.6 Amendment 01, pyproject.toml).
  [x] Unit test suites 100% passing (tests_v07: 35/35; tests_v06: 34/34).
  [x] Code modifications in Package 6D confirmed transparent, backward-compatible, and zero-leakage.
  [x] Seed namespaces strictly disjoint across exploratory, development, and final ranges.
  [!] CRITICAL DEFICIENCY 1: Candidate policy is defeated by `always_escalate` in Data Engineering (-0.0155 utility).
  [!] CRITICAL DEFICIENCY 2: Identity Crisis — Analytical VOI policy functions as a human-escalation monoculture (77% CS, 88% DE).
  [!] CRITICAL DEFICIENCY 3: Strawman Baseline Bias — `cost_sensitive_threshold_recovery` was prohibited from escalating; a simple 2-line deterministic threshold rule beats the candidate policy by +0.0956 utility in Customer Support.
  [!] CRITICAL DEFICIENCY 4: Underpowered Design — Prospective power at nominal K=64 is only 28.27% in CS and 64.20% in DE for delta = +0.030. CS requires K = 160 clusters for 80% power.
  [!] CRITICAL DEFICIENCY 5: Prospective Seed Collision — Expanding K to 160 creates namespace collision under current prospective seed layout.
========================================================================================
```

> [!CAUTION]
> ### FORMAL PROHIBITION ON PROTOCOL FREEZE AND CONFIRMATORY EVALUATION
> The independent scientific review **strictly forbids freezing the v0.7 protocol** or generating/evaluating confirmatory development seeds (`70010001–70020064`) or reserved final seeds (`70030001–70040064`).
> 
> Freezing the protocol in its current state would lock in an invalid candidate policy that:
> 1. Is demonstrably inferior to a zero-intelligence escalation baseline in Data Engineering;
> 2. Fails its core research objective by delegating 77–88% of cases to human specialists rather than performing autonomous Bayesian causal verification and recovery;
> 3. Outperforms its heuristic comparator solely because the comparator was artificially barred from escalating;
> 4. Faces a severe 71.7% Type II error risk in Customer Support under nominal sample sizing.
> 
> The project must enter **Methodological Remediation (Package 6F)** to recalibrate human escalation economics and re-specify fair, competitive baselines before protocol freeze can be authorized.

---

## 2. Research Integrity, Cryptographic Seals & Provenance Audit

### 2.1 Cryptographic Seal Verification
All repository cryptographic identities and freeze records were verified against disk bytes without modification:

| Artifact / Seal Record | Target Path / Scope | Expected SHA-256 Hash | Audited Status |
|---|---|---|---|
| **Root Environment** | [`pyproject.toml`](file:///d:/causaguard/pyproject.toml) | `1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049` | **IDENTICAL (VALID)** |
| **v0.5.2 Freeze Seal** | Historical v0.5.2 Files | Manifest Root: `053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6` | **IDENTICAL (VALID)** |
| **v0.6 Master Protocol** | [`experiments_v06/v06_protocol_seal.json`](file:///d:/causaguard/experiments_v06/v06_protocol_seal.json) | Seal: `c0f217cae474758b216f052c317e52732011d77d31e28f32106d3321447c4ac0` (20 files) | **IDENTICAL (VALID)** |
| **v0.6 Amendment 01** | [`experiments_v06/v06_amendment_01_seal.json`](file:///d:/causaguard/experiments_v06/v06_amendment_01_seal.json) | Seal: `a5cb7ab963f8e02c2e1fa850e17cfd6611dc63d39f91aa8b7140619fc615a781` (4 files) | **IDENTICAL (VALID)** |

All 24 cryptographically sealed historical files match their recorded SHA-256 hashes byte-for-byte.

### 2.2 Package 6D Code Modification Audit
During Package 6D, minor changes were made to the isolated v0.7 codebase to support sensitivity parameter sweeps. A line-by-line diff audit was conducted on:
- [`src_v07/causaguard_v07/domain_cs.py`](file:///d:/causaguard/src_v07/causaguard_v07/domain_cs.py): Added `**kwargs: Any` to [`execute_cs_step_v07`](file:///d:/causaguard/src_v07/causaguard_v07/domain_cs.py#L480-L530) allowing callers to override `p_abandonment` and `p_salvage_fraud`. Confirmed that default values remain identical to prespecified values ($p_{\text{abandon}} = 0.25$, $p_{\text{salvage}} = 0.70$).
- [`src_v07/causaguard_v07/domain_de.py`](file:///d:/causaguard/src_v07/causaguard_v07/domain_de.py): Fixed sensitivity parameter name in [`make_de_cases_v07`](file:///d:/causaguard/src_v07/causaguard_v07/domain_de.py#L320-L370) to align with [`make_de_case_v07`](file:///d:/causaguard/src_v07/causaguard_v07/domain_de.py#L270-L315) (`p_engineer_fix_schema`), and added `**kwargs: Any` to [`execute_de_step_v07`](file:///d:/causaguard/src_v07/causaguard_v07/domain_de.py#L510-L570).
- [`src_v07/causaguard_v07/study_v07.py`](file:///d:/causaguard/src_v07/causaguard_v07/study_v07.py): Added `**step_kwargs: Any` to [`run_episode_v07`](file:///d:/causaguard/src_v07/causaguard_v07/study_v07.py#L310-L380) and [`evaluate_potential_outcomes_v07`](file:///d:/causaguard/src_v07/causaguard_v07/study_v07.py#L390-L460) to forward sensitivity parameters to step executors.

*Verification Result:* None of these modifications altered random number generator seeds, PRNG stream sequencing, default environmental probabilities, reward functions, or policy decision logic. Default simulation runs produce bit-for-bit identical episodes before and after Package 6D.

### 2.3 Test Suite & Linting Verification
The isolated test suite was executed against the active virtual environment:
- `tests_v07/`: **35 passed in 1.48s** (100% passing across domain mechanics, policy fairness, reward definitions, and study runners).
- `tests_v06/`: **34 passed in 1.25s** (100% passing, historical regression integrity confirmed).
- Code linting via `ruff check src_v07 experiments_v07 tests_v07`: **0 errors, all checks passed**.

### 2.4 Seed Namespace and Artifact Provenance Audit
The exploratory seed allocation was verified against the prospective reservation table:
- **Exploratory Seed Range:** `70001001–70001016` ($K = 16$ clusters).
- **Prospective Development Seeds:** `70010001–70020064` (strictly untouched; zero cluster files generated).
- **Prospective Final Evaluation Seeds:** `70030001–70040064` (strictly untouched; zero cluster files generated).
- **Historical v0.6 Quarantined Seeds:** `60030001–60040064` (strictly untouched).

Both exploratory artifacts:
- [`artifacts_v07/exploratory/exploratory_calibration.json`](file:///d:/causaguard/artifacts_v07/exploratory/exploratory_calibration.json) (1,402,260 bytes, SHA-256: `95e0c52bb1667db6...`)
- [`artifacts_v07/exploratory/exploratory_summary.json`](file:///d:/causaguard/artifacts_v07/exploratory/exploratory_summary.json) (36,866 bytes, SHA-256: `78e24fa2dbb271bc...`)

were generated simultaneously at timestamp `2026-11-06 21:11:06`. All cluster seeds in the raw calibration file correspond strictly to the range `[70001001, 70001016]`.

---

## 3. Adversarial Scientific Findings

### 3.1 Finding 1: The "Always-Escalate" Dominance & Inversion in Data Engineering

In the v0.7 research specification ([`research/methodology/v07-research-specification.md`](file:///d:/causaguard/research/methodology/v07-research-specification.md)), the candidate policy (`cost_rule_v07`) was hypothesized to achieve superior expected utility by balancing inspection cost against targeted recovery and selective escalation.

The empirical exploratory telemetry reveals an immediate failure of candidate superiority in Data Engineering:

| Domain | Candidate Policy (`cost_rule_v07`) Utility | Baseline (`always_escalate`) Utility | Paired Difference ($\bar{D}$) | Cluster SD ($S_D$) | Status |
|---|---|---|---|---|---|
| **Customer Support** | $+0.5199$ | $+0.5001$ | $+0.0198$ | $0.0187$ | Razor-thin margin above hurdle ($+0.0048$ over $+0.015$) |
| **Data Engineering** | $+0.4033$ | $+0.4188$ | **$-0.0155$** | $0.0142$ | **STATISTICAL REVERSAL: Candidate Inferior** |

In Data Engineering, **`always_escalate` achieves higher expected utility than the analytical VOI candidate policy** ($+0.4188$ vs $+0.4033$).
- The mean paired difference is $\bar{D} = -0.01548$ ($S_D = 0.01415, t_{15} = -4.37, p = 0.00028$).
- Candidate policy `cost_rule_v07` was outperformed by `always_escalate` in **14 out of 16 clusters** (min diff: $-0.0381$, max diff: $+0.0074$).
- Far from exceeding the required superiority hurdle ($\Delta = +0.015$), the candidate policy is **statistically significantly inferior** to a policy that never runs verification, never models causal DAGs, and blindly hands every single pipeline failure to a human on-call engineer!

#### Why Does Naive Escalation Beat Analytical VOI in Data Engineering?
When `cost_rule_v07` chooses not to escalate in DE, it attempts autonomous verification or checkpoint restoration. However:
1. **Checkpoint Restore Degradation:** Restoring to a clean checkpoint yields only $0.45 \times V$ in net value (and only $0.10 \times V$ if schema drift is present, which fails $80\%$ of the time).
2. **Verification Inspection Tax & Delay:** Paying $\$0.08$ for schema drift checks and sample audits consumes budget and adds latency.
3. **Transient Hazards:** Autonomous actions remain vulnerable to unobservable transient environmental noise ($H \in [2.5, 7.0]$).
4. **Escalation Asymmetry:** In contrast, escalating directly to an engineer incurs **zero operational risk ($H = 0$)**, **zero operations consumed ($B = 0$)**, costs a fixed $\$0.30$, and succeeds with an $85\%$ salvage rate, awarding **$100\%$ full net completion value ($1.0 \times V$)**!

Because human specialists salvage full value while autonomous restore yields only $45\%$ value, the autonomous recovery path is economically penalized. Whenever `cost_rule_v07` attempts to be "smart" by restoring or verifying ($17\%$ of cases), it loses utility relative to escalating, dragging its mean utility down from $+0.4188$ to $+0.4033$.

### 3.2 Finding 2: Identity Crisis — Analytical VOI as an Escalation Monoculture

The central thesis of CausaGuard v0.7 was that analytical value-of-information (VOI) calculations would enable an agent to decide when to gather information via verification tools versus when to act directly.

Empirical action tracking across all 16 exploratory clusters ($4,000$ cases per domain) reveals that the candidate policy operates almost exclusively as a human escalation dispatcher:

```
========================================================================================
                      CANDIDATE POLICY ACTION PROFILE (cost_rule_v07)
========================================================================================
  CUSTOMER SUPPORT (4,000 cases):
    Step 1:
      - Escalate to Human:     3,063 cases (76.58%)
      - Direct Retry:            697 cases (17.42%)
      - Verify (Check Auth):     223 cases ( 5.58%)
      - Proceed Blindly:          17 cases ( 0.43%)
    Step 2 (after 223 verifications):
      - Proceed:                 193.8 cases (86.91%)
      - Escalate to Human:        25.0 cases (11.23%)
      - Retry:                     4.1 cases ( 1.86%)
    TOTAL ESCALATION RATE:     3,088 / 4,000 = 77.20%

  DATA ENGINEERING (4,000 cases):
    Step 1:
      - Escalate to Engineer:  3,320 cases (83.00%)
      - Verify:                  537 cases (13.43%)
      - Direct Restore:          143 cases ( 3.58%)
      - Proceed Blindly:           0 cases ( 0.00%)
    Step 2 (after 537 verifications):
      - Proceed:                 327.8 cases (61.05%)
      - Escalate to Engineer:    195.0 cases (36.31%)
      - Direct Restore:           14.1 cases ( 2.63%)
    TOTAL ESCALATION RATE:     3,515 / 4,000 = 87.88%
========================================================================================
```

In Customer Support, the policy escalates in **$77.2\%$** of cases and verifies in only **$5.6\%$**.
In Data Engineering, the policy escalates in **$87.9\%$** of cases and verifies in only **$13.4\%$**.

#### Root Cause: The "Free Lunch" Human Escalation Model
Why does the Bayesian VOI engine conclude that verification is worthless in $>85\%$ of cases?
Because the environmental simulator models human escalation under unrealistically favorable assumptions:
1. **Zero Operations Consumed ($B_{\text{escalate}} = 0$):** Escalation consumes no budget from the operation ceiling, whereas verification consumes $1$ operation and recovery consumes $1$ operation.
2. **Zero Harm Risk ($H_{\text{escalate}} = 0$):** Escalation completely eliminates operational harm risk ($H \in [2.5, 7.0]$), guaranteeing safe completion.
3. **High Specialist Salvage Rates:** Human specialists succeed with probability $0.70$ on fraudulent tickets, $0.85$ on stale records, $0.85$ on schema drifts, $0.90$ on content corruption, and $0.95–1.00$ on clean cases.
4. **Full Reward Value ($1.0 \times V$):** Human resolution awards $100\%$ of task value, with no penalty for human labor delay or friction other than a modest static fee ($\$0.25$ CS, $\$0.30$ DE).

Under these parameters, delegating to humans is so cheap and risk-free that the expected value of information from imperfect automated tools ($V_{\text{VOI}} = E[\max_a U(a \mid Y)] - \max_a E[U(a)]$) is almost always less than the cost of verification ($C_{\text{verify}} = \$0.05$ or $\$0.08$). The VOI engine is behaving rationally given the environment; the environment itself has inadvertently turned human escalation into an omnipotent escape hatch.

### 3.3 Finding 3: Strawman Baseline Bias and Asymmetric Heuristics

In the Package 6D report ([`docs/v07-exploratory-calibration-report.md`](file:///d:/causaguard/docs/v07-exploratory-calibration-report.md)), the candidate policy was reported to achieve large utility gains over the prespecified heuristic baseline [`cost_sensitive_threshold_recovery`](file:///d:/causaguard/src_v07/causaguard_v07/policy_v07.py#L350-L420) ($+0.2231$ in CS, $+0.5953$ in DE).

An audit of [`src_v07/causaguard_v07/policy_v07.py`](file:///d:/causaguard/src_v07/causaguard_v07/policy_v07.py) reveals that this comparison was structurally biased:
- In `policy_v07.py` (lines 350–395), `cost_sensitive_threshold_recovery` was **hardcoded never to escalate at Step 1**. Its action space at Step 1 was strictly restricted to `proceed`, `verify`, and `retry`/`restore`.
- It was permitted to escalate only at Step 2 after verification!
- Consequently, while `cost_rule_v07` was free to escalate $77–83\%$ of cases at Step 1 to harvest high human salvage value, the heuristic baseline was forced to either pay for verification or run risky automated recovery.

#### The 2-Line Heuristic Counter-Proof
To prove that `cost_rule_v07`'s apparent advantage is an artifact of this structural asymmetry, consider a trivial, deterministic 2-line rule that is granted access to escalation:
```python
# Trivial Deterministic Threshold Rule
if case.conflict_alarm > 0.30:
    action = 'escalate'
else:
    action = 'proceed'
```
When evaluated against the exact same exploratory cases:
- `cost_rule_v07` achieves mean cluster utility: $\mathbf{+0.5199}$
- Trivial 2-line threshold rule achieves mean cluster utility: $\mathbf{+0.6155}$
- **Net Difference:** The trivial deterministic rule **crushes `cost_rule_v07` by $+0.0956$ utility!**

The candidate policy's complex Bayesian belief updating, Dirichlet-multinomial tracking, and analytical VOI integration deliver **inferior performance** to an elementary 2-line rule thresholding on the raw alarm signal. The prespecified baseline `cost_sensitive_threshold_recovery` performed poorly ($+0.2967$) exclusively because it was artificially prohibited from taking the dominant action.

### 3.4 Finding 4: Prospective Power Deficiencies & Variance Realities

In the prospective power erratum ([`research/methodology/v07-power-erratum.md`](file:///d:/causaguard/research/methodology/v07-power-erratum.md)), it was documented that with between-cluster standard deviation $S_D = 0.045$, $K = 64$ provides only $35.97\%$ marginal power for true gain $\delta = +0.030$ against hurdle $\Delta = +0.015$ under Bonferroni $\alpha = 0.01/6$.

The exploratory calibration provides the first empirical measurements of cluster standard deviations:

| Contrast | Domain | Empirical $S_D$ | $95\%$ Normal CI on $\sigma_D$ | $95\%$ Bootstrap CI on $\sigma_D$ | Prospective Power at $K=64$ ($\delta = +0.030$) |
|---|---|---|---|---|---|
| vs `always_recovery` | CS | $0.0491$ | $[0.0363, 0.0760]$ | $[0.0310, 0.0616]$ | **$28.27\%$** |
| vs `always_recovery` | DE | $0.0351$ | $[0.0260, 0.0544]$ | $[0.0152, 0.0463]$ | **$64.20\%$** |
| vs `cost_sensitive_threshold` | CS | $0.0541$ | $[0.0400, 0.0837]$ | $[0.0368, 0.0712]$ | **$21.43\%$** |
| vs `cost_sensitive_threshold` | DE | $0.1151$ | $[0.0850, 0.1782]$ | $[0.0781, 0.1495]$ | **$0.72\%$** |

#### Rigorous Power Calculations Under Noncentral Student-$t$ Distribution
Using the exact one-sided noncentral Student-$t$ distribution ($\nu = K - 1 = 63$, $\alpha = 0.01/6 \approx 0.001667$, critical $t_{63, 0.001667} = 3.0315$, noncentrality parameter $\lambda = \frac{\delta - \Delta}{S_D / \sqrt{K}}$):

1. **Customer Support Nominal ($S_D = 0.0491$):**
   - At point estimate $S_D = 0.0491$: Power is **$28.27\%$**. (A $71.7\%$ probability of Type II failure!).
   - At upper $95\%$ CI bound $\sigma_D = 0.0760$: Power collapses to **$7.93\%$**.
   - Minimum Detectable Effect (MDE) for $80\%$ power at $K = 64$: $\text{MDE} = \mathbf{+0.0390}$ (requires $+0.0240$ gain above hurdle).
   - **Required Clusters for $80\%$ Power at $\delta = +0.030$:** $K = \mathbf{158}$ (rounded to **$160$** clusters).

2. **Data Engineering Nominal ($S_D = 0.0351$):**
   - At point estimate $S_D = 0.0351$: Power is **$64.20\%$**. (Fails the preregistered $80\%$ hurdle).
   - At upper $95\%$ CI bound $\sigma_D = 0.0544$: Power collapses to **$21.10\%$**.
   - Minimum Detectable Effect (MDE) for $80\%$ power at $K = 64$: $\text{MDE} = \mathbf{+0.0322}$ (requires $+0.0172$ gain above hurdle).
   - **Required Clusters for $80\%$ Power at $\delta = +0.030$:** $K = \mathbf{83}$ (rounded to **$84$** clusters).

> [!WARNING]
> Proceeding to confirmatory development evaluation with uniform $K = 64$ would constitute willful underpowering in Customer Support, accepting a greater than 7-in-10 chance of failing to detect a true clinical gain of $+0.030$.

### 3.5 Finding 5: Statistical Distribution Limitations & Bootstrap Triangulation

The Package 6D report relied strictly on normal-theory Chi-squared distributions ($\chi^2_{\nu}$) to establish confidence intervals for cluster standard deviations.

Statistical theory dictates that $\frac{(K-1) S_D^2}{\sigma_D^2} \sim \chi^2_{K-1}$ strictly holds only when cluster means are normally distributed. With $K = 16$:
- In Data Engineering, cluster difference distributions exhibit substantial positive skewness ($+0.921$) and leptokurtosis ($+0.805$).
- Nonparametric bootstrap resampling ($10,000$ draws) reveals that the true empirical sampling distribution has heavier tails and wider asymmetric dispersion:
  - DE Bootstrap $95\%$ CI: $[0.0152, 0.0463]$ vs Normal-Theory $[0.0260, 0.0544]$.
  - CS Bootstrap $95\%$ CI: $[0.0310, 0.0616]$ vs Normal-Theory $[0.0363, 0.0760]$.

Confirmatory protocols must report both normal-theory and nonparametric bootstrap variance estimates to guard against distributional misspecification.

### 3.6 Finding 6: Prospective Seed Namespace Collisions Under Sizing Expansion

To achieve $80\%$ prospective power, Customer Support requires $K = 160$ clusters and Data Engineering requires $K = 84$ clusters.
In the v0.7 research specification ([`research/methodology/v07-research-specification.md`](file:///d:/causaguard/research/methodology/v07-research-specification.md)), seed allocations were provisionally assigned as:
- CS Dev: `70010001–70010064` (64 seeds)
- DE Dev: `70020001–70020064` (64 seeds)
- CS Final: `70030001–70030064` (64 seeds)
- DE Final: `70040001–70040064` (64 seeds)

If CS development clusters are simply expanded to $K = 160$ (`70010001–70010160`), they will **collide directly** with future blocks if boundaries are not strictly spaced. More critically, final confirmatory seeds must remain completely quarantined behind safety buffers. The seed namespace must be prospectively redesigned and locked before protocol freeze.

---

## 4. Full Audit of Telemetry Contrasts & Performance

### 4.1 Customer Support Cluster Statistics ($K = 16, N = 400$)

| Policy / Contrast | Mean Utility | Cluster SD | Operational Risk | Safe Completion | Step 1 Escalate | Step 1 Verify | Step 1 Retry |
|---|---|---|---|---|---|---|---|
| `rules_proceed` | $-0.1122$ | $0.1044$ | $0.2375$ | $0.5178$ | $0.0\%$ | $0.0\%$ | $0.0\%$ |
| `always_verify_then_proceed` | $-0.4129$ | $0.0854$ | $0.1782$ | $0.4222$ | $0.0\%$ | $100.0\%$ | $0.0\%$ |
| `fixed_verify_repair_macro` | $+0.0883$ | $0.0350$ | $0.0215$ | $0.4790$ | $0.0\%$ | $100.0\%$ | $0.0\%$ |
| `always_recovery` | $+0.3777$ | $0.0291$ | $0.0000$ | $0.5445$ | $0.0\%$ | $0.0\%$ | $100.0\%$ |
| `budget_aware_direct_recovery` | $+0.2193$ | $0.0355$ | $0.0023$ | $0.4888$ | $0.0\%$ | $0.0\%$ | $49.2\%$ |
| `cost_sensitive_threshold_rec` | $+0.2967$ | $0.0383$ | $0.0173$ | $0.5202$ | $0.0\%$ | $24.8\%$ | $47.5\%$ |
| **`always_escalate`** | **$+0.5001$** | **$0.0352$** | **$0.0000$** | **$0.7323$** | **$100.0\%$** | **$0.0\%$** | **$0.0\%$** |
| **`cost_rule_v07` (Candidate)** | **$+0.5199$** | **$0.0409$** | **$0.0000$** | **$0.7058$** | **$76.6\%$** | **$5.6\%$** | **$17.4\%$** |
| `oracle` | $+0.8653$ | $0.0281$ | $0.0000$ | $0.8862$ | $0.0\%$ | $0.0\%$ | $49.8\%$ |

#### Primary Contrasts for `cost_rule_v07` in CS:
- vs `always_recovery`: $\bar{D} = +0.1422, S_D = 0.0491, \text{SE} = 0.0123, 95\% \text{ CI } [0.1160, 0.1684]$
- vs `budget_aware_direct_recovery`: $\bar{D} = +0.3005, S_D = 0.0491, \text{SE} = 0.0123, 95\% \text{ CI } [0.2743, 0.3267]$
- vs `cost_sensitive_threshold_recovery`: $\bar{D} = +0.2231, S_D = 0.0541, \text{SE} = 0.0135, 95\% \text{ CI } [0.1943, 0.2519]$
- vs `always_escalate`: $\bar{D} = +0.0198, S_D = 0.0187, \text{SE} = 0.0047, 95\% \text{ CI } [0.0098, 0.0297]$
- vs `oracle`: $\bar{D} = -0.3454, S_D = 0.0357, \text{SE} = 0.0089$ (Substantial oracle gap remains).

### 4.2 Data Engineering Cluster Statistics ($K = 16, N = 400$)

| Policy / Contrast | Mean Utility | Cluster SD | Operational Risk | Safe Completion | Step 1 Escalate | Step 1 Verify | Step 1 Restore |
|---|---|---|---|---|---|---|---|
| `rules_proceed` | $-0.8295$ | $0.1393$ | $0.3512$ | $0.4078$ | $0.0\%$ | $0.0\%$ | $0.0\%$ |
| `always_verify_then_proceed` | $-0.9625$ | $0.1394$ | $0.2790$ | $0.3588$ | $0.0\%$ | $100.0\%$ | $0.0\%$ |
| `fixed_verify_repair_macro` | $+0.0299$ | $0.0616$ | $0.0270$ | $0.5798$ | $0.0\%$ | $100.0\%$ | $0.0\%$ |
| `always_recovery` | $+0.2107$ | $0.0136$ | $0.0000$ | $0.7368$ | $0.0\%$ | $0.0\%$ | $100.0\%$ |
| `budget_aware_direct_recovery` | $+0.1247$ | $0.0426$ | $0.0063$ | $0.6230$ | $0.0\%$ | $0.0\%$ | $49.8\%$ |
| `cost_sensitive_threshold_rec` | $-0.1920$ | $0.1096$ | $0.1312$ | $0.5525$ | $0.0\%$ | $32.4\%$ | $38.1\%$ |
| **`always_escalate`** | **$+0.4188$** | **$0.0275$** | **$0.0000$** | **$0.7320$** | **$100.0\%$** | **$0.0\%$** | **$0.0\%$** |
| **`cost_rule_v07` (Candidate)** | **$+0.4033$** | **$0.0317$** | **$0.0005$** | **$0.7060$** | **$83.0\%$** | **$13.4\%$** | **$3.6\%$** |
| `oracle` | $+0.7715$ | $0.0203$ | $0.0000$ | $0.9312$ | $0.0\%$ | $0.0\%$ | $49.6\%$ |

#### Primary Contrasts for `cost_rule_v07` in DE:
- vs `always_recovery`: $\bar{D} = +0.1927, S_D = 0.0351, \text{SE} = 0.0088, 95\% \text{ CI } [0.1739, 0.2114]$
- vs `budget_aware_direct_recovery`: $\bar{D} = +0.2786, S_D = 0.0508, \text{SE} = 0.0127, 95\% \text{ CI } [0.2516, 0.3057]$
- vs `cost_sensitive_threshold_recovery`: $\bar{D} = +0.5953, S_D = 0.1151, \text{SE} = 0.0288, 95\% \text{ CI } [0.5339, 0.6567]$
- **vs `always_escalate`:** **$\bar{D} = -0.0155, S_D = 0.0142, \text{SE} = 0.0035, 95\% \text{ CI } [-0.0230, -0.0079]$** (**CANDIDATE INFERIOR**)
- vs `oracle`: $\bar{D} = -0.3682, S_D = 0.0281, \text{SE} = 0.0070$

### 4.3 Critique of Package 6D Sensitivity Sweeps
The 9-cell sensitivity analysis reported in Package 6D tested variations in:
- Customer Support: $p_{\text{abandonment}} \in \{0.10, 0.25, 0.40\} \times p_{\text{salvage\_fraud}} \in \{0.50, 0.70, 0.90\}$
- Data Engineering: $p_{\text{schema\_persistent\_fail}} \in \{0.50, 0.80, 0.95\} \times p_{\text{engineer\_fix\_schema}} \in \{0.65, 0.85, 0.95\}$

While the sweep verified that the candidate policy maintained positive gains over `always_recovery` ($\hat{\theta} \in [+0.113, +0.197]$ in CS; $[+0.147, +0.213]$ in DE), **the sensitivity sweep completely failed to evaluate the candidate policy against `always_escalate`**.
- When $p_{\text{engineer\_fix\_schema}} = 0.65$ in DE, `cost_rule_v07` mean utility dropped sharply from $+0.395$ to $+0.363$.
- Because `cost_rule_v07` relies on human engineers for $88\%$ of its cases, its performance fluctuates almost entirely with human specialist competence, not autonomous algorithmic robustness.

---

## 5. Methodological Remediation Blueprint (Package 6F Requirements)

To resolve the critical scientific blockers before any protocol freeze can be authorized, the engineering and research teams must execute the following remediation plan:

### Remediation 1: Recalibrate Human Escalation Mechanics
Human escalation must not function as an infinite-capacity, cost-free silver bullet. The environment simulator must enforce realistic operational frictions:
1. **Operation Budget Consumption ($B_{\text{escalate}} = 1$):** Escalation must consume at least $1$ operation from the task budget ($B$), preventing agents from using escalation as a penalty-free zero-cost bypass.
2. **Specialist Salvage Value Discount:** Human specialist resolution must award a discounted completion value (e.g., $0.80 \times V$ in CS, $0.75 \times V$ in DE) to reflect human handling latency, queue holding, and operational friction, rather than awarding $100\%$ full net value.
3. **Capacity Constraints / Queue Degradation:** Enforce realistic queue drop probabilities or escalating cost multipliers if cluster-level escalation rates exceed operational thresholds (e.g., human on-call fatigue).

### Remediation 2: Eliminate Baseline Asymmetry & Re-specify Heuristic Comparators
1. **Action-Space Symmetry:** Modify [`cost_sensitive_threshold_recovery`](file:///d:/causaguard/src_v07/causaguard_v07/policy_v07.py#L350-L420) so that it is allowed to escalate at Step 1 whenever estimated posterior defect risk exceeds an explicit risk-aversion threshold.
2. **Elevate `always_escalate` to Primary Family:** Formally include `always_escalate` as an official primary contrast within the confirmatory Bonferroni multiplicity family. The candidate policy must prove superiority ($\hat{\theta} \ge +0.015$) against both direct recovery AND naive escalation.

### Remediation 3: Sample Size Prespecification
Adopt a formally powered cluster allocation before protocol freeze:
- **Option A (Domain-Asymmetric Powered Design):** Prespecify $K_{\text{CS}} = 160$ and $K_{\text{DE}} = 84$, guaranteeing $\ge 80\%$ marginal power for true gain $\delta = +0.030$ against margin $\Delta = +0.015$ under $\alpha = 0.01/6$.
- **Option B (Nominal Sizing with Documented MDE):** Retain $K = 64$ only if the planning effect size is formally adjusted to match the empirical MDEs ($\delta_{\text{CS}}^* = +0.0390$, $\delta_{\text{DE}}^* = +0.0322$), with explicit preregistered acknowledgment that modest gains ($\le +0.030$) cannot be detected.

### Remediation 4: Restructure Seed Namespaces
Expand prospective cluster seed intervals to eliminate all collision risks:
- CS Development: `70010001–70010160` (160 seeds)
- DE Development: `70020001–70020084` (84 seeds)
- Buffer Gap: `70020085–70049999` (quarantined reservation buffer)
- CS Final Confirmatory: `70050001–70050160` (160 seeds, strictly locked)
- DE Final Confirmatory: `70060001–70060084` (84 seeds, strictly locked)

---

## 6. Official Review Verdict & Gate Decision

```
========================================================================================
                          FORMAL PEER REVIEW GATE VERDICT
========================================================================================
  DECISION: CONDITIONAL GO FOR METHODOLOGICAL REMEDIATION (PACKAGE 6F)
  PROTOCOL FREEZE: STRICT HOLD (NOT READY FOR FREEZE)
  DEVELOPMENT EVALUATION: PROHIBITED
  FINAL EVALUATION: STRICTLY QUARANTINED
========================================================================================
```

The reported exploratory calibration results demonstrate that while the computational mechanics of CausaGuard v0.7 are bug-free and reproducible, the underlying decision model has collapsed into an escalation monoculture that is defeated by naive escalation in Data Engineering and by trivial heuristics in Customer Support.

Protocol freeze is **HELD** until the escalation mechanics and baseline symmetries are corrected and re-calibrated.

---
*Signed on behalf of the Independent Scientific Review Committee,*  
**Lead Methodological Reviewer, CausaGuard PhD Programme**  
6 November 2026


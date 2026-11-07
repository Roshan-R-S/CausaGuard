# CausaGuard v0.7.1: Prospective Confirmatory Statistical Protocol (DRAFT)

**Document ID:** `PROT-CG-071-DRAFT-01`  
**Study Version:** `0.7.1-confirmatory-draft`  
**Protocol Status:** PROSPECTIVE DRAFT — RECONCILED PRE-FREEZE SPECIFICATION (PACKAGE 6J-A)
**Commit Baseline:** [`5e1d05b`](file:///d:/causaguard) (Post-Package 6I-ENG / v0.7.1-alpha.1 baseline; previously [`3450d6e`](file:///d:/causaguard))
**Target Evaluation Engine:** Isolated v0.7.1 CausaGuard Engine (`src_v07_1/causaguard_v07_1/`)  
**Primary Confirmatory Domain:** Data Engineering Batch Pipeline Supervision (`de`)  
**Secondary Boundary Domain:** Customer Support Record Resolution (`cs`)  
**Proposed Allocation:** $K = 128$ clusters per domain, $N = 400$ cases per cluster ($51{,}200$ cases per domain)  
**Date:** November 2026  
**Authors:** CausaGuard Research Methodology & Statistical Planning Group  

---

> [!WARNING]
> ### PROSPECTIVE DRAFT NOTICE
> This document represents a **prospectively specified draft protocol**. It is **NOT** a sealed, frozen, or preregistered final artifact. No confirmatory development evaluations (`70100001+`) or final evaluations (`70200001+`) may be executed under this draft until it has been formally reviewed, assigned a prospective SHA-256 seal manifest, and authorized by an independent gate decision.

---

## 1. Scientific Objectives & Empirical Claims

### 1.1 Core Empirical Hypothesis
The central scientific inquiry of CausaGuard v0.7.1 is:
> **Under realistic operational conditions where automated interventions can disrupt healthy executions, human escalation incurs finite bandwidth and handling fees, and catastrophic failures are unobservable, does analytical Bayesian Value of Information (VOI) decision-making achieve superior operational utility ($\Delta \ge +0.015$) compared to strong direct-recovery, human-delegation, and deterministic heuristic policies?**

### 1.2 Explicit Provenance & Anti-HARKing Demarcation
In accordance with open science preregistration standards (Center for Open Science, FDA Statistical Principles):
1. **Informed Domain Selection:** The designation of **Data Engineering** as the Primary Confirmatory Domain was **informed by exploratory calibration findings** in v0.7 (Package 6D) and v0.7.1 (Package 6F-C). It is explicitly documented that in exploratory data, Data Engineering exhibited high unobservable hazard ($F_s, F_c$), costly checkpoint recovery ($v_{\text{fallback}} = 0.45 \times V$), and strong positive VOI, whereas Customer Support exhibited low-friction retry where universal direct recovery dominated.
2. **No Retrospective A Priori Pretension:** This selection must **never** be represented as an a priori hypothesis conceived prior to exploratory research. It represents a prospectively registered hypothesis for a *new, independent confirmatory sample* on strictly quarantined seeds.
3. **Preservation of the Secondary Domain:** Customer Support is **not discarded or hidden**. It is formally preregistered as a **Secondary Boundary Domain** to test the operational limits of Bayesian VOI.

### 1.3 Distinction of Analytical Bayesian VOI from Learned/Trained AI
The candidate policy `cost_rule_v07_1` is an **analytical, closed-form, non-learned decision-theoretic policy**:
- It does **not** employ neural networks, deep reinforcement learning, parameter fine-tuning, or prompt-engineered large language models.
- It computes closed-form expected utilities by propagating prior beliefs through a known causal POMDP graphical model and performing exact Bayesian conditioning on fallible diagnostic evidence.
- This distinction ensures that the confirmatory evaluation tests the fundamental decision-theoretic value of causal information, completely isolated from model training instability, generalization gap, or reward-hacking artifacts.

---

## 2. Prospective Hypothesis Architecture & Multiplicity Control

### 2.1 The Superiority Hurdle ($\Delta = +0.015$)
In enterprise automated workflow management, deploying an active Bayesian causal verification engine introduces computational latency and system complexity. A marginal gain indistinguishable from zero is insufficient to justify adoption.
- **Superiority Hurdle:** $\Delta = +0.015$ (net gain of $+1.5$ utility units per 100 tasks).
- To reject the null hypothesis, the **lower bound of the Bonferroni-corrected confidence interval** for the paired mean difference must strictly exceed $+0.015$:
  $$\text{LCB}_{\text{Bonferroni}} > +0.015$$

### 2.2 Primary Confirmatory Family: Data Engineering (`de`)
The Primary Confirmatory Family evaluates `cost_rule_v07_1` against three distinct, highly competitive baselines under symmetric action access:

$$\mathcal{H}_{0, j}: \mu_{d, j} \le +0.015 \quad \text{vs.} \quad \mathcal{H}_{1, j}: \mu_{d, j} > +0.015 \quad (j \in \{1, 2, 3\})$$

Where paired cluster difference is defined as:
$$d_{j, k} = U_{\text{cand}, k} - U_{\text{comparator}_j, k}$$

```
========================================================================================
              PRIMARY CONFIRMATORY CONTRAST SUITE (DATA ENGINEERING)
========================================================================================
  ID  CONTRAST NAME                           SCIENTIFIC COMPARISON TESTED
  --------------------------------------------------------------------------------------
  C1  cost_rule_v07_1 vs always_recovery      Value of Bayesian selective action over 
                                              universal automated checkpoint restoration.
  C2  cost_rule_v07_1 vs always_escalate      Value of autonomous intelligence over 
                                              universal on-call engineer delegation.
  C3  cost_rule_v07_1 vs cost_sensitive_     Value of analytical Bayesian VOI over 
      symmetric_heuristic                     the strongest symmetric cost-benefit heuristic.
========================================================================================
```

#### Multiplicity Control Allocation:
- Total Primary Family-Wise Error Rate: $\alpha_{\text{FWER}} = 0.010$ (one-sided).
- Bonferroni per-contrast significance threshold across $M = 3$ primary tests:
  $$\alpha_{\text{primary}} = \frac{0.010}{3} \approx 0.00333333$$
- Critical value under $K = 128$ clusters ($df = 127$):
  $$t_{\text{crit}} = t_{127, \; 1 - 0.00333333} = 2.758398 \approx 2.7584$$
- Decision Rule: Reject $\mathcal{H}_{0, j}$ if:
  $$\bar{d}_j - 2.7584 \cdot \frac{S_{D, j}}{\sqrt{128}} > +0.015$$

### 2.3 Critical Defense of Comparator Fairness (Why Heuristic C3 is Mandatory)
In Package 6G, it was proposed to replace `cost_sensitive_symmetric_heuristic` with an obsolete historical macro (`fixed_verify_repair_macro`) because the heuristic exhibited an exploratory risk of $R = 0.0633 > 0.050$.
**This draft formally rejects that substitution:**
1. **Anti-Strawman Principle:** `cost_sensitive_symmetric_heuristic` is the strongest full-action deterministic heuristic in the repository. Silently removing it from the primary family because it had a borderline risk violation in exploratory runs would constitute post-hoc baseline filtering.
2. **Rigorous Dual Win:** In exploratory runs, `cost_rule_v07_1` defeated `cost_sensitive_symmetric_heuristic` by $\mathbf{+0.2844}$ utility units ($p < 10^{-11}$). Including it directly in the primary family allows CausaGuard to demonstrate that Bayesian VOI achieves **superior utility while simultaneously maintaining safety compliance ($R = 0.0023 \le 0.050$)**, whereas the best heuristic fails safety ($R = 0.0633$).
3. **Reference Benchmark:** `fixed_verify_repair_macro` is retained as an active secondary reference benchmark ($C_{\text{ref}}$).

### 2.4 Secondary Boundary Domain: Customer Support (`cs`)
Customer Support is formally preregistered as a **Secondary Boundary Domain**:
- **Specific Boundary Hypothesis:** In workflows with low automated retry penalties ($c_{\text{retry}} = \$0.05$) and moderate customer friction, direct retry dominates complex Bayesian verification.
- **Inference Rule:** Evaluated hierarchically or as descriptive secondary endpoints. Multiplicity for primary claims is preserved entirely within Data Engineering.

---

## 3. Two-Stage Safety Gatekeeping Framework

In automated data engineering and AI agent supervision, a policy that achieves high utility by ignoring safety constraints is operationally unacceptable.

```
                           +--------------------------------+
                           |       Evaluated Policy p       |
                           +---------------+----------------+
                                           |
                                  [Gate 1: Safety]
                                 Is R(p) <= 0.050?
                                           |
                         +-----------------+-----------------+
                         |                                   |
                     (FAIL)                               (PASS)
              Disqualified as                      Eligible for
             Operationally Reckless             Superiority Contrast
                                                             |
                                                   [Gate 2: Superiority]
                                                   d_bar - Hurdle > 0?
                                                   Bonferroni LCB > +0.015?
```

### Gate 1: Clustered Operational Safety ($R(p) \le 0.050$)
- Operational Risk $R(p)$ is the expected rate of unmitigated catastrophic harm ($-H$).
- To account for intra-cluster correlation ($\rho > 0$), safety inference is conducted at the **cluster level**, where each of the $K = 128$ clusters is an independent sampling unit:
  - Cluster operational failure rate:
    $$R_k = \frac{1}{N} \sum_{i=1}^N Y_{k, i}$$
  - Clustered sample mean:
    $$\bar{R} = \frac{1}{K} \sum_{k=1}^K R_k$$
  - Cluster sample variance and standard error:
    $$s_R^2 = \frac{1}{K - 1} \sum_{k=1}^K (R_k - \bar{R})^2, \quad \text{SE}_{\text{cluster}}(\bar{R}) = \frac{s_R}{\sqrt{K}}$$
  - Upper 95% one-sided Student-$t$ confidence bound ($df = 127$, $s_R > 0$):
    $$\text{UCB}_{0.95}^{\text{cluster}} = \bar{R} + t_{0.95, 127} \times \text{SE}_{\text{cluster}}(\bar{R}) \le 0.050 \quad (t_{0.95, 127} \approx 1.6570)$$
  - **Zero-Event Boundary Standard ($R_k = 0 \ \forall k$, $s_R = 0$):**
    When zero catastrophic failures occur across all $51{,}200$ cases, $s_R = 0$, rendering $t$-bounds degenerate. Since clusters are independent Bernoulli draws, exact cluster-level Clopper-Pearson bounding yields:
    $$\text{UCB}_{0.95}(p_{\text{cluster}}) = 1 - 0.05^{1/K} = 1 - 0.05^{1/128} \approx \mathbf{0.02314} \quad (2.314\%)$$
    Because $\theta = \mathbb{E}[R_k] \le P(R_k > 0) = p_{\text{cluster}}$, this represents an assumption-free upper bound that does not require case-level independence ($\rho = 0$). Since $0.02314 \le 0.050$, Gate 1 is satisfied under zero events. Case-level independence formulas (yielding $0.0000585$) are strictly forbidden for formal gate certification.
- **Authorization Violations:** Absolute zero tolerance ($\text{Total Violations} == 0$).
- If a comparator policy fails Gate 1, it is formally recorded as **Operationally Reckless / Safety-Disqualified**.
- The candidate policy `cost_rule_v07_1` **must pass Gate 1** as an absolute prerequisite. If `cost_rule_v07_1` violates either criterion ($\text{UCB}_{0.95} > 0.050$ or $\text{Violations} > 0$), the confirmatory evaluation is declared an **immediate catastrophic failure**, regardless of utility gains.

### Gate 2: Statistical Superiority Hurdle
Candidate superiority is tested against safety-compliant baselines. If a comparator is disqualified at Gate 1, candidate superiority is established a fortiori by safety compliance.

---

## 4. Power Planning & Sample Size Sizing

### 4.1 Noncentral Student-$t$ Sizing Derivation
Statistical power was independently calculated using the exact noncentral Student-$t$ distribution for one-sided hypothesis testing with hurdle $\Delta = +0.015$ and planning effect $\delta = +0.030$:

$$t_{\text{crit}} = t_{df, \; 1 - \alpha}, \quad \text{ncp} = \frac{\delta - \Delta}{S_D / \sqrt{K}}, \quad \text{Power} = 1 - F_{\text{nct}}(t_{\text{crit}} \mid df, \text{ncp})$$

Using empirical between-cluster standard deviations from fresh exploratory calibration:
- Contrast $C_1$ vs `always_recovery`: Point $S_D = 0.02601$, Upper 95% Bound $S_D = 0.04026$.
- Contrast $C_2$ vs `always_escalate`: Point $S_D = 0.03581$, Upper 95% Bound $S_D = 0.05542$.
- Contrast $C_3$ vs `cost_sensitive_symmetric_heuristic`: Point $S_D = 0.05802$, Upper 95% Bound $S_D = 0.08980$.

### 4.2 Exact Power Table Across Sample Sizes & Multiplicity Allocations (Contrast $C_1$)

| Clusters ($K$) | Total Cases | 3-Contrast Family ($\alpha = 0.003333$) | | 4-Contrast Family ($\alpha = 0.002500$) | | 6-Contrast Family ($\alpha = 0.001667$) | |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| | | **Point $S_D$** | **Upper $S_D$** | **Point $S_D$** | **Upper $S_D$** | **Point $S_D$** | **Upper $S_D$** |
| **48** | 19,200 | 86.96% | 40.82% | 84.61% | 36.95% | 80.95% | 31.88% |
| **64** | 25,600 | 96.12% | 57.18% | 95.16% | 53.22% | 93.56% | 47.77% |
| **80** | 32,000 | 98.99% | 70.61% | 98.68% | 67.10% | 98.13% | 62.05% |
| **96** | 38,400 | 99.76% | 80.70% | 99.68% | 77.88% | 99.51% | 73.66% |
| **108** | 43,200 | 99.93% | 86.27% | 99.89% | 83.98% | 99.83% | 80.48% |
| **128** | 51,200 | **99.99%** | **92.53%** | **99.98%** | **91.04%** | **99.97%** | **88.66%** |
| **133** | 53,200 | 99.99% | 93.63% | 99.99% | 92.30% | 99.98% | 90.18% |
| **160** | 64,000 | 100.00% | 97.41% | 100.00% | 96.77% | 100.00% | 95.67% |

### 4.3 Prospective Sample Size Mandate
- **Mandated Sample Size:** **$K = 128$ clusters per domain** ($N = 400$ cases/cluster; $51{,}200$ cases per domain).
- **Conditional Power Guarantee at $K = 128$ under the 3-Contrast Family:**
  - Under point estimate $S_D = 0.02601$: **$99.99\%$ power**.
  - Under conservative upper 95% confidence bound $S_D = 0.04026$: **$92.53\%$ power** (exceeds the $90\%$ gold standard).
  - Minimum Detectable Effect (MDE) at $80\%$ power: **$+0.0270$** (comfortably below $+0.030$).
- **Power for Contrast $C_3$:** At observed difference $\bar{d} = +0.2844$, power is **$100.0\%$**. Even if true gain drops to $+0.100$, power remains **$100.0\%$**.

### 4.4 Joint Study Success Probability (Fréchet-Bonferroni Lower Bound)
To evaluate the overall probability that `cost_rule_v07_1` simultaneously rejects all $M = 3$ null hypotheses in the Primary Confirmatory Family, earlier drafts cited Slepian's inequality under positive dependence. As demonstrated in `research/methodology/v071-pre-freeze-statistical-corrections.md`, Slepian's lemma is invalid for noncentral multivariate Student-$t$ distributions sharing degrees of freedom, and positive correlation does not imply comonotonicity ($\min(P_j)$).

Instead, joint study power is rigorously bounded below by the **Fréchet-Bonferroni inequality**:
$$\text{Power}_{\text{joint}} = P\left(\bigcap_{j=1}^3 A_j\right) \ge 1 - \sum_{j=1}^3 P(A_j^c) = P(A_1) - P(A_2^c) - P(A_3^c)$$

Where $A_j$ denotes rejection of $\mathcal{H}_{0, j}$ at Bonferroni level $\alpha = 0.010/3 \approx 0.00333333$:
- **Contrast $C_1$ vs `always_recovery` ($\delta = +0.030$):**
  - Under point variance ($S_D = 0.02601$): Marginal power $P(A_1) = 0.99990$, failure risk $P(A_1^c) = 0.00010$.
  - Under conservative upper 95% bound ($S_D = 0.04026$): Marginal power $P(A_1) = 0.92525$, failure risk $P(A_1^c) = 0.07475$.
- **Contrast $C_2$ vs `always_escalate` ($\delta = +0.500$, $S_D = 0.080$):**
  - Noncentrality parameter $\lambda = \frac{0.500 - 0.015}{0.080 / \sqrt{128}} = 68.59$.
  - Failure risk $P(A_2^c) < 10^{-15}$.
- **Contrast $C_3$ vs `cost_sensitive_symmetric_heuristic` ($\delta = +0.100$, $S_D = 0.040$):**
  - Noncentrality parameter $\lambda = \frac{0.100 - 0.015}{0.040 / \sqrt{128}} = 24.04$.
  - Failure risk $P(A_3^c) < 10^{-15}$.

**Joint Study Success Guarantee at $K = 128$:**
- Under conservative variance bound ($S_D = 0.04026$):
  $$\text{Power}_{\text{joint}} \ge 1 - 0.07475 - 10^{-15} - 10^{-15} = \mathbf{92.52\%}$$
- Under point variance estimate ($S_D = 0.02601$):
  $$\text{Power}_{\text{joint}} \ge 1 - 0.00010 - 10^{-15} - 10^{-15} = \mathbf{99.99\%}$$

Even under the most conservative variance bound, joint confirmatory study power comfortably exceeds the 90% gold standard.

---

## 5. Prospective Seed Namespace Architecture

To prevent any possibility of seed collision, data snooping, or premature exposure:

```
========================================================================================
                      PROSPECTIVE SEED ALLOCATION REGISTRY
========================================================================================
  SEED BLOCK               SCOPE / ALLOCATION           STATUS / RULES
  --------------------------------------------------------------------------------------
  60001001 – 60001010      v0.6 Exploratory Variance     Historical Archived
  60010001 – 60020064      v0.6 Dev Confirmatory         Historical Sealed
  60030001 – 60040064      v0.6 Final Confirmatory       PERMANENTLY LOCKED
  --------------------------------------------------------------------------------------
  70001001 – 70001016      v0.7 Exploratory Calibration  Historical Archived (Package 6D)
  70002001 – 70002016      v0.7.1 Fresh Calibration      Historical Archived (Package 6F-C)
  70003001 – 70009999      Safety Buffer Zone            RESERVED (Pre-flight Smoke Tests)
  --------------------------------------------------------------------------------------
  70100001 – 70100128      DE Confirmatory Development   PRIMARY DEV CONFIRMATORY (K=128)
  70110001 – 70110128      CS Confirmatory Development   SECONDARY DEV CONFIRMATORY (K=128)
  70120001 – 70199999      Development Expansion Buffer  RESERVED EXPANSION
  --------------------------------------------------------------------------------------
  70200001 – 70200128      DE Confirmatory Final         STRICT QUARANTINE (K=128)
  70210001 – 70210128      CS Confirmatory Final         STRICT QUARANTINE (K=128)
  70220001 – 70299999      Final Expansion Buffer        STRICT QUARANTINE
  --------------------------------------------------------------------------------------
  70300001 – 70399999      Replication Study Reserve     INDEPENDENT LAB REPLICATION
========================================================================================
```

- **Strict Quarantine Rule:** Zero cases from `70100001+` or `70200001+` may be generated, sampled, previewed, or executed prior to formal protocol sealing.

---

## 6. Proposed Codebase & Configuration Immutability Manifest (PRE-FREEZE DRAFT)

A future formal protocol freeze will bind the exact code, runner, test, and configuration baseline. In accordance with Package 6I blocker resolutions, the immutability manifest is expanded to encompass the runner execution engine and the invariance test suite in addition to the core policy simulator:

```
========================================================================================
             PROPOSED PRE-FREEZE IMMUTABILITY MANIFEST (17 BOUND FILES)
========================================================================================
  [CORE POLICY & SIMULATOR ENGINE]
  src_v07_1/causaguard_v07_1/__init__.py:       1056a3635a314a1317eee1f52757f6804f65d6fa4f3c7a74a4eb9518116d6507
  src_v07_1/causaguard_v07_1/domain_cs.py:      6098fadf98345bcf02d69c0c2d68829800e0346598fac8629efe1113d879995c
  src_v07_1/causaguard_v07_1/domain_de.py:      9c9309b2ae00354ccf73417138224dc83e0c72ee68d352cf47eb9f2ee255fb0e
  src_v07_1/causaguard_v07_1/escalation.py:     18a612b9233a7ebaf0c341b4d47f7ff9fc59f8b6716fefdc3ed7febdb077574e
  src_v07_1/causaguard_v07_1/policy_v07_1.py:   8cd42ee3063729ef71b2104c1a07ebfa4c97f5b098cd4c022fda3d666a9ac5bf
  src_v07_1/causaguard_v07_1/study_v07_1.py:    80aedbe57135b65c99e39f0bec2c92c98272128663bc49998988a7ae840b7bbf

  [INVARIANCE & UNIT TEST SUITE]
  tests_v07_1/test_cs_domain_v07_1.py:          519915200b9300b2e08de814ae1e8bb66f35f55cf56cfd3df61899daa8bc54e8
  tests_v07_1/test_de_domain_v07_1.py:          6b26a3e1aa6ec8747b8ff8f1c936ae9109a92e68a23048af16abd6d6fabc4029
  tests_v07_1/test_escalation_v07_1.py:         ea11ce99801043215be26e29c48e1aa6bbef18d69fb53d49583c54e70caea100
  tests_v07_1/test_exploratory_runner_v07_1.py: 6b65755d91a352061c13549f6a787df9980730074fe67aa102296d11e1692377
  tests_v07_1/test_identity_preservation_v07_1.py: 43967d063971e0b902f0000b8daa90d320bff019efb7e439c9b98157cd915bd1
  tests_v07_1/test_policy_fairness_v07_1.py:    ea5cba067fe4e3f487d282f9d8ad2f580eae975e29e05cf1e119bdfb7e2e2e94
  tests_v07_1/test_study_v07_1.py:              a4cc83527c34bdbbf8f8890a8bd3e03eaaa4de6b41029f615ef2f6c42758590f
  tests_v07_1/test_confirmatory_runner_v07_1.py: 92b6135a5386b31161d23777d689fb59862b1c9f0604bcc591d3196745d3306b

  [CONFIRMATORY EVALUATION RUNNER]
  experiments_v07_1/evaluate_confirmatory_v07_1.py: b0aae881171a849e466848280737457f3093e9eed457a125158a33d8dc2b237a

  [CONFIGURATION & RUNTIME SPECIFICATIONS]
  pyproject.toml:                               1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049
  pytest_v07_1.ini (LF normalized):             de3933f9821209828c85d2b201d3a69cef9dcfcf8560e5afe5bae27c2c854a98
========================================================================================
```

- **Notice on Manifest Status:** This is a **pre-freeze proposed draft manifest**. It does **not** constitute a sealed or preregistered final artifact. Final SHA-256 seal generation and cryptographic signature will take place in the formal freeze package.
- **Immutability Mandate:** Any modification to reward parameters, labor fees, queue capacities, verification error rates, or baseline policies will invalidate this protocol draft and mandate a new versioned implementation package.

---

## 7. Cross-Platform Cryptographic Preservation Strategy

To guarantee byte-level reproducibility across Windows and POSIX systems without altering historical sealed files:
1. **Established Repository Line-Ending Rules:** As verified in Package 6I-ENG, repository-level `.gitattributes` has been committed to enforce:
   - Historical preservation: `research/methodology/v06-statistical-protocol.md text eol=crlf`
   - Modern namespace enforcement: `src_v07_1/** text eol=lf`, `tests_v07_1/** text eol=lf`, `experiments_v07_1/** text eol=lf`, `research/methodology/v071* text eol=lf`, and `docs/v071* text eol=lf`.
   - Raw byte preservation: `artifacts/v052/development-frozen.json -text`.
2. **Platform-Aware Verification Harness:** Verification harnesses verify disk bytes against LF-normalized git blobs, ensuring cross-platform stability regardless of checkout environment.

---

## 8. Prespecified Decision Rules for Negative and Inconclusive Outcomes

The confirmatory experiment is designed with complete decisional symmetry:
1. **Positive Confirmatory Success:** Candidate policy satisfies Gate 1 ($R \le 0.050$) and rejects all three null hypotheses in the Primary Confirmatory Family ($\text{LCB}_{\text{Bonferroni}} > +0.015$).
2. **Negative Boundary Finding (Heuristic Equivalence):** If candidate fails to reject $H_{0, 3}$ against `cost_sensitive_symmetric_heuristic` while passing Gate 1, the result is reported as a **Negative Finding for VOI Complexity**: proving that simple deterministic heuristics capture the economic value of sequential intervention without Bayesian computation.
3. **Negative Safety Finding (Overconfidence):** If candidate fails Gate 1 ($R > 0.050$), the result is reported as a **Safety Disqualification**: proving that analytical VOI overestimates model certainty in high-hazard environments.
4. **Inconclusive Finding:** If $\bar{d}_j > +0.015$ but the lower confidence bound fails to clear $+0.015$ due to observed variance, the finding is reported as **Statistically Underpowered / Inconclusive**.

---

*Authored on behalf of the Methodological Planning Group,*  
**CausaGuard PhD Programme**  
November 2026


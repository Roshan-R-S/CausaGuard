# CausaGuard v0.7.1: Prospective Confirmatory Statistical Protocol

**Document ID:** `PROT-CG-071-REVIEW-01`
**Study Version:** `0.7.1-isolated`
**Protocol Status:** REVIEW CANDIDATE — PRE-FREEZE — NOT APPROVED
**Commit Baseline:** [`f7eb5e7`](file:///d:/causaguard) (`security(v071): add fail-closed protocol seal verification` — Pre-freeze preparation baseline; not an approved final freeze commit)
**Target Evaluation Engine:** Isolated v0.7.1 CausaGuard Engine (`src_v07_1/causaguard_v07_1/`)
**Primary Confirmatory Domain:** Data Engineering Batch Pipeline Supervision (`data_engineering`, `de`)
**Secondary Boundary Domain:** Customer Support Record Resolution (`customer_support`, `cs`)
**Sample Allocation:** $K = 128$ independent clusters per domain, $N = 400$ cases per cluster ($51{,}200$ cases per domain)
**Date:** November 2026
**Authors:** CausaGuard Research Methodology & Statistical Planning Group

---

> [!WARNING]
> ### NON-AUTHORIZING REVIEW CANDIDATE — PRE-FREEZE NO-GO
> This document represents the **authoritative review-candidate specification** for the prospective CausaGuard v0.7.1 confirmatory evaluation.
> - **Protocol Status:** PRE-FREEZE REVIEW CANDIDATE (NOT APPROVED).
> - **Formal Protocol Seal:** NOT CREATED.
> - **Confirmatory Development Authorization:** STRICTLY LOCKED (`confirmatory_development_authorized: false`).
> - **Confirmatory Experimental Execution:** STRICTLY PROHIBITED.
>
> Neither confirmatory development seeds (`70100001+`) nor final evaluation seeds (`70200001+`) may be sampled, generated, or evaluated under this candidate until independent scientific review approves this protocol, assigns the detached cryptographic seal, and issues an authorized signing record.

---

## 1. Scientific Objectives & Empirical Claims

### 1.1 Core Empirical Hypothesis
The central scientific inquiry of CausaGuard v0.7.1 is:
> **Under operational conditions where automated interventions can disrupt healthy executions, human escalation incurs finite bandwidth and labor fees, and catastrophic failures are unobservable, does analytical Bayesian Value of Information (VOI) decision-making achieve superior operational utility ($\Delta \ge +0.015$) compared to strong direct-recovery, universal-escalation, and deterministic heuristic policies?**

### 1.2 Explicit Provenance & Anti-HARKing Demarcation
In strict compliance with open science preregistration standards (Center for Open Science, FDA Statistical Principles E9):
1. **Informed Domain Selection:** The designation of **Data Engineering** as the Primary Confirmatory Domain was **informed by exploratory calibration findings** in v0.7 (Package 6D) and v0.7.1 (Package 6F-C). In exploratory data, Data Engineering exhibited high unobservable hazard rates ($F_s, F_c$), costly checkpoint recovery ($v_{\text{fallback}} = 0.45 \times V$), and strong positive VOI, whereas Customer Support exhibited low-friction retry where universal direct recovery dominated.
2. **No Retrospective A Priori Pretension:** This selection must **never** be represented as an a priori hypothesis conceived prior to exploratory research. It represents a prospectively registered hypothesis for a *new, independent confirmatory sample* on strictly quarantined seeds.
3. **Preservation of the Secondary Domain:** Customer Support is **not discarded or hidden**. It is formally registered as a **Secondary Boundary Domain** to test the operational limits of Bayesian VOI.

### 1.3 Distinction of Analytical Bayesian VOI from Learned/Trained AI
The candidate policy `cost_rule_v07_1` is an **analytical, closed-form, non-learned decision-theoretic policy**:
- It does **not** employ neural networks, deep reinforcement learning, parameter fine-tuning, or prompt-engineered large language models.
- It computes closed-form expected utilities by propagating prior beliefs through a causal POMDP graphical model and performing exact Bayesian conditioning on fallible diagnostic evidence.
- This design guarantees that the confirmatory evaluation tests the fundamental decision-theoretic value of causal information, completely isolated from model training instability, generalization gaps, or reward-hacking artifacts.

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
  $$\alpha_{\text{primary}} = \frac{0.010}{3} \approx 0.0033333333333333335$$
- Critical value under $K = 128$ clusters ($df = 127$):
  $$t_{\text{crit}} = t_{127, \; 1 - 0.00333333} = 2.75839762\dots \approx \mathbf{2.758398} \quad (\text{rounded: } 2.7584)$$
- Decision Rule: Reject $\mathcal{H}_{0, j}$ if:
  $$\bar{d}_j - 2.758398 \cdot \frac{S_{D, j}}{\sqrt{128}} > +0.015$$

### 2.3 Comparator Fairness & Mandatory Inclusion of Heuristic C3
In Package 6G review, it was noted that `cost_sensitive_symmetric_heuristic` exhibited an exploratory risk of $R = 0.0633 > 0.050$.
**This protocol formally mandates the retention of Contrast C3:**
1. **Anti-Strawman Principle:** `cost_sensitive_symmetric_heuristic` is the strongest full-action deterministic heuristic in the repository. Omitting it from the primary family because of a borderline risk violation in exploratory runs would constitute post-hoc baseline suppression.
2. **Dual-Gate Superiority:** In exploratory calibration, `cost_rule_v07_1` defeated `cost_sensitive_symmetric_heuristic` by $\mathbf{+0.2844}$ utility units ($p < 10^{-11}$). Retaining it in the primary family enables CausaGuard to demonstrate that Bayesian VOI achieves **superior utility while simultaneously maintaining safety compliance ($R = 0.0023 \le 0.050$)**, whereas the best heuristic fails safety ($R = 0.0633$).
3. **Reference Benchmarks:** `fixed_verify_repair_macro` is retained as an active secondary reference benchmark ($C_{\text{ref}}$).

### 2.4 Secondary Boundary Domain: Customer Support (`cs`)
Customer Support is formally preregistered as a **Secondary Boundary Domain**:
- **Boundary Hypothesis:** In workflows with low automated retry penalties ($c_{\text{retry}} = \$0.05$) and moderate customer friction, direct retry dominates complex Bayesian verification.
- **Inference Hierarchy:** Evaluated as secondary/exploratory endpoints. Multiplicity for primary claims is preserved entirely within Data Engineering.

---

## 3. Two-Stage Safety Gatekeeping Framework

In autonomous engineering workflow supervision, policies achieving high utility through safety violations are disqualified.

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
- To account for intra-cluster correlation ($\rho > 0$), safety inference is conducted at the **cluster level** ($K = 128$ independent clusters):
  - Cluster operational failure rate:
    $$R_k = \frac{1}{N} \sum_{i=1}^N Y_{k, i}$$
  - Clustered sample mean:
    $$\bar{R} = \frac{1}{K} \sum_{k=1}^K R_k$$
  - Cluster sample variance and standard error:
    $$s_R^2 = \frac{1}{K - 1} \sum_{k=1}^K (R_k - \bar{R})^2, \quad \text{SE}_{\text{cluster}}(\bar{R}) = \frac{s_R}{\sqrt{K}}$$
  - Upper 95% one-sided Student-$t$ confidence bound ($df = 127$, $s_R > 0$):
    $$\text{UCB}_{0.95}^{\text{cluster}} = \bar{R} + t_{0.95, 127} \times \text{SE}_{\text{cluster}}(\bar{R}) \le 0.050 \quad (t_{0.95, 127} \approx 1.6570)$$
    *Limitation:* Finite-sample validity of Student-$t$ inference strictly requires Gaussian cluster outcomes. For non-Gaussian bounded rates, CLT-based inference across $K = 128$ clusters is asymptotic and approximate; finite-sample $t$-intervals are not automatically guaranteed to be strictly conservative.
  - **Zero-Event Boundary Standard ($R_k = 0 \ \forall k$, $s_R = 0$):**
    When zero catastrophic failures occur across all $51{,}200$ cases, $s_R = 0$, rendering $t$-bounds degenerate. Under the model assumption that clusters behave as independent Bernoulli trials with parameter $p_{\text{cluster}} = P(R_k > 0)$, exact one-sided $95\%$ Clopper-Pearson binomial tail bounding yields:
    $$\text{UCB}_{0.95}(p_{\text{cluster}}) = 1 - 0.05^{1/K} = 1 - 0.05^{1/128} = 0.0231324053\dots \approx \mathbf{0.023132405}$$
    The reported threshold value **$0.02314$** represents an explicit **conservative upward rounding** of this exact value, preserving the nominal $\ge 95\%$ confidence coverage.
    Because $\theta = \mathbb{E}[R_k] \le P(R_k > 0) = p_{\text{cluster}}$, this represents an upper bound on population operational risk that does not require case-level independence ($\rho = 0$). Since $0.02314 \le 0.050$, Gate 1 is satisfied under zero events. Unadjusted case-level independence formulas (yielding $0.0000585$) are strictly forbidden for formal gate certification.
  - **Degenerate Constant Positive Risk Regime ($s_R = 0, \bar{R} > 0$):**
    When constant nonzero harm occurs across all clusters ($s_R = 0, \bar{R} > 0$), degenerate zero-variance data cannot support standard Student-$t$ inference without unverified distributional assumptions, nor can zero-event Clopper-Pearson bounds apply. In this regime, safety governance mandates an immediate fail-closed **INCONCLUSIVE / GATE 1 FAIL** outcome (`gate1_passed = False`, `inference_method = "degenerate_constant_positive_risk_fail_closed"`). For downstream numeric compatibility, $\text{UCB}_{\text{cluster}}$ is set to $1.0$ as an explicit worst-case policy bound (not a calculated 95% confidence estimate), ensuring candidate disqualification.
- **Authorization Violations:** Absolute zero tolerance ($\text{Total Violations} == 0$).
- **Disqualification Rule:** The candidate policy `cost_rule_v07_1` **must pass Gate 1** as an absolute prerequisite. If `cost_rule_v07_1` violates either criterion ($\text{UCB}_{0.95} > 0.050$ or $\text{Violations} > 0$), the evaluation is declared an **immediate catastrophic failure**, regardless of utility gains.

### Gate 2: Statistical Superiority Hurdle
Candidate superiority is tested against safety-compliant baselines. If a comparator is disqualified at Gate 1, candidate superiority is established a fortiori by safety compliance.

---

## 4. Power Planning & Sample Size Sizing

### 4.1 Noncentral Student-$t$ Sizing Derivation
Statistical power was independently calculated using the exact noncentral Student-$t$ distribution for one-sided hypothesis testing with hurdle $\Delta = +0.015$ and planning effect $\delta = +0.030$:

$$t_{\text{crit}} = t_{df, \; 1 - \alpha}, \quad \text{ncp} = \frac{\delta - \Delta}{S_D / \sqrt{K}}, \quad \text{Power} = 1 - F_{\text{nct}}(t_{\text{crit}} \mid df, \text{ncp})$$

Using empirical between-cluster standard deviations from exploratory calibration:
- Contrast $C_1$ vs `always_recovery`: Point $S_D = 0.02601$, Upper 95% Bound $S_D = 0.04026$.
- Contrast $C_2$ vs `always_escalate`: Point $S_D = 0.03581$, Upper 95% Bound $S_D = 0.05542$.
- Contrast $C_3$ vs `cost_sensitive_symmetric_heuristic`: Point $S_D = 0.05802$, Upper 95% Bound $S_D = 0.08980$.

### 4.2 Exact Power Allocation at $K = 128$ Clusters
- **Mandated Sample Size:** **$K = 128$ clusters per domain** ($N = 400$ cases/cluster; $51{,}200$ cases per domain).
- **Conditional Power for Contrast $C_1$ under the 3-Contrast Family:**
  - Under point estimate $S_D = 0.02601$: **$99.99\%$ power**.
  - Under conservative upper 95% confidence bound $S_D = 0.04026$: **$92.52\%$ power** (exceeds the $90\%$ gold standard).
  - Minimum Detectable Effect (MDE) at $80\%$ power: **$+0.0270$** (comfortably below $+0.030$).
- **Power for Contrast $C_2$ & $C_3$:** At expected differences ($\bar{d}_{C2} \approx +0.500$, $\bar{d}_{C3} \ge +0.100$), power is $> 99.99\%$.

### 4.3 Joint Study Success Probability (Fréchet-Bonferroni Lower Bound)
Joint study power is bounded below by the **Fréchet-Bonferroni inequality**:
$$\text{Power}_{\text{joint}} = P\left(\bigcap_{j=1}^3 A_j\right) \ge 1 - \sum_{j=1}^3 P(A_j^c) = P(A_1) - P(A_2^c) - P(A_3^c)$$

Where $A_j$ denotes rejection of $\mathcal{H}_{0, j}$ at Bonferroni level $\alpha = 0.010/3 \approx 0.00333333$:
- **Contrast $C_1$ vs `always_recovery` ($\delta = +0.030$):**
  - Under point variance ($S_D = 0.02601$): Marginal power $P(A_1) = 0.99990$, failure risk $P(A_1^c) = 0.00010$.
  - Under conservative upper 95% bound ($S_D = 0.04026$): Marginal power $P(A_1) = 0.92518$, failure risk $P(A_1^c) = 0.07482$.
- **Contrast $C_2$ vs `always_escalate` ($\delta = +0.500$, $S_D = 0.080$):**
  - Noncentrality parameter $\lambda = \frac{0.500 - 0.015}{0.080 / \sqrt{128}} = 68.59$. Failure risk $P(A_2^c) < 10^{-15}$.
- **Contrast $C_3$ vs `cost_sensitive_symmetric_heuristic` ($\delta = +0.100$, $S_D = 0.040$):**
  - Noncentrality parameter $\lambda = \frac{0.100 - 0.015}{0.040 / \sqrt{128}} = 24.04$. Failure risk $P(A_3^c) < 10^{-15}$.

**Joint Study Success Guarantee at $K = 128$:**
- Under conservative variance bound ($S_D = 0.04026$):
  $$\text{Power}_{\text{joint}} \ge 1 - 0.07482 - 10^{-15} - 10^{-15} = \mathbf{92.52\%}$$
- Under point variance estimate ($S_D = 0.02601$):
  $$\text{Power}_{\text{joint}} \ge 1 - 0.00010 - 10^{-15} - 10^{-15} = \mathbf{99.99\%}$$

---

## 5. Prospective Seed Namespace Architecture

To prevent seed collision, exploratory snooping, or premature exposure:

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

## 6. Review-Candidate Immutability Manifest (21 Assets)

In accordance with Package 6K security remediations, the prospective protocol manifest encompasses the complete 21-asset architecture:

```
========================================================================================
            REVIEW-CANDIDATE IMMUTABILITY MANIFEST (21 ASSETS)
========================================================================================
  [CORE SIMULATOR & POLICY ENGINE]
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
  tests_v07_1/test_confirmatory_runner_v07_1.py: 6273cad72b66c90d10543e436865f976e60da84852bc925ece323ffd438208fc

  [CONFIRMATORY RUNNER ENGINE]
  experiments_v07_1/evaluate_confirmatory_v07_1.py: 5c4158edbc4651bd232808de5764ccf9925ac77cd87e3b6c1d543ef9808f6a3d

  [CONFIGURATION & RUNTIME SPECIFICATIONS]
  pyproject.toml:                               1141251febe3c6fed044f1a8a77df2dafd4ad3ecc1bca3e0df4a9daa38430049
  pytest_v07_1.ini (LF normalized):             de3933f9821209828c85d2b201d3a69cef9dcfcf8560e5afe5bae27c2c854a98

  [SECURITY VERIFIER INFRASTRUCTURE]
  experiments_v07_1/verify_seal_v07_1.py:       a382dafb2c219ba953b96a9c03af01bc7bf4b4f50d8e36afef07fd43b6c60d47
  tests_v07_1/test_seal_verifier_v07_1.py:      ee38adb0f9f739c499973c82d41eb4219f7aabc3c60cee5ade03fc92fb770f64

  [AUTHORITATIVE PROTOCOL SPECIFICATIONS]
  research/methodology/v071-confirmatory-statistical-protocol.md:  (Bound in detached seal experiments_v07_1/v071_protocol_seal.json at freeze time)
  experiments_v07_1/v071_confirmatory_protocol.json:               (Bound in detached seal experiments_v07_1/v071_protocol_seal.json at freeze time)
========================================================================================
```

- **Detached Seal Mechanism:** The protocol seal will reside in detached manifest `experiments_v07_1/v071_protocol_seal.json`, binding the complete 21-asset suite and preventing circular self-hashing.

---

## 7. Methodological Assumptions & Explicit Research Limitations

1. **PRNG Cluster Independence Assumption:** In computational experiments, clusters are instantiated with distinct integer seeds. Distinct PRNG seeds alone do not establish independent sampling clusters in a physical or measure-theoretic sense. Algorithmic pseudo-random sequences may exhibit unobserved inter-sequence cross-talk or generator cycle overlaps. The statistical inference model *assumes* that the generator produces sequences with negligible inter-cluster correlation under the designated simulators. This is an explicit operational modeling assumption and limitation, not an empirically verified physical property.
2. **Student-$t$ Finite-Sample Coverage:** Exact finite-sample validity under Student-$t$ requires Gaussian cluster outcomes. For non-Gaussian bounded rates or utilities, CLT-based inference across $K = 128$ is asymptotic and approximate; finite-sample $t$-intervals are not automatically guaranteed to be strictly conservative.
3. **Historical v0.5.2 Dynamic Provenance Limitation:** The historical v0.5.2 identity seal (`053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6`) and frozen artifact (`artifacts/v052/development-frozen.json`) are cryptographically bound into `historical_seal_dependencies` as an immutable frozen anchor. However, dynamic regeneration of v0.5.2 from scratch remains unresolved due to an exact hash mismatch on historical `tests/test_v052_study.py` documented in Package 6B/6C. The confirmatory study treats v0.5.2 solely as an immutable cryptographic benchmark, acknowledging this provenance limitation explicitly.

---

## 8. Cross-Platform Cryptographic Preservation Strategy

1. **Repository Line-Ending Configuration:** Enforced via repository `.gitattributes`:
   - Historical preservation: `research/methodology/v06-statistical-protocol.md text eol=crlf`
   - Modern namespaces: `src_v07_1/** text eol=lf`, `tests_v07_1/** text eol=lf`, `experiments_v07_1/** text eol=lf`, `research/methodology/v071* text eol=lf`, `docs/v071* text eol=lf`.
   - Raw byte preservation: `artifacts/v052/development-frozen.json -text`.
2. **Platform-Aware Verification Harness:** Verification harnesses check raw disk bytes against LF-normalized git blobs for approved text extensions (`.py`, `.md`, `.json`, `.ini`, `.toml`). Line normalization is strictly forbidden on historical artifacts (`artifacts/`, `experiments_v05/`, `experiments_v06/`).

---

## 9. Prespecified Decision Rules for Experimental Outcomes

1. **Positive Confirmatory Success:** Candidate policy satisfies Gate 1 ($R \le 0.050$) and rejects all three null hypotheses in the Primary Confirmatory Family ($\text{LCB}_{\text{Bonferroni}} > +0.015$).
2. **Negative Boundary Finding (Heuristic Equivalence):** If candidate fails to reject $\mathcal{H}_{0, 3}$ against `cost_sensitive_symmetric_heuristic` while passing Gate 1, the result is reported as a **Negative Finding for VOI Complexity**: proving that simple deterministic heuristics capture the economic value of sequential intervention without Bayesian computation.
3. **Negative Safety Finding (Overconfidence):** If candidate fails Gate 1 ($R > 0.050$), the result is reported as a **Safety Disqualification**: proving that analytical VOI overestimates model certainty in high-hazard environments.
4. **Inconclusive Finding:** If $\bar{d}_j > +0.015$ but the lower confidence bound fails to clear $+0.015$ due to observed variance, the finding is reported as **Statistically Underpowered / Inconclusive**.

---

## 10. Independent Approval & Prospective Sealing Governance

1. **Authoritative Key Infrastructure:** Production authorization requires an external signing identity outside the repository payload. Unkeyed SHA-256 digests or self-generated metadata flags cannot authorize execution.
2. **Detached Cryptographic Protocol Seal:** At formal freeze time, an authorized oversight entity will inspect the repository, generate `experiments_v07_1/v071_protocol_seal.json`, bind the 21 asset hashes, compute the canonical digest, and sign the payload with an external authorized key.
3. **Pre-Freeze Status:** Until formal freeze review is completed and signed, `PRODUCTION_AUTHORIZATION_ENABLED` remains `False`, the runner remains fail-closed locked, and confirmatory execution is strictly prohibited.
4. **Unresolved Authorization Governance Decision:** The specific production cryptographic authorization mechanism (e.g., asymmetric Ed25519 digital signature vs. multi-party threshold signature vs. external key management service), the key distribution architecture, and the trusted signer registry population remain an unresolved security and governance decision to be formally established by the independent scientific oversight authority prior to freeze. No production signing keys are provisioned, committed, or enabled in this baseline.

---

*Authored on behalf of the Methodological Planning Group,*
**CausaGuard PhD Programme**
November 2026

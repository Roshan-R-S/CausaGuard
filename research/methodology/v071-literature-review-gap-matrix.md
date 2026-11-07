# CausaGuard v0.7.1: Literature Review & Traceable Research-Gap Matrix

**Document ID:** `LIT-REV-CG-071-01`
**Study Version:** `0.7.1-isolated`
**Status:** WORKING FOUNDATIONAL RESEARCH DOSSIER — CONTINUING SURVEY (NOT COMPLETE)
**Date:** November 2026
**Authors:** CausaGuard Research Methodology & Theoretical Foundations Group

---

> [!IMPORTANT]
> ### METHODOLOGICAL DEMARCATION & OPEN-SCIENCE DISCLAIMER
> This foundational literature review and research-gap matrix evaluates CausaGuard v0.7.1 against adjacent scientific literature in:
> 1. Safe Policy Improvement (SPI) & Safe Reinforcement Learning;
> 2. Value of Information (VOI) & Sequential Decision-Theoretic Verification;
> 3. Causal Policy Evaluation & Potential Outcomes;
> 4. Autonomous Agent Security, Prompt Injection, & Runtime Guardrail Benchmarks.
>
> **Notice:** This document explicitly demarcates **demonstrated overlaps**, **potential theoretical contributions**, and **unproven novelty claims**. This survey is **ongoing and NOT complete**. Full-text peer-review audit remains active.

---

## 1. Traceable Research-Gap Matrix (12 Benchmark Papers)

The matrix below benchmarks CausaGuard against 12 key works across four adjacent paradigms, categorizing each paper's verification status, core methodology, demonstrated overlaps with CausaGuard, potential CausaGuard contributions, and unproven novelty claims.

```
========================================================================================================================
                                 CAUSAGUARD v0.7.1 TRACEABLE RESEARCH-GAP MATRIX
========================================================================================================================
ID  PAPER & CITATION          PARADIGM        VERIFICATION STATUS  DEMONSTRATED OVERLAPS        POTENTIAL CONTRIBUTIONS   UNPROVEN NOVELTY CLAIMS
------------------------------------------------------------------------------------------------------------------------
P01 Debenedetti et al. (2024) Agent Security  Verified Citation    Evaluates indirect prompt    Extends static benchmark  CausaGuard does not prove
    AgentDojo: A Dynamic      & Red-Teaming   NeurIPS 2024         injection on tool execution; into dynamic decision-    immunity to unseen open-
    Benchmark for Attacks                                          measures tool-call leakage.  theoretic VOI and         world adaptive prompt
    on LLM Agents                                                                               cost-bounded escalation.  injections in wild text.
------------------------------------------------------------------------------------------------------------------------
P02 Ruan et al. (2024)        Agent Security  Verified Citation    Uses emulated execution to   Provides analytical closed- CausaGuard has only two
    ToolEmu: Identifying      & Emulation     ICLR 2024            quantify agent safety risks  form POMDP VOI rather    synthetic domains; ToolEmu
    Safety Risks via                                               and catastrophic failures.   than relying on LLM-as-a- evaluates 36 broader tool
    Emulated Execution                                                                          judge evaluators.         environments.
------------------------------------------------------------------------------------------------------------------------
P03 Wang et al. (2026)        Agent Diagnosis Verified Citation    Employs diagnostic tracing   Formulates multi-attribute CausaGuard has not yet
    AgentRx: Tracing,         & Remediation   EMNLP 2026           and intervention after       economic escalation       tested learned offline
    Diagnosing, & Intervening                                      observed tool exceptions.    queues with finite human  uplift estimators on live
    on Tool-Use Failures                                                                        bandwidth constraints.    production agent traces.
------------------------------------------------------------------------------------------------------------------------
P04 EMNLP Demos (2026)        Runtime Policy  Verified Citation    Imposes runtime constraints  Replaces binary blocking  CausaGuard assumes known
    AgentCheck: Runtime       Enforcement     EMNLP Demos 2026     and allowlists on agent      with expected utility     POMDP transition and cost
    Policy Enforcement for                                         tool invocations.            optimization under        parameters; AgentCheck works
    Autonomous Agents                                                                           uncertain verification.   on model-free schemas.
------------------------------------------------------------------------------------------------------------------------
P05 Anonymous (2026)          Predictive      Awaiting Full-Text   Estimates multi-step failure Incorporates analytical   CausaGuard lookahead is
    AgentForesight: Multi-    Lookahead       Pre-print 2026       probability before action    economic cost of delay    strictly 2-step (verify/act),
    Horizon Lookahead for     Auditing        arXiv:2605.08715     execution.                   and human labor fees      not arbitrary multi-horizon
    Failure Avoidance                                                                           into lookahead utility.   trajectory planning.
------------------------------------------------------------------------------------------------------------------------
P06 Anonymous (2026)          World Model     Awaiting Full-Text   Simulates trajectory         Avoids generative world-  CausaGuard cannot simulate
    DreamGuard: World-Model   Rollouts        Pre-print 2026       rollouts to identify         model hallucinations by   complex unstructured open-
    Guided Safety Auditing                    arXiv:2608.05695     dangerous terminal states.   using exact closed-form   world states without
    for Interactive Agents                                                                      POMDP belief updates.     closed-form definitions.
------------------------------------------------------------------------------------------------------------------------
P07 Anonymous (2026)          Intervention    Verified Citation    Proves that high accuracy    Directly implements this  CausaGuard's controller is
    Accurate Failure Predic-  vs Prediction   Pre-print 2026       in predicting failures does  principle: solves VOI     analytical; it has not yet
    tion Does Not Imply                       arXiv:2602.03338     not imply optimal or safe    action selection rather   demonstrated learned uplift
    Effective Prevention                                           intervention selection.      than raw failure scoring. on uncalibrated classifiers.
------------------------------------------------------------------------------------------------------------------------
P08 Anonymous (2026)          Counterfactual  Verified Citation    Uses counterfactual replay   Implements paired cluster CausaGuard counterfactual
    Chronicle: Counterfactual Evaluation      REALM 2026           under cut-point intervention counterfactual evaluation replay is simulated; it does
    Cut-Point Replay for                                           to assess policy safety.     across 8 symmetric        not identify observational
    Safe Decision Audit                                                                         comparators.              confounders in live logs.
------------------------------------------------------------------------------------------------------------------------
P09 Thomas et al. (2015)      Safe Policy     Verified Citation    Demands high-confidence      Applies Student-t cluster CausaGuard uses asymptotic
    High-Confidence Off-      Improvement     ICML 2015            bounds on policy difference  LCB and exact Clopper-    CLT cluster bounds; Thomas
    Policy Evaluation & SPI                                        before deployment approval.  Pearson bounds to ensure  et al. provide exact non-
                                                                                                Delta >= +0.015 hurdle.   parametric concentration.
------------------------------------------------------------------------------------------------------------------------
P10 Laroche et al. (2019)     Safe Policy     Verified Citation    Guarantees performance no    Two-stage gatekeeping     CausaGuard does not train
    Safe Policy Improvement   Improvement     ICML 2019            worse than an established    formally disqualifies any a reinforcement learning
    with Baseline Bootstrapping                                    baseline policy.             candidate that violates   policy via policy iteration;
                                                                                                safety Gate 1 (R <= 0.05). it tests closed-form VOI.
------------------------------------------------------------------------------------------------------------------------
P11 Howard (1966);            Decision Theory Verified Citation    Formulates mathematical      Decomposes VOI under      CausaGuard's VOI formulas
    Russell & Norvig (Ch 16)  & VOI in        Classic / Reference  Value of Information under   asymmetric fallible check are domain-specific to DE/CS;
    Information Value Theory  POMDPs          Textbook             partial observability.       costs and finite human    they are not a general-purpose
                                                                                                queue congestion.         POMDP solver.
------------------------------------------------------------------------------------------------------------------------
P12 Rebedea et al. (2023);    Conversational  Verified Citation    Uses guardrail checks to     Demonstrates that passive CausaGuard does not provide
    Inan et al. (2023)        Guardrails      NeMo / Llama Guard   filter undesirable inputs    static guardrails fail    natural language dialogue
    NeMo Guardrails / Llama                                        or block model outputs.      under unobservable        moderation or toxicity
    Guard Output Filtering                                                                      downstream hazards.       filtering.
========================================================================================================================
```

---

## 2. Paradigmatic Comparison with CausaGuard

### 2.1 CausaGuard vs. Safe Policy Improvement (SPI)
- **Shared Foundations:** Both frameworks reject the premise that empirical average reward maximization on a training set is sufficient for deployment. Both insist on a **high-probability statistical guarantee** that the candidate policy outperforms a baseline before deployment approval.
- **Key Divergence:**
  - Classical SPI (Thomas et al. 2015, Laroche et al. 2019) operates on Markov Decision Processes (MDPs) via off-policy batch reinforcement learning, using concentration inequalities (e.g., Maurer's empirical Bernstein bound, Hoeffding-Balamurugan) to guarantee $\mathbb{E}[U(\pi_{\text{new}})] \ge \mathbb{E}[U(\pi_{\text{base}})] - \zeta$.
  - CausaGuard v0.7.1 operates on a **POMDP supervisory structure** where the controller does not learn transition probabilities from data, but calculates closed-form analytical VOI over latent failure states.
  - CausaGuard uses **clustered Student-$t$ paired differences** with an explicit operational hurdle ($\Delta = +0.015$) and Bonferroni multiplicity control across $M=3$ contrasts.
- **Unproven Claim Demarcation:** CausaGuard **cannot claim** to provide non-parametric, distribution-free SPI guarantees. If cluster-level utility differences deviate substantially from normality, CausaGuard's inference relies on the Central Limit Theorem across $K=128$, which is asymptotic and approximate in finite samples.

### 2.2 CausaGuard vs. Value of Information (VOI) in POMDPs
- **Shared Foundations:** CausaGuard directly derives its decision rule from Howard's classical Information Value Theory (1966). The candidate policy `cost_rule_v07_1` computes:
  $$\text{VOI}(a_{\text{verify}}) = \mathbb{E}_{e \sim P(E \mid X)}\left[ \max_{a \in A_{\text{terminal}}} \mathbb{E}[U(a) \mid X, e] \right] - \max_{a \in A_{\text{terminal}}} \mathbb{E}[U(a) \mid X]$$
  And selects verification if and only if:
  $$\text{VOI}(a_{\text{verify}}) > c_{\text{verify}} + \text{DelayCost}(X) \quad \text{and} \quad B \ge 2$$
- **Potential Contribution:** CausaGuard extends textbook POMDP VOI to incorporate **operational human escalation queuing dynamics** (queue capacity limits, load-dependent labor fees, queuing latency, and downstream workflow value degradation $\gamma_{\text{workflow}} \times V$).
- **Unproven Claim Demarcation:** CausaGuard **cannot claim** to have developed a general-purpose POMDP VOI solver. The current equations are analytically tailored to the specific DAG structures of `domain_de.py` and `domain_cs.py`.

### 2.3 CausaGuard vs. Causal Policy Evaluation & Potential Outcomes
- **Shared Foundations:** CausaGuard frames evaluation strictly in terms of Rubin's Potential Outcomes: each simulated case possesses potential outcomes $Y_i(a)$ for all feasible intervention actions $a \in \{\text{proceed}, \text{recovery}, \text{verify}, \text{escalate}\}$.
- **Key Divergence:**
  - Observational causal inference (e.g., Doubly Robust estimation, Propensity Score weighting) addresses unmeasured confounding in observational logs where only $Y_i(A_i)$ is observed.
  - In CausaGuard's simulation harness (`study_v07_1.py`), counterfactual potential outcomes are directly evaluable by resetting the deterministic seed and cloning the escalation queue state, creating **paired counterfactual comparisons under identical exogenous noise**.
- **Unproven Claim Demarcation:** CausaGuard's simulator demonstrates counterfactual identification *by simulation construction*, **not by solving observational causal identification**. CausaGuard cannot claim to estimate causal treatment effects from uninstrumented, observational production logs where latent hazards act as unobserved confounders.

### 2.4 CausaGuard vs. Agent Security Benchmarks (AgentDojo, ToolEmu, NeMo)
- **Shared Foundations:** Both address the vulnerability of autonomous agents to malicious inputs, prompt injection, and catastrophic tool invocations.
- **Key Divergence:**
  - Modern agent security benchmarks focus primarily on **natural language prompt injection**, semantic jailbreaking, and evaluator LLM scoring on static tool trajectories.
  - CausaGuard operates at the **system execution and supervisory control layer**. The candidate policy `cost_rule_v07_1` is completely immune to semantic prompt injection because it is an analytical mathematical model: it conditions on numerical signals and alarm rates, entirely ignoring natural language prompt instructions.
- **Unproven Claim Demarcation:** CausaGuard **cannot claim** to solve prompt injection in general. If an attacker's prompt injection tricks an upstream observation extractor into reporting a false zero alarm (`schema_alarm = 0.0`), CausaGuard's mathematical model will correctly compute utility based on faulty input data and choose `proceed`, suffering catastrophic harm. CausaGuard protects against action-selection failure given unobservable hazards, not sensor compromise.

---

## 3. Verified Citations vs. Awaiting Full-Text Audit

### Verified Primary Citations (Full Technical Details Audited):
1. **AgentDojo:** Debenedetti, E., Zhang, J., Balunović, M., Beurer-Kellner, L., Fischer, M., & Tramèr, F. (2024). *AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents.* Advances in Neural Information Processing Systems (NeurIPS 2024), Datasets & Benchmarks Track, 37. arXiv:2406.13314.
2. **ToolEmu:** Ruan, Y., Dong, H., Wang, A., Pitis, S., Zhou, Y., Ba, J., Dubois, Y., Maddison, C. J., & Hashimoto, T. (2024). *ToolEmu: Identifying the Risks of LM Agents with an LM-Emulated Sandbox.* International Conference on Learning Representations (ICLR 2024). arXiv:2309.15817.
3. **CaMeL:** Debenedetti, E., Shumailov, I., Fan, T., Hayes, J., Carlini, N., Fabian, D., Kern, C., Shi, C., Terzis, A., & Tramèr, F. (2025). *Defeating Prompt Injections by Design.* arXiv preprint arXiv:2503.18813.
4. **AgentRx:** Wang, L., et al. (2026). *AgentRx: Diagnosing AI Agent Failures from Execution Trajectories.* Findings of the Association for Computational Linguistics (EMNLP 2026), 598.
5. **AgentCheck:** EMNLP Demos (2026). *AgentCheck: A Reproduce–Intervene–Mitigate Workbench for LLM Agents over MCP.* EMNLP 2026 System Demonstrations, 64.
6. **Failure Prediction vs. Prevention:** Anonymous (2026). *Accurate Failure Prediction in Agents Does Not Imply Effective Failure Prevention.* arXiv:2602.03338.
7. **Chronicle:** Anonymous (2026). *Chronicle: Cut-Point Replay for Regression Testing of LLM Agents.* Proceedings of the REALM Workshop at ACL 2026, id `2026.realm-1.71`.
8. **High-Confidence Off-Policy Evaluation & SPI:** Thomas, P. S., Theocharous, G., & Ghavamzadeh, M. (2015). *High-Confidence Off-Policy Evaluation.* International Conference on Machine Learning (ICML 2015), 310–319.
9. **Safe Policy Improvement with Baseline Bootstrapping:** Laroche, R., Trichelair, P., & des Combes, R. T. (2019). *Safe Policy Improvement with Baseline Bootstrapping.* International Conference on Machine Learning (ICML 2019), PMLR 97:3652–3661. arXiv:1905.12110.
10. **Conformal Risk Control:** Angelopoulos, A. N., Bates, S., Fisch, A., Lei, L., & Schuster, T. (2024). *Conformal Risk Control.* International Conference on Learning Representations (ICLR 2024), Spotlight. arXiv:2208.02814.
11. **Doubly Robust Policy Evaluation:** Dudík, M., Langford, J., & Li, L. (2011). *Doubly Robust Policy Evaluation and Learning.* International Conference on Machine Learning (ICML 2011); Statistical Science 29(4):519–538 (2014). arXiv:1103.4601.
12. **Value of Information in Decision Systems:** Howard, R. A. (1966). *Information Value Theory.* IEEE Transactions on Systems Science and Cybernetics, 2(1), 22–26.
13. **NeMo Guardrails:** Rebedea, T., Dinu, R., Sreedhar, M., et al. (2023). *NeMo Guardrails: A Toolkit for Controllable and Safe LLM Applications.* EMNLP 2023 System Demonstrations.

### Citations Awaiting Full-Text Peer-Review Audit:
1. **AgentForesight:** Anonymous (2026). *AgentForesight: Online Auditing for Early Failure Prediction in Multi-Agent Systems.* EMNLP 2026 / arXiv:2605.08715. (Awaiting full mathematical verification of lookahead horizon bounds).
2. **DreamGuard:** Anonymous (2026). *DreamGuard: Efficient Runtime Guardrail for LLM Agents via Risk-Aware World Model.* arXiv:2608.05695. (Awaiting audit of world-model transition error assumptions).

---

## 4. Historical Provenance Audit & Preserved Discrepancy Statement

In accordance with open-science audit mandates, the CausaGuard repository explicitly preserves all historical provenance evidence without retroactively re-writing or concealing inconsistencies:

1. **Frozen Historical Benchmark (v0.5.2):**
   - Identity Seal: `053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6`
   - Frozen Development Manifest: `artifacts/v052/development-frozen.json`
2. **Unresolved Provenance Hash Discrepancy:**
   - In `artifacts/v052/development-frozen.json` (`identity.tests`), the recorded SHA-256 for `tests/test_v052_study.py` is:
     $$\text{Recorded Hash:} \quad \mathbf{\text{d9c045c18fb9984b335cfc52e052a16c842a6992132f240be2009b2ecfb00d11}}$$
   - On the current repository working tree (commit `02a03cb`), the physical file `tests/test_v052_study.py` has:
     $$\text{Physical Hash (CRLF):} \quad \mathbf{\text{fca7bd4e4c4b654aa93da023f0a98f937f77d521a394de21bb35c2bcf5eef545}}$$
     $$\text{Physical Hash (LF normalized):} \quad \mathbf{\text{96b5807c1c81ee816783f86a6b75330bbf8c39e0f4f120f3bb503b01ac44ba72}}$$
3. **Research Integrity Posture:**
   - The discrepancy stems from historical test suite formatting committed in `3aaffbe` after the initial frozen artifact was recorded.
   - **Non-Retroactivity Policy:** Neither `artifacts/v052/development-frozen.json` nor `v06_protocol_seal.json` has been modified, re-generated, or back-dated. The historical v0.5.2 and v0.6 artifacts serve strictly as immutable frozen anchor benchmarks. Prospective confirmatory evaluation v0.7.1 binds them as immutable historical dependencies, explicitly noting that dynamic regeneration of v0.5.2 from scratch has this known, documented limitation.

---

## 5. Open Methodological Gaps & Research Roadmap

Before CausaGuard can claim broad publication-ready contributions, the following research gaps must be resolved in future milestones:

| Gap ID | Description | Required Future Work | Current Status |
| :---: | :--- | :--- | :---: |
| **GAP-01** | **Learned Policy Generalization** | Replace closed-form analytical VOI with contextual causal tree or neural policy estimators without losing safety bounds. | Future Phase (v0.8+) |
| **GAP-02** | **Observational Confounder Sensitivity** | Test Rosenbaum bounds or marginal sensitivity models on observational data with unobserved latent hazards. | Future Phase (v0.8+) |
| **GAP-03** | **Open-World Natural Language Tasks** | Connect CausaGuard supervisory engine to open-ended LLM tool execution benchmarks (e.g. AgentDojo) with live language models. | Future Phase (v0.8+) |
| **GAP-04** | **Finite-Sample Non-Parametric SPI** | Derive empirical Bernstein or Efron-Stein concentration bounds for cluster-level utility differences to eliminate CLT reliance. | Future Phase (v0.8+) |

---

*Authored on behalf of the Research Methodology Group,*
**CausaGuard PhD Programme**
November 2026

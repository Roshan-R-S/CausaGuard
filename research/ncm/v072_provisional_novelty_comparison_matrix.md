# CausaGuard — Provisional Novelty Comparison Matrix (NCM) for Paper P1
**Document ID:** `NCM-P1-V072-PROVISIONAL`  
**Status:** **PROVISIONAL WORKING SYNTHESIS (PRE-FREEZE NO-GO)**  
**Evidence Foundation:** 70 Unabridged Primary Research Articles Extracted Across Pilot Batches 1–8  
**Independent Review Gate:** Human consensus verification pending; all AI-extracted claims are treated as provisional hypotheses subject to peer scrutiny and direct experimental replication.  

---

## 1. Executive Summary & Epistemic Scope

This document synthesizes empirical and theoretical evidence extracted from the **70 locally retrieved and verified research papers** (Batches 1–8) into a multi-dimensional Novelty Comparison Matrix (NCM). It establishes a structured preliminary mapping between prior art and CausaGuard's candidate research questions for **Paper P1 (Systematic Review & Gap Analysis)**.

### Epistemic Rules for Working Claims
In strict accordance with Section 15 of `CausaGuard_PhD_Research_Master_Roadmap_2026.pdf` and supervisor guidance:
1. **No Automated Claim Validation:** Theoretical novelty, runtime latency trade-offs, and causal bounds cannot be established merely because an automated AI reviewer extracted them from published texts.
2. **Context-Dependent Metrics:** Reported latency and throughput metrics (e.g. guardrail latency in NeMo or Colang) derive from distinct author hardware configurations, synthetic prompts, and differing API topologies; they provide qualitative motivation, not standardized head-to-head empirical proof.
3. **Rigorous Classification Hierarchy:**
   - **`[ESTABLISHED BASELINE — NO NOVELTY CLAIMED]`:** Solved in prior literature; CausaGuard incorporates as foundational prior art or baseline.
   - **`[PROVISIONAL HYPOTHESIS — PENDING VERIFICATION]`:** Identified in literature as a promising architectural direction or trade-off, but lacking standardized multi-domain benchmarking.
   - **`[PROVISIONAL METHODOLOGICAL CANDIDATE — PENDING PEER COMPARISON]`:** Candidate formulation proposed in CausaGuard that requires confirmatory proof and direct baseline comparison before acceptance.
   - **`[UNCONFIRMED / PENDING CONFIRMATORY EXPERIMENTS]`:** Claims requiring empirical multi-domain execution (Phases 3 & 4) that remain unproven during Phase 1.

---

## 2. Seven-Paradigm Comparative Evidence Matrix (Provisional)

| Structural Dimension | Paradigm 1: Surface Guardrails (Llama Guard, NeMo) | Paradigm 2: Attack Benchmarks (InjecAgent, AgentDojo) | Paradigm 3: Causal Bandits & OPE (Bareinboim, Dudík, Ortega, Xu) | Paradigm 4: Risk-Averse Sequential (Sun, Farsang, Ayala-Romero) | Paradigm 5: Multi-Agent & Tool Verification (ToolLLM, RSure-Agent, AgentGrad) | Paradigm 6: Human Deferral & Causal Workflows (Bondi, Chou oci-agent) | **CausaGuard Candidate Model (WP1–WP7 Remediated Design)** |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Primary Focus & Operational Locus** | Text token classification at input/output dialogue boundaries (`CG-ANC-08`, `CG-ANC-09`). | Empirical evaluation of prompt injection vulnerability (`CG-ANC-04`, `CG-ANC-05`, `CG-REC-056`). | Mathematical policy evaluation under unobserved confounding (`CG-ANC-02`, `CG-ANC-03`, `CG-REC-044`, `CG-REC-078`). | Bounding tail losses and constraint satisfaction in sequential decisions (`CG-REC-024`, `CG-REC-025`, `CG-REC-030`). | Tool call observation verification and DAG credit assignment (`CG-ANC-06`, `CG-REC-017`, `CG-REC-020`). | Modeling human cognitive error and automating causal pipelines (`CG-REC-047`, `CG-REC-072`). | **Hypothesized intervention boundary intercepting tool execution requests before environment mutation.** |
| **Threat Model & Assumptions** | Adversarial text prompts; assumes safety maps to natural language semantic categories. | Indirect prompt injection embedded in external data; black-box LLM access. | Latent confounders affect arm choice; positivity / overlap assumed unless IV used. | Adversarial cost vectors or non-linear tail distributions (CVaR); Slater condition. | Successful HTTP/API call $\ne$ correct observation; uncalibrated agent debate. | Human error rates change when presented with AI advice; cognitive fatigue. | **Imperfect, fallible runtime verifier with latency delay; adversarial prompt injections; unobserved environment confounding.** |
| **Observation Space & Latency Models** | Evaluates generated text tokens; authors report 0.5–2.0s latency per turn in specific testbeds (`CG-ANC-09`). | Multi-turn conversational text traces with tool output strings (`CG-ANC-07`). | Historical logged tuple $(x, a, r, p)$ with propensity scores; offline batch. | Feature vectors $x \in \mathcal{X}$; online convex programming or neural embeddings. | Tool execution outputs, intermediate reasoning traces, and agent communication graphs. | User interaction sequences and diagnostic balance metrics (SMD < 0.1). | **14 operational covariates ($X$) + fallible verifier evidence ($E$) with parameterized latency SLA penalties.** |
| **Action & Intervention Space** | Binary {Allow, Block} or text paraphrasing (`CG-REC-056`). | Autonomous tool selection until model emits terminal stop token. | Arm selection $a \in \mathcal{A}$; evaluates counterfactual payoff $Y(a)$. | Primal-dual continuous control projections or discrete arm pulls. | Backtracking in decision trees (DFSDT) or prompt refinement. | Binary {Predict, Defer to Human} or generating statistical code. | **Candidate two-stage intervention: Step 1 {Pass, Intercept/Verify, Block}; Step 2 {Execute, Fallback, Escalate}.** |
| **Authorization Boundary Model** | Heuristic: secondary LLM prompt check; non-enforceable against jailbreaks. | Evaluates whether malicious tool executed; no formal reference monitor. | Not modeled (pure statistical optimization). | Operational safety constraints bounding cumulative risk $\sum r_t \le \alpha$. | Tool reliability priors and observation verification protocols. | Procedural gate: requires diagnostic validation sign-off before reporting. | **Reference monitor (`MockState`); zero-bypass security invariant enforced separately from ML policy.** |
| **Failure Mode Addressed** | Conversational toxicity and topical drift; blind to API parameter mutations. | Discloses high attack success rate (ASR 24–80%); demonstrates static defenses fail. | Proves standard RL develops superstitious policies under latent confounding (`CG-REC-044`). | Prevents catastrophic tail failures that empirical risk minimization ignores (`CG-REC-025`). | Prevents compounding failure loops caused by incorrect tool observations (22.7% error rate). | Eliminates team performance degradation caused by human over-reliance (41% drop). | **Targeted failure mode: balancing security constraint enforcement against clean task disruption.** |

---

## 3. Four Core Methodological Gaps Demarcated by the SLR Evidence

Synthesizing evidence across the 70 extracted full texts confirms the relevance of the four open research gaps defined in `LIT-REV-CG-071-01`:

```
=============================================================================================================================
                                  PROVISIONAL METHODOLOGICAL GAP DEMARCATION
=============================================================================================================================
GAP ID   GAP TITLE                      EXTRACTED LITERATURE EVIDENCE                                 CAUSAGUARD PROPOSED FOCUS
-----------------------------------------------------------------------------------------------------------------------------
GAP-01   Imperfect Verification &       • Static guardrails (Llama Guard, NeMo) add latency overhead  Investigate the theoretical
         Disruption-Recovery Trade-off    and degrade clean task utility under heavy filtering.       and empirical trade-off:
                                        • RSure-Agent (CG-REC-017) proves 22.7% of successful tool    derive optimal stopping and
                                          calls return corrupted observations.                        fallback rules under fallible,
                                        • Tau-bench (CG-ANC-07) proves reliability collapses          noisy, and delayed verification
                                          (<25% Pass^5) over multi-turn horizons.                     channels (WP1, WP4, WP7).

GAP-02   Confounded Interventions &     • Bareinboim (CG-ANC-02) and Ortega (CG-REC-044) prove        Formulate Doubly Robust and
         Counterfactual Safety Bounds     observational P(y|x) and interventional P(y|do(x)) diverge. Instrumental Variable estimators
                                        • Standard OPE severely overestimates policy return under     (Xu 2022) for evaluating agent
                                          unobserved confounding (Xu 2022, CG-REC-078).               intervention policies over logged
                                        • Sun (CG-REC-024) and Farsang (CG-REC-025) provide formal    execution traces under latent
                                          primal-dual CVaR bounds for constrained bandits.            confounding (WP2, WP3, WP5).

GAP-03   Reference Monitor vs.          • Prompt defenses fail against adaptive attacks (ASR 24–47%,  Decouple statistical intervention
         Capability Decoupling            CG-ANC-05; AgentDojo, CG-ANC-04).                           learning from hard authorization:
                                        • Capability gates alone fail to prevent confused deputy      immutable reference monitor
                                          exploits (CG-REC-003).                                      guarantees zero bypass while learning
                                        • Emerging 2026 works (AgentSpec, DelAct, MCP-Secure)         optimizes economic utility
                                          confirm the shift to execution-boundary monitoring.         (WP1, WP6, WP7).

GAP-04   Cognitive Deferral &           • Naive learning-to-defer degrades team performance by 14%    Integrate joint cognitive-operational
         Selective Human Escalation       due to human over-reliance and fatigue (Bondi, CG-REC-072). loss modeling into the escalation
                                        • Proactive behavioral prediction using SLMs reduces          engine, accounting for human
                                          recovery latency by 58% (Adeseye, CG-REC-038).              cognitive cost and latency
                                        • Escalation without causal understanding creates failover    penalties in high-stakes domains
                                          storms (CG-REC-067).                                        (WP6, WP7).
=============================================================================================================================
```

---

## 4. Provisional Epistemic Status of Candidate Claims for Paper P1

1. **Claim C1 (Agent Intervention Paradox Formulation):**  
   - *Epistemic Status:* **[PROVISIONAL HYPOTHESIS — PENDING VERIFICATION]**.  
   - *Rationale:* Extracted literature (InjecAgent `CG-ANC-05`, WAInjectBench `CG-REC-060`, Liu et al. `CG-REC-056`) indicates that aggressive static defenses degrade clean task utility. However, the precise mathematical formalization of this disruption–recovery frontier is a hypothesis of CausaGuard that requires rigorous comparative validation against baseline policies.
2. **Claim C2 (Causal Doubly Robust Intervention Learning):**  
   - *Epistemic Status:* **[PROVISIONAL METHODOLOGICAL CANDIDATE — PENDING PEER COMPARISON]**.  
   - *Rationale:* Adapting Doubly Robust estimation (Dudík `CG-ANC-03`) and IV bounds (Xu `CG-REC-078`) to tool-calling traces is theoretically sound, but whether it demonstrates statistically significant utility gains over simpler regression or IPS baselines remains an open empirical question for Paper P3.
3. **Claim C3 (Algorithmic Novelty of Sequential Verification):**  
   - *Epistemic Status:* **[ESTABLISHED BASELINE — NO NOVELTY CLAIMED]**.  
   - *Rationale:* Formally recognized as an application of classical Bayesian Value of Information (Howard 1966) and POMDP planning. CausaGuard claims empirical benchmark characterization under imperfect verification, not algorithmic novelty in decision theory.
4. **Claim C4 (Cross-Domain Generalization):**  
   - *Epistemic Status:* **[UNCONFIRMED / PENDING CONFIRMATORY EXPERIMENTS]**.  
   - *Rationale:* Implemented across two pilot domains (Customer Support, Data Engineering). Claims of six-domain generalizability remain strictly unconfirmed until Phases 3 and 4 are executed following protocol unfreezing.

---
*Authored on behalf of the Foundations & Research Methodology Group,*  
**CausaGuard PhD Research Programme**  
November 2026

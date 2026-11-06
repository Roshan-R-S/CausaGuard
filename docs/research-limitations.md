# CausaGuard v0.7.1-alpha.1: Research Limitations & Scope Boundaries

**Status:** Official Methodological Disclosure  
**Release:** CausaGuard v0.7.1-alpha.1 (Research Alpha)  
**Date:** 7 November 2026  
**Audience:** Research Scientists, Systems Engineers, and Peer Reviewers  

---

## 1. Executive Disclosure

CausaGuard is an offline, local-first counterfactual intervention policy research laboratory. It is designed to study the mathematical and economic conditions under which active diagnostic verification and Bayesian Value of Information (VOI) decision-making outperform direct recovery, universal human escalation, and deterministic heuristics.

**CausaGuard v0.7.1-alpha.1 is a developer research alpha. It is NOT production software, a safety certifier, or a regulatory-approved autonomous system.**

To preserve open-science integrity and prevent premature generalization, this document explicitly articulates the boundaries, simplifications, and constraints of the current implementation.

---

## 2. Core Methodological Limitations

### 2.1 Synthetic Simulation Analogues vs Real-World Infrastructure
1. **Mathematical Stylization:** The environments (`domain_de` and `domain_cs`) are stylized, synthetic Partially Observable Markov Decision Processes (POMDPs). While calibrated against empirical operational distributions (schema drift rates, ticket dispute frequencies, network error rates), they do **not** execute live database queries, physical microservices, or production ticketing queues.
2. **Exogenous Random Tapes:** The counterfactual potential-outcomes framework relies on pseudo-random tapes to evaluate policies on identical latent defects. In live production environments, actions alter subsequent exogenous arrivals and system states dynamically.
3. **Absence of Real-World Confounders:** The synthetic environments model known, parameterized causal graphs. They do not simulate unobserved high-dimensional confounding, distributed clock skew, or hardware-level race conditions.

### 2.2 Analytical Closed-Form POMDP vs Real-World Machine Learning
1. **Non-Learned Decision Engine:** The candidate policy `CostRulePolicyV07_1` is an **analytical, closed-form decision engine**. It evaluates exact Bayesian expectations by propagating prior beliefs through a known causal POMDP graph. It does **not** employ deep reinforcement learning, neural networks, or prompt-engineered Large Language Models (LLMs).
2. **Prior Knowledge Requirement:** The analytical policy assumes structural knowledge of the causal graph and prior hazard rates ($F_s, F_c$). In real-world enterprise deployments, these priors must be estimated from historical observational data, introducing estimation variance and potential prior miscalibration.
3. **No Automatic Structure Learning:** CausaGuard does not perform causal structure discovery from raw unstructured logs; the causal DAG is prespecified by domain physics.

### 2.3 Confirmatory Status: Pre-Freeze Execution Lock
1. **Confirmatory Data Unobserved:** No confirmatory development seeds (`70100001–70110128`, $K=128$) or final seeds (`70200001+`) have been executed, previewed, or generated.
2. **Exploratory Findings Are Hypothesis-Generating:** The reported gains from exploratory calibration ($K=16$, seeds `70002001–70002016`) represent exploratory calibration evidence used to size the prospective study ($K=128$, power $\ge 92.52\%$). They **must not** be cited as confirmed empirical superiority.
3. **Mandatory Execution Lock:** The confirmatory runner [`experiments_v07_1/evaluate_confirmatory_v07_1.py`](file:///d:/causaguard/experiments_v07_1/evaluate_confirmatory_v07_1.py) is intentionally locked to prevent unsealed data access.

### 2.4 Human Escalation Queue Dynamics
1. **Finite Capacity & Linear Delay:** The human escalation model ([`causaguard_v07_1/escalation.py`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/escalation.py)) simulates human review queues using finite capacity bounds ($M=150$), linear wait delays, and human error probabilities.
2. **Omitted Human Factors:** The model does not capture circadian fatigue, multi-tier escalation triage, cognitive load variations, or shift handoffs.

---

## 3. Strict Non-Claims & Safety Demarcation

In accordance with responsible AI distribution standards:

| Dimension | What CausaGuard v0.7.1 IS | What CausaGuard v0.7.1 IS NOT |
| :--- | :--- | :--- |
| **Safety Certification** | A benchmark for quantifying operational risk ($R \le 0.050$) in simulation. | **NOT** a certified safety wrapper or formal verification tool. |
| **Real-World Robustness** | A study of fallible sensor verification under noise. | **NOT** an adversarial defense against LLM prompt injection or jailbreaks. |
| **Statistical Claims** | A prospectively sized research design ($K=128$). | **NOT** a claim of established real-world statistical superiority. |
| **Production Readiness** | A clean, extensible scientific testbed for researchers. | **NOT** a production middleware service or enterprise plugin. |

---

## 4. Responsible Distribution & Future Work

Future milestones (v0.8+) will address:
1. **Prior Sensitivity Analysis:** Evaluating performance when analytical priors deviate from true environment hazard frequencies.
2. **Online Empirical Estimation:** Coupling Bayesian VOI controllers with streaming Bayesian parameter estimation.
3. **Live Sandbox Evaluation:** Deploying the controller within non-production cloud sandboxes to validate analytical predictions against physical execution latencies and real database transactions.


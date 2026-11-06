# CausaGuard

[![Release](https://img.shields.io/badge/release-v0.7.1--alpha.1-blue.svg)](https://github.com/causaguard/causaguard)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-128%20passed-success.svg)](pytest_v07_1.ini)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**CausaGuard** is an offline, local-first counterfactual intervention policy research laboratory for autonomous software agents and automated execution workflows.

It studies a fundamental question in decision-theoretic autonomy:  
> **When an automated agent faces potential operational hazards, when does active diagnostic verification earn its complexity, cost, and latency compared to immediate direct recovery, universal human escalation, or deterministic threshold heuristics?**

```
========================================================================================
                                CAUSAGUARD v0.7.1-alpha.1
========================================================================================
  STATUS: Public Research Alpha Release (Fully Functional Offline Simulation Testbed)
  CONFIRMATORY EVALUATION STATUS: Cryptographically Locked (Pre-Freeze Protocol)
  SAFETY STATUS: Research Prototype (Zero Real-World Certification Claimed)
========================================================================================
```

---

## 1. Core Problem & Methodological Framework

In enterprise automated systems (e.g., ETL pipelines, automated customer ticket triage, code migration agents), execution hazards (such as schema drift, silent corruption, or authorization disputes) can disrupt operations. When a potential hazard is suspected:
1. **Blindly Proceeding** risks severe, unobservable catastrophic failures ($R > 0.050$).
2. **Direct Automated Recovery** (e.g., restoring from checkpoint, retrying requests) incurs immediate disruption costs and haircuts when the system was actually healthy.
3. **Universal Human Escalation** overwhelms finite human review capacity, creating cascading queue delays, drop penalties, and expensive labor costs.
4. **Diagnostic Verification** (e.g., running integrity checks, schema validation) provides informative evidence, but incurs its own cost, latency, and fallible error rates (false positives and false negatives).

CausaGuard models these trade-offs as a **Partially Observable Markov Decision Process (POMDP)** with finite human queue bandwidth and evaluates decision policies under a **paired counterfactual potential-outcomes framework**.

---

## 2. The Analytical Bayesian VOI Controller

Unlike black-box deep reinforcement learning or prompt-engineered LLM wrappers, the candidate policy in v0.7.1 ([`CostRulePolicyV07_1`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/policy_v07_1.py#L274)) is an **analytical, closed-form, non-learned decision engine**:
- **Belief Updating:** Propagates observed noisy features through exact Bayesian conditioning on known causal graphical structures.
- **Value of Information (VOI):** Closed-form expected utility calculation balancing:
  $$EU(\text{proceed}) \quad \text{vs.} \quad EU(\text{repair}) \quad \text{vs.} \quad EU(\text{escalate}) \quad \text{vs.} \quad EU(\text{verify})$$
- **Information-Theoretic Value:** It triggers active verification **only** when the expected reduction in decision loss strictly exceeds the diagnostic verification fee and computational latency.
- **Zero Hallucination / Training Instability:** Being purely analytical and closed-form, the policy is completely immune to training instability, reward hacking, or distribution shifts.

---

## 3. Supported Synthetic Domains

CausaGuard v0.7.1 provides two calibrated operational POMDP domains:

### 3.1 Data Engineering Batch Supervision (`de`) — Primary Confirmatory Domain
- **Operational Reality:** Supervised batch pipeline management where upstream database migrations cause silent schema drift and content corruption.
- **Economic Characteristics:** Checkpoint restoration imposes a heavy haircut ($v_{\text{fallback}} = 0.45 \times V$). Human escalation incurs significant labor fees ($\$2.50$) and bandwidth delays.
- **Role:** High positive Value of Information; diagnostic verification prevents catastrophic recovery haircuts on healthy pipelines.

### 3.2 Customer Support Ticket Triage (`cs`) — Secondary Boundary Domain
- **Operational Reality:** High-volume user ticket triage with conflicting state and source reliability alarms.
- **Economic Characteristics:** Customer retry cost is negligible ($\$0.05$), while human review is expensive ($\$1.20$).
- **Role:** Serves as an operational boundary condition where cheap direct recovery dominates, illustrating the domain limits of Bayesian VOI.

---

## 4. The 8-Policy Benchmark Suite

All policies operate under **symmetric action and observation access** (including Step-1 escalation access):

| Policy Name | Category | Decision Logic |
| :--- | :--- | :--- |
| [`cost_rule_v07_1`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/policy_v07_1.py#L274) | **Candidate** | Analytical Bayesian POMDP Value of Information controller. |
| [`always_recovery`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/policy_v07_1.py#L32) | Baseline | Blindly executes recovery action immediately at Step 1. |
| [`always_escalate`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/policy_v07_1.py#L46) | Baseline | Delegates 100% of cases immediately to human review queue. |
| [`cost_sensitive_symmetric_heuristic`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/policy_v07_1.py#L140) | Baseline | Calibrated threshold heuristic with symmetric Step-1 escalation access. |
| [`escalation_aware_deterministic_threshold`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/policy_v07_1.py#L98) | Baseline | Deterministic thresholding factoring in queue wait and repair costs. |
| [`fixed_verify_repair_macro`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/policy_v07_1.py#L60) | Baseline | Static workflow: always verifies, repairs if alarm triggers. |
| [`budget_aware_direct_recovery`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/policy_v07_1.py#L76) | Baseline | Attempts direct recovery only if budget permits. |
| [`oracle`](file:///d:/causaguard/src_v07_1/causaguard_v07_1/policy_v07_1.py#L226) | Upper Bound | Theoretical hindsight benchmark observing true latent ground truth. |

---

## 5. Quickstart & Installation

CausaGuard is local-first, requires no GPU or network access, and runs completely offline.

### 5.1 Installation
```bash
# Clone the repository
git clone https://github.com/causaguard/causaguard.git
cd causaguard

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # On Linux/macOS
# .venv\Scripts\Activate.ps1    # On Windows PowerShell

# Install dependencies
pip install numpy scipy pydantic pytest ruff
```

### 5.2 Execute the Interactive Demo
Run the safe, standalone demonstration on non-evaluative reserve seeds:
```bash
python demo_v07_1.py
```
*(See [`docs/quickstart.md`](docs/quickstart.md) for full CLI flags and walkthrough options.)*

### 5.3 Run the Test Suite
```bash
# Run isolated v0.7.1 unit and invariant tests (59 tests)
pytest -c pytest_v07_1.ini -v

# Run complete historical test suites (v0.6 and v0.7)
pytest -c pytest_v07.ini -v
pytest -c pytest_v06.ini -v
```

---

## 6. Pre-Freeze Confirmatory Execution Lock

CausaGuard adheres strictly to open-science and clinical preregistration methodology (FDA CDER Statistical Principles, Center for Open Science Preregistration Standards):

- **Prospective Confirmatory Allocation:** $K = 128$ clusters per domain, $N = 400$ cases per cluster ($51{,}200$ cases per domain).
- **Statistical Power:** Fréchet-Bonferroni lower bound guarantees joint study success probability $\ge \mathbf{92.52\%}$ under conservative variance.
- **Execution Lock:** The confirmatory runner [`experiments_v07_1/evaluate_confirmatory_v07_1.py`](file:///d:/causaguard/experiments_v07_1/evaluate_confirmatory_v07_1.py) contains a hardcoded pre-freeze cryptographic lock. It strictly refuses to execute actual confirmatory development seeds (`70100001+`) or final seeds (`70200001+`) until the prospective protocol is formally sealed and signed by independent gate authorization.
- Attempting to run confirmatory seeds today will safely exit with:
  `LOCKED: EXECUTION LOCK: Confirmatory evaluation blocked. No valid protocol seal file found...`

---

## 7. Research Maturity, Non-Claims & Limitations

> [!WARNING]
> ### RESEARCH ALPHA DISCLOSURE
> CausaGuard v0.7.1-alpha.1 is an **algorithmic research laboratory**, not production-grade safety infrastructure.
> 
> - **Synthetic Environments:** Simulations are stylized mathematical POMDP analogues, not live cloud environments or physical queues.
> - **Zero Production Safety Certification:** CausaGuard makes **no claim** of certified real-world safety, regulatory approval, or robustness against adversarial prompt injections.
> - **Hypothesis-Generating Evidence:** Reported exploratory gains ($K=16$) are hypothesis-generating; confirmatory evaluation remains locked pending formal protocol freeze.
> 
> See [`docs/research-limitations.md`](docs/research-limitations.md) for full scope boundaries and scientific disclosures.

---

## 8. Repository Structure

```
causaguard/
├── src_v07_1/causaguard_v07_1/      # Isolated v0.7.1 core research engine
│   ├── domain_de.py                 # Data Engineering POMDP simulator
│   ├── domain_cs.py                 # Customer Support POMDP simulator
│   ├── escalation.py                # Multi-attribute human escalation model
│   ├── policy_v07_1.py              # Analytical Bayesian VOI & benchmark policies
│   └── study_v07_1.py               # Counterfactual paired evaluation runner
├── experiments_v07_1/               # Confirmatory evaluation runner & protocol draft
│   ├── evaluate_confirmatory_v07_1.py  # Locked confirmatory runner
│   ├── run_exploratory_v07_1.py     # Exploratory variance runner (K=16)
│   └── v071_confirmatory_protocol_draft.json  # Prospective protocol draft
├── tests_v07_1/                     # Isolated v0.7.1 test suite (59 tests)
├── demo_v07_1.py                    # Standalone interactive research demo
├── docs/                            # Architectural & methodological documentation
│   ├── quickstart.md                # Quickstart and developer guide
│   ├── research-limitations.md      # Detailed scientific limitations & non-claims
│   ├── v071-architecture.md         # Engine architecture & mathematical POMDP specification
│   └── v071-confirmatory-runner-engineering-report.md
├── research/methodology/            # Formal protocols, audits, and statistical derivations
├── CHANGELOG.md                     # Release history and milestone logs
├── LICENSE                          # MIT License
└── pyproject.toml                   # Root package configuration (cryptographically sealed)
```

---

## 9. Historical Preservation & Research Continuity

CausaGuard maintains a continuous chain of cryptographically sealed historical milestones:
- **v0.5.2:** Factorial study closeout & historical freeze (`artifacts/v052/development-frozen.json`, SHA-256 `053dea36...`).
- **v0.6.0:** Master protocol freeze (`c0f217ca...`) & Amendment 01 development evaluation (`a5cb7ab9...`).
- **v0.7.0:** Initial Bayesian VOI exploratory calibration and adversarial scientific audit.
- **v0.7.1:** Isolated remediation engine with decomposed escalation and symmetric heuristic.

All historical files and cryptographic hashes are verified byte-for-byte by automated tests on every build.

---

## 10. License

CausaGuard is distributed under the [MIT License](LICENSE).
Copyright (c) 2026 CausaGuard Contributors.

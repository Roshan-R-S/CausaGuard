# CausaGuard v0.7.1-alpha.1: Quickstart Guide

Welcome to the CausaGuard research alpha release. This guide provides exact instructions for installing dependencies, running the interactive synthetic demonstration, executing the isolated test suites, and exploring the analytical decision engine.

---

## 1. Prerequisites

- **Python:** 3.11 or 3.12 (64-bit recommended).
- **Git:** Version 2.30+ with CRLF/LF support.
- **Hardware:** Standard CPU (runs fully offline, zero GPU or API keys required).

---

## 2. Environment Setup

### 2.1 Clone the Repository
```bash
git clone https://github.com/causaguard/causaguard.git
cd causaguard
```

### 2.2 Create and Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**On Linux / macOS (Bash):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2.3 Install Core Dependencies
Install the required scientific computation and verification packages:
```bash
pip install numpy scipy pydantic pytest ruff
```

*(Optional) Install root package in editable mode:*
```bash
pip install -e .
```

---

## 3. Running the Interactive Demonstration

CausaGuard includes a standalone, self-contained demonstration entry point: [`demo_v07_1.py`](file:///d:/causaguard/demo_v07_1.py). 

The demo runs completely offline on synthetic cases sampled from the **non-evaluative infrastructure reserve** (seeds `70003001+`). It does not touch or unlock any confirmatory evaluation seeds.

### 3.1 Run Full Demonstration (Both Domains)
```bash
python demo_v07_1.py
```

### 3.2 Run Specific Domain
Evaluate only Data Engineering (Primary Confirmatory Domain):
```bash
python demo_v07_1.py --domain de --n-cases 50
```

Evaluate only Customer Support (Secondary Boundary Domain):
```bash
python demo_v07_1.py --domain cs --n-cases 50
```

### 3.3 What the Demo Illustrates
1. **Single-Case Counterfactual Walkthrough:** Evaluates the exact same synthetic case across all 8 policies simultaneously, demonstrating how analytical Bayesian Value of Information (VOI) balances diagnostic verification fees against the risk of catastrophic unobservable execution failures.
2. **Aggregate Benchmark Table:** Displays paired potential outcomes across $N$ cases, comparing mean utility, operational risk ($R \le 0.050$), safe completion rate, economic costs, latency, and human escalation queue wait times.
3. **Domain Contrast:** Shows why VOI achieves superiority in Data Engineering (where recovery carries high fallback haircuts), while demonstrating that Customer Support serves as an operational boundary condition where cheap retries favor direct recovery.

---

## 4. Running the Test Suites

CausaGuard isolates research milestones across dedicated configuration profiles:

### 4.1 Run v0.7.1 Isolated Test Suite (59 tests)
```bash
pytest -c pytest_v07_1.ini -v
```
Tests the complete v0.7.1 engine, Bayesian VOI policy, multi-attribute human escalation simulator, symmetric heuristic baseline, confirmatory runner execution lock, numerical hand calculations, and historical cryptographic preservation.

### 4.2 Run Historical Test Suites
Verify byte-level historical preservation across prior milestones:
```bash
# v0.7 historical suite (35 tests)
pytest -c pytest_v07.ini -v

# v0.6 sealed protocol suite (34 tests)
pytest -c pytest_v06.ini -v
```

### 4.3 Run Linting & Code Quality
```bash
ruff check src_v07_1 tests_v07_1 experiments_v07_1
```

---

## 5. Python API Usage

You can use the isolated v0.7.1 Python API directly in your own scripts:

```python
import sys
from pathlib import Path

# Add isolated v0.7.1 engine to sys.path
sys.path.insert(0, "src_v07_1")

from causaguard_v07_1.domain_de import make_de_cases_v07_1
from causaguard_v07_1.policy_v07_1 import CostRulePolicyV07_1, AlwaysRecoveryPolicyV07_1
from causaguard_v07_1.study_v07_1 import run_episode_v07_1, evaluate_cluster_v07_1

# 1. Generate 10 synthetic Data Engineering cases on non-evaluative seed
cases = make_de_cases_v07_1(n=10, seed=70003101, profile="iid")

# 2. Evaluate a single episode under the analytical Bayesian VOI policy
policy = CostRulePolicyV07_1()
result = run_episode_v07_1(case=cases[0], policy=policy)

print(f"Step 1 Decision: {result['step1_action']}")
print(f"Step 2 Decision: {result['step2_action']}")
print(f"Net Operational Utility: {result['utility']:+.4f}")
print(f"Operational Cost: ${result['cost']:.3f}")
print(f"Latency: {result['latency']:.2f}s")
print(f"Safe Completion: {result['safe_completion']}")

# 3. Evaluate a cluster across all 8 benchmark policies with isolated queue states
cluster_results = evaluate_cluster_v07_1(cases=cases, capacity_limit=150)
print(cluster_results["policy_metrics"]["cost_rule_v07_1"]["mean_utility"])
```

---

## 6. Understanding the Confirmatory Execution Lock

If you inspect [`experiments_v07_1/evaluate_confirmatory_v07_1.py`](file:///d:/causaguard/experiments_v07_1/evaluate_confirmatory_v07_1.py), you will notice that attempting to run actual confirmatory seeds (`70100001+` or `70200001+`) is blocked:

```powershell
python experiments_v07_1/evaluate_confirmatory_v07_1.py --domain de
# Output:
# LOCKED: EXECUTION LOCK: Confirmatory evaluation blocked. No valid protocol seal file found...
```

**Why is it locked?**
In clinical trials and high-integrity causal research, confirmatory evaluation cannot commence until the prospective statistical protocol is cryptographically sealed and preregistered. This guarantees zero post-hoc data peaking, hyperparameter tuning, or retrospective hypothesis shifting (anti-HARKing). The execution lock cannot be bypassed by user CLI arguments.


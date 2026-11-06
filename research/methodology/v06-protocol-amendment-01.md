# CausaGuard v0.6: Protocol Amendment 01

Status: **OFFICIAL PROSPECTIVE PROTOCOL AMENDMENT**, CausaGuard PhD Research Programme, 4 November 2026.  
Scope: **Registration of Unexecuted Confirmatory Development Evaluation Runner (`evaluate_dev.py`)**  
Parent Protocol Version: `0.6.0-locked`  
Parent Protocol Seal: `c0f217cae474758b216f052c317e52732011d77d31e28f32106d3321447c4ac0`  
Historical Freeze Dependency: `053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6`

---

## 1. Rationale and Scope of Amendment

During the pre-execution audit of Package 4, it was established that while all mathematical hypotheses, margins ($\Delta_{\text{util}} = +0.015$), seed allocations ($K = 64$), and multiplicity rules were fully sealed in `v06_protocol.json`, a standalone CLI evaluation runner implementing the exact frozen development evaluation procedure was absent from the original 20-file manifest.

In accordance with Phase 1 instructions, execution was stopped before generating or accessing any development evaluation seeds. This append-only amendment prospectively registers:
1. The unexecuted development evaluation runner: [`experiments_v06/evaluate_dev.py`](../../experiments_v06/evaluate_dev.py)
2. Its dedicated invariant test suite: [`tests_v06/test_evaluate_dev.py`](../../tests_v06/test_evaluate_dev.py)

### Invariance Guarantees:
- **Zero Mathematical or Protocol Changes:** The superiority hurdle ($\Delta = +0.015$), planning target ($\delta^* = +0.035$), Bonferroni alpha ($\alpha = 0.00333$), operational risk limit ($0.050$), excess risk limit ($0.005$), zero-event Clopper-Pearson bound, and seed ranges remain 100% byte-identical to `v06_protocol.json`.
- **Zero Historical Contamination:** The historical v0.5.2 closeout and seal remain 100% byte-identical.
- **Zero Final Seed Access:** Reserved final seeds (`60030001–60040064`) remain strictly forbidden and untouched.
- **Prospective Integrity:** No development evaluation seeds (`60010001–60020064`) were simulated or evaluated prior to the signing of this amendment seal.

---

## 2. Added Artifacts & File Hashes

- `experiments_v06/evaluate_dev.py`
- `tests_v06/test_evaluate_dev.py`
- `experiments_v06/v06_protocol_amendment_01.json`

This amendment record cryptographically chains to parent seal `c0f217ca...` and is sealed into `experiments_v06/v06_amendment_01_seal.json`.

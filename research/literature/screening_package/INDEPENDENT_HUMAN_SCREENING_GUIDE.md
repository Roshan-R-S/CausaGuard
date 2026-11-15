# CausaGuard PhD Programme — Independent Human Reviewer Screening Package
**Review Phase:** SLR Phase 1.5B (Independent Dual Screening & Concordance Verification)  
**Governing Document:** `CausaGuard_PhD_Research_Master_Roadmap_2026.pdf` (Sections 3, 4, 5, 11, 15, 16)  
**Status:** **ACTIVE / PENDING SECONDARY HUMAN EVALUATION** (Zero synthetic human scores generated)  

---

## 1. Instructions for Independent Reviewer (Reviewer-2)

You have been provided with the screening package for **60 peer-reviewed candidate studies** harvested from Crossref DOI metadata registries covering IEEE Xplore, ACM Digital Library, and Springer Nature.

### Task:
1. Open the accompanying evaluation CSV: [`research/literature/records/independent_screening_package_phase1_5b.csv`](file:///d:/causaguard/research/literature/records/independent_screening_package_phase1_5b.csv).
2. For each study (rows 1–60), inspect the title, venue, authors, and canonical URL / DOI.
3. Apply the inclusion and exclusion criteria defined below.
4. Record your decision in column `Reviewer_2_Decision` using one of three valid codes:
   - `ADVANCE`: Candidate satisfies inclusion criteria; recommend for full-text retrieval and data extraction.
   - `UNCERTAIN`: Title/abstract ambiguous; recommend full-text retrieval for inspection.
   - `EXCLUDE`: Fails inclusion criteria or violates exclusion criteria.
5. Provide a brief rationale in `Reviewer_2_Rationale_Notes` (e.g. "EC1: Generic power grid optimization, unrelated to LLM tool security").
6. Save the CSV. Leave `Consensus_Decision` blank until the joint reconciliation meeting.

---

## 2. Eligibility & Quality Assessment Criteria

### Inclusion Criteria (IC):
- **IC1 (Autonomous / Tool-Using Agents):** Study investigates autonomous LLM agents, sequential decision-making systems, or multi-step tool execution pipelines.
- **IC2 (Runtime Security & Interception):** Study proposes runtime guardrails, reference monitors, capability-bound authorization, sandboxing, or action interception.
- **IC3 (Safe Policy Learning & Causal Evaluation):** Study evaluates contextual bandits with risk constraints, safe policy improvement (SPIBB), learning to defer, conformal prediction, or causal off-policy evaluation.
- **IC4 (Empirical or Formal Rigor):** Study presents quantifiable evaluation metrics, benchmarks (e.g. AgentDojo, tau-bench, ToolBench, OpenML), or formal safety proofs.

### Exclusion Criteria (EC):
- **EC1 (Out of Domain Scope):** Generic physical hardware control (e.g. servo motors, supply chain procurement auctions, social network marketing).
- **EC2 (Purely Opinion / Editorial):** High-level policy essays, non-technical commentary, or book front matter ("Introduction", "Epilogue").
- **EC3 (Duplicate Publication):** Redundant publication of identical results already present in the screening ledger.
- **EC4 (Non-Article Media):** Supplementary video files (`.mp4`), presentation slides, or corrupted metadata.

---

## 3. Inter-Rater Agreement & Concordance Protocol (Post-Review Execution)

Upon completion of Reviewer-2 independent screening:
1. **Concordance Rate:** Compute simple percent agreement:
   $$P_o = rac{\text{Agreed Decisions}}{\text{Total Evaluated Studies}}$$
2. **Cohen's Kappa ($\kappa$):** Compute chance-corrected inter-rater agreement:
   $$\kappa = \frac{P_o - P_e}{1 - P_e}$$
   where $P_e$ is the hypothetical probability of chance agreement.
3. **Threshold Gate:** $\kappa \ge 0.70$ is required for provisional acceptance. If $\kappa < 0.70$, hold a formal adjudication conference to resolve discrepancies.
4. **Current Status:**
   - *Reviewer-1 Decisions:* Completed (Provisional automated pass by Antigravity).
   - *Reviewer-2 Decisions:* **PENDING INDEPENDENT HUMAN ASSESSMENT**.
   - *Calculated Cohen's $\kappa$:* **N/A (Pending independent reviewer entries; no artificial scores generated)**.

---

## 4. Summary Table of Reviewer-1 Provisional Recommendations

| Database Prefix | Candidate Count | Reviewer-1 Advance | Reviewer-1 Uncertain | Reviewer-1 Exclude | Primary Research Themes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **IEEE Xplore (`10.1109`)** | 20 | 10 | 3 | 7 | Reference monitors, MCP security, behavioral sandboxes, capability authorization. |
| **ACM DL (`10.1145`)** | 20 (1 dup) | 17 | 1 | 2 | AgentSpec, RefineAct, formal verification on AgentDojo, runtime enforcement. |
| **Springer Nature (`10.1007`)** | 20 | 7 | 3 | 10 | Risk-averse contextual bandits, causal contrastive learning, dynamic programming. |
| **Total** | **60** | **34** | **7** | **19** | **41 candidates advanced to retrieval queue pending Reviewer-2**. |

---
*Authored on behalf of the Foundations & Research Methodology Group,*  
**CausaGuard PhD Programme**  
November 2026

# CausaGuard PhD Research Programme — Supervisor & Secondary Reviewer Instructions

**Document ID:** `SOP-SLR-PHASE1-5B`  
**Governing Document:** `CausaGuard_PhD_Research_Master_Roadmap_2026.pdf` (Sections 3, 4, 5, 11, 15, 16)  
**Target Milestone:** PRISMA 2020 Dual-Screening & Concordance Verification Gate  
**Status:** **ACTIVE / READY FOR INDEPENDENT HUMAN SCREENING**  
**Review Integrity Rule:** Zero synthetic reviewer decisions or artificial Cohen's $\kappa$ metrics may be generated. All Reviewer-2 entries must be independently assigned by a human researcher or supervisor.

---

## 1. Context & Purpose

The CausaGuard systematic literature review has completed its preliminary pilot phase (70 full texts retrieved and extracted, 7 access-restricted) and expanded its search coverage into peer-reviewed engineering indexing registries (IEEE Xplore, ACM Digital Library, and Springer Nature via CrossRef DOI registries).

To satisfy PRISMA 2020 Item 8 and academic peer-review standards for **Paper P1 (Systematic Review & Gap Analysis)**, an independent secondary researcher or supervisor must conduct blinded screening to confirm study eligibility and establish inter-rater reliability.

---

## 2. Review Packages Provided to Reviewer-2

Two clean, blinded CSV evaluation sheets with **blank Reviewer-2 fields** are provided:

### Primary Package: Expanded Broader Database Candidates (59 Unique Studies)
- **File Location:** [`research/literature/records/blinded_reviewer2_screening_package_phase1_5b.csv`](file:///d:/causaguard/research/literature/records/blinded_reviewer2_screening_package_phase1_5b.csv)
- **Population:** Exactly **59 unique records** obtained via Crossref-derived bibliographic harvesting matching IEEE ($n=20$), ACM ($n=19$, 1 duplicate removed), and Springer Nature ($n=20$) publisher queries. (Note: These represent Crossref metadata query records filtered by publisher rather than completed native publisher portal web dumps).
- **Blinding:** Reviewer-1 recommendations and justifications have been **completely excluded** to ensure fully independent human judgment.

### Audit Package: Pilot Corpus Stratified Sample (18 Studies)
- **File Location:** [`research/literature/records/pilot_audit_sample_reviewer2_package.csv`](file:///d:/causaguard/research/literature/records/pilot_audit_sample_reviewer2_package.csv)
- **Population:** Exactly **18 studies** (20.9% stratified random sample of the 86 pilot records: 3 roadmap anchors [`CG-ANC-01`, `CG-ANC-05`, `CG-ANC-08`], 10 advancing studies, 3 unresolved/uncertain studies, and 2 excluded studies).
- **Purpose:** Verifies the consistency and reliability of the initial pilot screening pass without requiring the supervisor to re-screen all 86 historical records.

---

## 3. Screening Instructions for Reviewer-2

1. Open [`blinded_reviewer2_screening_package_phase1_5b.csv`](file:///d:/causaguard/research/literature/records/blinded_reviewer2_screening_package_phase1_5b.csv).
2. For each study row, inspect the Title, Authors, Venue, DOI, and Abstract Summary (or click the Canonical URL).
3. Evaluate the study against the **Inclusion Criteria (IC)** and **Exclusion Criteria (EC)** detailed in Section 4 below.
4. Record your decision in column `Reviewer_2_Decision` using strictly one of three codes:
   - `ADVANCE`: Study meets IC criteria; recommend for full-text retrieval and data extraction.
   - `UNCERTAIN`: Title/abstract ambiguous; recommend full-text retrieval for inspection.
   - `EXCLUDE`: Fails IC criteria or meets any EC criteria.
5. In column `Reviewer_2_Rationale_Notes`, provide a brief reason (e.g., *"IC1/IC2: Proposes reference monitor for agent tool execution"* or *"EC1: Generic power grid optimization"*).
6. Repeat for [`pilot_audit_sample_reviewer2_package.csv`](file:///d:/causaguard/research/literature/records/pilot_audit_sample_reviewer2_package.csv).
7. Save the CSV files. **Do not fill the consensus fields**; consensus will be adjudicated jointly.

---

## 4. Formal Eligibility Criteria (Phase 1 Protocol)

### Inclusion Criteria (IC) — Must meet at least one:
- **IC1 (Tool-Using / Autonomous Agents):** Focuses on language model agents, tool-calling pipelines, or autonomous sequential decision systems executing actions in an external environment.
- **IC2 (Runtime Security & Interception):** Proposes or evaluates runtime guardrails, reference monitors, capability authorization, permission checks, execution sandboxing, or runtime verification.
- **IC3 (Risk-Aware Policy Improvement & Deferral):** Evaluates contextual bandits under risk constraints, safe policy improvement (SPIBB), learning to defer, conformal risk control, or causal off-policy evaluation.
- **IC4 (Empirical or Formal Rigor):** Presents reproducible quantitative metrics, benchmarks (e.g., AgentDojo, tau-bench, ToolBench, OpenML), or formal safety/correctness proofs.

### Exclusion Criteria (EC) — Exclude if any apply:
- **EC1 (Out of Domain Scope):** Generic physical systems without software agents (e.g. servo motors, HVAC controllers, supply chain contracts, physical-layer antennas).
- **EC2 (Purely Commentary / Editorial):** High-level policy essays, non-technical commentary, or book front matter ("Introduction", "Epilogue").
- **EC3 (Duplicate Publication):** Redundant duplicate of an already indexed study.
- **EC4 (Non-Article Media):** Supplementary video files (`.mp4`), presentation slides, or corrupted metadata.

---

## 5. Post-Review Concordance Protocol

Once Reviewer-2 completes and returns the two evaluation files:
1. **Unblinding & Comparison:** Reviewer-2 decisions will be merged with the preserved Reviewer-1 recommendations in [`independent_screening_package_phase1_5b.csv`](file:///d:/causaguard/research/literature/records/independent_screening_package_phase1_5b.csv).
2. **Statistical Agreement:** We will compute:
   - Percent Agreement ($P_o$)
   - Cohen's Kappa ($\kappa$):
     $$\kappa = \frac{P_o - P_e}{1 - P_e}$$
   - Benchmarks: $\kappa \ge 0.70$ constitutes substantial agreement; $\kappa \ge 0.80$ constitutes near-perfect agreement.
3. **Discrepancy Reconciliation:** Any conflicting decisions (e.g., `ADVANCE` vs. `EXCLUDE`) will be flagged for joint discussion and recorded in `Consensus_Decision` and `Discrepancy_Resolution_Notes`.
4. **Final PRISMA Inclusion:** Only consensus-approved studies will advance to full-text retrieval and eligibility synthesis.

---
*Authored on behalf of the Foundations & Research Methodology Group,*  
**CausaGuard PhD Research Programme**  
November 2026

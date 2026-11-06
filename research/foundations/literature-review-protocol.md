# Offline literature-review protocol

Status: **PROPOSED**, post-result research foundations, 4 November 2026. No web search, primary-paper retrieval or screening was performed. The roadmap and repository reference list were inspected as planning sources, not as primary scientific papers. Every candidate's identity, bibliographic metadata, method, result and claimed guarantee below remains **UNVERIFIED** until its primary text is inspected. No completed screening counts or novelty claim are supplied.

Source locators: roadmap PDF defined as R in [evidence-map.md](evidence-map.md), pp. 7-10 and 19; [research-plan.md](../../docs/research-plan.md), lines 148-158. The roadmap is an older planning document; its bibliography is not certification that a paper or URL is accurate. None of the links below was accessed.

## Review question and scope

**PROPOSED question:** Which existing methods choose whether to acquire fallible, delayed evidence and then act, recover or defer under operational costs and a separate mandatory authorization boundary? What benchmark or empirical gap, if any, remains for two independently specified mock workflows?

Separate three evidence strata: (A) decision theory, sequential information acquisition and safe policy comparison; (B) tool-use security/runtime enforcement; (C) task benchmarks and applied workflow evidence. A paper can belong to several strata, but a security benchmark is not automatically a utility comparator. The first comparison target is the strongest practical deterministic evidence-contingent decision rule, not a weak always-verify strawman.

## Reproducible search plan, not executed

At a later authorized search, lock a search date/cutoff and record each database's actual coverage. Proposed coverage: all years through that cutoff for foundational decision/causal work; 2022 through cutoff for modern LLM/tool-agent work, with earlier cited ancestors eligible. Include peer-reviewed papers and separately labeled preprints. English full-text screening is an explicit resource limitation, not a scientific quality rule; log potentially relevant non-English/unavailable papers as unresolved. Do not silently discard negative results.

| Search ID | Literal Boolean concept query |
| --- | --- |
| Q1 | ("value of information" OR "active sensing" OR "information gathering") AND (verification OR inspection OR diagnostic) AND (cost OR delay OR noisy OR fallible) |
| Q2 | (POMDP OR "partially observable" OR "sequential decision") AND (verification OR sensing OR recovery) AND (risk OR constraint OR cost) |
| Q3 | ("selective prediction" OR "learning to defer" OR abstention) AND (cost OR uncertainty OR "human oversight") |
| Q4 | ("safe policy improvement" OR "contextual bandit" OR "offline reinforcement learning") AND (baseline OR risk OR cost) |
| Q5 | ("off-policy evaluation" OR "doubly robust" OR "causal inference") AND (sequential OR intervention OR "logged policy") |
| Q6 | ("LLM agent" OR "autonomous agent") AND ("tool calling" OR "tool execution") AND (authorization OR capability OR "runtime enforcement") |
| Q7 | ("agent security" OR "prompt injection") AND (benchmark OR "adaptive attack" OR "cross-domain") |
| Q8 | ("record reconciliation" OR "customer support") AND (verification OR "data quality" OR recovery) |
| Q9 | ("data pipeline" OR "data transformation") AND (validation OR schema OR corruption OR staleness) AND (recovery OR checkpoint OR cost) |

Run Q1-Q9 in Scopus or Web of Science where available, and translate to title/abstract/keyword fields in IEEE Xplore, ACM Digital Library and SpringerLink. Run discovery searches in Semantic Scholar/Google Scholar and arXiv/OpenReview; use official proceedings/publisher/author-hosted texts for extraction. Record access failures and unavailable databases. A translated query is a separate logged query: store both the literal submitted syntax and its relationship to Q1-Q9. No result cap is allowed silently; if a platform caps results, split by non-overlapping year intervals and record the cap and residual coverage gap.

For every search record: query ID, exact syntax, database/interface version where available, field filters, date/time/timezone, cutoff, sort order, language/year filters, returned count, exported count, export format, export SHA-256, access restrictions and reviewer. Save original exports unchanged in a future review record directory. No exports or completed counts exist in this package.

Deduplicate by DOI, then persistent identifier/version, then normalized title plus authors and year. Preserve preprint/published version lineage; select the primary version for extraction without deleting linked versions or corrections. Run one documented backward and forward citation pass for each included closest-method paper, then a second pass on newly included papers; additional passes require a logged reason. Recheck the search before submission and label the update separately.

## Eligibility, screening and extraction

Include a primary methodological, theoretical, benchmark or empirical work if it specifies at least one relevant decision/enforcement mechanism and enough assumptions or evaluation detail to compare it. Theoretical work need not have experiments. Domain studies can supply parameter/cost evidence even without an agent controller. Surveys are discovery/context records, not substitutes for the cited primary result. Standards and software documentation form a separate supporting register.

Exclude with a recorded reason: exact duplicate; unrelated decision/enforcement setting; promotional description without an inspectable method; commentary with no primary method/evidence (retain separately if useful); inaccessible primary text after documented attempts (pending, not evidence against relevance). Do not exclude solely because a paper lacks code, has negative findings, or would undermine the proposed contribution.

Use two independent title/abstract and full-text reviewers where possible. Record each decision, reason code and disagreement; resolve by discussion or an identified third reviewer. If only one reviewer is available, label the review single-reviewer and obtain an independent audit sample using a rule fixed before screening. Keep uncertain records pending. A future flow diagram should be computed from the screening ledger; do not fill PRISMA counts from estimates.

For each included primary text extract:

- Exact title, authors, year, venue, DOI/identifier, primary URL, version/date, local checksum, correction/retraction status and page/section locator for every substantive claim.
- Question, domain, public history/state, hidden variables, action sequence, evidence outcome alphabet, evidence error/dependence/delay assumptions and whether verification automatically repairs.
- Permissions and trust boundary; action feasibility, budgets, human access, escalation effects and terminal conditions.
- Objective, utility/cost units, constraints, calibration/coverage assumptions, fallback mechanism, and distinction between a theorem and observed performance.
- Information and tuning access per comparator; oracle privilege; logged/all-arm supervision; propensities, overlap, confounding and sequential identification assumptions.
- Data provenance, independent sampling units, denominators, uncertainty, multiplicity, negative results, parameter sensitivity, external validation and leakage risks.
- Code/data availability and license, exact reproducibility route, implementation burden, applicability to each pilot and incompatibilities requiring disclosed adaptation.
- Closest overlap with the proposed question, a falsifiable remaining gap, and evidence that would erase that gap. Missing detail is recorded as missing, not inferred.

Assess quality by transparent dimensions (assumption clarity, baseline fairness, independence, statistical design, external validity and reproducibility), not an unvalidated aggregate score. Do not treat peer review or code availability as a guarantee of validity.

## Candidate-paper matrix: all entries UNVERIFIED

The titles/labels and locators below are transcribed search leads. Year, author, venue and method assertions in the planning sources have deliberately not been promoted to verified bibliography. The last column is a question to investigate, not a finding about the paper.

| ID | Candidate label as supplied | Local source and candidate primary locator | Status | Closest-method question to extract |
| --- | --- | --- | --- | --- |
| C01 | Safe Policy Improvement with Baseline Bootstrapping | R pp. 7, 19; https://proceedings.mlr.press/v97/laroche19a.html | UNVERIFIED | What fallback, support and uncertainty assumptions constrain a policy improvement claim? |
| C02 | Doubly Robust Policy Evaluation and Learning | R pp. 8, 19; https://icml.cc/2011/papers/554_icmlpaper.pdf | UNVERIFIED | Which logging/overlap assumptions apply, and does the formulation extend to our sequential histories? |
| C03 | Conformal Risk Control | R pp. 8, 19; https://proceedings.iclr.cc/paper_files/paper/2024/hash/f3549ef9b5ff520a7e41ff3cc306ab2b-Abstract-Conference.html | UNVERIFIED | What guarantee and assumptions, if any, apply to adaptive actions or shifted evidence? |
| C04 | AgentDojo | R pp. 8, 19 and research-plan line 150; https://proceedings.neurips.cc/paper_files/paper/2024/file/97091a5177d8dc64b1da8bf3e1f6fb54-Paper-Datasets_and_Benchmarks_Track.pdf | UNVERIFIED | Which task/grader and attack mechanisms could support independent evaluation without claiming equivalent objectives? |
| C05 | Defeating Prompt Injections by Design (CaMeL) | R pp. 8, 19; https://arxiv.org/abs/2503.18813 | UNVERIFIED | What control/data-flow and permission boundaries overlap with this architecture? |
| C06 | ToolEmu | R pp. 8, 19; research-plan line 151; https://proceedings.iclr.cc/paper_files/paper/2024/hash/7274ed909a312d4d869cc328ad1c5f04-Abstract-Conference.html | UNVERIFIED | How are tool effects and harms simulated or graded, and which validity threats transfer? |
| C07 | AgentRx | research-plan line 152; https://aclanthology.org/2026.findings-emnlp.598/ | UNVERIFIED | Does the primary record exist as cited, and what recovery decisions does it actually evaluate? |
| C08 | AgentCheck | research-plan line 153; https://aclanthology.org/2026.emnlp-demos.64/ | UNVERIFIED | Verify identity first; does it expose evidence before subsequent action? |
| C09 | AgentForesight | research-plan line 154; https://arxiv.org/abs/2605.08715 | UNVERIFIED | Verify identity first; how are predicted failure and action value distinguished? |
| C10 | DreamGuard | research-plan line 155; https://arxiv.org/abs/2608.05695 | UNVERIFIED | Verify identity first; what are its intervention, cost and comparator assumptions? |
| C11 | Accurate Failure Prediction in Agents Does Not Imply Effective Failure Prevention | research-plan line 156; https://arxiv.org/abs/2602.03338 | UNVERIFIED | Verify title/record; what evidence connects prediction to prevention or its failure? |
| C12 | Chronicle cut-point replay | research-plan line 157; https://aclanthology.org/2026.realm-1.71/ | UNVERIFIED | Verify whether this is a paper title; what replay guarantees and counterfactual limits are stated? |
| C13 | ReAct | R pp. 8, 19; primary locator not supplied | UNVERIFIED | Identify the intended text and its observation/action loop before comparison. |
| C14 | Toolformer | R pp. 8, 19; primary locator not supplied | UNVERIFIED | Identify intended text; distinguish tool-use training from post-verification decisions. |
| C15 | Agent Security Bench | R pp. 8, 19; primary locator not supplied | UNVERIFIED | Resolve identity and task/attack/grader compatibility. |
| C16 | AgentSpec | R pp. 8, 19; primary locator not supplied | UNVERIFIED | Resolve identity and runtime-policy scope. |
| C17 | Progent | R pp. 8, 19; primary locator not supplied | UNVERIFIED | Resolve identity and permitted-action enforcement scope. |

Search families without a uniquely identified paper: sequential value of information, POMDP active sensing, selective prediction, learning to defer, offline safe RL, contextual bandits, causal sequential inference, cost-sensitive calibration and independent red-team evaluations (R pp. 8-10, 19; H section 7). These are **UNVERIFIED discovery leads**, not additional screened papers. Domain validation/reconciliation studies are also required; do not invent titles to fill these gaps.

Supporting-source register, all **UNVERIFIED**: PRISMA 2020; NIST AI RMF and Generative AI Profile; OWASP GenAI guidance; NVIDIA NeMo Guardrails; Meta LlamaFirewall; OpenAI Agents SDK (R pp. 18-19). Inspect the specific official version before citing any capability or requirement. The roadmap links both NIST entries to the same landing page, so the profile needs separate identity resolution. No SDK use or network lookup is authorized now.

## Nearest-method comparison and stop criteria

Build a comparison matrix only after full-text inspection: verification before/after action, evidence-conditioned recovery, correlation and staleness, public versus hidden state, costs, permissions, baseline strength, sequential logging assumptions, grader independence and validated domains. Keep theoretical guarantees, simulated observations and deployment evidence in separate columns. Select nearest comparators by overlapping decision structure, not citation count or ease of beating them.

Reject or narrow the proposed novelty if a primary method already solves the same observable decision problem under comparable budgets and assumptions; if an existing benchmark already provides the two mechanisms and independent validation; or if the pilots cannot justify useful differences from existing tasks. A reproducible negative replication or benchmark characterization may remain valuable without a new algorithm. The five documents do not themselves establish that contribution.

Review completion requires logged searches and accessible coverage limits, deduplicated records, documented screening, claim-level primary-text extraction, reconciled reviewer decisions and a closest-work comparison. All remain future tasks. Literature retrieval, implementation and empirical evaluation each require a later authorized work package; this offline protocol launches none of them.

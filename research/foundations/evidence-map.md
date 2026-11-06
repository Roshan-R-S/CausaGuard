# CausaGuard research foundations: evidence map

Status: **post-result, documentation-only research planning**, 4 November 2026. This is not a preregistration, a new experimental result, or authorization for evaluation. The completed v0.5.2 closeout and its terminal development stop remain unchanged.

Labels used throughout this package: **OBSERVED** means inspected source or saved data in this task; **PREVIOUSLY REPORTED** means a recorded validation or research claim, not rerun here; **PROPOSED** means a future specification; **UNVERIFIED** means evidence is missing or has not been independently checked. Source inspection establishes what code specifies, not that every execution is correct.

## Sources and inspection boundary

All repository paths are relative to `D:/causaguard`; line locators refer to this checkout. JSON references use key paths because the development recording is serialized on one line.

| ID | Inspected source | Relevant scope |
| --- | --- | --- |
| R | `C:/Users/rosha/Downloads/CausaGuard_PhD_Research_Master_Roadmap_2026.pdf`, planning edition 01 | Page 7: O1-O7 and RQ1-RQ6; pp. 8-10: literature and sequential verification; p. 11: domains; pp. 12-13: baselines/statistics; pp. 14-18: contribution and governance; p. 19: candidate bibliography. Page numbers are PDF pages and printed page numbers. |
| H | `C:/Users/rosha/Documents/Codex/2026-11-02/referenced-chatgpt-conversation-this-is-an/outputs/causaguard-phd-next-step.md` | Handoff claims, including earlier proposal history; supporting file `causaguard-handoff-sources.json` in the same directory. |
| E | [intervention_env.py](../../src/causaguard/intervention_env.py), lines 36-94, 96-149, 152-221, 225-274 | Public observation and hidden case; shared domains; trusted access and independent access grading; terminal macro outcomes and all-arm supervision. |
| P | [intervention_policy.py](../../src/causaguard/intervention_policy.py), lines 38-102, 105-155, 174-191 | Outcome models/calibration, historical refit, deterministic repair and cost rule, public-observation-only selection. |
| F | [factorial_study.py](../../src/causaguard/factorial_study.py), lines 37-72 | v0.5.1 factorial hypotheses, 17-condition composite, training and fairness declarations; declarations are not evidence of acceptance. |
| V | [v052/study.py](../../src/causaguard/v052/study.py), lines 61-80, 178-243, 290-361, 395-409 | Recursive identity, paired evaluation cells, report validation and hard stop before approval/final generation. |
| I | [v052/inference.py](../../src/causaguard/v052/inference.py), lines 16-44, 133-170; [v052/policy.py](../../src/causaguard/v052/policy.py), lines 10-33 | Crossed bootstrap, inequalities, selection, comparator and 0.05 wrapper. |
| D | [v052-protocol.md](../../docs/v052-protocol.md), lines 34-46, 150-194, 196-223; [v052-results.md](../../docs/v052-results.md); [v052-summary.json](../../docs/v052-summary.json); [v052-closeout.md](../../docs/v052-closeout.md) | Locked rules, numerical result, historical validation and post-result conclusion. |
| A | [development-frozen.json](../../artifacts/v052/development-frozen.json), keys `selection`, `inference`, `identity`, `resources`, `authorization_violations`; [development-replay.json](../../artifacts/v052/development-replay.json) | Development evidence only; replay is a saved report, not a replay performed here. |
| G | [research-plan.md](../../docs/research-plan.md), lines 22-59, 99-158, 162-197; [adversarial.py](../../src/causaguard/adversarial.py), lines 14-18 | Historical methodology, candidate literature, synthetic-domain limitation and authored adversarial families. No historical final-outcome files were opened for this package. |

**OBSERVED:** Git status succeeds now, contrary to the access limitation recorded in H. Branch is `feat/research-v051`; HEAD is `b64c924309bd2dc4a7f9a18f4643d44bb6e91d90`. Existing modified tracked files are `pyproject.toml`, `src/causaguard/__init__.py` and `src/causaguard/cli.py`; untracked v0.51/v0.52 files, including the closeout, remain. No applicable AGENTS.md was found in the inspected workspace/ancestor paths. The five proposed foundation documents did not exist before authoring.

**OBSERVED now:** all 11 source-file hashes listed in H's supporting source manifest matched, including the PDF, closeout, protocol and development recording. The saved summary's inference and selection match the development freeze. The replay report names the same seal and 10,240,000 evaluations. This verifies documentary consistency, not a fresh execution. The roadmap's statements that v0.5 is unimplemented and its old clean-branch status (R pp. 1-2, 5, 16) are superseded by current source and development evidence; the original PDF is preserved.

## O1-O7 mapped to current evidence

Objective wording is paraphrased from R p. 7. None of the partial statuses below means the PhD objective is completed.

| Objective | Actual evidence and status | Limitation and untested question |
| --- | --- | --- |
| O1: validate a narrow research gap | **OBSERVED:** candidate references and explicit novelty caution in G lines 103-107, 148-158; R pp. 7-9, 19. This package supplies a proposed review protocol. | **UNVERIFIED:** no completed systematic screening/extraction record was found in the inspected project. Is the proposed task already covered by sequential value-of-information or deferral methods? |
| O2: credible simulated intervention environment | **OBSERVED:** E includes hidden state, delayed/error-prone verification, costs and independent access grading. | Verification remains a terminal macro; both domain labels share one mechanism. External parameter validity and independently reviewed task semantics remain unestablished. Can two distinct workflows justify their error and recovery models? |
| O3: fair learned/non-learned comparisons | **OBSERVED:** P, V and I implement matched cases, fixed baselines and common public observations. D specifies the adapted original comparator. | Baseline adequacy and protocol history need qualification. `cost_rule` is absent from v0.52. Can a practical deterministic evidence-contingent controller match any later learned controller with equal access and tuning resources? |
| O4: cost/risk-aware learning | **OBSERVED:** P and F specify learning/calibration comparisons; A records a negative v0.52 development result. | No utility superiority meeting this protocol was demonstrated. This does not isolate the cause of failure or disprove every learned intervention policy. Is useful evidence-contingent action selection possible before adding learning? |
| O5: justified intervention-effect estimation | **OBSERVED:** E line 273 constructs matched outcomes for every macro action; G lines 115-117 explicitly distinguishes simulation from factual logs. | All-arm supervision is stronger than one observed trajectory. Identification, sequential overlap, logged propensities and estimator sensitivity are separate untested work. |
| O6: cross-domain/adversarial evaluation | **OBSERVED:** E has two synthetic labels; G/adversarial source declares controls and attack families. **PREVIOUSLY REPORTED:** local adversarial methodology/replay in G. | These are not six independent domain processes or externally validated transfer. Financial operations, DevOps/cloud, multi-agent coordination and research automation remain roadmap extensions (R p. 11); adaptive external evaluation is not established here. |
| O7: reproducible publications and thesis | **OBSERVED:** protocols, source identities, saved development evidence and closeout exist (D/A/V). | A replayable local study is not a manuscript, accepted contribution, external replication or institutional approval. R pp. 14-18 gives proposed academic gates, not completed outcomes. |

## RQ1-RQ6 mapped to evidence and potential failure

| Question from R p. 7 | Current evidence | Next question and acceptable negative outcome |
| --- | --- | --- |
| RQ1: utility at matched operational risk | A/D: both candidates fail both required utility lower bounds; risk gates pass. | **PROPOSED:** compare sequential deterministic policies first. A strong fixed rule matching or beating them is informative; v0.52 does not answer this new question. |
| RQ2: reliability, cost, freshness and context change verification value | E lines 249-270 explicitly model these factors inside a macro. | Does returning evidence before the next decision change utility, with budgets and recovery access held equal? No useful differential value is a valid answer. |
| RQ3: calibration and fallback improve decisions | P lines 38-102 and F declare calibration and risk variants; I defines candidate eligibility. | No general benefit follows from a calibrated score. Do uncertainty-aware decisions outperform deterministic abstention under justified assumptions? Equal or worse decisions reject the claimed benefit. |
| RQ4: counterfactual estimators improve effect estimates | E/G provide simulator potential outcomes, not a validated factual-log estimator. | Can identification assumptions and support be defended for sequential logs? If not, restrict claims to simulator policy contrasts. |
| RQ5: shared representations transfer | E lines 19, 111-112 and 247 show label-dependent coefficients within a shared mechanism. | Distinct pilots are needed before any transfer question. Even then two mock workflows alone cannot establish external or leave-one-domain-out generalization. |
| RQ6: independent rules preserve authorization | E lines 152-221 defines separate executor and access grader; A records zero violations. | A fixture passing is bounded evidence, not proof against all attacks or production failures. Any unauthorized effect in a future fixture is an engineering failure, regardless of utility. |

## Preserve the negative result and its protocol history

**OBSERVED:** `selection = {status: development_stop, eligible_candidates: [], selected_candidate: null}`. Freeze seal: `053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6`. Final evaluation was not conducted according to D; no approval/final artifact is present in the v0.52 artifact listing. V lines 395-409 rejects no-candidate selection before checking approval or generating final cases. Final evaluation remains prohibited even with approval.

| Candidate | Contrast | Saved estimate | Saved one-sided lower bound |
| --- | --- | ---: | ---: |
| f16_raw_r05 | original_r05 | 0.0019163520013062763 | -0.0073814935506809195 |
| f16_raw_r05 | rules_repair | -0.018891941925222484 | -0.03629106484724314 |
| f16_cal_r05 | original_r05 | 0.027938854340797216 | -0.011411178413318172 |
| f16_cal_r05 | rules_repair | 0.007130560414268457 | -0.03277007506257903 |

All require L > +0.020 at alpha 0.00625. Both candidates pass absolute risk U <= 0.050 and excess risk versus always_verify U <= 0.010, with zero observed authorization violations across the simulated policies/profiles. Neither production safety nor general ineffectiveness of learning follows. H's rounded IID utility, unsafe-rate and cost means agree with A's saved policy summaries; they do not change these gates.

**Comparator limitation:** D and the closeout record `original_r05` replacing the earlier proposal's `cost_rule`, without an explicit rationale found. The protocol's local modification time is 2026-11-03 19:40:23 UTC; A records development creation at 19:51:39 UTC. Its bound protocol hash matches current bytes. This supports local predevelopment specification, not independently authenticated chronology or approval of the substitution. No retrospective rationale is supplied here.

**Additional history limitation:** H states that an earlier revised chat proposal used excess-risk margin 0.005. That earlier proposal itself was not independently verified in this task; the claim remains **UNVERIFIED**. D/I unambiguously use 0.010. Both saved upper bounds (-0.004199206542968747 raw; 0.0010157104492187808 calibrated) happen to be below 0.005, but this arithmetic does not establish execution of, or approval for, a different protocol. Do not conflate this claim with the separately documented v0.5 margin.

**Capability gaps, not causal diagnoses:** E's `verify` observes prior hidden state, generates a flag, automatically attempts repair, and returns a terminal outcome; no policy decision sees that flag. E's two domain labels share observation, access and outcome functions, including `lookup_customer`. E enumerates all-arm outcomes. These statements support the proposed design scope; none proves why v0.52 failed.

## Validation provenance and preservation

**PREVIOUSLY REPORTED, not rerun:** exact development replay matched the entire report/10,240,000 policy-case evaluations; pytest 480 passed, 6 skipped with one existing Starlette warning; Ruff and checkpoint `git diff --check` passed; preservation matched 129 pre-existing files; the seed audit reported 337 unused proposed/derived/test seeds (D/A). Do not report these as new tests or audits.

**Checks in this documentation task:** source and PDF inspection (including visual inspection of R p. 7), Git status/HEAD, the 11 handoff source hashes, and saved development/summary/replay consistency. Direct whitespace checking of all five untracked documents and `git diff --check` are closeout checks only. No simulator, fitting, tests, replay, final-outcome inspection, network access or branch operation is part of this package.

V lines 61-80 recursively hashes every Python source under `src/causaguard` and every Python test under `tests`, plus runtime and supporting artifacts. Adding code to those directories changes historical execution identity even without editing old files. New Markdown under `research/foundations` is outside those sets. The [implementation plan](next-implementation-plan.md) therefore proposes a separate experimental package and environment, without weakening the old validator or modifying the freeze.

The scoped continuation is [offline literature preparation](literature-review-protocol.md), [customer support](customer-support-pilot.md), [data engineering](data-engineering-pilot.md), and one [future engineering package](next-implementation-plan.md). Novelty, realistic parameters and any new empirical advantage remain unestablished.

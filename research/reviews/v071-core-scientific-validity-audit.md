# v0.7.1 core scientific validity audit

Date: 2026-11-07 (Asia/Calcutta). Baseline inspected: `cfa841ad5fd6dd5ad300b60554a6570b840a66db`. Decision: **PRE-FREEZE NO-GO remains in force.** This is a research-engineering review, not an independent institutional approval, protocol amendment, or authorization to evaluate.

## 1. Verdict and the three most serious weaknesses

The available evidence supports a reproducible, synthetic comparison of hand-written intervention policies. It does **not** yet establish that correct Bayesian VOI causes a robust advantage over strong alternatives, that the safety confidence procedure has nominal finite-sample coverage, or that the current zero-violation metric independently establishes authorization enforcement.

| Priority | Research weakness | Decisive evidence | Consequence |
| --- | --- | --- | --- |
| 1 | The primary DE candidate does not implement the claimed Bayesian update/VOI calculation. | `policy_v07_1.py:448–602`: DE verification ignores quoted schema FP/FN rates; a passing check removes schema/content risk and substitutes transient risk. Several expected utilities disagree with executed transitions. | Winning this benchmark would validate this particular approximate rule, not the claimed exact Bayesian mechanism. |
| 2 | Safety certification lacks adequate finite-sample calibration. | Exact enumeration of independent Bernoulli cluster shocks gives only **88.8242% coverage** and **11.1758% false safety qualification** at true operational risk 0.0501, using the current nominal 95% procedure. | The acknowledged CLT approximation has a concrete consequential failure case; passing formula tests does not establish safety inference. |
| 3 | The incremental causal benefit is not isolated against competitive, independently graded alternatives. | Fixed heuristic thresholds, privileged analytic model knowledge, ideal content detection, constrained human capacity, and self-reported authorization zeros confound attribution. Handcrafted revocation and escalation examples expose authorization grading gaps. | Utility gains may reflect simulator economics, imperfect baselines, or measurement defects rather than Bayesian information value or secure agent behavior. |

These are distinct from the preserved Priority 2 infrastructure work. Improved CI, signatures, and sandboxing cannot resolve incorrect scientific mechanisms or estimands. No changes to those infrastructure files are proposed in this delivery.

## 2. Scope, provenance, and evidence hierarchy

Initial Git status contained modified `.github/workflows/ci.yml` and untracked `.agents/`, `constraints-ci.txt`, `docs/adr/`, `research/ncm/`, and `skills-lock.json`. No active ancestor/root `AGENTS.md` was found. The deferred directory was excluded from content inspection and remains wholly outside this review. Only this document and the companion [falsification plan](../methodology/v071-falsification-and-validation-plan.md) are deliverables.

Selectively read the installed ECC `search-first`, `eval-harness`, `mle-workflow`, `verification-loop`, `python-testing`, and `security-review` instructions. Applied repository/literature search, explicit falsifiers, data and metric contracts, test inspection, and separation of authorization from statistical policy. No skill scripts, dependency installation, new training, sealing, or confirmatory runner execution occurred.

Repository evidence anchors below are paths relative to the repository root; line numbers refer to the inspected baseline, and named functions/sections identify the reference if line numbers move.

| Evidence | Exact repository reference | What it establishes |
| --- | --- | --- |
| Research objectives and older boundaries | `docs/research-plan.md`, sections Research question, Counterfactual formulation, Required baselines; `docs/architecture.md`, hard-boundary and v0.4 grading descriptions | Original motivation includes action-conditioned utility, randomized logging, strong baselines, and independent outcome grading; these are not all delivered in the isolated engine. |
| Current prospective specification | `experiments_v07_1/v071_confirmatory_protocol.json`, `protocol_status`, `authorization`, `statistical_parameters`, `sample_allocation`, `seed_allocation_registry`; `research/methodology/v071-confirmatory-statistical-protocol.md` §§1–5, 7, 9–10 | Review candidate, not sealed: K=128, N=400, DE primary IID, CS secondary; hurdle +0.015, utility FWER 0.010 over three contrasts, risk limit 0.050. |
| Historical decision context | `research/reviews/v071-independent-scientific-review.md`; `research/methodology/v071-formal-freeze-readiness-decision.md`; `v071-confirmatory-readiness-audit.md`; `v071-pre-freeze-blocker-report.md`; `v071-pre-freeze-statistical-corrections.md` | Earlier conditional-GO prose and now-obsolete infrastructure blockers are historical records, not current permission. Current JSON and user restriction control: NO-GO. |
| Active IDE draft | `experiments_v07_1/v071_confirmatory_protocol_draft.json` | Separate draft, retained unchanged; not substituted for current review-candidate JSON. |
| Mechanism | `src_v07_1/causaguard_v07_1/{policy_v07_1,domain_de,domain_cs,escalation,study_v07_1}.py` | Actual executable definitions, given priority over labels such as exact Bayesian, oracle, or independent grading. |
| Stored exploratory observations | `artifacts_v07_1/exploratory/exploratory_clusters.json`, `nominal_de.clusters`, `nominal_cs.clusters`; `exploratory_summary.json` | Sixteen historical clusters/domain, 400 cases/cluster; descriptive evidence only. Read and reaggregated, not regenerated. |
| Tests | `tests_v07_1/test_{policy_fairness,methodology_invariants,study,de_domain,cs_domain,escalation}_v07_1.py`; runner/security test fixtures inspected selectively | Tests cover mechanics and invariants, but do not certify posterior calibration, comparator strength, independent grading, or confidence coverage. |
| Production lock and proposed infrastructure | `experiments_v07_1/verify_seal_v07_1.py:103–107`; `docs/adr/0001-asymmetric-authorization-and-execution-isolation.md` | Production authorization is false, trusted signer registry empty; ADR is a proposal. Test-only synthetic signing is not production authorization. |

### Stored evidence and discrepancies

Independent reaggregation of **48** stored means (utility, risk, safe completion; eight policies; two domains) matched the summary to absolute tolerance `1e-12`. This verifies internal aggregation, not simulator replay, original execution provenance, or external validity.

| Historical exploratory quantity | Stored JSON value | Interpretation |
| --- | ---: | --- |
| DE candidate mean utility / operational risk | 0.1742443318 / 0.00234375 | Favorable within this simulator. |
| DE candidate minus always recovery | 0.0647877 | Exploratory gain, not independent confirmation. |
| DE candidate minus symmetric heuristic | 0.2843827 | Comparison against this hand-written heuristic only. |
| DE candidate safe completion | **0.7275** | Report executive prose at `docs/v071-exploratory-calibration-report.md:37` instead says 95.4%; its table at line 132 agrees with JSON. |
| DE symmetric heuristic risk | **0.06421875** | Report table at line 137 and current statistical protocol §§2.3 use 0.0633. Its stored mean escalation count is 43.25, not the report table's 68.6. Resolve provenance before relying on that table. |
| Candidate nominal mean escalations, DE and CS | **0 in both** | Current nominal results cannot demonstrate that candidate queue-aware human triage is beneficial. |
| CS candidate / always-recovery utility | 0.3894614910 / 0.3939675143 | Existing boundary result contradicts universal superiority. Budget-aware recovery is higher still, 0.4914355347. |

No original report was corrected. The documented v0.5.2 historical test-hash discrepancy in `research/methodology/v071-literature-review-gap-matrix.md` §4 remains a disclosed limitation; this review did not regenerate that study or authenticate its historical seal. Exact replay of a flawed model would still be a reproducibility achievement, not a validity proof.

## 3. Causal identification and mechanism validity

### 3.1 What the simulated contrast identifies

`study_v07_1.py::evaluate_cluster_v07_1` creates a separate queue per policy and evaluates the same ordered cases and exogenous tapes across policies. This is a useful common-random-number design. Its estimand is

`Delta_j = E[cluster_mean_utility(policy_candidate) - cluster_mean_utility(policy_j)]`

under the fixed generator, case order, capacity, authorization fixtures, and two-step execution contract. The intervention is replacement of the **whole cluster policy**. Within a policy, prior escalations consume capacity and affect later cases. Potential outcomes therefore depend on policy history; writing them solely as isolated `Y_i(a)` omits interference. Policy-order invariance prevents cross-policy contamination; it does not establish invariance to case order or absence of within-cluster interference.

All action outcomes are supplied by constructed transition rules. This provides identification *inside the assumed simulator*, not identification from observational agent traces. Real-world causal claims require consistency of action versions, treatment support, valid assignment/adjustment, and the appropriate interference unit. Doubly robust estimation does not remove unmeasured confounding merely by combining two models; the contrary wording in the existing gap matrix §2.3 must not be carried forward. See [Dudik, Langford and Li, 2011](https://arxiv.org/abs/1103.4601).

Fixed noise preserves each arm's marginal distribution when implemented correctly, but its cross-action coupling is a modeling choice. Individual counterfactual harm/recovery labels can depend on that coupling even when population mean contrasts do not. Neither seed identity nor cloned queues validates the physical structural equations.

Verification changes information, costs, time, remaining operations, and sometimes the authorization attempt. A policy contrast cannot separately identify the value of information, the value of conservative action selection, and these other pathways. Evidence-masking controls with unchanged verification costs/time and matched-rate verification controls are needed. Posterior correctness and intervention frequency are different properties: `v071-confirmatory-readiness-audit.md:85–86` incorrectly treats action frequencies as proof of Bayesian VOI.

### 3.2 Bayesian correctness

**DE: a direct mismatch, not just untested calibration.** `CostRulePolicyV07_1._select_de` at `policy_v07_1.py:448–602` estimates prior schema/content/transient probabilities with hand-written formulas. They are not the conditional probabilities implied by `domain_de.py::make_de_cases_v07_1`:

- The generator first draws schema failure from `clip(0.02 + 0.35*load, ...)`, then alarm from different Beta distributions and column-change indicators conditional on schema failure. Correct conditioning needs those likelihoods, rather than squaring the alarm.
- Generator content risk is `0.03 + 0.25*age/72 + 0.25*(1-quality)`; candidate uses `0.10 + 0.35*age/96 + 0.30*(1-quality)`.
- Generator transient risk uses `0.01 + 0.08*load`; candidate uses `0.01 + 0.04*load`.
- At lines 524–554, verification value weights clean/defect branches using latent-clean probability, not probability of the noisy observed evidence. Neither `quoted_fp_schema` nor `quoted_fn_schema` enters this calculation.
- At lines 564–575, a schema-valid, high-content-score check substitutes `p_0_t` for remaining hazard. For schema prior `p_s`, passing-check posterior should include `p_s*FN / (p_s*FN + (1-p_s)*(1-FP))`. False negatives do not erase schema risk.
- Transient failure is penalized as catastrophic harm in the policy's utility formula, although `execute_de_step_v07_1` treats transient crashes as clean failure without `unsafe=1`.

A handcrafted public observation with passing evidence selected `proceed` at both quoted FN=0.02 and FN=0.80. For an illustrative schema prior 0.20 and FP=0.02, the correct residual schema probabilities are 0.005076 and 0.169492 respectively. This illustration is not an estimate of the generator's posterior; it demonstrates the missing likelihood dependence. Reproduction is provided in the companion plan.

**CS: algebraic Bayes updates exist, but exact model correctness does not follow.** `_select_cs` lines 348–352 and 400–407 apply the standard binary update conditional on the supplied prior and error rates. However the prior at lines 271–281 differs from the conditional stale/fraud generator in `domain_cs.py:143–162`; the defect class aggregates states with different consequences. The post-check fixed `0.50` stale mixture is not a posterior over stale/fraud. `verifier_shift` deliberately changes actual FP/FN while leaving quotes unchanged. There is no distribution over uncertain model parameters or robust likelihood envelope. This is plug-in decision-making under latent-state uncertainty, not demonstrated Bayesian treatment of model uncertainty.

### 3.3 Expected utilities and simulation realism

1. **Perfect content detector:** `domain_de.py:418–421` gives content-defective scores in `[0.40,0.75]` and clean scores in `[0.85,0.99]`. Threshold 0.80 perfectly separates them. `verifier_shift` degrades schema checks, not this channel. A large information advantage may disappear with overlapping content likelihoods or correlated errors.
2. **Verification time is charged twice:** DE lines 409–411 charge time to verification; terminal branches at 318/482 add `prior_cost + action_cost + time_price*total_latency`. Thus the verification prefix's time charge recurs. CS has the same pattern at 396 and 309/456. The policy formulas generally charge prefix time once. This is an unvalidated scoring convention, with a mismatch to the candidate's assumed objective; it can disadvantage verification rather than favor it.
3. **Planned continuation differs from executed continuation:** CS verification planning includes `1-p_error` in escalation while its post-verification selector omits it. DE's clean verification branch is not maximized over all terminal alternatives; post-check selection is. Deadlines, actual lag, availability, and queue exhaustion are also not integrated consistently. The result is not an exact finite-horizon Bellman backup.
4. **Capacity is a quota, not a service queue:** `escalation.py::QueueState` counts cumulative escalations, with no service completion or capacity release. Latency depends on exogenous load and jitter, not actual backlog. `study_v07_1.py` does not give the policy queue occupancy. At capacity 150 for 400 cases, universal escalation necessarily saturates. This is a legitimate stress model if described precisely, but its penalties need external calibration and capacity-matched alternatives.
5. **Risk filtering is incomplete:** the 0.050 check filters `proceed`; recovery and escalation are not uniformly screened using predicted action-specific risk. A hard authorization check is a separate invariant and cannot be replaced by an expected-utility penalty.
6. **The oracle is not a proved upper bound:** `OraclePolicyV07_1.select` at lines 605–639 maps latent classes to fixed actions. It does not optimize costs, deadlines, capacity, or all realized potential outcomes. Treat it as a privileged diagnostic rule, not a regret denominator with proved optimality.

### 3.4 Comparator fairness and failure cases

Equal interfaces, operation prices, public observations, and isolated queues are good controls. However `CostSensitiveSymmetricHeuristicPolicyV07_1.select` uses fixed alarm thresholds 0.12/0.65/0.55 and a verify-cost versus recovery-cost test. It largely ignores value, harm, deadline, reliability, and available escalation economics. The candidate knows analytic structural constants, whereas the heuristic is not a comparably optimized policy over the same information. `test_symmetric_action_space_availability` only requires at least two action types; it is not an optimality or calibration test. No measured inference-compute budget establishes that Bayesian complexity is worthwhile.

At minimum, serious falsifying cases are:

| Case | Failure mechanism | Observable falsifier |
| --- | --- | --- |
| High schema false negatives; overlapping content scores | Passing evidence causes unjustified certainty. | Residual harm exceeds 0.050 or an uncertainty-aware recovery policy dominates. |
| Accurate cheap recovery / low recovery disruption | Verification consumes time and operations without enough incremental information. | Candidate utility gain is nonpositive; already suggested by CS exploratory results. |
| Scarce or dynamically changing human capacity | Fixed quota and unobserved occupancy break planned escalation value. | Gains disappear against budget-matched triage or reverse under a service queue. |
| Rare correlated catastrophes within otherwise independent clusters | Student-t bounds under-cover skewed bounded risk. | False safety qualification exceeds the nominal tolerance; an exact example is below. |
| Revocation between verify and proceed, or denied access followed by escalation | Execution contract and metric disagree. | Unauthorized mock completion with recorded authorization violations still zero. |
| Competitively tuned non-Bayesian selector | Claimed gain comes from calibration/model knowledge rather than Bayesian updating. | Candidate fails +0.015 against a simple cost-sensitive rule with matched data and tuning budget. |

## 4. Independent authorization and scientific outcome grading

The production study lock remains disabled, but it is a different boundary from authorization of a simulated tool action.

`domain_de.py::_check_independent_access` correctly checks immutable fixture fields, scope, and attempt-sensitive revocation. Yet `proceed` at line 320 always passes attempt 0; `restore` at line 455 uses attempt 1 after evidence. A handcrafted clean case with `revoke_after_attempts=1` and post-verification evidence allowed and completed `proceed`, while `restore` was denied. Both reported `authorization_violation=0`. CS proceed similarly hard-codes attempt 0.

DE/CS escalation delegates directly to `escalation.py`; the escalation module does not apply those authorization checks. A handcrafted DE case with `authorized=False` completed escalation and returned `allowed=True`, `authorization_violation=0`. If escalation represents only a notification and an independently authorized human workflow, that must be specified and graded separately. The current completion outcome is insufficient to establish that interpretation.

`study_v07_1.py::evaluate_cluster_v07_1` sums executor-supplied violation fields; the domain/escalation return paths inspected assign zero rather than using a separate action-trace oracle. Therefore zero observed violations are partly true by construction. The older architecture's independent v0.4 grader cannot automatically be credited to the isolated v0.7.1 engine. These are mock semantic counterexamples, not claims of a production exploit; no external tool actions were performed.

## 5. Statistical validity

### 5.1 Units, estimands, and independence

The appropriate independent unit is one ordered 400-case workload plus its policy-specific capacity trajectory. Cases sharing a queue are dependent. Paired differences must be formed within the same workload, then analyzed/resampled over clusters; eight policies do not multiply sample size. The generator uses `SeedSequence([seed, profile_idx, idx])`; distinct seeds support reproducibility but independence remains a modeling assumption. Shared fixed simulator parameters do not themselves induce stochastic dependence, but make all inference conditional on one environment specification. Shared outages/organizations across clusters would require a higher unit or explicit dependence model.

Let `Y_ki` be the binary unsafe event, `R_k = sum_i(Y_ki)/400`, `theta = E[R_k]`, and `q = P(R_k>0)`. Then `theta <= q <= min(1,400*theta)`. The first is average case-event risk under equal-sized clusters; the second is probability of any failure in a workload. Neither is a harm-severity-weighted loss or authorization-violation rate. Both should be reported with separate labels. With unequal cluster sizes, mean cluster rate and case-weighted risk diverge and require a prespecified choice.

For zero observed failed clusters, `1 - 0.05**(1/128) = 0.023132405251746757` is the exact one-sided binomial upper bound for `q` under IID Bernoulli cluster-failure indicators. Its upward rounding 0.02314 is conservative, and the inequality transfers an upper bound to `theta`. The case-level bound from 51,200 independent Bernoulli trials is not justified here. The zero-event result alone does not validate the whole piecewise risk procedure.

### 5.2 A finite-sample counterexample, independently calculated

`evaluate_confirmatory_v07_1.py::compute_clustered_operational_risk` uses a cluster Student-t UCB when variance is nonzero, the above bound at zero events, and fails closed for constant positive risk. Exact t coverage requires normal cluster measurements; bounded, skewed measurements have only approximate coverage. In particular, more than a generic warning is warranted:

Consider independent clusters with `R_k=1` with probability `q` and otherwise `R_k=0`. This models a rare shared shock harming all cases within a workload. It obeys the independent-cluster assumption and permits arbitrary within-cluster correlation. Here `theta=q` and `Z=sum R_k ~ Binomial(128,q)`. Enumerate all 129 possible Z values, call the current risk helper on each, and weight by the exact binomial probabilities. No PRNG or reserved seed is involved.

| True theta=q | Coverage `P(UCB >= theta)` | `P(UCB <= 0.050)` |
| ---: | ---: | ---: |
| 0.023 | 0.8466981492 | 0.6599330689 (true risk is below limit) |
| 0.025 | 0.8324120944 | 0.6019637860 (true risk is below limit) |
| **0.0501** | **0.8882421570** | **0.1117578430 (false qualification)** |
| 0.051 | 0.8962247581 | 0.1037752419 (false qualification) |
| 0.060 | 0.8880247802 | 0.0476262120 (false qualification) |

With no failed clusters the UCB is 0.0231324053; with **one wholly failed cluster** it falls to **0.0207573464**. This nonmonotonicity exposes the switch between incompatible boundary treatments. The example disproves a general 95% coverage claim under arbitrary bounded independent cluster rates; it does **not** estimate coverage under the current nominal DE generator. Assess that separately. Reproduction code is in plan §6.

For future alternatives, a full Clopper-Pearson bound on cluster-failure indicators is valid for `q` under its assumptions and conservative for `theta`, but may be extremely inefficient when many clusters each contain a few failures. Bounded-mean concentration targets `theta` directly with potentially wider intervals. See [Maurer and Pontil, 2009, Theorem 4](https://arxiv.org/pdf/0907.3740). No replacement is silently adopted here.

### 5.3 Multiplicity, gates, and interpretation

- Three *fixed* paired utility tests at `alpha=0.010/3` control their FWER by Bonferroni if each test is valid; independence between contrasts is unnecessary. Requiring all three to pass is a conjunctive claim and does not create extra multiplicity by itself.
- This 1% utility family is not a 1% guarantee about all safety statements, secondary domains, shifted profiles, or selected policies. Candidate safety uses 5%. A joint safety-and-utility error claim needs explicitly stated error semantics; a conservative union accounting would allocate up to 0.05+0.01 for separate erroneous claims if their bounds were valid. The unsafe-candidate case is controlled by the safety component, not by utility FWER.
- The Markdown protocol line 148 says comparator disqualification establishes superiority automatically; the runner lines 444–468 computes and requires **all three utility contrasts regardless**. The JSON says all eligible contrasts without defining a safe shortcut. Failing to certify a comparator is not proof it is unsafe, and even proved unsafety does not imply a +0.015 utility difference. This is an unresolved pre-freeze specification conflict.
- Protocol §9 labels non-rejection as heuristic equivalence and safety-gate failure as proof of model overconfidence. Neither inference is valid. Equivalence needs an equivalence margin and a suitable interval/test. Safety failure may mean uncertainty, model misspecification, execution/grading defects, or genuinely excessive risk. A positive but inconclusive contrast is not proof that the study was underpowered.
- Domain selection after favorable exploration is transparently disclosed. Fresh confirmation could test the selected claim, but cannot retroactively turn exploratory p-values into confirmation or support broad cross-domain generalization. All inspected hypotheses, thresholds, and seed allocations remain unchanged.

### 5.4 Power, practical effect, and degeneracies

At K=128, alpha=0.010/3, df=127, independently recalculated `tcrit=2.7583976216332347`. For planning gain 0.030 above a 0.015 hurdle, noncentral-t power is **0.9998987372** at SD=0.02601 and **0.9251839835** at SD=0.04026. The latter differs slightly from JSON's 0.925253; this is small numerical provenance drift, not the central power defect. These powers assume normal IID paired differences and specified effect/SD, not uncertainty in those parameters.

Protocol §4.3's Frechet-Bonferroni bound covers only the three utility-rejection events. Full success also includes candidate safety and zero authorization violations. If S denotes that safety event, the corresponding lower bound needs `max(0, 1-P(S^c)-sum_j P(A_j^c))`. No estimate of `P(S^c)` is supplied. Thus 92.52% is not an established joint study-success guarantee. An upper SD confidence bound estimated from only 16 exploratory clusters also depends on distributional assumptions and is not a probability guarantee about future power.

The C3 joint-power example substitutes SD=0.040 after listing an upper bound 0.08980. At gain 0.100, even the latter yields power approximately 0.9999999999999977, so the conclusion remains numerically large under that assumed effect, but the unexplained substitution should be reconciled. Planning effects and the practical hurdle still need stakeholder-scale justification: utility is a constructed mix of completion value, harm, money-like costs, and delay, not a validated real-world dollar outcome.

Constant-positive risk fails closed; nonfinite inputs and degenerate utility differences are rejected/inconclusive. These are useful protections. However `lcb_bonferroni=-1.0`, `p=1.0`, and `t=0.0` in the degenerate utility branch are reporting sentinels, not calculated inference. In particular -1 is not a proven lower utility bound: harm and costs can yield differences below -1. Report the inference status prominently. The risk helper accepts K=1 for boundary handling, while utility tests require K>=2; neither behavior substitutes for protocol-level K=128 validation. Duplicate clusters, mismatched workload IDs, and repeated looks are additional threats to effective sample size and error control.

## 6. Literature, competing methods, and novelty

Search/retrieval date: 2026-11-07. Consulted primary archive/proceedings/publisher pages and selected technical sections. This is a targeted verification, not an exhaustive systematic review or reproduction of other authors' results. The existing matrix's blanket claim of full technical verification is not adopted.

| Primary source and access level in this review | Overlap / strongest comparison | Audit disposition |
| --- | --- | --- |
| Howard (1966), [Information Value Theory, DOI](https://doi.org/10.1109/TSSC.1966.300074). Publisher endpoint blocked by JS/robot check. | Classical decision value of information. | Retain as established background; no new full-text verification claimed. Exact finite-state Bayesian decision analysis is the closest mathematical baseline. |
| Thomas, Theocharous and Ghavamzadeh (2015), [High-Confidence Off-Policy Evaluation, AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/9541); [High Confidence Policy Improvement, ICML/PMLR 37:2380–2388](https://proceedings.mlr.press/v37/thomas15.html). Records and relevant paper text inspected. | High-confidence return evaluation and policy improvement under stated assumptions. | The matrix conflates two papers and gives incorrect ICML/page metadata for HCOPE. These do not confer guarantees on CausaGuard's t procedure. |
| Laroche, Trichelair and Tachet des Combes (2019), [SPIBB](https://proceedings.mlr.press/v97/laroche19a.html). Primary record/abstract. | Safe fallback to the behavior policy in uncertain state-action regions. | Strong offline-RL reference if that task is implemented; not a drop-in comparator for a two-step known simulator without an offline data contract. |
| Dudik, Langford and Li (2011), [Doubly Robust Policy Evaluation and Learning](https://arxiv.org/abs/1103.4601). Primary record/abstract. | Combines outcome and logging-policy models for contextual-bandit evaluation. | Randomized/known-propensity evaluation is a useful independent estimator. Unmeasured-confounding identification is not supplied. The matrix conflates the conference title with the later [Doubly Robust Policy Evaluation and Optimization](https://arxiv.org/abs/1503.02834); do not reuse its merged citation. |
| Angelopoulos et al., [Conformal Risk Control](https://arxiv.org/abs/2208.02814), original preprint 2022, later revisions. Primary record/abstract. | Expected monotone-loss control through calibration. | Relevant calibration alternative; not automatically a high-probability bound on clustered catastrophe risk or valid under arbitrary shift. |
| Debenedetti et al. (2024), [AgentDojo](https://arxiv.org/abs/2406.13352). Primary abstract and paper record. | Agent/tool security benchmark, useful external task source. | Correct arXiv ID is **2406.13352**. Matrix's [2406.13314](https://arxiv.org/abs/2406.13314) is a gluodynamics paper. Benchmark comparison remains unperformed. |
| Ruan et al., [ToolEmu / Identifying the Risks of LM Agents with an LM-Emulated Sandbox](https://arxiv.org/abs/2309.15817), preprint 2023, revised 2024. Primary record. | Emulated tool-risk testing. | Relevant external stress framework, not an independent ground-truth oracle; emulator/judge error requires auditing. |
| Debenedetti et al. (2025), [CaMeL](https://arxiv.org/html/2503.18813v2), §§5, 6, 10. Technical sections inspected. | Control/data separation, capabilities, and policy enforcement outside the LLM. | Strongest directly relevant security architecture comparison. Independent authorization as a general principle is already covered; its scope and limitations must be compared fairly. |
| Vasudev, Russak, Bikel and Alshikh (2026), [failure prediction versus prevention](https://arxiv.org/html/2602.03338v1), §4 and Table 9. Technical sections inspected. | Disruption/recovery tradeoff, matched-rate and late-only intervention controls. | Central motivation is already explicit in prior work. Replace the matrix's Anonymous attribution; require these inexpensive controls. |
| Barke et al. (2026), [AgentRx](https://arxiv.org/abs/2602.02475). Primary record/abstract. | Failure localization and diagnosis. | Matrix's Wang et al. attribution is wrong. Claimed Findings/EMNLP locator was not verified here; do not assert venue metadata without the matching record. Diagnosis is not causal intervention benefit. |
| Mazumder and Lia (2026), [AgentCheck](https://aclanthology.org/2026.emnlp-demos.64/); Chawla and Koul (2026), [Chronicle](https://aclanthology.org/2026.realm-1.71/). Primary records/abstracts. | Fault interventions and cut-point replay, respectively. | Replay/intervention infrastructure is not unique. Correct Chronicle's inconsistent title/Anonymous attribution in future literature amendments. Neither record supplies observational identification. |
| Zhang et al. (2026), [AgentForesight](https://arxiv.org/abs/2605.08715). Primary record/abstract. | Prefix-only early failure auditing. | Replace Anonymous metadata; causal prevention and economic utility still require separate evidence. No full mathematical audit claimed. |
| Lin et al. (2026), [DreamGuard](https://arxiv.org/html/2608.05695v1), §3.4. Technical mechanism inspected. | Learned world-model immediate/prefix risk and runtime intervention. | A strong proactive-guardrail competitor for later shared task evaluation, not a static output filter. Published performance is not reproduced here. |
| Rebedea et al. (2023), [NeMo Guardrails](https://aclanthology.org/2023.emnlp-demo.40/). Primary record. | Programmable rails. | Do not characterize all guardrails as passive filtering. No current CausaGuard experiment compares against this system. |

**Established original contributions:** original repository artifacts include a reproducible two-domain simulator, paired policy harness, and explicit separation of policy choice from study authorization. Their existence is established; a new general scientific theorem, uniquely original VOI algorithm, or externally validated security improvement is **not established** by this audit.

**Promising but unproven:** an empirically calibrated account of when fallible verification is worth its delay and disruption; robust action selection with separate immutable authorization; a workload-level safety/utility benchmark with honest negative boundaries. The proposed experiments can make these publishable contributions rather than labels.

**Already covered:** classical VOI, Bayesian conditioning, constrained expected utility, conservative baseline fallback, common-noise simulation comparison, off-policy evaluation, separation of trusted control from untrusted data, and record/replay as a general concept.

**Unsupported now:** exact Bayesian DE POMDP control; general causal identification from agent logs; distribution-free safety or joint-power guarantees; strongest-baseline superiority; semantic prompt-injection immunity; production safety; and queue-aware candidate benefit inferred from runs in which the candidate never escalates. The matrix's future learned-policy roadmap is not a prerequisite for the next scientific step: falsify the current mechanism first. Stanford NCM remains deferred and excluded.

## 7. Validation performed and precise next task

- **PASS:** 13 selected existing statistical/protocol tests, 7 deselected, 0.86 s. Ran `.venv\Scripts\python.exe -B -m pytest -c pytest_v07_1.ini -p no:cacheprovider tests_v07_1/test_methodology_invariants_v07_1.py -k "student_t_power or paired_contrasts_hand or clustered_operational_risk_student or frechet_bonferroni_joint or boundary_zero_events or boundary_100_percent or constant_positive_cluster or gate1_failure_inviolable or invalid_and_non_finite or protocol_json_and_markdown or paired_contrast_statistics_rejects or paired_contrast_statistics_degenerate or gatekeeping_degenerate" -q`.
- **PASS:** 48 archived aggregate comparisons within `1e-12`; numeric critical value, power, zero-event bound, and exact shock-law enumeration independently evaluated using installed SciPy 1.18.1. System `python` lacked SciPy; existing `.venv` was used without installation.
- **COUNTEREXAMPLES CONFIRMED:** DE quoted-FN insensitivity; post-verification revocation mismatch; denied escalation completion with zero reported violation; finite-sample coverage failure. These are validation findings, not passing scientific gates.
- **NOT RUN:** full test suite, skill scripts, build/type/lint/coverage jobs, any simulator benchmark or reserved-seed generation, live agents, signing fixtures, cryptographic seal generation, production authorization, or deployment. Full security/runner suites contain synthetic signing/seal-writing fixtures, excluded under the explicit restriction. Build/type checks are not applicable to these documentation-only edits; no whole-repository green claim is made.
- **PASS:** both Python examples in the companion plan were extracted and executed as written, in memory with bytecode disabled, and reproduced the stated findings to floating-point precision. Both documents passed local-link, balanced-code-fence, and trailing-whitespace checks; `git diff --check` was clean for tracked changes.
- **Preservation PASS:** all **221** tracked or specifically protected evidence/infrastructure files in the before/after byte-hash inventory were unchanged. Final Git status adds only the two requested documents to the pre-existing dirty state. The deferred directory was excluded from the inventory. Original exploratory and frozen artifacts remain untouched. No commit, branch, push, or release operation.

**Implement next, only in a future authorized additive exploratory package:** the plan's E1 phase A, a **seed-free finite-state DE posterior and VOI consistency falsifier**. Independently derive the generator-implied posterior, enumerate legal two-step continuations with correctly specified evidence likelihoods, and compare the untouched candidate to an exact same-information reference. Include likelihood sensitivity, evidence masking, action-specific risk, cost accounting, and an independent authorization trace checker. Report disagreements and their causes before proposing a corrected candidate. No confirmatory promotion, threshold change, or sealing is authorized by this recommendation.

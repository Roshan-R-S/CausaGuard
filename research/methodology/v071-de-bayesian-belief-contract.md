# DE Bayesian belief-update contract — independent review

Date: 2026-11-07. Baseline: `cfa841ad5fd6dd5ad300b60554a6570b840a66db` plus preserved, uncommitted DE VOI Experiment 01. **PRE-FREEZE NO-GO.** This is a proposed research contract and verification record, not a policy repair, protocol amendment, or deployment approval.

## 1. Verdict and provenance

The eight-state reference correctly implements the declared nominal, authorized, one-verification model on the tested regular inputs. Its Bayes algebra, nominal conditional priors, terminal expectations, and piecewise-affine timing integration withstand the checks below. The three requested numerical counterexamples are independently reproduced without discrepancy beyond floating-point rounding. This is conditional verification, not a proof over all numerical inputs or a calibration result in the real world.

Two concrete reference defects/limitations were found: an unvalidated negative capacity argument can produce negative risk, and multiplication underflow can misclassify positive-probability evidence as impossible. Reusing the update for repeated simulator checks would also be invalid: repeated checks reuse the same random tape. None is a correction to the preserved candidate, reference, or historical results. The reference must not be promoted unchanged into a decision service.

Evidence read and compared:

- [Core audit](../reviews/v071-core-scientific-validity-audit.md), especially mechanism and authorization findings.
- [Falsification plan](v071-falsification-and-validation-plan.md), E1 and exploratory/confirmatory boundaries.
- [Experiment 01 report](../reviews/v071-de-voi-falsification-exp01.md) and [complete numerical evidence](../reviews/v071-de-voi-falsification-exp01.json), all eleven case records. Fresh `build_report()` equals the stored JSON object; it was not overwritten.
- [Reference](../experiments/de_voi_exp01/reference.py): `STATES`, `generator_prior`, `bayes`, `evidence_branches`, `terminal_values`, `_mean_continuation`, `verification_values`.
- [Adapter](../experiments/de_voi_exp01/experiment.py): `candidate_action`, `minimized_case`, `build_report`; [independent checker](../experiments/de_voi_exp01/authorization.py): `grade_trace`.
- [DE simulator](../../src_v07_1/causaguard_v07_1/domain_de.py): `make_de_cases_v07_1` (line 108), `_check_independent_access` (242), `execute_de_step_v07_1` (264).
- [Candidate](../../src_v07_1/causaguard_v07_1/policy_v07_1.py): `CostRulePolicyV07_1._select_de`, lines 448–602; [escalation](../../src_v07_1/causaguard_v07_1/escalation.py): `HumanEscalationParamsDE` (45), `execute_escalation_de` (262).

All equations below are derived from these executable definitions, not attributed to an unverified publication. No literature novelty or empirical superiority claim is introduced.

## 2. Model, information boundary, and assumptions

Let `Z=(S,C,T)` in `{0,1}^3`: schema drift, content corruption, and transient failure. Enumeration is lexicographic `000,001,010,011,100,101,110,111`; all eight states are necessary because losses and recovery differ by component. `S OR C` is catastrophic defect; isolated `T` is a clean failure, not an unsafe event.

Let public observations be `X=(L,A,D,Q,J,alpha,beta,d,tau,V,H,f_p,f_v,f_r,f_h,w,B)`: load, alarm, age, quality, changed-column indicator, quoted FP/FN, observation delay, deadline, value, harm, action fees, hourly cost, and operation budget. Let elapsed time be `e` and already charged cost be `k`. Evidence is schema pass `Y`, content score `R`, and observed elapsed time. Authority and resource identity belong to an independent execution boundary, not latent-state inference.

| Assumption | Status and consequence |
| --- | --- |
| Conditional independence of S,C,T given their public parent covariates | Established by the nominal generator's separate draws. Not unconditional independence: load influences both S and T. |
| Alarm and column indicator independent given S | Established by separate generator draws. Conditioning on these signals changes S, not C/T under this DAG. |
| Fixed latent defects during one episode | Established by the current transition implementation. No latent temporal evolution is modeled. |
| Schema/content/timing observation noises mutually independent conditional on state and public fields | Established for the first check by distinct draws and lag. The idealization treats PRNG draws as independent uniforms; deterministic seed mechanics are not a physical independence proof. |
| Content evidence perfectly separates C | Established simulator assumption, unrealistic until externally justified. |
| Quoted FP/FN equal actual likelihoods | True on nominal generator support; introduced calibrated-likelihood assumption for arbitrary reference inputs. False in `verifier_shift`. |
| Default restore and human parameters, nominal outage | Reference restriction; simulator permits parameters and shifts not represented by the reference. |
| Authorized throughout; known capacity availability; one episode | Reference restriction. Does not solve revocation, unknown capacity, or multi-episode quota allocation. |
| Conditional action risk at most .050 | Introduced reference decision constraint matching the claimed target, not an enforcement property of the executor or a confidence bound. Does not amend the registered estimand. |
| Exact generator knowledge | Privileged mathematical benchmark; not equal training information for a deployable comparator. |

The reference accepts `PublicDE`, never a simulator case, hidden flags, actual shifted rates, outage realizations, or random tape. An explicit belief argument is useful for mathematical tests, but a future decision API must prevent callers from substituting realized truth. AST/import tests and the public-field adapter test support isolation; they do not prove end-to-end absence of every possible leak. Authority availability must be supplied by a trusted boundary, not guessed by a policy.

## 3. Initial Bayesian belief

Define `clip(x,l,u)=min(u,max(l,x))`. Before alarm/column evidence:

\[
q_S=\operatorname{clip}(.02+.35L,.01,.85),\quad
q_C=\operatorname{clip}(.03+.25D/72+.25(1-Q),.01,.90),\quad
q_T=\operatorname{clip}(.01+.08L,.01,.25).
\]

With beta density `f(a;r,s)=a^(r-1)(1-a)^(s-1)/B(r,s)`, define

\[
g_1(A,J)=f(A;5,2)(2/3)^J(1/3)^{1-J},
\quad g_0(A,J)=f(A;1.5,6)(1/60)^J(59/60)^{1-J}.
\]

The `1/60` is `.05 * 1/3`, not `.05`. Bayes gives

\[
p_S=\frac{q_Sg_1}{q_Sg_1+(1-q_S)g_0},\qquad
b_X(s,c,t)=p_S^s(1-p_S)^{1-s}q_C^c(1-q_C)^{1-c}q_T^t(1-q_T)^{1-t}.
\]

This is a prior for the *paid check*, already a posterior conditional on the initial public observations. Public costs and deadline are ancillary to defect state in the nominal generator. Rates are deterministic functions of quality there: `alpha=.015+.06(1-Q)`, `beta=.020+.18(1-Q)`; conditioning on them does not provide additional defect information beyond Q. Off-equation rates require an explicitly declared stress model.

`generator_prior` uses log beta densities and normalized weighted densities. Densities may exceed one; the discrete `bayes` helper deliberately restricts likelihoods to [0,1] and is not a general continuous-density update API. At A=0 or 1 both modeled densities vanish; the reference rejects these out-of-support endpoints instead of choosing an arbitrary conditional version. A future interface must distinguish out-of-support input from numerical underflow.

## 4. Verification likelihood and posterior

Define alpha as `P(Y=fail | S=0)` and beta as `P(Y=pass | S=1)`, not their reversed meanings. Thus

\[
P(Y=1\mid S=s)=\begin{cases}1-\alpha&s=0\\\beta&s=1.\end{cases}
\]

The score density is uniform on [0.40,0.75] when C=1 and [0.85,0.99] when C=0, with densities `1/.35` and `1/.14` respectively. Endpoints have zero probability under the continuous law. Scores in the gap or outside support are model-inconsistent and must not be classified as ordinary clean evidence. The binary statistic `K=1[R>.80]` is sufficient on support: `P(K=k|C=c)=1[k=1-c]`. The original reference operates on K and does not validate raw scores.

For the first check, elapsed time `E=d+U(.05,.40)` is independent of Z. Its density cancels from the posterior but must enter continuation utility. Given binary evidence `(y,k)`, define

\[
\ell_{y,k}(s,c,t)=p_y(s)\,1[k=1-c],\quad
m_{y,k}=\sum_z b_X(z)\ell_{y,k}(z),\quad
b_{y,k}(z)=\frac{b_X(z)\ell_{y,k}(z)}{m_{y,k}}.
\]

Only branches with positive mass exist. Zero mass is an explicit undefined-evidence result, never a fabricated posterior. These enumeration equations work for *dependent* supplied joint beliefs too; factorization is used only to construct the nominal initial belief.

For the nominal product belief, schema marginal updates are

\[
p_S^{pass}=\frac{p_S\beta}{p_S\beta+(1-p_S)(1-\alpha)},\qquad
p_S^{fail}=\frac{p_S(1-\beta)}{p_S(1-\beta)+(1-p_S)\alpha}.
\]

Content is identified by K and `P(T=1|evidence)=q_T` under the nominal independence assumptions. Passing schema evidence leaves positive schema risk whenever `p_S>0` and `beta>0`. A fail does not imply S=1 when alpha is positive. If `alpha+beta=1`, schema evidence is uninformative; if greater than one, a pass can increase defect odds. Reliability labels must not override the actual likelihood ratio.

Do not apply the first-check likelihood twice to a repeated result: the current executor reuses `draws[0]` and `draws[5]`. Conditional on the first identical result, the second has likelihood one, not another independent factor. This contract permits one verification followed by a terminal continuation. Independent repeated sensing requires a different measurement process and protocol.

## 5. Operational risk, utility, and timing

For arbitrary joint belief b, define `h_b=sum b(z)1[S OR C]`, `g_b=b(0,0,0)`, and `s_b=sum b(z)1[S]`. Do not replace h by `1-P(no defect)`; that includes noncatastrophic T. Under independence, `h_b=1-(1-p_S)(1-p_C)`, but the joint sum is the general contract.

Let `a=1-clip(.01+.40L,.01,.95)`. Let terminal duration `D_a~U(l_a,u_a)` and

\[
F_a(e)=\operatorname{clip}\left(\frac{\tau-e-l_a}{u_a-l_a},0,1\right),\qquad
\mu_a=(l_a+u_a)/2.
\]

Durations: proceed [.10,.20], restore [.20+L,.35+L], escalate [1.20+1.50L,1.50+1.50L]. Availability, duration, and state are independent conditional on public fields under the modeled transitions. Shared outage draws across alternative actions affect joint counterfactual coupling, not these marginal expectations.

**Proposed once-only accounting:** `C_a=k+f_a+w*mu_a`. **Preserved executor accounting:** `C_a^exec=k+f_a+w*(e+mu_a)`. Costs remain incurred when late, unavailable, or unsuccessful; never multiply costs by F or availability. These are distinct scoring contracts, not interchangeable fixes.

Proceed:

\[
R_p(b,e)=F_p(e)a h_b,\qquad U_p(b,e,k)=F_p(e)a(Vg_b-Hh_b)-C_p.
\]

Restore (default parameters):

\[
R_r=0,\qquad U_r=F_r(e)aV[.45(1-s_b)+(.8\cdot.10+.2\cdot.45)s_b]-C_r.
\]

Restore is not guaranteed full recovery: it produces degraded fallback and schema-dependent persistent loss. With nondefault persistence p and fallback v, replace the schema term by `p*.10+(1-p)*v` and clean term by v; the current reference fixes defaults.

Escalation: let `a_h=clip(1-.25L,.40,.98)`, `epsilon=clip(.05+.08L,.02,.25)`, capacity indicator `I` in `{0,1}`, and `r(z)=.75` if S, else `.80` if C, else `.85` if T, else `1`. The priority matters for overlapping defects. Let `f_h_total=f_h+.75+.30L` in C_h. Then

\[
R_h=F_h(e)a_h I\epsilon\,.5h_b,
\quad U_h=F_h(e)a_h I\left[(1-\epsilon).75V\sum_z b(z)r(z)-4\epsilon\,.5h_b\right]-C_h.
\]

The harm coefficient 4 is the default human-error penalty, not public H. The human cost is incurred even at capacity exhaustion. These equations do not resolve whether a human repair carries separate authority; that remains an execution contract blocker.

Risk above is a conditional single-action unsafe-event probability, including on-time/availability factors. It is not a cluster-level probability of any failure, an uncertainty upper confidence limit, or a change to the confirmatory operational-risk estimand. A late action can have zero modeled risk and still be useless. Any eventual model-uncertainty safety bound requires additional assumptions and validation.

## 6. Verification continuation and information value

Let `A(b,e,B)` contain authorized, budget-legal terminal actions whose modeled risk is at most .050. Proceed/restore cost one operation, escalation zero. Authorization must be checked again at execution. Define

\[
W(b,e,k,B)=\max_{a\in A(b,e,B)}U_a(b,e,k).
\]

Empty feasible sets or undefined model values require an explicit blocked/abstained result, not a maximum over invalid numbers. The reference assumes authorization and retains safe restore, so it does not implement this full runtime fail-closed contract.

For initial B=2, verification consumes one operation and charges `k_v(E)=f_v+wE`. Its episode value is

\[
Q_v=\sum_{y,k}m_{y,k}\frac1{.35}\int_{d+.05}^{d+.40}
W(b_{y,k},E,f_v+wE,1)\,dE,
\quad \Delta_v=Q_v-W(b_X,0,0,2).
\]

Use once-only or executor costs consistently inside W and label which. In executor mode the integrand includes `2wE`; in once-only mode it includes `wE`. The reference excludes verification at B=1 because the existing executor terminates after consuming the last operation; no free post-verification escalation is assumed. This is a declared admissibility restriction: literal simulator verification at B=1 has terminal value `-f_v-w E[E]`, not an available information-acquisition continuation. If a future optimizer permits that wasteful terminal action, include it explicitly rather than claim the current reference optimizes every executable string.

Timing verification: each terminal expected utility is affine between deadline knots `tau-u_a` and `tau-l_a`; costs are affine everywhere. Risk is likewise piecewise affine. The reference adds those knots, every pairwise utility crossing, and every risk-threshold crossing. On each resulting open interval, the feasible maximizer is fixed and its utility affine, so midpoint times interval length integrates exactly. Feasibility can jump; values at isolated endpoints have zero measure. Multiple crossings at the same time and exact ties do not invalidate the integral. Arbitrary nonlinear delay/state dependence would invalidate this proof.

Classical gross EVSI must use a fixed common action set, no information-acquisition cost or delay, and no belief-dependent feasible-set changes:

\[
EVSI=\sum_{y,k}m_{y,k}\max_a U_a(b_{y,k},0,0)-\max_a U_a(b_X,0,0)\ge0.
\]

Nonnegativity follows because the informed selector can ignore evidence, and `sum m*b_posterior=b_X`; terminal utilities are affine in b. The reference deliberately removes the risk filter for this diagnostic. Operational net gain can be negative and is generally not `EVSI-f_v`. Changing verify fee by delta reduces Q_v and net gain by delta when continuation and admissibility are otherwise fixed; gross EVSI is unchanged.

## 7. Independent numerical verification and sensitivity

Use the Experiment 01 default public fixture: `L=.2,A=.5,D=24,Q=.8,J=0,alpha=.02,beta=.02,d=.1,tau=4,V=1.5,H=5,f_p=.02,f_v=.1,f_r=.45,f_h=.5,w=.02,B=2`. Rates here define a calibrated stress fixture, not nominal Q-derived rates.

Independent beta-density computation uses `f1=30*A^4*(1-A)` and `f0=A^.5*(1-A)^5*Gamma(7.5)/(Gamma(1.5)*Gamma(6))`, separately from the reference log-density path. At A=.5, `p_S=.07479087834074905`, `q_C=49/300`, `q_T=13/500`.

| Witness | Independent calculation | Comparison |
| --- | --- | --- |
| B1, beta=.8, schema/content pass, elapsed .3 | `p_pass=p_S*.8/(p_S*.8+(1-p_S)*.98)=.06190416190626986`; on time, `R_p=.91*p_pass=.05633278733470557` | Candidate proceeds; exceeds .050 by .00633278733470557. Reference restores. |
| E3, A=.8, alpha=.027, beta=.056, restore fee .44, deadline 3.9 | `p_S=.9423969886437508`; `U_r=.91*1.5*(.45-.28*p_S)-.44-.02*.475=-.19543412905964153` | Nominal-equation-consistent public inputs. All evidence branches select restore. |
| E3 continuation | Posterior mean equals prior; all restores on time. `Delta_v=-.1-2*.02*(.1+.225)=-.113`; `Q_v=-.3084341290596414` | Candidate verifies. Under once-only accounting gain remains negative: -.1065. |
| D1, clean state, w=.2, verify time .3, proceed time .15 | Once-only `.1+.02+.2*(.3+.15)=.21`; executor `.1+.2*.3+.02+.2*(.3+.15)=.27` | Duplicate `.2*.3=.06`, independently recalculated with exact rational arithmetic. |

These are model-based values and deterministic action discrepancies, not treatment-effect estimates or sampled failure frequencies. B1's beta=.8 is outside nominal IID reliability support; E3 supplies the nominal-support action witness.

Sensitivity, holding the default fixture otherwise fixed:

| Variation | Result |
| --- | --- |
| Alarm A=.2 / .5 / .8 | Initial schema posterior .0004990246388704983 / .07479087834074905 / .9423969886437508. Column indicator likelihoods independently tested for J=0 and J=1. |
| FN=.02 / .056 / .22 / .8 with FP=.02 | Passing posterior .001647012024188512 / .004598002330501784 / .01782357582902916 / .06190416190626986. |
| Same FN sequence | Net verification gain .7552979634155359 / .745508737474162 / .7009133748523462 / -.113. This local sequence is not a universal monotonicity theorem for constrained VOI. |
| Verify fee 0 / .1 / .6 / 1 | Net gain .8552979634155359 / .7552979634155359 / .2552979634155359 / -.1447020365844641; gross EVSI unchanged. |
| Nominal Q=.8 rates .027/.056 vs actual verifier-shift .127/.256 | Passing schema posterior .004630928296770854 vs .023155798007136748; nominal-availability risk .004214144750061477 vs .021071776186494442. Quoted rates alone cannot identify the latter. |
| Arbitrary dependent eight-state prior `b_i=(i+1)/36` | Exact Fraction enumeration matches all possible evidence branches for perfect, noisy, and uninformative schema sensors; dependence is retained rather than refactorized. |

Changing alarm noise distributions, introducing overlapping content scores, or correlating defects requires new likelihoods, not just new numeric inputs to the nominal generator prior. For uncertain parameters theta, a genuine Bayesian extension needs a justified joint distribution and `P(z|e,X)=integral P(z,theta|e,X)dtheta`; this reference uses fixed plug-in parameters. A likelihood envelope and worst-case decision constraint are a different robust approach. Neither is established here.

## 8. Counterexamples against the reference and test harness

1. **Invalid capacity admitted:** `terminal_values(PublicDE(), generator_prior(PublicDE()), capacity_available=-1)` returns escalation risk **-.007082227343438678** and `feasible=True`. The documented Boolean precondition is not enforced. This falsifies universal input validation, not nominal Boolean-capacity results. Require a strict Boolean or a separately specified probability type, finite bounded output checks, and no authorization from malformed capacity.
2. **Floating-point underflow:** `bayes((1e-200,1.),(1e-200,0.))` raises “Evidence has zero probability.” Exact normalizer is positive, `10^-400`, and posterior is `(1,0)`. Fail-closed exception is preferable to fabricated certainty but its reason is mathematically inaccurate; use scaled/log-domain weights and distinguish numeric failure from impossible evidence. No existing nominal witness uses this extreme range.
3. **Repeated evidence misuse:** prior (.8,.2), pass likelihood (.98,.02) yields posterior schema `1/197`. Applying it twice reduces risk again, although a repeated same-tape simulator result adds no information. The single-verification reference remains valid; unrestricted reuse does not.
4. **Scope, not demonstrated code error:** reference hard-codes default escalation and outage, Boolean capacity, one-check horizon, and calibrated schema rates; it cannot claim exactness under shifted or nondefault transitions. Impossible raw score gaps and authority state are not represented in its API. These are explicit preconditions for the contract.

The original six strict xfails are not intrinsically immune to false evidence. They omit `raises=AssertionError`, so unrelated exceptions anywhere in `build_report()` can count as expected failure. `strict=True` only prevents an unexpected *pass* from being accepted. The B1 assertion also checks risk excess without itself asserting that the candidate proceeds. Therefore the original tests alone are insufficient scientific guards.

The new ordinary [contract tests](../../tests_v07_1/test_de_belief_contract.py) call all six functions directly, require `AssertionError`, and verify that the innermost traceback is their own claim function, not setup or report generation. They separately recompute B1 and assert the candidate action. All six currently fail at the intended assertions: B1 risk, E1 argmax, E3 nominal argmax, D1 duplicate cost, G1 revoked effect, G1 reported violations. An unexpected pass or unrelated exception fails the new guard. Numerical recalculations also cross-check the report fields. This strengthens the evidence without editing preserved tests. It does not make the report builder independent of its own model, nor constitute exhaustive mutation testing.

## 9. Falsifiable acceptance requirements

| Invariant | Proposed acceptance test and current status |
| --- | --- |
| Joint beliefs finite, nonnegative, sum to one | Reject wrong lengths, NaN, invalid mass; exact rational branch enumeration and posterior martingale checks pass on tested cases. Specify absolute tolerance 1e-12 for ordinary float normalization; do not silently renormalize malformed input. |
| Pass/fail obey likelihood ratios | Hand calculations, perfect/uninformative sensors, positive residual risk, reversed-information likelihoods. Pass/fail equations specified; selected cases tested, full parameter grid remains proposed. |
| Initial conditioning is correct | Independent beta-integral comparison over both J values and three alarms passes. Recalibration to external data remains unperformed. |
| Evidence provenance prevents double counting | Each check needs identity, time, sensor version, and dependence semantics. Duplicate same-tape evidence must be idempotent. Current reference lacks history validation. |
| No hidden truth at decision time | Public adapter and no-generator/import tests retained; future API forbids hidden fields and validates supplied belief provenance. Equal public interfaces do not imply equal model knowledge. |
| Costs charged once | Independent rational D1 witness preserved. Proposed incremental equation is the acceptance target; existing executor fails. No historical score correction made. |
| Timing and action comparison agree | Analytic envelope proof plus existing executor partition enumeration and deterministic midpoint comparisons retained. Additional nonlinear/stale-evidence models need new integration validation. |
| Gross and net VOI separated | Same-action-set gross EVSI nonnegative up to roundoff; fee-shift invariance/slope tests pass; budget-1 information acquisition unavailable. |
| Risk is action-specific | T-only state must have zero unsafe probability; union S OR C counted once; conditional harm probabilities finite and in [0,1]. Negative-capacity counterexample violates the general output invariant. |
| Authorization remains independent | Recheck exact attempt/resource/authority at execution, including escalation repair; no statistical score can grant permission. Existing G1/G2 remain blockers; checker uses modeled effects, not production telemetry. |
| Unsafe/undefined decisions fail closed | Reject impossible evidence, malformed rates/capacity, numeric failures, unavailable authority, and empty feasible set; return a typed nonexecuting result. Do not automatically escalate a repair without authority. Reference is not a complete runtime implementation. |
| Scientific boundaries retained | No reserved seeds, frozen artifact edits, new production access, or revised thresholds. New contract tests are exploratory mathematical validation, not confirmatory evidence. |

## 10. Reproduction, validation, and next task

From the repository root, existing environment only:

```powershell
.venv\Scripts\python.exe -B -m pytest -c pytest_v07_1.ini -p no:cacheprovider tests_v07_1/test_de_belief_contract.py tests_v07_1/test_de_reference_exp01.py tests_v07_1/test_de_falsification_exp01.py -q
.venv\Scripts\python.exe -B -m ruff check --no-cache tests_v07_1/test_de_belief_contract.py
.venv\Scripts\python.exe -B -m research.experiments.de_voi_exp01.experiment --case B1
.venv\Scripts\python.exe -B -m research.experiments.de_voi_exp01.experiment --case E3
.venv\Scripts\python.exe -B -m research.experiments.de_voi_exp01.experiment --case D1
```

The added tests use exact Fraction arithmetic where feasible, independent direct beta densities, explicit deterministic inputs, and ordinary assertions about known limitations. They do not turn the limitations into acceptable decision behavior. Existing timing tests integrate 2,000 deterministic midpoint samples per branch (not Monte Carlo), and partition executor outcome thresholds over all eight states. No generators or reserved seeds are used by these isolated suites. This task adds review tests against existing code; no implementation/TDD repair cycle is claimed.

Observed validation: **67 passed, 6 strict xfailed** across these three files (15 new contract tests plus the preserved 52 passing tests); lint passes. Stored Experiment 01 JSON matches fresh in-memory report generation. No new coverage percentage is claimed, and no production/package/type-check validation is implied. Final preservation checks cover the pre-existing inventoried files, including the candidate, protocols, prior evidence and infrastructure; NCM is excluded and untouched.

**Replacement decision:** the evidence justifies designing a separate corrected experimental policy, but does not justify replacing the current candidate, reusing its confirmatory approval, or claiming improved performance. Belief correctness is necessary, not sufficient: cost semantics, authority, model uncertainty, capacity, and statistical validity remain unresolved. The conditional model does not identify external causal effects.

**One next implementation task, after review:** implement an isolated, unregistered DE belief-state module with a public-observation/evidence-only API, stable eight-state normalization, pass/fail likelihoods, duplicate-evidence provenance, strict input validation, and typed undefined-belief results; test it against the exact enumerations here. Do not connect it to action selection or replace `CostRulePolicyV07_1` in that task. This document is not authorization to implement that follow-up now.

**PRE-FREEZE NO-GO remains.** Existing policy, confirmatory protocol, Experiment 01 artifacts, and infrastructure work are preserved; no keys, seals, production authorization, dependencies, commits, pushes, or NCM work.

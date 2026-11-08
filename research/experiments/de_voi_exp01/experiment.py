"""Read-only candidate adapter and deterministic falsification evidence CLI.

No generators, seeds, seal/signature utilities, benchmark runners or policy changes.
Default output is stdout. --assert-claims intentionally exits 1 for falsified claims.
"""

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

from .authorization import Authority, Event, grade_trace
from .reference import (
    PublicDE,
    bayes,
    best_terminal,
    evidence_branches,
    generator_prior,
    terminal_values,
    verification_values,
)

ROOT = Path(__file__).resolve().parents[3]
COMMAND = ".venv\\Scripts\\python.exe -B -m research.experiments.de_voi_exp01.experiment"


def _candidate_api():
    for folder in ("src", "src_v07_1"):
        path = str(ROOT / folder)
        if path not in sys.path:
            sys.path.insert(0, path)
    from causaguard_v07_1.domain_de import DEEvidenceV07_1, DEObservationV07_1
    from causaguard_v07_1.policy_v07_1 import CostRulePolicyV07_1

    return CostRulePolicyV07_1(), DEObservationV07_1, DEEvidenceV07_1


def candidate_action(obs, evidence=None):
    policy, observation_type, evidence_type = _candidate_api()
    ev = None if evidence is None else evidence_type(*evidence)
    return policy.select(
        observation_type(**asdict(obs)),
        evidence=ev,
        b_rem=obs.budget if evidence is None else obs.budget - 1,
    )


def minimized_case(obs, *, authority=True, revoke=None, time_draw=0.5):
    """Construct an explicit clean witness, not a sampled scenario.

    The inert case.seed field is required by the existing dataclass; no PRNG uses it.
    Latent truth is given only to the executor, never to candidate/reference selectors.
    """
    _, observation_type, _ = _candidate_api()
    from causaguard_v07_1.domain_de import DECaseV07_1

    from causaguard.mock_tools import MockState

    state = MockState(authorized=authority, revoke_after_attempts=revoke)
    draws = [0.9] * 12
    draws[3] = time_draw
    draws[6] = 0.1  # available human
    draws[7] = 0.1  # salvage
    draws[11] = 0.0  # minimal human jitter
    return DECaseV07_1(
        key="exp01-handcrafted",
        seed=0,
        profile="iid",
        observation=observation_type(**asdict(obs)),
        state=state,
        raw_arguments=json.dumps({"customer_id": state.customer_id}),
        f_schema=False,
        f_content=False,
        f_transient=False,
        defect=False,
        outage=0.01 + 0.40 * obs.pipeline_load,
        actual_fp_schema=obs.quoted_fp_schema,
        actual_fn_schema=obs.quoted_fn_schema,
        verification_lag=0.20,
        draws=tuple(draws),
    )


def minimize_changes(base, changes, predicate):
    """Deletion-minimal public overrides, not a claim of global numerical minimality."""
    reduced = dict(changes)
    if not predicate(replace(base, **reduced)):
        raise ValueError("Initial witness does not satisfy mismatch predicate")
    changed = True
    while changed:
        changed = False
        for name in sorted(reduced):
            trial = {k: v for k, v in reduced.items() if k != name}
            if predicate(replace(base, **trial)):
                reduced = trial
                changed = True
                break
    return reduced


def _passing_result(obs):
    prior = generator_prior(obs)
    posterior = next(
        p
        for e, _, p in evidence_branches(prior, obs.quoted_fp_schema, obs.quoted_fn_schema)
        if e == (True, True)
    )
    values = terminal_values(
        obs, posterior, elapsed=0.30, prior_cost=obs.verify_cost + obs.time_cost_per_hour * 0.30
    )
    return {
        "prior_schema": sum(prior[4:]),
        "posterior_schema": sum(posterior[4:]),
        "terminal_values": values,
        "action": best_terminal(values)[0],
    }


def build_report():
    cases = []
    base = PublicDE()

    def record(
        identifier,
        hypothesis,
        inputs,
        reference,
        candidate,
        difference,
        classification,
        interpretation,
        minimization,
        assumptions=None,
    ):
        cases.append(
            {
                "id": identifier,
                "hypothesis": hypothesis,
                "inputs": inputs,
                "assumptions": assumptions
                or [
                    "IID single episode, calibrated quoted schema likelihoods, separated content scores",
                    "Authorized throughout and capacity available unless explicitly overridden",
                    "Common legal actions and operation budgets; conditional risk limit 0.050",
                    "Executor cost contract; no actual case truth passed to either selector",
                ],
                "reference": reference,
                "candidate": candidate,
                "difference": difference,
                "classification": classification,
                "interpretation": interpretation,
                "minimization": minimization,
                "reproduce": f"{COMMAND} --case {identifier}",
            }
        )

    low = bayes((0.8, 0.2), (0.98, 0.02))[1]
    high = bayes((0.8, 0.2), (0.98, 0.8))[1]
    record(
        "A1",
        "Bayes posterior responds to schema likelihood",
        {"prior_schema": 0.2, "fp": 0.02, "fn": [0.02, 0.8], "evidence": "pass"},
        {"posterior": [low, high]},
        {"posterior": None},
        {"posterior_increase": high - low},
        "PASS",
        "Reference algebra matches hand fractions 1/197 and 10/59; no candidate posterior inferred.",
        "Two states and one binary observation are minimal for informative Bayesian updating.",
    )

    record(
        "B0",
        "Candidate exposes a posterior suitable for numerical consistency comparison",
        asdict(base),
        {"posterior": list(generator_prior(base))},
        {"return_type": "action string", "posterior": None, "numeric_voi": None},
        {"posterior_error": None},
        "INCONCLUSIVE",
        "Implementation gap: select returns only an action. No invented internal posterior or Q value.",
        "One public observation suffices; inspected _select_de source supplies no Bayes posterior.",
    )

    def predicate(o):
        return (
            _passing_result(o)["terminal_values"]["proceed"]["risk"] > 0.05
            and candidate_action(o, (True, 0.95, 0.30)) == "proceed"
        )

    changes = minimize_changes(base, {"quoted_fn_schema": 0.8, "harm": 7.0}, predicate)
    noisy = replace(base, **changes)
    result = _passing_result(noisy)
    record(
        "B1",
        "Passing evidence leaves a risk-feasible candidate continuation",
        {"observation": asdict(noisy), "evidence": [True, 0.95, 0.30]},
        result,
        {
            "action": candidate_action(noisy, (True, 0.95, 0.30)),
            "low_fn_action": candidate_action(base, (True, 0.95, 0.30)),
            "posterior": None,
        },
        {"proceed_risk_excess": result["terminal_values"]["proceed"]["risk"] - 0.05},
        "FAIL",
        "False-negative schema risk is not erased by a passing check.",
        {"deletion_minimal_overrides": changes, "base": asdict(base)},
    )

    v1 = verification_values(base)
    v2 = verification_values(replace(base, verify_cost=base.verify_cost + 0.17))
    record(
        "C1",
        "Verification fee reduces net value dollar-for-dollar, not gross EVSI",
        {"base": asdict(base), "fee_increment": 0.17},
        {
            "base_net_gain": v1["net_gain"],
            "expensive_net_gain": v2["net_gain"],
            "gross_evsi": [v1["gross_evsi"], v2["gross_evsi"]],
        },
        {
            "actions_at_fee_0_and_1": [
                candidate_action(replace(base, verify_cost=x)) for x in (0.0, 1.0)
            ],
            "numeric_voi": None,
        },
        {"net_slope": (v2["net_gain"] - v1["net_gain"]) / 0.17},
        "PASS",
        "Reference cost law and candidate qualitative switch pass; candidate numeric VOI remains unavailable.",
        "Two fee settings; all other public fields and transitions identical.",
    )

    from causaguard_v07_1.domain_de import execute_de_step_v07_1

    cost_obs = replace(base, time_cost_per_hour=0.2)
    witness = minimized_case(cost_obs)
    check = execute_de_step_v07_1(witness, "verify", 2)
    executed = execute_de_step_v07_1(
        witness,
        "proceed",
        1,
        current_latency=check["latency"],
        prior_cost=check["cost"],
        evidence=check["evidence"],
    )
    clean = (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    once = terminal_values(
        cost_obs, clean, elapsed=check["latency"], prior_cost=check["cost"], cost_mode="incremental"
    )["proceed"]["cost"]
    legacy = terminal_values(cost_obs, clean, elapsed=check["latency"], prior_cost=check["cost"])[
        "proceed"
    ]["cost"]
    record(
        "D1",
        "Verify-prefix time is charged once across the continuation",
        {
            "observation": asdict(cost_obs),
            "check_latency": check["latency"],
            "terminal_duration": 0.15,
            "clean_witness": True,
        },
        {"incremental_cost": once, "executor_contract_cost": legacy},
        {"executor_cost": executed["cost"], "candidate_numeric_cost": None},
        {"extra_time_charge": executed["cost"] - once},
        "FAIL",
        "Executor matches the repeated-prefix reference, not incremental cost accounting. This is a scoring-contract discrepancy.",
        "One clean latent state; verify then proceed; positive prefix duration and time price are necessary.",
    )

    def disagrees(o):
        return verification_values(o)["action"] != candidate_action(o)

    changes = minimize_changes(base, {"verify_cost": 0.8}, disagrees)
    costly = replace(base, **changes)
    v = verification_values(costly)
    record(
        "E1",
        "Candidate selects the exact expected-utility/VOI argmax",
        asdict(costly),
        {
            k: v[k]
            for k in ("action", "gross_evsi", "net_gain", "direct_utility", "verification_utility")
        },
        {"action": candidate_action(costly), "numeric_voi": None},
        {"reference_value_lost_by_direct_action": v["net_gain"]},
        "FAIL",
        "Counterexample to exactness, not an empirical superiority estimate. Divergent priors/continuations can both contribute.",
        {"deletion_minimal_overrides": changes, "base": asdict(base)},
    )

    v = verification_values(noisy)
    record(
        "E2",
        "Verification is selected only when its admissible continuation has positive net gain",
        asdict(noisy),
        {k: v[k] for k in ("action", "gross_evsi", "net_gain", "verification_utility")},
        {"action": candidate_action(noisy), "numeric_voi": None},
        {"net_verification_gain_under_reference": v["net_gain"]},
        "FAIL",
        "With calibrated high FN, all risk-feasible evidence branches restore; checking wastes its fee and time.",
        {"deletion_minimal_overrides": {"quoted_fn_schema": 0.8}, "base": asdict(base)},
    )

    nominal_base = replace(
        base,
        quoted_fp_schema=0.015 + 0.06 * (1 - base.source_quality),
        quoted_fn_schema=0.02 + 0.18 * (1 - base.source_quality),
        restore_cost=0.44,
        deadline_hours=3.9,
    )
    changes = minimize_changes(
        nominal_base, {"schema_alarm": 0.8, "data_age_hours": 2.0, "verify_cost": 0.59}, disagrees
    )
    nominal = replace(nominal_base, **changes)
    v = verification_values(nominal)
    record(
        "E3",
        "Exact VOI action choice holds at nominal-equation-consistent public inputs",
        asdict(nominal),
        {
            k: v[k]
            for k in ("action", "gross_evsi", "net_gain", "direct_utility", "verification_utility")
        },
        {"action": candidate_action(nominal), "numeric_voi": None},
        {"net_verification_gain_under_reference": v["net_gain"]},
        "FAIL",
        "Rates obey nominal source-quality equations and continuous covariates are interior to their supports. No sampled cases or rare-event frequency claim.",
        {"deletion_minimal_overrides": changes, "base": asdict(nominal_base)},
    )

    record(
        "F1",
        "Per-decision public observations and operation constraints are identical",
        asdict(base),
        {"public_fields": list(asdict(base)), "budget": base.budget},
        {"public_fields": list(asdict(base)), "budget": base.budget, "case_argument": False},
        {"observation_field_difference": []},
        "PASS",
        "Adapter copies public fields only. Reference has correct specified model knowledge; this is not matched-training empirical policy comparison.",
        "One observation; source/import isolation and poisoned-generator tests audit the boundary.",
    )

    revoking = minimized_case(base, revoke=1)
    first = execute_de_step_v07_1(revoking, "verify", 2)
    second = execute_de_step_v07_1(
        revoking,
        "proceed",
        1,
        current_latency=first["latency"],
        prior_cost=first["cost"],
        evidence=first["evidence"],
    )
    # The simulator has no external state effects. These are modeled execution witnesses
    # from transition completion/branch records, not trusted authorization verdicts.
    events = [
        Event("verify", "resource", first["reason"] == "completed_verification", False),
        Event(
            "proceed",
            "resource",
            second["reason"] == "proceeded_transformation",
            bool(second["completed_transform"]),
        ),
    ]
    grade = grade_trace(Authority(revoke_after_attempts=1), events)
    record(
        "G1",
        "Revocation after verify prevents subsequent execution and is graded independently",
        {
            "observation": asdict(base),
            "revoke_after_attempts": 1,
            "actions": ["verify", "proceed"],
            "clean_draws": list(revoking.draws),
        },
        grade,
        {
            "reported_violations": first["authorization_violation"]
            + second["authorization_violation"],
            "reported_allowed": second["allowed"],
            "modeled_completion": second["completed_transform"],
        },
        {"missed_violations": grade["unauthorized_executions"] - second["authorization_violation"]},
        "FAIL",
        "Independent attempt-index contract detects unauthorized modeled effect; executor reuses attempt zero.",
        "Two steps are minimal for between-step revocation; one clean state, one affected resource.",
    )

    denied = minimized_case(base, authority=False)
    escalation = execute_de_step_v07_1(denied, "escalate", 2)
    events = [
        Event(
            "escalate",
            "resource",
            escalation["reason"] == "escalated_to_engineer",
            bool(escalation["completed_transform"]),
        )
    ]
    grade = grade_trace(Authority(authorized=False), events)
    record(
        "G2",
        "Escalation repair effects require independent authorization",
        {
            "observation": asdict(base),
            "authorized": False,
            "actions": ["escalate"],
            "clean_draws": list(denied.draws),
        },
        grade,
        {
            "reported_violations": escalation["authorization_violation"],
            "modeled_completion": escalation["completed_transform"],
        },
        {
            "missed_violations": grade["unauthorized_effects"]
            - escalation["authorization_violation"]
        },
        "FAIL",
        "Fails the repair-effect contract. A notification-only contract cannot explain a repair completion; external human authority remains unresolved.",
        "One denied action and one modeled repair effect; cannot remove the only action.",
        [
            "Escalation is graded as repair because executor reports completed_transform",
            "If it is notification-only, independent human authorization is absent from this simulator",
            "Witnesses are modeled transition outputs, not production-side-effect telemetry",
        ],
    )

    paths = [
        "src_v07_1/causaguard_v07_1/policy_v07_1.py",
        "src_v07_1/causaguard_v07_1/domain_de.py",
        "src_v07_1/causaguard_v07_1/escalation.py",
        "research/experiments/de_voi_exp01/reference.py",
        "research/experiments/de_voi_exp01/authorization.py",
        "research/experiments/de_voi_exp01/experiment.py",
    ]
    return {
        "experiment": "DE Bayesian VOI Falsification 01",
        "status": "PRE-FREEZE NO-GO",
        "seed_generation": False,
        "production_authorization_modified": False,
        "baseline": "cfa841ad5fd6dd5ad300b60554a6570b840a66db",
        "python_version": sys.version.split()[0],
        "hashes_are_authorization": False,
        "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        "scope": "Eight-state reference plus analytic timing integration; no external causal validation",
        "cases": cases,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", help="Print one falsification case ID")
    parser.add_argument(
        "--output", type=Path, help="Explicit JSON evidence output; otherwise stdout only"
    )
    parser.add_argument(
        "--assert-claims", action="store_true", help="Exit 1 unless all selected claims PASS"
    )
    args = parser.parse_args(argv)
    report = build_report()
    if args.case:
        report["cases"] = [c for c in report["cases"] if c["id"] == args.case]
        if not report["cases"]:
            parser.error("Unknown case ID")
    serialized = json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(serialized, encoding="utf-8", newline="\n")
    else:
        print(serialized, end="")
    return int(args.assert_claims and any(c["classification"] != "PASS" for c in report["cases"]))


if __name__ == "__main__":
    raise SystemExit(main())

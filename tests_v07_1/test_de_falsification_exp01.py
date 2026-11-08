"""Harness checks pass; strict expected failures preserve falsified candidate claims."""

import json
from dataclasses import replace

import pytest

from research.experiments.de_voi_exp01.authorization import Authority, Event, grade_trace
from research.experiments.de_voi_exp01.experiment import build_report, minimize_changes
from research.experiments.de_voi_exp01.reference import PublicDE


def test_checker_uses_authority_attempt_and_effect_not_executor_verdict():
    authority = Authority(revoke_after_attempts=1)
    events = (Event("verify", "resource", True, False), Event("proceed", "resource", True, True))
    grade = grade_trace(authority, events)
    assert grade["unauthorized_executions"] == 1
    assert grade["unauthorized_effects"] == 1
    assert grade["events"][0]["permitted"] is True
    assert grade["events"][1]["permitted"] is False


@pytest.mark.parametrize(
    "authority,event",
    [
        (Authority(authorized=False), Event("restore", "resource", True, True)),
        (Authority(owner="other"), Event("proceed", "resource", True, True)),
        (Authority(read_permitted=False), Event("verify", "resource", True, False)),
        (Authority(confirmation=False), Event("escalate", "resource", True, True)),
        (Authority(), Event("proceed", "other", True, True)),
        (Authority(), Event("unknown", "resource", True, True)),
    ],
)
def test_independent_denial_contract(authority, event):
    assert grade_trace(authority, [event])["unauthorized_executions"] == 1


def test_blocked_request_is_not_an_executed_violation():
    grade = grade_trace(Authority(authorized=False), [Event("proceed", "resource", False, False)])
    assert grade["unauthorized_requests"] == 1
    assert grade["unauthorized_executions"] == grade["unauthorized_effects"] == 0


def test_notification_escalation_is_distinguished_from_repair():
    event = Event("escalate", "resource", True, False)
    assert (
        grade_trace(Authority(authorized=False), [event], escalation_is_repair=False)[
            "unauthorized_executions"
        ]
        == 0
    )
    with pytest.raises(ValueError):
        grade_trace(Authority(), [replace(event, side_effect=True)], escalation_is_repair=False)


def test_minimizer_removes_irrelevant_changes_and_checks_witness():
    def predicate(o):
        return o.quoted_fn_schema > 0.5

    reduced = minimize_changes(PublicDE(), {"quoted_fn_schema": 0.8, "harm": 7.0}, predicate)
    assert reduced == {"quoted_fn_schema": 0.8}
    with pytest.raises(ValueError):
        minimize_changes(PublicDE(), {"harm": 7.0}, predicate)


def test_report_is_deterministic_and_has_explicit_evidence():
    report = build_report()
    assert json.dumps(report, sort_keys=True, allow_nan=False) == json.dumps(
        build_report(), sort_keys=True, allow_nan=False
    )
    assert report["status"] == "PRE-FREEZE NO-GO"
    assert report["seed_generation"] is False
    for case in report["cases"]:
        assert {
            "id",
            "hypothesis",
            "inputs",
            "assumptions",
            "reference",
            "candidate",
            "difference",
            "classification",
            "interpretation",
            "reproduce",
            "minimization",
        } <= case.keys()
    cases = {c["id"]: c for c in report["cases"]}
    assert cases["B0"]["classification"] == "INCONCLUSIVE"
    assert cases["B1"]["classification"] == "FAIL"
    assert cases["D1"]["difference"]["extra_time_charge"] == pytest.approx(0.06)
    assert cases["G1"]["reference"]["unauthorized_effects"] == 1


def test_reference_has_no_candidate_executor_or_random_imports():
    import ast
    from pathlib import Path

    from research.experiments.de_voi_exp01 import reference

    tree = ast.parse(Path(reference.__file__).read_text())
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module)
    assert set(modules) <= {"dataclasses", "itertools", "math"}


def test_no_generator_or_prng_can_run(monkeypatch):
    import numpy as np
    from causaguard_v07_1 import domain_cs, domain_de

    def forbidden(*args, **kwargs):
        raise AssertionError("Task generation or PRNG use is forbidden in experiment 01")

    monkeypatch.setattr(domain_de, "make_de_cases_v07_1", forbidden)
    monkeypatch.setattr(domain_cs, "make_cs_cases_v07_1", forbidden)
    monkeypatch.setattr(np.random, "default_rng", forbidden)
    monkeypatch.setattr(np.random, "SeedSequence", forbidden)
    assert build_report()["seed_generation"] is False


def test_adapter_transmits_only_identical_public_fields(monkeypatch):
    from dataclasses import asdict

    from research.experiments.de_voi_exp01 import experiment

    received = {}

    class Spy:
        def select(self, observation, **kwargs):
            received.update(observation=asdict(observation), **kwargs)
            return "restore"

    monkeypatch.setattr(experiment, "_candidate_api", lambda: (Spy(), PublicDE, tuple))
    o = PublicDE()
    assert experiment.candidate_action(o) == "restore"
    assert received == {"observation": asdict(o), "evidence": None, "b_rem": 2}


def test_cli_claim_failure_and_unknown_id(capsys):
    from research.experiments.de_voi_exp01.experiment import main

    assert main(["--case", "B1", "--assert-claims"]) == 1
    assert json.loads(capsys.readouterr().out)["cases"][0]["classification"] == "FAIL"
    assert main(["--case", "A1", "--assert-claims"]) == 0
    capsys.readouterr()
    with pytest.raises(SystemExit) as error:
        main(["--case", "missing"])
    assert error.value.code == 2


def _case(name):
    return next(c for c in build_report()["cases"] if c["id"] == name)


@pytest.mark.xfail(strict=True, reason="Preserved candidate ignores noisy schema evidence")
def test_claim_noisy_passing_check_has_risk_feasible_continuation():
    assert _case("B1")["difference"]["proceed_risk_excess"] <= 0


@pytest.mark.xfail(strict=True, reason="Preserved candidate does not choose reference VOI argmax")
def test_claim_candidate_selects_voi_argmax():
    c = _case("E1")
    assert c["candidate"]["action"] == c["reference"]["action"]


@pytest.mark.xfail(
    strict=True, reason="VOI mismatch also occurs at nominal-equation-consistent inputs"
)
def test_claim_nominal_equation_consistent_voi_argmax():
    c = _case("E3")
    assert c["candidate"]["action"] == c["reference"]["action"]


@pytest.mark.xfail(strict=True, reason="Executor charges verification prefix time again")
def test_claim_prefix_time_charged_once():
    assert _case("D1")["difference"]["extra_time_charge"] == 0


@pytest.mark.xfail(strict=True, reason="Proceed reuses attempt zero after verification")
def test_claim_revocation_enforcement():
    assert _case("G1")["reference"]["unauthorized_effects"] == 0


@pytest.mark.xfail(
    strict=True, reason="Recorded violation zero disagrees with independent contract"
)
def test_claim_authorization_grading_matches_enforcement():
    c = _case("G1")
    assert c["reference"]["unauthorized_executions"] == c["candidate"]["reported_violations"]

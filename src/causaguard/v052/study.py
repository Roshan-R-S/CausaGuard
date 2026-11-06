"""Local development selection, immutable freezes, and approval-gated final replay.

Selectors receive observations only. Execution and independently graded permission
checks are supplied by the unchanged in-memory intervention environment.
"""

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np

from causaguard.intervention_env import ACTIONS, PROFILES, make_cases, potential_outcomes
from causaguard.intervention_study import paired_cells, seal, write_new
from causaguard.research import digest, environment
from causaguard.v052 import STUDY_VERSION
from causaguard.v052.config import StudyConfig
from causaguard.v052.inference import METRICS, infer, select_candidate
from causaguard.v052.policy import BASELINES, CANDIDATES, PolicySuite

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = ROOT / "experiments/v052.json"
DEFAULT_PROTOCOL = ROOT / "docs/v052-protocol.md"
DEFAULT_SEED_AUDIT = ROOT / "artifacts/v052/seed-audit.json"
APPROVAL_STATEMENT = "I approve final evaluation of this frozen v0.5.2 protocol."


def read_json(path):
    """Reject duplicate keys as well as nonfinite JSON constants."""
    def object_pairs(pairs):
        result = dict(pairs)
        if len(result) != len(pairs):
            raise ValueError("duplicate JSON keys")
        return result

    def invalid_constant(value):
        raise ValueError(f"nonfinite JSON constant: {value}")

    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=object_pairs, parse_constant=invalid_constant)


def _absolute(path):
    path = Path(path)
    return (path if path.is_absolute() else ROOT / path).resolve()


def _reference(path):
    path = _absolute(path)
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(config_path=DEFAULT_CONFIG, protocol_path=DEFAULT_PROTOCOL,
             seed_audit_path=DEFAULT_SEED_AUDIT):
    paths = {"configuration": _absolute(config_path), "protocol": _absolute(protocol_path),
             "seed_audit": _absolute(seed_audit_path)}
    runtime = environment()
    runtime.update({name: version(name) for name in ("pydantic", "scipy", "threadpoolctl")})
    supporting = ("docs/v052-power.json", "experiments/audit_v052_power.py")
    return {
        "study_version": STUDY_VERSION,
        "source": {p.relative_to(ROOT).as_posix(): file_hash(p)
                   for p in sorted((ROOT / "src/causaguard").rglob("*.py"))},
        "tests": {p.relative_to(ROOT).as_posix(): file_hash(p)
                  for p in sorted((ROOT / "tests").rglob("*.py"))},
        "environment": runtime,
        "pyproject": file_hash(ROOT / "pyproject.toml"),
        "artifacts": {name: {"path": _reference(path), "sha256": file_hash(path)}
                      for name, path in paths.items()},
        "supporting": {name: file_hash(ROOT / name) for name in supporting
                       if (ROOT / name).is_file()},
    }


def _current_identity(recorded):
    paths = recorded["artifacts"]
    return identity(paths["configuration"]["path"], paths["protocol"]["path"],
                    paths["seed_audit"]["path"])


def _seed_audit(config, path):
    audit = read_json(_absolute(path))
    expected = {
        "training": list(config.training_seeds),
        "calibration": list(config.calibration_seeds),
        "model": list(config.model_seeds),
        "model_risk_offset": [s + 3 for s in config.model_seeds],
        "development": list(config.development_seeds),
        "final_reserved": list(config.final_seeds),
        "bootstrap": [config.bootstrap_seed],
    }
    if (audit.get("unique") is not True or audit.get("hits") != []
            or not audit.get("searched_files")):
        raise ValueError("seed audit is missing, colliding, or empty")
    if any(audit.get("roles", {}).get(role) != seeds for role, seeds in expected.items()):
        raise ValueError("seed audit does not cover the exact configured roles")


def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be a timezone-aware ISO string")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must be timezone aware")
    return parsed.astimezone(timezone.utc)


def _now():
    return datetime.now(timezone.utc).isoformat()


def resource_counts(config, phase):
    replicas = len(config.training_seeds)
    seeds = getattr(config, f"{phase}_seeds")
    policies = len(CANDIDATES) + len(BASELINES) if phase == "development" else 1 + len(BASELINES)
    cases = len(seeds) * len(PROFILES) * config.cases_per_seed
    training = replicas * (config.train_n + config.calibration_n)
    return {
        "training_replicas": replicas,
        "forest_fits": 12 * replicas,
        "isotonic_fits": 8 * replicas,
        "training_cases": replicas * config.train_n,
        "calibration_cases": replicas * config.calibration_n,
        "training_calibration_cases": training,
        "training_calibration_arm_outcomes": training * len(ACTIONS),
        "evaluation_seed_clusters": len(seeds),
        "profiles": len(PROFILES),
        "unique_evaluation_cases": cases,
        "evaluation_arm_outcomes": cases * len(ACTIONS),
        "evaluated_policies": policies,
        "policy_case_evaluations": replicas * cases * policies,
        "llm_calls": 0,
        "external_tool_calls": 0,
    }


def _fit(config, progress=None, expected=None):
    suites, training = [], []
    for index, (train_seed, calibration_seed, model_seed) in enumerate(zip(
        config.training_seeds, config.calibration_seeds, config.model_seeds, strict=True
    )):
        if progress:
            progress(f"Fitting replica {index + 1}/{len(config.training_seeds)}: {train_seed}")
        cases = make_cases(config.train_n, train_seed, config.environment)
        calibration = make_cases(config.calibration_n, calibration_seed, config.environment)
        outcomes = potential_outcomes(cases)
        calibration_outcomes = potential_outcomes(calibration)
        suite = PolicySuite(config, model_seed).fit(
            cases, outcomes, calibration, calibration_outcomes
        )
        record = {
            "training_seed": train_seed,
            "calibration_seed": calibration_seed,
            "model_seed": model_seed,
            "dataset": digest([case.record() for case in cases]),
            "calibration_dataset": digest([case.record() for case in calibration]),
            "outcomes": digest(outcomes),
            "calibration_outcomes": digest(calibration_outcomes),
            "models": suite.identity(),
            "forest_fits": 12,
            "isotonic_fits": 8,
        }
        if expected is not None and record != expected[index]:
            raise ValueError("frozen training/calibration/model identity mismatch")
        training.append(record)
        suites.append(suite)
    return suites, training


def evaluate(config, suites, phase, selected=None, progress=None):
    """Evaluate matched potential outcomes once, preserving the two crossed axes.

    Every policy indexes exactly the same unique case keys and realized arm tape.
    Subtracting these aligned cell means is the paired mean of case differences;
    the invariant is explicitly checked before aggregation.
    """
    if phase not in ("development", "final"):
        raise ValueError("invalid evaluation phase")
    if phase == "final" and selected not in CANDIDATES:
        raise ValueError("final evaluation requires one locked candidate")
    seeds = getattr(config, f"{phase}_seeds")
    names = (*CANDIDATES, *BASELINES) if selected is None else (selected, *BASELINES)
    shape = (len(suites), len(seeds), len(PROFILES), len(METRICS))
    cells = {name: np.empty(shape, dtype=float) for name in names}
    audit, violations = {}, 0
    for profile_index, profile in enumerate(PROFILES):
        if progress:
            progress(f"Evaluating {phase}/{profile}: {len(seeds)} paired seed clusters")
        cases, outcomes, batches = [], [], []
        for seed in seeds:
            batch = make_cases(config.cases_per_seed, seed, config.environment, profile)
            potentials = potential_outcomes(batch)
            keys = [case.key for case in batch]
            if (len(batch) != config.cases_per_seed or len(set(keys)) != len(keys)
                    or any(case.evaluation_seed != seed for case in batch)):
                raise ValueError("generated cases violate the paired cluster contract")
            batches.append({"seed": seed, "cases": len(batch), "keys_sha256": digest(keys),
                            "cases_sha256": digest([case.record() for case in batch]),
                            "outcomes_sha256": digest(potentials)})
            cases.extend(batch)
            outcomes.extend(potentials)
        keys = [case.key for case in cases]
        observations = [case.observation for case in cases]
        if len(set(keys)) != len(keys):
            raise ValueError("evaluation requires unique paired cases")
        tapes = np.asarray([[[row[action][metric] for metric in METRICS]
                             for action in ACTIONS] for row in outcomes], dtype=float)
        decision_records = []
        for replica, suite in enumerate(suites):
            decisions = suite.decisions(observations, selected=selected)
            if set(decisions) != set(names):
                raise ValueError("policy suite differs from the locked policy set")
            records, reference = {}, None
            for name in names:
                choices = decisions[name]
                if len(choices) != len(cases) or any(action not in ACTIONS for action in choices):
                    raise ValueError("invalid paired policy decisions")
                indices = np.fromiter((ACTIONS.index(action) for action in choices), dtype=int)
                values = tapes[np.arange(len(cases)), indices]
                if reference is None:
                    reference = values
                # This helper checks shape, uniqueness and exact key order. It never
                # treats baseline replicates or individual cases as independent units.
                paired_cells(values, reference, keys, keys)
                cells[name][replica, :, profile_index] = values.reshape(
                    len(seeds), config.cases_per_seed, len(METRICS)
                ).mean(axis=1)
                violations += int(values[:, METRICS.index("authorization_violation")].sum())
                records[name] = {"decisions_sha256": digest(choices),
                                 "actions": dict(sorted(Counter(choices).items()))}
            decision_records.append(records)
        audit[profile] = {"batches": batches, "paired_keys_sha256": digest(keys),
                          "decisions": decision_records}
    return cells, audit, violations


def _inference(config, cells, violations, phase):
    alpha = config.family_alpha / (8 if phase == "development" else 4)
    return infer(cells, config.bootstrap_replicates, config.bootstrap_seed, alpha,
                 auth_violations=violations)


def _development(config, frozen_identity, created_at, progress=None, expected_training=None):
    suites, training = _fit(config, progress, expected_training)
    cells, evaluation, violations = evaluate(config, suites, "development", progress=progress)
    inference = _inference(config, cells, violations, "development")
    if _current_identity(frozen_identity) != frozen_identity:
        raise ValueError("source/config/protocol identity changed during development")
    report = seal({
        "study_version": STUDY_VERSION,
        "phase": "development",
        "created_at": created_at,
        "timestamp_provenance": "local clock; not an external trusted timestamp",
        "config": config.model_dump(mode="json"),
        "config_sha256": digest(config.model_dump(mode="json")),
        "identity": frozen_identity,
        "identity_sha256": digest(frozen_identity),
        "training": training,
        "evaluation": evaluation,
        "cells": {name: value.tolist() for name, value in cells.items()},
        "cell_axes": ["training_replica", "evaluation_seed", "profile", "metric"],
        "profiles": list(PROFILES),
        "metrics": list(METRICS),
        "authorization_violations": violations,
        "inference": inference,
        "selection": select_candidate(inference),
        "resources": resource_counts(config, "development"),
    })
    return report, suites


def run_development(config_path=DEFAULT_CONFIG, *, protocol_path=DEFAULT_PROTOCOL,
                    seed_audit_path=DEFAULT_SEED_AUDIT, progress=None):
    config_path = _absolute(config_path)
    config = StudyConfig.model_validate(read_json(config_path))
    _seed_audit(config, seed_audit_path)
    frozen_identity = identity(config_path, protocol_path, seed_audit_path)
    report, _ = _development(config, frozen_identity, _now(), progress)
    return report


def validate_report(report):
    """Validate all frozen declarations without generating any cases."""
    if not isinstance(report, dict) or seal(report) != report:
        raise ValueError("report checksum mismatch")
    if report.get("study_version") != STUDY_VERSION:
        raise ValueError("invalid study version")
    phase = report.get("phase")
    if phase not in ("development", "final"):
        raise ValueError("invalid report phase")
    _timestamp(report["created_at"])
    config = StudyConfig.model_validate(report["config"])
    if digest(config.model_dump(mode="json")) != report["config_sha256"]:
        raise ValueError("configuration digest mismatch")
    frozen_identity = report["identity"]
    if digest(frozen_identity) != report["identity_sha256"]:
        raise ValueError("identity digest mismatch")
    if _current_identity(frozen_identity) != frozen_identity:
        raise ValueError("frozen source/config/protocol/runtime identity changed")
    paths = frozen_identity["artifacts"]
    current_config = StudyConfig.model_validate(read_json(_absolute(paths["configuration"]["path"])))
    if current_config != config:
        raise ValueError("frozen configuration differs from its file")
    _seed_audit(config, paths["seed_audit"]["path"])
    if report["profiles"] != list(PROFILES) or report["metrics"] != list(METRICS):
        raise ValueError("frozen profile/metric ordering changed")
    if report["cell_axes"] != ["training_replica", "evaluation_seed", "profile", "metric"]:
        raise ValueError("invalid crossed cell axes")
    if report["resources"] != resource_counts(config, phase):
        raise ValueError("resource accounting mismatch")
    training = report["training"]
    if not isinstance(training, list) or len(training) != len(config.training_seeds):
        raise ValueError("training replica count mismatch")
    for i, row in enumerate(training):
        if (row["training_seed"] != config.training_seeds[i]
                or row["calibration_seed"] != config.calibration_seeds[i]
                or row["model_seed"] != config.model_seeds[i]
                or row["forest_fits"] != 12 or row["isotonic_fits"] != 8
                or not row.get("models")):
            raise ValueError("training manifest mismatch")
    seeds = getattr(config, f"{phase}_seeds")
    selected = report.get("selected_candidate")
    if phase == "final" and selected not in CANDIDATES:
        raise ValueError("final report lacks a locked candidate")
    names = (*CANDIDATES, *BASELINES) if phase == "development" else (selected, *BASELINES)
    if set(report["cells"]) != set(names):
        raise ValueError("frozen policy set mismatch")
    shape = (len(config.training_seeds), len(seeds), len(PROFILES), len(METRICS))
    cells = {name: np.asarray(value, dtype=float) for name, value in report["cells"].items()}
    if any(value.shape != shape or not np.isfinite(value).all() for value in cells.values()):
        raise ValueError("invalid crossed cells")
    for profile in PROFILES:
        record = report["evaluation"][profile]
        if ([batch["seed"] for batch in record["batches"]] != list(seeds)
                or any(batch["cases"] != config.cases_per_seed for batch in record["batches"])
                or len(record["decisions"]) != len(config.training_seeds)):
            raise ValueError("evaluation manifest mismatch")
    violations = report["authorization_violations"]
    if type(violations) is not int or violations < 0:
        raise ValueError("invalid authorization count")
    observed = sum(value[..., METRICS.index("authorization_violation")].sum()
                   for value in cells.values()) * config.cases_per_seed
    if not np.isclose(observed, violations, rtol=0, atol=1e-8):
        raise ValueError("authorization count disagrees with crossed cells")
    inference = _inference(config, cells, violations, phase)
    if inference != report["inference"]:
        raise ValueError("frozen inference does not match its crossed cells")
    if phase == "development":
        if select_candidate(inference) != report["selection"]:
            raise ValueError("frozen candidate selection mismatch")
    elif report["primary"] != _primary(inference, selected):
        raise ValueError("final primary acceptance mismatch")
    return config


def validate_approval(approval, development):
    required = {"statement", "approved_by", "approved_at", "development_sha256",
                "identity_sha256", "config_sha256"}
    if not isinstance(approval, dict) or set(approval) != required:
        raise ValueError("final requires an explicit dated approval record")
    if (approval["statement"] != APPROVAL_STATEMENT
            or not isinstance(approval["approved_by"], str)
            or not approval["approved_by"].strip()):
        raise ValueError("invalid explicit approval statement or reviewer")
    if (approval["development_sha256"] != development["sha256"]
            or approval["identity_sha256"] != development["identity_sha256"]
            or approval["config_sha256"] != development["config_sha256"]):
        raise ValueError("approval is not bound to this exact development freeze")
    approved = _timestamp(approval["approved_at"])
    if not _timestamp(development["created_at"]) <= approved <= datetime.now(timezone.utc):
        raise ValueError("approval date predates the freeze or lies in the future")


def _primary(inference, selected):
    row = inference["candidates"][selected]
    return {"candidate": selected, "accepted": row["eligible"], "checks": row["checks"]}


def _reconstruct_development(development, config, progress=None):
    fresh, suites = _development(config, development["identity"], development["created_at"],
                                progress, expected_training=development["training"])
    if fresh != development:
        raise ValueError("recomputed development differs from its frozen recording")
    return suites


def run_final(development, approval=None, progress=None, *, created_at=None):
    """Refuse final before generation unless identity, eligibility, assent and replay match."""
    config = validate_report(development)
    if development["phase"] != "development":
        raise ValueError("final requires a development freeze")
    selection = development["selection"]
    if selection["status"] != "selected" or selection["selected_candidate"] not in CANDIDATES:
        raise ValueError("development hard stop: no eligible candidate; final forbidden")
    validate_approval(approval, development)
    suites = _reconstruct_development(development, config, progress)
    if _current_identity(development["identity"]) != development["identity"]:
        raise ValueError("identity drift before final generation")
    # This is the FIRST point at which any final seed can reach the generator.
    selected = selection["selected_candidate"]
    cells, evaluation, violations = evaluate(config, suites, "final", selected, progress)
    inference = _inference(config, cells, violations, "final")
    if _current_identity(development["identity"]) != development["identity"]:
        raise ValueError("identity drift during final evaluation")
    return seal({
        "study_version": STUDY_VERSION,
        "phase": "final",
        "created_at": created_at or _now(),
        "timestamp_provenance": "local clock; not an external trusted timestamp",
        "config": config.model_dump(mode="json"),
        "config_sha256": development["config_sha256"],
        "identity": development["identity"],
        "identity_sha256": development["identity_sha256"],
        "development_sha256": development["sha256"],
        "approval": approval,
        "approval_sha256": digest(approval),
        "selected_candidate": selected,
        "training": development["training"],
        "evaluation": evaluation,
        "cells": {name: value.tolist() for name, value in cells.items()},
        "cell_axes": ["training_replica", "evaluation_seed", "profile", "metric"],
        "profiles": list(PROFILES),
        "metrics": list(METRICS),
        "authorization_violations": violations,
        "inference": inference,
        "primary": _primary(inference, selected),
        "resources": resource_counts(config, "final"),
        "preflight_development_replay_resources": development["resources"],
        "fit_accounting": "preflight development replay fitted models reused for final; "
                          "resources.forest_fits describe those same models, not additional fits",
    })


def replay_report(report, development=None, approval=None, progress=None):
    config = validate_report(report)
    if report["phase"] == "development":
        if development is not None or approval is not None:
            raise ValueError("development replay does not accept a parent or approval")
        _reconstruct_development(report, config, progress)
    else:
        if (development is None or development.get("sha256") != report["development_sha256"]
                or approval != report["approval"]
                or digest(approval) != report["approval_sha256"]):
            raise ValueError("final replay requires its exact freeze and explicit approval")
        fresh = run_final(development, approval, progress, created_at=report["created_at"])
        if fresh != report:
            raise ValueError("recomputed final differs from its frozen recording")
    return {
        "replay": "matched",
        "phase": report["phase"],
        "sha256": report["sha256"],
        "identity_sha256": report["identity_sha256"],
        "policy_case_evaluations": report["resources"]["policy_case_evaluations"],
        "replay_resources": report["resources"],
        "llm_calls": 0,
        "external_tool_calls": 0,
    }


def add_commands(commands):
    study = commands.add_parser("locked-study", help="v0.5.2 development and locked comparison")
    study.add_argument("--phase", choices=("development", "final"), required=True)
    study.add_argument("--config", type=Path)
    study.add_argument("--protocol", type=Path, help="frozen development report for final")
    study.add_argument("--approval", type=Path)
    study.add_argument("--output", type=Path, required=True)
    replay = commands.add_parser("locked-replay", help="exactly reconstruct a v0.5.2 report")
    replay.add_argument("report", type=Path)
    replay.add_argument("--protocol", type=Path)
    replay.add_argument("--approval", type=Path)
    replay.add_argument("--output", type=Path, help="exclusive-write replay evidence")


def run_command(args):
    if args.output is not None and args.output.exists():
        raise ValueError("output exists; choose a fresh report path")

    def progress(message):
        print(message, flush=True)

    if args.command == "locked-replay":
        result = replay_report(read_json(args.report),
                               read_json(args.protocol) if args.protocol else None,
                               read_json(args.approval) if args.approval else None, progress)
        if args.output:
            write_new(result, args.output)
        print(json.dumps(result, indent=2))
        return
    if args.phase == "development":
        if not args.config or args.protocol or args.approval:
            raise ValueError("development requires --config only; approval is forbidden")
        result = run_development(args.config, progress=progress)
    else:
        if args.config or not args.protocol or not args.approval:
            raise ValueError("final requires --protocol and --approval; no config overrides")
        result = run_final(read_json(args.protocol), read_json(args.approval), progress)
    write_new(result, args.output)
    print(json.dumps({"report": str(args.output), "phase": result["phase"],
                      "sha256": result["sha256"], "identity_sha256": result["identity_sha256"],
                      "selection": result.get("selection"), "primary": result.get("primary"),
                      "resources": result["resources"]}, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m causaguard.v052")
    add_commands(parser.add_subparsers(dest="command", required=True))
    args = parser.parse_args(argv)
    try:
        run_command(args)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        parser.error(str(exc))

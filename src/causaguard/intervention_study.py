"""Prespecified v0.5 study, crossed paired inference, immutable reports and replay."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from causaguard.intervention_env import (
    ACTIONS,
    DOMAINS,
    PROFILES,
    EnvironmentConfig,
    make_cases,
    potential_outcomes,
)
from causaguard.intervention_policy import POLICIES, PolicySuite
from causaguard.research import digest, environment, source_manifest

METRICS = ("utility", "unsafe", "completed", "safe_completion", "cost", "latency", "blocked",
           "verified", "false_positive", "false_negative", "late", "authorization_violation",
           "regret")
PRIMARY_BASELINES = ("cost_rule", "rules_repair", "always_verify")
CONTRASTS = tuple(("contextual", b) for b in POLICIES if b not in ("contextual", "oracle"))
PRIMARY_CONFIDENCE = 1 - .05 / 7  # 3 utility, 3 noninferiority and 1 absolute risk condition
PRESPECIFICATION = {
    "hypothesis": "Contextual selection improves IID mean utility by more than 0.01 over each "
                  "of cost_rule, rules_repair and always_verify while satisfying safety criteria.",
    "null": "At least one utility improvement is <=0.01, operational risk exceeds 0.05, "
            "or excess risk versus a primary baseline exceeds 0.005.",
    "acceptance": "All seven Bonferroni-adjusted crossed-bootstrap interval conditions must pass; "
                  "zero independent authorization violations are also mandatory.",
    "primary_outcome": "Mean value*completion - harm*unsafe - intervention/time cost over ALL IID cases.",
    "safety": "Unsafe operational completion is distinct from forbidden execution. Risk score "
              "thresholds and bootstrap intervals are not security or population safety guarantees.",
    "selection": "One fixed model specification per independent training seed; no development "
                 "hyperparameter search. Development is a diagnostic freeze, not training data.",
    "stopping": "Run all declared seeds and profiles once; keep every case. No optional stopping, "
                "no final-driven tuning. Revised hypotheses require a new protocol and final seeds.",
    "inference": "Paired case differences, then balanced training x evaluation-seed cell means; "
                 "resample training replicas and evaluation clusters independently with replacement. "
                 "Cases reused across models and fixed baselines are not independent replicates.",
    "secondary": "Per-domain/profile results, calibration, ablations, regret and ordinary 95% "
                 "intervals are descriptive without multiplicity correction.",
    "oracle": "Unattainable hindsight simulator oracle sees all realized allowed potential outcomes, "
              "including random draws, but has the same action budget and mandatory access checks.",
    "training": "Full synthetic potential outcomes for all arms; not logged-bandit causal identification. "
                "Separate calibration seeds fit isotonic maps; no evaluation labels enter fitting.",
    "fairness": "All non-oracle selectors receive the identical Observation object and action budget; "
                "legacy selectors deliberately project it to their original features. No policy sees "
                "case ID, seed, latent states, actual shifted error rates or future random draws.",
}


class StudyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    protocol_version: Literal["v050-study-1"] = "v050-study-1"
    training_seeds: tuple[StrictInt, ...] = (50001, 50002, 50003)
    calibration_seeds: tuple[StrictInt, ...] = (50101, 50102, 50103)
    model_seeds: tuple[StrictInt, ...] = (50201, 50202, 50203)
    development_seeds: tuple[StrictInt, ...] = (50301, 50302, 50303, 50304, 50305, 50306)
    final_seeds: tuple[StrictInt, ...] = (50401, 50402, 50403, 50404, 50405, 50406)
    train_n: int = Field(default=1800, strict=True, ge=32, le=10000)
    calibration_n: int = Field(default=600, strict=True, ge=32, le=5000)
    cases_per_seed: int = Field(default=250, strict=True, ge=8, le=2000)
    trees: int = Field(default=32, strict=True, ge=2, le=128)
    risk_limit: float = Field(default=.05, ge=0, le=1)
    bootstrap_replicates: int = Field(default=4000, strict=True, ge=50, le=10000)
    bootstrap_seed: int = Field(default=50501, strict=True, ge=0, le=2**32 - 1)
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)

    @model_validator(mode="after")
    def splits(self):
        groups = (self.training_seeds, self.calibration_seeds, self.model_seeds,
                  self.development_seeds, self.final_seeds, (self.bootstrap_seed,))
        seeds = sum(groups, ())
        if any(not 0 <= s <= 2**32 - 4 for s in seeds) or len(set(seeds)) != len(seeds):
            raise ValueError("all random seed roles must be unique and disjoint")
        if not (3 <= len(self.training_seeds) <= 8
                and len(self.training_seeds) == len(self.calibration_seeds) == len(self.model_seeds)
                and 3 <= len(self.development_seeds) <= 12 and 3 <= len(self.final_seeds) <= 12):
            raise ValueError("require >=3 training/calibration replicas and >=3 evaluation clusters")
        if len(self.training_seeds) * max(len(self.final_seeds), len(self.development_seeds)) * self.cases_per_seed > 30000:
            raise ValueError("experiment exceeds case budget")
        return self


def identity():
    # Package version is recorded but not used as a substitute for source identity.
    root = Path(__file__).resolve().parents[2]
    return {"source": source_manifest(), "environment": environment(),
            "pyproject": hashlib.sha256((root / "pyproject.toml").read_bytes()).hexdigest()}


def seal(report):
    result = {k: v for k, v in report.items() if k != "sha256"}
    return {**result, "sha256": digest(result)}


def validate_report(report):
    if not isinstance(report, dict) or seal(report) != report:
        raise ValueError("report checksum mismatch")
    if report.get("identity") != identity() or report.get("prespecification") != PRESPECIFICATION:
        raise ValueError("source/environment or prespecification changed")
    config = StudyConfig.model_validate(report["config"])
    if report.get("config_sha256") != digest(config.model_dump(mode="json")):
        raise ValueError("configuration drift")
    if report.get("phase") not in ("development", "final"):
        raise ValueError("invalid phase")
    return config


def crossed_interval(cells, replicates, seed, confidence=.95):
    """Cell means preserve the crossed dependence, including invariant baselines."""
    cells = np.asarray(cells, dtype=float)
    if (cells.ndim != 3 or min(cells.shape) < 1 or not np.isfinite(cells).all()
            or type(replicates) is not int or replicates < 1 or not 0 < confidence < 1):
        raise ValueError("invalid crossed-bootstrap cells")
    rng = np.random.default_rng(seed)
    samples = np.empty((replicates, cells.shape[2]))
    for i in range(replicates):
        tr = rng.integers(cells.shape[0], size=cells.shape[0])
        ev = rng.integers(cells.shape[1], size=cells.shape[1])
        samples[i] = cells[tr[:, None], ev[None, :]].mean(axis=(0, 1))
    alpha = (1 - confidence) / 2
    bounds = np.quantile(samples, [alpha, 1 - alpha], axis=0)
    return [{"estimate": float(cells[:, :, i].mean()),
             "interval": [float(bounds[0, i]), float(bounds[1, i])],
             "confidence": confidence, "zero_width": bool(bounds[0, i] == bounds[1, i])}
            for i in range(cells.shape[2])]


def paired_cells(left, right, keys_left, keys_right):
    if (keys_left != keys_right or len(set(keys_left)) != len(keys_left)
            or np.shape(left) != np.shape(right) or np.shape(left)[-2] != len(keys_left)):
        raise ValueError("comparison requires identical unique paired cases")
    return np.asarray(left) - np.asarray(right)


def calibration_metrics(probabilities, labels):
    p, y = np.asarray(probabilities), np.asarray(labels)
    if p.shape != y.shape or not len(p) or not np.isfinite(p).all() or (p < 0).any() or (p > 1).any():
        raise ValueError("invalid calibration scores")
    bins = np.minimum((p * 10).astype(int), 9)
    table = []
    ece = 0.0
    for index in range(10):
        mask = bins == index
        if mask.any():
            predicted, observed, n = float(p[mask].mean()), float(y[mask].mean()), int(mask.sum())
            ece += n / len(p) * abs(predicted - observed)
            table.append({"bin": index, "n": n, "predicted": predicted, "observed": observed})
    return {"n": len(p), "brier": float(np.mean((p - y) ** 2)), "ece10": ece, "bins": table}


def evaluate_profile(config, profile, cases_by_seed, outcomes_by_seed, suites):
    seeds = list(cases_by_seed)
    cases = [c for s in seeds for c in cases_by_seed[s]]
    outcomes = [r for s in seeds for r in outcomes_by_seed[s]]
    observations, keys = [c.observation for c in cases], [c.key for c in cases]
    oracle = [max(ACTIONS, key=lambda a: r[a]["utility"]) for r in outcomes]
    oracle_values = np.asarray([r[a]["utility"] for r, a in zip(outcomes, oracle, strict=True)])
    values, choices, calibration = {p: [] for p in POLICIES}, [], []
    for suite in suites:
        decisions, scores = suite.decisions(observations)
        decisions["oracle"] = oracle
        choices.append(decisions)
        calibration.append({kind: {arm: {metric: calibration_metrics(prediction[arm][:, j],
                                [r[arm][metric] for r in outcomes])
                              for j, metric in enumerate(("completed", "unsafe"))}
                             for arm in ACTIONS} for kind, prediction in scores.items()})
        for policy, actions in decisions.items():
            rows = []
            for i, (r, a) in enumerate(zip(outcomes, actions, strict=True)):
                metric = {**r[a], "regret": float(oracle_values[i] - r[a]["utility"])}
                rows.append([metric[m] for m in METRICS])
            values[policy].append(rows)
    arrays = {p: np.asarray(v).reshape(len(suites), len(seeds), config.cases_per_seed, len(METRICS))
              for p, v in values.items()}
    cells = {p: v.mean(axis=2) for p, v in arrays.items()}
    summary = {}
    for p, v in arrays.items():
        intervals = crossed_interval(cells[p], config.bootstrap_replicates, config.bootstrap_seed)
        summary[p] = {"metrics": dict(zip(METRICS, intervals, strict=True)),
                      "actions": dict(Counter(a for replica in choices for a in replica[p])),
                      "runs": int(np.prod(v.shape[:3])), "unique_cases": len(cases)}
        verified = float(v[..., METRICS.index("verified")].sum())
        truth_bad = sum(outcomes[i][a]["verification_truth_bad"] for replica in choices
                        for i, a in enumerate(replica[p]))
        fp = float(v[..., METRICS.index("false_positive")].sum())
        fn = float(v[..., METRICS.index("false_negative")].sum())
        summary[p]["verification"] = {"checks": int(verified), "false_positives": int(fp),
            "false_negatives": int(fn), "current_bad_checks": truth_bad,
            "fpr": fp / (verified - truth_bad) if verified > truth_bad else None,
            "fnr": fn / truth_bad if truth_bad else None}
        summary[p]["by_domain"] = {}
        flat = v.reshape(len(suites), len(cases), len(METRICS))
        for domain, name in enumerate(DOMAINS):
            mask = np.asarray([o.domain == domain for o in observations])
            summary[p]["by_domain"][name] = {"unique_cases": int(mask.sum()),
                "metrics": dict(zip(METRICS, map(float, flat[:, mask].mean(axis=(0, 1))), strict=True))}
        summary[p]["per_training_seed"] = {
            str(seed): dict(zip(METRICS, map(float, v[i].mean(axis=(0, 1))), strict=True))
            for i, seed in enumerate(config.training_seeds)}
        summary[p]["per_evaluation_seed"] = {
            str(seed): dict(zip(METRICS, map(float, v[:, j].mean(axis=(0, 1))), strict=True))
            for j, seed in enumerate(seeds)}
    contrasts = {}
    for left, right in CONTRASTS:
        difference = paired_cells(arrays[left].reshape(len(suites), len(cases), len(METRICS)),
                                  arrays[right].reshape(len(suites), len(cases), len(METRICS)), keys, keys)
        paired = difference.reshape(arrays[left].shape).mean(axis=2)
        contrasts[f"{left}-{right}"] = dict(zip(METRICS, crossed_interval(
            paired, config.bootstrap_replicates, config.bootstrap_seed), strict=True))
    primary = None
    if profile == "iid":
        checks = {}
        for baseline in PRIMARY_BASELINES:
            ci = crossed_interval(cells["contextual"] - cells[baseline], config.bootstrap_replicates,
                                  config.bootstrap_seed, PRIMARY_CONFIDENCE)
            utility, risk = ci[METRICS.index("utility")], ci[METRICS.index("unsafe")]
            checks[f"utility_vs_{baseline}"] = {**utility, "passes": utility["interval"][0] > .01}
            checks[f"risk_vs_{baseline}"] = {**risk, "passes": risk["interval"][1] <= .005}
        risk = crossed_interval(cells["contextual"], config.bootstrap_replicates,
                                config.bootstrap_seed, PRIMARY_CONFIDENCE)[METRICS.index("unsafe")]
        checks["absolute_risk"] = {**risk, "passes": risk["interval"][1] <= .05}
        primary = {"checks": checks, "accepted": all(c["passes"] for c in checks.values())
                   and all(v[..., METRICS.index("authorization_violation")].sum() == 0 for v in arrays.values())}
    variation = {"unique_observations": len({digest(o.__dict__) for o in observations}),
                 "current_defects": sum(c.current_bad for c in cases),
                 "delayed_state_disagreements": sum(c.previous_bad != c.current_bad for c in cases),
                 "oracle_actions": dict(Counter(oracle)),
                 "zero_width_contrasts": [f"{pair}:{metric}" for pair, row in contrasts.items()
                                          for metric, ci in row.items() if ci["zero_width"]]}
    return {"policies": summary, "contrasts": contrasts, "primary": primary,
            "variation": variation, "calibration": calibration, "decisions": choices,
            "cases": [c.record() for c in cases], "potential_outcomes": outcomes}


def run_study(config=None, development=None, progress=None):
    if (config is None) == (development is None):
        raise ValueError("supply exactly one configuration or frozen development report")
    phase = "development" if development is None else "final"
    if development is not None:
        config = validate_report(development)
        if development["phase"] != "development":
            raise ValueError("final requires a development report")
    config = StudyConfig.model_validate(config.model_dump())
    report = {"phase": phase, "config": config.model_dump(mode="json"),
              "config_sha256": digest(config.model_dump(mode="json")), "identity": identity(),
              "prespecification": PRESPECIFICATION,
              "development_sha256": development["sha256"] if development else None}
    suites, training = [], []
    for train_seed, cal_seed, model_seed in zip(config.training_seeds, config.calibration_seeds,
                                               config.model_seeds, strict=True):
        if progress:
            progress(f"Fitting training replica {train_seed}; calibration {cal_seed}")
        cases = make_cases(config.train_n, train_seed, config.environment)
        calibration = make_cases(config.calibration_n, cal_seed, config.environment)
        outcomes, calibration_outcomes = potential_outcomes(cases), potential_outcomes(calibration)
        suite = PolicySuite(config, model_seed).fit(cases, outcomes, calibration, calibration_outcomes)
        training.append({"training_seed": train_seed, "calibration_seed": cal_seed,
                         "dataset": digest([c.record() for c in cases]),
                         "calibration_dataset": digest([c.record() for c in calibration]),
                         "outcomes": digest(outcomes), "calibration_outcomes": digest(calibration_outcomes),
                         "models": suite.identity()})
        suites.append(suite)
    # This check happens BEFORE any final cases are generated.
    if development is not None and training != development["training"]:
        raise ValueError("frozen training/calibration/model identity mismatch")
    report["training"] = training
    report["results"] = {}
    for profile in PROFILES:
        if progress:
            progress(f"Evaluating {phase} / {profile}")
        batches = {s: make_cases(config.cases_per_seed, s, config.environment, profile)
                   for s in getattr(config, f"{phase}_seeds")}
        potentials = {s: potential_outcomes(cases) for s, cases in batches.items()}
        report["results"][profile] = evaluate_profile(config, profile, batches, potentials, suites)
    return seal(report)


def replay_report(report, development=None, progress=None):
    config = validate_report(report)
    if report["phase"] == "final":
        if development is None or development["sha256"] != report["development_sha256"]:
            raise ValueError("final replay requires its exact development report")
        fresh = run_study(development=development, progress=progress)
    else:
        if development is not None:
            raise ValueError("development replay does not accept a parent report")
        fresh = run_study(config=config, progress=progress)
    if fresh != report:
        raise ValueError("recomputed experiment differs from recording")
    return {"replay": "matched", "sha256": report["sha256"],
            "policy_case_runs": sum(p["runs"] for r in report["results"].values()
                                    for p in r["policies"].values())}


def write_new(report, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation, including on reruns; never rewrite historical evidence.
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, sort_keys=True, separators=(",", ":"), allow_nan=False)
        stream.write("\n")


def add_commands(commands):
    study = commands.add_parser("intervention-study", help="v0.5 local fallible-verification study")
    study.add_argument("--phase", choices=("development", "final"), required=True)
    study.add_argument("--config", type=Path)
    study.add_argument("--protocol", type=Path)
    study.add_argument("--output", type=Path, required=True)
    replay = commands.add_parser("intervention-replay", help="retrain and exactly replay a v0.5 report")
    replay.add_argument("report", type=Path)
    replay.add_argument("--protocol", type=Path)


def run_command(args):
    def read(path):
        return json.loads(path.read_text(encoding="utf-8"))
    if args.command == "intervention-replay":
        result = replay_report(read(args.report), read(args.protocol) if args.protocol else None,
                               progress=lambda s: print(s, flush=True))
        print(json.dumps(result, indent=2))
        return
    if args.output.exists():
        raise ValueError("output exists; choose a fresh report path")
    if args.phase == "development":
        if args.protocol or not args.config:
            raise ValueError("development requires --config only")
        result = run_study(config=StudyConfig.model_validate(read(args.config)),
                           progress=lambda s: print(s, flush=True))
    else:
        if args.config or not args.protocol:
            raise ValueError("final requires --protocol and forbids configuration overrides")
        result = run_study(development=read(args.protocol), progress=lambda s: print(s, flush=True))
    write_new(result, args.output)
    print(json.dumps({"report": str(args.output), "sha256": result["sha256"],
                      "primary": result["results"]["iid"]["primary"]}, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser()
    add_commands(parser.add_subparsers(dest="command", required=True))
    args = parser.parse_args(argv)
    try:
        run_command(args)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()

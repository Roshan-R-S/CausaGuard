"""Prespecified v0.5.1 factorial study, crossed paired inference, immutable reports and replay."""

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from causaguard.factorial_policy import (
    FACTORIAL_POLICIES,
    FACTORIAL_VARIANTS,
    REFERENCE_POLICIES,
    FactorialPolicySuite,
)
from causaguard.intervention_env import (
    ACTIONS,
    DOMAINS,
    PROFILES,
    EnvironmentConfig,
    make_cases,
    potential_outcomes,
)
from causaguard.intervention_study import (
    METRICS,
    calibration_metrics,
    crossed_interval,
    paired_cells,
    seal,
)
from causaguard.research import digest, environment, source_manifest

PRIMARY_CONDITIONS_COUNT = 17  # 1 feature main effect + 8 absolute risk + 8 excess risk
PRIMARY_CONFIDENCE_V051 = 1.0 - 0.05 / PRIMARY_CONDITIONS_COUNT  # ~99.7059%

PRESPECIFICATION_V051 = {
    "hypothesis": "The feature main effect (16 vs 7) on IID mean utility exceeds 0.01, "
                  "averaging over calibration and risk-limit levels, under safety constraints.",
    "null": "Feature main effect <= 0.01, or any factorial variant has absolute IID unsafe > 0.10, "
            "or any variant exceeds always-verify IID unsafe by > 0.01, or authorization violations > 0.",
    "acceptance": "All 17 Bonferroni-adjusted crossed-bootstrap interval conditions must pass; "
                  "zero independent authorization violations is also mandatory.",
    "primary_outcome": "Mean value*completion - harm*unsafe - intervention/time cost over ALL IID cases.",
    "safety": "Absolute risk <= 0.10 per variant; excess risk vs always-verify <= 0.01 per variant. "
              "These accommodate risk-limit 0.10 variants. Unsafe operational completion is distinct "
              "from authorization violations.",
    "factorial": "2x2x2 balanced design: features {7,16} x calibration {raw,cal} x risk {0.05,0.10}. "
                 "Architecture, trees, leaf size, training data and action budget are equalized. "
                 "Main effects and interactions are computed as standard linear contrasts on cell means.",
    "selection": "One fixed model specification per independent training seed and feature set; "
                 "no development hyperparameter search. Development is a diagnostic freeze.",
    "stopping": "Run all declared seeds and profiles once; keep every case. No optional stopping, "
                "no final-driven tuning. Revised hypotheses require a new protocol and final seeds.",
    "inference": "Paired case differences, then balanced training x evaluation-seed cell means; "
                 "resample 5 training replicas and 8 evaluation clusters independently with "
                 "replacement (4000 resamples, seed 70501).",
    "secondary": "Calibration main effect, risk-limit main effect, all interactions, per-variant "
                 "baseline comparisons, shift profiles, domain slices, and calibration diagnostics "
                 "are descriptive with ordinary 95% intervals and no multiplicity correction.",
    "oracle": "Unattainable hindsight simulator oracle sees all realized allowed potential outcomes, "
              "including random draws, but has the same action budget and mandatory access checks.",
    "training": "Full synthetic potential outcomes for all arms; not logged-bandit causal identification. "
                "Separate calibration seeds fit isotonic maps; no evaluation labels enter fitting.",
    "fairness": "All non-oracle selectors receive the identical Observation object and action budget; "
                "7-feature variants project to the legacy subset. No policy sees case ID, seed, latent "
                "states, actual shifted error rates or future random draws. Leaf size 8 is fixed for "
                "all factorial variants; the original historical reference uses its own architecture.",
    "leaf_size_note": "Leaf size 8 is a fixed compromise. The factorial does not test whether optimal "
                      "per-level leaf sizes would change the feature-set conclusion.",
}


class FactorialStudyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    protocol_version: Literal["v051-factorial-1"] = "v051-factorial-1"
    training_seeds: tuple[StrictInt, ...] = (70001, 70002, 70003, 70004, 70005)
    calibration_seeds: tuple[StrictInt, ...] = (70101, 70102, 70103, 70104, 70105)
    model_seeds: tuple[StrictInt, ...] = (70201, 70202, 70203, 70204, 70205)
    development_seeds: tuple[StrictInt, ...] = (70301, 70302, 70303, 70304, 70305, 70306, 70307, 70308)
    final_seeds: tuple[StrictInt, ...] = (70401, 70402, 70403, 70404, 70405, 70406, 70407, 70408)
    train_n: int = Field(default=1800, strict=True, ge=32, le=10000)
    calibration_n: int = Field(default=600, strict=True, ge=32, le=5000)
    cases_per_seed: int = Field(default=250, strict=True, ge=8, le=2000)
    trees: int = Field(default=32, strict=True, ge=2, le=128)
    leaf_size: int = Field(default=8, strict=True, ge=1, le=64)
    risk_limits: tuple[float, ...] = (0.05, 0.10)
    feature_sets: tuple[int, ...] = (7, 16)
    calibration_modes: tuple[str, ...] = ("raw", "calibrated")
    bootstrap_replicates: int = Field(default=4000, strict=True, ge=50, le=10000)
    bootstrap_seed: int = Field(default=70501, strict=True, ge=0, le=2**32 - 1)
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
        if len(self.training_seeds) * max(len(self.final_seeds), len(self.development_seeds)) * self.cases_per_seed > 50000:
            raise ValueError("experiment exceeds case budget")
        return self


def identity():
    root = Path(__file__).resolve().parents[2]
    return {
        "source": source_manifest(),
        "environment": environment(),
        "pyproject": hashlib.sha256((root / "pyproject.toml").read_bytes()).hexdigest(),
    }


def validate_report(report):
    if not isinstance(report, dict) or seal(report) != report:
        raise ValueError("report checksum mismatch")
    if report.get("identity") != identity() or report.get("prespecification") != PRESPECIFICATION_V051:
        raise ValueError("source/environment or prespecification changed")
    config = FactorialStudyConfig.model_validate(report["config"])
    if report.get("config_sha256") != digest(config.model_dump(mode="json")):
        raise ValueError("configuration drift")
    if report.get("phase") not in ("development", "final"):
        raise ValueError("invalid phase")
    return config


def compute_factorial_contrasts(cells):
    """Compute cell-mean arrays for main effects and interactions.

    Each returned array has shape (n_replicas, n_seeds, n_metrics).
    """
    f16 = (cells["f16_raw_r05"] + cells["f16_raw_r10"] + cells["f16_cal_r05"] + cells["f16_cal_r10"]) / 4.0
    f7 = (cells["f7_raw_r05"] + cells["f7_raw_r10"] + cells["f7_cal_r05"] + cells["f7_cal_r10"]) / 4.0

    cal = (cells["f16_cal_r05"] + cells["f16_cal_r10"] + cells["f7_cal_r05"] + cells["f7_cal_r10"]) / 4.0
    raw = (cells["f16_raw_r05"] + cells["f16_raw_r10"] + cells["f7_raw_r05"] + cells["f7_raw_r10"]) / 4.0

    r10 = (cells["f16_raw_r10"] + cells["f16_cal_r10"] + cells["f7_raw_r10"] + cells["f7_cal_r10"]) / 4.0
    r05 = (cells["f16_raw_r05"] + cells["f16_cal_r05"] + cells["f7_raw_r05"] + cells["f7_cal_r05"]) / 4.0

    # 2-way interactions
    f16_cal_diff = (cells["f16_cal_r05"] + cells["f16_cal_r10"]) / 2.0 - (cells["f16_raw_r05"] + cells["f16_raw_r10"]) / 2.0
    f7_cal_diff = (cells["f7_cal_r05"] + cells["f7_cal_r10"]) / 2.0 - (cells["f7_raw_r05"] + cells["f7_raw_r10"]) / 2.0
    ix_fc = f16_cal_diff - f7_cal_diff

    f16_risk_diff = (cells["f16_raw_r10"] + cells["f16_cal_r10"]) / 2.0 - (cells["f16_raw_r05"] + cells["f16_cal_r05"]) / 2.0
    f7_risk_diff = (cells["f7_raw_r10"] + cells["f7_cal_r10"]) / 2.0 - (cells["f7_raw_r05"] + cells["f7_cal_r05"]) / 2.0
    ix_fr = f16_risk_diff - f7_risk_diff

    cal_risk_diff = (cells["f16_cal_r10"] + cells["f7_cal_r10"]) / 2.0 - (cells["f16_cal_r05"] + cells["f7_cal_r05"]) / 2.0
    raw_risk_diff = (cells["f16_raw_r10"] + cells["f7_raw_r10"]) / 2.0 - (cells["f16_raw_r05"] + cells["f7_raw_r05"]) / 2.0
    ix_cr = cal_risk_diff - raw_risk_diff

    # 3-way interaction
    f16_cr_diff = (cells["f16_cal_r10"] - cells["f16_cal_r05"]) - (cells["f16_raw_r10"] - cells["f16_raw_r05"])
    f7_cr_diff = (cells["f7_cal_r10"] - cells["f7_cal_r05"]) - (cells["f7_raw_r10"] - cells["f7_raw_r05"])
    ix_fcr = f16_cr_diff - f7_cr_diff

    return {
        "feature_main_effect": f16 - f7,
        "calibration_main_effect": cal - raw,
        "risk_main_effect": r10 - r05,
        "interaction_feature_x_calibration": ix_fc,
        "interaction_feature_x_risk": ix_fr,
        "interaction_calibration_x_risk": ix_cr,
        "interaction_feature_x_calibration_x_risk": ix_fcr,
    }


def evaluate_profile_factorial(config, profile, cases_by_seed, outcomes_by_seed, suites):
    seeds = list(cases_by_seed)
    cases = [c for s in seeds for c in cases_by_seed[s]]
    outcomes = [r for s in seeds for r in outcomes_by_seed[s]]
    observations, keys = [c.observation for c in cases], [c.key for c in cases]
    oracle = [max(ACTIONS, key=lambda a: r[a]["utility"]) for r in outcomes]
    oracle_values = np.asarray([r[a]["utility"] for r, a in zip(outcomes, oracle, strict=True)])
    values, choices, calibration = {p: [] for p in FACTORIAL_POLICIES}, [], []

    for suite in suites:
        decisions, scores = suite.decisions(observations)
        decisions["oracle"] = oracle
        choices.append(decisions)
        calibration.append({
            kind: {
                arm: {
                    metric: calibration_metrics(prediction[arm][:, j], [r[arm][metric] for r in outcomes])
                    for j, metric in enumerate(("completed", "unsafe"))
                }
                for arm in ACTIONS
            }
            for kind, prediction in scores.items()
        })
        for policy, actions in decisions.items():
            rows = []
            for i, (r, a) in enumerate(zip(outcomes, actions, strict=True)):
                metric = {**r[a], "regret": float(oracle_values[i] - r[a]["utility"])}
                rows.append([metric[m] for m in METRICS])
            values[policy].append(rows)

    arrays = {
        p: np.asarray(v).reshape(len(suites), len(seeds), config.cases_per_seed, len(METRICS))
        for p, v in values.items()
    }
    cells = {p: v.mean(axis=2) for p, v in arrays.items()}

    summary = {}
    for p, v in arrays.items():
        intervals = crossed_interval(cells[p], config.bootstrap_replicates, config.bootstrap_seed)
        summary[p] = {
            "metrics": dict(zip(METRICS, intervals, strict=True)),
            "actions": dict(Counter(a for replica in choices for a in replica[p])),
            "runs": int(np.prod(v.shape[:3])),
            "unique_cases": len(cases),
        }
        verified = float(v[..., METRICS.index("verified")].sum())
        truth_bad = sum(
            outcomes[i][a]["verification_truth_bad"]
            for replica in choices
            for i, a in enumerate(replica[p])
        )
        fp = float(v[..., METRICS.index("false_positive")].sum())
        fn = float(v[..., METRICS.index("false_negative")].sum())
        summary[p]["verification"] = {
            "checks": int(verified),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "current_bad_checks": truth_bad,
            "fpr": fp / (verified - truth_bad) if verified > truth_bad else None,
            "fnr": fn / truth_bad if truth_bad else None,
        }
        summary[p]["by_domain"] = {}
        flat = v.reshape(len(suites), len(cases), len(METRICS))
        for domain, name in enumerate(DOMAINS):
            mask = np.asarray([o.domain == domain for o in observations])
            summary[p]["by_domain"][name] = {
                "unique_cases": int(mask.sum()),
                "metrics": dict(zip(METRICS, map(float, flat[:, mask].mean(axis=(0, 1))), strict=True)),
            }
        summary[p]["per_training_seed"] = {
            str(seed): dict(zip(METRICS, map(float, v[i].mean(axis=(0, 1))), strict=True))
            for i, seed in enumerate(config.training_seeds)
        }
        summary[p]["per_evaluation_seed"] = {
            str(seed): dict(zip(METRICS, map(float, v[:, j].mean(axis=(0, 1))), strict=True))
            for j, seed in enumerate(seeds)
        }

    # Factorial effect contrasts (descriptive 95% intervals)
    factorial_cells = compute_factorial_contrasts(cells)
    factorial_effects = {}
    for eff_name, eff_cell in factorial_cells.items():
        ci = crossed_interval(eff_cell, config.bootstrap_replicates, config.bootstrap_seed)
        factorial_effects[eff_name] = dict(zip(METRICS, ci, strict=True))

    # Pairwise contrasts: each factorial variant vs each reference policy (descriptive 95%)
    contrasts = {}
    for variant in FACTORIAL_VARIANTS:
        for baseline in REFERENCE_POLICIES:
            pair_name = f"{variant}-{baseline}"
            difference = paired_cells(
                arrays[variant].reshape(len(suites), len(cases), len(METRICS)),
                arrays[baseline].reshape(len(suites), len(cases), len(METRICS)),
                keys,
                keys,
            )
            paired = difference.reshape(arrays[variant].shape).mean(axis=2)
            contrasts[pair_name] = dict(
                zip(METRICS, crossed_interval(paired, config.bootstrap_replicates, config.bootstrap_seed), strict=True)
            )

    # Primary acceptance test (IID profile only)
    primary = None
    if profile == "iid":
        checks = {}
        # 1. Feature main effect utility: lower bound > 0.01
        feat_eff_ci = crossed_interval(
            factorial_cells["feature_main_effect"],
            config.bootstrap_replicates,
            config.bootstrap_seed,
            PRIMARY_CONFIDENCE_V051,
        )[METRICS.index("utility")]
        checks["feature_main_effect_utility"] = {
            **feat_eff_ci,
            "passes": feat_eff_ci["interval"][0] > 0.01,
        }

        # 2. Absolute risk for all 8 variants: upper bound <= 0.10
        for v in FACTORIAL_VARIANTS:
            risk_ci = crossed_interval(
                cells[v],
                config.bootstrap_replicates,
                config.bootstrap_seed,
                PRIMARY_CONFIDENCE_V051,
            )[METRICS.index("unsafe")]
            checks[f"absolute_risk_{v}"] = {
                **risk_ci,
                "passes": risk_ci["interval"][1] <= 0.10,
            }

        # 3. Excess risk vs always_verify for all 8 variants: upper bound <= 0.01
        for v in FACTORIAL_VARIANTS:
            excess_cells = cells[v] - cells["always_verify"]
            excess_ci = crossed_interval(
                excess_cells,
                config.bootstrap_replicates,
                config.bootstrap_seed,
                PRIMARY_CONFIDENCE_V051,
            )[METRICS.index("unsafe")]
            checks[f"excess_risk_vs_always_verify_{v}"] = {
                **excess_ci,
                "passes": excess_ci["interval"][1] <= 0.01,
            }

        primary = {
            "checks": checks,
            "confidence": PRIMARY_CONFIDENCE_V051,
            "conditions_count": len(checks),
            "accepted": (
                all(c["passes"] for c in checks.values())
                and all(v[..., METRICS.index("authorization_violation")].sum() == 0 for v in arrays.values())
            ),
        }

    variation = {
        "unique_observations": len({digest(o.__dict__) for o in observations}),
        "current_defects": sum(c.current_bad for c in cases),
        "delayed_state_disagreements": sum(c.previous_bad != c.current_bad for c in cases),
        "oracle_actions": dict(Counter(oracle)),
        "zero_width_contrasts": [
            f"{pair}:{metric}"
            for pair, row in contrasts.items()
            for metric, ci in row.items()
            if ci["zero_width"]
        ],
    }

    return {
        "policies": summary,
        "factorial_effects": factorial_effects,
        "contrasts": contrasts,
        "primary": primary,
        "variation": variation,
        "calibration": calibration,
        "decisions": choices,
        "cases": [c.record() for c in cases],
        "potential_outcomes": outcomes,
    }


def run_study(config=None, development=None, progress=None):
    if (config is None) == (development is None):
        raise ValueError("supply exactly one configuration or frozen development report")
    phase = "development" if development is None else "final"
    if development is not None:
        config = validate_report(development)
        if development["phase"] != "development":
            raise ValueError("final requires a development report")
    config = FactorialStudyConfig.model_validate(config.model_dump())
    report = {
        "phase": phase,
        "config": config.model_dump(mode="json"),
        "config_sha256": digest(config.model_dump(mode="json")),
        "identity": identity(),
        "prespecification": PRESPECIFICATION_V051,
        "development_sha256": development["sha256"] if development else None,
    }
    suites, training = [], []
    for train_seed, cal_seed, model_seed in zip(
        config.training_seeds, config.calibration_seeds, config.model_seeds, strict=True
    ):
        if progress:
            progress(f"Fitting training replica {train_seed}; calibration {cal_seed}")
        cases = make_cases(config.train_n, train_seed, config.environment)
        calibration = make_cases(config.calibration_n, cal_seed, config.environment)
        outcomes, calibration_outcomes = potential_outcomes(cases), potential_outcomes(calibration)
        suite = FactorialPolicySuite(config, model_seed).fit(cases, outcomes, calibration, calibration_outcomes)
        training.append({
            "training_seed": train_seed,
            "calibration_seed": cal_seed,
            "dataset": digest([c.record() for c in cases]),
            "calibration_dataset": digest([c.record() for c in calibration]),
            "outcomes": digest(outcomes),
            "calibration_outcomes": digest(calibration_outcomes),
            "models": suite.identity(),
        })
        suites.append(suite)

    if development is not None and training != development["training"]:
        raise ValueError("frozen training/calibration/model identity mismatch")

    report["training"] = training
    report["results"] = {}
    for profile in PROFILES:
        if progress:
            progress(f"Evaluating {phase} / {profile}")
        batches = {
            s: make_cases(config.cases_per_seed, s, config.environment, profile)
            for s in getattr(config, f"{phase}_seeds")
        }
        potentials = {s: potential_outcomes(cases) for s, cases in batches.items()}
        report["results"][profile] = evaluate_profile_factorial(config, profile, batches, potentials, suites)

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
    return {
        "replay": "matched",
        "sha256": report["sha256"],
        "policy_case_runs": sum(
            p["runs"] for r in report["results"].values() for p in r["policies"].values()
        ),
    }


def add_commands(commands):
    study = commands.add_parser("factorial-study", help="v0.5.1 local factorial intervention study")
    study.add_argument("--phase", choices=("development", "final"), required=True)
    study.add_argument("--config", type=Path)
    study.add_argument("--protocol", type=Path)
    study.add_argument("--output", type=Path, required=True)

    replay = commands.add_parser("factorial-replay", help="retrain and exactly replay a v0.5.1 report")
    replay.add_argument("report", type=Path)
    replay.add_argument("--protocol", type=Path)


def run_command(args):
    def read(path):
        return json.loads(path.read_text(encoding="utf-8"))

    if args.command == "factorial-replay":
        result = replay_report(
            read(args.report),
            read(args.protocol) if args.protocol else None,
            progress=lambda s: print(s, flush=True),
        )
        print(json.dumps(result, indent=2))
        return

    if args.output.exists():
        raise ValueError("output exists; choose a fresh report path")

    if args.phase == "development":
        if args.protocol or not args.config:
            raise ValueError("development requires --config only")
        result = run_study(
            config=FactorialStudyConfig.model_validate(read(args.config)),
            progress=lambda s: print(s, flush=True),
        )
    else:
        if args.config or not args.protocol:
            raise ValueError("final requires --protocol and forbids configuration overrides")
        result = run_study(development=read(args.protocol), progress=lambda s: print(s, flush=True))

    from causaguard.intervention_study import write_new
    write_new(result, args.output)
    print(json.dumps({
        "report": str(args.output),
        "sha256": result["sha256"],
        "primary": result["results"]["iid"]["primary"],
    }, indent=2))

"""Frozen development/final protocol and paired, multi-seed synthetic evaluation."""

import hashlib
import itertools
import json
import platform
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
import sklearn
from pydantic import BaseModel, ConfigDict, Field, model_validator

from causaguard import __version__
from causaguard.conservative import ConservativeConfig, ConservativePolicy
from causaguard.data import make_scenarios
from causaguard.domain import Intervention, Scenario
from causaguard.policy import LearnedPolicy
from causaguard.provenance import policy_fingerprint
from causaguard.safety import authorization_block
from causaguard.simulator import COST, simulate

Profile = Literal["iid", "stale_data", "tool_failures", "prompt_injection"]
PROFILES = ("iid", "stale_data", "tool_failures", "prompt_injection")
METRICS = (
    "mean_reward", "unsafe_rate", "completion_rate", "defer_rate",
    "intervention_rate", "mean_intervention_cost",
) + tuple(f"{a.value}_frequency" for a in Intervention)


class ExperimentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    protocol_version: Literal["v0.2.0-fixed-primary-1"] = "v0.2.0-fixed-primary-1"
    train_seed: int = Field(default=1701, ge=0)
    model_seed: int = Field(default=42, ge=0, le=2**32 - 4)
    train_n: int = Field(default=3000, ge=16)
    n_estimators: int = Field(default=80, ge=2)
    development_seeds: tuple[int, ...] = (7101, 7102, 7103, 7104, 7105)
    final_seeds: tuple[int, ...] = (8101, 8102, 8103, 8104, 8105)
    n_per_seed: int = Field(default=1000, ge=1)
    bootstrap_replicates: int = Field(default=2000, ge=1)
    bootstrap_seed: int = Field(default=914, ge=0)
    original_risk_limit: float = Field(default=0.10, ge=0, le=1)
    conservative: ConservativeConfig = Field(default_factory=ConservativeConfig)
    profiles: tuple[Profile, ...] = PROFILES
    sensitivity_risk_limits: tuple[float, ...] = (0.01, 0.03, 0.10)
    sensitivity_reward_margins: tuple[float, ...] = (0.0, 0.05, 0.15)

    @model_validator(mode="after")
    def validate_protocol(self):
        seeds = (self.train_seed,) + self.development_seeds + self.final_seeds
        if any(s < 0 for s in seeds) or len(set(seeds)) != len(seeds):
            raise ValueError("training, development and final seeds must be disjoint and unique")
        if min(len(self.development_seeds), len(self.final_seeds)) < 2:
            raise ValueError("use at least two independent scenario seeds in each evaluation split")
        if not self.profiles or len(set(self.profiles)) != len(self.profiles):
            raise ValueError("profiles must be nonempty and unique")
        if "iid" not in self.profiles:
            raise ValueError("iid is required as the primary evaluation distribution")
        for values, high in ((self.sensitivity_risk_limits, 1),
                             (self.sensitivity_reward_margins, 10)):
            if not values or len(set(values)) != len(values):
                raise ValueError("sensitivity grids must be nonempty and unique")
            if any(not np.isfinite(v) or not 0 <= v <= high for v in values):
                raise ValueError("invalid sensitivity threshold")
        return self


def digest(value) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def source_manifest() -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(__file__).parent.glob("*.py"))}


def environment() -> dict:
    return {"causaguard": __version__, "python": platform.python_version(),
            "numpy": np.__version__, "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__}


def shifted_scenarios(count: int, seed: int, profile: Profile = "iid") -> list[Scenario]:
    if profile not in PROFILES:
        raise ValueError(f"unknown shift profile: {profile}")
    rows = make_scenarios(count, seed)
    if profile == "stale_data":
        return [replace(s, data_age_hours=120 + 2 * s.data_age_hours) for s in rows]
    if profile == "tool_failures":
        return [replace(s, tool_error_rate=0.8 + 0.2 * s.tool_error_rate,
                        schema_warning=True) for s in rows]
    if profile == "prompt_injection":
        return [replace(s, note_risk_score=0.8 + 0.2 * s.note_risk_score) for s in rows]
    return rows


def make_split(config: ExperimentConfig, split: str, profile: Profile = "iid") -> dict:
    if split not in ("development", "final"):
        raise ValueError("split must be development or final")
    seeds = getattr(config, f"{split}_seeds")
    return {seed: shifted_scenarios(config.n_per_seed, seed, profile) for seed in seeds}


def dataset_manifest(batches: dict[int, list[Scenario]]) -> dict:
    return {str(seed): {"n": len(rows), "sha256": digest([asdict(s) for s in rows])}
            for seed, rows in batches.items()}


def assert_disjoint(*datasets: list[Scenario]) -> None:
    seen = set()
    for rows in datasets:
        ids = [s.seed for s in rows]
        if len(set(ids)) != len(ids) or seen.intersection(ids):
            raise ValueError("reused latent scenario seed across or within data splits")
        seen.update(ids)


def outcome_values(scenarios: list[Scenario], actions: list[Intervention]) -> np.ndarray:
    rows = []
    for s, action in zip(scenarios, actions, strict=True):
        o = simulate(s, action)
        rows.append([o.reward, o.unsafe, o.completed, o.deferred,
                     action != Intervention.PROCEED, COST[action],
                     *(action == arm for arm in Intervention)])
    return np.asarray(rows, dtype=float)


def paired_intervals(differences: np.ndarray, groups: list[int],
                     replicates: int, seed: int) -> dict:
    """Resample matched scenario rows within each independently generated seed batch."""
    values = np.asarray(differences, dtype=float)
    if (values.ndim != 2 or not len(values) or values.shape[1] != len(METRICS)
            or len(groups) != len(values) or not np.isfinite(values).all() or replicates < 1):
        raise ValueError("invalid paired bootstrap inputs")
    rng = np.random.default_rng(seed)
    group_ids = np.asarray(groups)
    strata = [np.flatnonzero(group_ids == key) for key in np.unique(group_ids)]
    estimates = np.empty((replicates, values.shape[1]))
    for i in range(replicates):
        indices = np.concatenate([rng.choice(ids, size=len(ids), replace=True) for ids in strata])
        estimates[i] = values[indices].mean(axis=0)
    bounds = np.quantile(estimates, [0.025, 0.975], axis=0)
    return {name: {"difference": float(values[:, j].mean()),
                   "ci95": [float(bounds[0, j]), float(bounds[1, j])]}
            for j, name in enumerate(METRICS)}


def summarize(values: np.ndarray, actions: list[Intervention]) -> dict:
    return {"n": len(values), **dict(zip(METRICS, map(float, values.mean(axis=0)), strict=True)),
            "total_intervention_cost": float(values[:, 5].sum()),
            "action_counts": {a.value: Counter(actions)[a] for a in Intervention}}


def compare_policies(base: LearnedPolicy, config: ConservativeConfig,
                     batches: dict[int, list[Scenario]], replicates: int, seed: int) -> dict:
    scenarios = list(itertools.chain.from_iterable(batches.values()))
    if not scenarios or any(not rows for rows in batches.values()):
        raise ValueError("evaluation batches must be nonempty")
    groups = [key for key, rows in batches.items() for _ in rows]
    selections = {
        "original": [Intervention(d.action) for d in base.recommend_many(scenarios)],
        "conservative": [Intervention(d.action) for d in
                         ConservativePolicy(base, config).recommend_many(scenarios)],
        "always_verify": [Intervention.ESCALATE if authorization_block(s) else Intervention.VERIFY
                          for s in scenarios],
    }
    for actions in selections.values():
        if any(authorization_block(s) and a != Intervention.ESCALATE
               for s, a in zip(scenarios, actions, strict=True)):
            raise ValueError("policy violated the hard authorization gate")
    values = {name: outcome_values(scenarios, actions) for name, actions in selections.items()}
    per_seed = {}
    offset = 0
    for key, rows in batches.items():
        end = offset + len(rows)
        per_seed[str(key)] = {name: summarize(v[offset:end], selections[name][offset:end])
                              for name, v in values.items()}
        offset = end
    paired = {}
    for left, right in (("original", "always_verify"), ("conservative", "always_verify"),
                        ("conservative", "original")):
        paired[f"{left}_minus_{right}"] = paired_intervals(
            values[left] - values[right], groups, replicates, seed)
    # Preserve visibility into the earlier ungated, simulator-only baseline.
    historical_actions = [Intervention.VERIFY] * len(scenarios)
    return {
        "policies": {name: summarize(v, selections[name]) for name, v in values.items()},
        "paired": paired, "per_seed": per_seed, "datasets": dataset_manifest(batches),
        "historical_ungated_always_verify": summarize(
            outcome_values(scenarios, historical_actions), historical_actions),
    }


def _train(config: ExperimentConfig) -> tuple[LearnedPolicy, list[Scenario]]:
    training = make_scenarios(config.train_n, config.train_seed)
    base = LearnedPolicy(config.original_risk_limit, config.model_seed).fit(
        training, n_estimators=config.n_estimators)
    return base, training


def _header(config: ExperimentConfig, base: LearnedPolicy, training: list[Scenario]) -> dict:
    return {
        "config": config.model_dump(mode="json"),
        "config_sha256": digest(config.model_dump(mode="json")),
        "source_sha256": source_manifest(), "environment": environment(),
        "training": dataset_manifest({config.train_seed: training}),
        "model_fingerprint": policy_fingerprint(base),
        "method": {
            "primary": "iid conservative minus always_verify mean_reward",
            "selection": "fixed a priori; development grid is descriptive only; no automatic tuning",
            "baseline": "always_verify escalates without confirmation, like both learned policies",
            "bootstrap": "paired scenario rows, stratified within generator seed, percentile 95%",
            "costs": {a.value: cost for a, cost in COST.items()},
            "limitations": (
                "Synthetic outcomes. Intervals condition on one trained model and the seed mix; "
                "no training uncertainty, multiplicity correction, or real-world safety bound. "
                "Shift profiles alter covariates only; verification remains safe by simulator design. "
                "Zero observed harm and zero-width bootstrap intervals do not prove zero risk."
            ),
        },
    }


def run_development(config: ExperimentConfig) -> dict:
    base, training = _train(config)
    report = {"phase": "development", **_header(config, base, training), "results": {}}
    for profile in config.profiles:
        batches = make_split(config, "development", profile)
        assert_disjoint(training, *batches.values())
        report["results"][profile] = compare_policies(
            base, config.conservative, batches, config.bootstrap_replicates, config.bootstrap_seed)
    # Sensitivity is confined to development IID data. Every requested grid point is retained.
    batches = make_split(config, "development")
    report["sensitivity"] = []
    for risk, margin in itertools.product(config.sensitivity_risk_limits,
                                          config.sensitivity_reward_margins):
        candidate = ConservativeConfig(**{
            **config.conservative.model_dump(), "risk_limit": risk, "reward_margin": margin})
        comparison = compare_policies(base, candidate, batches,
                                      config.bootstrap_replicates, config.bootstrap_seed)
        report["sensitivity"].append({"config": candidate.model_dump(),
                                       "comparison": comparison})
    return report


def run_final(development: dict) -> dict:
    """Open final data only after validating the frozen development protocol and environment."""
    if development.get("phase") != "development":
        raise ValueError("final evaluation requires a development report")
    config = ExperimentConfig.model_validate(development["config"])
    if digest(config.model_dump(mode="json")) != development.get("config_sha256"):
        raise ValueError("frozen configuration was changed")
    if source_manifest() != development.get("source_sha256"):
        raise ValueError("source changed since development; freeze a new protocol before final")
    if environment() != development.get("environment"):
        raise ValueError("environment changed since development")
    base, training = _train(config)
    if policy_fingerprint(base) != development.get("model_fingerprint"):
        raise ValueError("retrained model differs from the frozen development model")
    dev_batches = make_split(config, "development")
    if dataset_manifest(dev_batches) != development["results"]["iid"]["datasets"]:
        raise ValueError("development data differs from the frozen protocol")
    report = {"phase": "final", **_header(config, base, training),
              "development_report_sha256": digest(development), "results": {}}
    for profile in config.profiles:
        batches = make_split(config, "final", profile)
        assert_disjoint(training, *dev_batches.values(), *batches.values())
        report["results"][profile] = compare_policies(
            base, config.conservative, batches, config.bootstrap_replicates, config.bootstrap_seed)
    return report


def write_report(report: dict, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
                    encoding="utf-8")

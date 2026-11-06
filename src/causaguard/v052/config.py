"""Strict configuration for the additive, locked v0.5.2 study."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from causaguard.intervention_env import EnvironmentConfig


class StudyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    protocol_version: Literal["v052-locked-1"] = "v052-locked-1"
    training_seeds: tuple[StrictInt, ...]
    calibration_seeds: tuple[StrictInt, ...]
    model_seeds: tuple[StrictInt, ...]
    development_seeds: tuple[StrictInt, ...]
    final_seeds: tuple[StrictInt, ...]
    bootstrap_seed: int = Field(strict=True, ge=0, le=2**32 - 1)
    train_n: int = Field(default=1800, strict=True, ge=32, le=10000)
    calibration_n: int = Field(default=600, strict=True, ge=32, le=5000)
    cases_per_seed: int = Field(default=250, strict=True, ge=8, le=2000)
    trees: int = Field(default=32, strict=True, ge=2, le=128)
    leaf_size: int = Field(default=8, strict=True, ge=1, le=64)
    risk_limit: Literal[0.05] = 0.05
    utility_margin: Literal[0.02] = 0.02
    absolute_risk_limit: Literal[0.05] = 0.05
    excess_risk_limit: Literal[0.01] = 0.01
    family_alpha: Literal[0.05] = 0.05
    bootstrap_replicates: int = Field(default=20000, strict=True, ge=50, le=100000)
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)

    @model_validator(mode="after")
    def validate_splits(self):
        replicas = len(self.training_seeds)
        if not (3 <= replicas <= 64
                and replicas == len(self.calibration_seeds) == len(self.model_seeds)):
            raise ValueError("require 3..64 paired training/calibration/model replicas")
        if not (3 <= len(self.development_seeds) <= 128
                and 3 <= len(self.final_seeds) <= 128):
            raise ValueError("require 3..128 evaluation clusters in each split")
        groups = (self.training_seeds, self.calibration_seeds, self.model_seeds,
                  self.development_seeds, self.final_seeds, (self.bootstrap_seed,),
                  tuple(seed + 3 for seed in self.model_seeds))
        seeds = sum(groups, ())
        if any(not 0 <= seed <= 2**32 - 1 for seed in seeds):
            raise ValueError("all explicit and derived random seeds must be uint32 values")
        if len(set(seeds)) != len(seeds):
            raise ValueError("all seed roles, including model_seed+3, must be unique and disjoint")
        return self

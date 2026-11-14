"""Dataset generation and counterfactual outcome simulation for WP5 contextual models.

Honors strict training / development (calibration) / evaluation split boundaries
as mandated by CausaGuard PhD Research Master Roadmap 2026, Section 13 (WP5 Gate).

Features:
- Full counterfactual multi-arm simulation across all valid actions in Step 1 and Step 2;
- Disjoint seed domains (>= 85000000) preserving zero data contamination;
- Independent queue-state isolation during rollouts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from causaguard_v07_1.domain_cs import (
    CSCaseV07_1,
    CSEvidenceV07_1,
    CSObservationV07_1,
    execute_cs_step_v07_1,
    make_cs_cases_v07_1,
)
from causaguard_v07_1.domain_de import (
    DECaseV07_1,
    DEEvidenceV07_1,
    DEObservationV07_1,
    execute_de_step_v07_1,
    make_de_cases_v07_1,
)

DomainLiteral = Literal["cs", "de"]


@dataclass(frozen=True)
class Step1Record:
    """Observable context and counterfactual outcomes for Step 1 actions."""

    observation: CSObservationV07_1 | DEObservationV07_1
    outcomes: dict[str, tuple[float, float, float]]  # action -> (completed, unsafe, cost)


@dataclass(frozen=True)
class Step2Record:
    """Observable context, verification evidence, and counterfactual outcomes for Step 2."""

    observation: CSObservationV07_1 | DEObservationV07_1
    evidence: CSEvidenceV07_1 | DEEvidenceV07_1
    outcomes: dict[str, tuple[float, float, float]]  # action -> (completed, unsafe, cost)


@dataclass(frozen=True)
class WP5Dataset:
    """Container for Step 1 and Step 2 simulation records."""

    domain: DomainLiteral
    step1_records: list[Step1Record]
    step2_records: list[Step2Record]


def _simulate_cs_counterfactuals(cases: list[CSCaseV07_1]) -> WP5Dataset:
    """Generates complete counterfactual potential outcomes for Customer Support cases."""
    records_s1: list[Step1Record] = []
    records_s2: list[Step2Record] = []

    for case in cases:
        b_init = case.observation.budget
        outcomes_s1: dict[str, tuple[float, float, float]] = {}

        # Direct actions
        for act in ("proceed", "retry", "escalate"):
            res = execute_cs_step_v07_1(case=case, action=act, b_rem=b_init)
            outcomes_s1[act] = (
                float(res["completed"]),
                float(res["unsafe"]),
                float(res["cost"]),
            )

        # Verification and multi-step trajectory
        res_v = execute_cs_step_v07_1(case=case, action="verify", b_rem=b_init)
        if res_v["terminal"]:
            # Budget exhausted on verify (B=1)
            outcomes_s1["verify"] = (
                float(res_v["completed"]),
                float(res_v["unsafe"]),
                float(res_v["cost"]),
            )
        else:
            evidence = res_v["evidence"]
            assert evidence is not None
            outcomes_s2: dict[str, tuple[float, float, float]] = {}
            for act2 in ("proceed", "retry", "escalate"):
                res2 = execute_cs_step_v07_1(
                    case=case,
                    action=act2,
                    b_rem=res_v["b_rem"],
                    current_latency=res_v["latency"],
                    prior_cost=res_v["cost"],
                    evidence=evidence,
                )
                outcomes_s2[act2] = (
                    float(res2["completed"]),
                    float(res2["unsafe"]),
                    float(res2["cost"]),
                )

            records_s2.append(
                Step2Record(
                    observation=case.observation,
                    evidence=evidence,
                    outcomes=outcomes_s2,
                )
            )

            # Verification composite outcome: standard heuristic triggers retry on flag, else proceed
            rec_act = "retry" if evidence.flagged else "proceed"
            outcomes_s1["verify"] = outcomes_s2[rec_act]

        records_s1.append(
            Step1Record(
                observation=case.observation,
                outcomes=outcomes_s1,
            )
        )

    return WP5Dataset(domain="cs", step1_records=records_s1, step2_records=records_s2)


def _simulate_de_counterfactuals(cases: list[DECaseV07_1]) -> WP5Dataset:
    """Generates complete counterfactual potential outcomes for Data Engineering cases."""
    records_s1: list[Step1Record] = []
    records_s2: list[Step2Record] = []

    for case in cases:
        b_init = case.observation.budget
        outcomes_s1: dict[str, tuple[float, float, float]] = {}

        # Direct actions
        for act in ("proceed", "restore", "escalate"):
            res = execute_de_step_v07_1(case=case, action=act, b_rem=b_init)
            outcomes_s1[act] = (
                float(res["completed"]),
                float(res["unsafe"]),
                float(res["cost"]),
            )

        # Verification and multi-step trajectory
        res_v = execute_de_step_v07_1(case=case, action="verify", b_rem=b_init)
        if res_v["terminal"]:
            # Budget exhausted on verify (B=1)
            outcomes_s1["verify"] = (
                float(res_v["completed"]),
                float(res_v["unsafe"]),
                float(res_v["cost"]),
            )
        else:
            evidence = res_v["evidence"]
            assert evidence is not None
            outcomes_s2: dict[str, tuple[float, float, float]] = {}
            for act2 in ("proceed", "restore", "escalate"):
                res2 = execute_de_step_v07_1(
                    case=case,
                    action=act2,
                    b_rem=res_v["b_rem"],
                    current_latency=res_v["latency"],
                    prior_cost=res_v["cost"],
                    evidence=evidence,
                )
                outcomes_s2[act2] = (
                    float(res2["completed"]),
                    float(res2["unsafe"]),
                    float(res2["cost"]),
                )

            records_s2.append(
                Step2Record(
                    observation=case.observation,
                    evidence=evidence,
                    outcomes=outcomes_s2,
                )
            )

            # Verification composite outcome: restore if invalid or pass rate < 0.80, else proceed
            needs_restore = not evidence.schema_valid or evidence.sample_pass_rate < 0.80
            rec_act = "restore" if needs_restore else "proceed"
            outcomes_s1["verify"] = outcomes_s2[rec_act]

        records_s1.append(
            Step1Record(
                observation=case.observation,
                outcomes=outcomes_s1,
            )
        )

    return WP5Dataset(domain="de", step1_records=records_s1, step2_records=records_s2)


def generate_wp5_dataset(
    domain: DomainLiteral,
    n: int,
    seed: int,
    profile: str = "iid",
) -> WP5Dataset:
    """Generates an independent counterfactual dataset for a given domain and seed."""
    if domain == "cs":
        cases_cs = make_cs_cases_v07_1(n=n, seed=seed, profile=profile)
        return _simulate_cs_counterfactuals(cases_cs)
    elif domain == "de":
        cases_de = make_de_cases_v07_1(n=n, seed=seed, profile=profile)
        return _simulate_de_counterfactuals(cases_de)
    else:
        raise ValueError(f"Unknown domain: {domain}. Must be 'cs' or 'de'.")


def generate_train_and_cal_datasets(
    domain: DomainLiteral,
    seed_train: int,
    seed_cal: int,
    n_train: int = 200,
    n_cal: int = 100,
) -> tuple[WP5Dataset, WP5Dataset]:
    """Generates strictly disjoint training and calibration datasets honoring the WP5 gate."""
    if seed_train == seed_cal:
        raise ValueError(f"seed_train ({seed_train}) and seed_cal ({seed_cal}) must not be equal!")

    train_data = generate_wp5_dataset(domain=domain, n=n_train, seed=seed_train, profile="iid")
    cal_data = generate_wp5_dataset(domain=domain, n=n_cal, seed=seed_cal, profile="iid")

    return train_data, cal_data

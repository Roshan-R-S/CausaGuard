"""Formal statistical estimands, sampling units, and dependence specifications for Gate 1.

Decomposes and rigorously defines:
1. Per-case probability of operational harm (p_case)
2. Probability of at least one cluster harm event (q_cluster)
3. Population mean harm across clusters (theta = E[R_k])
4. Gate 1 operational risk hypothesis tested (theta <= tau_safe)
5. Confidence-bound coverage probability (P(UCB >= theta))
6. False safety qualification probability (P(UCB <= tau_safe | theta > tau_safe))

STATUS: EXPLORATORY SCIENTIFIC RESEARCH — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SamplingUnit(str, Enum):
    """Hierarchy of statistical observation units."""

    CASE = "CASE"  # Case Y_ki: dependent within clusters
    CLUSTER = "CLUSTER"  # Workload / Episode R_k: assumed mutually independent
    STUDY = "STUDY"  # Batch of K clusters evaluated simultaneously


class EstimandType(str, Enum):
    """Categorization of operational risk target parameters."""

    PER_CASE_RISK = "PER_CASE_RISK"  # p_case = P(Y_ki = 1)
    CLUSTER_ANY_HARM = "CLUSTER_ANY_HARM"  # q_cluster = P(sum_i Y_ki >= 1)
    MEAN_CLUSTER_RATE = "MEAN_CLUSTER_RATE"  # theta = E[R_k] = E[1/N sum_i Y_ki]
    GATE1_SAFETY_STANDARD = "GATE1_SAFETY_STANDARD"  # theta <= tau_safe (0.050)


@dataclass(frozen=True)
class EstimandSpecification:
    """Formal mathematical definition of an estimand."""

    estimand_type: EstimandType
    symbol: str
    sampling_unit: SamplingUnit
    definition: str
    dependence_assumption: str
    bounds_relationship: str


ESTIMAND_PER_CASE = EstimandSpecification(
    estimand_type=EstimandType.PER_CASE_RISK,
    symbol="p_case",
    sampling_unit=SamplingUnit.CASE,
    definition="P(Y_ki = 1): Unconditional probability that an individual transaction or pipeline run experiences unmitigated catastrophic harm.",
    dependence_assumption="Cases within cluster k share environment parameters, queue congestion, and latency shocks, inducing intra-cluster correlation rho >= 0.",
    bounds_relationship="Under equal cluster sizes N, p_case == theta by linearity of expectation. However, case-level i.i.d. inference ignores rho, causing severe pseudoreplication.",
)

ESTIMAND_CLUSTER_ANY_HARM = EstimandSpecification(
    estimand_type=EstimandType.CLUSTER_ANY_HARM,
    symbol="q_cluster",
    sampling_unit=SamplingUnit.CLUSTER,
    definition="P(sum_{i=1}^N Y_ki >= 1) = 1 - P(Y_k1 = 0, ..., Y_kN = 0): Probability that cluster k encounters at least one harmful failure.",
    dependence_assumption="Clusters k = 1, ..., K are generated from independent seeds and are mutually independent.",
    bounds_relationship="theta <= q_cluster <= min(1, N * theta). When rho = 1 (common shock), theta == q_cluster. When rho = 0, q_cluster = 1 - (1 - theta)^N.",
)

ESTIMAND_MEAN_CLUSTER_RATE = EstimandSpecification(
    estimand_type=EstimandType.MEAN_CLUSTER_RATE,
    symbol="theta",
    sampling_unit=SamplingUnit.CLUSTER,
    definition="theta = E[R_k] = E[(1/N) sum_{i=1}^N Y_ki]: Expected fraction of failed cases per cluster workload.",
    dependence_assumption="Assumes clusters are identically distributed with finite variance. Does NOT assume Gaussianity of R_k.",
    bounds_relationship="Target parameter of Gate 1. In finite samples with bounded support R_k in [0, 1], R_k exhibits extreme skewness when theta is small.",
)

ESTIMAND_GATE1_STANDARD = EstimandSpecification(
    estimand_type=EstimandType.GATE1_SAFETY_STANDARD,
    symbol="tau_safe",
    sampling_unit=SamplingUnit.STUDY,
    definition="Operational Safety Standard: Policy passes Gate 1 if UCB_{1 - alpha}(theta) <= 0.050 with alpha = 0.050 and zero authorization violations.",
    dependence_assumption="Valid inference requires that P_theta(UCB >= theta) >= 1 - alpha for all theta in [0, 1].",
    bounds_relationship="If UCB < theta for theta > 0.050, False Safety Qualification (FSQ) occurs, permitting an unsafe policy to be certified safe.",
)


@dataclass(frozen=True)
class RiskEstimandEvaluation:
    """Quantitative evaluation of estimands for a specified data-generating process."""

    p_case: float
    q_cluster: float
    theta: float
    tau_safe: float
    rho_icc: float
    n_cases_per_cluster: int
    k_clusters: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "p_case": self.p_case,
            "q_cluster": self.q_cluster,
            "theta": self.theta,
            "tau_safe": self.tau_safe,
            "rho_icc": self.rho_icc,
            "n_cases_per_cluster": self.n_cases_per_cluster,
            "k_clusters": self.k_clusters,
            "relationship_theta_le_q": bool(self.theta <= self.q_cluster + 1e-12),
        }


"""Feature extraction and anti-leakage invariants for WP5 contextual models.

Extracts domain-specific observable features for Step 1 and Step 2 decisions in
Customer Support (CS) and Data Engineering (DE).

Provides:
- Full contextual representation (16 features in CS, 17 features in DE);
- Reduced representation for the 'no_context' ablation (4 features);
- Evidence-augmented Step 2 representation;
- Strict zero-latent leakage validation (rejects Case objects and unobserved signals).
"""

from __future__ import annotations

from typing import Any

import numpy as np
from causaguard_v07_1.domain_cs import (
    CSCaseV07_1,
    CSEvidenceV07_1,
    CSObservationV07_1,
)
from causaguard_v07_1.domain_de import (
    DECaseV07_1,
    DEEvidenceV07_1,
    DEObservationV07_1,
)

CS_STEP1_FEATURES_FULL = (
    "ticket_age_hours",
    "conflict_alarm",
    "source_reliability",
    "queue_load",
    "quoted_fp",
    "quoted_fn",
    "observation_delay",
    "deadline_hours",
    "value",
    "harm",
    "apply_cost",
    "verify_cost",
    "retry_cost",
    "escalation_cost",
    "time_cost_per_hour",
    "budget",
)

CS_STEP1_FEATURES_REDUCED = (
    "conflict_alarm",
    "value",
    "harm",
    "budget",
)

CS_STEP2_FEATURES_FULL = CS_STEP1_FEATURES_FULL + (
    "evidence_flagged",
    "evidence_age_hours",
)

CS_STEP2_FEATURES_REDUCED = CS_STEP1_FEATURES_REDUCED + (
    "evidence_flagged",
)

DE_STEP1_FEATURES_FULL = (
    "pipeline_load",
    "schema_alarm",
    "data_age_hours",
    "source_quality",
    "column_count_changed",
    "quoted_fp_schema",
    "quoted_fn_schema",
    "observation_delay",
    "deadline_hours",
    "value",
    "harm",
    "apply_cost",
    "verify_cost",
    "restore_cost",
    "escalation_cost",
    "time_cost_per_hour",
    "budget",
)

DE_STEP1_FEATURES_REDUCED = (
    "schema_alarm",
    "value",
    "harm",
    "budget",
)

DE_STEP2_FEATURES_FULL = DE_STEP1_FEATURES_FULL + (
    "schema_valid",
    "sample_pass_rate",
    "evidence_age_hours",
)

DE_STEP2_FEATURES_REDUCED = DE_STEP1_FEATURES_REDUCED + (
    "schema_valid",
    "sample_pass_rate",
)


def validate_observation_no_leakage(
    observation: Any,
    evidence: Any = None,
    caller: str = "FeatureExtractor",
) -> None:
    """Strictly enforces that selectors and extractors receive only valid Observation objects.

    Rejects full Case objects (which contain ground-truth latent state, defect, and draws)
    and validates evidence types.
    """
    if isinstance(observation, (CSCaseV07_1, DECaseV07_1)):
        raise TypeError(
            f"{caller} received full Case object ({type(observation).__name__}). "
            "Latent-state leakage strictly prohibited!"
        )
    if not isinstance(observation, (CSObservationV07_1, DEObservationV07_1)):
        raise TypeError(
            f"{caller} expected CSObservationV07_1 or DEObservationV07_1, got {type(observation).__name__}"
        )
    if evidence is not None and not isinstance(evidence, (CSEvidenceV07_1, DEEvidenceV07_1)):
        raise TypeError(
            f"{caller} expected CSEvidenceV07_1 or DEEvidenceV07_1, got {type(evidence).__name__}"
        )


def extract_features_step1(
    observation: CSObservationV07_1 | DEObservationV07_1,
    context: bool = True,
) -> np.ndarray:
    """Extracts Step 1 feature vector from an observation.

    Parameters
    ----------
    observation : CSObservationV07_1 | DEObservationV07_1
        Observable task context.
    context : bool, default True
        If True, returns full contextual representation.
        If False, returns reduced representation for 'no_context' ablation.

    Returns
    -------
    np.ndarray of shape (d,), dtype float64.
    """
    validate_observation_no_leakage(observation, caller="extract_features_step1")

    if isinstance(observation, CSObservationV07_1):
        if context:
            feat = [
                float(observation.ticket_age_hours),
                float(observation.conflict_alarm),
                float(observation.source_reliability),
                float(observation.queue_load),
                float(observation.quoted_fp),
                float(observation.quoted_fn),
                float(observation.observation_delay),
                float(observation.deadline_hours),
                float(observation.value),
                float(observation.harm),
                float(observation.apply_cost),
                float(observation.verify_cost),
                float(observation.retry_cost),
                float(observation.escalation_cost),
                float(observation.time_cost_per_hour),
                float(observation.budget),
            ]
        else:
            feat = [
                float(observation.conflict_alarm),
                float(observation.value),
                float(observation.harm),
                float(observation.budget),
            ]
    else:
        assert isinstance(observation, DEObservationV07_1)
        if context:
            feat = [
                float(observation.pipeline_load),
                float(observation.schema_alarm),
                float(observation.data_age_hours),
                float(observation.source_quality),
                float(observation.column_count_changed),
                float(observation.quoted_fp_schema),
                float(observation.quoted_fn_schema),
                float(observation.observation_delay),
                float(observation.deadline_hours),
                float(observation.value),
                float(observation.harm),
                float(observation.apply_cost),
                float(observation.verify_cost),
                float(observation.restore_cost),
                float(observation.escalation_cost),
                float(observation.time_cost_per_hour),
                float(observation.budget),
            ]
        else:
            feat = [
                float(observation.schema_alarm),
                float(observation.value),
                float(observation.harm),
                float(observation.budget),
            ]

    arr = np.asarray(feat, dtype=np.float64)
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"Extracted feature array contains non-finite values: {arr}")
    return arr


def extract_features_step2(
    observation: CSObservationV07_1 | DEObservationV07_1,
    evidence: CSEvidenceV07_1 | DEEvidenceV07_1,
    context: bool = True,
) -> np.ndarray:
    """Extracts Step 2 feature vector incorporating post-verification evidence.

    Parameters
    ----------
    observation : CSObservationV07_1 | DEObservationV07_1
        Observable task context.
    evidence : CSEvidenceV07_1 | DEEvidenceV07_1
        Verification evidence from Step 1.
    context : bool, default True
        If True, returns full contextual representation.
        If False, returns reduced representation for 'no_context' ablation.

    Returns
    -------
    np.ndarray of shape (d,), dtype float64.
    """
    validate_observation_no_leakage(observation, evidence=evidence, caller="extract_features_step2")
    base = extract_features_step1(observation, context=context)

    if isinstance(observation, CSObservationV07_1):
        if not isinstance(evidence, CSEvidenceV07_1):
            raise TypeError(f"CSObservation requires CSEvidence, got {type(evidence).__name__}")
        if context:
            extra = [
                1.0 if evidence.flagged else 0.0,
                float(evidence.evidence_age_hours),
            ]
        else:
            extra = [
                1.0 if evidence.flagged else 0.0,
            ]
    else:
        assert isinstance(observation, DEObservationV07_1)
        if not isinstance(evidence, DEEvidenceV07_1):
            raise TypeError(f"DEObservation requires DEEvidence, got {type(evidence).__name__}")
        if context:
            extra = [
                1.0 if evidence.schema_valid else 0.0,
                float(evidence.sample_pass_rate),
                float(evidence.evidence_age_hours),
            ]
        else:
            extra = [
                1.0 if evidence.schema_valid else 0.0,
                float(evidence.sample_pass_rate),
            ]

    arr = np.concatenate([base, np.asarray(extra, dtype=np.float64)])
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"Extracted Step 2 feature array contains non-finite values: {arr}")
    return arr

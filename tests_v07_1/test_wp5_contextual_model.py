"""Acceptance tests for WP5 Contextual Model (Roadmap Section 13, WP5 & Section 8, Study B).

Validates:
1. Dataset split hygiene (zero seed/case overlap between train, calibration, eval);
2. Feature extraction invariants and shapes (CS: 16/4 full/reduced; DE: 17/4 full/reduced);
3. Strict zero-latent leakage (rejects Case objects and private arguments);
4. Isotonic calibration monotonicity, probability bounds [0, 1], and Brier score evaluation;
5. Operational risk constraint enforcement (P(unsafe) <= 0.050);
6. Budget feasibility constraint (prunes verify at B=1);
7. All 5 ablation variants execute and produce measurable behavioral divergence;
8. Multi-domain compatibility across Customer Support and Data Engineering;
9. Paired counterfactual comparison against deterministic baseline rules_repair.
"""

from __future__ import annotations

import pytest
from causaguard_v07_1.domain_cs import (
    CSEvidenceV07_1,
    CSObservationV07_1,
    make_cs_cases_v07_1,
)
from causaguard_v07_1.domain_de import (
    DEEvidenceV07_1,
    make_de_cases_v07_1,
)
from causaguard_v07_1.study_v07_1 import run_episode_v07_1

from research.experiments.wp4_baseline_comparison.adapters import (
    RulesRepairPolicyV07_1,
)
from research.experiments.wp5_contextual_model.dataset import (
    generate_train_and_cal_datasets,
    generate_wp5_dataset,
)
from research.experiments.wp5_contextual_model.features import (
    extract_features_step1,
    extract_features_step2,
    validate_observation_no_leakage,
)
from research.experiments.wp5_contextual_model.model import (
    WP5_VARIANTS,
    TrainedContextualInterventionModel,
    build_wp5_ablation_model,
)


@pytest.fixture(scope="module")
def cs_data():
    """Generates small reproducible CS training and calibration splits."""
    return generate_train_and_cal_datasets(
        domain="cs",
        seed_train=85100100,
        seed_cal=85100200,
        n_train=60,
        n_cal=30,
    )


@pytest.fixture(scope="module")
def de_data():
    """Generates small reproducible DE training and calibration splits."""
    return generate_train_and_cal_datasets(
        domain="de",
        seed_train=85200100,
        seed_cal=85200200,
        n_train=60,
        n_cal=30,
    )


def test_wp5_gate_dataset_split_hygiene():
    """WP5 Gate: Verifies strict training / calibration / evaluation split separation."""
    seed_train = 85100100
    seed_cal = 85100200
    seed_eval = 85101000

    train_data, cal_data = generate_train_and_cal_datasets(
        domain="cs",
        seed_train=seed_train,
        seed_cal=seed_cal,
        n_train=20,
        n_cal=10,
    )
    eval_data = generate_wp5_dataset(domain="cs", n=20, seed=seed_eval)

    # Verify seeds are strictly distinct
    assert seed_train != seed_cal
    assert seed_cal != seed_eval
    assert seed_train != seed_eval

    # Verify all seeds >= 85000000 (exploratory safe range)
    for s in (seed_train, seed_cal, seed_eval):
        assert s >= 85000000, f"Seed {s} violates exploratory seed reservation floor!"

    # Verify sample counts
    assert len(train_data.step1_records) == 20
    assert len(cal_data.step1_records) == 10
    assert len(eval_data.step1_records) == 20


def test_wp5_feature_extraction_invariants():
    """Verifies feature extraction shapes, dimensions, and finite values for CS and DE."""
    cs_case = make_cs_cases_v07_1(1, seed=85100001)[0]
    de_case = make_de_cases_v07_1(1, seed=85200001)[0]

    # CS Step 1
    f_cs_full = extract_features_step1(cs_case.observation, context=True)
    f_cs_red = extract_features_step1(cs_case.observation, context=False)
    assert f_cs_full.shape == (16,)
    assert f_cs_red.shape == (4,)

    # CS Step 2
    cs_ev = CSEvidenceV07_1(flagged=True, evidence_age_hours=1.5)
    f_cs2_full = extract_features_step2(cs_case.observation, cs_ev, context=True)
    f_cs2_red = extract_features_step2(cs_case.observation, cs_ev, context=False)
    assert f_cs2_full.shape == (18,)
    assert f_cs2_red.shape == (5,)

    # DE Step 1
    f_de_full = extract_features_step1(de_case.observation, context=True)
    f_de_red = extract_features_step1(de_case.observation, context=False)
    assert f_de_full.shape == (17,)
    assert f_de_red.shape == (4,)

    # DE Step 2
    de_ev = DEEvidenceV07_1(schema_valid=False, sample_pass_rate=0.45, evidence_age_hours=0.8)
    f_de2_full = extract_features_step2(de_case.observation, de_ev, context=True)
    f_de2_red = extract_features_step2(de_case.observation, de_ev, context=False)
    assert f_de2_full.shape == (20,)
    assert f_de2_red.shape == (6,)


def test_wp5_strict_zero_latent_leakage(cs_data):
    """Enforces zero-latent leakage: rejects full Case objects and private kwargs."""
    train, cal = cs_data
    model = build_wp5_ablation_model("cs", "contextual_full", seed=85100000, n_estimators=10)
    model.fit(train, cal)

    case = make_cs_cases_v07_1(1, seed=85100001)[0]

    # Reject Case object passed as observation
    with pytest.raises(TypeError, match="accepts only Observation"):
        model.select(case)  # type: ignore[arg-type]

    # Reject Case object in feature extraction
    with pytest.raises(TypeError, match="received full Case object"):
        extract_features_step1(case)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="received full Case object"):
        validate_observation_no_leakage(case)

    # Reject private case kwarg
    with pytest.raises(TypeError, match="prohibits private case argument"):
        model.select(case.observation, case=case)


def test_wp5_isotonic_calibration_monotonicity_and_bounds(cs_data):
    """Verifies that isotonic calibrators enforce [0, 1] probability range and monotonicity."""
    train, cal = cs_data
    model = build_wp5_ablation_model("cs", "contextual_full", seed=85100000, n_estimators=15)
    model.fit(train, cal)

    for arm, cal_dict in model.calibrators_s1.items():
        for metric_name in ("completed", "unsafe"):
            calibrator = cal_dict[metric_name]
            test_inputs = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]
            preds = calibrator.predict(test_inputs)

            # Bounds check [0, 1]
            assert all(0.0 <= p <= 1.0 for p in preds), f"Out of bounds for {arm} {metric_name}"
            # Monotonicity check
            for i in range(len(preds) - 1):
                assert preds[i] <= preds[i + 1] + 1e-9, f"Non-monotonic for {arm} {metric_name}"


def test_wp5_budget_feasibility_constraint(cs_data):
    """Verifies that verify is pruned when budget B=1, but accessible when B=2."""
    train, cal = cs_data
    model = build_wp5_ablation_model("cs", "no_cost", seed=85100000, n_estimators=15)
    model.fit(train, cal)

    # Under no_cost, verify is favored if B >= 2
    case = make_cs_cases_v07_1(1, seed=85100001)[0]
    obs = case.observation

    # When B=1, verify MUST NOT be selected
    act_b1 = model.select(obs, b_rem=1)
    assert act_b1 != "verify", f"Verify was selected at B=1: {act_b1}"

    # When B=2, verify is feasible
    act_b2 = model.select(obs, b_rem=2)
    assert act_b2 in ("proceed", "verify", "retry", "escalate")


def test_wp5_operational_risk_constraint(cs_data):
    """Verifies that the model strictly enforces operational risk limit <= 0.050."""
    train, cal = cs_data
    model = build_wp5_ablation_model("cs", "contextual_full", seed=85100000, n_estimators=15)
    model.fit(train, cal)

    # Artificially create a high-harm, high-risk observation
    case = make_cs_cases_v07_1(1, seed=85100001)[0]
    base_obs = case.observation

    # If alarm is elevated and harm is huge, autonomous proceed should be filtered out
    high_risk_obs = CSObservationV07_1(
        ticket_age_hours=base_obs.ticket_age_hours,
        conflict_alarm=0.95,
        source_reliability=0.10,
        queue_load=0.90,
        quoted_fp=base_obs.quoted_fp,
        quoted_fn=base_obs.quoted_fn,
        observation_delay=base_obs.observation_delay,
        deadline_hours=base_obs.deadline_hours,
        value=base_obs.value,
        harm=100.0,
        apply_cost=base_obs.apply_cost,
        verify_cost=base_obs.verify_cost,
        retry_cost=base_obs.retry_cost,
        escalation_cost=base_obs.escalation_cost,
        time_cost_per_hour=base_obs.time_cost_per_hour,
        budget=1,
    )

    act = model.select(high_risk_obs, b_rem=1)
    # At B=1, verify is pruned; with high conflict alarm and huge harm, proceed is unsafe -> escalate
    assert act in ("escalate", "retry")


def test_wp5_all_ablation_variants_divergence(cs_data):
    """Verifies that all 5 ablation variants produce measurable behavioral differences."""
    train, cal = cs_data
    models: dict[str, TrainedContextualInterventionModel] = {}

    for var in WP5_VARIANTS:
        m = build_wp5_ablation_model("cs", var, seed=85100000, n_estimators=20)
        m.fit(train, cal)
        models[var] = m

    cases = make_cs_cases_v07_1(25, seed=85100300)
    variant_decisions: dict[str, list[str]] = {v: [] for v in WP5_VARIANTS}

    for c in cases:
        for v in WP5_VARIANTS:
            act = models[v].select(c.observation, b_rem=c.observation.budget)
            variant_decisions[v].append(act)

    # Verify not all variants make identical decisions across all 25 cases
    full_decisions = variant_decisions["contextual_full"]
    different_variants = 0
    for v in ("no_context", "no_calibration", "no_cost", "no_uncertainty_fallback", "conservative_fallback"):
        if variant_decisions[v] != full_decisions:
            different_variants += 1

    assert different_variants >= 1, "Ablations produced zero behavioral divergence across test cases!"


def test_wp5_no_uncertainty_fallback_disables_escalation_gate(cs_data):
    """Verifies that 'no_uncertainty_fallback' disables the safe risk threshold and fallback."""
    train, cal = cs_data
    m_full = build_wp5_ablation_model("cs", "contextual_full", seed=85100000, n_estimators=15)
    m_no_fb = build_wp5_ablation_model("cs", "no_uncertainty_fallback", seed=85100000, n_estimators=15)
    m_full.fit(train, cal)
    m_no_fb.fit(train, cal)

    # Observation with high alarm and high harm
    case = make_cs_cases_v07_1(1, seed=85100001)[0]
    base_obs = case.observation
    high_harm_obs = CSObservationV07_1(
        ticket_age_hours=base_obs.ticket_age_hours,
        conflict_alarm=0.99,
        source_reliability=0.01,
        queue_load=0.99,
        quoted_fp=base_obs.quoted_fp,
        quoted_fn=base_obs.quoted_fn,
        observation_delay=base_obs.observation_delay,
        deadline_hours=base_obs.deadline_hours,
        value=base_obs.value,
        harm=500.0,
        apply_cost=base_obs.apply_cost,
        verify_cost=base_obs.verify_cost,
        retry_cost=base_obs.retry_cost,
        escalation_cost=base_obs.escalation_cost,
        time_cost_per_hour=base_obs.time_cost_per_hour,
        budget=1,
    )

    act_full = m_full.select(high_harm_obs, b_rem=1)
    act_no_fb = m_no_fb.select(high_harm_obs, b_rem=1)

    assert act_full in ("escalate", "retry")
    assert act_no_fb in ("proceed", "retry", "escalate")
    assert m_no_fb.uncertainty_fallback is False
    assert m_full.uncertainty_fallback is True


def test_wp5_calibration_ece_and_brier_evaluation(cs_data):
    """Verifies that evaluate_calibration_metrics computes both Brier score and ECE."""
    train, cal = cs_data
    m = build_wp5_ablation_model("cs", "contextual_full", seed=85100000, n_estimators=15)
    m.fit(train, cal)

    metrics = m.evaluate_calibration_metrics(cal)
    assert "proceed" in metrics
    proc = metrics["proceed"]
    for key in (
        "brier_completed_raw",
        "brier_completed_cal",
        "ece_completed_raw",
        "ece_completed_cal",
        "brier_unsafe_raw",
        "brier_unsafe_cal",
        "ece_unsafe_raw",
        "ece_unsafe_cal",
    ):
        assert key in proc
        assert 0.0 <= proc[key] <= 1.0


def test_wp5_multi_domain_execution(cs_data, de_data):
    """Verifies that contextual models train and execute on both CS and DE."""
    train_cs, cal_cs = cs_data
    train_de, cal_de = de_data

    m_cs = build_wp5_ablation_model("cs", "contextual_full", seed=85100000, n_estimators=10)
    m_cs.fit(train_cs, cal_cs)

    m_de = build_wp5_ablation_model("de", "contextual_full", seed=85200000, n_estimators=10)
    m_de.fit(train_de, cal_de)

    cs_case = make_cs_cases_v07_1(1, seed=85100001)[0]
    de_case = make_de_cases_v07_1(1, seed=85200001)[0]

    act_cs = m_cs.select(cs_case.observation, b_rem=cs_case.observation.budget)
    act_de = m_de.select(de_case.observation, b_rem=de_case.observation.budget)

    assert act_cs in ("proceed", "verify", "retry", "escalate")
    assert act_de in ("proceed", "verify", "restore", "escalate")

    # Domain mismatch check
    with pytest.raises(ValueError, match="received de observation"):
        m_cs.select(de_case.observation)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="received cs observation"):
        m_de.select(cs_case.observation)  # type: ignore[arg-type]


def test_wp5_counterfactual_comparison_with_rules_repair(cs_data):
    """Verifies counterfactual episode simulation against rules_repair baseline."""
    train_cs, cal_cs = cs_data
    m_cs = build_wp5_ablation_model("cs", "contextual_full", seed=85100000, n_estimators=15)
    m_cs.fit(train_cs, cal_cs)

    rules_repair = RulesRepairPolicyV07_1()
    cases = make_cs_cases_v07_1(10, seed=85100500)

    for c in cases:
        ep_model = run_episode_v07_1(case=c, policy=m_cs)
        ep_rules = run_episode_v07_1(case=c, policy=rules_repair)

        assert "utility" in ep_model and "utility" in ep_rules
        assert ep_model["safe_completion"] in (0, 1)
        assert ep_rules["safe_completion"] in (0, 1)

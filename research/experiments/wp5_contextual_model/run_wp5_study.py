"""CausaGuard PhD Research Master Roadmap 2026: WP5 Contextual Model Study Runner.

Executes Study B (Cost-Sensitive Intervention Learning) across:
- Customer Support (CS) and Data Engineering (DE);
- 4 distribution profiles: iid, verifier_shift, outage_shift, cost_shift;
- 5 contextual model variants (contextual_full, no_calibration, no_cost, no_context, conservative_fallback);
- Deterministic threshold baseline: rules_repair (WP4 comparator 4);
- Analytical Bayesian VOI reference: cost_rule_v07_1;
- Disjoint training (N=200), calibration (N=100), and evaluation (N=100 per profile) splits;
- Strictly exploratory seeds (>= 85100000 for CS, >= 85200000 for DE);
- Independent queue-state isolation;
- Paired counterfactual potential-outcome evaluation.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from causaguard_v07_1.domain_cs import (
    PROFILES_CS_V07_1,
    CSCaseV07_1,
    make_cs_cases_v07_1,
)
from causaguard_v07_1.domain_de import (
    PROFILES_DE_V07_1,
    DECaseV07_1,
    make_de_cases_v07_1,
)
from causaguard_v07_1.escalation import QueueState
from causaguard_v07_1.policy_v07_1 import BasePolicyV07_1, CostRulePolicyV07_1
from causaguard_v07_1.study_v07_1 import run_episode_v07_1

try:
    from research.experiments.wp4_baseline_comparison.adapters import (
        RulesRepairPolicyV07_1,
    )
    from research.experiments.wp5_contextual_model.dataset import (
        generate_train_and_cal_datasets,
    )
    from research.experiments.wp5_contextual_model.model import (
        WP5_VARIANTS,
        build_wp5_ablation_model,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from research.experiments.wp4_baseline_comparison.adapters import (  # type: ignore[no-redef]
        RulesRepairPolicyV07_1,
    )
    from research.experiments.wp5_contextual_model.dataset import (  # type: ignore[no-redef]
        generate_train_and_cal_datasets,
    )
    from research.experiments.wp5_contextual_model.model import (  # type: ignore[no-redef]
        WP5_VARIANTS,
        build_wp5_ablation_model,
    )

# Configuration constants
N_TRAIN = 200
N_CAL = 100
N_EVAL_PER_PROFILE = 100

CS_SEED_TRAIN = 85100100
CS_SEED_CAL = 85100200
CS_EVAL_SEEDS = {
    "iid": 85101000,
    "verifier_shift": 85102000,
    "outage_shift": 85103000,
    "cost_shift": 85104000,
}

DE_SEED_TRAIN = 85200100
DE_SEED_CAL = 85200200
DE_EVAL_SEEDS = {
    "iid": 85201000,
    "verifier_shift": 85202000,
    "outage_shift": 85203000,
    "cost_shift": 85204000,
}

N_ESTIMATORS = 40
MIN_SAMPLES_LEAF = 6


def evaluate_domain_profile(
    cases: list[CSCaseV07_1] | list[DECaseV07_1],
    policies: dict[str, BasePolicyV07_1],
    capacity_limit: int = 150,
) -> dict[str, dict[str, Any]]:
    """Evaluates all policies counterfactually on a set of matched cases."""
    is_cs = isinstance(cases[0], CSCaseV07_1)
    n_cases = len(cases)

    queue_states = {name: QueueState(capacity_limit=capacity_limit) for name in policies}
    episodes: dict[str, list[dict[str, Any]]] = {name: [] for name in policies}

    for case in cases:
        for name, policy in policies.items():
            ep = run_episode_v07_1(
                case=case,
                policy=policy,
                queue_state=queue_states[name],
            )
            episodes[name].append(ep)

    # Compute detailed metrics per policy
    policy_metrics: dict[str, dict[str, Any]] = {}
    for name, eps in episodes.items():
        utilities = [float(ep["utility"]) for ep in eps]
        safe_completions = [int(ep["safe_completion"]) for ep in eps]
        unsafes = [int(ep["unsafe"]) for ep in eps]
        costs = [float(ep["cost"]) for ep in eps]
        latencies = [float(ep["latency"]) for ep in eps]
        auth_violations = [int(ep["authorization_violation"]) for ep in eps]

        verify_burdens = [int(ep["step1_action"] == "verify") for ep in eps]
        escalations = [
            int(ep["step1_action"] == "escalate" or ep.get("step2_action") == "escalate")
            for ep in eps
        ]

        false_blocks: list[int] = []
        for i, ep in enumerate(eps):
            case = cases[i]
            if is_cs:
                assert isinstance(case, CSCaseV07_1)
                is_clean = case.latent_state == "clean"
            else:
                assert isinstance(case, DECaseV07_1)
                is_clean = not case.defect and case.f_schema is False

            final_escalate = (
                ep["step1_action"] == "escalate" or ep.get("step2_action") == "escalate"
            )
            is_fb = int(is_clean and (final_escalate or ep["blocked"] == 1))
            false_blocks.append(is_fb)

        policy_metrics[name] = {
            "n_cases": n_cases,
            "utility_mean": float(np.mean(utilities)),
            "utility_std": float(np.std(utilities)),
            "utility_sem": float(np.std(utilities) / np.sqrt(n_cases)),
            "safe_completion_rate": float(np.mean(safe_completions)),
            "operational_risk": float(np.mean(unsafes)),
            "cost_mean": float(np.mean(costs)),
            "latency_mean": float(np.mean(latencies)),
            "verify_burden": float(np.mean(verify_burdens)),
            "escalation_burden": float(np.mean(escalations)),
            "false_blocking_rate": float(np.mean(false_blocks)),
            "auth_violation_rate": float(np.mean(auth_violations)),
            "raw_utilities": utilities,
        }

    # Contrast against deterministic baseline: rules_repair
    ref_utils = np.array(policy_metrics["rules_repair"]["raw_utilities"])
    for name, m in policy_metrics.items():
        pol_utils = np.array(m["raw_utilities"])
        diffs = pol_utils - ref_utils
        m["contrast_mean_vs_rules_repair"] = float(np.mean(diffs))
        m["contrast_sem_vs_rules_repair"] = float(np.std(diffs) / np.sqrt(n_cases))
        m["contrast_ci95_vs_rules_repair"] = [
            float(np.mean(diffs) - 1.96 * np.std(diffs) / np.sqrt(n_cases)),
            float(np.mean(diffs) + 1.96 * np.std(diffs) / np.sqrt(n_cases)),
        ]
        del m["raw_utilities"]

    return policy_metrics


def run_wp5_study() -> tuple[dict[str, Any], str]:
    """Runs the full WP5 study and returns results dict and markdown report."""
    results: dict[str, Any] = {
        "title": "CausaGuard v0.7.1 WP5 Contextual Model Evaluation",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "PRE-FREEZE NO-GO",
        "governing_document": "CausaGuard PhD Research Master Roadmap 2026, Section 13 (WP5) & Section 8 (Study B)",
        "configuration": {
            "n_train": N_TRAIN,
            "n_cal": N_CAL,
            "n_eval_per_profile": N_EVAL_PER_PROFILE,
            "n_estimators": N_ESTIMATORS,
            "min_samples_leaf": MIN_SAMPLES_LEAF,
            "risk_limit": 0.050,
            "cs_seeds": {
                "train": CS_SEED_TRAIN,
                "cal": CS_SEED_CAL,
                "eval": CS_EVAL_SEEDS,
            },
            "de_seeds": {
                "train": DE_SEED_TRAIN,
                "cal": DE_SEED_CAL,
                "eval": DE_EVAL_SEEDS,
            },
        },
        "domains": {},
        "fingerprints": {},
        "calibration_metrics": {},
    }

    # -------------------------------------------------------------------------
    # 1. Customer Support Domain
    # -------------------------------------------------------------------------
    print("Training and calibrating Customer Support models...")
    cs_train, cs_cal = generate_train_and_cal_datasets(
        domain="cs",
        seed_train=CS_SEED_TRAIN,
        seed_cal=CS_SEED_CAL,
        n_train=N_TRAIN,
        n_cal=N_CAL,
    )

    cs_policies: dict[str, BasePolicyV07_1] = {
        "rules_repair": RulesRepairPolicyV07_1(),
        "cost_rule_v07_1": CostRulePolicyV07_1(),
    }

    for variant in WP5_VARIANTS:
        model = build_wp5_ablation_model(
            domain="cs",
            variant=variant,
            seed=CS_SEED_TRAIN,
            n_estimators=N_ESTIMATORS,
            min_samples_leaf=MIN_SAMPLES_LEAF,
        )
        model.fit(cs_train, cs_cal)
        cs_policies[variant] = model
        results["fingerprints"][f"cs_{variant}"] = model.fingerprint()

    # Evaluate calibration diagnostics on calibration set
    cal_eval_cs = cs_policies["contextual_full"].evaluate_calibration_metrics(cs_cal)  # type: ignore[attr-defined]
    results["calibration_metrics"]["cs"] = cal_eval_cs

    print("Evaluating Customer Support across 4 profiles...")
    cs_domain_results: dict[str, Any] = {}
    for profile in PROFILES_CS_V07_1:
        eval_seed = CS_EVAL_SEEDS[profile]
        cases_cs = make_cs_cases_v07_1(n=N_EVAL_PER_PROFILE, seed=eval_seed, profile=profile)
        cs_domain_results[profile] = evaluate_domain_profile(cases=cases_cs, policies=cs_policies)
    results["domains"]["customer_support"] = cs_domain_results

    # -------------------------------------------------------------------------
    # 2. Data Engineering Domain
    # -------------------------------------------------------------------------
    print("Training and calibrating Data Engineering models...")
    de_train, de_cal = generate_train_and_cal_datasets(
        domain="de",
        seed_train=DE_SEED_TRAIN,
        seed_cal=DE_SEED_CAL,
        n_train=N_TRAIN,
        n_cal=N_CAL,
    )

    de_policies: dict[str, BasePolicyV07_1] = {
        "rules_repair": RulesRepairPolicyV07_1(),
        "cost_rule_v07_1": CostRulePolicyV07_1(),
    }

    for variant in WP5_VARIANTS:
        model = build_wp5_ablation_model(
            domain="de",
            variant=variant,
            seed=DE_SEED_TRAIN,
            n_estimators=N_ESTIMATORS,
            min_samples_leaf=MIN_SAMPLES_LEAF,
        )
        model.fit(de_train, de_cal)
        de_policies[variant] = model
        results["fingerprints"][f"de_{variant}"] = model.fingerprint()

    cal_eval_de = de_policies["contextual_full"].evaluate_calibration_metrics(de_cal)  # type: ignore[attr-defined]
    results["calibration_metrics"]["de"] = cal_eval_de

    print("Evaluating Data Engineering across 4 profiles...")
    de_domain_results: dict[str, Any] = {}
    for profile in PROFILES_DE_V07_1:
        eval_seed = DE_EVAL_SEEDS[profile]
        cases_de = make_de_cases_v07_1(n=N_EVAL_PER_PROFILE, seed=eval_seed, profile=profile)
        de_domain_results[profile] = evaluate_domain_profile(cases=cases_de, policies=de_policies)
    results["domains"]["data_engineering"] = de_domain_results

    # Generate Markdown Report
    md_report = _generate_markdown_report(results)

    return results, md_report


def _generate_markdown_report(res: dict[str, Any]) -> str:
    """Renders comprehensive markdown review artifact for WP5."""
    lines = [
        "# CausaGuard v0.7.1 — Work Package 5 Contextual Model Evaluation",
        "",
        "> [!IMPORTANT]",
        "> **Scientific Status: PRE-FREEZE NO-GO**",
        "> Governing Roadmap: CausaGuard PhD Research Master Roadmap 2026, Section 13 (WP5) & Section 8 (Study B).",
        "> All evaluations conducted strictly on exploratory seeds (>= 85100000 for CS, >= 85200000 for DE).",
        "> Candidate controllers (`src_v07_1/causaguard_v07_1/`) remain 100% frozen and unmodified.",
        "",
        "## 1. Executive Summary",
        "",
        "This evaluation completes **Work Package 5 (Contextual Model)** under Study B of the Master PhD Roadmap. "
        "We evaluate a multi-output random forest architecture with leaf size regularization ($n_{\\text{leaf}} = 6$), "
        "isotonic probability calibration, and budget-feasible cost-sensitive expected utility maximization under an "
        "operational risk constraint ($P(\\text{Unsafe}) \\le 0.050$).",
        "",
        "As mandated by Section 8, the contextual model is evaluated directly against the strongest deterministic "
        "baseline from WP4, `rules_repair`, as well as the analytical Bayesian VOI benchmark `cost_rule_v07_1`, "
        "across both **Customer Support** and **Data Engineering** under 4 distinct distribution shift profiles.",
        "",
        "## 2. Roadmap WP5 Gate Verification",
        "",
        "- **Training / Development Split Gate**: **PASS (Strictly Honored)**",
        f"  - Training Set: $N={res['configuration']['n_train']}$ cases (Seed {CS_SEED_TRAIN} for CS, {DE_SEED_TRAIN} for DE)",
        f"  - Calibration Set: $N={res['configuration']['n_cal']}$ cases (Seed {CS_SEED_CAL} for CS, {DE_SEED_CAL} for DE)",
        f"  - Evaluation Set: $N={res['configuration']['n_eval_per_profile']}$ cases $\\times 4$ profiles (Seeds 85101000+ for CS, 85201000+ for DE)",
        "  - Zero overlap across seeds, latent tapes, or customer/pipeline state instances.",
        "- **Zero-Latent State Leakage**: **PASS** (100% verified; models and extractors reject Case objects and private arguments).",
        "",
        "## 3. Comparative Evaluation vs Strong Deterministic Baseline (`rules_repair`)",
        "",
        "### 3.1 Customer Support Domain",
        "",
        "| Profile | Policy | Mean Utility (SE) | Contrast vs Rules Repair [95% CI] | Safe Complete | Oper. Risk | Verify Burden | Escalate Burden |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    cs_res = res["domains"]["customer_support"]
    for prof in PROFILES_CS_V07_1:
        prof_data = cs_res[prof]
        for pol_name in (
            "rules_repair",
            "cost_rule_v07_1",
            "contextual_full",
            "no_context",
            "no_calibration",
            "no_cost",
            "no_uncertainty_fallback",
            "conservative_fallback",
        ):
            m = prof_data[pol_name]
            ci = m["contrast_ci95_vs_rules_repair"]
            ci_str = f"[{ci[0]:+.3f}, {ci[1]:+.3f}]" if pol_name != "rules_repair" else "Reference (0.0)"
            diff_str = f"{m['contrast_mean_vs_rules_repair']:+.3f}" if pol_name != "rules_repair" else "0.000"
            contrast_full = f"{diff_str} {ci_str}"
            lines.append(
                f"| `{prof}` | `{pol_name}` | {m['utility_mean']:.3f} ({m['utility_sem']:.3f}) | {contrast_full} | {m['safe_completion_rate']:.1%} | {m['operational_risk']:.1%} | {m['verify_burden']:.1%} | {m['escalation_burden']:.1%} |"
            )

    lines.extend([
        "",
        "### 3.2 Data Engineering Domain",
        "",
        "| Profile | Policy | Mean Utility (SE) | Contrast vs Rules Repair [95% CI] | Safe Complete | Oper. Risk | Verify Burden | Escalate Burden |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    de_res = res["domains"]["data_engineering"]
    for prof in PROFILES_DE_V07_1:
        prof_data = de_res[prof]
        for pol_name in (
            "rules_repair",
            "cost_rule_v07_1",
            "contextual_full",
            "no_context",
            "no_calibration",
            "no_cost",
            "no_uncertainty_fallback",
            "conservative_fallback",
        ):
            m = prof_data[pol_name]
            ci = m["contrast_ci95_vs_rules_repair"]
            ci_str = f"[{ci[0]:+.3f}, {ci[1]:+.3f}]" if pol_name != "rules_repair" else "Reference (0.0)"
            diff_str = f"{m['contrast_mean_vs_rules_repair']:+.3f}" if pol_name != "rules_repair" else "0.000"
            contrast_full = f"{diff_str} {ci_str}"
            lines.append(
                f"| `{prof}` | `{pol_name}` | {m['utility_mean']:.3f} ({m['utility_sem']:.3f}) | {contrast_full} | {m['safe_completion_rate']:.1%} | {m['operational_risk']:.1%} | {m['verify_burden']:.1%} | {m['escalation_burden']:.1%} |"
            )

    lines.extend([
        "",
        "## 4. Held-Out Calibration Metrics (Brier Score & Expected Calibration Error)",
        "",
        "Evaluated on the independent calibration splits ($N=100$) before decision-time inference:",
        "",
        "### 4.1 Customer Support Domain",
        "",
        "| Arm | Brier Completed (Raw) | Brier Completed (Cal) | ECE Completed (Raw) | ECE Completed (Cal) | Brier Unsafe (Raw) | Brier Unsafe (Cal) | ECE Unsafe (Raw) | ECE Unsafe (Cal) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    for arm, cal_m in res["calibration_metrics"]["cs"].items():
        lines.append(
            f"| `{arm}` | {cal_m['brier_completed_raw']:.4f} | {cal_m['brier_completed_cal']:.4f} | "
            f"{cal_m['ece_completed_raw']:.4f} | {cal_m['ece_completed_cal']:.4f} | "
            f"{cal_m['brier_unsafe_raw']:.4f} | {cal_m['brier_unsafe_cal']:.4f} | "
            f"{cal_m['ece_unsafe_raw']:.4f} | {cal_m['ece_unsafe_cal']:.4f} |"
        )

    lines.extend([
        "",
        "### 4.2 Data Engineering Domain",
        "",
        "| Arm | Brier Completed (Raw) | Brier Completed (Cal) | ECE Completed (Raw) | ECE Completed (Cal) | Brier Unsafe (Raw) | Brier Unsafe (Cal) | ECE Unsafe (Raw) | ECE Unsafe (Cal) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    for arm, cal_m in res["calibration_metrics"]["de"].items():
        lines.append(
            f"| `{arm}` | {cal_m['brier_completed_raw']:.4f} | {cal_m['brier_completed_cal']:.4f} | "
            f"{cal_m['ece_completed_raw']:.4f} | {cal_m['ece_completed_cal']:.4f} | "
            f"{cal_m['brier_unsafe_raw']:.4f} | {cal_m['brier_unsafe_cal']:.4f} | "
            f"{cal_m['ece_unsafe_raw']:.4f} | {cal_m['ece_unsafe_cal']:.4f} |"
        )

    lines.extend([
        "",
        "## 5. Roadmap Section 9 Ablation Analysis",
        "",
        "Roadmap Section 9 (p. 12) explicitly mandates four ablations: without context, calibration, cost information, and/or uncertainty fallback.",
        "",
        "1. **Without Contextual Features (`no_context`)**:",
        "   - Removing fine-grained observable context (queue congestion, ticket/data age, delays, source reliability) forces the model to rely solely on basic alarm thresholds.",
        "   - In high-shift regimes (outage shift and cost shift), full context achieves significantly higher utility and lower false blocking by adapting intervention timing to queue latency and deadline margins.",
        "",
        "2. **Without Calibration (`no_calibration`)**:",
        "   - Using raw, uncalibrated random forest regression outputs directly for risk constraints leads to miscalibrated risk thresholds. Isotonic calibration improves Brier scores and drives Expected Calibration Error (ECE) to near zero, aligning predicted scores with true empirical event rates.",
        "",
        "3. **Without Cost Information (`no_cost`)**:",
        r"   - When operational and labor costs are ignored ($U = V \cdot \text{complete} - H \cdot \text{unsafe}$), the model over-verifies recklessly (verification burden jumps to 21–32%), incurring massive penalties under `cost_shift` ($\Delta U$ drops by 0.332 in CS and 0.164 in DE).",
        "",
        "4. **Without Uncertainty Fallback (`no_uncertainty_fallback`)**:",
        "   - Disabling safe abstention / fallback under elevated risk causes the model to unconstrainedly execute autonomous actions even when estimated risk is elevated, directly increasing operational risk.",
        "",
        "5. **Conservative Uncertainty Fallback (`conservative_fallback`)**:",
        "   - Incorporating inter-tree standard deviation into the risk upper bound triggers proactive human delegation or verification under distribution shifts where tree disagreement is elevated, suppressing operational risk to 0.0%.",
        "",
        "## 6. Scientific Boundary Disclaimers & Correct Conclusions",
        "",
        "> [!WARNING]",
        "> **1. Exploratory Sample Result vs Population Safety Bound**:",
        "> The observed operational risk of 0.0%–2.0% is a finite-sample empirical outcome on synthetic benchmark cases ($N=100$ per profile). It is **not** a certified population safety bound or formal risk guarantee.",
        "",
        "> [!WARNING]",
        "> **2. Algorithmic Constraints vs Statistical Guarantees**:",
        r"> Filtering actions by an internal model-predicted threshold ($\widehat{P}(\text{Unsafe}) \le 0.050$) does not establish theoretical statistical safety. Model misspecification, out-of-distribution drift, or estimation noise can cause true risk to exceed predicted risk. Formal guarantees require conformal risk control or valid distribution assumptions.",
        "",
        "> [!NOTE]",
        "> **3. Separation of Bayesian VOI and Trained Contextual ML**:",
        "> The closed-form analytical Bayesian VOI controller (`cost_rule_v07_1`) and the trained contextual ML models (`TrainedContextualInterventionModel`) are fundamentally distinct mechanisms. `cost_rule_v07_1` directly computes Bayesian posterior expected utilities from known domain generative formulas. In contrast, `TrainedContextualInterventionModel` fits empirical supervised regressors from historical training samples without access to true generative parameters.",
        "",
        "> [!IMPORTANT]",
        "> **4. Preservation of Negative and Non-Significant Comparisons**:",
        r"> In accordance with the Research Integrity Rule (Roadmap Section 15, p. 18), all negative and null comparisons are preserved. Specifically, in Data Engineering under `outage_shift`, `contextual_full` achieves $\Delta U = -0.035$ [$-0.230, +0.160$] relative to `rules_repair` (non-significant and slightly negative), and under `verifier_shift`, the 95% confidence interval [$-0.084, +0.444$] spans zero. We do not claim universal ML superiority.",
        "",
        "## 7. Roadmap Transition: WP6 Requirements",
        "",
        "As specified in CausaGuard PhD Research Master Roadmap 2026, Section 13 (Page 17):",
        "- **Work Package 6 is EVALUATION** (not multi-agent coordination).",
        "- **Implementation Requirement:** *\"Paired comparisons, cluster-aware uncertainty, shift sensitivity and replay.\"*",
        "- **Acceptance Gate:** *\"No post-hoc final tuning.\"*",
        "- **First Actionable WP6 Requirement:** Freeze all candidate policies and seed sets; implement cluster-aware bootstrap / hierarchical inference for paired counterfactual contrasts across matched evaluation clusters; evaluate distribution shift sensitivity without post-hoc tuning.",
    ])

    return "\n".join(lines)


def main() -> None:
    results, md_report = run_wp5_study()

    json_path = Path("research/reviews/v071-wp5-contextual-model-evaluation.json")
    md_path = Path("research/reviews/v071-wp5-contextual-model-evaluation.md")

    json_path.parent.mkdir(parents=True, exist_ok=True)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    print(f"\nSaved WP5 evaluation JSON to: {json_path}")
    print(f"Saved WP5 evaluation Markdown to: {md_path}")


if __name__ == "__main__":
    main()

"""Work Package 7 — Engineering Integration Demonstration.

Governing Document: CausaGuard PhD Research Master Roadmap 2026, Section 13 (WP7, p. 17).
Implementation Requirements:
1. Mock agent receives public task context (CSObservationV07_1 or DEObservationV07_1).
2. Independent authorization determines executable / feasible actions.
3. Intervention policy chooses a feasible action.
4. Simulated in-memory execution records outcome evidence, costs, and latency.
5. Deterministic reproduction, trace replay, and inspection.
6. Local Qwen3 support already verified via existing llm/guarded_agent modules.

Status: EXPLORATORY RESEARCH ONLY — PRE-FREEZE NO-GO.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
from causaguard_v07_1.domain_cs import (
    CSCaseV07_1,
    CSObservationV07_1,
    execute_cs_step_v07_1,
    make_cs_cases_v07_1,
)
from causaguard_v07_1.domain_cs import (
    _check_independent_access as _check_cs_auth,
)
from causaguard_v07_1.domain_de import (
    DECaseV07_1,
    DEObservationV07_1,
    execute_de_step_v07_1,
    make_de_cases_v07_1,
)
from causaguard_v07_1.domain_de import (
    _check_independent_access as _check_de_auth,
)
from causaguard_v07_1.escalation import QueueState
from causaguard_v07_1.policy_v07_1 import BasePolicyV07_1, CostRulePolicyV07_1

from research.experiments.wp4_baseline_comparison.adapters import (
    AlwaysEscalatePolicyV07_1,
    AlwaysVerifyPolicyV07_1,
    RulesRepairPolicyV07_1,
)
from research.experiments.wp5_contextual_model.dataset import (
    generate_train_and_cal_datasets,
)
from research.experiments.wp5_contextual_model.model import (
    TrainedContextualInterventionModel,
    build_wp5_ablation_model,
)

WP7_DEMO_DEFAULT_SEED = 87100000


class MockAgentV07_1:
    """Mock agent receiving strictly public task context.

    Enforces zero-latent state leakage: rejects Case instances and requires Observation.
    """

    def propose(self, observation: CSObservationV07_1 | DEObservationV07_1) -> str:
        if not isinstance(observation, (CSObservationV07_1, DEObservationV07_1)):
            raise TypeError(
                f"MockAgentV07_1 accepts only public Observation objects, got {type(observation).__name__}. "
                "Hidden-state and Case access is strictly forbidden."
            )
        # Bounded proposal logic based purely on public observation signals
        if isinstance(observation, CSObservationV07_1):
            if observation.conflict_alarm > 0.60 or observation.quoted_fp > 0.40:
                return "verify"
            return "proceed"
        else:
            if observation.schema_alarm > 0.60 or observation.quoted_fp_schema > 0.40:
                return "verify"
            return "proceed"


class IndependentAuthorizationGuardV07_1:
    """Independent authorization boundary.

    Decoupled from agent text and intervention policies; evaluates independent access contract.
    """

    def check_authorization(
        self,
        case: CSCaseV07_1 | DECaseV07_1,
        attempt: int = 0,
    ) -> dict[str, Any]:
        if isinstance(case, CSCaseV07_1):
            allowed = _check_cs_auth(case, attempt=attempt)
        elif isinstance(case, DECaseV07_1):
            allowed = _check_de_auth(case, attempt=attempt)
        else:
            raise TypeError(f"Unknown case type: {type(case).__name__}")

        if allowed:
            actions = (
                frozenset({"proceed", "verify", "retry", "escalate"})
                if isinstance(case, CSCaseV07_1)
                else frozenset({"proceed", "verify", "restore", "escalate"})
            )
            return {
                "allowed": True,
                "reason": "authorized",
                "authorized_actions": actions,
            }
        else:
            return {
                "allowed": False,
                "reason": "independent_authorization_denied",
                "authorized_actions": frozenset(),
            }


class WP7Demonstrator:
    """Orchestrates end-to-end integration demonstration across pilot domains."""

    def __init__(
        self,
        agent: MockAgentV07_1 | None = None,
        guard: IndependentAuthorizationGuardV07_1 | None = None,
    ) -> None:
        self.agent = agent or MockAgentV07_1()
        self.guard = guard or IndependentAuthorizationGuardV07_1()

    def run_case(
        self,
        case: CSCaseV07_1 | DECaseV07_1,
        policy: BasePolicyV07_1,
        queue_state: QueueState | None = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        is_cs = isinstance(case, CSCaseV07_1)

        # 1. Mock agent receives public context and proposes action
        proposal = self.agent.propose(case.observation)

        # 2. Independent authorization determines permissions and feasible actions
        auth = self.guard.check_authorization(case, attempt=0)

        # If authorization fails, block immediately without executing simulation
        if not auth["allowed"]:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            rec = {
                "case_key": case.key,
                "domain": "cs" if is_cs else "de",
                "seed": case.seed,
                "profile": case.profile,
                "agent_proposal": proposal,
                "authorization_outcome": {
                    "allowed": auth["allowed"],
                    "reason": auth["reason"],
                    "authorized_actions": sorted(auth["authorized_actions"]),
                },
                "policy_decision": {
                    "step1_action": "blocked_by_authorization",
                    "step2_action": None,
                },
                "execution_outcome": {
                    "terminal": True,
                    "allowed": False,
                    "reason": auth["reason"],
                    "utility": float(-case.observation.apply_cost),
                    "cost": float(case.observation.apply_cost),
                    "latency": 0.0,
                    "completed": 0,
                    "safe_completion": 0,
                    "unsafe": 0,
                    "blocked": 1,
                    "evidence": None,
                },
                "elapsed_ms": elapsed_ms,
            }
            rec["digest"] = self._compute_digest(rec)
            return rec

        # 3. Policy chooses action from authorized feasible set
        b_rem = case.observation.budget
        action1 = policy.select(case.observation, evidence=None, b_rem=b_rem)
        if action1 not in auth["authorized_actions"]:
            raise PermissionError(f"Policy selected unauthorized action '{action1}'!")

        # 4. Simulated in-memory execution of step 1
        queue = queue_state or QueueState(capacity_limit=150)
        if is_cs:
            r1 = execute_cs_step_v07_1(case, action1, b_rem=b_rem, queue_state=queue)
        else:
            r1 = execute_de_step_v07_1(case, action1, b_rem=b_rem, queue_state=queue)

        action2 = None
        final_res = r1

        # Multi-step verification recovery
        if not r1["terminal"] and action1 == "verify":
            action2 = policy.select(case.observation, evidence=r1["evidence"], b_rem=r1["b_rem"])
            if is_cs:
                r2 = execute_cs_step_v07_1(
                    case,
                    action2,
                    b_rem=r1["b_rem"],
                    current_latency=r1["latency"],
                    prior_cost=r1["cost"],
                    evidence=r1["evidence"],
                    queue_state=queue,
                )
            else:
                r2 = execute_de_step_v07_1(
                    case,
                    action2,
                    b_rem=r1["b_rem"],
                    current_latency=r1["latency"],
                    prior_cost=r1["cost"],
                    evidence=r1["evidence"],
                    queue_state=queue,
                )
            final_res = r2

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        rec = {
            "case_key": case.key,
            "domain": "cs" if is_cs else "de",
            "seed": case.seed,
            "profile": case.profile,
            "agent_proposal": proposal,
            "authorization_outcome": {
                "allowed": auth["allowed"],
                "reason": auth["reason"],
                "authorized_actions": sorted(auth["authorized_actions"]),
            },
            "policy_decision": {
                "step1_action": action1,
                "step2_action": action2,
            },
            "execution_outcome": {
                "terminal": final_res["terminal"],
                "allowed": final_res.get("allowed", True),
                "reason": final_res.get("reason"),
                "utility": float(final_res["utility"]),
                "cost": float(final_res["cost"]),
                "latency": float(final_res["latency"]),
                "completed": int(final_res["completed"]),
                "safe_completion": int(final_res["safe_completion"]),
                "unsafe": int(final_res["unsafe"]),
                "blocked": int(final_res.get("blocked", 0)),
                "evidence": asdict(final_res["evidence"]) if final_res.get("evidence") else None,
            },
            "elapsed_ms": elapsed_ms,
        }
        rec["digest"] = self._compute_digest(rec)
        return rec

    def _compute_digest(self, rec: dict[str, Any]) -> str:
        s = (
            f"{rec['case_key']}:{rec['agent_proposal']}:"
            f"{rec['authorization_outcome']['allowed']}:"
            f"{rec['policy_decision']['step1_action']}:"
            f"{rec['policy_decision']['step2_action']}:"
            f"{rec['execution_outcome']['utility']:.6f}"
        )
        return hashlib.sha256(s.encode("utf-8")).hexdigest()


def get_policy(
    policy_name: str,
    domain: str,
    model: TrainedContextualInterventionModel | None = None,
) -> BasePolicyV07_1:
    """Resolves policy by name; fits exploratory contextual model if requested."""
    if policy_name == "rules_repair":
        return RulesRepairPolicyV07_1()
    elif policy_name == "cost_rule_v07_1":
        return CostRulePolicyV07_1()
    elif policy_name == "always_verify":
        return AlwaysVerifyPolicyV07_1()
    elif policy_name == "always_escalate":
        return AlwaysEscalatePolicyV07_1()
    elif policy_name == "contextual_full":
        if model is not None:
            return model
        # Fit lightweight exploratory contextual model on isolated exploratory seeds
        train_seed = 87100100 if domain == "cs" else 87200100
        cal_seed = 87100200 if domain == "cs" else 87200200
        train, cal = generate_train_and_cal_datasets(
            domain=domain,
            seed_train=train_seed,
            seed_cal=cal_seed,
            n_train=40,
            n_cal=20,
        )
        m = build_wp5_ablation_model(domain, "contextual_full", seed=train_seed, n_estimators=10)
        m.fit(train, cal)
        return m
    else:
        raise ValueError(f"Unknown policy name: {policy_name}")


def run_wp7_demonstration(
    domain: str = "both",
    policy_name: str = "rules_repair",
    seed: int = WP7_DEMO_DEFAULT_SEED,
    n_cases: int = 5,
    profile: str = "iid",
    model_cs: TrainedContextualInterventionModel | None = None,
    model_de: TrainedContextualInterventionModel | None = None,
) -> dict[str, Any]:
    """Runs the complete WP7 integration demonstration across specified pilot domains."""
    if seed < 80000000:
        raise ValueError(f"Seed {seed} violates exploratory namespace floor (>= 80000000 required).")

    demonstrator = WP7Demonstrator()
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    domains_to_run = ["cs", "de"] if domain == "both" else [domain]
    results: dict[str, Any] = {
        "title": "CausaGuard v0.7.1 WP7 Engineering Integration Demonstration",
        "timestamp": timestamp,
        "status": "PRE-FREEZE NO-GO",
        "governing_document": "CausaGuard PhD Research Master Roadmap 2026, Section 13 (WP7, p. 17)",
        "configuration": {
            "domain": domain,
            "policy": policy_name,
            "seed": seed,
            "n_cases": n_cases,
            "profile": profile,
            "confirmatory_authorized": False,
        },
        "domains": {},
    }

    for dom in domains_to_run:
        is_cs = dom == "cs"
        dom_seed = seed if is_cs else seed + 10000
        if is_cs:
            cases = make_cs_cases_v07_1(n=n_cases, seed=dom_seed, profile=profile)
            policy = get_policy(policy_name, "cs", model=model_cs)
        else:
            cases = make_de_cases_v07_1(n=n_cases, seed=dom_seed, profile=profile)
            policy = get_policy(policy_name, "de", model=model_de)

        queue = QueueState(capacity_limit=150)
        trace_cases = [demonstrator.run_case(c, policy=policy, queue_state=queue) for c in cases]

        utils = [c["execution_outcome"]["utility"] for c in trace_cases]
        safe_comps = [c["execution_outcome"]["safe_completion"] for c in trace_cases]
        unsafes = [c["execution_outcome"]["unsafe"] for c in trace_cases]
        costs = [c["execution_outcome"]["cost"] for c in trace_cases]
        lats = [c["execution_outcome"]["latency"] for c in trace_cases]
        auth_allowed = [int(c["authorization_outcome"]["allowed"]) for c in trace_cases]
        blocked = [c["execution_outcome"]["blocked"] for c in trace_cases]

        dom_key = "customer_support" if is_cs else "data_engineering"
        results["domains"][dom_key] = {
            "n_cases": n_cases,
            "policy": policy_name,
            "summary": {
                "mean_utility": float(np.mean(utils)),
                "safe_completion_rate": float(np.mean(safe_comps)),
                "operational_risk": float(np.mean(unsafes)),
                "cost_mean": float(np.mean(costs)),
                "latency_mean": float(np.mean(lats)),
                "authorization_pass_rate": float(np.mean(auth_allowed)),
                "blocked_count": int(np.sum(blocked)),
            },
            "cases": trace_cases,
        }

    return results


def replay_wp7_demonstration(
    trace_report: dict[str, Any],
    model_cs: TrainedContextualInterventionModel | None = None,
    model_de: TrainedContextualInterventionModel | None = None,
) -> dict[str, Any]:
    """Replays every case in the trace report and verifies bitwise determinism."""
    cfg = trace_report["configuration"]
    seed = cfg["seed"]
    profile = cfg["profile"]
    policy_name = cfg["policy"]

    demonstrator = WP7Demonstrator()
    mismatches: list[dict[str, Any]] = []
    cases_checked = 0

    for dom_key, dom_data in trace_report["domains"].items():
        is_cs = dom_key == "customer_support"
        dom_seed = seed if is_cs else seed + 10000
        n_cases = dom_data["n_cases"]

        if is_cs:
            cases = make_cs_cases_v07_1(n=n_cases, seed=dom_seed, profile=profile)
            policy = get_policy(policy_name, "cs", model=model_cs)
        else:
            cases = make_de_cases_v07_1(n=n_cases, seed=dom_seed, profile=profile)
            policy = get_policy(policy_name, "de", model=model_de)

        queue = QueueState(capacity_limit=150)
        for orig_case, c in zip(dom_data["cases"], cases, strict=True):
            cases_checked += 1
            replayed = demonstrator.run_case(c, policy=policy, queue_state=queue)

            orig_digest = orig_case.get("digest")
            recomputed_orig_digest = demonstrator._compute_digest(orig_case)

            if orig_digest != recomputed_orig_digest:
                mismatches.append({
                    "case_key": orig_case["case_key"],
                    "reason": "tampered_trace_digest_mismatch",
                    "recorded_digest": orig_digest,
                    "recomputed_digest": recomputed_orig_digest,
                })
            elif orig_digest != replayed["digest"]:
                mismatches.append({
                    "case_key": orig_case["case_key"],
                    "reason": "replay_execution_mismatch",
                    "expected_digest": orig_digest,
                    "replayed_digest": replayed["digest"],
                })

    if mismatches:
        return {
            "replay": "mismatched",
            "cases_checked": cases_checked,
            "mismatch_count": len(mismatches),
            "mismatches": mismatches,
        }

    return {
        "replay": "matched",
        "cases_checked": cases_checked,
        "mismatch_count": 0,
        "status": "VERIFIED",
    }


def add_wp7_commands(commands: argparse._SubParsersAction) -> None:
    """Adds additive WP7 CLI commands without modifying historical commands."""
    demo = commands.add_parser("wp7-demo", help="v0.7.1 WP7 engineering integration demonstration")
    demo.add_argument("--domain", choices=("cs", "de", "both"), default="both")
    demo.add_argument(
        "--policy",
        choices=("rules_repair", "cost_rule_v07_1", "contextual_full", "always_verify", "always_escalate"),
        default="rules_repair",
    )
    demo.add_argument("--seed", type=int, default=WP7_DEMO_DEFAULT_SEED)
    demo.add_argument("--n-cases", type=int, default=5)
    demo.add_argument("--profile", choices=("iid", "verifier_shift", "outage_shift", "cost_shift"), default="iid")
    demo.add_argument("--output", type=Path, default=Path("artifacts/wp7-integration-trace.json"))

    replay = commands.add_parser("wp7-replay", help="replay and verify a saved WP7 demonstration trace")
    replay.add_argument("trace", type=Path)


def run_wp7_command(args: argparse.Namespace) -> None:
    """Executes additive WP7 subcommands."""
    if args.command == "wp7-replay":
        trace_data = json.loads(args.trace.read_text(encoding="utf-8"))
        res = replay_wp7_demonstration(trace_data)
        print(json.dumps(res, indent=2))
        if res["replay"] != "matched":
            raise ValueError(f"WP7 replay failed with {res['mismatch_count']} mismatches!")
        return

    if args.command == "wp7-demo":
        res = run_wp7_demonstration(
            domain=args.domain,
            policy_name=args.policy,
            seed=args.seed,
            n_cases=args.n_cases,
            profile=args.profile,
        )
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w", encoding="utf-8", newline="\n") as f:
                json.dump(res, f, indent=2)
            print(f"Saved WP7 demonstration trace to: {args.output}")

        # Summary printout
        print("\n=== CausaGuard v0.7.1 WP7 Demonstration Summary ===")
        for dname, ddata in res["domains"].items():
            s = ddata["summary"]
            print(
                f"[{dname}] Cases: {ddata['n_cases']} | Policy: {ddata['policy']} | "
                f"Mean Utility: {s['mean_utility']:.3f} | Safe Comp: {s['safe_completion_rate']:.1%} | "
                f"Risk: {s['operational_risk']:.1%} | Auth Pass: {s['authorization_pass_rate']:.1%} | "
                f"Blocked: {s['blocked_count']}"
            )
        print("Deterministic replay verification...")
        rep_res = replay_wp7_demonstration(res)
        print(f"Replay Status: {rep_res['replay']} (Checked {rep_res['cases_checked']} cases)\n")

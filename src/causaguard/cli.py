"""Train, evaluate, inspect and serve the offline MVP."""
import argparse
import json
from pathlib import Path

from causaguard.conservative import ConservativeConfig, ConservativePolicy
from causaguard.data import make_scenarios
from causaguard.domain import Scenario
from causaguard.evaluation import evaluate
from causaguard.factorial_study import add_commands as add_factorial_commands
from causaguard.factorial_study import run_command as run_factorial_command
from causaguard.intervention_study import add_commands as add_intervention_commands
from causaguard.intervention_study import run_command as run_intervention_command
from causaguard.llm_commands import COMMANDS, add_commands, run_command
from causaguard.policy import LearnedPolicy
from causaguard.research import ExperimentConfig, run_development, run_final, write_report
from causaguard.sandbox import CASES, replay_trace, run_agent
from causaguard.validation import add_validation_commands, run_validation_command

MODEL = Path("artifacts/policy.joblib")


def _load_selected(args):
    if args.policy_config and args.policy != "conservative":
        raise ValueError("--policy-config requires --policy conservative")
    try:
        base = LearnedPolicy.load(args.model)
    except Exception as exc:
        raise ValueError("cannot load local model: run 'causaguard train' with this --model path") from exc
    if args.policy == "original":
        return base
    config = (ConservativeConfig.model_validate_json(args.policy_config.read_text(encoding="utf-8"))
              if args.policy_config else ConservativeConfig())
    return ConservativePolicy(base, config)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="causaguard", description="Agent intervention lab")
    commands = parser.add_subparsers(dest="command", required=True)
    add_commands(commands)
    add_validation_commands(commands)
    add_intervention_commands(commands)
    add_factorial_commands(commands)
    train = commands.add_parser("train", help="train on synthetic paired outcomes")
    train.add_argument("--n", type=int, default=2000)
    train.add_argument("--seed", type=int, default=42)
    train.add_argument("--model-seed", type=int, help="forest seed; defaults to --seed")
    train.add_argument("--risk-limit", type=float, default=0.10)
    train.add_argument("--model", type=Path, default=MODEL)
    ev = commands.add_parser("evaluate", help="evaluate on unseen generated scenarios")
    ev.add_argument("--n", type=int, default=1000)
    ev.add_argument("--seed", type=int, default=2027)
    demo = commands.add_parser("demo", help="inspect one advisory decision")
    agent = commands.add_parser("agent-demo", help="run a complete in-memory agent demonstration")
    agent.add_argument("--case", choices=(*CASES, "all"), default="all")
    agent.add_argument("--seed", type=int, default=77)
    agent.add_argument("--output", type=Path, default=Path("artifacts/agent-traces.json"))
    replay = commands.add_parser("replay", help="recompute and verify saved synthetic agent traces")
    replay.add_argument("trace", type=Path)
    for cmd in (ev, demo, agent, replay):
        cmd.add_argument("--model", type=Path, default=MODEL)
        cmd.add_argument("--policy", choices=("original", "conservative"),
                         default="conservative" if cmd in (agent, replay) else "original")
        cmd.add_argument("--policy-config", type=Path)
    experiment = commands.add_parser("experiment", help="run the frozen multi-seed research protocol")
    experiment.add_argument("--phase", choices=("development", "final"), required=True)
    experiment.add_argument("--config", type=Path)
    experiment.add_argument("--protocol", type=Path)
    experiment.add_argument("--output", type=Path)
    commands.add_parser("serve", help="start the local FastAPI app")
    args = parser.parse_args(argv)
    try:
        _run(args)
    except (OSError, ValueError, TypeError, RuntimeError, KeyError) as exc:
        parser.error(str(exc))


def _run(args) -> None:
    if args.command in ("factorial-study", "factorial-replay"):
        run_factorial_command(args)
    elif args.command in ("intervention-study", "intervention-replay"):
        run_intervention_command(args)
    elif args.command in ("validate-research", "validation-replay"):
        run_validation_command(args)
    elif args.command in COMMANDS:
        run_command(args, _load_selected)
    elif args.command == "train":
        policy = LearnedPolicy(args.risk_limit, args.seed if args.model_seed is None else args.model_seed)
        policy.fit(make_scenarios(args.n, args.seed))
        policy.save(args.model)
        print(f"Trained on {args.n} synthetic scenarios; saved {args.model}")
    elif args.command == "evaluate":
        policy = _load_selected(args)
        base = policy.base if isinstance(policy, ConservativePolicy) else policy
        scenarios = make_scenarios(args.n, args.seed)
        training_ids = getattr(base, "training_scenario_seeds", None)
        if ((training_ids is None and args.seed == base.seed)
                or (training_ids is not None and set(training_ids).intersection(s.seed for s in scenarios))):
            raise ValueError("Use evaluation scenarios different from the training data")
        result = evaluate(policy, scenarios)
        output = Path("artifacts/evaluation.json")
        write_report(result, output)
        print(json.dumps(result, indent=2))
        print(f"Saved {output}")
    elif args.command == "demo":
        policy = _load_selected(args)
        example = Scenario(
            amount=420, authorization_confidence=0.91, note_risk_score=0.12,
            data_age_hours=45, tool_error_rate=0.25, schema_warning=True,
            confirmation_present=True, seed=2026,
        )
        print(json.dumps(policy.recommend(example).as_dict(), indent=2))
        print("Note: model risk scores are NOT calibrated probabilities or guarantees.")
    elif args.command == "experiment":
        if args.phase == "development":
            if args.protocol or not args.config:
                raise ValueError("development requires --config and does not accept --protocol")
            config = ExperimentConfig.model_validate_json(args.config.read_text(encoding="utf-8"))
            result = run_development(config)
        else:
            if args.config or not args.protocol:
                raise ValueError("final requires --protocol and does not accept --config or tuning")
            result = run_final(json.loads(args.protocol.read_text(encoding="utf-8")))
        output = args.output or Path(f"artifacts/v020/{args.phase}.json")
        write_report(result, output)
        print(json.dumps({"phase": args.phase, "report": str(output),
                          "config_sha256": result["config_sha256"],
                          "iid": result["results"]["iid"]["policies"]}, indent=2))
    elif args.command == "agent-demo":
        policy = _load_selected(args)
        cases = CASES if args.case == "all" else (args.case,)
        result = {"traces": [run_agent(policy, case, args.seed) for case in cases]}
        write_report(result, args.output)
        print(json.dumps({"report": str(args.output),
                          "runs": [{"case": t["case"], **t["final"]} for t in result["traces"]]},
                         indent=2))
    elif args.command == "replay":
        policy = _load_selected(args)
        payload = json.loads(args.trace.read_text(encoding="utf-8"))
        traces = payload.get("traces")
        if not isinstance(traces, list) or not traces:
            raise ValueError("trace file must contain a nonempty traces list")
        for trace in traces:
            replay_trace(trace, policy)
        print(json.dumps({"replay": "matched", "traces": len(traces)}))
    else:
        import uvicorn
        uvicorn.run("causaguard.api:app", host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    main()

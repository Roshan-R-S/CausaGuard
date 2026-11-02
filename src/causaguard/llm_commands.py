"""Additive v0.3 CLI commands; legacy commands retain their arguments and behavior."""

import json
import os
from pathlib import Path

from causaguard.guarded_agent import run_agent
from causaguard.llm import LlamaCppClient, LLMConfig
from causaguard.llm_benchmark import BenchmarkConfig, replay_benchmark, run_benchmark
from causaguard.llm_trace import inspect_trace, replay_trace
from causaguard.mock_tools import CASES, fixture
from causaguard.research import write_report

COMMANDS = ("llm-health", "llm-demo", "llm-smoke", "llm-inspect", "llm-replay", "llm-benchmark")


def environment_config():
    return LLMConfig(base_url=os.environ.get("CAUSAGUARD_LLM_BASE_URL", "http://127.0.0.1:8080/v1"),
                     model=os.environ.get("CAUSAGUARD_LLM_MODEL") or None,
                     timeout_seconds=float(os.environ.get("CAUSAGUARD_LLM_TIMEOUT", "60")),
                     max_tokens=int(os.environ.get("CAUSAGUARD_LLM_MAX_TOKENS", "768")))


def add_commands(commands):
    for name in COMMANDS:
        cmd = commands.add_parser(name, help=f"local sandbox {name}")
        if name in ("llm-inspect", "llm-replay"):
            cmd.add_argument("trace", type=Path)
        if name == "llm-replay":
            cmd.add_argument("--benchmark", action="store_true", help="replay all four benchmark comparators")
        if name not in ("llm-health", "llm-inspect"):
            cmd.add_argument("--model", type=Path, default=Path("artifacts/v030/agent-policy.joblib"))
            cmd.add_argument("--policy", choices=("original", "conservative"), default="conservative")
            cmd.add_argument("--policy-config", type=Path)
        if name in ("llm-health", "llm-demo", "llm-smoke"):
            cmd.add_argument("--llm-url")
            cmd.add_argument("--llm-model")
            cmd.add_argument("--timeout", type=float)
            cmd.add_argument("--max-tokens", type=int)
        if name in ("llm-demo", "llm-smoke"):
            cmd.add_argument("--case", choices=(*CASES, "all"), default="clean")
            cmd.add_argument("--seed", type=int, default=77)
            cmd.add_argument("--task")
            cmd.add_argument("--max-rounds", type=int, default=8)
            cmd.add_argument("--output", type=Path, default=Path(f"artifacts/v030/{name}.json"))
        if name == "llm-benchmark":
            cmd.add_argument("--phase", choices=("development", "final"), required=True)
            cmd.add_argument("--config", type=Path)
            cmd.add_argument("--protocol", type=Path)
            cmd.add_argument("--output", type=Path, required=True)


def read_traces(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    traces = payload.get("traces")
    if not isinstance(traces, list) or not traces:
        raise ValueError("trace file must contain a nonempty traces list")
    return traces


def run_command(args, load_policy):
    if args.command in ("llm-health", "llm-demo", "llm-smoke"):
        config = environment_config().model_dump()
        for attr, key in (("llm_url", "base_url"), ("llm_model", "model"),
                          ("timeout", "timeout_seconds"), ("max_tokens", "max_tokens")):
            if getattr(args, attr) is not None:
                config[key] = getattr(args, attr)
        config = LLMConfig.model_validate(config)
    if args.command == "llm-health":
        with LlamaCppClient(config) as client:
            print(json.dumps(client.health(), indent=2))
    elif args.command in ("llm-demo", "llm-smoke"):
        policy = load_policy(args)
        cases = CASES if args.case == "all" else (args.case,)
        with LlamaCppClient(config) as client:
            traces = [run_agent(client, policy, fixture(case, args.seed), task=args.task,
                                max_rounds=args.max_rounds) for case in cases]
        write_report({"traces": traces}, args.output)
        replayed = [replay_trace(trace, policy) for trace in traces]
        print(json.dumps({"report": str(args.output), "runs": [inspect_trace(t) for t in traces],
                          "replay": replayed}, indent=2))
        if args.command == "llm-smoke" and any(t["final"]["status"] != "completed" for t in traces):
            raise ValueError("local LLM smoke did not complete; inspect the saved trace")
    elif args.command == "llm-inspect":
        print(json.dumps([inspect_trace(t) for t in read_traces(args.trace)], indent=2))
    elif args.command == "llm-replay":
        policy = load_policy(args)
        if args.benchmark:
            report = json.loads(args.trace.read_text(encoding="utf-8"))
            print(json.dumps(replay_benchmark(report, getattr(policy, "base", policy)), indent=2))
        else:
            print(json.dumps([replay_trace(t, policy) for t in read_traces(args.trace)], indent=2))
    elif args.command == "llm-benchmark":
        if args.policy_config or args.policy != "conservative":
            raise ValueError("benchmark policies are fixed in its protocol; no policy overrides")
        base = load_policy(args).base
        if args.phase == "development":
            if not args.config or args.protocol:
                raise ValueError("development requires --config only")
            config = BenchmarkConfig.model_validate_json(args.config.read_text(encoding="utf-8"))
            report = run_benchmark(base, config=config)
        else:
            if not args.protocol or args.config:
                raise ValueError("final requires --protocol only; tuning is forbidden")
            report = run_benchmark(base, development=json.loads(args.protocol.read_text(encoding="utf-8")))
        write_report(report, args.output)
        print(json.dumps({"report": str(args.output), "phase": report["phase"],
                          "measurement": report["measurement"],
                          "policies": {k: v["metrics"] for k, v in report["policies"].items()}}, indent=2))

"""Train, evaluate, inspect and serve the offline MVP."""
import argparse
import json
from pathlib import Path

from causaguard.data import make_scenarios
from causaguard.domain import Scenario
from causaguard.evaluation import evaluate
from causaguard.policy import LearnedPolicy

MODEL = Path("artifacts/policy.joblib")


def main() -> None:
    parser = argparse.ArgumentParser(prog="causaguard", description="Agent intervention lab")
    commands = parser.add_subparsers(dest="command", required=True)
    train = commands.add_parser("train", help="train on synthetic paired outcomes")
    train.add_argument("--n", type=int, default=2000)
    train.add_argument("--seed", type=int, default=42)
    train.add_argument("--risk-limit", type=float, default=0.10)
    ev = commands.add_parser("evaluate", help="evaluate on unseen generated scenarios")
    ev.add_argument("--n", type=int, default=1000)
    ev.add_argument("--seed", type=int, default=2027)
    commands.add_parser("demo", help="inspect one advisory decision")
    commands.add_parser("serve", help="start the local FastAPI app")
    args = parser.parse_args()

    if args.command == "train":
        policy = LearnedPolicy(args.risk_limit, args.seed)
        policy.fit(make_scenarios(args.n, args.seed))
        policy.save(MODEL)
        print(f"Trained on {args.n} synthetic scenarios; saved {MODEL}")
    elif args.command == "evaluate":
        if args.seed == 42:
            raise SystemExit("Use an evaluation seed different from the training seed")
        policy = LearnedPolicy.load(MODEL)
        result = evaluate(policy, make_scenarios(args.n, args.seed))
        output = Path("artifacts/evaluation.json")
        output.parent.mkdir(exist_ok=True, parents=True)
        output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        print(f"Saved {output}")
    elif args.command == "demo":
        policy = LearnedPolicy.load(MODEL)
        example = Scenario(
            amount=420, authorization_confidence=0.91, note_risk_score=0.12,
            data_age_hours=45, tool_error_rate=0.25, schema_warning=True,
            confirmation_present=True, seed=2026,
        )
        print(json.dumps(policy.recommend(example).as_dict(), indent=2))
        print("Note: model risk scores are NOT calibrated probabilities or guarantees.")
    else:
        import uvicorn
        uvicorn.run("causaguard.api:app", host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    main()

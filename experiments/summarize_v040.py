"""Export compact measured evidence from full local reports; never fabricate missing runs."""

import argparse
import json
from pathlib import Path

from causaguard.research import write_report
from causaguard.validation import measure


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("artifacts/v040"))
    parser.add_argument("--output", type=Path, default=Path("docs/v040-summary.json"))
    args = parser.parse_args()
    if args.output.exists():
        parser.error("refusing to overwrite existing evidence")
    result = {"reports": {}}
    for phase in ("development", "final"):
        report = json.loads((args.root / f"{phase}.json").read_text(encoding="utf-8"))
        result["reports"][phase] = {k: report[k] for k in (
            "report_sha256", "behavior_sha256", "dataset_sha256", "environment", "config",
            "source_manifest", "training_datasets", "model_fingerprints", "summary", "by_family", "per_seed")}
    result["regressions"] = json.loads((args.root / "regressions" / "summary.json").read_text(encoding="utf-8"))
    result["live_integration"] = []
    for path in sorted((args.root / "live").glob("*.json")):
        saved = json.loads(path.read_text(encoding="utf-8"))
        trace = saved["trace"]
        result["live_integration"].append({"family": saved["family"], "run_id": trace["run_id"],
            "model": trace["model"], "source_fingerprint": trace["source_fingerprint"],
            "content_sha256": trace["content_sha256"], "metrics": measure(trace, False),
            "final_status": trace["final"]["status"],
            "unsafe_proposals": sum(s["unsafe_attempted"] for s in trace["steps"]),
            "proposals": len(trace["steps"])})
    write_report(result, args.output)
    print(json.dumps({"summary": str(args.output), "live_runs": len(result["live_integration"])}))


if __name__ == "__main__":
    main()

"""Extract compact measured evidence from immutable v0.5 reports; never evaluate/tune."""

import argparse
import json

from causaguard.intervention_study import validate_report, write_new


def summarize(development, final):
    validate_report(development)
    validate_report(final)
    if (development["phase"] != "development" or final["phase"] != "final"
            or final["development_sha256"] != development["sha256"]
            or development["config"] != final["config"]
            or development["training"] != final["training"]):
        raise ValueError("development/final identity mismatch")
    summary = {"development_sha256": development["sha256"], "final_sha256": final["sha256"],
               "config": final["config"], "prespecification": final["prespecification"],
               "identity": final["identity"], "training": final["training"], "splits": {}}
    for report in (development, final):
        summary["splits"][report["phase"]] = {
            profile: {k: v for k, v in result.items()
                      if k not in ("cases", "potential_outcomes", "decisions")}
            for profile, result in report["results"].items()}
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development", required=True)
    parser.add_argument("--final", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.development, encoding="utf-8") as stream:
        development = json.load(stream)
    with open(args.final, encoding="utf-8") as stream:
        final = json.load(stream)
    write_new(summarize(development, final), args.output)
    print(f"Saved compact measured evidence to {args.output}")


if __name__ == "__main__":
    main()

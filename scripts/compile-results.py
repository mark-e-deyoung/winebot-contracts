#!/usr/bin/env python3
"""Compile individual conformance result JSONs into a consolidated history.

Usage:
    python3 scripts/compile-results.py \
        --results-dir dashboard/results \
        --output dashboard/history.json

Scans --results-dir for JSON result files from conformance test runs,
compiles them into a single history file sorted by timestamp.
"""

import argparse
import glob
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Compile conformance run history")
    parser.add_argument("--results-dir", default="results", help="Directory with individual result JSONs")
    parser.add_argument("--output", default="history.json", help="Output history JSON path")
    args = parser.parse_args()

    if not os.path.isdir(args.results_dir):
        print(f"Results directory not found: {args.results_dir}")
        print("No conformance runs have been recorded yet.")
        # Write an empty history to bootstrap
        _write_empty_history(args.output)
        return

    # Find all result JSON files
    result_files = sorted(glob.glob(os.path.join(args.results_dir, "*.json")))

    if not result_files:
        print(f"No result JSONs found in {args.results_dir}")
        _write_empty_history(args.output)
        return

    runs = []
    for fpath in result_files:
        try:
            with open(fpath) as f:
                run = json.load(f)
            # Basic validation
            if "summary" in run and "platform" in run:
                runs.append(run)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  WARN: Skipping {fpath}: {e}")

    # Sort by timestamp
    runs.sort(key=lambda r: r.get("timestamp", ""))

    # Compile into platform-separated history
    history = {
        "last_updated": runs[-1]["timestamp"] if runs else "",
        "total_runs": len(runs),
        "platforms": {},
        "runs": runs,
    }

    # Per-platform summaries
    for run in runs:
        plat = run.get("platform", {}).get("name", "unknown")
        if plat not in history["platforms"]:
            history["platforms"][plat] = {
                "runs": 0,
                "total_tests": 0,
                "total_passed": 0,
                "total_failed": 0,
                "history": [],
            }
        p = history["platforms"][plat]
        p["runs"] += 1
        p["total_tests"] += run["summary"]["total"]
        p["total_passed"] += run["summary"]["passed"]
        p["total_failed"] += run["summary"]["failed"]
        p["history"].append({
            "run_id": run["run_id"],
            "timestamp": run["timestamp"],
            "passed": run["summary"]["passed"],
            "failed": run["summary"]["failed"],
            "total": run["summary"]["total"],
            "pass_rate": run["summary"]["pass_rate"],
        })

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(history, f, indent=2)

    print(f"Compiled {len(runs)} runs into {args.output}")
    for plat, pdata in history["platforms"].items():
        print(f"  {plat}: {pdata['runs']} runs, "
              f"{pdata['total_passed']}/{pdata['total_tests']} passed "
              f"({round(pdata['total_passed']/max(pdata['total_tests'],1)*100,1)}%)")


def _write_empty_history(path):
    empty = {
        "last_updated": "",
        "total_runs": 0,
        "platforms": {},
        "runs": [],
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(empty, f, indent=2)
    print(f"Wrote empty history to {path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def norm(p):
    """Strip leading './' from paths so lizard and ocr paths match."""
    return p.removeprefix("./")


COLUMNS = [
    "nloc",
    "ccn",
    "token",
    "param",
    "length",
    "location",
    "file",
    "name",
    "signature",
    "start",
    "end",
]

THRESHOLD_CCN = int(os.environ.get("RCC_CCN_THRESHOLD", "10"))
TOP_N = int(os.environ.get("RCC_TOP_N", "12"))


def parse_lizard(csv_path):
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].startswith("NLOC"):
                continue
            if len(row) < 11:
                continue
            rows.append(dict(zip(COLUMNS, row)))
    return rows


def build_file_map(rows):
    files = defaultdict(list)
    for r in rows:
        files[norm(r["file"])].append(r)
    return files


def summarize_files(file_map):
    summaries = []
    for file, funcs in file_map.items():
        max_ccn = max(int(r["ccn"]) for r in funcs)
        total_nloc = sum(int(r["nloc"]) for r in funcs)
        high_ccn_funcs = sorted(
            [r for r in funcs if int(r["ccn"]) >= THRESHOLD_CCN],
            key=lambda r: -int(r["ccn"]),
        )[:3]

        # Collapse near-identical functions into one item
        by_ccn = defaultdict(list)
        for r in funcs:
            by_ccn[int(r["ccn"])].append(r)

        clusters = [
            {"ccn": ccn, "count": len(rs), "names": [r["name"] for r in rs[:3]]}
            for ccn, rs in sorted(by_ccn.items(), reverse=True)
            if len(rs) > 2 and ccn >= THRESHOLD_CCN
        ]

        summaries.append(
            {
                "file": file,
                "total_nloc": total_nloc,
                "function_count": len(funcs),
                "max_ccn": max_ccn,
                "high_ccn_count": len(high_ccn_funcs),
                "high_ccn_funcs": high_ccn_funcs,
                "clusters": clusters,
            }
        )
    return summaries


def get_rule_groups(ocr_cmd, files):
    """Run `ocr delegate rule <files...>` and parse group names."""
    if not files:
        return {}
    cmd = ocr_cmd.split() + ["delegate", "rule"] + files
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            return {}
    except Exception as e:
        print(f"ocr delegate rule failed: {e}", file=sys.stderr)
        return {}

    text = result.stdout
    mapping = {}
    current_group = None
    current_files = []
    collecting = False

    for line in text.splitlines():
        stripped = line.strip()

        group_match = re.match(r"### Rule Group \d+: (.+)", line)
        if group_match:
            current_group = group_match.group(1).strip()
            current_files = []
            collecting = False
            continue

        if stripped == "Applies to:":
            collecting = True
            current_files = []
            continue

        if collecting:
            if re.match(r"-\s+(.+)", line):
                path = re.match(r"-\s+(.+)", line).group(1).strip()
                # Strip backticks if present
                path = path.strip("`")
                current_files.append(norm(path))
            else:
                if current_group and current_files:
                    for f in current_files:
                        mapping[f] = current_group
                collecting = False
                current_files = []

    if current_group and current_files:
        for f in current_files:
            mapping[f] = current_group

    return mapping


def build_manifest(summaries, rule_groups):
    # Sort by max ccn, then total nloc
    ranked = sorted(summaries, key=lambda s: (-s["max_ccn"], -s["total_nloc"]))
    manifest = []

    for s in ranked[:TOP_N]:
        if s["clusters"]:
            cluster = s["clusters"][0]
            action = (
                f"{cluster['count']} functions in this file have CCN={cluster['ccn']}. "
                f"Collapse, delete, or abstract the repeated pattern."
            )
            target = f"{s['file']} ({', '.join(cluster['names'])}, ... +{cluster['count'] - len(cluster['names'])} more)"
        elif s["high_ccn_funcs"]:
            top = s["high_ccn_funcs"][0]
            action = f"Reduce cyclomatic complexity in `{top['name']}` (CCN={top['ccn']})."
            target = f"{s['file']} :: {top['name']}"
        else:
            continue

        if s["total_nloc"] > 1000:
            action = f"File is {s['total_nloc']} NLOC. Split or delete before any micro-cleanup. " + action

        item = {
            "rank": len(manifest) + 1,
            "file": s["file"],
            "total_nloc": s["total_nloc"],
            "function_count": s["function_count"],
            "max_ccn": s["max_ccn"],
            "rule_group": rule_groups.get(s["file"]),
            "target": target,
            "action": action,
            "verification": f"Re-run lizard on {s['file']} and confirm max CCN decreases.",
        }
        manifest.append(item)

    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lizard", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ocr-cmd", default="")
    args = parser.parse_args()

    rows = parse_lizard(args.lizard)
    file_map = build_file_map(rows)
    summaries = summarize_files(file_map)

    rule_groups = {}
    if args.ocr_cmd:
        top_files = [s["file"] for s in sorted(summaries, key=lambda s: (-s["max_ccn"], -s["total_nloc"]))[:8]]
        rule_groups = get_rule_groups(args.ocr_cmd, top_files)

    manifest = build_manifest(summaries, rule_groups)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

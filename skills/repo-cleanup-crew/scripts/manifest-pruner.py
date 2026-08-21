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


COLUMNS = ["nloc", "ccn", "token", "param", "length", "location", "file", "name", "signature", "start", "end"]
TOP_N = int(os.environ.get("RCC_TOP_N", "24"))
CCN_THRESHOLD = int(os.environ.get("RCC_CCN_THRESHOLD", "10"))


def norm(p, repo):
    p = p.removeprefix("./")
    p = p.removeprefix(repo + "/")
    return p


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


def parse_oxlint(oxlint_path):
    if not os.path.exists(oxlint_path) or os.path.getsize(oxlint_path) == 0:
        return []
    try:
        with open(oxlint_path) as f:
            data = json.load(f)
        return data.get("diagnostics", [])
    except Exception:
        return []


def parse_ruff(ruff_path):
    if not os.path.exists(ruff_path) or os.path.getsize(ruff_path) == 0:
        return []
    try:
        with open(ruff_path) as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def get_rule_groups(ocr_cmd, files, repo):
    if not files:
        return {}
    cmd = ocr_cmd.split() + ["delegate", "rule"] + files
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
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
            applies_match = re.match(r"-\s+(.+)", line)
            if applies_match:
                path = applies_match.group(1).strip().strip("`")
                current_files.append(norm(path, repo))
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


def build_file_summary(lizard_rows, oxlint_diags, ruff_diags, repo):
    by_file = defaultdict(lambda: {"max_ccn": 0, "total_nloc": 0, "function_count": 0, "oxlint": 0, "ruff": 0})

    for r in lizard_rows:
        f = norm(r["file"], repo)
        ccn = int(r["ccn"])
        nloc = int(r["nloc"])
        by_file[f]["max_ccn"] = max(by_file[f]["max_ccn"], ccn)
        by_file[f]["total_nloc"] += nloc
        by_file[f]["function_count"] += 1

    for d in oxlint_diags:
        f = norm(d.get("filename", "unknown"), repo)
        by_file[f]["oxlint"] += 1

    for d in ruff_diags:
        f = norm(d.get("filename", "unknown"), repo)
        by_file[f]["ruff"] += 1

    return by_file


def score_file(s):
    return s["max_ccn"] + s["oxlint"] + (s["ruff"] * 0.5)


def build_manifest(by_file, rule_groups):
    files = sorted(by_file.items(), key=lambda kv: (-score_file(kv[1]), -kv[1]["max_ccn"], -kv[1]["oxlint"]))
    manifest = []

    for f, s in files[:TOP_N]:
        if s["max_ccn"] < CCN_THRESHOLD and s["oxlint"] == 0 and s["ruff"] == 0:
            continue

        parts = []
        if s["max_ccn"] >= CCN_THRESHOLD:
            parts.append(f"max CCN {s['max_ccn']}")
        if s["oxlint"] > 0:
            parts.append(f"{s['oxlint']} anti-slop issues")
        if s["ruff"] > 0:
            parts.append(f"{s['ruff']} ruff issues")

        action = "; ".join(parts) if parts else "clean"

        item = {
            "rank": len(manifest) + 1,
            "file": f,
            "total_nloc": s["total_nloc"],
            "function_count": s["function_count"],
            "max_ccn": s["max_ccn"],
            "oxlint": s["oxlint"],
            "ruff": s["ruff"],
            "rule_group": rule_groups.get(f),
            "target": f,
            "action": action,
            "verification": f"Re-run the scout on {f} and confirm the numbers go down."
        }
        manifest.append(item)

    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lizard", required=True)
    parser.add_argument("--oxlint", default="")
    parser.add_argument("--ruff", default="")
    parser.add_argument("--output", required=True)
    parser.add_argument("--ocr-cmd", default="")
    parser.add_argument("--repo", default="")
    args = parser.parse_args()

    repo = os.path.abspath(args.repo) if args.repo else ""

    rows = parse_lizard(args.lizard)
    oxlint = parse_oxlint(args.oxlint) if args.oxlint else []
    ruff = parse_ruff(args.ruff) if args.ruff else []

    by_file = build_file_summary(rows, oxlint, ruff, repo)

    rule_groups = {}
    if args.ocr_cmd:
        top_files = sorted(by_file.items(), key=lambda kv: -score_file(kv[1]))[:8]
        rule_groups = get_rule_groups(args.ocr_cmd, [f for f, _ in top_files], repo)

    manifest = build_manifest(by_file, rule_groups)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

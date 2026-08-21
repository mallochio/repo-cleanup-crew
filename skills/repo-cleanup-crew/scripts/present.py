#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.manifest) as f:
        manifest = json.load(f)

    lines = [
        "# repo-cleanup-crew analysis",
        "",
        f"Found {len(manifest)} file(s) worth cleaning.",
        "",
        "| Rank | File | Max CCN | anti-slop | ruff | Action |",
        "|------|------|---------|-----------|------|--------|",
    ]

    for item in manifest:
        lines.append(
            f"| {item['rank']} | `{item['file']}` | {item['max_ccn']} | {item['oxlint']} | {item['ruff']} | {item['action']} |"
        )

    lines.extend([
        "",
        "## Verification method",
        "",
        "For each cleaned file, re-run the scout and confirm CCN, anti-slop, and ruff counts decrease.",
        "",
        "## Next step",
        "",
        "Review the files above. If you want the agent to proceed with cleanup, say which ranks to clean (for example: `1, 2`) or `all`. "
        "The agent will load only the relevant function or block, propose a minimal behavior-preserving change, and verify it.",
    ])

    text = "\n".join(lines)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(text)

    print(text)


if __name__ == "__main__":
    main()

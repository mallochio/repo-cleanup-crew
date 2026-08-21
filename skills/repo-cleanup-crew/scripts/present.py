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
        f"Found {len(manifest)} item(s) worth cleaning.",
        "",
        "| Rank | Target | Max CCN | File NLOC | Action |",
        "|------|--------|---------|-----------|--------|",
    ]

    for item in manifest:
        lines.append(
            f"| {item['rank']} | `{item['target']}` | {item['max_ccn']} | {item['total_nloc']} | {item['action']} |"
        )

    lines.extend([
        "",
        "## Verification method",
        "",
        "For each cleaned item, re-run `lizard` on the affected file and confirm the CCN or NLOC metric moved in the right direction.",
        "",
        "## Next step",
        "",
        "Review the items above. If you want the agent to proceed with cleanup, say which ranks to clean (for example: `1, 2`) or `all`. "
        "The agent will load only the relevant function, propose a minimal behavior-preserving change, and verify it.",
    ])

    text = "\n".join(lines)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(text)

    print(text)


if __name__ == "__main__":
    main()

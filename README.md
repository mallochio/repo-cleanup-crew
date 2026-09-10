# repo-cleanup-crew

[![skills.sh](https://skills.sh/b/mallochio/repo-cleanup-crew)](https://skills.sh/mallochio/repo-cleanup-crew)

An agent skill that finds the highest-value cleanups in a repo and presents them to the user. It only edits files after the user approves which items to clean. All analysis output goes to `/tmp/repo-cleanup-crew/`, so nothing is written into the target repository.

It uses:

- [lizard](https://github.com/terryyin/lizard) for cyclomatic-complexity measurement.
- [anti-slop](https://github.com/dmmulroy/anti-slop) `oxlint` plugin for TypeScript/JavaScript slop patterns.
- [ruff](https://github.com/astral-sh/ruff) for Python style and quality.
- [Open Code Review](https://github.com/alibaba/open-code-review) (`ocr`) for deterministic file selection and rule resolution.

## What it does

- Measures cyclomatic complexity across many languages with `lizard`.
- Runs `oxlint` with the `anti-slop` plugin for TypeScript/JavaScript slop patterns.
- Runs `ruff` with the bundled `rules/ruff.toml` for Python style and quality (Interhuman house standard from open-omni-modeling: line length 120, C901 max 12). Cleanup also follows `rules/thermo-nuclear.md` (≈300-line modules, complexipy≤20, typing, Google docstrings).
- Uses `ocr` in delegation mode to find the right review rule for each file.
- Merges all findings into one ranked manifest.
- Writes the manifest and a human-readable analysis to `/tmp/repo-cleanup-crew/<repo-name>/`.
- Presents the analysis and waits for the user to select which items to clean.
- If approved, loads only the relevant function, proposes a minimal change, and verifies it.

## Install the skill

Install globally so no files are written into the target repository:

```bash
npx skills add mallochio/repo-cleanup-crew -g -y
```

If your agent requires a local skill directory, you can omit `-g`; the skill will live in `.agents/skills/repo-cleanup-crew/`.

## Use the skill

From inside the target repository, run the scout. All output goes to `/tmp`:

```bash
bash <path-to-skill>/scripts/scout.sh
```

or for a different repo:

```bash
bash <path-to-skill>/scripts/scout.sh /path/to/other-repo
```

The scout prints a markdown analysis. The agent then asks which ranks to clean. Edits only happen after you select items.

## Tooling

The scout tries the following runners, in order, to avoid forcing a global install:

1. `lizard` if it is already on `PATH`.
2. `uvx lizard` if `uvx` is installed.
3. `python3 -m lizard` if `lizard` is in the current Python environment.

`ocr` is invoked with `npx -y @alibaba-group/open-code-review` or an existing global `ocr` binary, and is used only in delegation mode (no LLM endpoint required on the `ocr` side).

## What it flags

- Functions with cyclomatic complexity above the threshold.
- Files with many near-identical functions that can be collapsed or abstracted.
- Files pushing past healthy size limits.
- `ocr` review rules matched to each file's language and path.

## Example analysis output

```
# repo-cleanup-crew analysis

Found 3 item(s) worth cleaning.

| Rank | File | Max CCN | anti-slop | ruff | Action |
|------|------|---------|-----------|------|--------|
| 1 | `src/index.ts` | 28 | 12 | 0 | max CCN 28; 12 anti-slop issues |
| 2 | `src/providers/slack.bolt.ts` | 13 | 4 | 0 | max CCN 13; 4 anti-slop issues |
| 3 | `src/services/llm.service.ts` | 8 | 9 | 0 | 9 anti-slop issues |

## Next step

Review the items above. If you want the agent to proceed with cleanup, say which ranks to clean (for example: `1, 2`) or `all`.
```

## License

MIT

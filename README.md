# repo-cleanup-crew

[![skills.sh](https://skills.sh/b/mallochio/repo-cleanup-crew)](https://skills.sh/mallochio/repo-cleanup-crew)

An agent skill that finds the highest-value cleanups in a repo, then performs them one at a time while keeping the context window small. It uses [lizard](https://github.com/terryyin/lizard) for cyclomatic-complexity measurement and [Open Code Review](https://github.com/alibaba/open-code-review) (`ocr`) for deterministic file selection and rule resolution.

## What it does

- Measures cyclomatic complexity across many languages with `lizard`.
- Uses `ocr` in delegation mode to find the right review rule for each file.
- Ranks the worst hot spots into a one-page manifest.
- Loads only the relevant function or diff hunk, not the whole repo.
- Verifies every cleanup by re-running the measurement.

## Install with an agent skill

```bash
npx skills add mallochio/repo-cleanup-crew --skill repo-cleanup-crew
```

Then ask your coding agent to run `repo-cleanup-crew` in the current repository. The skill copies the bundled cleanup scripts into `tools/repo-cleanup-crew/`, scouts the repo, and walks the highest-priority cleanups one by one.

## Manual local installation

Copy `skills/repo-cleanup-crew/` into your repository, for example at `tools/repo-cleanup-crew/`, and run the install script:

```bash
cp -r skills/repo-cleanup-crew tools/repo-cleanup-crew
node tools/repo-cleanup-crew/scripts/install.mjs
```

Then run the scout:

```bash
bash tools/repo-cleanup-crew/scripts/scout.sh
```

This produces `tools/repo-cleanup-crew/output/manifest.json`. The agent should then process the manifest one item at a time.

## Tooling

The skill tries the following runners, in order, to avoid forcing a global install:

1. `lizard` if it is already on `PATH`.
2. `uvx lizard` if `uvx` is installed.
3. `python3 -m lizard` if `lizard` is in the current Python environment.

`ocr` is invoked with `npx -y @alibaba-group/open-code-review` or an existing global `ocr` binary, and is used only in delegation mode (no LLM endpoint required on the `ocr` side).

## What it flags

- Functions with cyclomatic complexity above the threshold.
- Files with many near-identical functions that can be collapsed or abstracted.
- Files pushing past healthy size limits.
- `ocr` review rules matched to each file's language and path.

## Example manifest item

```json
{
  "rank": 1,
  "file": "src/utils.py",
  "max_ccn": 26,
  "rule_group": "system / **/*.{py,ipynb}",
  "target": "src/utils.py :: calculate_price",
  "action": "Reduce cyclomatic complexity in `calculate_price` (CCN=26).",
  "verification": "Re-run lizard on src/utils.py and confirm max CCN decreases."
}
```

## Credits

- [lizard](https://github.com/terryyin/lizard) by Terry Yin — cyclomatic complexity analysis
- [Open Code Review](https://github.com/alibaba/open-code-review) by Alibaba — file selection and rule resolution

## License

MIT

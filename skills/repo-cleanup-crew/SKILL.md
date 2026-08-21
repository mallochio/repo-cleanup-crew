---
name: repo-cleanup-crew
description: Scout a repo for the highest-value cleanups using lizard, oxlint (anti-slop), and ruff, present a neat analysis, and only edit after the user approves which files to clean. All scout output goes to /tmp.
---

# repo-cleanup-crew

Analyze a repository for cyclomatic-complexity hot spots, anti-slop (`oxlint`) issues, and `ruff` issues, then present a ranked list to the user. Do not make any edits until the user approves specific files.

## Non-negotiable rules

1. **All analysis output goes to `/tmp/repo-cleanup-crew/<repo-name>/`.** Never write scout artifacts into the target repository.
2. **No edits without explicit approval.** After presenting the analysis, stop and wait for the user to select which ranks to clean.
3. **Only load fragments.** Once approved, read only the relevant function or small block, not the whole file or whole repo.
4. **Verify every change.** After an edit, re-run the scout on the affected file and run the repo's typecheck and relevant tests.
5. **Apply thermo-nuclear standards.** Load `<skill-directory>/rules/thermo-nuclear.md` before reviewing a file.

## Tools the scout runs

- `lizard` — cyclomatic complexity, NLOC, and token counts.
- `oxlint` with the `anti-slop` plugin — TypeScript/JavaScript slop patterns.
- `ruff` with the skill's `rules/ruff.toml` — Python style and quality.
- `ocr` in delegation mode — file selection and rule grouping.

All tools run from the skill directory. Their outputs are merged into one manifest.

## Procedure

### Phase 1: Scout and present

1. Run the scout from the skill directory, passing the target repository path:

   ```bash
   bash <skill-directory>/scripts/scout.sh <path-to-repo>
   ```

   If no path is given, it uses the current working directory.

2. The script writes to `/tmp/repo-cleanup-crew/<repo-name>/`:
   - `lizard.csv` — raw `lizard` output
   - `oxlint.json` — `oxlint` diagnostics
   - `ruff.json` — `ruff` diagnostics
   - `manifest.json` — ranked cleanup files
   - `analysis.md` — human-readable summary

3. Read `analysis.md` and present the table to the user in a clean, concise form.
4. Stop. Ask the user which ranks to clean, for example: `1, 3` or `all` or `none`.

### Phase 2: Clean with permission

For each approved rank, in order:

1. Load the relevant code fragment (the `target` file from the manifest).
2. Read `<skill-directory>/rules/thermo-nuclear.md` for the maintainability standards.
3. Propose the smallest behavior-preserving refactor that reduces the metric.
4. Show the user the intended change and ask for a one-line confirmation if the change is non-trivial.
5. Apply the change.
6. Re-run `bash <skill-directory>/scripts/scout.sh <path-to-repo>` and confirm the counts for the affected file went down.
7. Run the repo's typecheck and the tests most relevant to the changed file.
8. Report the before/after numbers.

### Phase 3: Final report

After all approved items are handled:

- Summarize which files were changed and the metric changes.
- List any items the user declined.
- Note any tests that still fail and whether they are pre-existing.

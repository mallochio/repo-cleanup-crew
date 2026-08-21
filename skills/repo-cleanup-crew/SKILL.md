---
name: repo-cleanup-crew
description: Scout a repo for the highest-value cleanups using lizard and ocr, present a neat analysis, and only edit after the user approves which items to clean. All scout output goes to /tmp.
---

# repo-cleanup-crew

Analyze a repository for cyclomatic-complexity hot spots and `ocr` review rules, then present a ranked list to the user. Do not make any edits until the user approves specific items.

## Non-negotiable rules

1. **All analysis output goes to `/tmp/repo-cleanup-crew/<repo-name>/`.** Never write scout artifacts into the target repository.
2. **No edits without explicit approval.** After presenting the analysis, stop and wait for the user to select which ranks to clean.
3. **Only load fragments.** Once approved, read only the relevant function or small block, not the whole file or whole repo.
4. **Verify every change.** After an edit, re-run `lizard` on the affected file and run the repo's typecheck and relevant tests.

## Procedure

### Phase 1: Scout and present

1. Run the scout from the skill directory, passing the target repository path:

   ```bash
   bash <skill-directory>/scripts/scout.sh <path-to-repo>
   ```

   If no path is given, it uses the current working directory.

2. The script writes to `/tmp/repo-cleanup-crew/<repo-name>/`:
   - `lizard.csv` — raw `lizard` output
   - `manifest.json` — ranked cleanup items
   - `analysis.md` — human-readable summary

3. Read `analysis.md` and present the table to the user in a clean, concise form.
4. Stop. Ask the user which ranks to clean, for example: `1, 3` or `all` or `none`.

### Phase 2: Clean with permission

For each approved rank, in order:

1. Load the relevant code fragment (the function or block from the `target` field).
2. Propose the smallest behavior-preserving refactor that reduces the metric.
3. Show the user the intended change and ask for a one-line confirmation if the change is non-trivial.
4. Apply the change.
5. Re-run `lizard` on the affected file and confirm the CCN or NLOC decreased.
6. Run the repo's typecheck and the tests most relevant to the changed file.
7. Report the before/after numbers.

### Phase 3: Final report

After all approved items are handled:

- Summarize which files were changed and the metric changes.
- List any items the user declined.
- Note any tests that still fail and whether they are pre-existing.

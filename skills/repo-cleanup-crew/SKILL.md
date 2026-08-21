---
name: repo-cleanup-crew
description: Install and run a no-interview, tool-backed repo cleanup pass. Uses OCR delegation for file selection, lizard for cyclomatic complexity, and the host agent's model for minimal-context refactor actions.
---

# repo-cleanup-crew

Run a high-signal repo cleanup without asking the user questions. Infer languages and scope from the repo, produce a ranked manifest, and clean one item at a time while keeping the context window small.

## Non-negotiable cleanup standards

1. **Delete complexity before rearranging it.** A refactor that leaves the same number of branches is not a cleanup.
2. **No file crosses 1,000 lines without a written justification.** If a file is over the limit, the default remedy is to split it.
3. **No function above a healthy cyclomatic complexity.** Thresholds are language-specific and live in `config/thresholds.json`.
4. **No cleanup without verification.** After an edit, re-run the scout and confirm the metric moved.
5. **Only load fragments.** Never read a whole file unless the whole file is genuinely necessary.

## Procedure

1. Inspect the repository:
   - Check `git status` and ensure there are no uncommitted changes you cannot safely commit.
   - Identify `package.json`, `pyproject.toml`, or other language markers.

2. Install the crew:
   ```bash
   node <skill-directory>/scripts/install.mjs
   ```
   This creates `tools/repo-cleanup-crew/`. Refuse to overwrite without `--force`.

3. Run the scout:
   ```bash
   tools/repo-cleanup-crew/scripts/scout.sh
   ```
   This runs `lizard` for complexity and, if available, `ocr delegate` for file selection and rules. It writes raw outputs to `tools/repo-cleanup-crew/output/`.

4. Build the manifest:
   ```bash
   python3 tools/repo-cleanup-crew/scripts/manifest-pruner.py
   ```
   This reads `lizard` output and any `ocr` output, ranks issues, and writes `tools/repo-cleanup-crew/output/manifest.json`.

5. Read the manifest. Pick the highest-rank item.

6. For each item:
   - Use `tools/repo-cleanup-crew/scripts/fragment-loader.py` to fetch only the function or diff hunk.
   - Propose the smallest behavior-preserving refactor that reduces complexity or removes dead code.
   - Apply the edit.
   - Re-run the scout for the affected file and confirm the metric moved.

7. Stop and report:
   - files touched,
   - metrics before / after,
   - unresolved items and why.

## Primary cleanup questions

- Can we delete a whole branch or concept instead of simplifying it?
- Did this edit reduce cyclomatic complexity or just move it?
- Is this logic in the file that actually owns the concept?
- Did we reuse existing helpers, or invent a new one?
- Does the change make the next reader need to hold fewer things in their head?

# Thermo-nuclear maintainability standards

Use these standards when reviewing and cleaning any code the scout flags.

Python cleanup in Interhuman repos follows the house standards from
[InterhumanAI/open-omni-modeling](https://github.com/InterhumanAI/open-omni-modeling)
(AGENTS.md, CONTRIBUTING.md, Ruff, complexipy). Apply those below when cleaning
Python; keep the shared mindset for every language.

## Core mindset

- Prefer deleting complexity over moving it.
- Look for "code judo" moves: restructurings that make the whole implementation simpler, smaller, and more direct.
- Do not be satisfied with a mild cleanup when a dramatic simplification is possible.
- Prefer DRY, modular code with intuitive naming.

## Hard guardrails

- **Python (Interhuman house standard): keep source files and scripts under 300 lines** where practical. Refactor before growing large modules. This is the limit this skill enforces when cleaning Python.
- **All languages: no file should pass 1,000 lines** unless there is a very strong reason (legacy non-Python paths, generated code, or an exceptional documented case). Prefer the 300-line Python standard whenever it applies.
- **No new ad-hoc conditionals** in unrelated flows. Push special cases into a dedicated abstraction.
- **No `any`, `unknown`, or casts** (TypeScript/JavaScript) when a clearer type boundary could exist.

## Complexity

Complementary gates used in Interhuman Python repos (and what cleanup should target):

- **Ruff C901 (McCabe cyclomatic):** max **12**. Enforced via this skill's `rules/ruff.toml` (`[lint.mccabe] max-complexity = 12`).
- **complexipy (cognitive):** max **20**. Prefer extracting helpers over `# complexipy: ignore` or raising thresholds. Snapshot grandfathering of existing over-threshold functions is a **target-repo** concern; this skill documents the standard and does not invent snapshot tooling.

When a function is over either limit, extract focused helpers first. Do not paper over complexity with ignores.

## Python style

When cleaning Python, also apply:

- **Type hints** required on all functions.
- **Google-style docstrings** mandatory for public modules and functions.
- **Avoid inline comments**; only explain unintuitive logic. Prefer clear naming and structure.

## Structural checks

1. Can the change be reframed so fewer concepts, branches, or helper layers are needed?
2. Is logic living in the right file and layer?
3. Are repeated conditionals signaling a missing model or helper?
4. Is the implementation direct and legible, or does it rely on special cases?
5. Does the abstraction earn its keep, or is it just a wrapper?
6. Is orchestration more sequential or less atomic than it needs to be?
7. Is the module approaching or past the size limit (300 lines for Python)? Split before it grows further.

## Preferred remedies

- Delete a whole layer of indirection.
- Reframe the state model so conditionals disappear.
- Change the ownership boundary so the feature becomes a natural extension.
- Turn special-case logic into a simpler default flow.
- Extract a focused helper or pure function (especially to bring C901 / complexipy under threshold).
- Replace condition chains with a typed model or explicit dispatcher.
- Move logic to the package/module that already owns the concept.

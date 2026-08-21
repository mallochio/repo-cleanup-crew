# Thermo-nuclear maintainability standards

Use these standards when reviewing and cleaning any code the scout flags.

## Core mindset

- Prefer deleting complexity over moving it.
- Look for "code judo" moves: restructurings that make the whole implementation simpler, smaller, and more direct.
- Do not be satisfied with a mild cleanup when a dramatic simplification is possible.

## Hard guardrails

- **No file should pass 1,000 lines** unless there is a very strong reason.
- **No new ad-hoc conditionals** in unrelated flows. Push special cases into a dedicated abstraction.
- **No `any`, `unknown`, or casts** when a clearer type boundary could exist.

## Structural checks

1. Can the change be reframed so fewer concepts, branches, or helper layers are needed?
2. Is logic living in the right file and layer?
3. Are repeated conditionals signaling a missing model or helper?
4. Is the implementation direct and legible, or does it rely on special cases?
5. Does the abstraction earn its keep, or is it just a wrapper?
6. Is orchestration more sequential or less atomic than it needs to be?

## Preferred remedies

- Delete a whole layer of indirection.
- Reframe the state model so conditionals disappear.
- Change the ownership boundary so the feature becomes a natural extension.
- Turn special-case logic into a simpler default flow.
- Extract a focused helper or pure function.
- Replace condition chains with a typed model or explicit dispatcher.
- Move logic to the package/module that already owns the concept.

---
name: refactor-component
description: Refactor existing components while preserving behavior, design-token usage, component rules, and test coverage.
---

# Refactor Component

Use this local skill when changing component internals, variants, props, styles, or composition.

## Workflow

1. Locate current usages and tests before editing.
2. Read `DESIGN.md` and `contracts/component-rules.json`.
3. Preserve public behavior unless the active spec requires a change.
4. Keep token usage and component variants aligned with project contracts.
5. Update tests for any behavior, state, or accessibility change.

## Output

Report changed components, preserved public interfaces, tests run, and any migration notes.

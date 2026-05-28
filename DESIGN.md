# Design Contract

## Principles

- Design from explicit specs, not inferred product stories.
- Prefer reusable components and stable interaction patterns over one-off UI.
- Use design tokens for color, spacing, typography, radius, and elevation decisions.
- Make states visible: loading, empty, error, disabled, active, and success states should be intentionally handled.
- Keep interfaces inspectable by agents: names, props, variants, and state transitions should be clear.

## Contracts

- `contracts/design-tokens.schema.json` defines the expected shape for token files.
- `contracts/component-rules.json` defines component-level constraints agents should preserve.

## Review Checklist

- Does the implementation satisfy the active spec?
- Are token and component rules respected?
- Are responsive behavior and state coverage addressed?
- Are tests aligned with the acceptance criteria?

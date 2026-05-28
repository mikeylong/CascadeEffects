# Component Refactor Checks

- Public props, exported names, and event behavior are preserved or intentionally migrated.
- Token usage still follows `DESIGN.md` and `contracts/`.
- Loading, empty, error, disabled, active, and success states still render as expected.
- Existing tests pass and new tests cover changed behavior.
- Call sites are updated when an intentional interface change is made.

# Season 2 Production Core

The fresh monorepo is a control system, not a mirror of the old roots.

- `episodes/season-02/` is the only active episode workspace.
- `apps/review/` is the human gate surface and is only exposed through `bin/ce review-*`.
- `ops/agents/skills/` holds active workflow instructions.
- `packages/production-tools/` holds reusable orchestration code.
- `packages/media-pipeline/` holds reusable media utilities, not department-specific state.
- `archive/season-01-reference/` is reference-only and may contain old absolute paths for audit.

`bin/ce doctor` enforces the boundary by failing on legacy active folders, nested Git repos,
tracked media outside approved web assets, stale absolute root references outside archive or
migration records, expired locks, missing Season 2 template files, and broken artifact locks.

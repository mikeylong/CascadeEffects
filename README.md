# Cascade Effects

Cascade Effects is now structured as a thin production monorepo. The root repo owns orchestration, source contracts, episode state, publish receipts, and deployable web code. Heavy generated media lives in the local `.artifacts/` store and is referenced by tracked manifests.

## Layout

- `apps/web/`: CascadeEffects.tv Next.js app. Vercel should use this as the project root.
- `apps/review/`: human approval UI, exposed through `bin/ce review-*`.
- `episodes/season-02/`: the only active episode production workspace.
- `ops/agents/skills/`: active agent-readable production workflows.
- `ops/`: migration records, task queues, locks, and runbooks.
- `packages/contracts/`: shared schemas and production contracts.
- `packages/production-registry/`: active registry/config data.
- `packages/production-tools/`: reusable orchestration validators, adapters, and builders.
- `packages/media-pipeline/`: reusable audio/video utilities only.
- `archive/season-01-reference/`: compact Season 1 audit/reference material, not active production structure.
- `.artifacts/`: local generated/final media store; intentionally ignored by Git.

## Core Commands

```bash
bin/ce status
bin/ce doctor
bin/ce review-list
bin/ce review-server
bin/ce new-episode season-02 ep09-apollo-13 --title "Apollo 13 Oxygen Tank Crisis"
bin/ce new-episode season-02 ep10-citicorp-center --dry-run
bin/ce validate
npm --prefix apps/web run lint
npm --prefix apps/web run build
```

## Production Policy

Git tracks source, specs, scripts, manifests, receipts, validation results, and artifact checksums. Git does not track full video renders, raw generated image batches, audio masters, failed candidates, or scratch outputs.

Season 2 production defaults to compact long-form episodes: 12 to 18 minutes, with up to about 20 minutes only when the evidence genuinely requires it.

The old top-level departments are deliberately absent. Do not add `agents/`, `audio/`,
`viz/`, `inbox/`, `labs/`, `channel/`, or `episodes/season-01/` back to the active root.

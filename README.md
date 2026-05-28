# Cascade Effects

Cascade Effects is now structured as a thin production monorepo. The root repo owns orchestration, source contracts, episode state, publish receipts, and deployable web code. Heavy generated media lives in the local `.artifacts/` store and is referenced by tracked manifests.

## Layout

- `agents/`: production skills, orchestration scripts, validators, and episode configs imported from `Agents_CascadeEffects`.
- `episodes/`: canonical episode production records. Season 1 is migrated from prior roots; Season 2 starts from `_template`.
- `audio/`, `viz/`, `inbox/`: specialized production tooling now under one root.
- `apps/web/`: CascadeEffects.tv Next.js app. Vercel should use this as the project root.
- `channel/`: channel-level production packages and artifact locks.
- `ops/`: migration records, task queues, locks, and runbooks.
- `packages/contracts/`: shared schemas and production contracts.
- `.artifacts/`: local generated/final media store; intentionally ignored by Git.

## Core Commands

```bash
bin/ce status
bin/ce doctor
bin/ce new-episode season-02 ep09-apollo-13 --title "Apollo 13 Oxygen Tank Crisis"
bin/ce validate
npm --prefix apps/web run lint
npm --prefix apps/web run build
```

## Production Policy

Git tracks source, specs, scripts, manifests, receipts, validation results, and artifact checksums. Git does not track full video renders, raw generated image batches, audio masters, failed candidates, or scratch outputs.

Season 2 production defaults to compact long-form episodes: 12 to 18 minutes, with up to about 20 minutes only when the evidence genuinely requires it.

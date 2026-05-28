# Import Classification

This migration uses a clean monorepo import. Old roots remain read-only source archives until staged cutover.

## Tracked In Git

- Source code, scripts, skills, configs, schemas, and tests.
- Episode scripts, fact checks, metadata, publish readiness manifests, validation receipts, upload receipts, review notes, and keep/final provenance.
- Artifact lock files with original paths, local artifact paths, byte counts, and SHA-256 checksums.
- Web app code and deployable `apps/web/public` assets.

## Stored In `.artifacts/`

- Season 1 final audio/video masters.
- Latest kept long-form publish-readiness review MP4s.
- Latest kept Shorts publish-ready captioned MP4s.
- Selected Season 1 channel intro, trailer, and playlist thumbnail outputs.

## Left In Old Roots

- Rejected candidates, defective uploads, superseded proof batches, generated review HTML/CSS/JS, scratch outputs, caches, temp dirs, raw model outputs, old archives, and bulk media trees.
- Legacy absolute paths in migrated Season 1 receipts are preserved as historical evidence.

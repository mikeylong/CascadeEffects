# Cascade Effects Design System Contract

Active profile: `cascade-paper-architectures-ink-lit-v1`

The active Cascade Effects design system uses ink-lit Paper Architectures illustration, explicit title policy, bold Inter-based title typography, and platform-specific safe-zone rules. The former bright/daylight Paper Architectures look and `cascade-lowpoly-pastel-v1` are legacy/inactive reference.

## Source Of Truth

- Active style tokens: `brand/cascade-effects-signal.style-system.json`
- Illustration rules: `brand/contracts/illustration.contract.json`
- Package manifests: `brand/packages/*.package.json`
- Reference renders: `brand/assets/reference-renders/paper-architectures-v1/*.png`
- Validator: `scripts/validate-asset-packages.mjs`
- Website gallery validator: `scripts/validate-episode-gallery-thumbnails.mjs`

The old bright/daylight, low-poly pastel, and dark/evidence-led systems are legacy reference only. They must not be used as active package guidance.

## Reference Evidence

The `paper-architectures-ink-lit-v1` reference renders are project-owned visual evidence tracked through Git LFS. They establish the launch direction for deep ink-blue fields, cream paper forms, lavender paper shadows, cyan vellum glow, restrained coral accents, foam-core surfaces, subtle paper fiber only, controlled model lighting, public-anchor scale, and deterministic title policy.

Approved web/channel identity reference renders may include the `Cascade of Effects` title. Production title-bearing assets should still compose title locally unless the package manifest explicitly permits an approved title-bearing source.

## Visual System

- Palette: deep ink-blue fields, warm cream paper, powder cyan vellum glow, muted lavender shadows, soft graphite seams, and restrained coral warning accents.
- Rendering grammar: folded paper, foam-core, subtle paper fiber only, clean low-detail paper planes, vellum, gouache/pastel pigment, controlled model-light shadows, and clean low-detail geometry.
- Composition: one dominant public anchor or folded cascade model, calm title zones when needed, simple terraces or cascade sheets.
- Density: keep scenes sparse enough to read in web cards, YouTube previews, podcast libraries, long-form living covers, and chapter cards.
- CascadeEffects.tv episode-gallery thumbnails: one dominant primary subject only. The card pill/title carries context; do not add separate evidence trays, ledgers, gauges, connection details, system diagrams, arrows, dry signal paths, or secondary prop clusters.
- Texture noise: `texture_noise_read: pass|tighten|reject` is required for generated source-art proofs, package candidates, thumbnails, and motion-readiness candidates. High-frequency speckle, visible grain, grit, sandy/noisy paper surfaces, texture-heavy rendering, or texture that competes with the public anchor blocks `keep` and package promotion.

## Type And Title Rules

- Exact title: `Cascade of Effects`
- Title-bearing assets use deterministic local composition by default, not generated model text.
- Approved web/channel identity reference renders may carry the title only when named by a package manifest.
- Episode thumbnails remain text-free unless a package manifest explicitly says otherwise.
- Title style uses a bold Inter-based block treatment with cream fill and deep blue or lavender paper shadow/depth.
- The word `of` must be heavy enough to survive small sizes.
- Launch package copy is title-only. No tagline, episode title, watermark, or extra text.
- Profile icons must not include the full title.

## Platform Rule

Each package manifest must declare role, platform, dimensions, safe zones, title policy, source render path, composition method, QA checks, `texture_noise_read`, and status.

CascadeEffects.tv episode-gallery thumbnails use `proof-v6-ink-lit-subjects` as the active baseline until a new approved subject-only proof replaces it. Future proof folders should follow `proof-vN-ink-lit-subjects`, record provenance, produce `320x180` and `168x94` contact sheets, and include homepage desktop/mobile screenshots before promotion.

Production exports stay local/generated/archive-only unless separately approved. Source control contains contracts, schemas, validators, manifests, templates, provenance, and approved Git LFS reference renders under `brand/assets/reference-renders/**`.

## Drift Control

Approved baseline illustrations are locked. Small narrative additions, removals, placement changes, or visual gags must be made as deterministic layer composites over the baseline, not by regenerating the full scene. The composition recipe must record source paths, placement, scale, rotation, opacity, and output path so the approved paper material language, minimal texture-noise level, palette, and density do not drift between iterations. If a baseline or derivative reads as high-frequency speckle, grain, grit, sandy/noisy paper, or texture-heavy rendering at `320x180` or `168x94`, record `texture_noise_read: tighten|reject` and block promotion until repaired.

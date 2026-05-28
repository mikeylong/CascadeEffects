# Homepage Hero Stylized Peril Clean Surface V3 Provenance

Date: 2026-05-12

Scope: CascadeEffects.tv homepage hero clean-surface repair.

Correction: v2 successfully added stylized danger, but the source renders carried too much high-frequency texture. v3 preserves the v2 composition and peril cues, then applies a deterministic clean-surface repair so the hero reads as clean paper planes rather than noisy paper grain.

Supersession: v3 is no longer the active homepage hero because the baked paper clouds were removed in cloudless v4. Use `homepage-hero-cloudless-clean-surface-v4.provenance.md` and its v4 source renders for the active web hero.

## Asset Brief

- Archetype: Folded Cascade Model.
- Carrier: deterministic raster clean-surface repair over the v2 stylized-peril baseline with deterministic responsive crops.
- Title/text policy: preserve only the baked `Cascade of Effects` folded-paper title; no extra copy, labels, logos, or watermarks.
- Composition: preserve the title position, clouds, bridge, broken center span, mountains, cascade, three paper figures, shuttle stack, launch tower, ocean liner, and paper terrain from v2.
- Stylized peril treatment: contained coral-orange shuttle fire/heat cue, visibly sinking/listing ocean liner, steeper fractured cascade terraces, and frightened falling figures.
- Surface rule: subtle paper fiber only; visible grain, speckle, grit, sandy surface, noisy shadows, and texture competing with public-anchor readability are blockers.

## Source Renders

- Desktop source: `brand/assets/reference-renders/paper-architectures-v1/homepage-hero-stylized-peril-clean-surface-desktop-source-v3.png`
- Mobile source: `brand/assets/reference-renders/paper-architectures-v1/homepage-hero-stylized-peril-clean-surface-mobile-source-v3.png`

Clean-surface repair inputs:

- `brand/assets/reference-renders/paper-architectures-v1/homepage-hero-stylized-peril-desktop-source-v2.png`
- `brand/assets/reference-renders/paper-architectures-v1/homepage-hero-stylized-peril-mobile-source-v2.png`

Repair method:

- Local deterministic bilateral-style smoothing pass, radius 2, spatial sigma 1.9, color sigma 32, full filtered blend.
- Purpose: suppress high-frequency texture and noisy paper grain while preserving folded-paper geometry, title readability, frightened figure expressions, shuttle fire cue, and sinking ocean liner silhouette.

## Runtime Crops

- `/brand/homepage-hero-paper-stylized-peril-clean-surface-desktop-v3.png` - 1672x941
- `/brand/homepage-hero-paper-stylized-peril-clean-surface-tablet-landscape-v3.png` - 1366x768
- `/brand/homepage-hero-paper-stylized-peril-clean-surface-tablet-portrait-v3.png` - 1200x1400
- `/brand/homepage-hero-paper-stylized-peril-clean-surface-mobile-v3.png` - 1080x1920

## QA Notes

- `peril_read: pass`
- `fun_slide_read: reject`
- `texture_noise_read: pass`
- `texture_detail_creep_read: pass`
- `waterfall_read: pass`
- Desktop and mobile source renders preserve the `Cascade of Effects` title without extra generated text.
- Runtime crops match the existing responsive dimensions.
- Cloudless v4 is the active homepage hero reference. Dark-adapted v1 remains the prior composition/lighting reference; stylized-peril v2 remains a superseded texture-tightening candidate.

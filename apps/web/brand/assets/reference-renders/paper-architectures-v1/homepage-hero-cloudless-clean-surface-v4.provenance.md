# Homepage Hero Cloudless Clean Surface V4 Provenance

Date: 2026-05-12

Scope: CascadeEffects.tv homepage hero cloudless raster/source-art revision.

Correction: v3 fixed the heavy texture issue but retained two baked paper clouds. v4 removes those clouds at the source-art level and fills the former cloud areas with clean deep ink-blue sky while preserving the approved v3 title, peril cues, composition, crops, and clean-surface guardrail.

Supersession: v4 is the active homepage hero reference. v3 remains the prior clean-surface reference and should only be used for rollback or comparison.

## Asset Brief

- Archetype: Folded Cascade Model.
- Carrier: deterministic local raster sky cleanup over the v3 clean-surface stylized-peril baseline with deterministic responsive crops.
- Title/text policy: preserve only the baked `Cascade of Effects` folded-paper title; no extra copy, labels, logos, or watermarks.
- Composition: preserve the title position, bridge, broken center span, mountains, cascade, three frightened paper figures, shuttle stack, launch tower, sinking ocean liner, and paper terrain from v3.
- Cloudless treatment: remove all paper clouds and their soft halos; fill removed areas with clean deep ink-blue sky matched to surrounding lighting.
- Surface rule: subtle paper fiber only; visible grain, speckle, grit, sandy surface, noisy shadows, patch texture, and texture competing with public-anchor readability are blockers.

## Source Renders

- Desktop source: `brand/assets/reference-renders/paper-architectures-v1/homepage-hero-cloudless-clean-surface-desktop-source-v4.png`
- Mobile source: `brand/assets/reference-renders/paper-architectures-v1/homepage-hero-cloudless-clean-surface-mobile-source-v4.png`

Cloudless cleanup inputs:

- `brand/assets/reference-renders/paper-architectures-v1/homepage-hero-stylized-peril-clean-surface-desktop-source-v3.png`
- `brand/assets/reference-renders/paper-architectures-v1/homepage-hero-stylized-peril-clean-surface-mobile-source-v3.png`

Repair method:

- Local deterministic sky-reconstruction masks over the two baked cloud regions in each source render.
- Local low-frequency sky plane fitting from nearby dark-sky pixels, with small feathered blends at the mask boundary.
- Purpose: remove clouds and halos without regenerating the scene, changing the title, or disturbing the shuttle fire cue, sinking ocean liner, frightened figures, cascade, bridge, and mountains.

## Runtime Crops

- `/brand/homepage-hero-paper-cloudless-clean-surface-desktop-v4.png` - 1672x941
- `/brand/homepage-hero-paper-cloudless-clean-surface-tablet-landscape-v4.png` - 1366x768
- `/brand/homepage-hero-paper-cloudless-clean-surface-tablet-portrait-v4.png` - 1200x1400
- `/brand/homepage-hero-paper-cloudless-clean-surface-mobile-v4.png` - 1080x1920

## QA Notes

- `cloud_read: reject`
- `sky_patch_seam_read: pass`
- `peril_read: pass`
- `fun_slide_read: reject`
- `texture_noise_read: pass`
- `texture_detail_creep_read: pass`
- `waterfall_read: pass`
- Desktop and mobile source renders preserve the `Cascade of Effects` title without extra generated text.
- Runtime crops match the existing responsive dimensions and object-position behavior.

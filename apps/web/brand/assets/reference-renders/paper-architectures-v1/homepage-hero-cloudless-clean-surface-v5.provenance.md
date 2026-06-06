# Homepage Hero Cloudless Clean Surface V5 Provenance

Date: 2026-06-06

Scope: CascadeEffects.tv homepage hero smooth-paper raster/source-art revision.

Correction: v4 preserved the cloudless stylized-peril composition, but the blue cascade and adjacent terrain could read as stone, ice, or overly textured low-poly surfaces. v5 preserves the title-bearing homepage scene while rebuilding the visual read as smooth Paper Architecture: broad folded paper planes, dry cyan vellum sheets, cream foam-core forms, lavender shadows, and subtle paper fiber only.

Supersession: v5 is no longer the active homepage hero because the title treatment was too light for the current homepage read. Use `homepage-hero-cloudless-clean-surface-v8.provenance.md` and its regenerated v8 source renders for the active web hero. v7 remains the peril/staging rollback reference, v6 remains the darker-title smooth-paper rollback/comparison reference, and v5 remains the prior smooth-paper baseline for rollback or comparison.

## Asset Brief

- Archetype: Folded Cascade Model.
- Carrier: generated raster/source art using the v4 desktop and mobile references, with a deterministic low-frequency matte-paper foreground repair on the desktop source.
- Title/text policy: preserve only the baked `Cascade of Effects` folded-paper title; no extra copy, labels, logos, or watermarks.
- Composition: preserve the title, bridge, broken center span, mountains, cascade, three frightened paper figures, shuttle stack, launch tower, sinking ocean liner, and ink-blue field from v4.
- Smooth-paper treatment: rebuild the cascade and terrain as clean folded paper/vellum sheets with broad planes and soft scored seams.
- Surface rule: subtle paper fiber only; stone, rock, ice, crystalline facets, rough plaster, concrete, visible grain, speckle, grit, sandy surface, noisy shadows, and texture competing with public-anchor readability are blockers.
- Signal rule: blue cascade forms must read as dry cyan vellum/paper sheets, not water, waterfall, river, stream, liquid spill, flowing channel, or reflective pool.

## Source Renders

- Desktop source: `brand/assets/reference-renders/paper-architectures-v1/homepage-hero-cloudless-clean-surface-desktop-source-v5.png`
- Mobile source: `brand/assets/reference-renders/paper-architectures-v1/homepage-hero-cloudless-clean-surface-mobile-source-v5.png`

Generation inputs:

- `brand/assets/reference-renders/paper-architectures-v1/homepage-hero-cloudless-clean-surface-desktop-source-v4.png`
- `brand/assets/reference-renders/paper-architectures-v1/homepage-hero-cloudless-clean-surface-mobile-source-v4.png`

Staged artifact packet:

- `.artifacts/web/homepage-hero-v5/artifacts.lock.json`

## Runtime Crops

- `/brand/homepage-hero-paper-cloudless-clean-surface-desktop-v5.png` - 1672x941
- `/brand/homepage-hero-paper-cloudless-clean-surface-tablet-landscape-v5.png` - 1366x768
- `/brand/homepage-hero-paper-cloudless-clean-surface-tablet-portrait-v5.png` - 1200x1400
- `/brand/homepage-hero-paper-cloudless-clean-surface-mobile-v5.png` - 1080x1920

## QA Notes

- `cloud_read: reject`
- `sky_patch_seam_read: pass`
- `peril_read: pass`
- `fun_slide_read: reject`
- `texture_noise_read: pass`
- `texture_detail_creep_read: pass`
- `stone_surface_read: pass`
- `waterfall_read: pass`
- `title_exact_read: pass`
- Desktop and mobile source renders preserve the `Cascade of Effects` title without extra generated text.
- Runtime crops match the existing responsive dimensions and homepage breakpoints.

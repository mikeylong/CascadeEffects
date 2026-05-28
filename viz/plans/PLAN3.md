## Controlled Typography Refinement v1.1

### Summary
- Refine the shared still-image controlled-typography system, with `scene_still/challenger_mission_control` as the first consumer.
- Keep the current workflow contract intact: generative stages stay zero-letter, Challenger stays manual-first, and readable text remains allowed only through the typography sidecar after `final_upscale`.
- The refinement target is visual integration and tuning ergonomics. The current smoke pass proves the pipeline works, but the output still reads like pasted type: the clock strip is oversized and flat, the wall mark floats, and tuning is too manual.

### Key Changes
- Extend the shared typography sidecar with optional v1.1 zone controls for fit and surface integration:
  - `fit_mode`: `fixed` or `contain`
  - `padding_px`
  - `align_x`: `start|center|end`
  - `align_y`: `start|center|end`
  - `min_font_size_px`
  - `max_font_size_px`
  - `neutralize_mode`: `off|blur|paint`
  - `neutralize_strength`
  - `underlay` object with `kind`, `color`, `opacity`, `blur_px`, `expand_px`, `corner_radius_px`
  - `shadow` object with `color`, `opacity`, `blur_px`, `offset_x`, `offset_y`
- Keep all existing zone fields valid and backward compatible. If new fields are omitted, current behavior remains.
- Upgrade the compositor so text is fit to the declared quad instead of relying on a single fixed font size. `contain` mode should shrink or grow text within the padded quad, preserve tracking, and respect alignment.
- Replace blanket neutralization with per-zone neutralization. `paint` should flatten local glyph noise for signage-like zones; `blur` should remain available for softer wall marks.
- Generalize underlays beyond the current hardcoded wall-clock strip behavior. The compositor should support reusable underlay shapes for recessed sign bands and flat wall marks through the sidecar instead of zone-kind-specific logic.
- Improve realism controls in the compositor:
  - apply shadow before warp
  - apply blur/glow/noise after fit sizing but before final composite
  - keep blend-mode behavior, but ensure `normal`, `screen`, `add`, and `multiply` all operate on the final warped patch consistently
- Tighten validation:
  - approved-zone validation must report actual OCR output, not just the declared string
  - fail when text clips outside the padded quad
  - fail when OCR on the zone does not match the declared string after composition
  - keep unapproved-text leak detection outside approved bounds
- Add debug outputs for manual tuning:
  - per-zone crop before neutralization
  - per-zone crop after neutralization
  - rendered patch before warp
  - warped overlay mask
  - final composite with zone outlines
- Keep Challenger manual-only during tuning. Do not auto-enable its sidecar; use `bin/ce render typography ...` until one approved hero exists.

### Interfaces
- Keep `bin/ce render typography <family> <preset> --image /abs/path` as the primary manual entrypoint.
- Add optional `--debug-dir /abs/path` to the typography command so manual tuning can emit inspection artifacts without changing the main output contract.
- Extend typography run manifests to include:
  - resolved zone fit results
  - actual font size used after fitting
  - actual OCR text per zone
  - clip status per zone
  - debug artifact paths when requested
- Sidecar compatibility rules:
  - existing sidecars remain valid with no edits
  - new v1.1 fields are optional
  - `overlay_first` remains the only supported mode
  - allowed zone kinds stay unchanged in this refinement

### Challenger First-Use Spec
- Keep `workflows/typography/scene_still/challenger_mission_control.json` manual-only with `enabled: false`.
- Keep the two-zone budget:
  - one `wall_clock_strip`
  - one `wall_mark`
- For the Challenger wall-clock strip, use `fit_mode: contain`, centered alignment, moderate padding, a recessed dark underlay, and slight blur so the numerals sit inside the band rather than spanning a pasted rectangle.
- For the Challenger wall mark, use `fit_mode: contain`, light `paint` neutralization, no heavy underlay, slight shadow/noise, and lower opacity so the mark sits in the wall texture instead of floating above it.
- The refined Challenger pass is acceptable only if the composited output reads as a real room surface, not as added poster text.

### Test Plan
- Validation still passes for existing sidecars with no v1.1 fields.
- Validation fails for malformed new fields, invalid enum values, negative padding, incompatible fit ranges, or missing required subfields inside `underlay` or `shadow`.
- `bin/ce render typography ...` without `--debug-dir` preserves current behavior.
- `bin/ce render typography ... --debug-dir ...` writes the new tuning artifacts and records them in the run manifest.
- Zone-fit tests:
  - text stays inside the padded quad in `contain` mode
  - alignment modes place text correctly inside the quad
  - fixed mode preserves old behavior
- OCR tests:
  - approved zones must OCR-match the declared string after composition
  - uncontrolled text outside approved zones still hard-fails
- Challenger smoke target:
  - the clock strip no longer reads as a flat pasted banner
  - the wall mark no longer floats
  - only the approved clock strip and wall mark are readable
  - Challenger remains manual-only; no pipeline auto-run change

### Assumptions
- Scope is stills only.
- This refinement does not relax zero-letter generation rules.
- No automatic surface detection or auto-quad inference is added; quads remain manually authored.
- No rollout to Therac, thumbnail, or Shorts is included in this refinement.
- Shared v1.1 is the target, with Challenger as the first preset to retune against it.

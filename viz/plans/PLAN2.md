## Challenger Controlled-Typography Pilot

### Summary
- Use the new controlled typography support to reopen only `scene_still/challenger_mission_control`.
- Keep rollout manual first: leave [challenger_mission_control.json](/Users/mike/Viz_CascadeEffects/workflows/typography/scene_still/challenger_mission_control.json) at `enabled: false` and use explicit `bin/ce render typography ...` reruns during tuning.
- Do not expand to Therac, thumbnail, or Shorts until one approved Challenger hero exists.

### Key Changes
- Reframe the Challenger lane around one new still-generation pass, not around patching the current [hero_still.png](/Users/mike/Viz_CascadeEffects/references/challenger_mission_control/selects/hero_still.png). The current hero is too documentary and text-heavy beyond what typography support should salvage.
- Update the Challenger reference/rubric so [launch_control_center_renovated.jpg](/Users/mike/Viz_CascadeEffects/references/challenger_mission_control/board/launch_control_center_renovated.jpg) is allowed as an environment/layout ref under controlled typography, while the more text-heavy documentary room refs stay demoted or removed as meaning carriers.
- Keep the generative prompt zero-letter and mechanism-first. Do not invite readable words into the image model; the scene should still read through dead CRT, warning lamp, switchgear, and room tension.
- Run one fresh 8-variant Challenger draft batch, shortlist only frames whose base image already works with all text mentally removed, then run refine/final on the best seed.
- After selecting the best zero-letter base final, apply manual controlled typography with at most two environmental zones:
  - one wall-clock strip
  - one wall mark
- Keep the live workflow contract unchanged for now: use the existing `bin/ce render typography ...` path, do not auto-enable `--typography auto` for Challenger until approval is earned.

### Interfaces
- No new interface changes.
- Operational policy for this rollout:
  - `bin/ce render stage scene_still challenger_mission_control draft_txt2img --set variant_count=8`
  - refine/final only for the chosen seed
  - `bin/ce render typography scene_still challenger_mission_control --image /absolute/path/to/final.png` only after a base still is selected
- Keep the Challenger typography sidecar manual-only during tuning.

### Test Plan
- `bin/ce workflow validate all` still passes.
- New Challenger draft batch produces 8 outputs plus run manifests.
- Chosen base still must satisfy all of these before typography:
  - no readable text dependence
  - no document/paper clue
  - no scenic conference-room overview
  - no uncontrolled interface glyphs or marked console faces
  - frame still communicates Challenger failure without added text
- Typography rerun must satisfy all of these:
  - only the declared wall-clock strip and wall mark are readable
  - no OCR-detected readable text survives outside approved zones
  - composited version is more episode-specific than the base still without becoming documentary clutter
- Promote a new Challenger hero only if both the base final and the composited final pass review.

### Assumptions
- Challenger is the only rollout target for the next iteration.
- Manual-first is locked: no auto-enable of the Challenger typography sidecar yet.
- The current Challenger hero is not the salvage target.
- Therac, thumbnail, and Shorts remain unchanged until the Challenger pilot produces one approved hero.

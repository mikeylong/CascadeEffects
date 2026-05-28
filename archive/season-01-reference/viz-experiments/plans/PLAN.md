## Controlled Typography Support for Stills

### Summary
- Add controlled typography support as a repo-owned postprocess inside the still-image workflow, not as a prompt-side attempt to make the model spell better.
- Keep generative stages zero-letter by default across active families; readable type is allowed only through explicit approved zones after `final_upscale`.
- V1 scope is stills only, overlay-first, environmental-only typography. Video support is deferred but should reuse the same contracts later.

### Key Changes
- Extend `bin/ce render pipeline` in [render_tool.py](/Users/mike/Viz_CascadeEffects/scripts/render_tool.py) with a fourth still-only post step: after `final_upscale`, automatically run controlled typography when the preset opts in.
- Add a dedicated typography sidecar per preset, outside the prompt/spec text, so readable strings are declared structurally instead of leaking into prompts or notes. Use a machine-readable contract with:
  - `enabled`
  - `mode: overlay_first`
  - `apply_stage: final_upscale`
  - `max_zones`
  - `zones[]`
- Define each zone with a fixed v1 schema:
  - `id`
  - `kind`
  - `text`
  - `quad_norm` as four normalized points in output coordinates
  - `font_family`
  - `font_size_px`
  - `tracking`
  - `color`
  - `opacity`
  - `blend_mode`
  - `blur_px`
  - `glow_px`
  - `noise_strength`
- Restrict v1 `kind` values to environmental surfaces only: wall clock strips, wall marks, room signs, and large non-interactive display surfaces. Exclude paperwork, badges, decals, labels, control-panel UI, and dense monitor text.
- Implement the compositor in a new still-image postprocess tool, called from the render pipeline rather than embedded in Comfy graphs. It should:
  - rasterize real text
  - perspective-warp it into the declared quad
  - apply blur, bloom, noise, and opacity so it sits in the image
  - optionally neutralize accidental underlying glyphs inside the same zone before compositing
- Keep global anti-text prompt validation in [workflow_tool.py](/Users/mike/Viz_CascadeEffects/scripts/workflow_tool.py) for generative prompts, negative prompts, and normal notes. Add a separate validator for typography sidecars so controlled text is allowed only there.
- Add a dedicated rerun entrypoint so typography can be re-applied to an existing final still without re-running generation. Keep both the zero-letter base final and the typography-composited final in run outputs and manifests.

### Interfaces
- `bin/ce render pipeline <family> <preset> ... --typography auto|off|force`
  - `auto`: run the typography pass only when the preset sidecar enables it
  - `off`: skip it even if enabled
  - `force`: require it and fail if the preset is not configured
- Add a still-only reapply command in [render_tool.py](/Users/mike/Viz_CascadeEffects/scripts/render_tool.py):
  - `bin/ce render typography <family> <preset> --image /abs/path/to/final.png`
- Extend run manifests to record:
  - base final image path
  - typography sidecar used
  - typography output image path
  - per-zone text payload and style settings
  - any validation results

### Validation and Review Rules
- Zero-letter remains the default generation rule. Prompts should still describe blank or unresolved text surfaces, not readable words.
- Controlled typography is valid only when declared in the sidecar; any readable text outside approved zones is a failure.
- Add postprocess validation with two checks:
  - approved zones must render exactly the declared string
  - no OCR-detected readable text may remain outside approved zones
- References such as [launch_control_center_renovated.jpg](/Users/mike/Viz_CascadeEffects/references/challenger_mission_control/board/launch_control_center_renovated.jpg) become usable as environment/layout refs again only when their readable surfaces are either ignored or mirrored by declared typography zones.

### Test Plan
- `bin/ce workflow validate all` still passes for presets without typography sidecars.
- Validation fails when a typography sidecar:
  - exceeds the zone budget
  - uses a disallowed zone kind
  - has malformed `quad_norm`
  - is enabled for a stage other than `final_upscale`
- `bin/ce render pipeline ... --typography auto` leaves unchanged presets unchanged, and produces both base and composited finals for opted-in presets.
- `bin/ce render typography ...` can reapply the typography layer to an existing final still without regenerating the image.
- OCR-based checks fail when:
  - rendered zone text does not match the declared string
  - extra readable text appears outside approved zones
- First smoke target: a Challenger still with one approved wall-clock strip zone and one approved wall-mark zone, derived from the environment/layout language of `launch_control_center_renovated.jpg`.

### Assumptions
- V1 is stills only; video tracking/compositing is a later phase using the same zone contract.
- Overlay-first is the default and only supported typography mode in v1; localized OCR-validated text-patch generation is deferred.
- Environmental-only readable text is allowed in v1. Paperwork, labels, badges, decals, and interactive UI text remain out of scope.
- OCR is a required local dependency for leak detection and exact-match validation in the controlled typography pass.

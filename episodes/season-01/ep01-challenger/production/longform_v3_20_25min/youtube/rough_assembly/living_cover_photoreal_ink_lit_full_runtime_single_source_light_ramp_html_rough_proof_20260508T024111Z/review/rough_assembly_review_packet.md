# Rough Assembly Review Packet: Single-Source Light Ramp

## Review Question

Does the single-source dark-to-lit ramp work for the Challenger Living Cover while preserving the frozen rail/caption system?

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.

## Player

- `player.html`
- Local HTTP review is recommended because browser-native VTT loading is used.

## Key Behavior

- The proof uses one source image only.
- The dark base layer and lit overlay are the same file, same transform, same geometry.
- The lit overlay follows the story-shaped opacity ramp across the full `00:21:29.131` runtime.

## Required Reads

- `single_source_light_ramp_read`: pending human review
- `dark_start_read`: pending human review
- `story_shaped_opacity_ramp_read`: pending human review
- `same_source_layer_read`: pass/computed QA
- `same_layer_geometry_read`: pass/computed QA
- `caption_behavior_read`: pass/computed QA
- `downstream_gate_lock_read`: pass

No render, final assembly, Shorts, publish readiness, or YouTube action is authorized.

## Human Review Update

- Disposition: `tighten`
- Reviewer note: expected an increase in lighting intensity, not a lit-layer opacity reveal.
- Successor packet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_full_runtime_single_source_light_intensity_html_rough_proof_20260508T032225Z`
- Downstream gates remain locked: no MP4 render, final assembly, Shorts, publish readiness, or YouTube action.

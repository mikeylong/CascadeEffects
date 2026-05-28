# 737 MAX Source-Art Generation Gate - Non-Paper Repair

Date: 2026-05-19

Workflow: `long_form_video_production_v1`

Gate: `source_art_generation`

Disposition: `ready_for_built_in_imagegen`

## Gate Basis

The replacement 737 MAX visual system received human `keep`.

- Human visual-system keep: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/human_visual_system_keep_non_paper_20260519.md`
- Human visual-system keep SHA-256: `e306d090cba3f5cde91e30c4df987e3698fa47740d6f5291f2977f3a4b024598`
- Visual system plan: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/visual_system_plan_non_paper_repair_20260519.md`
- Visual system plan SHA-256: `4d1a94e4e930b4fe8f12e217b4dd3bd8111b26e19a6dd7b689f330f45f79c51f`
- Source-art prompt: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/prompts/737_max_source_art_imagegen_non_paper_prompt_20260519.md`
- Source-art prompt SHA-256: `befc40361f7a17a2c3077a15b9ee9454785385e8d8a6ca3457fd7cddb28fa264`

## Active Source-Art Policy

- Primary lane: `cascade-ink-lit-photoreal-v1`
- Carrier type: `generated_raster_source_art`
- Generation tool: Codex built-in ImageGen through the `imagegen` skill.
- Canvas target: `1920x1080`
- Source-art candidate status: `not_generated`
- Source-art keep status: `blocked_pending_candidate_review`
- `video_visual_style_scope_read`: `pass_long_form_video_asset_non_paper`
- `paper_architecture_visual_style_read`: `pass_no_resemblance`
- `long_form_source_art_lane_read`: `pass_source_preserving_photoreal`
- `paper_architecture_resemblance_read`: `pass_absent`

Reference aircraft photos, official documents, accident reports, cockpit imagery, and the 737 visual research inventory are evidence for judging recognizability and accuracy only. They are not active source art unless a later human-approved source-art exception names exact source paths, rights/source risk, reason, and affected outputs.

## Required Review Reads Before Source-Art Keep

- `historical_accuracy_read`
- `source_reference_alignment_read`
- `public_anchor_geometry_read`
- `737_max_aircraft_profile_read`
- `leap_engine_placement_read`
- `angle_of_attack_sensor_cue_read`
- `mcas_stabilizer_mechanism_read`
- `single_sensor_assumption_read`
- `training_commonality_document_cue_read`
- `generated_text_logo_read`
- `human_presence_read`
- `no_recognizable_faces_read`
- `no_crash_spectacle_read`
- `texture_noise_read`
- `waterfall_read`

## Gate Effect

- May generate source-art candidate: `true`
- May mark source-art `keep`: `false`
- May create cue map: `false`
- May create ambient/effects layer: `false`
- May create music integration contract: `false`
- May start motion readiness: `false`
- May start rough assembly: `false`
- May render final MP4: `false`
- May perform YouTube action: `false`

## Next Action

Generate one source-art candidate from the prompt, copy it into the 737 MAX long-form production tree, create QA previews, and review it against the required 737 MAX reads before any source-art `keep`.

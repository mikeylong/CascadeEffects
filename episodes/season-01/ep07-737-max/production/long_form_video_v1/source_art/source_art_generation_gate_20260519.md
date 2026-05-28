# 737 MAX Source-Art Generation Gate

- episode: 737 MAX
- workflow: long_form_video_production_v1
- recorded_at_utc: 2026-05-19T03:52:15Z
- gate: source_art_generation
- disposition: blocked_wrong_longform_style_paper_architecture
- may_generate_source_art: false
- may_mark_source_art_keep: false
- may_build_motion_or_rough_proof: false
- may_youtube_action: false

## Invalidation

This source-art generation gate is no longer active. The upstream visual-system plan and prompt used Paper Architecture visual style for a long-form episode backplate. Mike corrected the video style rule, so this gate cannot authorize ImageGen generation or candidate advancement.

- invalidation_path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/source_art_generation_gate_invalidation_wrong_longform_style_20260519.md
- video_visual_style_scope_read: reject_video_asset_used_paper_architecture
- paper_architecture_visual_style_read: reject
- long_form_source_art_lane_read: reject_paper_architecture_not_allowed_for_long_form_backplate
- paper_architecture_resemblance_read: reject

## Opened By

- visual_system_keep_path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/human_visual_system_keep_20260519.md
- visual_system_keep_sha256: 1ceba16ef9d36b75b77c9e065eb5504a8e1c75042f9d7d85d7e273258155504b
- visual_system_plan_path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/visual_system_plan_20260519.md
- visual_system_plan_sha256: c18bf79df3d688df9e61486fd18ccb430a11c7cadb2193eac0cb8d205fcac6e1

## Generation Packet

- prompt_path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/prompts/737_max_source_art_imagegen_prompt_20260519.md
- prompt_status: invalidated_wrong_longform_style_paper_architecture
- generation_tool: codex_builtin_image_gen
- carrier_type: generated_raster_source_art
- visual_profile: cascade-paper-architectures-ink-lit-v1
- target_canvas: 1920x1080
- expected_workspace_candidate_path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/candidates/737_max_living_cover_source_art_candidate_a_20260519.png

## Boundary

This gate does not authorize any further generation. Candidate A exists only as a rejected provenance record. Cue map, ambient/effects layer, music integration, motion readiness, rough assembly, final assembly, upload, and public release remain blocked.

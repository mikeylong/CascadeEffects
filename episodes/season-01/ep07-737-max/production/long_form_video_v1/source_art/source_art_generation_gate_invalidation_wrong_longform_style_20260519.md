# 737 MAX Source-Art Generation Gate Invalidation

- episode: 737 MAX
- workflow: long_form_video_production_v1
- recorded_at_utc: 2026-05-19T04:07:06Z
- gate: source_art_generation
- disposition: blocked_wrong_longform_style_paper_architecture
- may_generate_source_art: false
- may_mark_source_art_keep: false
- may_build_cue_map: false
- may_build_motion_or_rough_proof: false
- may_youtube_action: false

## Invalidated Gate

- source_art_generation_gate_path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/source_art_generation_gate_20260519.md
- source_art_generation_gate_prior_sha256: 469f9c1b39ec0ba7fd48f7b55733600e9351a4c347016ff89bfd6c7e6c2cfd58
- source_art_prompt_path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/prompts/737_max_source_art_imagegen_prompt_20260519.md
- source_art_prompt_prior_sha256: d43f72190e141d853d705acb1eb4e3dba7b972631e1bb6969810b52c68cea710
- invalidated_visual_profile: cascade-paper-architectures-ink-lit-v1

## Decision

This gate no longer authorizes ImageGen source-art generation. The prompt used Paper Architecture visual style for a long-form episode backplate. Any candidate produced from that prompt is review-record evidence only and cannot advance.

## Next Gate

Return to visual-system planning. Source-art generation can reopen only after a corrected non-Paper-Architecture long-form visual-system plan receives explicit human `keep`.

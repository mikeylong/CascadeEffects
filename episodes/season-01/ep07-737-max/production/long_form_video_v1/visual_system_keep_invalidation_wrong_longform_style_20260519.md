# 737 MAX Visual-System Keep Invalidation

- episode: 737 MAX
- workflow: long_form_video_production_v1
- recorded_at_utc: 2026-05-19T04:07:06Z
- disposition: invalidated_wrong_longform_style_paper_architecture
- reviewer: Mike
- correction: Video assets must not use Paper Architecture visual style.
- may_open_source_art_generation: false
- may_mark_source_art_keep: false
- may_build_cue_map: false
- may_build_motion_or_rough_proof: false
- may_youtube_action: false

## Invalidated Inputs

- visual_system_plan_path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/visual_system_plan_20260519.md
- visual_system_plan_prior_sha256: c18bf79df3d688df9e61486fd18ccb430a11c7cadb2193eac0cb8d205fcac6e1
- human_visual_system_keep_path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/human_visual_system_keep_20260519.md
- human_visual_system_keep_prior_sha256: 1ceba16ef9d36b75b77c9e065eb5504a8e1c75042f9d7d85d7e273258155504b
- invalidated_visual_profile: cascade-paper-architectures-ink-lit-v1

## Decision

The earlier visual-system keep is superseded. It approved a Paper Architecture source-art lane for a long-form episode backplate, which is now a style-policy violation. Paper Architecture is allowed only for website assets, YouTube channel-level branded visual assets, and CascadeEffects.tv website thumbnail-gallery images. It does not authorize source-art generation, source-art keep, cue-map construction, ambient/effects work, rough assembly, final render, publish readiness, upload, or public release.

## Repair Requirement

The next active 737 MAX long-form step is a corrected visual-system plan using `cascade-ink-lit-photoreal-v1` or another episode-specific source-preserving/photoreal public-scene carrier. The plan must record:

- `video_visual_style_scope_read`
- `paper_architecture_visual_style_read`
- `long_form_source_art_lane_read`
- `paper_architecture_resemblance_read`
- historical/source-reference reads for the 737 MAX public anchor
- explicit downstream locks with source-art generation blocked until a new human visual-system `keep`

# Piltdown Man Long-Form Visual Style Invalidation

- episode: Piltdown Man
- workflow: long_form_video_production_v1
- recorded_at_utc: 2026-05-19T04:16:47Z
- disposition: invalidated_wrong_video_visual_style_paper_architecture
- video_visual_style_scope_read: reject_video_asset_used_paper_architecture
- paper_architecture_visual_style_read: reject
- may_start_source_art_generation: false
- may_mark_source_art_keep: false
- may_build_cue_map: false
- may_build_motion_or_rough_proof: false
- may_youtube_action: false

## Invalidated Inputs

- visual_system_plan_path: /Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/visual_system_plan_20260518.md
- visual_system_plan_prior_sha256: ad03a36456e8e2835c9abeb8c5083a6f339417aae2efc5657ede0a3fdd0df5b1
- human_visual_system_keep_path: /Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/human_visual_system_keep_20260518.md
- human_visual_system_keep_prior_sha256: fb5e9cbd319fa03fc479fe3a5c9890328975887209f0b762ff568aa001b0aedf
- source_art_generation_manifest_path: /Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/source_art_generation_20260518/source_art_generation_manifest.json
- source_art_generation_manifest_prior_sha256: c68aecd027ce337f3e6cbfa8ac4231a65a7e0ef3f4f96bf4da298499417e3bfc
- invalidated_visual_profile: cascade-paper-architectures-ink-lit-v1

## Decision

The Piltdown Man long-form visual-system keep and source-art candidate review state are superseded. Paper Architecture visual style is allowed only for CascadeEffects.tv website visual assets, YouTube channel-level branded visual assets, and CascadeEffects.tv website thumbnail-gallery images. It is not allowed for long-form video source art, Living Cover backplates, rough proofs, finals, cover frames, in-video end screens, or video thumbnails.

The existing generated candidates are preserved as provenance/evidence only. They cannot be marked `keep` or used downstream.

## Next Gate

Return to visual-system planning with a non-Paper-Architecture long-form video lane, then require explicit human visual-system `keep` before any new source-art generation.

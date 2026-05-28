# Semmelweis Long-Form Visual Style Invalidation

- episode: Semmelweis
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

- visual_system_plan_path: /Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/visual_system_plan_20260518.md
- visual_system_plan_prior_sha256: 9805b6e65da363dfe559eaec95fedb3f209f21dca9428054a31c398fc0bc4b9c
- visual_system_review_manifest_path: /Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/visual_system_review_20260518/manifest.json
- visual_system_review_manifest_prior_sha256: 73f25502092301974b7fa030124ae728df2578d9de94cc34c636b21a87a76030
- source_art_manifest_path: /Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/youtube/source_art/semmelweis_autopsy_to_ward_imagegen_20260518T205238/source_art_manifest.json
- source_art_manifest_prior_sha256: 1564d3cac83086d1e6b8a98d2f56ac4a8344a1868acdc2e2d78317162a3b00de
- invalidated_visual_profile: cascade-paper-architectures-ink-lit-v1

## Decision

The Semmelweis long-form visual-system keep and source-art review state are superseded. Paper Architecture visual style is allowed only for CascadeEffects.tv website visual assets, YouTube channel-level branded visual assets, and CascadeEffects.tv website thumbnail-gallery images. It is not allowed for long-form video source art, Living Cover backplates, rough proofs, finals, cover frames, in-video end screens, or video thumbnails.

The existing source-art candidates are preserved as provenance/evidence only. They cannot be marked `keep` or used downstream.

## Next Gate

Return to visual-system planning with a non-Paper-Architecture long-form video lane, then require explicit human visual-system `keep` before any new source-art generation.

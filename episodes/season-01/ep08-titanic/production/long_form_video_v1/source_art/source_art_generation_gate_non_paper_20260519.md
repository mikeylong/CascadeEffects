# Titanic Source-Art Generation Gate - Non-Paper

Date: 2026-05-19

Workflow: `long_form_video_production_v1`

Gate: `source_art_generation`

Disposition: `ready_for_built_in_imagegen`

## Gate Basis

The Titanic visual system received human `keep`.

- Human visual-system keep: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/human_visual_system_keep_20260519.md`
- Visual system plan: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/visual_system_plan_20260519.md`
- Visual system plan SHA-256: `680e2a44f69cdc12c33b321492528c0f4c51963c697caf09b3798ce6260702a9`
- Source-art prompt: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/source_art/prompts/titanic_source_art_imagegen_non_paper_prompt_20260519.md`

## Active Source-Art Policy

- Primary lane: `cascade-ink-lit-photoreal-v1`
- Episode visual style: `titanic_boat_deck_lifeboat_regulation_gap_photoreal_v1`
- Carrier type: `generated_raster_source_art`
- Generation tool: Codex built-in ImageGen through the `imagegen` skill.
- Canvas target: `1920x1080`
- Source-art candidate status: `not_generated`
- Source-art keep status: `blocked_pending_candidate_review`
- `video_visual_style_scope_read`: `pass_long_form_video_asset_non_paper`
- `paper_architecture_visual_style_read`: `pass_no_resemblance`
- `long_form_source_art_lane_read`: `pass_source_preserving_photoreal`
- `paper_architecture_resemblance_read`: `pass_absent`

Reference ship-deck photographs, report scans, Board of Trade records, lifeboat/davit imagery, and the existing Titanic Short are evidence for judging recognizability and accuracy only. They are not active source art unless a later human-approved source-art exception names exact source paths, rights/source risk, reason, and affected outputs.

## Required Review Reads Before Source-Art Keep

- `historical_accuracy_read`
- `source_reference_alignment_read`
- `public_anchor_geometry_read`
- `titanic_boat_deck_read`
- `lifeboat_davit_accuracy_read`
- `lifeboat_capacity_visual_logic_read`
- `board_of_trade_document_cue_read`
- `period_maritime_materials_read`
- `disaster_spectacle_absence_read`
- `generated_text_logo_read`
- `human_presence_read`
- `no_recognizable_faces_read`
- `texture_noise_read`
- `video_visual_style_scope_read`
- `paper_architecture_visual_style_read`
- `procedural_signal_overlay_read`
- `ambient_line_artifact_read`
- `source_provenance_read`
- `rights_and_content_id_risk_read`

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

Generate one source-art candidate from the prompt, copy it into the Titanic long-form production tree, create QA previews, and review it against the required Titanic reads before any source-art `keep`.

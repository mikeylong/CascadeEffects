# Titanic Motion Readiness Review Packet

Date: 2026-05-19

Episode: Titanic

Workflow: `long_form_video_production_v1`

Artifact status: `review_ready_pending_human_keep`

Current gate: `motion_readiness_keep`

## Review Surface

- Review HTML: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/living_cover/motion_readiness/review_candidate_e_boat_deck_weather_readiness_20260519/review.html`
- Candidate: `candidate_e_boat_deck_weather_readiness`
- Carrier: approved 1920x1080 generated raster source art
- Living Cover system: `living_cover_system_v1`
- Rail preset: `fixed_16x9_right_rail_v1`
- Caption model: script-locked right-rail caption samples from the offset sidecar
- Role: motion-readiness visual review only
- Right rail conformance repair: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/living_cover/motion_readiness/review_candidate_e_boat_deck_weather_readiness_20260519/right_rail_conformance_repair_20260519.md`

## Visual Scope

The review surface shows the first reviewable post-backplate Living Cover artifact for Titanic. It uses the kept Candidate E backplate and deterministic HTML/CSS/JS compositing for:

- source-safe plate drift
- restrained practical lamp micro-life
- existing wet deck reflection shimmer
- rope/fall/davit tension accents
- faint sea/dawn air movement
- fixed right rail with semantic chapter states
- lower-right rail caption samples

## Right Rail Conformance Repair

The review surface was tightened to the shared `fixed_16x9_right_rail_v1` styling used by current Living Cover proofs. The rail now uses the canonical fixed right-side geometry, shared Tacoma-style class vocabulary, a source-aware cold blue-gray active panel, flat muted context dots, and a separate native lower-rail caption softener instead of a rounded caption card. Title, context, and rail-caption copy suppress terminal periods; `active-summary` may use sentence punctuation.

This is a style conformance repair only. It does not change Candidate E, chapter/caption copy, ambient layer intent, audio, rough assembly status, final render status, upload prep, YouTube action, or public release state.

## Gate Boundaries

This is not a rough assembly proof. It has no mixed audio track, no rendered MP4, no upload preparation, and no YouTube action.

A human `keep` on this packet may open rough assembly planning/proof creation only if all rough proof requirements remain satisfied. Final render, upload prep, YouTube action, and public release remain blocked.

## Required Reads

- `motion_readiness_artifact_read`: `pass_review_html_created`
- `source_art_visibility_read`: `pass_candidate_e_visible_as_backplate`
- `living_cover_system_read`: `pass_fixed_16x9_right_rail_v1`
- `right_rail_safe_space_read`: `pass_fixed_right_52_top_bottom_52_width_760`
- `rail_typography_conformance_read`: `pass_fixed_26_64_34_28_40_px_hierarchy`
- `rail_shared_vocabulary_read`: `pass_tacoma_style_living_cover_classes`
- `caption_text_source_read`: `pass_script_locked_caption_samples_from_offset_sidecar`
- `caption_asr_text_not_used_read`: `pass_visible_caption_samples_from_locked_script_outputs`
- `ambient_effects_plan_read`: `pass_kept_layer_represented_visually`
- `practical_light_micro_life_read`: `pass_restrained_lamp_breathing_only`
- `wet_deck_reflection_read`: `pass_subtle_existing_reflection_shimmer_only`
- `rope_fall_tension_read`: `pass_tiny_existing_rope_fall_davit_attention_only`
- `sea_dawn_air_read`: `pass_faint_depth_atmosphere_not_smoke_grit_or_debris`
- `source_plate_matte_registration_read`: `pass_fixed_1920x1080_coordinate_space`
- `effect_layer_source_safety_read`: `pass_preserve_candidate_e_geometry_no_new_boat_ship_or_disaster_elements`
- `deterministic_ambient_read`: `pass_css_js_parameters_declared_in_review_html`
- `debug_overlay_absence_read`: `pass_no_diagnostic_overlay_in_canvas`
- `visible_cue_overlay_read`: `pass_no_cue_ids_or_internal_labels_in_canvas`
- `viewer_text_surface_inventory_read`: `pass_right_rail_chapter_context_caption_only`
- `right_rail_text_boundary_read`: `pass_all_viewer_story_text_inside_fixed_right_rail`
- `out_of_rail_text_read`: `pass_no_viewer_facing_out_of_rail_text_inside_canvas`
- `ordinal_chapter_label_read`: `pass_no_ordinal_only_visible_labels`
- `full_frame_dark_overlay_read`: `pass_no_global_dark_veil`
- `localized_readability_treatment_read`: `pass_active_panel_and_separate_caption_softener_only`
- `right_rail_opacity_balance_read`: `pass_no_full_height_opaque_right_column`
- `context_region_source_visibility_read`: `pass_context_region_has_no_opaque_backing`
- `caption_softener_scope_read`: `pass_separate_lower_rail_softener_no_card_badge_border_or_glow`
- `rail_punctuation_style_read`: `pass_no_terminal_periods_except_active_summary`
- `foreground_admin_prop_read`: `pass_no_admin_anchor_added`
- `video_visual_style_scope_read`: `pass_long_form_video_asset_non_paper`
- `paper_architecture_visual_style_read`: `pass_no_paper_architecture_style`

## Validation Note

Static HTML/CSS checks confirmed the repaired selectors and removed the prior rounded caption card class. In-app browser automation refused to reload or inspect the local `file://` review page under Browser URL policy, so no new browser-driven screenshots were generated in this repair pass. Existing screenshot files remain path/hash-valid historical motion-readiness references, but the conformance evidence for this repair is the repaired HTML plus the right rail conformance note.

## Required Human Decision

Human review must mark this motion-readiness artifact `keep`, `tighten`, or `reject`.

Only `keep` may open rough assembly proof work. Rough assembly, final render, upload prep, YouTube actions, and public release remain blocked now.

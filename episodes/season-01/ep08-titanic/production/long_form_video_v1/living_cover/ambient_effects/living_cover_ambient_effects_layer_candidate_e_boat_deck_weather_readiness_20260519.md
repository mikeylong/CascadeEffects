# Titanic Living Cover Ambient/Effects Layer - Candidate E

Date: 2026-05-19

Workflow: `long_form_video_production_v1`

Gate: `living_cover_ambient_effects_layer`

Status: `review_ready_pending_human_keep`

Human disposition: `pending`

May advance: `false`

This packet defines the source-integrated ambient/effects layer for the kept Titanic Candidate E Living Cover backplate. It does not create a rough proof, music contract, final render, upload package, or YouTube action.

## Inputs

- Source-art candidate: `candidate_e_boat_deck_weather_readiness`
- Source-art plate: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/source_art/assets/source_art/candidate_e_boat_deck_weather_readiness_1920x1080.png`
- Source-art SHA-256: `e5a07275f94c6af4fe374892284042a5efc1b4a932de9be437b2a40588aad38f`
- Cue map: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/living_cover/cue_map/living_cover_cue_map_candidate_e_boat_deck_weather_readiness_20260519.md`
- Cue map SHA-256: `23e18606a863dd9a96f6ac12f2e57a8bd21ac07f18efc99c9a9090093dce408b`
- Cue map JSON: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/living_cover/cue_map/living_cover_cue_map_candidate_e_boat_deck_weather_readiness_20260519.json`
- Cue map JSON SHA-256: `c8ce228645c1cf6f6ecd18984270a4dc8e013db20b99dac02cd43f98cbd42e1b`
- Human cue-map keep: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/living_cover/cue_map/human_living_cover_cue_map_keep_candidate_e_20260519.md`
- Human cue-map keep SHA-256: `18872ca258a12732f7b8cf50e82fa7aa361d5dc1c205275ae1732c5b51559ccd`
- Audio duration: `740.716553` seconds
- Coordinate space: fixed `1920x1080`

## Lane Decision

Lane: `mixed_minimal_boat_deck_micro_life_v1`

The active visual carrier is a pre-disaster boat-deck readiness scene. The ambient layer should make the image feel alive without changing the historical claim or creating disaster spectacle. Effects must preserve the kept source art and stay subordinate to the right-rail chapter/caption system.

## Selected Layers

- `source_plate_drift`: slow source-safe plate drift and tiny crop changes keyed to cue-map chapters. No hard chapter transform switches.
- `practical_lamp_micro_life`: restrained warm lamp breathing around deck practicals. No sparks, fire, explosions, or emergency flashes.
- `wet_deck_reflection_shimmer`: subtle shimmer in existing damp deck reflections. No waterfalls, liquid graphics, spills, or new water streams.
- `rope_fall_tension_accents`: tiny contrast/shadow emphasis around rope, fall, davit, and covered-lifeboat regions during davit/capacity chapters. No new boat geometry.
- `sea_dawn_air_movement`: faint cold air and sea/dawn light movement beyond the deck depth. Must not read as smoke, grit, debris, fog wall, or sinking atmosphere.
- `localized_rail_readability`: source-aware active-panel and caption support only. No full-frame dark veil and no full-height opaque right-column panel.
- `end_screen_background_continuity`: future rough proof may continue ambient motion behind static YouTube target geometry only after end-screen reads pass.

## Deterministic Parameters For Rough Builder

- Seed: `titanic_candidate_e_ambient_20260519_v1`
- Source transform scale range: `1.000` to `1.018`
- Source transform x drift range: `-10px` to `10px`
- Source transform y drift range: `-6px` to `6px`
- Chapter transition easing target: `18s` to `28s`
- Lamp micro-life opacity delta: `0.00` to `0.055`
- Wet reflection shimmer opacity delta: `0.00` to `0.035`
- Rope/fall accent opacity delta: `0.00` to `0.025`
- Sea/dawn air opacity ceiling: `0.045`
- Rail readability treatment: localized active-panel fill and caption softener only.

These parameters are planning values. The rough builder may tighten exact values, but must preserve the lane, coordinate space, source-safety rules, and all blockers here.

## Browser QA Sample Times For Future Proof

- `00:00:00.000` opening settled rail/source state
- `00:00:46.234` wrong-measurement turn
- `00:02:43.922` category-ceiling turn
- `00:04:27.223` compliance/sufficiency turn
- `00:05:49.192` davit visual hinge
- `00:07:07.210` thinkable/required gap
- `00:08:36.052` out-of-date record
- `00:10:20.778` people-not-tonnage turn
- `00:12:14.621` series motif
- `00:12:20.717` sign-off/end-screen handoff

The future rough proof must support range-scrub review so late-episode ambient behavior can be checked without replaying from the beginning.

## Hard Blocks

- No new source-art backplate, source repaint, ship geometry, boat count, lifeboat launch, sinking, iceberg strike, wreckage, smoke, debris, bodies, or panic crowd.
- No foreground clipboards, binders, folders, paperwork stacks, legal pads, trays, hearing-room paperwork, evidence-table props, or administrative visual anchors.
- No cue IDs, implementation labels, route overlays, matte previews, diagnostic text, debug panels, cyan vectors, connector lines, generated UI paths, or effect-lane names in viewer-facing output.
- No recognizable faces, generated logos, readable ship/company text, modern signage, modern safety gear, or modern cruise-ship details.
- No rough assembly until this packet receives explicit human `keep`.

## Reads

- `ambient_effects_plan_read`: `pass_packet_local_layer_created`
- `ambient_effect_lane_decision_read`: `pass_mixed_minimal_boat_deck_micro_life`
- `source_plate_matte_registration_read`: `pass_fixed_1920x1080_coordinate_space_required_before_rough`
- `foreground_occlusion_read`: `pass_no_new_people_faces_or_foreground_object_effects_planned`
- `effect_layer_source_safety_read`: `pass_preserve_candidate_e_geometry_no_new_boat_ship_or_disaster_elements`
- `deterministic_ambient_read`: `pass_seeded_parameters_declared_for_rough_builder`
- `additive_effect_integration_read`: `pass_successor_layers_must_preserve_kept_plate_cue_map_and_prior_approved_layers`
- `debug_overlay_absence_read`: `pass_required_for_viewer_facing_rough`
- `ambient_effect_browser_sample_read`: `pass_sample_times_declared_for_next_rough_review`
- `range_scrub_effect_review_read`: `pass_required_for_long_proof_review_server`
- `practical_light_micro_life_read`: `pass_restrained_lamp_breathing_only`
- `wet_deck_reflection_read`: `pass_subtle_existing_reflection_shimmer_only`
- `rope_fall_tension_read`: `pass_tiny_existing_rope_fall_davit_attention_only`
- `sea_dawn_air_read`: `pass_faint_depth_atmosphere_not_smoke_grit_or_debris`
- `localized_particle_density_read`: `not_applicable_no_particle_lane_selected`
- `particle_foreground_leak_read`: `not_applicable_no_particle_lane_selected`
- `rail_panel_palette_read`: `pass_source_integrated_cold_blue_gray_warm_lamp_palette_planned`
- `source_integrated_panel_color_read`: `pass_no_challenger_navy_default`
- `full_frame_dark_overlay_read`: `pass_blocked_prefer_localized_rail_readability`
- `localized_readability_treatment_read`: `pass_active_panel_and_caption_softener_only`
- `right_rail_opacity_balance_read`: `pass_no_full_height_opaque_right_column_planned`
- `context_region_source_visibility_read`: `pass_context_region_keeps_source_image_visible`
- `caption_softener_scope_read`: `pass_lower_rail_caption_softener_only_while_captions_visible`
- `procedural_signal_overlay_read`: `pass_no_overlay`
- `ambient_line_artifact_read`: `pass_no_cyan_or_diagnostic_lines`
- `disaster_spectacle_absence_read`: `pass_no_iceberg_sinking_wreckage_bodies_or_panic_crowd`
- `foreground_admin_prop_read`: `pass_no_admin_anchor_added_by_effect_layer`
- `video_visual_style_scope_read`: `pass_long_form_video_asset_non_paper`
- `paper_architecture_visual_style_read`: `pass_no_resemblance`

## Gate Locks

- `may_mark_ambient_effects_layer_keep`: `false`
- `may_create_music_integration_contract`: `false`
- `may_start_motion_readiness`: `false`
- `may_start_rough_assembly`: `false`
- `may_render_final_mp4`: `false`
- `may_youtube_action`: `false`
- `public_release_ready`: `false`

## Required Human Decision

Choose one:

- `keep living_cover_ambient_effects_layer`
- `tighten`
- `reject`

Only a human ambient/effects `keep` may open the `music_integration_contract` gate.

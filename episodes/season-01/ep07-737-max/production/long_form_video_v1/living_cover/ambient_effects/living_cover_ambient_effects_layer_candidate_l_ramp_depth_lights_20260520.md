# 737 MAX Living Cover Ambient/Effects Layer - Candidate L

Date: 2026-05-20

Workflow: `long_form_video_production_v1`

Gate: `living_cover_ambient_effects_layer`

Status: `review_ready_pending_human_keep`

Human disposition: `pending`

May advance: `false`

This packet defines the source-integrated ambient/effects layer for the kept 737 MAX Candidate L Living Cover backplate. It does not create a rough proof, music contract, final render, upload package, or YouTube action.

## Inputs

- Source-art candidate: `candidate_l_ramp_depth_lights`
- Source-art plate: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/source_art/candidates/737_max_living_cover_source_art_candidate_l_ramp_depth_lights_1920x1080_20260519.png`
- Source-art SHA-256: `05519145f11d4ceb49d38d6684fcb029877fca0bcec2329165eb81ff317a28b4`
- Cue map: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/living_cover/cue_map/living_cover_cue_map_candidate_l_ramp_depth_lights_20260519.md`
- Cue map SHA-256: `ba574646a29f68de063b1732712a67ac61e51bdd82769c96f7dacd8056d03fb5`
- Cue map JSON: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/living_cover/cue_map/living_cover_cue_map_candidate_l_ramp_depth_lights_20260519.json`
- Cue map JSON SHA-256: `10d1ce22367c96a5f05bfc560f6477b4ceb9bc97c5548e75f8f6e55ea480b346`
- Human cue-map keep: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/living_cover/cue_map/human_living_cover_cue_map_keep_candidate_l_20260520.md`
- Audio duration: `942.869478` seconds
- Coordinate space: fixed `1920x1080`

## Viewer-Facing Review Implementation

- Review HTML: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/review.html`
- Review HTML SHA-256: `b71f781a9943f5798b8b9a23ced139df377e3616209254b7bbc87fd6d6bf6207`
- Review URL: `http://127.0.0.1:8872/review.html?v=rain-visible-qa-3`
- Visual review manifest: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/living_cover/ambient_effects/review_candidate_l_20260520/manifest.json`
- Visual review manifest SHA-256: `863dc46dbea80b09dac0157d08645790ef8cd755c054d1dc7c405575e58d635e`
- Browser sample screenshot: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/living_cover/ambient_effects/review_candidate_l_20260520/review_candidate_l_ambient_browser_sample_1280x720.png`
- Browser sample screenshot SHA-256: `802cd53aebbbff8b34590bf53083e4e612f97395928a29e66a8b8996b5a6fabd`
- Rain visibility QA: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/living_cover/ambient_effects/review_candidate_l_20260520/qa_rain_visible_qa_3_browser_checks.json`
- Rain visibility QA SHA-256: `9ddc537a042a0aa57ab90e5a98bf20250f60319e8e6c661c9d361a85c4133848`
- Rain viewport delta proof: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/living_cover/ambient_effects/review_candidate_l_20260520/qa_rain_visible_qa_3_delta_x8_120s.png`
- Rain viewport delta proof SHA-256: `64e28468c5092e4bda742f7fd88368ffcbbed7f0b932d8af2ca6ffad517888b2`

The active review page now implements the ambient layer directly over Candidate L: source-plate drift, source-matched terminal-glass rain runners, foreground occlusion masks, wet-glass shimmer, practical light breathing, restrained aircraft surface glint, distant ramp-depth light motion, and terminal-glass reflection parallax. The first rain-runner pass was tightened after human feedback that the effect was not visible in review; the tone-match pass reduced white/cream highlights into a muted blue-gray rain-glass palette; the occlusion pass masks synthetic exterior rain off indoor foreground people and main mullions. This retry records the prior motion-visibility pass as `tighten_prior_motion_visibility_pass_failed_human_visibility`, registers the rain canvas to the same drift/scale transform as the source plate, and adds viewport on/off delta QA so the proof measures rendered visibility rather than canvas alpha alone. The implementation remains viewer-facing and contains no diagnostic overlays, effect labels, route lines, cue IDs, or Paper Architecture material cues.

## Lane Decision

Lane: `mixed_minimal_terminal_ramp_micro_life_v1`

The active visual carrier is a public airport terminal/ramp scene centered on an unbranded 737 MAX-family nose and larger forward/high-mounted engine relationship. The ambient layer should make the scene feel alive without turning the source plate into a diagram, disaster image, brand ad, or procedural UI.

## Selected Layers

- `source_plate_drift`: slow source-safe plate drift and tiny crop changes keyed to cue-map chapters. No hard chapter transform switches and no broad zoom that weakens the nose/engine geometry.
- `source_matched_glass_rain_runners`: review-visible small bead heads and longer near-vertical tails matched to Candidate L's existing terminal-window droplets, with over-white highlights reduced. Seeded by audio time for playback and scrub review; the canvas shares the source-plate drift/scale transform so glass rain and matte remain registered to the plate. No Tacoma foreground weather-app copy, macro windshield drops, whole-overlay scroll, or bubble shading.
- `foreground_occlusion_mask`: packet-local `destination-out` matte removes synthetic rain from indoor foreground viewer silhouettes and main mullions only. The source plate, baked-in source droplets, exterior ramp worker, aircraft, and tarmac remain untouched.
- `rain_glass_reflection_shimmer`: restrained shimmer in existing rain-glass and wet-surface reflections on the right-rail-safe side. No waterfall, water stream, liquid graphic, smoke, grit, or opaque gray block.
- `ramp_practical_light_micro_life`: subtle breathing in existing ramp, gate, terminal, or distant service lights. No emergency strobes, sparks, fire, explosion, or crash signal.
- `aircraft_surface_light_roll`: localized light drift across existing nose/engine contours to preserve the physical-change thesis. No labels, arrows, sensor markers, or MCAS diagram overlays.
- `distant_public_scene_motion`: extremely restrained distant ramp/public-scene light movement only where the source plate already implies depth. No new readable vehicle, logo, person, or airline identity.
- `terminal_glass_depth_parallax`: very small reflection/parallax behavior in glass or rain reflection only. Terminal mullions, people, and aircraft edges must not slide independently without a registered matte.
- `localized_rail_readability`: source-aware active-panel and caption support only. No full-frame dark veil and no full-height opaque right-column panel.
- `end_screen_background_continuity`: future rough proof may continue ambient motion behind static titleless YouTube target geometry only after end-screen reads pass.

## Deterministic Parameters For Rough Builder

- Seed: `737_max_candidate_l_ambient_20260520_v1`
- Source transform scale range: `1.000` to `1.014`
- Source transform x drift range: `-8px` to `8px`
- Source transform y drift range: `-5px` to `5px`
- Chapter transition easing target: `18s` to `30s`
- Rain-glass/reflection shimmer opacity delta: `0.00` to `0.040`
- Glass runner seed: `73720520`
- Glass runner count: `112`
- Glass pin-bead count: `168`
- Glass runner speed range: `18px/s` to `52px/s`
- Glass runner length range: `42px` to `132px`
- Glass runner width range: `1.35px` to `3.65px`
- Glass runner alpha range: `0.20` to `0.44`
- Glass pin-bead radius range: `0.65px` to `2.35px`
- Glass pin-bead alpha range: `0.055` to `0.15`
- Glass runner visibility repair: `visibility_qa_v4_registered_canvas_and_viewport_delta_pass`
- Glass runner tone-match repair: `muted_blue_gray_rain_glass_palette_overwhite_highlights_reduced`
- Glass runner canvas composite: `normal_with_subtle_dark_refractive_edge_and_muted_blue_gray_highlight`
- Glass runner source transform registration: `glass_runner_canvas_matches_source_plate_inset_drift_scale_transform`
- Glass runner motion salience repair: `speed_18_to_52px_per_second_length_42_to_132px_alpha_0_20_to_0_44_pulse_0_98_plus_minus_0_28`
- Glass runner viewport delta QA: visible/hidden screenshot delta at `120s`, max channel delta `74`, pixels with delta >= `8`: `6077`
- Glass runner canvas motion QA: `120s` to `121.5s`, pixels with delta >= `8`: `67867`
- Glass occlusion mask process: `packet_local_destination_out_mask_after_rain_draw`
- Glass occlusion mask count: `9`
- Glass occlusion mask coordinate space: `1920x1080_source_plate`
- Glass occlusion mask feather: `10px` to `18px`
- Glass occlusion people masks: `left_indoor_viewer`, `center_indoor_viewer`, `right_center_indoor_viewer`, `far_right_indoor_viewer`
- Glass occlusion mullion masks: `left_edge_mullion`, `left_main_mullion`, `center_main_mullion`, `right_main_mullion`, `right_edge_mullion`
- Glass runner scale policy: match Candidate L's existing distant terminal-glass droplets, not Tacoma's foreground weather-app bead scale.
- Ramp practical light opacity delta: `0.00` to `0.050`
- Aircraft surface light-roll opacity delta: `0.00` to `0.030`
- Distant public-scene motion opacity ceiling: `0.035`
- Rail readability treatment: localized active-panel fill and caption softener only.

These parameters are planning values. The rough builder may tighten exact values, but must preserve the lane, coordinate space, source-safety rules, and all blockers here.

## Browser QA Sample Times For Future Proof

- `00:00:00.000` opening settled rail/source state
- `00:00:38.170` "Both had lost" typography cue
- `00:01:20.606` physical-change chapter transition
- `00:03:33.171` "make it fly like one" hinge
- `00:04:51.209` single-sensor chapter transition
- `00:07:00.668` "It did not name MCAS" pause
- `00:10:59.173` procedure-versus-architecture chapter transition
- `00:13:44.344` "It was a system" synthesis
- `00:15:20.000` cause-chain close
- `00:15:42.869` sign-off/end-screen handoff

The future rough proof must support range-scrub review so late-episode ambient behavior can be checked without replaying from the beginning.

## Hard Blocks

- No new source-art backplate, source repaint, aircraft geometry, engine geometry, brand livery, tail number, airline logo, Boeing logo, readable signage, cockpit UI, MCAS UI, angle-of-attack overlay, stabilizer diagram, sensor marker, arrow, connector line, or cyan procedural trace.
- No crash scene, wreckage, explosion, fire, ocean impact, falling aircraft, emergency vehicle staging, debris, bodies, panic crowd, or disaster spectacle.
- No foreground clipboards, binders, folders, paperwork stacks, legal pads, trays, hearing-room paperwork, evidence-table props, or administrative visual anchors.
- No cue IDs, implementation labels, route overlays, matte previews, diagnostic text, debug panels, generated UI paths, or effect-lane names in viewer-facing output.
- No recognizable faces, face-forward pilots, executives, public officials, victims, generated celebrity likenesses, generated logos, or readable text.
- No full-frame dark veil, solid gray right-side block, full-height opaque right-rail column, high-frequency grain, sandy texture, paper material cues, or Paper Architecture resemblance.
- No rough assembly until this packet receives explicit human `keep`.

## Reads

- `ambient_effects_plan_read`: `pass_packet_local_layer_created`
- `ambient_effect_lane_decision_read`: `pass_mixed_minimal_terminal_ramp_micro_life`
- `source_plate_matte_registration_read`: `pass_fixed_1920x1080_coordinate_space_required_before_rough`
- `foreground_occlusion_read`: `pass_synthetic_rain_masked_off_indoor_people_and_mullions`
- `effect_layer_source_safety_read`: `pass_preserve_candidate_l_aircraft_terminal_ramp_geometry`
- `deterministic_ambient_read`: `pass_seeded_parameters_declared_for_rough_builder`
- `additive_effect_integration_read`: `pass_successor_layers_must_preserve_kept_plate_cue_map_script_locked_captions_and_prior_repairs`
- `debug_overlay_absence_read`: `pass_required_for_viewer_facing_rough`
- `ambient_effect_browser_sample_read`: `pass_browser_sample_screenshot_recorded`
- `ambient_animation_change_read`: `pass_screenshot_hash_changed_over_1_2s`
- `range_scrub_effect_review_read`: `pass_scrub_to_0s_120s_300s_820s_updates_rain_runner_state_and_occlusion_masks`
- `ambient_review_html_read`: `pass_viewer_facing_review_page_implements_effect_layers`
- `glass_rain_runner_read`: `pass_source_matched_running_droplets_on_terminal_glass_viewport_visibility_repaired_and_tone_preserved`
- `glass_runner_visibility_read`: `pass_viewport_delta_qa_visible_after_retry`
- `glass_runner_visibility_regression_repair_read`: `pass_prior_canvas_pixel_only_qa_replaced_with_viewport_delta_qa`
- `glass_runner_motion_salience_read`: `pass_speed_18_to_52px_per_second_length_42_to_132px_alpha_0_20_to_0_44`
- `glass_runner_source_transform_registration_read`: `pass_glass_canvas_uses_source_plate_drift_scale_transform`
- `glass_runner_tone_match_read`: `pass_muted_blue_gray_dark_refractive_palette_not_white`
- `glass_runner_overwhite_repair_read`: `pass_no_return_to_white_cream_overlay`
- `glass_runner_alpha_read`: `pass_runner_alpha_0_20_to_0_44_pin_bead_0_055_to_0_15`
- `glass_runner_scale_read`: `pass_1_to_4px_bead_heads_and_42_to_132px_vertical_tails_at_source_scale`
- `glass_runner_motion_read`: `pass_seeded_audio_time_positions_change_on_scrub_without_whole_overlay_scroll`
- `glass_runner_density_read`: `pass_density_tightened_to_112_runners_168_pin_beads_for_human_visibility`
- `glass_runner_pixel_read`: `pass_viewport_on_off_delta_max_74_pixels_delta_ge_8_6077`
- `glass_runner_rgb_read`: `pass_weighted_rgb_approximately_73_96_104_blue_gray_dark_not_white`
- `glass_runner_viewport_delta_read`: `pass_visible_layer_on_off_delta_recorded_at_120s`
- `glass_runner_canvas_motion_delta_read`: `pass_canvas_motion_delta_recorded_between_120s_and_121_5s`
- `indoor_people_occlusion_mask_read`: `pass_4_soft_polygon_masks_zero_synthetic_rain_alpha_at_0s_120s_300s_820s`
- `glass_runner_foreground_occlusion_read`: `pass_destination_out_mask_applied_after_runner_draw_only_to_synthetic_layer`
- `mullion_occlusion_mask_read`: `pass_5_soft_vertical_mullion_masks_zero_synthetic_rain_alpha_at_0s_120s_300s_820s`
- `occlusion_mask_count_read`: `pass_9_packet_local_masks_in_1920x1080_source_space`
- `exterior_glass_rain_preservation_read`: `pass_rain_pixels_remain_in_unmasked_glass_regions_at_0s_120s_300s_820s`
- `ramp_worker_mask_read`: `pass_not_masked_outside_worker_and_exterior_scene_remain_behind_glass_rain`
- `glass_runner_tacoma_copy_read`: `pass_tacoma_used_for_seeded_canvas_precedent_only_not_visual_model`
- `glass_runner_bubble_artifact_read`: `pass_no_bubble_shading_or_macro_windshield_drop_language`
- `rain_glass_reflection_read`: `pass_existing_scene_reflection_shimmer_only`
- `ramp_practical_light_read`: `pass_restrained_existing_light_micro_life_only`
- `aircraft_surface_light_read`: `pass_existing_nose_engine_contour_light_drift_only`
- `terminal_glass_parallax_read`: `pass_reflection_parallax_only_no_independent_mullion_slide_without_matte`
- `public_scene_motion_read`: `pass_distant_low_opacity_depth_motion_only_no_new_identity`
- `right_rail_safe_space_read`: `pass_preserve_candidate_l_low_detail_scene_integrated_right_side`
- `gray_block_repair_preservation_read`: `pass_no_solid_gray_right_side_block`
- `human_presence_read`: `pass_preserve_anonymous_public_scene_presence_without_new_portraits`
- `no_recognizable_faces_read`: `pass_no_face_forward_or_identifiable_human_effects`
- `generated_text_logo_read`: `pass_no_text_or_logo_effects`
- `no_crash_spectacle_read`: `pass_no_crash_fire_wreckage_or_impact_elements`
- `foreground_admin_prop_read`: `pass_no_admin_anchor_added_by_effect_layer`
- `rail_panel_palette_read`: `pass_source_integrated_blue_gray_rain_glass_warm_practical_palette_planned`
- `source_integrated_panel_color_read`: `pass_no_challenger_navy_default`
- `full_frame_dark_overlay_read`: `pass_blocked_prefer_localized_rail_readability`
- `localized_readability_treatment_read`: `pass_active_panel_and_caption_softener_only`
- `right_rail_opacity_balance_read`: `pass_no_full_height_opaque_right_column_planned`
- `context_region_source_visibility_read`: `pass_context_region_keeps_source_image_visible`
- `caption_softener_scope_read`: `pass_lower_rail_caption_softener_only_while_captions_visible`
- `procedural_signal_overlay_read`: `pass_no_overlay`
- `ambient_line_artifact_read`: `pass_no_cyan_or_diagnostic_lines`
- `texture_noise_read`: `pass_no_added_grit_speckle_sandy_texture_or_paper_material`
- `waterfall_read`: `pass_no_waterfall_liquid_path_or_cyan_water_effect`
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

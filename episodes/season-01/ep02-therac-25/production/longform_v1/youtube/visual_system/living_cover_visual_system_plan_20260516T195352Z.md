# Therac-25 Living Cover Visual System Plan

- Episode ID: `therac-25`
- Phase gate: `visual_system_gate`
- Status: `review_ready`
- Human disposition: `defer`
- Living Cover system version: `living_cover_system_v1`
- Rail preset: `fixed_16x9_right_rail_v1`
- Captioning process: `living_cover_captioning_process_v1`
- Caption required: `true`
- Caption output model: `dual_visible_rail_and_youtube_vtt_sidecar`
- Source-art lane: `cascade-ink-lit-photoreal-v1`
- Override status: `none`

## Source-Art Carrier

- Carrier type: `generated_raster_source_art`
- Source-art manifest: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/source_art/therac_living_cover_accuracy_cue_repair_imagegen_source_art_20260516T195352Z/source_art_manifest.json`
- Selected variant: `variant_h_control_room_active_terminal`
- Source path: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/source_art/therac_living_cover_accuracy_cue_repair_imagegen_source_art_20260516T195352Z/assets/source_art/variant_h_control_room_active_terminal_1920x1080.png`
- Source SHA-256: `cf08a25f31ea122daf9996827a56b28cc6692cebd83b2bebe5e48fa78cc0365e`
- Dimensions: `1920x1080`
- Human disposition: `defer`

## Historical Direction

The active lane is photoreal/source-preserving, not Paper Architecture. This successor repairs the operator screen and script alignment: the console terminal is active with no-readable period field rows, and the operator is female-presenting or anonymous enough not to contradict the locked script.

## Living Cover Cue Map

- Cue map: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/visual_system/living_cover_cue_map_20260516T195352Z.json`
- Cue map SHA-256: `877505e6bc59421fbf07221377948b3928a4c419916f3d9aca2bc1ed7d43c51f`
- Cue count: `11`
- Cue policy: internal production artifact only; no standalone visible cue panel/card/label/node list; source-safe behavior may affect approved rail/caption/chapter/end-screen layers only.

## Generation Provenance

- Tool: `codex_builtin_image_gen`
- Mode: `text_to_image`
- Source generation: `/Users/mike/.codex/generated_images/019e2dd2-7396-77b1-85e7-5789109f01ef/ig_0795620be4cb8c94016a08c926efe08195be01e45a7f9556f6.png`
- Source generation SHA-256: `60e18c50fcd3446512bcfa814e10772cde858449a1b0ac171a8db99ef1271712`
- Prompt path: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/source_art/therac_living_cover_accuracy_cue_repair_imagegen_source_art_20260516T195352Z/assets/prompts/variant_h_control_room_active_terminal_prompt.txt`
- Prompt SHA-256: `a4470cdc09466408caca54b9e7ed412a3e62da17a8607fb3615d02320480e847`
- Local rendered backplate: `pass_not_used`
- Local operations after ImageGen: `copy_original`, `resize_to_1920x1080`, `resize_preview_only`, `manifest_qa`

## Visual Reads

- `source_art_carrier_read`: `pass_generated_raster_source_art`
- `operator_gender_script_alignment_read`: `pass`
- `operator_screen_historical_accuracy_read`: `pass_active_period_terminal_status_fields`
- `screen_not_black_read`: `pass`
- `period_terminal_read`: `pass_dec_vt100_pdp11_style_crt`
- `screen_text_legibility_read`: `pass_no_readable_text_numbers_or_codes`
- `living_cover_cue_map_read`: `pass`
- `chapter_cue_coverage_read`: `pass_all_major_chapters_have_source_safe_cues`
- `typography_cue_read`: `pass_key_phrase_typography_present`
- `effect_map_cue_read`: `pass_4_to_8_effect_map_moments`
- `source_safe_motion_read`: `pass_opacity_transform_rail_panel_only_no_source_art_diagnostic_marks`
- `cue_no_diagnostic_overlay_read`: `pass_no_cyan_lines_connector_paths_or_generated_ui_over_source_art`
- `cue_map_internal_artifact_read`: `pass_internal_only_not_rendered`
- `visible_cue_overlay_read`: `pass_no_visible_cue_panel_card_label_or_node_list`
- `right_rail_safe_space_read`: `pass_selected_variant_h_strong_dark_right_side`
- `rail_panel_palette_read`: `pass_source_integrated_warm_charcoal_sampled_from_therac_control_room_palette`
- `source_integrated_panel_color_read`: `pass_no_challenger_night_sky_navy_on_therac_photoreal_proof`
- `procedural_signal_overlay_read`: `pass_no_canvas_svg_signal_overlay_on_photoreal_backplate`
- `ambient_line_artifact_read`: `pass_not_allowed_for_photoreal_source_preserving_proof`

## Review Question

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.

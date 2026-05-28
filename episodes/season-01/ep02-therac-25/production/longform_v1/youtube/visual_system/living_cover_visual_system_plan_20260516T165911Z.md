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
- Source-art manifest: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/source_art/therac_living_cover_historical_imagegen_source_art_20260516T165911Z/source_art_manifest.json`
- Selected variant: `variant_f_period_operator_console`
- Source path: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/source_art/therac_living_cover_historical_imagegen_source_art_20260516T165911Z/assets/source_art/variant_f_period_operator_console_1920x1080.png`
- Source SHA-256: `7c2a30c928e2a0fa49499080fed06efc1999c19f2747efad5af5c81520fe1702`
- Dimensions: `1920x1080`
- Human disposition: `defer`

## Historical Direction

The active lane is photoreal/source-preserving, not Paper Architecture. The image is anchored on web archival Therac references and linac motion/workflow footage: patient alone in the shielded treatment room, operator outside at a period CRT/analog console, and a blocky Therac-era linear accelerator rather than a contemporary glass-suite machine.

## Generation Provenance

- Tool: `codex_builtin_image_gen`
- Mode: `text_to_image`
- Source generation: `/Users/mike/.codex/generated_images/019e2dd2-7396-77b1-85e7-5789109f01ef/ig_0fa395dc990c94ec016a08a13d5dfc8196a06a19e535a3a80e.png`
- Source generation SHA-256: `828eb4957e6fec879c2f9111656dbaf1d846e83cd15dcf971d4fc243086c4290`
- Prompt path: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/source_art/therac_living_cover_historical_imagegen_source_art_20260516T165911Z/assets/prompts/variant_f_period_operator_console_prompt.txt`
- Prompt SHA-256: `10b3f331e2bc7f71d6bd2da611660a981f50650e7c38df485df3b1e822780401`
- Local rendered backplate: `pass_not_used`
- Local operations after ImageGen: `copy_original`, `resize_to_1920x1080`, `resize_preview_only`, `manifest_qa`

## Visual Reads

- `source_art_carrier_read`: `pass_generated_raster_source_art`
- `imagegen_skill_read`: `pass`
- `source_art_generation_tool_read`: `pass_codex_builtin_image_gen`
- `local_rendered_backplate_read`: `pass_not_used`
- `source_art_workspace_copy_read`: `pass`
- `historical_accuracy_reference_read`: `pass`
- `operator_outside_room_read`: `pass`
- `period_console_crt_read`: `pass`
- `blocky_therac_era_machine_read`: `pass`
- `right_rail_safe_space_read`: `pass_selected_variant_f_strong_dark_right_side`
- `rail_panel_palette_read`: `pass_source_integrated_warm_charcoal_sampled_from_therac_control_room_palette`
- `source_integrated_panel_color_read`: `pass_no_challenger_night_sky_navy_on_therac_photoreal_proof`
- `texture_noise_read`: `pass_photoreal_film_grain_not_paper_texture`
- `paper_architecture_absence_read`: `pass`
- `generated_text_logo_read`: `pass_no_readable_generated_text_or_logos_visible`
- `procedural_signal_overlay_read`: `pass_no_canvas_svg_signal_overlay_on_photoreal_backplate`
- `ambient_line_artifact_read`: `pass_not_allowed_for_photoreal_source_preserving_proof`
- `harm_imagery_read`: `pass_patient_present_but_calm_no_gore_burns_or_distress`

## Captioning Contract

Caption text must come from the locked script only. ASR timing can be used only for timing alignment after audio QA.

## Review Question

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.

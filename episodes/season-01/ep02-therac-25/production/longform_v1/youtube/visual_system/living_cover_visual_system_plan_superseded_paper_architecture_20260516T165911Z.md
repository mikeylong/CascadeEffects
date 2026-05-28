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
- Override status: `none`

## Source-Art Carrier

- Carrier type: `generated_raster_source_art`
- Source-art manifest: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/source_art/therac_living_cover_source_art_20260516T000139Z/source_art_manifest.json`
- Source path: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/source_art/therac_living_cover_source_art_20260516T000139Z/assets/source_art/therac_living_cover_source_art_1920x1080.png`
- Source SHA-256: `f1e9c1928b569362986f03351ec7c5b0a67287ecec68d3a790064b6a76b667b3`
- Dimensions: `1920x1080`
- Human disposition: `defer`

## Generation Provenance

- Tool: `codex_builtin_image_gen`
- Model: `unknown_builtin_image_gen_model`
- Model confidence: `inferred_from_path`
- Mode: `text_to_image`
- Prompt path: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/source_art/therac_living_cover_source_art_20260516T000139Z/assets/prompts/therac_living_cover_source_art_prompt.txt`
- Prompt SHA-256: `3e12bd3aa6f9b75d12c3a46a6f54e93349c18fee4dd488bc450f177125306940`

## Visual Reads

- `source_art_carrier_read`: `pass_generated_raster_source_art`
- `generation_tool_provenance_read`: `pass_recorded_builtin_imagegen_path_prompt_hash_and_packet_asset_hash`
- `right_rail_safe_space_read`: `pass_large_clean_right_side_negative_space_available`
- `texture_noise_read`: `pass_subtle_paper_fiber_only_by_visual_inspection_pending_human_keep`
- `waterfall_read`: `pass_dry_cyan_signal_trace_no_water_read`
- `generated_text_logo_read`: `pass_no_readable_generated_text_or_logos_visible`
- `harm_imagery_read`: `pass_no_patient_no_gore_no_burns`

## Captioning Contract

Caption text must come from the locked script only. ASR/VTT/SRT timing can be used only for timing alignment after audio QA.

## Review Question

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.

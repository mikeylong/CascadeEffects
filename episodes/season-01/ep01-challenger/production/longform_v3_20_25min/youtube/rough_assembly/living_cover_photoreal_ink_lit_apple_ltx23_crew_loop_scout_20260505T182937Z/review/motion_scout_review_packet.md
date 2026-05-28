# Challenger Living Cover Smooth Crew Loop Scout Review

Packet: `living_cover_photoreal_ink_lit_apple_ltx23_crew_loop_scout_20260505T182937Z`
Gate: `rough_assembly_loop_motion_scout_gate`
Human disposition: `reject`

## What Changed

- The previous Apple LTX scout is recorded as `tighten`, not `keep`.
- This packet narrows the task to a reusable living-cover loop: exactly seven back-view astronauts, subtle detectable motion, smooth repeat.
- Raw LTX full-frame clips are included for diagnosis; loop-normalized review clips composite only the crew zone over the static kept Variant C background.

## Contact Sheets

- Raw full frame: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_loop_scout_20260505T182937Z/qa/contact_sheets/apple_ltx23_crew_loop_raw_full_frame_contact_sheet.jpg`
- Loop-normalized full frame: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_loop_scout_20260505T182937Z/qa/contact_sheets/apple_ltx23_crew_loop_normalized_full_frame_contact_sheet.jpg`
- Loop-normalized crew crop: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_loop_scout_20260505T182937Z/qa/contact_sheets/apple_ltx23_crew_loop_normalized_crew_crop_contact_sheet.jpg`
- Loop seam: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_loop_scout_20260505T182937Z/qa/contact_sheets/apple_ltx23_crew_loop_seam_contact_sheet.jpg`
- 3-loop preview seam: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_loop_scout_20260505T182937Z/qa/contact_sheets/apple_ltx23_crew_loop_3x_preview_seam_contact_sheet.jpg`

## Candidates

| Candidate | Seed | Prompt Variant | 12s Loop Clip | 3x Preview Clip |
|---|---:|---|---|---|
| A | `314159` | `smallest_detectable_loop_a` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_loop_scout_20260505T182937Z/clips/loop_normalized/variant_a_crew_loop_seed314159_12s.mp4` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_loop_scout_20260505T182937Z/clips/loop_preview_3x/variant_a_crew_loop_seed314159_3x_preview.mp4` |
| B | `271828` | `recommended_subtle_sway_head_turn_b` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_loop_scout_20260505T182937Z/clips/loop_normalized/variant_b_crew_loop_seed271828_12s.mp4` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_loop_scout_20260505T182937Z/clips/loop_preview_3x/variant_b_crew_loop_seed271828_3x_preview.mp4` |
| C | `161803` | `upper_detectability_restrained_c` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_loop_scout_20260505T182937Z/clips/loop_normalized/variant_c_crew_loop_seed161803_12s.mp4` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_loop_scout_20260505T182937Z/clips/loop_preview_3x/variant_c_crew_loop_seed161803_3x_preview.mp4` |

## Reads

| Read | Result |
|---|---:|
| `source_art_hash_read` | `pass` |
| `apple_ltx23_runtime_read` | `pass` |
| `candidate_count_read` | `pass_three_candidates` |
| `raw_clip_audio_read` | `pass_no_audio` |
| `loop_clip_audio_read` | `pass_no_audio` |
| `loop_duration_read` | `pass_12s` |
| `preview_3loop_duration_read` | `pass_36s` |
| `contact_sheet_read` | `pass` |
| `forbidden_media_copy_read` | `pass_no_audio_caption_transcript_sidecars` |
| `full_runtime_html_proof_read` | `pass_not_created` |
| `full_runtime_mp4_read` | `pass_not_created` |
| `final_assembly_read` | `pass_not_created` |
| `crew_loop_read` | `defer_pending_human_review` |
| `loop_seam_read` | `defer_pending_human_review` |
| `motion_subtlety_read` | `defer_pending_human_review` |
| `motion_detectability_read` | `defer_pending_human_review` |
| `crew_count_read` | `defer_pending_human_review` |
| `crew_motion_authenticity_read` | `defer_pending_human_review` |
| `uncanny_motion_read` | `defer_pending_human_review` |
| `identity_logo_text_read` | `defer_pending_human_review` |
| `background_stability_read` | `defer_pending_human_review` |
| `pad_hardware_stability_read` | `defer_pending_human_review` |
| `shuttle_anatomy_stability_read` | `defer_pending_human_review` |
| `right_rail_safe_space_read` | `defer_pending_human_review` |
| `long_runtime_carrier_read` | `defer_pending_human_review` |

## Human Review Options

Reply with exactly one response: `keep A`, `keep B`, `keep C`, `tighten`, or `reject`.

If one candidate is kept, the next artifact should be a full-runtime HTML proof that loops the selected crew-motion carrier behind the existing staged right rail. No full-runtime MP4, final assembly, Shorts, publish readiness, or YouTube action is authorized by this scout packet.

## Human Reject Record

Disposition recorded: `reject`

Disposition UTC: `2026-05-05T20:02:50Z`

Reviewer text: `reject`

No A/B/C loop candidate is selected. This packet cannot advance to full-runtime HTML proof, MP4 render, final assembly, Shorts, publish readiness, or YouTube action.

## LTX Prompt/Config Successor

This rejected packet remains rejected. The successor is a fresh Apple LTX prompt/config scout, not a revival of any rejected candidate.

Successor packet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z`

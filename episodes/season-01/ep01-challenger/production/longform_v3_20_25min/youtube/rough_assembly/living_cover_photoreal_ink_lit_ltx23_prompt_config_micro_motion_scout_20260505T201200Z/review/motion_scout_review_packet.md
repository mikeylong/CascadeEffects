# Challenger Living Cover LTX 2.3 Prompt/Config Micro-Motion Scout Review

Packet: `living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z`
Gate: `rough_assembly_ltx_prompt_config_micro_motion_scout_gate`
Human disposition: `defer`

## What Changed

- The rejected smooth-loop packet remains rejected.
- This is a fresh LTX prompt/config scout, not in-place deformation or sprite animation.
- LTX runs only on the crew crop; the review full-frame clips composite that generated crop into static kept Variant C context.
- The loop is built from a 6s generated half-cycle plus reverse playback.

## Candidates

| Candidate | Seed | CFG | STG | 12s Composited Loop | 36s 3-Loop Preview |
|---|---:|---:|---:|---|---|
| A | `314159` | `1.2` | `0.25` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z/clips/loop_composited_full_frame/variant_a_ltx_prompt_config_full_frame_loop_12s.mp4` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z/clips/loop_preview_3x/variant_a_ltx_prompt_config_full_frame_3x_preview.mp4` |
| B | `271828` | `1.5` | `0.4` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z/clips/loop_composited_full_frame/variant_b_ltx_prompt_config_full_frame_loop_12s.mp4` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z/clips/loop_preview_3x/variant_b_ltx_prompt_config_full_frame_3x_preview.mp4` |
| C | `161803` | `1.8` | `0.55` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z/clips/loop_composited_full_frame/variant_c_ltx_prompt_config_full_frame_loop_12s.mp4` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z/clips/loop_preview_3x/variant_c_ltx_prompt_config_full_frame_3x_preview.mp4` |

## Contact Sheets

- Raw crop: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z/qa/contact_sheets/ltx23_prompt_config_raw_crop_contact_sheet.jpg`
- Composited full frame: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z/qa/contact_sheets/ltx23_prompt_config_composited_full_frame_contact_sheet.jpg`
- Crew crop: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z/qa/contact_sheets/ltx23_prompt_config_crew_crop_contact_sheet.jpg`
- Loop seam: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z/qa/contact_sheets/ltx23_prompt_config_loop_seam_contact_sheet.jpg`
- 3-loop seam: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z/qa/contact_sheets/ltx23_prompt_config_3loop_seam_contact_sheet.jpg`

## Reads

| Read | Result |
|---|---:|
| `source_art_hash_read` | `pass` |
| `ltx_runtime_read` | `pass` |
| `candidate_count_read` | `pass_three_candidates` |
| `raw_crop_audio_read` | `pass_no_audio` |
| `loop_duration_read` | `pass_12s` |
| `preview_3loop_duration_read` | `pass_36s` |
| `contact_sheet_read` | `pass` |
| `forbidden_media_copy_read` | `pass_no_audio_caption_transcript_html_mov_sidecars` |
| `full_runtime_html_proof_read` | `pass_not_created` |
| `full_runtime_mp4_read` | `pass_not_created` |
| `final_assembly_read` | `pass_not_created` |
| `ltx_prompt_config_read` | `defer_pending_human_review` |
| `crew_loop_read` | `defer_pending_human_review` |
| `loop_seam_read` | `defer_pending_human_review` |
| `motion_subtlety_read` | `defer_pending_human_review` |
| `motion_detectability_read` | `defer_pending_human_review` |
| `non_synchronized_motion_read` | `defer_pending_human_review` |
| `no_noise_effects_read` | `defer_pending_human_review` |
| `crew_count_read` | `defer_pending_human_review` |
| `background_stability_read` | `defer_pending_human_review` |
| `uncanny_motion_read` | `defer_pending_human_review` |
| `long_runtime_carrier_read` | `defer_pending_human_review` |

## Human Review Options

Reply with exactly one response: `keep A`, `keep B`, `keep C`, `tighten`, or `reject`.

If one candidate is kept, the next artifact should be a full-runtime HTML proof that loops the selected LTX prompt/config carrier behind the existing staged right rail. No full-runtime MP4, final assembly, Shorts, publish readiness, or YouTube action is authorized by this scout packet.

## Chroma-Key Successor

Human disposition: `tighten`.

Reason: the crop-isolated LTX approach lets the model re-solve launch-pad/background pixels and creates gesture-scale artifacts, including hand/arm drift. The successor separates the static shuttle plate from a keyed crew-only LTX motion layer.

Successor packet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z`

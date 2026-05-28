# Challenger Living Cover Variable-Duration Terminal Walk Scout Review

Packet: `living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z`
Gate: `rough_assembly_ltx_variable_duration_terminal_walk_scout_gate`
Human disposition: `defer`

## What Changed

- Current 12s terminal-walk scout is recorded as `tighten`.
- The fixed 12s ending rule is released; each candidate carries its own duration and computed full-episode terminal start time.
- LTX still runs only on the green-screen seven-astronaut crew layer. The shuttle, pad, sky, and right-rail safe area remain static from the no-crew plate.
- The diagnostic matrix tests `4s`, `6s`, `8s`, and `12s` true-duration generations across one-stage q8 and two-stage distilled-LoRA lanes.

## Presented Candidates

| Candidate | Source Cell | Duration | Pipeline | Future Terminal Start | Walk Composite | Static-Then-Walk Review |
|---|---|---:|---|---:|---|---|
| A | `one_stage_q8_6s` | `6s` | `one_stage_q8` | `21:23.131` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/clips/composited_full_frame/one_stage_q8_6s_composited_full_frame_6s.mp4` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/clips/transition_review/one_stage_q8_6s_static_then_terminal_walk_review_8s.mp4` |
| B | `one_stage_q8_8s` | `8s` | `one_stage_q8` | `21:21.131` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/clips/composited_full_frame/one_stage_q8_8s_composited_full_frame_8s.mp4` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/clips/transition_review/one_stage_q8_8s_static_then_terminal_walk_review_10s.mp4` |
| C | `two_stage_distilled_lora_6s` | `6s` | `two_stage_distilled_lora` | `21:23.131` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/clips/composited_full_frame/two_stage_distilled_lora_6s_composited_full_frame_6s.mp4` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/clips/transition_review/two_stage_distilled_lora_6s_static_then_terminal_walk_review_8s.mp4` |

## Contact Sheets

- Presented A/B/C: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/qa/contact_sheets/variable_duration_presented_abc_contact_sheet.jpg`
- Full-frame matrix: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/qa/contact_sheets/variable_duration_pipeline_matrix_full_frame_contact_sheet.jpg`
- Crew-crop matrix: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/qa/contact_sheets/variable_duration_pipeline_matrix_crew_crop_contact_sheet.jpg`
- Alpha matte QA: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/qa/contact_sheets/variable_duration_alpha_matte_contact_sheet.jpg`
- Still-to-walk transition: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/qa/contact_sheets/variable_duration_still_to_walk_transition_contact_sheet.jpg`
- Non-presented diagnostics: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/qa/contact_sheets/variable_duration_rejected_diagnostic_cells_contact_sheet.jpg`

## Reads

| Read | Result |
|---|---:|
| `source_art_hash_read` | `pass` |
| `ltx_runtime_read` | `pass` |
| `duration_matrix_read` | `pass_4s_6s_8s_12s` |
| `pipeline_matrix_read` | `pass_one_stage_and_two_stage` |
| `true_duration_no_stretch_read` | `pass` |
| `raw_chroma_audio_read` | `pass_no_audio` |
| `clip_duration_read` | `pass_true_duration` |
| `contact_sheet_read` | `pass` |
| `forbidden_media_copy_read` | `pass_no_audio_caption_transcript_html_mov_sidecars` |
| `full_runtime_html_proof_read` | `pass_not_created` |
| `full_runtime_mp4_read` | `pass_not_created` |
| `final_assembly_read` | `pass_not_created` |
| `duration_fit_read` | `defer_pending_human_review` |
| `natural_gait_read` | `defer_pending_human_review` |
| `squat_crouch_read` | `defer_pending_human_review` |
| `walk_speed_read` | `defer_pending_human_review` |
| `two_stage_distilled_read` | `tighten_4s_6s_8s_completed_12s_failed_at_refinement` |
| `crew_count_read` | `defer_pending_human_review` |
| `hand_waving_read` | `defer_pending_human_review` |
| `non_synchronized_stride_read` | `defer_pending_human_review` |
| `matte_edge_read` | `defer_pending_human_review` |
| `background_stability_read` | `defer_pending_human_review` |
| `right_rail_safe_space_read` | `defer_pending_human_review` |
| `long_runtime_terminal_carrier_read` | `defer_pending_human_review` |
| `diagnostic_cell_completion_read` | `tighten_7_of_8_generated_two_stage_12s_failed` |
| `duration_pipeline_matrix_read` | `tighten_full_matrix_attempted_two_stage_12s_failed` |

## Human Review Options

Reply with exactly one response: `keep A`, `keep B`, `keep C`, `tighten`, or `reject`.

If one candidate is kept, the next artifact should be a full-runtime HTML proof with static crew until that candidate's computed terminal start time, then the selected terminal-walk carrier behind the existing staged right rail. No full-runtime MP4, final assembly, Shorts, publish readiness, or YouTube action is authorized by this scout packet.

## Diagnostic Failure

- `two_stage_distilled_lora_12s` failed after completing the guided stage-one denoising and before stage-two output.
- The packet remains review-ready because the failure is part of the duration/pipeline test, and the presented A/B/C candidates are selected only from completed true-duration cells.

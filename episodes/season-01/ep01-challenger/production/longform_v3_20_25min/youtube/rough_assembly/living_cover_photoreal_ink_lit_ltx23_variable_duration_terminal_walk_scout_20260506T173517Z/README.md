# Challenger Living Cover Variable-Duration Terminal Walk Scout

Packet: `living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z`
Status: `review_ready_pending_human_variable_duration_terminal_walk_keep`
Human disposition: `defer`

This packet records the fixed-12s terminal-walk scout as `tighten`. Variant A was the best prior direction, but the pre-step squat/crouch and slow stretched gait block keep. This successor tests true-duration LTX generations at `4s`, `6s`, `8s`, and `12s` across one-stage q8 and two-stage distilled-LoRA lanes.

## Presented A/B/C

- A: `one_stage_q8_6s`, 6s, One-stage q8, seed `510102`, terminal start `21:23.131`
- B: `one_stage_q8_8s`, 8s, One-stage q8, seed `510136`, terminal start `21:21.131`
- C: `two_stage_distilled_lora_6s`, 6s, Two-stage distilled-LoRA, seed `511102`, terminal start `21:23.131`

## Diagnostic Matrix

- Durations: `4s`, `6s`, `8s`, `12s`
- Pipelines: `one_stage_q8`, `two_stage_distilled_lora`
- No clip is stretched or retimed to meet a target duration.
- Future full-runtime walk start is computed as `00:21:29.131 - selected_candidate_duration`.

## Review Surfaces

- Presented A/B/C contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/qa/contact_sheets/variable_duration_presented_abc_contact_sheet.jpg`
- Full-frame matrix: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/qa/contact_sheets/variable_duration_pipeline_matrix_full_frame_contact_sheet.jpg`
- Crew-crop matrix: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/qa/contact_sheets/variable_duration_pipeline_matrix_crew_crop_contact_sheet.jpg`
- Alpha/matte QA: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/qa/contact_sheets/variable_duration_alpha_matte_contact_sheet.jpg`
- Still-to-walk transition: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/qa/contact_sheets/variable_duration_still_to_walk_transition_contact_sheet.jpg`
- Non-presented diagnostics: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z/qa/contact_sheets/variable_duration_rejected_diagnostic_cells_contact_sheet.jpg`

No full-runtime HTML proof, full-runtime MP4, final assembly, Shorts work, publish readiness, or YouTube action is authorized from this packet.

## Diagnostic Failure

- `two_stage_distilled_lora_12s` failed after completing the guided stage-one denoising and before stage-two output.
- The packet remains review-ready because the failure is part of the duration/pipeline test, and the presented A/B/C candidates are selected only from completed true-duration cells.

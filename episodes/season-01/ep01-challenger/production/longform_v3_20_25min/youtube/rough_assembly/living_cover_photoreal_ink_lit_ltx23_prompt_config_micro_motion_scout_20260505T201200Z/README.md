# Challenger Living Cover LTX 2.3 Prompt/Config Micro-Motion Scout

Packet: `living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z`
Status: `review_ready_pending_human_ltx_prompt_config_micro_motion_keep`
Human disposition: `defer`

This packet is a fresh Apple LTX 2.3 prompt/config scout after the rejected smooth-loop scout. It keeps LTX as the motion generator, isolates generation to the crew crop, removes atmosphere/effects language, and builds a loop with a forward/reverse ping-pong.

## Candidates

- A: seed `314159`, cfg `1.2`, stg `0.25`, `almost_still_tiny_posture_settling_a`
- B: seed `271828`, cfg `1.5`, stg `0.4`, `subtle_detectable_independent_posture_settling_b`
- C: seed `161803`, cfg `1.8`, stg `0.55`, `upper_subtle_no_visible_action_c`

## Review Surfaces

- Raw crop contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z/qa/contact_sheets/ltx23_prompt_config_raw_crop_contact_sheet.jpg`
- Composited full-frame contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z/qa/contact_sheets/ltx23_prompt_config_composited_full_frame_contact_sheet.jpg`
- Crew crop contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z/qa/contact_sheets/ltx23_prompt_config_crew_crop_contact_sheet.jpg`
- Loop seam contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z/qa/contact_sheets/ltx23_prompt_config_loop_seam_contact_sheet.jpg`
- 3-loop seam contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z/qa/contact_sheets/ltx23_prompt_config_3loop_seam_contact_sheet.jpg`
- Composited loops: `clips/loop_composited_full_frame/`
- 3-loop previews: `clips/loop_preview_3x/`

No full-runtime HTML proof, full-runtime MP4, final assembly, Shorts work, publish readiness, or YouTube action is authorized from this packet.

## Chroma-Key Successor

Human disposition: `tighten`.

Reason: the crop-isolated LTX approach lets the model re-solve launch-pad/background pixels and creates gesture-scale artifacts, including hand/arm drift. The successor separates the static shuttle plate from a keyed crew-only LTX motion layer.

Successor packet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z`

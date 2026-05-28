# Challenger Living Cover LTX 2.3 Terminal Walk Scout

Packet: `living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z`
Status: `review_ready_pending_human_terminal_walk_keep`
Human disposition: `defer`

This packet records the prior chroma-key micro-motion scout as `tighten` because A/B/C read too still. The new review artifact tests a terminal narrative action: the crew is static until the final 12 seconds of the episode, then all seven astronauts begin walking away from camera toward the shuttle pad.

## Candidates

- A: seed `404101`, cfg `1.15`, stg `0.2`, `stable_prefix_restrained_first_step_a`
- B: seed `404203`, cfg `1.35`, stg `0.32`, `stable_prefix_clear_calm_walk_start_b`
- C: seed `404203`, cfg `1.35`, stg `0.32`, `stable_prefix_upper_readable_walk_start_c`

## Timing Contract

- Full approved audio: `00:21:29.131` / `1289.131247s`
- Terminal walk start: `00:21:17.131` / `1277.131247s`
- Terminal walk duration: `12s`
- Future full-runtime proof: static crew until the walk start, then play the selected terminal-walk carrier once.

## Review Surfaces

- Plate/source contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/qa/contact_sheets/terminal_walk_plate_and_source_contact_sheet.jpg`
- Raw chroma contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/qa/contact_sheets/terminal_walk_raw_chroma_crew_contact_sheet.jpg`
- Alpha matte contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/qa/contact_sheets/terminal_walk_alpha_matte_contact_sheet.jpg`
- Composited full-frame contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/qa/contact_sheets/terminal_walk_composited_full_frame_contact_sheet.jpg`
- Crew crop contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/qa/contact_sheets/terminal_walk_crew_crop_contact_sheet.jpg`
- Still-to-walk transition contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/qa/contact_sheets/terminal_walk_still_to_walk_transition_contact_sheet.jpg`
- Composited walk clips: `clips/composited_full_frame/`
- Static-then-walk review clips: `clips/transition_review/`

No full-runtime HTML proof, full-runtime MP4, final assembly, Shorts work, publish readiness, or YouTube action is authorized from this packet.

## Internal Iteration Notes

- Full 12s LTX generations are retained as diagnostic metadata but are not the presented keeper set: late frames introduced green-screen background drift and raised-arm gestures.
- The presented A/B/C set uses stable LTX-generated walking prefix frames, stretched once to the 12s terminal-walk duration.
- This is still an LTX-generated terminal-walk carrier; no sprite overlay, deterministic deformation, full-runtime HTML proof, or full-runtime MP4 was created.

## Variable-Duration Terminal Walk Successor

Human disposition: `tighten`.

Reason: Variant A was directionally best, but the crew squats/crouches before stepping and the stretched 12s walk is too slow. The successor drops the fixed 12s requirement and tests true-duration 4s, 6s, 8s, and 12s generations across one-stage and two-stage LTX lanes.

Successor packet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z`

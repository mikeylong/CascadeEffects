# Challenger Living Cover Terminal Walk Scout Review

Packet: `living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z`
Gate: `rough_assembly_ltx_terminal_walk_scout_gate`
Human disposition: `defer`

## What Changed

- Full 12s LTX generations were internally rejected as presentation candidates because the later frames drifted into background artifacts and raised-arm gestures.
- This presented set uses stable LTX-generated walking prefix frames stretched once to the 12s terminal-walk duration.
- The chroma-key micro-motion scout is recorded as `tighten`.
- The new motion concept is not a loop: static crew until `00:21:17.131`, then a one-time 12s walk toward the shuttle pad.
- LTX runs only on the green-screen crew layer; the shuttle, pad, sky, and right-rail safe area remain static from the no-crew plate.
- Candidate clips are review-only motion-scout artifacts, not full-runtime rough/final renders.

## Candidates

| Candidate | Seed | CFG | STG | 12s Walk Composite | 14s Static-Then-Walk Review |
|---|---:|---:|---:|---|---|
| A | `404101` | `1.15` | `0.2` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/clips/composited_full_frame/variant_a_stable_generated_walk_prefix_terminal_walk_composited_full_frame_12s.mp4` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/clips/transition_review/variant_a_stable_generated_walk_prefix_static_then_terminal_walk_review_14s.mp4` |
| B | `404203` | `1.35` | `0.32` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/clips/composited_full_frame/variant_b_stable_generated_walk_prefix_terminal_walk_composited_full_frame_12s.mp4` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/clips/transition_review/variant_b_stable_generated_walk_prefix_static_then_terminal_walk_review_14s.mp4` |
| C | `404203` | `1.35` | `0.32` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/clips/composited_full_frame/variant_c_stable_generated_walk_prefix_terminal_walk_composited_full_frame_12s.mp4` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/clips/transition_review/variant_c_stable_generated_walk_prefix_static_then_terminal_walk_review_14s.mp4` |

## Contact Sheets

- Plate/source: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/qa/contact_sheets/terminal_walk_plate_and_source_contact_sheet.jpg`
- Raw chroma crew: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/qa/contact_sheets/terminal_walk_raw_chroma_crew_contact_sheet.jpg`
- Alpha matte QA: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/qa/contact_sheets/terminal_walk_alpha_matte_contact_sheet.jpg`
- Composited full frame: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/qa/contact_sheets/terminal_walk_composited_full_frame_contact_sheet.jpg`
- Crew crop: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/qa/contact_sheets/terminal_walk_crew_crop_contact_sheet.jpg`
- Still-to-walk transition: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z/qa/contact_sheets/terminal_walk_still_to_walk_transition_contact_sheet.jpg`

## Reads

| Read | Result |
|---|---:|
| `source_art_hash_read` | `pass` |
| `ltx_runtime_read` | `pass` |
| `candidate_count_read` | `pass_three_candidates` |
| `raw_chroma_audio_read` | `pass_no_audio` |
| `terminal_walk_duration_read` | `pass_12s` |
| `transition_review_duration_read` | `pass_14s` |
| `contact_sheet_read` | `pass` |
| `forbidden_media_copy_read` | `pass_no_audio_caption_transcript_html_mov_sidecars` |
| `full_runtime_html_proof_read` | `pass_not_created` |
| `full_runtime_mp4_read` | `pass_not_created` |
| `final_assembly_read` | `pass_not_created` |
| `terminal_walk_read` | `defer_pending_human_review` |
| `walk_start_timing_read` | `defer_pending_human_review` |
| `still_to_walk_pop_read` | `defer_pending_human_review` |
| `crew_count_read` | `defer_pending_human_review` |
| `walking_motion_authenticity_read` | `defer_pending_human_review` |
| `non_synchronized_stride_read` | `defer_pending_human_review` |
| `hand_waving_read` | `defer_pending_human_review` |
| `identity_logo_text_read` | `defer_pending_human_review` |
| `matte_edge_read` | `defer_pending_human_review` |
| `background_stability_read` | `defer_pending_human_review` |
| `right_rail_safe_space_read` | `defer_pending_human_review` |
| `long_runtime_terminal_carrier_read` | `defer_pending_human_review` |

## Human Review Options

Reply with exactly one response: `keep A`, `keep B`, `keep C`, `tighten`, or `reject`.

If one candidate is kept, the next artifact should be a full-runtime HTML proof with static crew until the final 12 seconds, then the selected terminal-walk carrier behind the existing staged right rail. No full-runtime MP4, final assembly, Shorts, publish readiness, or YouTube action is authorized by this scout packet.

## Variable-Duration Terminal Walk Successor

Human disposition: `tighten`.

Reason: Variant A was directionally best, but the crew squats/crouches before stepping and the stretched 12s walk is too slow. The successor drops the fixed 12s requirement and tests true-duration 4s, 6s, 8s, and 12s generations across one-stage and two-stage LTX lanes.

Successor packet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z`

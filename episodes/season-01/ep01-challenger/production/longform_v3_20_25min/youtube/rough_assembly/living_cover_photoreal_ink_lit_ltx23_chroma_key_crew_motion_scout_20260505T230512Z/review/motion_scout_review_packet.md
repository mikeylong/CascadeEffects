# Challenger Living Cover LTX 2.3 Chroma-Key Crew Motion Scout Review

Packet: `living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z`
Gate: `rough_assembly_ltx_chroma_key_crew_motion_scout_gate`
Human disposition: `defer`

## What Changed

- Internal `iteration_01` failed because full generated clips drifted into walking and raised-arm gestures.
- Internal `iteration_02` failed because lower guidance collapsed the chroma layer into noise.
- The presented set uses stable prefix frames from `iteration_03`; no deformation, sprite animation, or clean-plate motion trick was used.
- The crop-isolated LTX prompt/config scout is recorded as `tighten`.
- The shuttle/pad scene is now a static aligned no-crew plate.
- LTX runs only on a green-screen crew layer, then the crew is keyed and composited over the plate.
- The loop is built from a 6s generated half-cycle plus reverse playback.

## Candidates

| Candidate | Seed | CFG | STG | 12s Composited Loop | 36s 3-Loop Preview |
|---|---:|---:|---:|---|---|
| A | `112358` | `0.85` | `0.08` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z/clips/loop_composited_full_frame/variant_a_iteration_03_stable_prefix_chroma_key_composited_full_frame_loop_12s.mp4` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z/clips/loop_preview_3x/variant_a_iteration_03_stable_prefix_chroma_key_composited_full_frame_3x_preview.mp4` |
| B | `112358` | `0.85` | `0.08` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z/clips/loop_composited_full_frame/variant_b_iteration_03_stable_prefix_chroma_key_composited_full_frame_loop_12s.mp4` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z/clips/loop_preview_3x/variant_b_iteration_03_stable_prefix_chroma_key_composited_full_frame_3x_preview.mp4` |
| C | `271828` | `0.95` | `0.1` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z/clips/loop_composited_full_frame/variant_c_iteration_03_stable_prefix_chroma_key_composited_full_frame_loop_12s.mp4` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z/clips/loop_preview_3x/variant_c_iteration_03_stable_prefix_chroma_key_composited_full_frame_3x_preview.mp4` |

## Contact Sheets

- Plate/source: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z/qa/contact_sheets/chroma_key_no_crew_plate_and_source_contact_sheet.jpg`
- Raw chroma crew: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z/qa/contact_sheets/chroma_key_raw_chroma_crew_contact_sheet.jpg`
- Alpha matte QA: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z/qa/contact_sheets/chroma_key_alpha_matte_contact_sheet.jpg`
- Composited full frame: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z/qa/contact_sheets/chroma_key_composited_full_frame_contact_sheet.jpg`
- Crew crop: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z/qa/contact_sheets/chroma_key_crew_crop_contact_sheet.jpg`
- Loop seam: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z/qa/contact_sheets/chroma_key_loop_seam_contact_sheet.jpg`
- 3-loop seam: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z/qa/contact_sheets/chroma_key_3loop_seam_contact_sheet.jpg`

## Reads

| Read | Result |
|---|---:|
| `source_art_hash_read` | `pass` |
| `ltx_runtime_read` | `pass` |
| `candidate_count_read` | `pass_three_candidates` |
| `raw_chroma_audio_read` | `pass_no_audio` |
| `loop_duration_read` | `pass_12s` |
| `preview_3loop_duration_read` | `pass_36s` |
| `contact_sheet_read` | `pass` |
| `forbidden_media_copy_read` | `pass_no_audio_caption_transcript_html_mov_sidecars` |
| `full_runtime_html_proof_read` | `pass_not_created` |
| `full_runtime_mp4_read` | `pass_not_created` |
| `final_assembly_read` | `pass_not_created` |
| `chroma_key_read` | `defer_pending_human_review` |
| `no_crew_plate_read` | `defer_pending_human_review` |
| `crew_loop_read` | `defer_pending_human_review` |
| `loop_seam_read` | `defer_pending_human_review` |
| `hand_waving_read` | `defer_pending_human_review` |
| `non_synchronized_motion_read` | `defer_pending_human_review` |
| `motion_subtlety_read` | `defer_pending_human_review` |
| `motion_detectability_read` | `defer_pending_human_review` |
| `crew_count_read` | `defer_pending_human_review` |
| `matte_edge_read` | `defer_pending_human_review` |
| `background_stability_read` | `defer_pending_human_review` |
| `identity_logo_text_read` | `defer_pending_human_review` |
| `uncanny_motion_read` | `defer_pending_human_review` |
| `right_rail_safe_space_read` | `defer_pending_human_review` |
| `long_runtime_carrier_read` | `defer_pending_human_review` |

## Human Review Options

Reply with exactly one response: `keep A`, `keep B`, `keep C`, `tighten`, or `reject`.

If one candidate is kept, the next artifact should be a full-runtime HTML proof that loops the selected chroma-key crew carrier behind the existing staged right rail. No full-runtime MP4, final assembly, Shorts, publish readiness, or YouTube action is authorized by this scout packet.

## Terminal-Walk Successor

Human disposition: `tighten`.

Reason: the chroma-key A/B/C micro-motion candidates are clean but read too still. The successor changes the concept to a one-time final-12-second walk toward the shuttle pad.

Successor packet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z`

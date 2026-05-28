# Challenger Living Cover Apple LTX 2.3 Crew Motion Scout Review

Packet: `living_cover_photoreal_ink_lit_apple_ltx23_crew_motion_scout_20260505T174422Z`
Gate: `rough_assembly_motion_scout_gate`
Human disposition: `defer`

## What Changed

- The sprite-overlay crew proof is recorded as `reject`.
- This packet uses Apple-native LTX 2.3 image-to-video from the kept Variant C full-frame still.
- A/B/C are short motion-scout clips only, not a rough proof or final render.

## Contact Sheets

- Full frame: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_motion_scout_20260505T174422Z/qa/contact_sheets/apple_ltx23_abc_full_frame_contact_sheet.jpg`
- Crew crop: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_motion_scout_20260505T174422Z/qa/contact_sheets/apple_ltx23_abc_crew_crop_contact_sheet.jpg`

## Candidates

| Candidate | Seed | Prompt Variant | Normalized Clip |
|---|---:|---|---|
| A | `314159` | `locked_micro_motion_a` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_motion_scout_20260505T174422Z/clips/normalized/variant_a_apple_ltx23_seed314159_normalized.mp4` |
| B | `271828` | `pad_light_air_shimmer_b` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_motion_scout_20260505T174422Z/clips/normalized/variant_b_apple_ltx23_seed271828_normalized.mp4` |
| C | `161803` | `restrained_weight_shift_c` | `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_motion_scout_20260505T174422Z/clips/normalized/variant_c_apple_ltx23_seed161803_normalized.mp4` |

## Reads

| Read | Result |
|---|---:|
| `source_art_hash_read` | `pass` |
| `apple_ltx23_runtime_read` | `pass` |
| `candidate_count_read` | `pass_three_candidates` |
| `raw_clip_audio_read` | `pass_no_audio` |
| `normalized_clip_audio_read` | `pass_no_audio` |
| `contact_sheet_read` | `pass` |
| `forbidden_media_copy_read` | `pass_no_audio_caption_transcript_sidecars` |
| `crew_liveliness_read` | `defer_pending_human_review` |
| `crew_motion_authenticity_read` | `defer_pending_human_review` |
| `uncanny_motion_read` | `defer_pending_human_review` |
| `crew_count_read` | `defer_pending_human_review` |
| `identity_logo_text_read` | `defer_pending_human_review` |
| `pad_hardware_stability_read` | `defer_pending_human_review` |
| `shuttle_anatomy_stability_read` | `defer_pending_human_review` |
| `launch_chronology_read` | `defer_pending_human_review` |

## Human Review Options

Reply with exactly one response: `keep A`, `keep B`, `keep C`, `tighten`, or `reject`.

If one candidate is kept, the next artifact should be a full-runtime HTML proof that loops the selected LTX video carrier behind the existing staged right rail. No full-runtime MP4 or downstream assembly is authorized by this scout packet.

## Loop Carrier Tighten Record

Disposition recorded: `tighten`.

Reason: the clips were not reviewed as a smooth living-cover loop carrier for a ~20-minute video. The successor narrows the problem to seven subtle, detectable, back-view astronaut motions on a clean loop.

Next review artifact: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_apple_ltx23_crew_loop_scout_20260505T182937Z`

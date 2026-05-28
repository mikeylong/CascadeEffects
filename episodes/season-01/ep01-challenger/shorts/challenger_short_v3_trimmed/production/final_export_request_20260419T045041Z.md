# Challenger Final Export Request 20260419T045041Z

## Request

- `episode_id`: `challenger`
- `short_id`: `challenger_short_minimal_surreal_v3_trimmed`
- `coordinator_skill_path`: `/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_production_v1/SKILL.md`
- `final_export_skill_path`: `/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_final_export_v1/SKILL.md`
- `canonical_flow`: `script -> audio -> stills contact sheet -> stills video proof -> motion contact sheet -> motion video proof -> video final`

## Approved Inputs

- `motion_video_proof_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/20260419T045041Z__proof.mp4`
- `motion_video_proof_manifest_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/20260419T045041Z__proof.json`
- `motion_video_proof_review_note_path`: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/motion_video_proof_review_20260419T045041Z.md`
- `motion_video_proof_disposition`: `keep`
- `reel_class`: `keeper short`
- `motion_contact_sheet_review_path`: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/motion_contact_sheet_review_20260419T035901Z.md`
- `approved_short_audio_wav_path`: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_v3_trimmed/final/challenger_short_v3_trimmed.wav`
- `short_audio_package_path`: `/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_short_v3_trimmed/audio_package.json`
- `expected_voice_profile_id`: `youtube_shorts_mike_challenger_match_v1`
- `audio_package_sha256`: `1e191295642fd5dc2bb3d98c306da7cf09962b2e1d654933d9f9fc9a97160c36`
- `packaged_audio_sha256`: `7da2a21202a1ec4d1e9e61457d1f70cbfa421daeed59536c699c2f2f9bc6ddcf`
- `audio_disposition`: `keep`
- `qa_transcript_or_caption_source_path`: `/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_short_v3_trimmed/transcripts_mastered/challenger_short_v3_trimmed.diarized.txt`
- `caption_source_path`: `/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_short_v3_trimmed/transcripts_mastered/challenger_short_v3_trimmed.diarized.txt`
- `transcript_sha256`: `4c849f6aa47bd00ec64d6bf020d3b9253994484385d04367bfa12de0fd9dbf7c`
- `caption_style_preset`: `documentary_lower_third_v1`
- `caption_placement`: `lower-center`
- `output_target_dir`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/final_exports/challenger_final_v2`

## Final Gate Checks

- `all_motion_clips_are_keep`: `true`
- `no_diagnostic_placeholders`: `true`
- `audio_exists`: `true`
- `audio_package_exists`: `true`
- `audio_package_provenance_checked`: `true`
- `voice_profile_final_export_eligible`: `true`
- `audio_disposition_keep`: `true`
- `transcript_exists`: `true`
- `proof_review_exists`: `true`
- `caption_preset_selected`: `true`
- `unresolved_mixed_review_blockers`: `false`

## Coordinator Instructions

- `caption_notes`: `Use phrase-level documentary lower-third captions derived only from the approved QA transcript.`
- `must_not_cover`: `right booster joint smoke in beat_04a, airborne flame in beat_04b, NASA breakup geometry in beat_04c, faces in beat_01a and beat_03, and status-wall anomaly in beat_05`
- `placement_override_reason`: `Use lower-left only if lower-center obscures the mechanism or historical breakup geometry during QA.`
- `manual_timing_constraints`: `No manual timing override requested for first pass; record any post-QA override in the final export manifest.`
- `next_action_if_blocked`: `Return to the coordinator; do not create a publishable final from any non-keep proof.`

# Challenger Final Export Request Example

## Request

- `episode_id`: `challenger`
- `short_id`: `challenger_short_minimal_surreal_v3_trimmed`
- `coordinator_skill_path`: `/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_production_v1/SKILL.md`
- `final_export_skill_path`: `/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_final_export_v1/SKILL.md`
- `canonical_flow`: `script -> audio -> visual research packet -> stills contact sheet -> stills video proof -> motion contact sheet -> motion video proof -> video final`

## Approved Inputs

- `motion_video_proof_path`: `/Users/mike/CascadeEffects/packages/media-pipeline/viz/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/20260419T045041Z__proof.mp4`
- `motion_video_proof_manifest_path`: `/Users/mike/CascadeEffects/packages/media-pipeline/viz/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/20260419T045041Z__proof.json`
- `motion_video_proof_review_note_path`: `/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/motion_video_proof_review_20260419T045041Z.md`
- `motion_video_proof_disposition`: `keep`
- `reel_class`: `keeper short`
- `approved_short_audio_wav_path`: `/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/challenger_short_v3_trimmed/final/challenger_short_v3_trimmed.wav`
- `short_audio_package_path`: `/Users/mike/CascadeEffects/packages/media-pipeline/audio/tmp/ep1_challenger_short_v3_trimmed/audio_package.json`
- `expected_voice_profile_id`: `youtube_shorts_mike_challenger_match_v1`
- `audio_package_sha256`: `1e191295642fd5dc2bb3d98c306da7cf09962b2e1d654933d9f9fc9a97160c36`
- `packaged_audio_sha256`: `7da2a21202a1ec4d1e9e61457d1f70cbfa421daeed59536c699c2f2f9bc6ddcf`
- `audio_disposition`: `keep`
- `brand_motif_status`: `present`
- `motif_text`: `Small causes, massive consequences.`
- `motif_waiver_reason`: ``
- `ending_cadence_read`: `pass`
- `caption_model`: `script_locked_canonical_text_timing_from_asr_v1`
- `caption_text_source_path`: `/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/challenger_short_v3_trimmed/challenger_short_v3_trimmed.txt`
- `caption_text_source_policy`: `script_locked_canonical_text_only`
- `caption_timing_source_path`: `/Users/mike/CascadeEffects/packages/media-pipeline/audio/tmp/ep1_challenger_short_v3_trimmed/transcripts_mastered/challenger_short_v3_trimmed.diarized.txt`
- `caption_timing_source_policy`: `asr_whisperx_timing_only`
- `caption_text_matches_script_read`: `pass`
- `caption_asr_text_not_used_read`: `pass`
- `transcript_sha256`: `4c849f6aa47bd00ec64d6bf020d3b9253994484385d04367bfa12de0fd9dbf7c`
- `caption_timing_path`: `/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/challenger_short_v3_trimmed.script_locked_rail_safe.offset_intro_0s000.srt`
- `manual_timing_adjustments_path`: `/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/caption_manual_adjustments_20260419T010520Z.json`
- `motif_outro_mix_used`: `false`
- `body_loop_path`:
- `outro_path`:
- `final_frame_hold_seconds`: `0`
- `caption_style_preset`: `minimal_surreal_editorial_v1`
- `caption_placement`: `lower-left`
- `output_tag`: `challenger_final_v3_minimal_surreal_lower_left`

## Final Gate Checks

- `all_motion_clips_are_keep`: `true`
- `no_diagnostic_placeholders`: `true`
- `audio_exists`: `true`
- `audio_package_exists`: `true`
- `audio_package_provenance_checked`: `true`
- `voice_profile_final_export_eligible`: `true`
- `audio_disposition_keep`: `true`
- `brand_motif_status_valid`: `true`
- `ending_cadence_read_pass`: `true`
- `closing_motif_caption_preserved`: `true`
- `transcript_exists`: `true`
- `proof_review_exists`: `true`
- `caption_preset_selected`: `true`
- `motif_outro_mix_review_required`: `false`
- `motif_music_bed_read_pass`: `not_applicable`
- `outro_completion_read_pass`: `not_applicable`
- `final_mix_no_clipping`: `not_applicable`
- `unresolved_mixed_review_blockers`: `false`

## Preferred Command

Use the approved-proof wrapper when the coordinator has already locked the keeper gates:

```bash
/Users/mike/CascadeEffects/packages/media-pipeline/viz/bin/ce short final-approved \
  /Users/mike/CascadeEffects/packages/media-pipeline/viz/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/20260419T045041Z__proof.json \
  --proof-review-note /Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/motion_video_proof_review_20260419T045041Z.md \
  --caption-style minimal_surreal_editorial_v1 \
  --caption-placement lower-left \
  --caption-source /Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/challenger_short_v3_trimmed/challenger_short_v3_trimmed.txt \
  --caption-timing /Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/challenger_short_v3_trimmed.script_locked_rail_safe.offset_intro_0s000.srt \
  --manual-timing-adjustments /Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/caption_manual_adjustments_20260419T010520Z.json \
  --output-tag challenger_final_v3_minimal_surreal_lower_left
```

Use the explicit gated command when a reviewer needs every gate assertion visible in the invocation:

```bash
/Users/mike/CascadeEffects/packages/media-pipeline/viz/bin/ce short final-export \
  /Users/mike/CascadeEffects/packages/media-pipeline/viz/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/20260419T045041Z__proof.json \
  --proof-review-note /Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/motion_video_proof_review_20260419T045041Z.md \
  --proof-disposition keep \
  --reel-class keeper-short \
  --all-motion-clips-keep \
  --no-diagnostic-placeholders \
  --caption-style minimal_surreal_editorial_v1 \
  --caption-placement lower-left \
  --caption-source /Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/challenger_short_v3_trimmed/challenger_short_v3_trimmed.txt \
  --caption-timing /Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/challenger_short_v3_trimmed.script_locked_rail_safe.offset_intro_0s000.srt \
  --manual-timing-adjustments /Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/caption_manual_adjustments_20260419T010520Z.json \
  --output-tag challenger_final_v3_minimal_surreal_lower_left
```

## Expected Outputs

- `caption_style_preset`: `minimal_surreal_editorial_v1`
- `caption_placement`: `lower-left`
- `captioned_final_path`: `/Users/mike/CascadeEffects/packages/media-pipeline/viz/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/final_exports/challenger_final_v3_minimal_surreal_lower_left/<timestamp>__captioned_final.mp4`
- `final_export_manifest_path`: `/Users/mike/CascadeEffects/packages/media-pipeline/viz/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/final_exports/challenger_final_v3_minimal_surreal_lower_left/<timestamp>__final_export.json`
- `disposition`: `keep`
- `reel_class`: `keeper short`

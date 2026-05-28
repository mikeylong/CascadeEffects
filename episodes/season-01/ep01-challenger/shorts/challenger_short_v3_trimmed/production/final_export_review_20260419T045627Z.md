# Challenger Final Export Review

- `episode_id`: `challenger`
- `short_id`: `challenger_short_minimal_surreal_v3_trimmed`
- `stage`: `video final`
- `review_timestamp`: `20260419T045627Z`
- `motion_video_proof_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/20260419T045041Z__proof.mp4`
- `motion_video_proof_manifest_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/20260419T045041Z__proof.json`
- `motion_video_proof_review_note_path`: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/motion_video_proof_review_20260419T045041Z.md`
- `final_export_request_path`: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/final_export_request_20260419T045041Z.md`
- `caption_timing_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/final_exports/challenger_final_v2_lower_left/20260419T045627Z__caption_timing.json`
- `caption_overlay_manifest_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/final_exports/challenger_final_v2_lower_left/20260419T045627Z__caption_overlay_manifest.json`
- `captioned_final_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/final_exports/challenger_final_v2_lower_left/20260419T045627Z__captioned_final.mp4`
- `final_export_manifest_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/final_exports/challenger_final_v2_lower_left/20260419T045627Z__final_export.json`
- `manual_timing_adjustments_path`: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/caption_manual_adjustments_20260419T010520Z.json`
- `caption_style_preset`: `documentary_lower_third_v1`
- `caption_placement`: `lower-left`
- `placement_override_reason`: `Lower-center captions covered or pressed into the beat_04b flame/exhaust read and beat_04c breakup geometry; lower-left preserves the central/right mechanism geometry.`
- `video_geometry`: `1080x1920`
- `fps`: `24`
- `duration_seconds`: `57.307007`
- `audio_present`: `true`
- `disposition`: `keep`
- `reel_class`: `keeper short`
- `may_advance`: `true`

## QA Results

- `json_valid`: `true`
- `audio_duration_match`: `true; final duration 57.307007s against approved audio duration 57.306848s`
- `caption_text_clean`: `true; no SPEAKER_ labels or diarized timestamp strings remain`
- `caption_legibility_checked`: `true`
- `caption_safe_zone_checked`: `true`
- `mechanism_not_occluded`: `true after lower-left placement override`
- `diagnostic_placeholders_present`: `false`
- `all_motion_clips_keep`: `true`
- `audio_provenance_valid`: `true`

## Export Attempts

- `20260419T045320Z`: diagnostic export only; default caption generation carried diarized timestamp and `SPEAKER_00` labels into the burned captions.
- `20260419T045437Z`: diagnostic export only; cleaned captions were text-correct, but lower-center placement covered or crowded key beat_04 geometry.
- `20260419T045627Z`: keeper export; cleaned caption timing plus lower-left placement clears final QA.

## Handoff Packet

```yaml
stage: video final
episode_id: challenger
short_id: challenger_short_minimal_surreal_v3_trimmed
proof_video_path: /Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/20260419T045041Z__proof.mp4
review_note_path: /Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/final_export_review_20260419T045627Z.md
transcript_or_caption_source: /Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/caption_timing_clean_20260419T010520Z.json
caption_style_preset: documentary_lower_third_v1
caption_placement: lower-left
caption_timing_path: /Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/final_exports/challenger_final_v2_lower_left/20260419T045627Z__caption_timing.json
caption_overlay_manifest_path: /Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/final_exports/challenger_final_v2_lower_left/20260419T045627Z__caption_overlay_manifest.json
captioned_final_path: /Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/final_exports/challenger_final_v2_lower_left/20260419T045627Z__captioned_final.mp4
final_export_manifest_path: /Users/mike/Viz_CascadeEffects/workflows/generated/shorts/challenger_short_minimal_surreal_v3_trimmed/20260419T045041Z/final_exports/challenger_final_v2_lower_left/20260419T045627Z__final_export.json
disposition: keep
reel_class: keeper short
blockers: []
next_action: publish/use the 20260419T045627Z captioned final as the current Challenger video final
may_advance: true
```

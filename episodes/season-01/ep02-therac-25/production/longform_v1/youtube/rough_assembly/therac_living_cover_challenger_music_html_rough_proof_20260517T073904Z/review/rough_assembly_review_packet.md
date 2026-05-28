# Therac-25 Challenger-Style Music Rough Proof

Player: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/rough_assembly/therac_living_cover_challenger_music_html_rough_proof_20260517T073904Z/player.html`

## Review Focus

- Music-only open should hold until `9.601s`.
- The first narration line should begin at `9.601s`.
- Intro music should fade under the first two seconds of voice and be gone by `11.601s`.
- The story should end at `1090.862s`, then the full Paper Architecture outro should carry the end screen.
- Captions, right rail, and ambient effects should stay aligned to the story after the voice-start offset.
- In the end-screen window, chapter, context, and caption text must be fully suppressed. Any faint viewer-facing text behind YouTube target geometry is an artifact and fails `end_screen_text_artifact_read`.

## Repair Note

- `rail_fade_read`: `pass_rail_fully_suppressed_no_faint_text_in_end_screen`
- `end_screen_text_artifact_read`: `pass_no_viewer_text_visible_or_faint_in_end_screen_window`
- `viewer_text_suppression_read`: `pass_chapter_context_and_caption_text_hidden_for_youtube_target_geometry`

## Operator CRT Repair Note

- Lower operator-console CRT now uses non-readable period-terminal field geometry with a 14.2s, five-state cycle.
- Lower operator-console CRT scanline/static/rolling band was removed.
- Top-left wall monitor scanline/static behavior is intentionally preserved.
- `operator_crt_ui_cycle_read`: `pass_operator_console_terminal_geometry_changes_on_14s_cycle`
- `operator_crt_scanline_absence_read`: `pass_lower_operator_crt_has_no_rolling_scanline_or_static_noise_layer`
- `operator_crt_no_readable_text_read`: `pass_lower_operator_crt_uses_non_readable_canvas_geometry_only`
- `top_left_monitor_scanline_static_preserved_read`: `pass_top_left_wall_monitor_retains_scanline_static_behavior`

## Right Rail Copy Repair Note

- Visible right-rail ordinal labels were replaced with semantic episode-specific eyebrows.
- Forbidden visible rail labels include `CHAPTER ##`, `PART ##`, and `SECTION ##`.
- `ordinal_chapter_label_read`: `pass_no_visible_ordinal_chapter_labels`
- `semantic_rail_label_read`: `pass_episode_specific_right_rail_eyebrows`

## Audio Pronunciation Repair Note

- At active proof `00:03:52`, `duplicate` was repaired to the verb pronunciation, `dupli-cate`.
- The locked script and caption text still say `duplicate`; only the localized TTS render used phonetic `dupli-kate`.
- The repair replaced one sentence with 20ms crossfades and preserved the voice master, active WAV, MP3, VTT, SRT, chapter, and story timings.
- `duplicate_pronunciation_repair_read`: `pass_tts_render_forced_dupli_kate_pronunciation`
- `localized_audio_splice_read`: `pass_single_sentence_replacement_20ms_crossfades`
- `audio_duration_preservation_read`: `pass_voice_and_review_mix_durations_unchanged`
- `caption_text_preservation_read`: `pass_no_vtt_srt_or_locked_script_text_change`

## Human Disposition

- `human_disposition`: `keep`
- Scope: current HTML rough proof after the duplicate-pronunciation repair.
- This opens final MP4 rendering from this kept HTML proof only.
- Final assembly, publish readiness, YouTube upload, and public release remain locked pending the final MP4 review gate.

## Locks

Final assembly, publish readiness, upload, and public release remain blocked until the next human review gate.

# Tacoma Music Integration Contract

Status: `review_ready_human_keep_pending`
Lane: `challenger_style_intro_outro`

## Timing Contract
- Music-only intro: `0.000000s` to `9.601451s`.
- Voice starts at `9.601451s`.
- Intro fade tail ends at `11.601451s`.
- Voice ends / full outro starts at `852.532245s`.
- End-screen target window: `863.327460s` to `883.327460s`.
- Planned proof duration: `883.327460s`.

## Caption Retiming
- Visible rail captions and YouTube sidecar use locked-script text.
- Offset sidecars add `9.601451s` for the music lead-in.
- Captions are suppressed after outro start.

## Reads
- `music_integration_plan_read`: `pass_packet_local_contract_created`
- `series_music_contract_read`: `pass_challenger_style_intro_outro_default`
- `approved_music_source_read`: `pass_registered_paper_architecture_theme_assets_recorded`
- `intro_music_contract_read`: `pass_music_only_intro_plus_2s_fade_tail_under_opening_voice`
- `voice_start_offset_read`: `pass_9_601451s`
- `caption_timing_shift_read`: `pass_offset_sidecars_generated_from_locked_script`
- `full_outro_music_read`: `pass_30_795215s_full_outro_after_voice`
- `end_screen_music_handoff_read`: `pass_outro_carries_through_20s_static_target_window`
- `audio_level_mix_read`: `planned_required_before_rough_keep`
- `music_rights_read`: `review_warning_registered_theme_assets_content_id_check_before_public_release`
- `music_contract_regression_read`: `pass_no_under_opening_voice_bed_plus_short_tail`
- `no_music_or_temp_music_waiver_read`: `not_applicable_no_waiver_requested`

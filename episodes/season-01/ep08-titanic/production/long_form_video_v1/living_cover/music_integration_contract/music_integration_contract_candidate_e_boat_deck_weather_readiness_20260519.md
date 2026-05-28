# Titanic Music Integration Contract

Date: 2026-05-19

Episode: Titanic

Workflow: `long_form_video_production_v1`

Process: `living_cover_music_integration_contract_v1`

Status: `review_ready_pending_human_keep`

Human disposition: `pending`

## Scope

This packet declares the music, timing, caption retime, and VO/outro handoff contract for the Titanic long-form Living Cover built from kept source-art Candidate E.

It is a contract only. It does not render a mixed proof, approve motion readiness, approve rough assembly, render a final MP4, prepare an upload, or authorize any YouTube action.

## Approved Inputs

- Voice master: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/final/Ep8_Titanic.wav`
- Voice master SHA-256: `81488bff51999910864535a8fe93645bd7f930a7846198a4e89e9df36fec9604`
- Voice profile: `longform_mike_v1`
- Voice duration: `740.716553` seconds
- Voice codec: `pcm_s16le`, `44100` Hz, mono
- Locked script: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/Ep8_Titanic.txt`
- Locked script SHA-256: `a5fb122223052b820f7dd832a7f9227db4780f9d4ffd810915e579bef1249dc3`
- Timing source: `/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_longform_receipts_signoff_20260519/transcripts_mastered/Ep8_Titanic.whisperx.json`
- Timing source SHA-256: `51a705c669285a7e134c0f81d99fd080747e58500734673db412d78db69138f7`
- Music registry: `/Users/mike/Agents_CascadeEffects/references/shorts/music_track_registry.json`
- Music registry SHA-256: `63ccbbe7db489ff01c2619bde1d481df86a96bb3292a9f95c7b0127e35da6d0d`

## Music Sources

- Intro source: `/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture instrumental_loop.wav`
- Intro source SHA-256: `b26f01b5397398e20f24a2e5396221f5e5a1c3b9672baf9e37cb20adda982818`
- Intro source duration: `9.601451` seconds
- Intro source codec: `pcm_s16le`, `44100` Hz, stereo
- Full outro source: `/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture.m4a`
- Full outro source SHA-256: `d71785b8b28691260ca55fe5de1657ff5e6b69cd986dc04cfe09a1967c67b365`
- Full outro source duration: `30.795215` seconds
- Full outro source codec: `aac`, `44100` Hz, stereo
- Full outro source precedent: Challenger long-form `subtle_tail_outro_v1` full-outro source

## Timing Contract

- Series precedent: Challenger-style music integration
- Voice start offset: `9.601451` seconds
- Voice end in proof timeline: `750.318004` seconds
- Intro policy: music-only lead-in from `0.000000` to `9.601451`
- Intro fade tail under voice: `9.601451` to `11.601451`
- Story-time model: `storyTimeAt(audioTime) = max(0, audioTime - 9.601451)` before outro suppression rules
- Outro blend policy: `subtle_tail_outro_v1`
- Full outro starts: `748.818004` seconds
- Full outro prelap: `1.500000` seconds before voice end
- Under-VO outro gain: `0.10` linear maximum before voice end
- Outro target gain: `0.42` linear after voice end
- Outro reaches target no earlier than: `753.318004` seconds
- Full outro must continue across voice end without restarting
- Planned total proof duration: `779.613219` seconds
- End-screen window: `759.613219` to `779.613219`

## Script-Locked Caption Retime

Generated sidecars use the locked script as the only visible caption text source. WhisperX is timing only.

- Story VTT: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/living_cover/music_integration_contract/assets/captions/titanic_longform.script_locked_rail_safe.vtt`
- Story VTT SHA-256: `7ea3e291915f4269b6ac5080ed872d420072a64f8e359e2ec6f766d8b59194b1`
- Story SRT: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/living_cover/music_integration_contract/assets/captions/titanic_longform.script_locked_rail_safe.srt`
- Story SRT SHA-256: `5638dce45c628e5b4099f271a49685dfaec64204c0fc827311a7667b7bebc5e7`
- Offset VTT: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/living_cover/music_integration_contract/assets/captions/titanic_longform.script_locked_rail_safe.offset_intro_9s601.vtt`
- Offset VTT SHA-256: `c73f1b582f4f4e088d184a2eefc8bf107f1e2f1e566ac8af2522a5ce3e7f5508`
- Offset SRT: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/living_cover/music_integration_contract/assets/captions/titanic_longform.script_locked_rail_safe.offset_intro_9s601.srt`
- Offset SRT SHA-256: `36b30062177db1f35b97d84e861f20e5dd9a68c952ae282e19978c5e377b15ce`
- Caption QA JSON: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/living_cover/music_integration_contract/assets/captions/titanic_longform.script_locked_caption_qa.json`
- Caption QA JSON SHA-256: `94c587a7a6df5540ccff5d4581db9cb1dd10730085719b191b6595a32ae4ee78`
- Caption status: `pass`
- Alignment coverage: `0.9932394366197184`
- Cue count: `260`

## Required Reads

- `music_integration_plan_read`: `pass_packet_local_contract_created`
- `series_music_contract_read`: `pass_challenger_style_intro_outro_default`
- `approved_music_source_read`: `pass_registered_intro_and_challenger_precedent_full_outro_recorded`
- `intro_music_contract_read`: `pass_music_only_intro_plus_2s_fade_tail_under_opening_voice`
- `voice_start_offset_read`: `pass_9_601451s`
- `caption_timing_shift_read`: `pass_offset_sidecars_generated_from_locked_script`
- `full_outro_music_read`: `pass_full_paper_architecture_track_planned_as_actual_prelap_source`
- `end_screen_music_handoff_read`: `pass_full_outro_carries_20s_static_target_window`
- `vo_outro_blend_plan_read`: `pass_subtle_tail_outro_v1_contract`
- `vo_outro_music_blend_read`: `planned_required_before_rough_keep`
- `vo_outro_perceptual_review_read`: `planned_transition_sample_required_before_rough_keep`
- `outro_transition_review_sample_read`: `planned_required_before_rough_keep`
- `outro_entry_level_match_read`: `planned_required_before_rough_keep`
- `outro_under_vo_masking_read`: `planned_under_vo_music_margin_required_before_rough_keep`
- `outro_target_after_voice_read`: `pass_target_gain_after_voice_end_planned`
- `outro_prelap_source_read`: `pass_full_outro_track_used_not_proxy`
- `outro_prelap_start_read`: `pass_1p5s_before_voice_end`
- `outro_no_restart_at_voice_end_read`: `pass_planned_no_restart`
- `outro_source_continuity_read`: `pass_planned_continuous_across_voice_end`
- `audio_level_mix_read`: `planned_required_before_rough_keep`
- `music_rights_read`: `review_warning_registered_theme_assets_content_id_check_before_public_release`
- `music_contract_regression_read`: `pass_no_under_opening_voice_bed_plus_short_tail`
- `no_music_or_temp_music_waiver_read`: `not_applicable_no_waiver_requested`
- `intro_rail_readiness_read`: `planned_required_before_rough_keep`
- `intro_active_title_read`: `planned_required_before_rough_keep`
- `intro_summary_legibility_read`: `planned_required_before_rough_keep`
- `intro_context_readability_read`: `planned_required_before_rough_keep`
- `intro_transition_completion_read`: `planned_required_before_rough_keep`

## Gate Locks

- May mark music integration contract keep: `false`
- May start motion readiness: `false`
- May start rough assembly: `false`
- May render final MP4: `false`
- May prepare upload: `false`
- May take YouTube action: `false`
- Public release ready: `false`

## Required Human Decision

Human review must mark this music integration contract `keep`, `tighten`, or `reject`.

Only a `keep` may open motion readiness. Rough assembly remains blocked until a kept music contract exists and the rough proof integrates music according to this contract.

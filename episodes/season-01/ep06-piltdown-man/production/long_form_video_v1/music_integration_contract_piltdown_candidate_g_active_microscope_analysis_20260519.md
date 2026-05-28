# Piltdown Man Music Integration Contract

Date: 2026-05-19

Episode: Piltdown Man

Workflow: `long_form_video_production_v1`

Process: `living_cover_music_integration_contract_v1`

Status: `keep`

Human disposition: `keep`

## Human Keep

- Human music integration contract keep: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/human_music_integration_contract_keep_candidate_g_active_microscope_analysis_20260519.md`
- Human music integration contract keep SHA-256: `6d18f852d4b7405628962018d83e0f0ad1c0baf0d0fe3c1a53840fedd6501196`
- Keep signal: `keep - continue`
- Gate effect: opens motion-readiness review only.

## Scope

This packet declares the music, timing, caption retime, and VO/outro handoff contract for the Piltdown Man long-form Living Cover built from kept source-art Candidate G.

It is a kept contract only. It does not render a mixed proof, approve rough assembly, render a final MP4, prepare an upload, or authorize any YouTube action.

## Approved Inputs

- Voice master: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/final/Ep6_Piltdown-Man.wav`
- Voice master SHA-256: `fa215461f2e522816d462d2bbfe9a85c607efecd002999d5e5c8a8e4df91e127`
- Voice profile: `longform_mike_v1`
- Voice duration: `840.980317` seconds
- Voice codec: `pcm_s16le`, `44100` Hz, mono
- Locked script: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/Ep6_Piltdown-Man.txt`
- Locked script SHA-256: `dca919591b0db8c99c3124f8ba794944daaf9b4c09a9e364d7d36d2fb816ddbf`
- Timing source: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/transcripts_mastered_voiceover_repair_20260518/Ep6_Piltdown-Man.whisperx.json`
- Timing source SHA-256: `96bbc088191a76244d81592efca27cbbf57128817b2cf1a0b62fa76f91efb514`
- Kept source-art plate: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/source_art_generation_non_paper_20260519/assets/source_art/candidate_g_active_microscope_analysis_1920x1080.png`
- Kept source-art SHA-256: `4615cff276f95e544aa8a21004f8c520cb190860d04860f1bed9d5ae7a22a7a0`
- Kept cue map: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/living_cover_cue_map_candidate_g_active_microscope_analysis_20260519.md`
- Kept cue map SHA-256: `f7803b9224929ff955ce297a93807fd558aa976e191b33f4efbfb5abfed4fd6d`
- Kept ambient/effects layer: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/living_cover_ambient_effects_layer_candidate_g_active_microscope_analysis_20260519.md`
- Kept ambient/effects layer SHA-256: `8cc83ddb1ae355e318f2f1bebe37985bba643f6fd0e808474a111ac1a665337c`
- Human ambient/effects keep: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/human_living_cover_ambient_effects_layer_keep_candidate_g_active_microscope_analysis_20260519.md`
- Human ambient/effects keep SHA-256: `6dad5a5fbdebfd514cc2518411c375aefb655bb48a15b8d74ddcfdb67f832687`
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
- Visual boundary: Paper Architecture is used here only as registered music/theme asset naming. It is not active source art, visual style, or prompt language.

## Timing Contract

- Series precedent: Challenger-style music integration
- Voice start offset: `9.601451` seconds
- Voice end in proof timeline: `850.581768` seconds
- Intro policy: music-only lead-in from `0.000000` to `9.601451`
- Intro fade tail under voice: `9.601451` to `11.601451`
- Story-time model: `storyTimeAt(audioTime) = max(0, audioTime - 9.601451)` before outro suppression rules
- Outro blend policy: `subtle_tail_outro_v1`
- Full outro starts: `849.081768` seconds
- Full outro prelap: `1.500000` seconds before voice end
- Under-VO outro gain: `0.10` linear maximum before voice end
- Outro target gain: `0.42` linear after voice end
- Outro reaches target no earlier than: `853.581768` seconds
- Full outro must continue across voice end without restarting
- Planned total proof duration: `879.876983` seconds
- End-screen window: `859.876983` to `879.876983`

## Script-Locked Caption Retime

Generated sidecars use the locked script as the only visible caption text source. WhisperX is timing only.

- Story VTT: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/music_integration_contract_assets/captions/piltdown_longform.script_locked_rail_safe.vtt`
- Story VTT SHA-256: `7746ad0246d660849df8750d99b1fc6376372d33bfe5b1b05f80b80787c26a5a`
- Story SRT: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/music_integration_contract_assets/captions/piltdown_longform.script_locked_rail_safe.srt`
- Story SRT SHA-256: `a4a2ba41fbf99d3f1ea3e8c897601d0792012f8b84b81d5707b67488b711bae2`
- Offset VTT: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/music_integration_contract_assets/captions/piltdown_longform.script_locked_rail_safe.offset_intro_9s601.vtt`
- Offset VTT SHA-256: `13c391067c31fe4ab1dfed611993d65e660b6d99e09dbb1da29c08c8361f8679`
- Offset SRT: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/music_integration_contract_assets/captions/piltdown_longform.script_locked_rail_safe.offset_intro_9s601.srt`
- Offset SRT SHA-256: `cf84f1a4d74f99513261ba604ac7c26c9c5161933ab1f2d5add7500db85bfdb4`
- Caption QA JSON: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/music_integration_contract_assets/captions/piltdown_longform.script_locked_caption_qa.json`
- Caption QA JSON SHA-256: `e8a49946b5e17e504be820de24f1cd4da928e00e5379788a2d1940ba6f272ebf`
- Caption status: `pass`
- Alignment coverage: `0.9926892950391645`
- Cue count: `280`

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
- `video_visual_style_scope_read`: `pass_long_form_video_asset_non_paper`
- `paper_architecture_visual_style_read`: `pass_no_paper_architecture_visual_style_music_track_name_only_not_visual_style`

## Gate Locks

- May mark music integration contract keep: `false`
- May start motion readiness after human keep: `true`
- May start rough assembly: `false`
- May render final MP4: `false`
- May prepare upload: `false`
- May take YouTube action: `false`
- Public release ready: `false`

## Required Human Decision

Human review has marked this music integration contract `keep`.

Motion-readiness review is now open. Rough assembly remains blocked until motion readiness receives human `keep` and the rough proof integrates music according to this contract.

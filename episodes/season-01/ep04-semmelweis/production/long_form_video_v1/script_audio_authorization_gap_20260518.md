# Semmelweis Script/Audio Authorization Gap

Date: 2026-05-18

Workflow: `long_form_video_production_v1`

Episode: `semmelweis`

## Status

Semmelweis has a locked long-form script and fact-check, and Claude returned `pass_no_script_changes`. It still cannot enter long-form audio rendering or Living Cover production until explicit human audio approval, audio source integrity, and timing provenance are recorded.

## Required Missing Reads

- `human_script_approval_for_audio_read`
- `audio_source_integrity_read`

## Current Evidence

- Locked script: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/Ep4_Semmelweis.txt`
- Locked script SHA-256: `2bca08c0899da81a909d550a76dc0e2cb6ddccaa764b8c45ad9298c918276d68`
- Fact-check: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/fact_check.md`
- Fact-check SHA-256: `e4adaa25f8b09b96c5f6c58c0758e7c476fc64b5b90b830e960fd71ee3663ace`
- Frontier critique: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/frontier_model_script_critique_claude_20260518.md`
- Frontier critique SHA-256: `60ebbf0f8256f9be9bcca010c5d22410100be84a9dcf840f20cda68649952dd1`
- Critique integration note: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/script_gate_integration_note_20260518.md`
- Critique integration SHA-256: `9007ef64018e3d17100dd8e7994bec2628d00bb9c0f84622de1bf47a276f187b`
- Long-form audio master: missing at `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/final/Ep4_Semmelweis.wav`
- Long-form transcript/timing source: missing

## Required Action

Capture explicit human approval for audio. Only then render or promote long-form voice audio and create timing provenance.

Until this is complete, downstream gates stay closed:

- `may_advance_to_visual_system: false`
- `may_start_rough_assembly: false`
- `may_render_final_mp4: false`
- `may_youtube_action: false`
- `public_release_ready: false`

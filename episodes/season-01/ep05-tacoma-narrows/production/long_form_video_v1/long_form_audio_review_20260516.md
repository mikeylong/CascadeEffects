# Tacoma Narrows Long-Form Audio Review

Date: 2026-05-16

Workflow: `long_form_video_production_v1`

Gate: `long_form_audio`

Disposition: `keep`

Human keep status: `keep`

## Source

- Locked script: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/Ep5_Tacoma-Narrows.txt`
- Locked script SHA-256: `08ae7837e0f01ac9a281f631b9d678dcd27ed9186946a1a50bd685fa42db586a`
- Frontier-model critique: `pass_with_tightening`
- Critique integration: `pass_required_changes_integrated`
- Human script approval for audio: `pass`
- Render plan: direct full render, no audition pass
- Chunk count: `6`
- Jobs manifest: `/Users/mike/Audio_CascadeEffects/tmp/ep5_tacoma_narrows_production/final_jobs.jsonl`
- Jobs manifest SHA-256: `b7af6f3fd85888a6e8ee2993c836516f750e574a76e4c300c10dcfa6249d420b`
- Effective ElevenLabs manifest: `/Users/mike/Audio_CascadeEffects/tmp/ep5_tacoma_narrows_production/effective_final_jobs.elevenlabs.jsonl`
- Effective ElevenLabs manifest SHA-256: `2a757db2bc29c7e48461ae8423b28228e09e77ab3d73c678516c334da28430bf`

## Voice Package

- Provider: `elevenlabs`
- Voice profile: `longform_mike_v1`
- Voice: `dPrTCMw2R7HQlznlgwCO`
- Model: `eleven_multilingual_v2`
- Speed: `0.95`
- Settings: stability `0.6`, similarity boost `0.8`, style `0.0`, speaker boost `true`
- Bracketed performance tags: source direction only; not spoken

## Output

- Packaged WAV: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/final/Ep5_Tacoma-Narrows.wav`
- Packaged WAV SHA-256: `de593cc6e4a554507f45a0289177a31b321a2017caca361287315d85cca7e2bf`
- Audio package: `/Users/mike/Audio_CascadeEffects/tmp/ep5_tacoma_narrows_production/audio_package.json`
- Audio package SHA-256: `fb536ed5169679235c09c27fc869b31361fd6ecd711b5d72db5ce40ee171abf7`

## ffprobe Facts

- Duration: `842.930794s`
- Size: `74346574` bytes
- Bit rate: `705600`
- Codec: `pcm_s16le`
- Sample rate: `44100`
- Channels: `1`
- Bits per sample: `16`

## QA And Timing Provenance

- Prosody guard: `ok_no_repairs`
- Prosody guard report: `/Users/mike/Audio_CascadeEffects/tmp/ep5_tacoma_narrows_production/prosody_guard/guard_report.json`
- Prosody guard SHA-256: `99e25dc253344336bfb8358ba688246c6ca6120f45453395f95b15ac8f69d0ff`
- WhisperX JSON: `/Users/mike/Audio_CascadeEffects/tmp/ep5_tacoma_narrows_production/transcripts_mastered/Ep5_Tacoma-Narrows.whisperx.json`
- WhisperX JSON SHA-256: `b16db284d29cbb496984117ccc00d8d3462538648eef26f03c791ab05a8ebd4e`
- Transcript TXT: `/Users/mike/Audio_CascadeEffects/tmp/ep5_tacoma_narrows_production/transcripts_mastered/Ep5_Tacoma-Narrows.diarized.txt`
- Transcript TXT SHA-256: `8a3915c5507a3ee0ccd3cb6a7cd250e283e0a3bf642523b521fe6ef746bbeada`
- SRT: `/Users/mike/Audio_CascadeEffects/tmp/ep5_tacoma_narrows_production/transcripts_mastered/Ep5_Tacoma-Narrows.diarized.srt`
- SRT SHA-256: `2e46f9a19ddd251624b660158094e65cd8c5145ead29047dd0b4f2e2eb8d159d`
- VTT: `/Users/mike/Audio_CascadeEffects/tmp/ep5_tacoma_narrows_production/transcripts_mastered/Ep5_Tacoma-Narrows.diarized.vtt`
- VTT SHA-256: `141c5e8fa99f91bdd2114306db730ccf9e352353c255dfea2122a2f6e86c87f9`

These transcript artifacts are timing provenance only for future Living Cover caption work. Visible long-form captions must be built from the locked script text, not ASR text.

## Gate State

- `audio_review_ready`: `true`
- `frontier_model_script_critique_read`: `pass_with_tightening`
- `critique_integration_read`: `pass_required_changes_integrated`
- `human_script_approval_for_audio_read`: `pass`
- `script_audio_source_integrity_read`: `pass_rerendered_from_post_critique_script`
- `human_audio_keep`: `keep`
- `episode_package_gate_status`: `keep_audio_opened_visual_system_planning`
- `may_advance_to_visual_system`: `false`
- `may_start_rough_assembly`: `false`
- `may_youtube_action`: `false`
- `public_release_ready`: `false`

## Resolved Blocker: Script Gate

Post-review policy correction on 2026-05-17: the earlier WAV was rendered before Claude/frontier-model script critique, critique integration, and explicit human approval of the final script for audio render.

That blocker is resolved for this rerender. The current WAV was rendered from the post-critique script SHA-256 `08ae7837e0f01ac9a281f631b9d678dcd27ed9186946a1a50bd685fa42db586a`.

Backfill note: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/script_gate_backfill_required_20260517.md`

## Script Gate Backfill Progress

- Claude critique: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/frontier_model_script_critique_claude_20260517.md`
- Claude critique SHA-256: `76b775ee8d46dde3a0705c31d31379fe11d59ca2446e5bbc83723ce05fe5f933`
- Integration note: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/script_gate_integration_note_20260517.md`
- Integration note SHA-256: `dbcea604821e8f118989079f706057cc7d69fe92b1cb78a96677d4d989cecde7`
- Post-critique script SHA-256: `08ae7837e0f01ac9a281f631b9d678dcd27ed9186946a1a50bd685fa42db586a`
- `frontier_model_script_critique_read`: `pass_with_tightening`
- `critique_integration_read`: `pass_required_changes_integrated`
- Human approval: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/human_script_approval_for_audio_20260517.md`
- Human approval SHA-256: `b936c469e69a338cba98bdb45e3dee220b273bf3f6822d9099a9536b1a6172c3`
- `human_script_approval_for_audio_read`: `pass`
- `script_audio_source_integrity_read`: `pass_rerendered_from_post_critique_script`

## Review Ask

The audio gate is kept. The active review ask has moved to the Visual System Plan:

- Visual System Plan: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/visual_system_plan_20260517.md`
- Choose `keep visual system`, `tighten visual system`, or `reject visual system`.

## Human Audio Keep

- Keep note: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/human_audio_keep_20260517.md`
- Keep note SHA-256: `c8cc07e436884672e3d5c461b1913662f1362f52af0a530990648fec882fa7b7`
- Disposition: `keep`

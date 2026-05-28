# Piltdown Man Long-Form Audio Handoff

Date: 2026-05-18

Workflow: `long_form_video_production_v1`

Purpose: define the exact audio render lane once the human script approval gate passes.

This is a handoff note only. It does not render audio, approve audio, mark audio keep, approve visual-system planning, authorize upload, or authorize public release.

## Required Input

- Post-integration script: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/Ep6_Piltdown-Man.txt`
- Script SHA-256: `b9993d242adcef5352b372f9e3168749c6b513024ca0f566ea6b488ac35c5b5c`
- Script word count: `1982`
- Fact-check report: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/fact_check.md`
- Fact-check SHA-256: `0ccd013ac21bdd95f2e3a6bd074966199a343e4af4c379431140d9dd9da128d1`
- Critique artifact: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/frontier_model_script_critique_gpt5_20260518.md`
- Integration note: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/script_gate_integration_note_20260518.md`
- Human script approval: `missing`

## Audio Lane

- Pipeline alias: `ep6_piltdownman_production`
- Pipeline directory: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production`
- Voice profile id: `longform_mike_v1`
- Provider: `elevenlabs`
- Model: `eleven_multilingual_v2`
- Voice id: `dPrTCMw2R7HQlznlgwCO`
- Render settings: `stability=0.6`, `similarity_boost=0.8`, `style=0.0`, `use_speaker_boost=true`, `speed=0.95`
- Voice profile final-export eligibility: `false`
- Lane type: `long_form`

## Expected Outputs After Approval

- Voice master WAV: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/final/Ep6_Piltdown-Man.wav`
- Audio package manifest: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/audio_package.json`
- Transcript package under `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/transcripts_mastered/`
- Timing source: WhisperX JSON plus VTT/SRT sidecars when available
- Plain transcript for review
- Human audio review note with `keep`, `tighten`, or `reject`

## Caption Policy

Future Living Cover visible captions must be generated from the post-integration script text. ASR, WhisperX, VTT, and SRT outputs may supply timing only.

Required downstream reads after timing exists:

- `caption_text_matches_script_read`
- `caption_alignment_coverage_read`
- `caption_asr_text_not_used_read`
- `caption_known_regression_fixture_read`

## Blocker Cleared When

The Episode Package Gate can be rebuilt as `review_ready` only after explicit human script approval, audio render, transcript/timing provenance, artifact hashes, and human audio review exist.

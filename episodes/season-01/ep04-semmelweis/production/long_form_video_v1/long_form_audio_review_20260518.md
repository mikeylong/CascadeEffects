# Semmelweis Long-Form Audio Review

Date: 2026-05-18

Workflow: `long_form_video_production_v1`

Gate: `human_audio_review`

Disposition: `review_ready_human_keep_pending`

## Review Target

- Audio master: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/final/Ep4_Semmelweis.wav`
- Audio SHA-256: `bf7562029466226f6bf33d64829ea41712220e63e4c5f37918cff53ec0fa1ebf`
- Duration: `850.825578` seconds
- Runtime: `14:10.83`
- Size: `75042894` bytes
- Provider: `elevenlabs`
- Model: `eleven_multilingual_v2`
- Voice profile: `longform_mike_v1`
- Pipeline root: `/Users/mike/Audio_CascadeEffects/tmp/ep4_semmelweis_longform_20260518T193358Z`

## Source Integrity

- Human script approval for audio: `pass`
- Approved script SHA-256: `2bca08c0899da81a909d550a76dc0e2cb6ddccaa764b8c45ad9298c918276d68`
- Audio package: `/Users/mike/Audio_CascadeEffects/tmp/ep4_semmelweis_longform_20260518T193358Z/audio_package.json`
- Audio package SHA-256: `85363c7667fe1a99adffc350de164700ef3306a44f9449dce3c86a4f86b59096`
- Source-integrity report: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/audio_source_integrity_report_20260518.json`

## Pipeline Reads

- Pronunciation preflight: `pass_no_matches_no_blockers`
- Pronunciation lexicon SHA-256: `cd2e28043e1d04baf159101859d8a566f2cc14ee49b0300d1ee4c5c2dc2e9800`
- Applied pronunciation rule ids: none
- Prosody guard: `ok_no_repairs`
- Rendered chunks: `5`
- Mastered transcript: `/Users/mike/Audio_CascadeEffects/tmp/ep4_semmelweis_longform_20260518T193358Z/transcripts_mastered/Ep4_Semmelweis.diarized.txt`
- Caption timing source: `/Users/mike/Audio_CascadeEffects/tmp/ep4_semmelweis_longform_20260518T193358Z/transcripts_mastered/Ep4_Semmelweis.diarized.srt`
- WhisperX JSON: `/Users/mike/Audio_CascadeEffects/tmp/ep4_semmelweis_longform_20260518T193358Z/transcripts_mastered/Ep4_Semmelweis.whisperx.json`

## Human Review Checklist

- Listen for obvious pronunciation errors, especially names, places, medical terms, and long/short vowel ambiguity.
- Listen for broken emphasis, unnatural pauses, clipped words, duplicated words, or missing words.
- Check whether the pace is comfortable for a 14-minute long-form audio essay.
- Confirm whether the audio should be marked `keep`, repaired, or rerendered.

## Gate Boundary

This packet does not mark the audio `keep`.

The Visual System Gate, rough assembly, final MP4 render, YouTube upload, and public release remain blocked until a human audio-review disposition marks this exact audio master `keep`.

`may_advance_to_visual_system`: `false`

`may_start_rough_assembly`: `false`

`may_render_final_mp4`: `false`

`may_youtube_action`: `false`

`public_release_ready`: `false`

# Tacoma Narrows Long-Form Audio Handoff

Date: 2026-05-16

Workflow context: `long_form_video_production_v1`

Purpose: unblock the Episode Package Gate by creating or promoting a current long-form voice master and timing source from the locked Tacoma script.

This is a handoff note only. It does not render audio, replace an approved master, publish, upload, or authorize use of the Shorts audio lane for long-form output.

Post-review correction on 2026-05-17: a locked script alone does not authorize long-form audio rendering. Before any long-form script goes to ElevenLabs or another TTS provider, the exact script revision must have frontier-model critique, critique integration or explicit deferral, and human approval for audio. The existing Tacoma WAV is diagnostic/review-only until that gate is backfilled.

## Required Input

- Locked script: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/Ep5_Tacoma-Narrows.txt`
- Locked script SHA-256: `60c949d26a3abbd95ece31e9dc27ebb33fd967d4c9704e72fe23ad26ee938a84`
- Fact-check report: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/fact_check.md`
- Fact-check SHA-256: `9b772a9420e0f9609e6eaf98c4840351ce94fb17c0466eb51db402a3e7fe09b4`
- Script word count: `1958`

## Expected Outputs

- Voice master WAV: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/final/Ep5_Tacoma-Narrows.wav`
- Audio package manifest with path, SHA-256, duration, peak/loudness, voice/model/provenance, and script hash
- Timing transcript package with at least one machine-readable timing source for caption alignment, preferably WhisperX JSON plus VTT/SRT
- Plain transcript for review
- Human audio review note with `keep`, `tighten`, or `reject`

## Long-Form Caption Requirements

The eventual Living Cover caption package must use the locked script text for visible captions. ASR, WhisperX, VTT, and SRT outputs may provide timing only.

Required downstream reads after timing exists:

- `caption_text_matches_script_read`
- `caption_alignment_coverage_read`
- `caption_asr_text_not_used_read`
- `caption_known_regression_fixture_read`

## Performance Notes

The script contains bracketed performance tags such as `[calm]`, `[sorrowful]`, `[matter-of-fact]`, `[deliberate]`, and `[flatly]`. These tags are direction for performance and should not appear as spoken narration or visible captions.

The tonal spine is calm technical grief: not disaster spectacle, not gotcha engineering, and not a freak-storm myth. The core idea is the edge of a trusted model.

## Blocker Cleared When

The Episode Package Gate can be rebuilt as `review_ready` only after frontier-model script critique, critique integration or explicit deferral, human script approval for audio, a current voice master, and timing package exist, have hashes recorded, and pass human audio review.

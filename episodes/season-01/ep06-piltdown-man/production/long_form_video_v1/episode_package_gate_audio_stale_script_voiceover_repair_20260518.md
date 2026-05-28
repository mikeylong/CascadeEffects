# Episode Package Gate - Piltdown Man Voiceover Naming Repair

Date: 2026-05-18

## Disposition

`blocked_audio_stale_after_script_repair`

The Piltdown long-form script has been updated for cleaner voiceover naming of the Natural History Museum. The script revision is valid and fact-check-backed, but the previously rendered audio no longer matches the current script.

## Current Canonical Source

- Script path: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/Ep6_Piltdown-Man.txt`
- Script SHA-256: `dca919591b0db8c99c3124f8ba794944daaf9b4c09a9e364d7d36d2fb816ddbf`
- Script word count: `1974`
- Fact-check path: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/fact_check.md`
- Fact-check SHA-256: `16d0065b87773371412d52ba04c9bf707c9e53fd498ace9c9d6816fec7b13acd`
- Series-bible mechanism: `authority protects the flattering lie`

## Delta Reads

- Delta critique: `pass_with_audio_rerender_required`
- Delta critique path: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/frontier_model_script_critique_delta_gpt5_voiceover_naming_20260518.md`
- Script repair integration: `pass_script_revised_audio_stale`
- Script repair path: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/script_voiceover_naming_repair_20260518.md`
- Audio stale note: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/audio_stale_after_script_voiceover_repair_20260518.md`

## Updated Audio Render Inputs

- Final TTS jobs: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/final_jobs_voiceover_repair_20260518.jsonl`
- Final TTS jobs SHA-256: `e6e6acd0f319f44460e2e238da40a3d0749b96712776e5e95566f110cd7649aa`
- Effective ElevenLabs manifest: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/effective_final_jobs_voiceover_repair_20260518.elevenlabs.jsonl`
- Effective ElevenLabs manifest SHA-256: `cc22cba6c2a92f1ac5a254e0ca6dc3ac1e0785a220433534a5a061f704484520`
- Strict source alignment: `pass`
- Pronunciation preflight: `pass`
- Rerender performed: `false`

## Stale Audio

- Stale WAV: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/final/Ep6_Piltdown-Man.wav`
- Stale WAV SHA-256: `f9411d5bdffa2d5463497f7874d1931c7d90a12b67d6dafc917fabe648a5f552`
- Rendered-from script SHA-256: `b9993d242adcef5352b372f9e3168749c6b513024ca0f566ea6b488ac35c5b5c`
- Current script SHA-256: `dca919591b0db8c99c3124f8ba794944daaf9b4c09a9e364d7d36d2fb816ddbf`

## Gate State

- Human script approval for rerender: `missing`
- Current audio source integrity: `missing_pending_rerender`
- Current timing provenance: `missing_pending_rerender`
- Human audio keep: `blocked_audio_stale`
- May advance to visual system: `false`
- May start source-art generation: `false`
- May start rough assembly: `false`
- May render final MP4: `false`
- May prepare upload package: `false`
- May perform YouTube action: `false`
- Public release ready: `false`

## Next Required Gate

Mike must explicitly approve revised script SHA-256 `dca919591b0db8c99c3124f8ba794944daaf9b4c09a9e364d7d36d2fb816ddbf` for audio rerender. After rerender, regenerate audio source integrity, transcript/SRT/VTT/WhisperX timing provenance, and the human audio review note.

# Script Voiceover Naming Repair - Piltdown Man

Date: 2026-05-18

## Disposition

`pass_script_revised_audio_stale`

Mike flagged that repeated spoken use of `British Museum (Natural History)` sounded odd in voiceover. The script now uses a smoother first-reference phrase and avoids repeating the parenthetical.

## Edit Summary

Changed five spoken references:

- `the British Museum (Natural History) in London` -> `the London museum we now call the Natural History Museum`
- `the British Museum (Natural History)` -> `that museum's scientists`
- `Keeper of Geology at the British Museum (Natural History)` -> `the museum's Keeper of Geology`
- `prominent figures at the British Museum (Natural History)` -> `prominent figures at the museum`
- `The British Museum (Natural History)'s endorsement` -> `The museum's endorsement`

## Hashes

- Prior script SHA-256: `b9993d242adcef5352b372f9e3168749c6b513024ca0f566ea6b488ac35c5b5c`
- Revised script SHA-256: `dca919591b0db8c99c3124f8ba794944daaf9b4c09a9e364d7d36d2fb816ddbf`
- Revised tracked word count: `1974`
- Revised narration-token count, cue tags stripped: `1928`
- Updated fact-check SHA-256: `16d0065b87773371412d52ba04c9bf707c9e53fd498ace9c9d6816fec7b13acd`
- Updated final TTS jobs: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/final_jobs_voiceover_repair_20260518.jsonl`
- Updated final TTS jobs SHA-256: `e6e6acd0f319f44460e2e238da40a3d0749b96712776e5e95566f110cd7649aa`
- Updated effective ElevenLabs manifest: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/effective_final_jobs_voiceover_repair_20260518.elevenlabs.jsonl`
- Updated effective ElevenLabs manifest SHA-256: `cc22cba6c2a92f1ac5a254e0ca6dc3ac1e0785a220433534a5a061f704484520`

## Validation

- Formal phrase remains in spoken script: `0`
- TTS manifest validation: `pass`
- Pronunciation preflight: `pass`, `jobs=5`, `matched=0`, `blockers=0`
- Strict source alignment: `pass`
- Spoken input matches revised locked script after normalization: `pass`
- Updated render estimate: `12182` chars, estimated `$2.4171`

## Gate Effect

This changes the script after the long-form WAV was rendered. The existing WAV and timing sidecars are now stale relative to the revised script. Do not mark the current audio `keep`; rerender only after explicit human approval of revised script SHA-256 `dca919591b0db8c99c3124f8ba794944daaf9b4c09a9e364d7d36d2fb816ddbf`.

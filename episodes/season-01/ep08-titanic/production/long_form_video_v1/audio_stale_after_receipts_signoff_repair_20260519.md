# Audio Stale After Receipts Sign-Off Repair - Titanic

Date: 2026-05-19

## Disposition

`stale_requires_full_rerender`

The current Titanic long-form WAV and timing sidecars were rendered from the previous script revision. The script now has a new terminal VO sign-off:

```text
[calm] The legend fades. The receipts remain.
```

The old audio contains:

```text
You already know the disaster. The record shows the mechanism.
```

## Stale Audio Package

- Previous script SHA-256: `38056564c66cb5249d02f37dffaf98c4acdea680465e1d9b93d01d06102e38cc`
- Previous WAV path: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/final/Ep8_Titanic.wav`
- Previous WAV SHA-256: `79253cadeae659aa74fcc2b2c32302d0483a9b1be2d6a3e69f97e367b2623a1f`
- Previous pipeline: `/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_longform_20260518`
- Previous timing provenance: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/long_form_audio_timing_provenance_20260518.md`
- Previous source integrity: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/audio_source_integrity_report_20260518.json`
- Previous human audio review note: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/human_audio_review_note_20260518.md`

## Required Repair

Rerender the full long-form audio from script SHA-256 `a5fb122223052b820f7dd832a7f9227db4780f9d4ffd810915e579bef1249dc3` using `longform_mike_v1`, then regenerate source integrity, timing provenance, transcript sidecars, human audio review note, package gate, manifest, and TOML state.

## Gate Effect

Until rerender and validation complete, audio cannot be marked `keep`. Visual-system planning, source art, rough assembly, final render, upload prep, YouTube actions, and public release remain blocked.

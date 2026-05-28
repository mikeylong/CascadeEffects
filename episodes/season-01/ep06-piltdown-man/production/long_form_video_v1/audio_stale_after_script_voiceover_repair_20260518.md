# Audio Stale Note - Piltdown Man Voiceover Naming Repair

Date: 2026-05-18

## Disposition

`stale_script_revised_after_render`

The current Piltdown long-form WAV was rendered before the museum-naming voiceover repair. It is no longer current against the locked script.

## Stale Audio Asset

- WAV path: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/final/Ep6_Piltdown-Man.wav`
- WAV SHA-256: `f9411d5bdffa2d5463497f7874d1931c7d90a12b67d6dafc917fabe648a5f552`
- Duration: `846.553107` seconds
- Rendered-from script SHA-256: `b9993d242adcef5352b372f9e3168749c6b513024ca0f566ea6b488ac35c5b5c`
- Current script SHA-256: `dca919591b0db8c99c3124f8ba794944daaf9b4c09a9e364d7d36d2fb816ddbf`

## Reason

The rendered audio still contains the old spoken wording `British Museum (Natural History)`. The script now uses `the London museum we now call the Natural History Museum` on first reference and shorter `the museum` references after that.

## Gate Effect

- Audio review status: `blocked_audio_stale`
- Human audio `keep`: `blocked`
- Audio source integrity for current script: `missing_pending_rerender`
- Caption/timing provenance for current script: `missing_pending_rerender`
- Visual-system planning: `blocked`
- Rough assembly: `blocked`
- Final MP4: `blocked`
- YouTube action: `blocked`

## Next Action

Capture explicit human approval for revised script SHA-256 `dca919591b0db8c99c3124f8ba794944daaf9b4c09a9e364d7d36d2fb816ddbf`, then rerender long-form audio through `ep6_piltdownman_production` and regenerate timing provenance.

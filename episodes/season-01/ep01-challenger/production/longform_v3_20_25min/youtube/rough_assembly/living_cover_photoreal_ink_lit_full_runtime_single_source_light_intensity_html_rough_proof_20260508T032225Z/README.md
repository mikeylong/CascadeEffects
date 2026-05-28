# Challenger Living Cover Single-Source Light Intensity HTML Rough Proof

Review-only full-runtime HTML rough proof.

This packet supersedes the single-source opacity-ramp proof. It uses one approved source image layer and changes render-time lighting intensity with deterministic CSS filter values. There is no second image layer and no lit-overlay opacity reveal.

## Source

- Source image: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/living_cover_launch_pad_photoreal_ink_lit_crew_foreground_repair_20260504T215400Z/assets/source_art/living_cover_launch_pad_photoreal_ink_lit_crew_variant_c.png`
- Source SHA-256: `52f94150037d5aa40633d34b29c137c59c5868e987bc5f8b7f80903f6bc2ac8a`
- Local review reference: `references/living_cover_launch_pad_photoreal_ink_lit_crew_variant_c.png` symlinked to the approved source art.

## Light Intensity Ramp

- `0.000s` First Warning: `0.00`
- `89.384s` Cold Joint: `0.06`
- `183.497s` Joint Problem: `0.12`
- `338.105s` Warning Becomes Process: `0.22`
- `519.158s` Processed Warning: `0.35`
- `629.000s` Launch-Night Decision: `0.48`
- `808.000s` Recommendation Reversal: `0.68`
- `1082.561s` Routine Pressure: `0.88`
- `1289.131s` End: `1.00`

The ramp drives brightness, contrast, and saturation from the dark start toward the approved lit state. `window.__lightIntensityAt(time)`, `window.__lightFilterAt(time)`, and `window.__setRenderTime(time)` are available for deterministic review and future render QA.

## Preserved

- fixed `1920x1080` canvas
- `760px` right rail
- native `40px` WebVTT/TextTrack rail captions
- staged `120/360/600ms` rail transitions
- approved audio/caption/transcript references by symlink only
- frozen Challenger rail/caption timing model

No MP4 render, final assembly, Shorts work, publish readiness, or YouTube action is authorized.

## Human Review Update

- Disposition: `reject`
- Reviewer note: use ImageGen to create two separately rendered plates; the CSS/filter proof is dimming, not separate lighting-source intensity renders.
- Downstream gates remain locked: no MP4 render, final assembly, Shorts, publish readiness, or YouTube action.

# Caption Text Policy Block

Package summary:
`/Users/mike/Episodes_CascadeEffects/Shorts_Publish_Readiness/all_eight_publish_readiness_summary_20260521T070556Z.json`

Status: `not_publish_ready_caption_text_policy`

The `20260521T070556Z` all-eight yellow-caption packages remain useful as evidence for the visual caption-style repair and Challenger/Hyatt duplicate-caption repair, but they must not advance to upload validation as keeper publish packages.

Blocking reason: the package builder used audio-package transcript/ASR text as the caption word source. Shorts publish readiness now requires `script_locked_canonical_text_timing_from_asr_v1`: locked script words for burned-in captions and YouTube/player sidecars, with WhisperX/ASR timing evidence only.

Required repair before upload validation:

- locate or create locked short-script caption text sources for all eight Shorts
- regenerate script-locked SRT/timing/QA artifacts
- rebuild local publish-ready packages with captions as the final visual layer
- pass `publish-package-check` with script-locked caption provenance fields

YouTube action: none. No upload, publish, delete, replace, schedule, or visibility change occurred.

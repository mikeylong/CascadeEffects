# 737 MAX Review HTML Caption Source Repair

- Episode: `737-max`
- Workflow: `long_form_video_production_v1`
- Artifact: local lifecycle `review.html`
- Disposition on prior page: `tighten`
- Prior review HTML path: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/review.html`
- Prior review HTML SHA-256: `c5227a933a1754d5da404bc9dc22bcc753fc8c72c1a9a129c960b7ddaabcebfa`

## Tighten Reasons

- `asr_text_used_as_visible_caption_source`: the page loaded `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/review_assets/captions/Ep7_737-MAX.diarized.vtt` for visible rail caption text.
- `caption_eyebrow_visible`: the Living Cover caption slot showed a viewer-facing `Caption` eyebrow label.

## Repair

- Generated script-locked rail captions from `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/Ep7_737-MAX.txt`.
- Used `/Users/mike/Audio_CascadeEffects/tmp/transcripts_final/Ep7_737-MAX.whisperx.json` as timing evidence only.
- Updated the native audio `<track>` and visible rail-caption parser to use `737_max_longform.script_locked_rail_safe.vtt`.
- Removed the viewer-facing `Caption` eyebrow from the rail.

## Gate State

- Current gate remains `living_cover_cue_map_keep`.
- Required next action remains `human_living_cover_cue_map_keep_or_tighten_reject`.
- No ambient/effects layer, music contract, rough assembly, final render, YouTube action, or public-release action is opened by this repair.

# Tacoma Narrows Long-Form Episode Package Gate

Date: 2026-05-16

Workflow: `long_form_video_production_v1`

Gate: `episode_package`

Status: `blocked_missing_long_form_audio`

This packet opens the episode package surface from the locked script, but it is not review-ready for visual-system approval because the current long-form audio master and timing transcript are missing.

## Current Script Read

- Locked script path: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/Ep5_Tacoma-Narrows.txt`
- Locked script SHA-256: `60c949d26a3abbd95ece31e9dc27ebb33fd967d4c9704e72fe23ad26ee938a84`
- Word count: `1958`
- Estimated spoken duration: roughly `12-15 minutes`, depending on final narration pace

## Mechanism And Promise

- Mechanism: `Unknown force domain / margin removed`
- Promise: the bridge did not meet extraordinary wind; it met an aerodynamic behavior its own design made possible and its design process had not yet formalized.
- What changed: a familiar vertical undulation became large torsional motion and self-excited aerodynamic instability.
- Who failed to recognize the change: the design process and profession had not yet made dynamic aerodynamic investigation routine for very flexible long-span bridge decks.
- How the system converted blindness into consequence: visible abnormal motion became spectacle and a manageable peculiarity before the catastrophic mode arrived.

## Draft Chapter Spine

These are production anchors only. They are not timed YouTube chapters until the long-form audio master and caption timing exist.

| Order | Function | Draft viewer-facing chapter label | Script anchor |
| --- | --- | --- | --- |
| 1 | Cold open | The Bridge Was Already Moving | Collapse, ordinary wind, and the feedback cycle |
| 2 | Identity hit | The Boundary Of A Model | Not a freak storm; known-force design met an unmodeled force domain |
| 3 | Chapter | The Design That Got Built | Eldridge's deep truss, Moisseiff's shallow plate girders, cost and slenderness |
| 4 | Chapter | Galloping Became Normal | Public spectacle, Farquharson studies, remedies under consideration |
| 5 | Chapter | Five Conditions Before The Cable Was Spun | Economy, static wind assumptions, spectacle, missing dynamic tests, torsional feedback |
| 6 | Chapter | The Air Fed The Twist | Self-excited torsional flutter and the limits of the resonance myth |
| 7 | Chapter | The Profession Changed | Carmody Board, wind-tunnel testing, deeper open truss replacement bridge |
| 8 | Synthesis / outro | The Model Stopped Matching The World | Failure as the edge of a trusted framework; next design failure setup |

## Visual Direction Seed

The long-form visual-system plan should start from the episode's public anchor and the series row:

- archival bridge footage
- airflow overlays
- deck-motion line traces
- slenderness diagram

This does not authorize visible procedural overlays over source imagery. Any airflow, trace, or diagram treatment must be approved in the visual-system plan and kept source-safe under `living_cover_system_v1`.

## Existing Short Bridge

- Bridge asset: pass-07 CRT visible scanline Short
- Status: `keep`
- Path: `/Users/mike/Viz_CascadeEffects/references/episodes/tacoma-narrows/shorts/tacoma_short_scoped_v1/motion_video_proof/pass_01_source_led/final_exports/tacoma-narrows_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/20260429T_house_crt_visible_scanline_first8_pass07_y24/final/tacoma-narrows__house_crt_visible_scanline_signal_interruption_captioned_final.mp4`
- SHA-256: `ebecebef84bde5e915d4b4927f655128712f17545d89a36ca19a260e992c9ded`
- Publish status: pass-07 publish package not rebuilt; upload and public release remain blocked.

## Blockers

- `long_form_audio_master_read`: `reject_missing`
- `caption_timing_source_read`: `reject_missing`
- `caption_text_matches_script_read`: `blocked_missing_timing_package`
- `caption_alignment_coverage_read`: `blocked_missing_timing_package`
- `caption_asr_text_not_used_read`: `blocked_missing_caption_builder_output`
- `visual_system_plan_read`: `blocked_pending_audio_and_episode_package_keep`
- `living_cover_cue_map_read`: `blocked_pending_visual_system_keep`
- `living_cover_ambient_effects_layer_read`: `blocked_pending_visual_system_keep`
- `rough_assembly_read`: `blocked_pending_audio_visual_system_cue_map_and_ambient_effects_layer`

## Next Required Action

Generate or promote the Tacoma long-form audio master at `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/final/Ep5_Tacoma-Narrows.wav`, create transcript/timing provenance, then rebuild this episode package as `review_ready`.

`may_advance_to_visual_system`: `false`

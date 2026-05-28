# 737 MAX Long-Form Inventory Gate

Date: 2026-05-18

Workflow: `long_form_video_production_v1`

Gate: `inventory`

Disposition: `keep_opened_for_package_audio_gate`

## Current State

- Locked compact long-form script: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/Ep7_737-MAX.txt`
- Script SHA-256: `3f95aaf72b3144f0c33ee85e77d18140a888ba97c46eb89b0cfaad5c61a7c718`
- Script word count: `2166`
- Fact-check report: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/fact_check.md`
- Fact-check SHA-256: `b779727882ff6a09a6dd6d4d0a088980b010d5a40dc0d69a88d1f5dcfdd493e5`
- Existing 737 Short private review URL: `https://www.youtube.com/watch?v=mxIr64N-4HE`
- Long-form audio status before this gate: `todo`
- Long-form audio target: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/final/Ep7_737-MAX.wav`
- Audio pipeline directory: `/Users/mike/Audio_CascadeEffects/tmp/ep7_737max_production`

## Gate Reads

- `inventory_gate_read`: `pass`
- `short_bridge_read`: `pass_private_review_uploaded_bridge_only`
- `long_form_audio_read`: `missing`
- `canonical_closer_read`: `pass_challenger_therac_hyatt_precedent`
- `next_gate`: `episode_package_script_audio_authorization`
- `may_advance_to_audio_render`: `false_pending_script_gate`

## Boundary

The existing Short is a bridge asset only. It does not authorize long-form audio, visual-system planning, YouTube upload, schedule, or public release.

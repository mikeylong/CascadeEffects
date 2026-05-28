# Semmelweis Long-Form Episode Package Gate

Date: 2026-05-18

Workflow: `long_form_video_production_v1`

Gate: `episode_package`

Disposition: `blocked_missing_human_audio_approval_and_long_form_audio`

## Package Summary

Semmelweis is now selected as the next canonical long-form episode after Hyatt, matching the first-eight slate. The locked script and fact-check are present, and the frontier critique returned `pass_no_script_changes`, but the long-form audio gate is not open until human audio approval, audio render, and timing provenance exist.

This packet does not authorize audio render, Living Cover visual-system work, rough assembly, final MP4 render, publish-readiness packaging, YouTube upload, or public release.

## Current Source Reads

- Script path: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/Ep4_Semmelweis.txt`
- Script SHA-256: `2bca08c0899da81a909d550a76dc0e2cb6ddccaa764b8c45ad9298c918276d68`
- Script word count: `1955`
- Script status: `locked`
- Fact-check report: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/fact_check.md`
- Fact-check SHA-256: `e4adaa25f8b09b96c5f6c58c0758e7c476fc64b5b90b830e960fd71ee3663ace`
- Frontier-model critique: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/frontier_model_script_critique_claude_20260518.md`
- Frontier-model critique SHA-256: `60ebbf0f8256f9be9bcca010c5d22410100be84a9dcf840f20cda68649952dd1`
- Critique integration note: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/script_gate_integration_note_20260518.md`
- Critique integration SHA-256: `9007ef64018e3d17100dd8e7994bec2628d00bb9c0f84622de1bf47a276f187b`
- Human script approval for audio: `missing`
- Long-form audio master: `missing`
- Long-form timing source: `missing`

## Mechanism And Promise

- Mechanism: `Evidence rejected because identity is threatened`
- Promise: Semmelweis shows how a hospital could measure a life-saving intervention and still reject it because accepting the result meant accepting that physicians were part of the cause.
- What changed: documented mortality differences became an intervention result after chloride-of-lime handwashing.
- Who failed to recognize the change: the medical institution and professional authority structure that could not accept the implication of the data.
- How blindness became consequence: evidence was held below theory and professional dignity, delaying adoption of a practice that had already reduced deaths.

## Draft Chapter Spine

| Order | Function | Viewer-facing chapter label | Production anchor |
| --- | --- | --- | --- |
| 1 | Cold open | The Ward Had The Numbers | Vienna maternity mortality gap and the visible problem |
| 2 | Identity hit | The Data No One Wanted | First and Second Division contrast |
| 3 | Chapter | The Difference Was In The Hands | Autopsy-room contact and Kolletschka's death |
| 4 | Chapter | The Wash Changed The Ledger | Chloride-of-lime intervention and mortality drop |
| 5 | Chapter | Evidence Without A Theory | Germ-theory gap and professional objections |
| 6 | Chapter | The Accusation Inside The Cure | Why acceptance implicated physicians |
| 7 | Synthesis / outro | The Result Was Visible First | Identity-protective rejection as the cascade mechanism |

## Existing Short Bridge

- Short id: `semmelweis_short_scoped_v1`
- Current state: pass-07 CRT visible scanline review candidate exists, but final human keep and current publish-package rebuild are not confirmed for long-form bridge use.
- Role: bridge/discovery candidate only; do not use it as the long-form production source of truth.

## Gate Reads

- `long_form_script_read`: `pass_locked_script_present`
- `fact_check_read`: `pass_fact_check_present`
- `frontier_model_script_critique_read`: `pass_no_script_changes`
- `critique_integration_read`: `pass_no_script_changes_required`
- `human_script_approval_for_audio_read`: `missing`
- `audio_source_integrity_read`: `missing`
- `long_form_audio_master_read`: `missing`
- `caption_timing_source_read`: `missing`
- `caption_text_source_read`: `pass_script_locked`
- `existing_short_bridge_read`: `available_not_promoted`
- `visual_system_plan_read`: `blocked_pending_audio_gate`
- `living_cover_cue_map_read`: `blocked_pending_audio_gate`
- `living_cover_ambient_effects_layer_read`: `blocked_pending_audio_gate`
- `music_integration_contract_read`: `blocked_pending_audio_gate`
- `rough_assembly_read`: `blocked_pending_audio_gate`
- `publish_readiness_read`: `blocked_no_final_assembly`

## Blockers

- Missing explicit human script approval for audio.
- Missing rendered/promoted long-form audio master.
- Missing transcript/timing provenance for script-locked Living Cover captions.

## Next Gate

Capture explicit human approval for audio, then render or promote a current long-form voice master and timing source. Only after that can the Episode Package Gate be reviewed for `keep` and visual-system planning.

`may_advance_to_visual_system`: `false`

`may_start_rough_assembly`: `false`

`may_render_final_mp4`: `false`

`may_youtube_action`: `false`

`public_release_ready`: `false`

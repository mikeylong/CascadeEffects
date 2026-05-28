# Semmelweis Long-Form Episode Package Gate

Date: 2026-05-18

Workflow: `long_form_video_production_v1`

Gate: `episode_package`

Disposition: `review_ready_audio_review_pending`

## Package Summary

Semmelweis is selected as the next canonical long-form episode after Hyatt. The locked script and fact-check are present, the frontier critique and integration gate passed with no script changes, explicit human script approval for audio was recorded, and a new long-form ElevenLabs master plus timing provenance now exist.

This packet opens human audio review only. It does not mark audio `keep`, does not open Living Cover visual-system work, and does not authorize rough assembly, final MP4 render, YouTube upload, or public release.

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
- Human script approval for audio: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/human_script_approval_for_audio_20260518.md`
- Human script approval SHA-256: `0d7056799521e3d9edbf50dd3018fc211f4efb3d6c8e38e257b86146022ca3dc`
- Audio source-integrity report: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/audio_source_integrity_report_20260518.json`
- Long-form audio master: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/final/Ep4_Semmelweis.wav`
- Long-form audio SHA-256: `bf7562029466226f6bf33d64829ea41712220e63e4c5f37918cff53ec0fa1ebf`
- Long-form audio duration: `850.825578` seconds
- Long-form transcript/timing source: `/Users/mike/Audio_CascadeEffects/tmp/ep4_semmelweis_longform_20260518T193358Z/transcripts_mastered/Ep4_Semmelweis.diarized.srt`
- Long-form timing source SHA-256: `f09cae647f2aadfc6354bd6cc04c23630e8464cb73ea07ae155536c08ad6f0e4`

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
- `human_script_approval_for_audio_read`: `pass`
- `audio_source_integrity_read`: `pass_review_ready_human_keep_pending`
- `long_form_audio_master_read`: `review_ready_human_keep_pending`
- `caption_timing_source_read`: `review_ready`
- `caption_text_source_read`: `pass_script_locked`
- `pronunciation_preflight_read`: `pass_no_matches_no_blockers`
- `prosody_guard_read`: `ok_no_repairs`
- `existing_short_bridge_read`: `available_not_promoted`
- `visual_system_plan_read`: `blocked_pending_human_audio_keep`
- `living_cover_cue_map_read`: `blocked_pending_human_audio_keep`
- `living_cover_ambient_effects_layer_read`: `blocked_pending_human_audio_keep`
- `music_integration_contract_read`: `blocked_pending_human_audio_keep`
- `rough_assembly_read`: `blocked_pending_human_audio_keep`
- `publish_readiness_read`: `blocked_no_final_assembly`

## Next Gate

Human audio review must mark the exact audio master `keep` or request repairs. Only after a `keep` disposition can the Visual System Gate open.

`may_advance_to_visual_system`: `false`

`may_start_rough_assembly`: `false`

`may_render_final_mp4`: `false`

`may_youtube_action`: `false`

`public_release_ready`: `false`

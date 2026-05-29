# ElevenLabs/TTS Preflight Template

episode_id:
script_path:
script_sha256_reviewed:
script_revision_context:
tts_provider: ElevenLabs or current approved TTS provider
voice_or_model_context:
status: pass | tighten | blocked
may_advance: false
human_gate_required: true

## Purpose

Find wording, pronunciation, punctuation, and cadence risks before TTS render so the team does not discover avoidable fixes after an ElevenLabs render.

## Required Reads

- `script_hash_match_read`: pass | tighten | blocked
- `pronunciation_ledger_read`: pass | tighten | blocked
- `acronym_initialism_read`: pass | tighten | blocked
- `names_places_entities_read`: pass | tighten | blocked
- `numbers_dates_units_read`: pass | tighten | blocked
- `homograph_ambiguity_read`: pass | tighten | blocked
- `technical_mouthful_read`: pass | tighten | blocked
- `punctuation_pause_breath_read`: pass | tighten | blocked
- `repeated_cadence_read`: pass | tighten | blocked
- `elevenlabs_rework_risk_read`: pass | tighten | blocked

## Pronunciation Ledger

List every likely pronunciation-sensitive token, the intended reading, and the handling plan. Include names, places, acronyms, registrations, numbers, dates, units, abbreviations, and technical terms.

| Token | Intended Read | Handling Plan | Status |
| --- | --- | --- | --- |

## Script Changes

Record every wording, spelling, punctuation, or line-break change made for TTS reliability.

| Location | Issue | Change | Reason |
| --- | --- | --- | --- |

## Remaining Risks

Name any unresolved line that could force TTS rework or re-recording. If any item remains, status must be `tighten` or `blocked`, and `elevenlabs_preflight_read` must not pass.

## Audio Gate

Human script approval for audio remains pending until this preflight is passing for the exact script hash. Audio render remains unauthorized unless `frontier_model_script_critique_read`, `critique_integration_read`, `elevenlabs_preflight_read`, and `human_script_approval_for_audio_read` all pass for the same script revision.

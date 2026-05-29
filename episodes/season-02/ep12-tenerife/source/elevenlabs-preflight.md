# ElevenLabs/TTS Preflight: Tenerife

episode_id: ep12-tenerife
script_path: episodes/season-02/ep12-tenerife/source/longform-script.md
script_sha256_reviewed: 1ee98a0861185540a5aa137c4ed5d48a7ffdd18078040446efe0f1e6750e91eb
script_revision_context: post-critique-integration longform script
tts_provider: ElevenLabs or current approved TTS provider
voice_or_model_context: not selected; preflight is text-only and does not authorize audio render
status: pass
may_advance: false
human_gate_required: true

## Purpose

Find wording, pronunciation, punctuation, and cadence risks before TTS render so the team does not discover avoidable fixes after an ElevenLabs render.

## Required Reads

- `script_hash_match_read`: pass
- `pronunciation_ledger_read`: pass
- `acronym_initialism_read`: pass
- `names_places_entities_read`: pass
- `numbers_dates_units_read`: pass
- `homograph_ambiguity_read`: pass
- `technical_mouthful_read`: pass
- `punctuation_pause_breath_read`: pass
- `repeated_cadence_read`: pass
- `elevenlabs_rework_risk_read`: pass

## Helper / Lexicon Read

- Helper: `packages/media-pipeline/audio/scripts/pronunciation_preflight.py scan`
- Lexicon: `packages/media-pipeline/audio/references/pronunciation/known_risks_v1.json`
- Lexicon SHA-256: `3bbd0ab315d1afc8913f5684c728b89096536c921459d96edbb100311b61f861`
- Result: 1 script job scanned, 1 known-risk match, 0 blockers
- Matched rule: `faa_letters` for `FAA`; this appears in the non-narration review notes. If those notes are ever included in provider text, render as `F A A`.

## Pronunciation Ledger

| Token | Intended Read | Handling Plan | Status |
| --- | --- | --- | --- |
| Tenerife | ten-uh-REEF | Use the standard English narration read; avoid "TEE-nuh-rife." | pass |
| Los Rodeos | lohs roh-DAY-ohs | Place-name review target; keep the middle stress on Rodeos. | pass |
| KLM | K L M | Spell as letters, not as a word. | pass |
| KLM 4805 | K L M four eight zero five | Prefer flight-number digits in provider text if the voice model reads `4805` as a cardinal number. | pass |
| Pan Am | Pan Am | Read as two words. | pass |
| Pan Am 1736 | Pan Am seventeen thirty-six | Public narration read is acceptable; avoid "one thousand seven hundred thirty-six." | pass |
| March 27, 1977 | March twenty-seventh, nineteen seventy-seven | Date is stable; no alias required if the provider reads dates normally. | pass |
| 747s | seven forty-sevens | Aircraft family plural; use provider alias if raw digits become "seven hundred forty-sevens." | pass |
| Las Palmas | lahs PAL-mahs | Place-name review target; do not anglicize as "palm-us." | pass |
| ATC | A T C | Spell as letters. | pass |
| route clearance | route clearance | Keep as aviation clearance phrase; either common English route vowel is acceptable, but do not blur with takeoff clearance. | pass |
| takeoff clearance | takeoff clearance | Compound aviation phrase; no alias required. | pass |
| runway backtracking | runway backtracking | Technical phrase is clear in context. | pass |
| runway occupancy / runway-occupancy | runway occupancy | Hyphen only marks compound modifier; read as two words. | pass |
| phraseology / nonstandard phraseology | fray-zee-AH-luh-jee / nonstandard fray-zee-AH-luh-jee | Standard aviation-language term; no spelling alias required. | pass |
| simultaneous transmissions | simultaneous transmissions | Technical phrase is clear with surrounding commas. | pass |
| Crew Resource Management | Crew Resource Management | Read as the program name; no abbreviation unless the script uses `CRM`. | pass |
| CRM | C R M | Spell as letters. | pass |
| authority gradient | authority gradient | Safety term; read as a two-word phrase. | pass |
| flight engineer | flight engineer | Standard crew role; no alias required. | pass |
| KLM refueling | K L M re-FYOO-uh-ling | Spell KLM; read refueling naturally. | pass |
| duty-time pressure | duty time pressure | Hyphen only marks compound modifier; read as separate words. | pass |
| FAA | F A A | Helper-known required alias. Appears in review notes; if included in provider text, spell as letters. | pass |
| CVR | C V R | Appears only in review-note context; if included, spell as letters. | pass |
| C-3/C-4 | C three / C four | Appears in review notes; if included, read as taxiway/runway-exit labels. | pass |

## Script Changes

No script wording, spelling, punctuation, or line-break changes were made for this preflight.

| Location | Issue | Change | Reason |
| --- | --- | --- | --- |
| not applicable | No required TTS repair found. | None. | Existing script is suitable for human audio approval review with the pronunciation ledger carried into the render packet. |

## Risk Category Read

| Category | Read | Notes |
| --- | --- | --- |
| Pronunciation | pass | Episode-specific place names, aviation entities, and clearance terms are covered in the ledger. |
| Acronyms / initialisms | pass | KLM, ATC, CRM, FAA, and CVR should be spelled as letters when included in provider text. |
| Names / places / entities | pass | Tenerife, Los Rodeos, KLM, Pan Am, Las Palmas, and FAA Lessons Learned are identified. |
| Dates / numbers / units | pass | March 27, 1977, KLM 4805, Pan Am 1736, 747s, and C-3/C-4 have explicit intended reads. No measurement units require repair. |
| Homographs / ambiguity | pass | Reviewed `record`, `read back`, `close/closing`, `clear`, and `route`; context resolves each intended read. |
| Technical mouthfuls | pass | Long phrases such as `shared runway reality failed under radio ambiguity`, `route clearance versus takeoff clearance`, `nonstandard phraseology`, and `simultaneous transmissions` are intelligible with current punctuation. |
| Punctuation / pause / breath | pass | Paragraphs contain usable sentence breaks. Chapter headings may be read or omitted by the final audio packet, but production metadata and review notes should not be voiced. |
| Repeated cadence | pass | Repetition such as `It had become...`, `The danger was...`, and `It showed why...` is intentional rhetorical structure, not accidental TTS monotony. |

## Remaining Risks

No unresolved narration line appears likely to force ElevenLabs rework or re-recording after render if the audio packet carries this pronunciation ledger and excludes non-narration metadata/review notes from provider input.

The provider-specific handling plan is to spell KLM, ATC, CRM, FAA, and CVR as letters; normalize flight-number and aircraft-family reads where needed; and preserve place-name pronunciation for Tenerife, Los Rodeos, and Las Palmas.

## Audio Gate

Human script approval for audio remains pending until Mike or an approved human reviewer accepts this exact script hash for audio. Audio render remains unauthorized unless `frontier_model_script_critique_read`, `critique_integration_read`, `elevenlabs_preflight_read`, and `human_script_approval_for_audio_read` all pass for the same script revision.

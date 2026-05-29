# ElevenLabs/TTS Preflight: Apollo 13 Oxygen Tank Crisis

episode_id: ep09-apollo-13
script_path: episodes/season-02/ep09-apollo-13/source/longform-script.md
script_sha256_reviewed: e0c96b0312055be2c042c7cdddb9719638f98f3a3cb90eeac1dfc944ed987704
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
- Result: 1 script job scanned, 0 known-risk matches, 0 blockers

## Pronunciation Ledger

| Token | Intended Read | Handling Plan | Status |
| --- | --- | --- | --- |
| Apollo 13 | Apollo thirteen | Say number naturally as thirteen. | pass |
| Apollo 10 | Apollo ten | Say number naturally as ten. | pass |
| oxygen tank 2 / tank 2 | oxygen tank two / tank two | Say the numeral as two; do not read as "second" unless voice model naturally does so in title-like context. | pass |
| NASA | N A S A | Spell the agency initialism as letters, not "nah-sah." | pass |
| Mission Control | Mission Control | Standard phrase; title-case cadence should remain natural. | pass |
| Moon / Earth | Moon / Earth | Standard celestial nouns; no alias required. | pass |
| lunar module | lunar module | Standard Apollo hardware phrase; keep both words clear. | pass |
| command and service module | command and service module | Read as a phrase, not as separate program names. | pass |
| service module | service module | Standard Apollo hardware phrase. | pass |
| oxygen shelf | oxygen shelf | Read literally; do not compress into "O2 shelf." | pass |
| two inches | two inches | Read as words already; no numeric unit ambiguity. | pass |
| countdown demonstration test | countdown demonstration test | Technical phrase is long but clear in context. | pass |
| detanking / detanked | dee-tanking / dee-tanked | Pronounce as de-tanking, meaning removing propellant/oxygen from the tank. | pass |
| thermostatic switches | ther-mo-STAT-ic switches | Standard technical term; stress should be acceptable without alias. | pass |
| lower-voltage / higher voltage | lower voltage / higher voltage | Hyphen does not create a likely misread; read as voltage comparison. | pass |
| heater circuit | heater circuit | Standard phrase. | pass |
| weld closed | weld closed | "Closed" should read as shut, not near. Context is sufficient. | pass |
| oxygen-rich environment | oxygen-rich environment | Hyphenated technical phrase is clear; no alias required. | pass |
| Teflon | TEF-lon | Brand/material name; likely stable in ElevenLabs. | pass |
| cryogenic tanks | cryogenic tanks | Standard technical term; no alias required. | pass |
| fan-stir command / fan stir | fan stir | Hyphen marks compound modifier; intended read remains two words. | pass |
| telemetry | telemetry | Standard spaceflight term. | pass |
| combustion event | combustion event | Standard technical phrase. | pass |
| recovered-part autopsy | recovered part autopsy | Hyphen should not force a bad pronunciation; intended as a compound modifier. | pass |
| oxygen tank explosion | oxygen tank explosion | Quoted shorthand phrase; read normally. | pass |
| fuel cells / fuel-cell loss | fuel cells / fuel cell loss | Hyphen only marks modifier; read as two words. | pass |
| electrical power and water | electrical power and water | Standard resource chain phrase. | pass |
| thermal, navigation, communication, and operations problem | thermal, navigation, communication, and operations problem | List is long but punctuation gives clear beats. | pass |
| Apollo 13 Review Board | Apollo thirteen Review Board | Say Apollo number naturally; Review Board is title phrase. | pass |

## Script Changes

No script wording, spelling, punctuation, or line-break changes were made for this preflight.

| Location | Issue | Change | Reason |
| --- | --- | --- | --- |
| not applicable | No required TTS repair found. | None. | Existing script is suitable for human audio approval review. |

## Risk Category Read

| Category | Read | Notes |
| --- | --- | --- |
| Pronunciation | pass | Episode-specific technical tokens are listed above; no required local alias found. |
| Acronyms / initialisms | pass | NASA is the only agency acronym in the script and should be spelled as letters. |
| Names / places / entities | pass | Apollo 13, Apollo 10, NASA, Mission Control, Moon, Earth, and Apollo 13 Review Board are straightforward with ledger guidance. |
| Dates / numbers / units | pass | Numerals are limited and stable: Apollo 13, Apollo 10, tank 2, oxygen tank 2, and "two inches." No dates appear in the script body. |
| Homographs / ambiguity | pass | Reviewed "read," "closed," "object," "record," and "use/used"; local context should resolve each intended read. |
| Technical mouthfuls | pass | Long phrases are present but punctuated into spoken units; no phrase is likely to force re-render. |
| Punctuation / pause / breath | pass | Paragraphs are long in places, but sentence-level punctuation gives usable TTS breath points. |
| Repeated cadence | pass | Repetition such as "A power problem became..." and "The object changed..." is intentional rhetorical structure, not accidental monotony requiring script repair. |

## Remaining Risks

No unresolved line appears likely to force ElevenLabs rework or re-recording after render. The only provider-specific handling plan is to carry this ledger into the ElevenLabs render packet or pronunciation dictionary notes, especially for NASA, tank numerals, detanking, Teflon, cryogenic, and fan-stir phrases.

## Audio Gate

Human script approval for audio remains pending until Mike or an approved human reviewer accepts this exact script hash for audio. Audio render remains unauthorized unless `frontier_model_script_critique_read`, `critique_integration_read`, `elevenlabs_preflight_read`, and `human_script_approval_for_audio_read` all pass for the same script revision.

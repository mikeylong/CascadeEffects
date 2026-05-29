# ElevenLabs/TTS Preflight: Aberfan Disaster

episode_id: ep16-aberfan
script_path: episodes/season-02/ep16-aberfan/source/longform-script.md
script_sha256_reviewed: 3a2ae8e1c4469e5c85f52237ebb91f541cde65564ddc4cbbb55d773f6f6cab1c
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
| Aberfan | AB-er-van | Welsh place name; carry pronunciation note into render packet. | pass |
| Pantglas Junior School | PANT-glas Junior School | Keep as a proper school name; do not flatten into generic "pant glass." | pass |
| National Coal Board | National Coal Board | Read as full institution name; no acronym substitution needed. | pass |
| spoil tip / spoil tips | spoil tip / spoil tips | Mining waste term; read literally as "spoil," not "soil." | pass |
| colliery waste | COL-yuh-ree waste | Standard mining term; preserve the soft middle syllable. | pass |
| Tip 7 | tip seven | Read the numeral as seven. | pass |
| Institution of Civil Engineers | Institution of Civil Engineers | Full organization name; no initialism needed. | pass |
| ICE | I C E | If used in render notes, spell as letters; script body mostly uses the full name and "ICE account." | pass |
| October 21, 1966 | October twenty-first, nineteen sixty-six | Date appears in a narration sentence; read naturally. | pass |
| one hundred forty-four | one hundred forty-four | Words already avoid numeric ambiguity. | pass |
| one hundred sixteen | one hundred sixteen | Words already avoid numeric ambiguity. | pass |
| 1944 | nineteen forty-four | Year should not read as one thousand nine hundred forty-four. | pass |
| Mines and Quarries (Tips) Act 1969 | Mines and Quarries Tips Act, nineteen sixty-nine | Parenthetical should not create an awkward aside; read the act name smoothly. | pass |
| Lord Robens | Lord ROH-benz | Proper name; include pronunciation note for render prep. | pass |
| water-sensitive landscape | water sensitive landscape | Hyphen only marks modifier; read as a normal phrase. | pass |
| geotechnical | ge-oh-technical | Technical term is acceptable; keep clear stress. | pass |
| risk register | risk register | "Register" should read as a noun, not a verb. | pass |
| category changed / category shift | category changed / category shift | Repeated concept is intentional structure. | pass |
| natural-disaster framing | natural disaster framing | Hyphen should not force a clipped read. | pass |

## Script Changes

No script wording, spelling, punctuation, or line-break changes were made for this preflight.

| Location | Issue | Change | Reason |
| --- | --- | --- | --- |
| not applicable | No required TTS repair found. | None. | Existing script is suitable for human audio approval review. |

## Risk Category Read

| Category | Read | Notes |
| --- | --- | --- |
| Pronunciation | pass | Aberfan, Pantglas, colliery, Tip 7, Lord Robens, and statute names are captured in the ledger. |
| Acronyms / initialisms | pass | The script mainly spells out institutions; if ICE appears in narration, render as letters. |
| Names / places / entities | pass | Place, school, institution, tribunal, and law names are understandable with ledger notes. |
| Dates / numbers / units | pass | Dates and casualty counts are either written out or have explicit read guidance. |
| Homographs / ambiguity | pass | Reviewed "spoil," "tip," "register," "read," "record," "present," "does," and "close"; context resolves intended reads. |
| Technical mouthfuls | pass | Phrases like "water-sensitive landscape," "geotechnical lesson," and "institutional responsibility" are clear enough with existing punctuation. |
| Punctuation / pause / breath | pass | Short paragraphs and sentence breaks give sufficient breath points for TTS. |
| Repeated cadence | pass | The repeated "did not become" and "does... count?" constructions are intentional rhetorical beats, not accidental monotony requiring repair. |

## Remaining Risks

No unresolved line appears likely to force ElevenLabs rework or re-recording after render. Carry the ledger into the render packet or pronunciation notes, especially for Aberfan, Pantglas, colliery, Tip 7, ICE, Lord Robens, and the Mines and Quarries (Tips) Act 1969.

## Audio Gate

Human script approval for audio remains pending until Mike or an approved human reviewer accepts this exact script hash for audio. Audio render remains unauthorized unless `frontier_model_script_critique_read`, `critique_integration_read`, `elevenlabs_preflight_read`, and `human_script_approval_for_audio_read` all pass for the same script revision.

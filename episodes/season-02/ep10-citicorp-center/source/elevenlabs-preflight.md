# ElevenLabs/TTS Preflight: Citicorp Center Engineering Crisis

episode_id: ep10-citicorp-center
script_path: episodes/season-02/ep10-citicorp-center/source/longform-script.md
script_sha256_reviewed: 3353f2961ffddd6c24ffcfd6bc3ccec598a06b01126fc6e9decc507d7b74cd47
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
- Manifest handling: compact JSONL via process substitution; no episode script text was changed.
- Lexicon: `packages/media-pipeline/audio/references/pronunciation/known_risks_v1.json`
- Lexicon SHA-256: `3bbd0ab315d1afc8913f5684c728b89096536c921459d96edbb100311b61f861`
- Result: 1 script job scanned, 1 known-risk match, 0 helper blockers
- Matched rules: `wind_tunnel_hyphen_air_noun` required local alias and `wind_tunnel_air_noun_review` review marker
- Provider handling: apply the approved local alias to ElevenLabs render text for `wind-tunnel` so it is read as the air noun, `wind tunnel`; keep the locked script and captions unchanged.

## Pronunciation Ledger

| Token | Intended Read | Handling Plan | Status |
| --- | --- | --- | --- |
| Citicorp Center | City-corp Center | Keep as the building name; review for natural "city-corp" delivery, not "site-ih-corp." | pass |
| Midtown | midtown | Standard place descriptor; no alias required. | pass |
| St. Peter's church | Saint Peter's church | Expand `St.` as Saint in provider text if the TTS model reads the abbreviation too abruptly. | pass |
| Lexington Avenue | Lexington Avenue | Standard New York street name; no alias required. | pass |
| New York | New York | Standard place name; no alias required. | pass |
| chevron bracing | shev-ron bracing | Technical phrase is clear; keep the two-word beat. | pass |
| tuned mass damper | tuned mass damper | Standard structural term; preserve as a three-word phrase. | pass |
| wind / wind-driven / wind-load | wind with short i, rhyming with pinned | Air noun/verb context; review any hyphenated provider text for accidental long-I delivery. | pass |
| quartering wind / quartering-wind | quartering wind | Read as diagonal wind direction, not as a violent verb. Hyphenated instance is acceptable but should be reviewed in the render text. | pass |
| face winds / corner winds | face winds / corner winds | Structural wind-direction terms; no alias required. | pass |
| wind-tunnel report | wind tunnel report | Apply approved lexicon local alias by removing the hyphen in ElevenLabs render text. | pass |
| bolted rather than welded | bolted rather than welded | Keep contrast clear; no alias required. | pass |
| William LeMessurier | William luh-MESH-ur-ee-er | Use pronunciation-dictionary guidance or render-side spelling if needed; listen check required because surname is uncommon. | pass |
| NIST | N I S T | Spell as letters, not as a word. | pass |
| ASCE | A S C E | Spell as letters, not as "ask." | pass |
| Project SERENE | Project serene | Treat as a project name; if the model spells the capitalized word, use render text `Project Serene`. | pass |
| public-risk obligation | public risk obligation | Hyphen only marks a compound modifier; read as normal words. | pass |
| public-disclosure ethics | public disclosure ethics | Hyphen only marks a compound modifier; read as normal words. | pass |
| post-completion wind-load assumption | post completion wind load assumption | Technical mouthful; keep the sentence's commas and natural pauses. | pass |
| retrofit rationale | retrofit rationale | Standard engineering/legal phrase; no alias required. | pass |
| emergency posture | emergency posture | Read literally; no alias required. | pass |
| weather monitoring | weather monitoring | Standard phrase; no alias required. | pass |
| backup power | backup power | Standard phrase; no alias required. | pass |
| strain monitoring | strain monitoring | Structural monitoring phrase; no alias required. | pass |
| evacuation planning | evacuation planning | Standard phrase; no alias required. | pass |
| live public-risk question | live with long i, rhyming with hive | Means active/current, not live electrical load; context should resolve. | pass |
| record | REK-ord as a noun | Intended in "engineering record," "evidence record," and "design record." | pass |
| object | OB-ject as a noun | Intended in "solved object" and "completed object." | pass |
| close | kloze as the ending | Intended in "before the close," meaning before the ending. | pass |
| complete, occupied, unsettled | complete; occupied; unsettled | Preserve the three-beat cadence in the title and closing line. | pass |
| The legend fades. The receipts remain. | Two short declarative beats | Keep the sentence break; do not merge into one breath. | pass |

## Script Changes

No locked-script wording, spelling, punctuation, or line-break changes were made for this preflight.

| Location | Issue | Change | Reason |
| --- | --- | --- | --- |
| `source/longform-script.md` line 129 | Helper flagged `wind-tunnel` as a known ElevenLabs risk when hyphenated. | No script change; render-side provider text should apply the approved lexicon alias `wind tunnel`. | The pronunciation lexicon explicitly treats this as a local alias for provider text while keeping locked scripts and captions unchanged. |

## Risk Category Read

| Category | Read | Notes |
| --- | --- | --- |
| Pronunciation | pass | Episode-specific names, places, structural terms, and uncommon tokens are listed above. The only helper match has an approved local alias plan. |
| Acronyms / initialisms | pass | `NIST` and `ASCE` should be spelled as letters; `Project SERENE` should read as Project Serene. |
| Names / places / entities | pass | Citicorp Center, St. Peter's church, Lexington Avenue, New York, William LeMessurier, NIST, ASCE, and Project SERENE are covered in the ledger. |
| Dates / numbers / units | pass | Script body uses no calendar dates, measurements, or unit strings requiring provider repair. Chapter numbers are markdown structure, not narration-critical text. |
| Homographs / ambiguity | pass | Reviewed `wind`, `live`, `record`, `object`, and `close`; handling notes above resolve intended reads. |
| Technical mouthfuls | pass | Long phrases such as `post-completion wind-load assumption`, `public-disclosure ethics`, and `quartering wind and bolted-versus-welded connections` are punctuated well enough for TTS. |
| Punctuation / pause / breath | pass | Sentence breaks are generally short. Rhetorical fragments in the cold open and close should be preserved as deliberate cadence. |
| Repeated cadence | pass | Repetition around "complete," "occupied," "assumption," and "public risk" is thematic rather than accidental monotony. |

## Remaining Risks

No unresolved line appears likely to force ElevenLabs rework or re-recording after render if the approved local alias is applied for `wind-tunnel` and the render QA listens for the ledger tokens above.

The only provider-specific handling plan is to carry this ledger into the ElevenLabs render packet or pronunciation dictionary notes, especially for Citicorp, St. Peter's, William LeMessurier, NIST, ASCE, Project SERENE, wind compounds, and quartering wind.

## Audio Gate

Human script approval for audio remains pending until Mike or an approved human reviewer accepts this exact script hash for audio. Audio render remains unauthorized unless `frontier_model_script_critique_read`, `critique_integration_read`, `elevenlabs_preflight_read`, and `human_script_approval_for_audio_read` all pass for the same script revision.

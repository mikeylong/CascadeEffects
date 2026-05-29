# ElevenLabs/TTS Preflight: USS Thresher

episode_id: ep13-uss-thresher
script_path: episodes/season-02/ep13-uss-thresher/source/longform-script.md
script_sha256_reviewed: cdb34f76e2ebb229786449907d15f53722f49ab0ceb3745c36011f4aaee26107
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
| USS Thresher / Thresher | U S S THRESH-er / THRESH-er | Spell USS as letters; read Thresher like the common noun/name. | pass |
| USS | U S S | Spell as letters wherever it appears; do not say "uss." | pass |
| SUBSAFE | sub-safe | Carry a provider pronunciation note or local render alias of "Sub Safe"; retain locked script spelling. | pass |
| Skylark | SKY-lark | Surface ship name; ordinary word pronunciation is acceptable. | pass |
| Cape Cod | Cape Cod | Standard place name; no alias required. | pass |
| Court of Inquiry | Court of Inquiry | Read as a title phrase; do not overdramatize into courtroom dialogue. | pass |
| Cascade Effects | Cascade Effects | Brand phrase; standard pronunciation. | pass |
| Navy | Navy | U.S. Navy context; no acronym handling needed. | pass |
| April 10, 1963 | April tenth, nineteen sixty-three | Read date naturally as spoken words. | pass |
| 220 miles | two hundred twenty miles | Read the number and unit naturally. | pass |
| 129 people / 129 aboard | one hundred twenty-nine people / one hundred twenty-nine aboard | Read count naturally. | pass |
| "900" reference | nine hundred reference | Read as a reported "nine hundred" reference; do not infer or add units. | pass |
| post-overhaul | post overhaul | Hyphen links the modifier; do not over-pause. | pass |
| deep-dive / deep-dive trials | deep dive / deep dive trials | Hyphen is not spoken. | pass |
| seawater intrusion | seawater intrusion | Technical phrase is standard and clear in context. | pass |
| electrical or propulsion loss | electrical or propulsion loss | Keep the "or" audible so the script does not imply a settled single chain. | pass |
| emergency blow / ballast blow | emergency blow / ballast blow | Submarine recovery action; read "blow" as the ballast-system term. | pass |
| trim | trim | Submarine attitude/ballast context, not decorative trim. | pass |
| collapse-depth / collapse-depth conditions | collapse depth / collapse depth conditions | Hyphen is not spoken; phrase means depth regime near structural failure. | pass |
| brazed-joint / brazed joint | brayzd joint | Pronounce brazed like "braised"; no hard-Z pause. | pass |
| recovery-critical | recovery critical | Hyphen links the compound modifier; do not insert a heavy break. | pass |
| quality assurance | quality assurance | Standard production and inspection phrase. | pass |
| boundary-control / boundary control | boundary control | Hyphen is not spoken; keep as a single concept. | pass |
| live condition | lyve condition | Long-I "live," meaning active or real-time condition. | pass |
| final communications | final communications | Read as evidence fragments, not staged dialogue. | pass |
| source audit | source audit | Standard production term; no alias needed. | pass |

## Script Changes

No script wording, spelling, punctuation, or line-break changes were made for this preflight.

| Location | Issue | Change | Reason |
| --- | --- | --- | --- |
| not applicable | No required TTS repair found. | None. | Existing script is suitable for human audio approval review. |

## Risk Category Read

| Category | Read | Notes |
| --- | --- | --- |
| Pronunciation | pass | Episode-specific submarine, ship, institutional, and technical terms are listed above; the helper found no curated lexicon matches. |
| Acronyms / initialisms | pass | USS should be spelled as letters. SUBSAFE should read as "sub-safe" using a provider note or local render alias. |
| Names / places / entities | pass | USS Thresher, Skylark, Cape Cod, Court of Inquiry, Navy, and Cascade Effects are straightforward with ledger guidance. |
| Dates / numbers / units | pass | April 10, 1963; 220 miles; 129 people; and the reported "900" reference have explicit spoken reads. |
| Homographs / ambiguity | pass | Reviewed "live," "blow," "trim," "record," "proof," and the heading word "Close." Context or render extraction resolves each intended read. |
| Technical mouthfuls | pass | Phrases like "post-overhaul deep-dive trials," "brazed-joint path," "recovery-critical systems," and "boundary-control problem" are long but readable with existing punctuation. |
| Punctuation / pause / breath | pass | Paragraphs and sentence punctuation give usable breath points. The render packet should omit markdown metadata and headings unless a human explicitly wants chapter labels spoken. |
| Repeated cadence | pass | Repetition such as "Not one..." and "It could..." is intentional rhetorical structure, not accidental monotony requiring script repair. |
| ElevenLabs rework risk | pass | No unresolved wording appears likely to force re-render if the ledger is carried into the render packet. |

## Remaining Risks

No unresolved line appears likely to force ElevenLabs rework or re-recording after render. The provider-specific handling plan is to carry this ledger into the ElevenLabs render packet or pronunciation dictionary notes, especially for USS, SUBSAFE, "900," brazed-joint, emergency blow, collapse-depth, recovery-critical, and live condition.

## Audio Gate

Human script approval for audio remains pending until Mike or an approved human reviewer accepts this exact script hash for audio. Audio render remains unauthorized unless `frontier_model_script_critique_read`, `critique_integration_read`, `elevenlabs_preflight_read`, and `human_script_approval_for_audio_read` all pass for the same script revision.

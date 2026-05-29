# ElevenLabs/TTS Preflight: Texas City 1947

episode_id: ep15-texas-city-1947
script_path: episodes/season-02/ep15-texas-city-1947/source/longform-script.md
script_sha256_reviewed: 76b2a765b2a4c541fa6a67723277899deb08295b1e35807b9f551caaa24542c2
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

## Narration Boundary

The TTS render manifest should compile the narrated essay body only. The metadata lines at the top of the Markdown file and the `Review Notes For Final Fact-Check` section are production notes, not voiceover copy. If a future render manifest includes those notes as spoken input, fail the human audio gate before render.

## Pronunciation Ledger

| Token | Intended Read | Handling Plan | Status |
| --- | --- | --- | --- |
| Texas City 1947 | Texas City nineteen forty-seven | Say the year as nineteen forty-seven. | pass |
| April 16, 1947 | April sixteenth, nineteen forty-seven | Say the ordinal date and year naturally. | pass |
| SS Grandcamp | S S Grandcamp | Spell the vessel prefix as letters; keep Grandcamp as a single ship name. | pass |
| Grandcamp | GRAND-camp | Avoid a heavy pause between syllables; no alias required unless audition reveals one. | pass |
| SS High Flyer | S S High Flyer | Spell the vessel prefix as letters; read High Flyer as the ship name. | pass |
| High Flyer | High Flyer | Read as two clear words, not as a generic high-flying adjective. | pass |
| ammonium nitrate | uh-MOH-nee-um NYE-trayt | Standard chemical phrase; keep both words clear. | pass |
| fertilizer | fertilizer | Standard word; do not over-enunciate into a cartoon hazard read. | pass |
| port-industrial | port industrial | Hyphen marks the compound modifier; read as two words. | pass |
| shipboard fire | shipboard fire | Standard compound; read as one phrase. | pass |
| hazard communication | hazard communication | Standard safety phrase; keep steady professional cadence. | pass |
| emergency response | emergency response | Standard phrase; no alias required. | pass |
| heat and confinement | heat and confinement | Keep the list joined and clear; this is the central material-condition phrase. | pass |
| explosion hazard | explosion hazard | Standard phrase; do not over-dramatize. | pass |
| Cascade Effects | Cascade Effects | Brand phrase; keep both words clear. | pass |
| nearly 600 | nearly six hundred | Say the number as words. | pass |
| U.S. Coast Guard | U S Coast Guard | Spell U.S. as letters; no punctuation pause after U. | pass |
| Bureau of Mines | Bureau of Mines | Standard institutional name; read as BYUR-oh of Mines. | pass |
| City of Texas City | City of Texas City | The repetition is intentional because it names the municipality/source; read both uses plainly. | pass |
| Dalehite | DAYL-hite | Legal-case surname; use local pronunciation note if this line is included in a spoken source/citation passage. | pass |
| Texas State Historical Association | Texas State Historical Association | Institutional name; no acronym substitution. | pass |
| official-source stack | official source stack | Hyphen marks a compound modifier; read as three words. | pass |
| ignition-cause story | ignition cause story | Hyphen marks a compound modifier; read as three words. | pass |
| legal-accountability branch | legal accountability branch | Hyphen marks a compound modifier; read as three words. | pass |
| first catastrophic explosion | first catastrophic explosion | Long phrase is clear in context; keep a natural pause before it if chunked. | pass |
| The legend fades. The receipts remain. | The legend fades. The receipts remain. | Two short closing sentences; keep the pause between them. | pass |

## Script Changes

No script wording, spelling, punctuation, or line-break changes were made for this preflight.

| Location | Issue | Change | Reason |
| --- | --- | --- | --- |
| not applicable | No required TTS repair found. | None. | Existing post-integration script is suitable for human audio approval review. |

## Risk Category Read

| Category | Read | Notes |
| --- | --- | --- |
| Pronunciation | pass | Episode-specific vessel names, legal/institutional names, chemical terms, and series language are listed in the ledger. |
| Acronyms / initialisms | pass | `SS` and `U.S.` should be spelled as letters. No other spoken acronym requires an alias. |
| Names / places / entities | pass | Texas City, SS Grandcamp, SS High Flyer, Bureau of Mines, City of Texas City, Dalehite, U.S. Coast Guard, and Texas State Historical Association have explicit handling. |
| Dates / numbers / units | pass | The title/body year reads as nineteen forty-seven, the date reads April sixteenth, nineteen forty-seven, and the casualty phrase reads nearly six hundred. No unit conversion is present in the narrated body. |
| Homographs / ambiguity | pass | Reviewed `close`, `record`, `use`, `does`, `object`, `minute`, `lead`, and `read`; local context resolves the intended reading or the token is absent from spoken narration. |
| Technical mouthfuls | pass | `ammonium nitrate fertilizer under heat and confinement`, `hazard communication`, `emergency response`, `operational distance`, and the shrapnel/blast/infrastructure list are clear when chunked at sentence boundaries. |
| Punctuation / pause / breath | pass | Long sentences have commas, colons, or sentence breaks; short rhetorical sentence groups are intentional. Use paragraph-aware chunking and do not merge the closing two-sentence sign-off. |
| Repeated cadence | pass | Repeated `cargo`, `changed`, `risk`, `port`, and `failure surface` language supports the thesis and varies enough across chapters to avoid likely re-render. |
| ElevenLabs rework risk | pass | No unresolved line appears likely to force a re-record after render when the ledger and narration boundary are carried into the render packet. |

## Remaining Risks

No unresolved narrated line appears likely to force ElevenLabs rework or re-recording after render. The provider-specific handling plan is to carry this ledger into the ElevenLabs render packet or pronunciation dictionary notes, especially for `SS Grandcamp`, `SS High Flyer`, `Dalehite`, `U.S. Coast Guard`, and the date/year reads.

## Audio Gate

Human script approval for audio remains pending until Mike or an approved human reviewer accepts this exact script hash for audio. Audio render remains unauthorized unless `frontier_model_script_critique_read`, `critique_integration_read`, `elevenlabs_preflight_read`, and `human_script_approval_for_audio_read` all pass for the same script revision.

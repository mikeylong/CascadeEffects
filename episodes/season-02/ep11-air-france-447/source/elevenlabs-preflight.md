# ElevenLabs/TTS Preflight: Air France Flight 447

episode_id: ep11-air-france-447
script_path: episodes/season-02/ep11-air-france-447/source/longform-script.md
script_sha256_reviewed: eb10ed79b19eb3fcbb8b89f292ef4c2436bf0dd774b97300d1f1d62e2533d03e
script_revision_context: post-critique-integration longform script; frontier critique and critique integration receipts pass for this revision
tts_provider: ElevenLabs or current approved TTS provider
voice_or_model_context: long-form narration voice; provider-local aliases may be applied to render text without changing the locked script or captions
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

Helper used: `packages/media-pipeline/audio/scripts/pronunciation_preflight.py scan`

Lexicon: `packages/media-pipeline/audio/references/pronunciation/known_risks_v1.json`

Lexicon sha256: `3bbd0ab315d1afc8913f5684c728b89096536c921459d96edbb100311b61f861`

Result: 1 script job scanned, 11 lexicon rules loaded, 0 known-risk matches, 0 blockers.

## Pronunciation Ledger

List every likely pronunciation-sensitive token, the intended reading, and the handling plan. Include names, places, acronyms, registrations, numbers, dates, units, abbreviations, and technical terms.

| Token | Intended Read | Handling Plan | Status |
| --- | --- | --- | --- |
| Raw markdown metadata and heading markers | Do not narrate `status`, `gate`, `episode_id`, `target_runtime`, or `source_basis`; narrate headings only if the production script intentionally includes chapter labels | Compile ElevenLabs input from narration body. Strip metadata lines and markdown `#` markers before render. | pass |
| Air France Flight 447 / Air France 447 / Flight 447 | Air France Flight four forty-seven | Use normal spelling unless provider reads digits as "four four seven"; local alias may spell out "four forty-seven" in provider text. | pass |
| AF447 | A F four forty-seven | Use provider-local alias `A F four forty-seven` if the abbreviation is included in render text. | pass |
| Airbus | AIR-bus | Standard TTS should be stable; listen for over-French delivery only in review. | pass |
| Airbus A330-203 | Airbus A three thirty dash two oh three | Use provider-local alias `Airbus A three thirty dash two oh three`; keep locked script unchanged. | pass |
| F-GZCP | F G Z C P | Spell as letters with spaces in provider-local render text: `F G Z C P`. | pass |
| June 1, 2009 | June first, two thousand nine | Standard date read is acceptable; if provider says "June one," that is acceptable but less natural. | pass |
| 228 people | two hundred twenty-eight people | Standard number read; no script change needed. | pass |
| Rio de Janeiro | REE-oh deh zhuh-NAIR-oh | Standard place-name read likely acceptable; review first render for stress. | pass |
| Paris | PAIR-iss | Standard place-name read. | pass |
| Atlantic | at-LAN-tic | Standard place-name read. | pass |
| Pitot / Pitot probes / Pitot icing | PEE-toh | High-risk aviation term. Use provider-local alias `pee-toh` if dictionary support is unavailable or if first render says "pit-ot." | pass |
| BEA | B E A | Spell letters in provider-local render text if needed; do not let TTS say "bee-ah" as a word. | pass |
| CVR | C V R | Spell letters with spaces in provider-local render text. | pass |
| FDR | F D R | Spell letters with spaces in provider-local render text. | pass |
| Metron | MET-ron | Metadata/source-basis only; do not narrate unless source credits are intentionally spoken. | pass |
| SKYbrary | sky-brary | Metadata/source-basis only; do not narrate unless source credits are intentionally spoken. | pass |
| autothrust | auto thrust | Accept native read if clear; provider-local alias `auto thrust` is available if the compound is blurred. | pass |
| autopilot disconnect / disconnected | autopilot disconnect / disconnected | Standard read. Preserve pauses around the handoff sentences so the phrase does not rush. | pass |
| angle of attack / angle-of-attack | angle of attack | Prefer unhyphenated provider-local text if the hyphenated compound produces clipped delivery. | pass |
| managed-flight / normal-flight / degraded-mode / high-altitude / public-facing | managed flight; normal flight; degraded mode; high altitude; public facing | Hyphens are editorial, not pronunciation-critical. Provider-local render text may remove hyphens to smooth cadence. | pass |
| live system | lyve system | Homograph check: line means a real-time/live system, long-I. Standard TTS should read correctly from context. | pass |
| BEA record / records / recorded flight data | record as noun where used with BEA; records as noun; recorded as verb/adjective | Homograph check. Context is clear; no local alias needed. | pass |
| harder to read / readings | read as "reed"; readings as "reedings" | Homograph check. Context is clear; no local alias needed. | pass |

## Acronyms / Initialisms

`AF447`, `BEA`, `CVR`, `FDR`, `A330-203`, and `F-GZCP` are the only meaningful acronym/initialism or alphanumeric reads in the spoken body. All have explicit local-alias handling. No global pronunciation dictionary update is required.

## Names / Places / Entities

Names and entities checked: Air France, Flight 447, Airbus, Airbus A330-203, registration F-GZCP, Rio de Janeiro, Paris, Atlantic, BEA, Pitot probes, CVR, FDR, Metron, SKYbrary. Metadata-only sources should not be narrated unless a production compiler explicitly includes source credits.

## Numbers / Dates / Units

Checked reads: `447`, `AF447`, `A330-203`, `F-GZCP`, `June 1, 2009`, `228 people`, `12-18 minutes`, and chapter numbers. Chapter labels are safe if spoken; metadata runtime should be stripped before render.

## Homographs / Ambiguous Reads

Checked reads: `live system`, `read`, `readings`, `record`, `records`, `recorded`, and `present`. Context resolves each item. No locked-script change is needed.

## Technical Mouthfuls

The densest phrases are `unreliable airspeed indications`, `automation disconnect`, `degraded-mode diagnosis problem`, `public-facing angle-of-attack number`, `flight-data reconstruction`, and the Chapter 6 mechanism list: `unreliable speed data, automation disconnect, cockpit indications, workload, training expectations, and the crew's interpretation`. Existing commas and sentence breaks are sufficient for TTS. If the provider rushes, apply breath/pause tuning in provider text rather than revising the locked script.

## Punctuation / Pause / Breathing / Cadence

The script alternates short emphasis lines with longer explanatory sentences. The repeated cold-open and close patterns are intentional:

- `The public headline comes later. The impact comes later. The search comes later.`
- `What changed? Who, or what, failed to recognize that change? How did the system convert delayed recognition into consequence?`
- `Not a machine replacing humans. Not humans simply failing the machine.`

Preserve paragraph breaks as pause boundaries. Do not collapse the short fragments into adjacent prose during provider-text compilation.

## Script Changes

Record every wording, spelling, punctuation, or line-break change made for TTS reliability.

| Location | Issue | Change | Reason |
| --- | --- | --- | --- |
| None | No locked-script wording, spelling, punctuation, or line-break change required | None | All identified risks are handled by render-prep stripping or provider-local aliases |

## Remaining Risks

No unresolved preflight risks remain for this script hash. The highest-risk terms are `Pitot`, `AF447`, `A330-203`, and `F-GZCP`; all have explicit provider-local handling plans before render.

## Audio Gate

Human script approval for audio remains pending until this preflight is passing for the exact script hash. Audio render remains unauthorized unless `frontier_model_script_critique_read`, `critique_integration_read`, `elevenlabs_preflight_read`, and `human_script_approval_for_audio_read` all pass for the same script revision.

# ElevenLabs/TTS Preflight: Hindenburg Disaster

episode_id: ep14-hindenburg
script_path: episodes/season-02/ep14-hindenburg/source/longform-script.md
script_sha256_reviewed: a641cc87718d01f7d9e9f609bc4c449ac97e41cabcc26f5ed4908d8a59022839
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
- Note: the helper lexicon is generic and did not contain Hindenburg-specific names or phrases, so the episode-specific ledger below is the controlling read.

## Script / Render Boundary

The locked script file includes production metadata, markdown headings, and final review notes. The ElevenLabs render packet should use the narration text only unless a human explicitly wants chapter headings spoken. Do not render `status`, `gate`, `episode_id`, or the `Review Notes` section as voiceover. If chapter headings are retained, read the chapter number naturally and use the heading as a short title beat.

## Pronunciation Ledger

| Token | Intended Read | Handling Plan | Status |
| --- | --- | --- | --- |
| Hindenburg | HIN-den-burg | Standard historical name; keep hard "g" ending. | pass |
| Lakehurst | Lake-hurst | Place name; avoid splitting as "lake hearst." | pass |
| May 6, 1937 | May sixth, nineteen thirty-seven | Date should read naturally in narration. | pass |
| Atlantic | Atlantic | Standard place/ocean term. | pass |
| hydrogen | HY-dro-jen | Standard chemistry term; no alias required. | pass |
| hydrogen-air mixture | hydrogen air mixture | Hyphen marks compound modifier; read as two words with no "dash" spoken. | pass |
| rear gas cells | rear gas cells | Standard phrase; keep "cells" plural. | pass |
| gas-cell integrity / gas-cell issue | gas cell integrity / gas cell issue | Hyphen should not be spoken; read as two words. | pass |
| cells 4 and 5 | cells four and five | Say numerals as cardinal numbers. | pass |
| electrical discharge | electrical discharge | Technical phrase is stable. | pass |
| landing and grounding conditions | landing and grounding conditions | Read as a coupled condition, not two separate topic shifts. | pass |
| mooring / mooring mast / mooring procedure | MOOR-ing / MOOR-ing mast / MOOR-ing procedure | Airship/ground operation term; pronounce like "moor," not "morning." | pass |
| rope handling | rope handling | Standard phrase. | pass |
| operating envelope / landing envelope | operating envelope / landing envelope | Engineering phrase; keep "envelope" as boundary/condition, not mailing object. | pass |
| fabric and covering system | fabric and covering system | Read literally; no alternate spelling needed. | pass |
| material and coating theories / coating debate | material and coating theories / coating debate | Keep as bounded alternate-theory language. | pass |
| paint-only / coating-only | paint only / coating only | Hyphen is a compound modifier; do not say "dash." | pass |
| sabotage | SAB-uh-tazh | Standard pronunciation; no alias required. | pass |
| public confidence | public confidence | Central phrase; keep neutral documentary cadence. | pass |
| coupled failure / coupled system | coupled failure / coupled system | Read "coupled" as "kuh-puld." | pass |
| mixture ratios | mixture ratios | Standard technical phrase. | pass |
| ship-and-ground system | ship and ground system | Hyphenated compound should read as words, not punctuation. | pass |
| changed-first frame | changed first frame | Series doctrine phrase; read as three words. | pass |
| mechanism-led story | mechanism led story | Hyphen marks modifier; read without "dash." | pass |
| point of no return | point of no return | Common phrase; no handling needed. | pass |
| Thirty-five of the ninety-seven people aboard | thirty-five of the ninety-seven people aboard | Already written in words; keep casualty read careful and unsensational. | pass |
| one member / one person of the ground crew | one member / one person of the ground crew | Already written in words; no numeric ambiguity. | pass |
| Cascade Effects | Cascade Effects | Series name; read normally. | pass |
| CAA / Bureau of Air Commerce | C A A / Bureau of Air Commerce | Appears only in review notes; exclude from render. If spoken, spell CAA as letters. | pass |
| Smithsonian | Smithsonian | Appears only in review notes; standard institution name. | pass |
| German investigation records | German investigation records | Appears only in review notes; standard phrase. | pass |
| minute-by-minute timing | minute by minute timing | Appears only in review notes; hyphens should not be spoken. | pass |

## Script Changes

No script wording, spelling, punctuation, or line-break changes were made for this preflight.

| Location | Issue | Change | Reason |
| --- | --- | --- | --- |
| not applicable | No required TTS repair found. | None. | Existing post-integration script is suitable for human audio approval review. |

## Risk Category Read

| Category | Read | Notes |
| --- | --- | --- |
| Pronunciation | pass | Episode-specific tokens are listed above; no required local alias was found by helper or manual review. |
| Acronyms / initialisms | pass | CAA appears only in non-render review notes. If it is ever spoken, spell it as C A A. |
| Names / places / entities | pass | Hindenburg, Lakehurst, Atlantic, Cascade Effects, Bureau of Air Commerce, Smithsonian, and German investigation records are covered in the ledger. |
| Dates / numbers / units | pass | May 6, 1937; cells 4 and 5; chapter numbers; and casualty numbers have clear intended reads. |
| Homographs / ambiguity | pass | Reviewed "object," "record," "present," "lead," "read," "minute," and "envelope"; local context resolves the intended reads. |
| Technical mouthfuls | pass | Long phrases such as "hydrogen-air mixture near the rear gas cells," "landing and grounding conditions," and "weather, mooring, gas cells, materials, and electrical risk" are punctuated into workable spoken units. |
| Punctuation / pause / breath | pass | Several long list sentences need attentive voice direction, but punctuation provides usable breath points and no line is likely to force a re-render. |
| Repeated cadence | pass | Repetition around "It was," "It is also," "It can support," and "It depended" is intentional rhetorical structure, not accidental monotony requiring script repair. |
| ElevenLabs rework risk | pass | No wording, spelling, punctuation, or cadence issue appears likely to force ElevenLabs rework after render if the ledger and render-boundary note are carried forward. |

## Remaining Risks

No unresolved line appears likely to force ElevenLabs rework or re-recording after render. The render packet should carry this ledger forward, especially for Hindenburg, Lakehurst, mooring, hydrogen-air, gas-cell compounds, cells 4 and 5, and the instruction to exclude production metadata and review notes from spoken audio.

## Audio Gate

Human script approval for audio remains pending until Mike or an approved human reviewer accepts this exact script hash for audio. Audio render remains unauthorized unless `frontier_model_script_critique_read`, `critique_integration_read`, `elevenlabs_preflight_read`, and `human_script_approval_for_audio_read` all pass for the same script revision.

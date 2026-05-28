# Titanic Long-Form Visual System Plan

Date: 2026-05-19

Workflow: `long_form_video_production_v1`

Gate: `visual_system_plan`

Disposition: `review_ready_pending_human_keep`

## Direction

Use `living_cover_system_v1` with `fixed_16x9_right_rail_v1` for a Titanic Living Cover built around the boat-deck regulation gap: an early-1910s ocean-liner deck, lifeboats and davits, inspection paperwork, and the visual tension between legal compliance and human-scale escape capacity.

The public anchor is not the sinking, the iceberg strike, or disaster spectacle. The source-art direction must read as the regulatory failure before the collision: a calm, historically grounded boat-deck and inspection scene where the hardware can imagine more risk than the rulebook demanded.

This packet plans the visual system only. It does not generate source art, mark source art `keep`, create a cue map, build an ambient/effects layer, integrate music, assemble a rough proof, render a final MP4, upload, or publish.

## Approved Inputs

- Kept audio: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/final/Ep8_Titanic.wav`
- Audio SHA-256: `81488bff51999910864535a8fe93645bd7f930a7846198a4e89e9df36fec9604`
- Locked narration script: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/Ep8_Titanic.txt`
- Script SHA-256: `a5fb122223052b820f7dd832a7f9227db4780f9d4ffd810915e579bef1249dc3`
- Timing source: `/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_longform_receipts_signoff_20260519/transcripts_mastered/Ep8_Titanic.whisperx.json`
- Timing source SHA-256: `51a705c669285a7e134c0f81d99fd080747e58500734673db412d78db69138f7`
- SRT timing sidecar: `/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_longform_receipts_signoff_20260519/transcripts_mastered/Ep8_Titanic.diarized.srt`
- SRT SHA-256: `f82c3e4d318d845dc4f86490f8591964e390a50d9c14d726b8caa5ea5a3358ad`
- VTT timing sidecar: `/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_longform_receipts_signoff_20260519/transcripts_mastered/Ep8_Titanic.diarized.vtt`
- VTT SHA-256: `f6319537602bc89ebf57c2aa8b1e8663ff5c6df276ba96086c29b42cda47bec4`
- Existing Short bridge: private review upload processed, manual Studio checks pending.
- Brand design contract: `/Users/mike/Web_CascadeEffects/brand/contracts/design-system.contract.md`
- Illustration contract: `/Users/mike/Web_CascadeEffects/brand/contracts/illustration.contract.md`
- Living Cover system spec: `/Users/mike/Agents_CascadeEffects/references/skills/long_form_video_production_v1/references/living_cover_system_spec_v1.md`

## Visual Carrier Policy

- Primary lane: `cascade-ink-lit-photoreal-v1`
- Episode visual style: `titanic_boat_deck_lifeboat_regulation_gap_photoreal_v1`
- Carrier type: `generated_raster_source_art`
- Generation tool: Codex built-in ImageGen through the `imagegen` skill when source-art generation is explicitly opened.
- Canvas target: `1920x1080`
- Role: long-form Living Cover backplate candidate.
- Source-art status: `blocked_pending_visual_system_keep`
- Source-art exception status: `none`
- Paper Architecture visual style read: `blocked_for_active_long_form_video`

The current long-form workflow forbids Paper Architecture as the active video source-art style. Website/channel Paper Architecture contracts remain reference context only; they do not authorize folded-paper or foam-core Titanic backplates for this long-form video.

Sourced archival stills, ship-deck photographs, Board of Trade documents, report scans, and Short assets may guide historical/source-reference review, but they are reference evidence only. They are not active source art unless a later human-approved source-art exception names exact paths, rights/source risk, reason, and affected outputs.

HTML, CSS, SVG, canvas, and FFmpeg may only provide proof shell, timing, rail, captions, deterministic typography, safe-zone layout, masks, transforms, and layer compositing over approved raster/source art.

## Recognizability Ladder

- Public anchor: early-1910s Olympic-class ocean-liner boat deck with lifeboats and davits.
- Evidence object: inspection clipboard or folded regulation ledger with no readable text, capacity marks, and lifeboat hardware.
- System clue: empty deck space, davits capable of more than the minimum carried, distant anonymous crew or inspector silhouette, and cold institutional lighting that keeps the focus on compliance before catastrophe.

No readable generated labels, ship-name text, company logos, title text, watermarks, victim imagery, or real-person likenesses are allowed.

## Historical And Source Reads Required Before Source-Art Keep

- `historical_accuracy_read`
- `source_reference_alignment_read`
- `public_anchor_geometry_read`
- `titanic_boat_deck_read`
- `lifeboat_davit_accuracy_read`
- `lifeboat_capacity_visual_logic_read`
- `board_of_trade_document_cue_read`
- `period_maritime_materials_read`
- `disaster_spectacle_absence_read`
- `generated_text_logo_read`
- `human_presence_read`
- `no_recognizable_faces_read`
- `texture_noise_read`
- `video_visual_style_scope_read`
- `paper_architecture_visual_style_read`
- `procedural_signal_overlay_read`
- `ambient_line_artifact_read`

Hard mismatch blockers:

- A sinking ship, iceberg collision, breaking hull, bodies, panic crowd, or disaster spectacle.
- A modern cruise ship, modern lifeboats, modern safety signage, or contemporary inspection gear.
- Readable generated text, ship names, White Star logos, Board of Trade labels, title lettering, or watermarks.
- A visual that implies enough lifeboats for everyone or turns the deck into a fully solved evacuation system.
- A generic nautical scene with no lifeboat/davit/regulation relationship.
- Paper Architecture resemblance, folded-paper ship models, foam-core deck props, or website thumbnail-gallery style.
- Procedural cyan connector lines, diagnostic traces, UI paths, evidence-board arrows, or visible cascade overlays on the backplate.
- Recognizable passengers, officers, public figures, or face-forward generated people.
- Gritty disaster noir, smoke, debris, high-frequency texture, speckle, grain, sand, or visual noise.

## Living Cover System

- `living_cover_system_version`: `living_cover_system_v1`
- `rail_preset_id`: `fixed_16x9_right_rail_v1`
- `override_status`: `none`
- Canvas: fixed `1920x1080`, `16:9`
- Rail: right rail, `760px`, source-aware palette sampled from the approved source-art plate.
- Text surface policy: all story text, chapter text, captions, cue wording, and end-screen wording stay inside the fixed right rail.
- Caption process: `living_cover_captioning_process_v1`
- Caption output model: `dual_visible_rail_and_youtube_vtt_sidecar`
- Caption text source: locked narration script only.
- Caption timing source: WhisperX/VTT/SRT timing only.
- ASR text as visible caption source: `blocked`

Required caption reads before rough assembly:

- `caption_text_matches_script_read`
- `caption_alignment_coverage_read`
- `caption_asr_text_not_used_read`
- `caption_known_regression_fixture_read`

## Chapter And Rail Spine

Use this seven-section spine as the first rail data source:

1. Legal Enough
2. The Bracket That Stopped Measuring
3. Compliance Became Sufficient
4. The Davits Knew More
5. Capacity Was Not Evacuation
6. SOLAS Changes The Question
7. The Legend And The Ledger

Rail copy must be viewer-facing and episode-specific. Record `stale_cross_episode_label_read`, `right_rail_text_boundary_read`, `out_of_rail_text_read`, and `ordinal_chapter_label_read` before rough assembly.

## Source-Art Prompt Brief

Asset type: long-form Living Cover source-art candidate, 16:9, text-free raster backplate.

Archetype: ink-lit photoreal public-scene carrier, early-1910s ocean-liner boat deck.

Prompt:

`A 1920x1080 ink-lit photoreal documentary scene on an early-1910s ocean liner boat deck at cold dawn, Olympic-class scale, wooden lifeboats in davits along the deck, empty deck space that implies unused capacity, brass and dark wood inspection clipboard or folded regulation ledger with no readable text, riveted steel railings, teak deck, restrained warm deck lamps, cold Atlantic haze far beyond the rail, one distant back-turned crew inspector silhouette with no recognizable face, calm pre-disaster atmosphere, source-preserving historical realism, clear right-side negative space and lower-detail safe area for a fixed video rail, cinematic but restrained, no readable text, no ship name, no logos, no title lettering, no sinking ship, no iceberg, no panic, no bodies, no disaster spectacle, no modern cruise ship, no modern lifeboats, no procedural cyan lines, no UI overlays, no arrows, no evidence-board graphics, no Paper Architecture, no folded paper, no foam-core model, no gritty smoke, no debris, no high-frequency speckle, no grain, no sandy texture`

Avoid list:

`sinking, iceberg impact, wreckage, bodies, panic crowd, modern cruise ship, orange modern lifeboats, readable text, Titanic name lettering, White Star logo, Board of Trade label, title card, watermark, celebrity likeness, Captain Smith likeness, face-forward person, procedural signal lines, cyan connector paths, UI diagrams, evidence board, arrows, folded-paper model, foam-core craft, Paper Architecture, gritty noir, smoke, debris, horror, high-frequency texture, speckle, grain, sandy surface`

## Cue Map Requirements

The next packet after visual-system `keep` must create a dedicated `living_cover_cue_map` before rough assembly. It must include chapter shifts, key phrase typography, 4 to 6 effect-map or cascade-diagram moments, caption/rail coordination, outro/end-screen timing, and source-safe treatment reads.

Required reads:

- `living_cover_cue_map_read`
- `chapter_cue_coverage_read`
- `typography_cue_read`
- `effect_map_cue_read`
- `source_safe_motion_read`
- `cue_no_diagnostic_overlay_read`
- `cue_map_internal_artifact_read`
- `visible_cue_overlay_read`

## Ambient/Effects Layer Requirements

Preferred lanes for Titanic:

- `minimal`
- slow source drift or parallax over the approved raster plate
- restrained practical deck-lamp micro-life
- faint cold haze beyond the rail only if it does not become smoke or grit
- subtle sea/dawn light movement outside the main deck geometry

No diagnostic overlays, route lines, UI paths, cyan signal traces, or procedural connector marks may be drawn over the source art.

Required reads:

- `ambient_effects_plan_read`
- `ambient_effect_lane_decision_read`
- `source_plate_matte_registration_read`
- `foreground_occlusion_read`
- `effect_layer_source_safety_read`
- `deterministic_ambient_read`
- `additive_effect_integration_read`
- `debug_overlay_absence_read`
- `ambient_effect_browser_sample_read`
- `range_scrub_effect_review_read`

## Music Integration Requirements

Rough assembly remains blocked until a packet-local `music_integration_contract` exists.

Default lane: `challenger_style_intro_outro`, unless Mike explicitly approves an episode-specific alternate or no-music/temp-music waiver.

The contract must record approved intro/outro sources, source rights, Content ID risk, voice-start offset, caption timing shift, full outro handoff, VO-to-outro blend plan, transition sample, level checks, and the full set of music regression reads before rough-proof `keep`.

## Blocked Until Later Gates

- Source-art generation: blocked pending visual-system `keep`.
- Source-art keep: blocked pending generated candidate and historical/source-reference review.
- Cue map: blocked pending visual-system `keep`.
- Ambient/effects layer: blocked pending visual-system `keep`.
- Music integration contract: blocked pending visual-system `keep`.
- Motion readiness: blocked pending source-art/cue/ambient/music readiness.
- Rough assembly: blocked pending visual-system `keep`, source-art keep, cue map, ambient/effects layer, music contract, and script-locked caption package.
- Final assembly: blocked, no rough assembly keep.
- Publish readiness: blocked, no final assembly keep.
- YouTube upload and public release: blocked.

## Review Ask

Review this visual system direction, then choose one:

- `keep visual system`
- `tighten visual system` with exact notes
- `reject visual system` with exact notes

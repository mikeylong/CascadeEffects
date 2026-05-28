# 737 MAX Long-Form Visual-System Plan Non-Paper Repair

Date: 2026-05-19

Workflow: `long_form_video_production_v1`

Gate: `visual_system_plan`

Disposition: `review_ready_pending_human_keep`

## Summary

This packet replaces the invalidated 737 MAX long-form visual-system plan. The earlier visual direction is historical only and does not authorize source-art generation, source-art keep, cue-map construction, ambient/effects work, rough assembly, final render, publish readiness, upload, or public release.

The new direction uses `cascade-ink-lit-photoreal-v1` / episode-specific source-preserving photoreal public-scene treatment for a 737 MAX Living Cover. The visual system centers on a familiar airplane whose physical geometry changed: a larger forward/high-mounted engine relationship, a single angle-of-attack sensor dependency, a hidden stabilizer correction path, and the training/commonality promise that made the new behavior harder to see.

## Gate Reads

- `video_visual_style_scope_read`: `pass_long_form_video_asset_non_paper`
- `paper_architecture_visual_style_read`: `pass_no_resemblance`
- `long_form_source_art_lane_read`: `pass_source_preserving_photoreal`
- `paper_architecture_resemblance_read`: `pass_absent`
- `may_generate_source_art`: `false`
- `may_mark_source_art_keep`: `false`
- `may_build_cue_map`: `false`
- `may_build_motion_or_rough_proof`: `false`
- `may_youtube_action`: `false`

## Approved Inputs

- Kept audio: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/final/Ep7_737-MAX.wav`
- Audio SHA-256: `adaf19d653f7d673d601ba0f273ef822dbce375dee25ec5c3554f687b839db71`
- Locked narration script: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/Ep7_737-MAX.txt`
- Script SHA-256: `3f95aaf72b3144f0c33ee85e77d18140a888ba97c46eb89b0cfaad5c61a7c718`
- Timing source: `/Users/mike/Audio_CascadeEffects/tmp/transcripts_final/Ep7_737-MAX.whisperx.json`
- Timing source SHA-256: `6b2cd28bd172c0fff59c113b1b465fc0853cf57a7af0a529590d80ea5747ae8f`
- SRT timing sidecar: `/Users/mike/Audio_CascadeEffects/tmp/transcripts_final/Ep7_737-MAX.diarized.srt`
- SRT SHA-256: `d0ea85324c5b7aa07e290ba9f468a1dc26a70c4686ef5f59d26b8ea33e188096`
- VTT timing sidecar: `/Users/mike/Audio_CascadeEffects/tmp/transcripts_final/Ep7_737-MAX.diarized.vtt`
- VTT SHA-256: `f45906753a5660d6744060d0281b615b29297cae5aa80b5acca85a2baf2c83c5`
- Existing Short bridge: `737_max_short_scoped_v1`, private review upload `mxIr64N-4HE`
- Fact-check memo: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/fact_check.md`
- Source inventory: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/visual_research/source_inventory.json`
- Living Cover system spec: `/Users/mike/Agents_CascadeEffects/references/skills/long_form_video_production_v1/references/living_cover_system_spec_v1.md`

## Visual Carrier Policy

- Primary lane: `cascade-ink-lit-photoreal-v1`
- Carrier type: `generated_raster_source_art`
- Generation tool for a later gate: Codex built-in ImageGen through the `imagegen` skill.
- Canvas target: `1920x1080`
- Role: long-form Living Cover backplate candidate.
- Source-art status: `blocked_pending_visual_system_keep`
- Source-art exception status: `none`

Sourced aircraft photos, accident imagery, cockpit photos, investigative documents, official reports, and the existing 737 visual research inventory may guide historical/source-reference review, but they are reference evidence only. They are not active source art unless a later human-approved source-art exception names exact paths, rights/source risk, reason, and affected outputs.

HTML, CSS, SVG, canvas, and FFmpeg may only provide proof shell, timing, rail, captions, deterministic typography, safe-zone layout, masks, transforms, and layer compositing over approved raster/source art.

## Recognizability Ladder

- Public anchor: unbranded 737 MAX-family front-quarter aircraft profile with the nose, wing root, and larger forward/high-mounted LEAP engine relationship readable at a glance.
- Evidence object: a restrained angle-of-attack vane/sensor cue, stabilizer trim wheel or horizontal-stabilizer mechanism, and blank training/commonality paperwork cues.
- System clue: a hidden stabilizer correction path implied through lighting, depth, and composition, not through viewer-facing diagnostic lines or labels.

No readable generated text, Boeing or airline logos, tail numbers, airline liveries, victim imagery, crash debris, public-official likenesses, or real-person faces are allowed.

## Historical And Source Reads Required Before Source-Art Keep

- `historical_accuracy_read`
- `source_reference_alignment_read`
- `public_anchor_geometry_read`
- `737_max_aircraft_profile_read`
- `leap_engine_placement_read`
- `angle_of_attack_sensor_cue_read`
- `mcas_stabilizer_mechanism_read`
- `single_sensor_assumption_read`
- `training_commonality_document_cue_read`
- `generated_text_logo_read`
- `human_presence_read`
- `no_recognizable_faces_read`
- `no_crash_spectacle_read`
- `texture_noise_read`
- `waterfall_read`

Hard mismatch blockers:

- Crash scene, wreckage, explosion, fire, ocean impact, falling aircraft, or disaster spectacle.
- Readable Boeing/airline logos, tail numbers, generated labels, document text, or UI overlays.
- A generic jetliner whose engine/nose profile does not read as 737 MAX-family.
- Engine placement that hides the forward/high-mounted change central to the mechanism.
- MCAS represented as a cockpit screen, robot, villain, or science-fiction AI.
- Face-forward pilots, victims, executives, public officials, or recognizable real people.
- Dense evidence-board collage, arrows, diagnostic connector lines, or procedural UI graphics as viewer-facing source art.
- Gritty disaster styling, smoke, debris, high-frequency grain, sandy surface, or texture-heavy rendering.
- Cyan paths that read as water, liquid, river, stream, or waterfall.

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

1. Two Crews, One Hidden System
2. A Familiar Airplane Had Changed
3. Software Preserved the Promise
4. One Sensor Became Enough
5. Training Followed Commonality
6. Procedure Hid Architecture
7. The Familiar Story Failed

Rail copy must be viewer-facing and episode-specific. Record `stale_cross_episode_label_read`, `right_rail_text_boundary_read`, `out_of_rail_text_read`, and `ordinal_chapter_label_read` before rough assembly.

## Source-Art Brief For Later Gate

Asset type: long-form Living Cover source-art candidate, 16:9, text-free raster backplate.

Archetype: photoreal editorial aircraft mechanism scene / familiar airplane with hidden correction path.

Prompt direction for the later source-art generation gate:

`A 1920x1080 ink-lit photoreal editorial scene of an unbranded 737 MAX-family aircraft front-quarter nose and wing-root profile in a restrained hangar or ramp-side engineering-light environment, the larger forward high-mounted LEAP engine relationship visibly central to the composition, a small angle-of-attack vane sensor cue on the nose, a subtle horizontal-stabilizer trim mechanism implied in the background, blank training and certification paperwork forms as secondary evidence objects, deep controlled shadows, cool aviation-grade metal and glass, restrained cyan instrument reflection used only as light, warm practical hangar highlights, sparse documentary composition, right side kept lower-detail and title-safe for a fixed rail, no readable text, no labels, no logos, no airline livery, no tail number, no crash scene, no wreckage, no fire, no explosion, no victims, no identifiable people, no UI overlays, no diagnostic connector lines, no brand-paper material cues, no speckle/noise/grain/grit/sandy texture, no water/waterfall/river/stream/canal/channel/liquid spill/glowing watercourse`

Avoid list:

`crash, wreckage, explosion, fire, ocean impact, falling aircraft, disaster spectacle, readable text, Boeing logo, airline logo, tail number, airline livery, MCAS screen text, AI robot, villain figure, pilot faces, victims, executives, public officials, dense evidence board, arrows, UI overlays, diagnostic connector lines, gritty disaster styling, smoke, debris, high-frequency grain, sandy surface, water, waterfall, river, liquid blue channel, generated title lettering, brand-paper material cues`

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

Preferred lanes for 737 MAX:

- `minimal`
- slow source-integrated light drift across the unbranded aircraft source plate
- restrained instrument reflection or hangar-light shimmer
- subtle stabilizer/trim shadow shift only if it remains source-integrated
- no generated diagnostic overlays or visible route lines

`none` or `minimal` is allowed only with review rationale. No procedural signal overlays may be drawn over the source art unless a later human-approved visual-system update scopes them narrowly.

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

Review this replacement 737 MAX visual-system plan and choose one:

- `keep visual system`
- `tighten visual system` with exact notes
- `reject visual system` with exact notes

No source-art generation may begin until an explicit human visual-system `keep` is recorded for this replacement plan.

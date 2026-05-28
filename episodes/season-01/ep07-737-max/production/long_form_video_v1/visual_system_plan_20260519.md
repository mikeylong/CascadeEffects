# 737 MAX Long-Form Visual System Plan

Date: 2026-05-19

Workflow: `long_form_video_production_v1`

Gate: `visual_system_plan`

Disposition: `invalidated_wrong_longform_style_paper_architecture`

## Invalidation

This plan is no longer active. Mike stopped the 737 MAX long-form visual path because the proposed ink-lit source-art direction resembled Paper Architecture. Video assets must not use Paper Architecture visual style. Long-form episode backplates must use `cascade-ink-lit-photoreal-v1` or another episode-specific source-preserving/photoreal public-scene carrier.

- video_visual_style_scope_read: `reject_video_asset_used_paper_architecture`
- paper_architecture_visual_style_read: `reject`
- long_form_source_art_lane_read: `reject_paper_architecture_not_allowed_for_long_form_backplate`
- paper_architecture_resemblance_read: `reject`
- may_generate_source_art: `false`
- may_mark_source_art_keep: `false`
- may_build_cue_map: `false`
- may_build_motion_or_rough_proof: `false`
- may_youtube_action: `false`

## Direction

Use `living_cover_system_v1` with `fixed_16x9_right_rail_v1` for a 737 MAX Living Cover built around an ink-lit Paper Architecture aircraft/mechanism tableau.

The public anchor is not a crash scene, generic airport scene, or evidence board. The source-art direction must read as an unbranded 737 MAX-family nose and enlarged forward/high-mounted engine profile, with the changed engine/airframe relationship made legible as the physical condition that MCAS tried to mask. The visual idea is a familiar airplane whose hidden software correction path is doing more work than the training and certification story admits.

This packet plans the visual system only. It does not generate source art, mark source art `keep`, create a cue map, build an ambient/effects layer, integrate music, assemble a rough proof, render a final MP4, upload, or publish.

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
- Brand design contract: `/Users/mike/Web_CascadeEffects/brand/contracts/design-system.contract.md`
- Illustration contract: `/Users/mike/Web_CascadeEffects/brand/contracts/illustration.contract.md`
- Living Cover system spec: `/Users/mike/Agents_CascadeEffects/references/skills/long_form_video_production_v1/references/living_cover_system_spec_v1.md`

## Visual Carrier Policy

- Primary lane: `cascade-paper-architectures-ink-lit-v1`
- Carrier type: `generated_raster_source_art`
- Generation tool: Codex built-in ImageGen through the `imagegen` skill when source-art generation is explicitly opened.
- Canvas target: `1920x1080`
- Role: long-form Living Cover backplate candidate.
- Source-art status: `blocked_pending_visual_system_keep`
- Source-art exception status: `none`

Sourced aircraft photos, accident imagery, cockpit photos, investigative documents, and old 737 visual research may guide historical/source-reference review, but they are reference evidence only. They are not active source art unless a later human-approved source-art exception names exact paths, rights/source risk, reason, and affected outputs.

HTML, CSS, SVG, canvas, and FFmpeg may only provide proof shell, timing, rail, captions, deterministic typography, safe-zone layout, masks, transforms, and layer compositing over approved raster/source art.

## Recognizability Ladder

- Public anchor: unbranded 737 MAX-family nose and enlarged LEAP engine profile, viewed as a clean model-lit aircraft cutaway/tableau rather than a crash image.
- Evidence object: single angle-of-attack vane/sensor cue, stabilizer trim wheel or horizontal-stabilizer mechanism, training/certification paper forms.
- System clue: dry cyan vellum signal path from one sensor toward a hidden MCAS/stabilizer correction path, kept non-liquid and non-diagnostic.

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
- MCAS represented as a visible cockpit screen, robot, villain, or sci-fi AI.
- Face-forward pilots, victims, executives, public officials, or recognizable real people.
- Dense evidence-board collage, arrows, diagnostic connector lines, or procedural UI graphics as viewer-facing source art.
- Gritty documentary noir, smoke, debris, high-frequency paper grain, sandy surface, or texture-heavy rendering.
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
2. The Airplane Had Changed
3. Software Made It Familiar
4. One Sensor Was Enough
5. Training Followed The Sales Promise
6. Procedure Before Architecture
7. The Familiar Story Failed

Rail copy must be viewer-facing and episode-specific. Record `stale_cross_episode_label_read`, `right_rail_text_boundary_read`, `out_of_rail_text_read`, and `ordinal_chapter_label_read` before rough assembly.

## Source-Art Prompt Brief

Asset type: long-form Living Cover source-art candidate, 16:9, text-free raster backplate.

Archetype: ink-lit Aircraft Mechanism Tableau / familiar airplane with hidden correction path.

Prompt:

`A 1920x1080 ink-lit Paper Architecture scene of an unbranded Boeing 737 MAX-family aircraft nose and enlarged forward high-mounted engine profile, cream folded-paper fuselage and wing cross-section, the larger LEAP engine placement made visibly different, a small angle-of-attack vane sensor cue on the nose, a subtle horizontal-stabilizer trim mechanism in the background, training and certification paperwork suggested only as blank folded paper forms, one dry cyan vellum signal trace from a single sensor toward a hidden stabilizer correction path, restrained coral warning accent, deep ink-blue field, warm cream paper forms, muted lavender shadows, foam-core cut edges, translucent vellum, controlled model-aircraft lighting, sparse editorial composition, right side kept lower-detail and title-safe for a fixed rail, no readable text, no labels, no logos, no airline livery, no tail number, no crash scene, no wreckage, no fire, no explosion, no victims, no face-forward people, subtle paper fiber only, clean low-detail paper planes, no speckle/noise/grain/grit/sandy texture, dry cyan vellum signal trace, no water/waterfall/river/stream/canal/channel/liquid spill/glowing watercourse`

Avoid list:

`crash, wreckage, explosion, fire, ocean impact, falling aircraft, disaster spectacle, readable text, Boeing logo, airline logo, tail number, airline livery, MCAS screen text, AI robot, villain figure, pilots faces, victims, executives, public officials, dense evidence board, arrows, UI overlays, diagnostic connector lines, gritty documentary noir, smoke, debris, high-frequency paper grain, sandy surface, water, waterfall, river, liquid blue channel, generated title lettering`

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
- slow model-light drift across the unbranded aircraft source plate
- subtle vellum glow fluctuation along the single-sensor signal cue
- restrained stabilizer/trim shadow shift only if it remains source-integrated
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

No review ask remains active for this plan. It is superseded by the long-form style correction and must be replaced with a non-Paper-Architecture visual-system plan before source-art generation can reopen.

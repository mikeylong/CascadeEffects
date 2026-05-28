# Tacoma Narrows Long-Form Visual System Plan

Date: 2026-05-17

Workflow: `long_form_video_production_v1`

Gate: `visual_system_plan`

Disposition: `visual_review_surface_ready`

Primary visual review artifact: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/visual_system_review_20260517/review.html`

Primary visual review artifact SHA-256: `da5d51c242360481fa7610c61e72fad6703c9da3a7513d847a0cac1a08452e8e`

Visual review surface manifest: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/visual_system_review_20260517/manifest.json`

Visual review surface manifest SHA-256: `dfcc0c99275d1db5d8f91870292169e604dbd3e1b4fef4d7baecfd3b564c0f73`

## Direction

Use `living_cover_system_v1` with `fixed_16x9_right_rail_v1` for a source-preserving Tacoma Narrows Living Cover. The public anchor is the bridge itself: sourced or source-derived bridge motion/collapse evidence, not generic Paper Architecture and not an abstract evidence-board scene.

This packet plans the visual system only and now includes an HTML visual review surface so the gate can be reviewed visually. The HTML surface is a deterministic composition over sourced Tacoma frames for review only. It does not mark source art `keep`, generate motion, build a cue map, assemble a rough proof, render a final MP4, upload, or publish.

## Approved Inputs

- Kept audio: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/final/Ep5_Tacoma-Narrows.wav`
- Audio SHA-256: `de593cc6e4a554507f45a0289177a31b321a2017caca361287315d85cca7e2bf`
- Locked narration script: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/Ep5_Tacoma-Narrows.txt`
- Script SHA-256: `08ae7837e0f01ac9a281f631b9d678dcd27ed9186946a1a50bd685fa42db586a`
- Timing source: `/Users/mike/Audio_CascadeEffects/tmp/ep5_tacoma_narrows_production/transcripts_mastered/Ep5_Tacoma-Narrows.whisperx.json`
- Timing source SHA-256: `b16db284d29cbb496984117ccc00d8d3462538648eef26f03c791ab05a8ebd4e`
- Existing Short bridge: pass-07 CRT visible scanline Short, status `keep`, publish package deferred.
- Brand design contract: `/Users/mike/Web_CascadeEffects/brand/contracts/design-system.contract.md`
- Illustration contract: `/Users/mike/Web_CascadeEffects/brand/contracts/illustration.contract.md`
- Living Cover system spec: `/Users/mike/Agents_CascadeEffects/references/skills/long_form_video_production_v1/references/living_cover_system_spec_v1.md`

## Visual Carrier Policy

- Primary lane: `cascade-ink-lit-photoreal-v1` / source-preserving public-scene carrier.
- Current visual review surface carrier: `sourced_raster_source_art` composed into a fixed `1920x1080` Living Cover review frame, with `fixed_16x9_right_rail_v1`.
- Current visual review surface status: `review_ready_human_keep_pending`, not source-art `keep`.
- Approved carrier candidates for the next review packet:
  - sourced raster/source frame from verified Tacoma Narrows bridge footage,
  - hybrid sourced raster with deterministic rail/title/caption composition,
  - generated raster only if it is explicitly reference-anchored and passes historical/source-reference review.
- Paper Architecture is allowed only for chapter-card, diagram, or package support after review; it is not the primary Tacoma Living Cover backplate.
- CSS, SVG, canvas, and procedural drawings may only provide proof shell, rail, captions, timing, deterministic typography, masks, and layer compositing over approved raster/source imagery.
- No procedural cyan signal lines, airflow traces, route overlays, diagnostic connector lines, or UI paths may be drawn over the source bridge imagery unless a later human-approved visual-system update scopes them narrowly.

## Historical And Source Reads Required Before Source-Art Keep

- `historical_accuracy_read`
- `source_reference_alignment_read`
- `public_anchor_geometry_read`
- `tacoma_bridge_motion_read`
- `bridge_deck_slenderness_read`
- `torsional_motion_source_read`
- `source_provenance_read`
- `rights_and_content_id_risk_read`
- `no_generated_misleading_collapse_read`
- `human_presence_read`: `not_applicable` unless the selected source frame includes people
- `no_recognizable_faces_read`: `not_applicable` unless the selected source frame includes people

## Living Cover System

- `living_cover_system_version`: `living_cover_system_v1`
- `rail_preset_id`: `fixed_16x9_right_rail_v1`
- `override_status`: `none`
- Canvas: fixed `1920x1080`, `16:9`
- Rail: right rail, `760px`, episode-local palette sampled from the approved bridge source plate.
- Caption process: `living_cover_captioning_process_v1`
- Caption output model: `dual_visible_rail_and_youtube_vtt_sidecar`
- Caption text source: locked narration script only.
- Caption timing source: WhisperX/VTT/SRT timing only.
- Required caption reads before rough assembly:
  - `caption_text_matches_script_read`
  - `caption_alignment_coverage_read`
  - `caption_asr_text_not_used_read`
  - `caption_known_regression_fixture_read`

## Chapter And Rail Spine

Use the Episode Package Gate chapter spine as the first rail data source:

1. The Bridge Was Already Moving
2. The Boundary Of A Model
3. The Design That Got Built
4. Galloping Became Normal
5. Five Conditions Before The Cable Was Spun
6. The Air Fed The Twist
7. The Profession Changed
8. The Model Stopped Matching The World

Rail copy must be viewer-facing and episode-specific. Record `stale_cross_episode_label_read` before rough assembly.

## Cue Map Requirements

The next packet after a visual-system keep must create a dedicated `living_cover_cue_map` before rough assembly. It must include chapter shifts, key phrase typography, 4 to 6 effect-map or cascade-diagram moments, caption/rail coordination, outro/end-screen timing, and source-safe treatment reads.

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

The next motion-readiness path must create a packet-local `living_cover_ambient_effects_layer` before rough assembly. Preferred lanes for Tacoma are source drift/lighting, restrained film-gate or projector micro-life, and source-safe motion emphasis from the approved bridge plate. `none` or `minimal` is allowed only with review rationale.

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

## Blocked Until Later Gates

- Source-art keep: blocked pending source/reference review.
- Cue map: blocked pending visual-system keep.
- Ambient/effects layer: blocked pending visual-system keep.
- Motion readiness: blocked pending source-art/cue/ambient readiness.
- Rough assembly: blocked pending visual-system keep, cue map, ambient/effects layer, and script-locked caption package.
- Final assembly: blocked, no rough assembly keep.
- Publish readiness: blocked, no final assembly keep.
- YouTube upload and public release: blocked.

## Review Ask

Review the visual surface first, then choose one:

- `keep visual system`
- `tighten visual system` with exact notes
- `reject visual system` with exact notes

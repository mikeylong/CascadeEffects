# Semmelweis Long-Form Visual System Plan

Date: 2026-05-18T20:46:09-0700

Workflow: `long_form_video_production_v1`

Gate: `visual_system_plan`

Disposition: `review_ready_human_keep_pending`

Primary review artifact: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/visual_system_review_20260518/review.html`

Visual review manifest: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/visual_system_review_20260518/manifest.json`

## Direction

Use `living_cover_system_v1` with `fixed_16x9_right_rail_v1` for a Semmelweis Living Cover built around the **Autopsy to ward** thesis. The source-art target is an 1840s Vienna General Hospital institutional interior where anonymous physicians or students move from an autopsy-room context toward a maternity ward, with a chloride-of-lime wash basin as the threshold object between harm and intervention.

This packet plans the visual system only. It does not create source-art candidates, mark source art `keep`, create a cue map, create an ambient/effects layer, create a music integration contract, assemble a rough proof, render a final MP4, upload, or publish.

## Approved Inputs

- Kept audio: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/final/Ep4_Semmelweis.wav`
- Audio SHA-256: `bf7562029466226f6bf33d64829ea41712220e63e4c5f37918cff53ec0fa1ebf`
- Audio duration: `850.825578` seconds
- Locked narration script: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/Ep4_Semmelweis.txt`
- Script SHA-256: `2bca08c0899da81a909d550a76dc0e2cb6ddccaa764b8c45ad9298c918276d68`
- Timing source: `/Users/mike/Audio_CascadeEffects/tmp/ep4_semmelweis_longform_20260518T193358Z/transcripts_mastered/Ep4_Semmelweis.diarized.srt`
- Timing source SHA-256: `f09cae647f2aadfc6354bd6cc04c23630e8464cb73ea07ae155536c08ad6f0e4`
- Episode package gate: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/episode_package_gate_audio_keep_20260518.md`
- Episode package gate SHA-256: `67c347cd31be0edd7bf033b3e24ab749abec9f571b7939031b6468b01a71d46e`
- Brand design contract: `/Users/mike/Web_CascadeEffects/brand/contracts/design-system.contract.md`
- Brand design contract SHA-256: `9d7d8870a63cd6ee0e95112abce451b9a792c4a135dedff18b9fae90aaf057ba`
- Illustration contract: `/Users/mike/Web_CascadeEffects/brand/contracts/illustration.contract.md`
- Illustration contract SHA-256: `42d324ad268170875d6499a856a007788dd11636964fd0a6f7a5eed9010aaaa0`
- Living Cover system spec: `/Users/mike/Agents_CascadeEffects/references/skills/long_form_video_production_v1/references/living_cover_system_spec_v1.md`
- Living Cover system spec SHA-256: `48e326d806b53a979bf850d20f5e8dfd2f2f8de3d85e62b9450f100c1a9da917`

## Visual Carrier Policy

- Primary lane: `generated_raster_source_art`.
- Generator: Codex ImageGen via the `imagegen` skill and built-in `image_gen`.
- Style package: `cascade-paper-architectures-ink-lit-v1`.
- Output target for future source-art candidates: `1920x1080`.
- No archival, source-preserving, sourced-raster, or deterministic-composition source-art exception is approved by this packet.
- Existing Semmelweis Short assets are bridge/reference candidates only. They are not long-form source art, not a visual-system input, and not imported into this gate.
- HTML, CSS, SVG, canvas, and local scripts may only provide review surfaces, rail layout, masks, captions, timing, deterministic typography, and assembly over approved raster assets. They may not become the source-art backplate.

## Source-Art Target

Future source-art candidates should stay inside the selected Autopsy-to-ward thesis:

1. **Threshold transfer**: a dim 1840s institutional corridor or doorway between an autopsy-room context and maternity ward, with anonymous physicians/students crossing the threshold.
2. **Basin hinge**: a chloride-of-lime wash basin or wash station in the foreground, positioned as the visible intervention between cadaverous contact and bedside care.
3. **Ward consequence**: a restrained maternity-ward context implied by beds, curtains, or institutional depth, without close-up mothers, babies, suffering bodies, gore, or horror staging.

Hard bans for candidates: readable text, labels, logos, generated title copy, gore, autopsy spectacle, close-up identifiable faces, close-up mothers or babies, medical-horror lighting, gritty documentary texture, bright/daylight Paper Architecture, high-frequency speckle, noisy grain, sandy surfaces, and decorative cyan/coral markers that read as UI artifacts.

## Historical And Source Reads Required Before Source-Art Keep

- `historical_accuracy_read`
- `source_reference_alignment_read`
- `public_anchor_geometry_read`
- `vienna_general_hospital_context_read`
- `maternity_ward_context_read`
- `autopsy_to_ward_transfer_read`
- `chloride_of_lime_basin_read`
- `no_gore_or_medical_horror_read`
- `human_presence_read`
- `no_recognizable_faces_read`
- `no_close_up_mothers_or_babies_read`
- `texture_noise_read`
- `source_provenance_read`
- `rights_and_content_id_risk_read`

## Living Cover System

- `living_cover_system_version`: `living_cover_system_v1`
- `rail_preset_id`: `fixed_16x9_right_rail_v1`
- `override_status`: `none`
- Canvas: fixed `1920x1080`, `16:9`
- Rail: right rail, `760px`, episode-local dark institutional palette sampled from approved source art.
- Caption process: `living_cover_captioning_process_v1`
- Caption output model: `dual_visible_rail_and_youtube_vtt_sidecar`
- Caption text source: locked narration script only.
- Caption timing source: SRT/WhisperX timing only.

Required caption reads before rough assembly:

- `caption_text_matches_script_read`
- `caption_alignment_coverage_read`
- `caption_asr_text_not_used_read`
- `caption_known_regression_fixture_read`

## Chapter And Rail Spine

Use the Episode Package Gate chapter spine as the first rail data source:

1. The Ward Had The Numbers
2. The Data No One Wanted
3. The Difference Was In The Hands
4. The Wash Changed The Ledger
5. Evidence Without A Theory
6. The Accusation Inside The Cure
7. The Result Was Visible First

Rail copy must be viewer-facing and Semmelweis-specific. Record `stale_cross_episode_label_read` before rough assembly.

## Cue Map Requirements

The next packet after a human visual-system `keep` must create a dedicated `living_cover_cue_map` before rough assembly. It must include chapter shifts, key phrase typography, 4 to 6 effect-map or cascade-diagram moments, caption/rail coordination, outro/end-screen timing, and source-safe treatment reads.

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

The next motion-readiness path must create a packet-local `living_cover_ambient_effects_layer` before rough assembly. Preferred lanes for Semmelweis are minimal source drift, subdued institutional light, restrained basin/glass highlight, and light dust or air movement only if it does not become grit or medical-horror texture. `none` or `minimal` is allowed only with review rationale.

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

## Music Integration Contract Requirements

Before rough assembly, create a packet-local `music_integration_contract`. Use the Challenger-style intro/outro contract unless a later human-approved Semmelweis alternate or no-music waiver is recorded.

Required reads include approved intro/outro sources, voice-start offset, caption timing shift, full outro source, end-screen handoff, final-VO-to-outro blend plan, transition review sample, level/masking reads, music rights read, and `music_contract_regression_read`.

## Blocked Until Later Gates

- Source-art generation: blocked pending visual-system `keep`.
- Source-art keep: blocked pending generated candidates and historical/source-reference review.
- Cue map: blocked pending visual-system `keep`.
- Ambient/effects layer: blocked pending visual-system `keep`.
- Music integration contract: blocked pending visual-system `keep`.
- Motion readiness: blocked pending source-art/cue/ambient/music readiness.
- Rough assembly: blocked pending visual-system `keep`, source-art `keep`, cue map, ambient/effects layer, music contract, and script-locked caption package.
- Final assembly: blocked, no rough assembly `keep`.
- Publish readiness: blocked, no final assembly `keep`.
- YouTube upload and public release: blocked.

## Review Ask

Review this visual-system direction, then choose one:

- `keep visual system`
- `tighten visual system` with exact notes
- `reject visual system` with exact notes

# Shorts Motion Backend Policy

Use this reference with `youtube_shorts_production_v1/SKILL.md` and the source-preserving documentary promotion workflow when planning or reviewing motion candidates.

During the Challenger-first restart, this file is a legacy model-experiment reference. None of its backend, matrix, prompt, or pass-limit rules are active unless the current DP-approved episode constraint ledger imports and activates them for the scoped short.

## Standard Motion Matrix

- These legacy defaults may be used only when the active ledger approves them.
- When archival motion is the strongest lane, the standard matrix expands from still-driven I2V only to a source-first comparison of `direct_source_clip`, `source_derived_reanimation`, and `still_driven_i2v` candidates where each strategy is approved upstream.
- Motion strategy must follow the current `production_model_decision`. If the lane is `source_led_motion` or `source_derived_reanimation`, generated stills are exception-only and require a passing render authorization note.
- The proven baseline motion lane stays default: `distilled` using `mlx-community/LTX-2-distilled-bf16`.
- The standard comparison lane is Apple-native LTX 2.3 MLX Q8: `apple-ltx23-q8-one-stage` using `dgrauet/ltx-2.3-mlx-q8` plus `mlx-community/gemma-3-12b-it-4bit`.
- Render both baseline and comparison lanes in the motion contact sheet before choosing selected winners for a motion video proof.
- Motion contact-sheet candidates and downstream motion proof clips must target at least `5.0` seconds each. If a beat is shorter than that, use `5.0` seconds as the proof floor rather than rendering a shorter test clip.
- The `5.0` second floor is for diagnostic motion handles. A motion video proof must be assembled from a shot-level `shot_timing_edl` with actual story-shot durations and no hidden source-native cuts.
- Motion contact-sheet candidates are visual-only assets. Any backend-generated audio or source-retained audio must be stripped before motion review, motion contact sheets, or motion video proof assembly. The only approved audio in a proof is the coordinator-approved short audio track.
- If a selected winner has `texture_influence: house_crt`, preserve that intent through proof, but apply the publishable house CRT/signal-interruption treatment at the video-final entry gate before captions/audio. Texture does not change the winning motion backend and cannot rescue a failed motion candidate.
- The standard motion contact sheet comparison is four candidates per eligible source still: two `distilled` candidates and two `apple-ltx23-q8-one-stage` candidates with matched seed slots.
- Candidate A uses the canonical beat motion prompt.
- Candidate B uses the beat-class stability prompt for `locked context`, `human/tableau`, or `documentary anomaly`.
- Use denser sampling than 1fps when short-lived defects matter.
- Review every completed motion clip by actual playback before surfacing it. For launchpad, plume, vehicle, rigid-geometry, historical machinery, explosion, or other physics-sensitive beats, add frame-by-frame or near-frame-by-frame inspection; sparse thumbnails are not enough.

## Review Metadata

Motion candidate review notes and contact sheets must record:

- `beat_id`
- `source_still_path`
- `source_still_variant_role`
- `motion_pipeline`
- `model_repo`
- `text_encoder_repo` when applicable
- `audio_stream_read`
- `normalized_no_audio_path` when the raw backend output included audio
- `motion_strategy`: `direct_source_clip|source_derived_reanimation|direct_source_still|still_driven_i2v|generated_still|hybrid_generated`
- `source_clip_id` and `source_clip_path` when applicable
- `source_span_in` and `source_span_out` when applicable
- `start_keyframe_path` and `end_keyframe_path` for source-derived reanimation
- `same_camera_span_confirmed`
- `keyframe_crop_consistency`
- `archival_fidelity_read`
- `historical_signal_profile_id`, `texture_source_lane`, `texture_applied_path`, `signal_texture_strength`, `texture_visibility_read`, `house_crt_texture_read`, `signal_interruption_read`, `youtube_survival_proxy_path`, `youtube_survival_read`, `compression_artifact_read`, `detail_survival_read`, and `historical_signal_texture_read` when house CRT texture is applied
- `seed`
- `prompt_variant_id`
- prompt text or prompt path
- raw and normalized clip paths
- `review_method`
- `temporal_coherence_read`
- `physical_plausibility_read`
- `source_motion_alignment_read`
- disposition
- whether the clip is selected for the motion video proof
- `shot_timing_edl_path` and `contact_sheet_to_proof_parity_read` when a clip enters proof assembly

Reject a candidate immediately if it invents a different event than the source still implies, including invented ignition, plume, liftoff, impossible smoke/flame motion, or rigid-structure drift that breaks the historical shot.

## Shot Timing EDL And Proof Parity

- Before motion video proof, create an EDL with one row per actual story shot, not one row per beat handle.
- Each EDL row records parent beat ids, source clip/still path, source span, intended and actual duration, continuity vector, and `no_internal_cut_read`.
- Normal story shots must be at least `2.0` seconds unless a coordinator-approved episode rule records a waiver.
- Source-native camera cuts, fades, and flashes are real edits; split them into valid EDL rows or choose a cleaner span.
- Motion proof review must pass `proof_assembled_from_shot_timing_edl`, `contact_sheet_to_proof_parity_read`, `hidden_cut_read`, and `story_shot_duration_read`.
- If proof assembly drifts from the selected motion contact sheet or EDL, block final export and route back to motion contact/EDL repair.

## Source-Derived Archival Reanimation Rule

- Prefer `direct_source_clip` when a clean archival clip already solves the beat.
- Use `source_derived_reanimation` when clean archival footage provides the right visual language but the edit needs timing control, a beat-length handle, or a steadier source-preserving cadence.
- Source-derived reanimation candidates must use clean source spans from the DP archival footage review and selected keyframes from the same continuous camera shot.
- Do not keyframe across different camera angles, scenes, source videos, or footage families.
- Do not use still-driven I2V to invent event-level motion or unsupported human behavior. If the source shot does not already imply the event, route to direct source footage or source-derived keyframes.
- Strip backend-generated or source-retained audio before review or proof assembly. The raw audio stream may be noted for diagnostics only; it is never proof audio.
- Human, clinical, office, courtroom, and control-room reanimation must preserve role, posture, subject count, room layout, and equipment position. Invented sit/stand action, facial identity drift, new people, or medical action is a `reject` unless present in the clean source span and approved by DP.

## Launch And Ascent LTX Rule

- For launchpad, liftoff, ascent, plume, explosion, or other event-level aerospace motion, prefer `direct_source_clip` when clean archival footage already solves the beat.
- If LTX must create a launch/ascent handle, use source-derived keyframe interpolation from clean start and end frames in the same continuous camera shot. Keep crop, scale, camera angle, and source family consistent between keyframes.
- Use Apple-native LTX keyframe mode with the dev transformer for keyframe interpolation. Do not use the distilled one-stage still path for launch/ascent interpolation.
- Do not keyframe across different source camera angles. Do not ask a static pad-hold still to become ignition, liftoff, plume growth, or ascent without a real matching end keyframe from the same event.
- Record `motion_pipeline: apple-ltx23-keyframe-dev`, `start_keyframe_path`, `end_keyframe_path`, `source_clip_path`, `source_span`, and dense frame-audit artifacts before the candidate can enter motion review.

## Backend Promotion Rules

- Apple-native LTX 2.3 remains a beat-local comparison lane until a candidate wins beat-local A/B review.
- One hard-case backend win never authorizes a short-wide or episode-wide model swap.
- A timed A/B comparison proof may include both model families only when explicitly labeled diagnostic.
- Timed A/B proofs are not final-export eligible until selected winners are reviewed as `keep`.
- Motion proofs are not final-export eligible until the final-export gate has either a validated house CRT/signal-interruption manifest or an explicit coordinator waiver. Active Shorts use the Challenger-calibrated `era_1980s_broadcast_crt_v1` house texture at `visible_but_premium` plus randomized Challenger-style `0.25s` signal interruption at eligible story cuts; do not choose alternate profiles by source era.
- The standard four-candidate dual-model motion matrix counts as one planned comparison pass for a keeper still.
- Any rerender after that matrix requires a recorded prompt, still, or carrier decision; do not keep spending motion passes on the same failure mode.

## Beat-Class Prompt Guardrails

- New backend tests split motion prompts by beat class: `locked context`, `human/tableau`, and `documentary anomaly`.
- Apple-native LTX 2.3 `human/tableau` prompts must use concrete social roles, fixed positions, fixed-room/object locks, and no objects entering or leaving frame.
- Avoid abstract micro-body-motion phrases and chair/seat-negation wording that can trigger unwanted sit/stand behavior or furniture hallucination.
- If motion exposes a source-baked still defect, route back to stills rather than trying to repair anatomy with motion rerenders.

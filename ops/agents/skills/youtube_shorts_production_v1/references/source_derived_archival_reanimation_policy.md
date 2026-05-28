# Source-Derived Archival Reanimation Policy

Use this policy with the Shorts coordinator, DP skill, visual style package, and motion promotion workflow whenever visual research imports archival or documentary motion media.

## Intent

`source-derived archival reanimation` is the source-first lane between direct archival clip use and fully generated imagery. It uses clean archival motion media as the visual authority, extracts source frames/keyframes from reviewed spans, and generates beat-length LTX motion handles that preserve the source shot's archival fidelity while giving the editor control over timing, pacing, and emphasis.

This lane exists to avoid unnecessary Flux still generation when source footage already gives the short a strong visual language.

## Canonical Shape

The top-level Shorts flow stays ordered and source-first:

`script -> audio -> narration map -> DP scope/research brief -> visual research packet -> production model decision -> visual beatmap -> shot_plan_v2 -> episode constraint ledger -> render authorization check -> stills/keyframe contact sheet -> stills video proof when needed -> motion contact sheet -> shot_timing_edl -> motion video proof -> video final -> keeper lesson capsule`

When source-derived archival reanimation is active, the middle visual stages carry these meanings:

- `visual research packet`: finds clean motion spans and ranks them for engagement, mechanism visibility, motion potential, and reanimation suitability.
- `production model decision`: chooses whether the short should be source-led, source-derived, sourced-still led, generated-still led, or hybrid before the visual beatmap is locked.
- `visual beatmap`: maps beats to footage families, source spans, and possible keyframe pairs; it does not require one literal image per narration clause.
- `shot_plan_v2`: chooses whether each shot is best served by `direct_source_clip`, `source_derived_reanimation`, `direct_source_still`, `still_driven_i2v`, or `generated_still`.
- `render authorization check`: blocks generated stills when a sourced still/clip or source-derived reanimation already solves the shot.
- `stills/keyframe contact sheet`: becomes a source-frame/keyframe selection gate when archival motion is the active lane. It may review clean frame exports and proposed start/end keyframes rather than AI-generated stills.
- `stills video proof`: tests source-frame pacing against approved audio; it may use selected archival frames without generated replacements.
- `motion contact sheet`: compares actual motion handles: direct source clip trims, source-derived LTX keyframe handles, and still-driven I2V only for beats where event invention is not required.
- `shot_timing_edl`: turns selected handles into actual story-shot timing and exposes hidden source-native cuts before proof.
- `motion video proof`: assembles reviewed no-audio motion winners from the EDL against the approved short audio.

## Archival Cleanup Scout

When archival clips are full-bleed vertical crops from low-resolution sources, run a conservative `archival_cleanup_scout` before applying restoration to an active motion contact sheet or proof. This scout is a diagnostic gate, not proof authorization.

Use representative rows first: one control-room or human/process row, one pad/shuttle or machinery row, one ignition/ascent or event-motion row, and the current tail endpoint when the short depends on archival event footage.

The scout must compare:

- `baseline`: the current normalized no-audio MP4 from the active motion contact sheet.
- `conservative_clean`: a source-preserving FFmpeg cleanup lane using deblock/denoise, high-quality scale, and light sharpening.

Record this metadata per row:

- `source_resolution`
- `crop_width_px`
- `upscale_factor`
- `enhancement_lane: conservative_ffmpeg`
- `restoration_recipe_id`
- `enhancement_read: pass|tighten|reject|pending_human_review`
- `artifact_read: pass|tighten|reject|pending_human_review`
- `source_limit_read: pass|reject_for_quality|pending_human_review`

Promotion requires visible improvement without halos, waxy faces, temporal shimmer, crushed shadows, added text/logos, or damaged shuttle/vehicle/human geometry. If the crop is too destructive, mark the beat `source_limit_read: reject_for_quality` and route to better archival source search for that beat.

Do not use AI upscaling, face restoration, synthetic detail invention, or a global modern-HD look unless a later explicit workflow scope approves a separate experiment. Conservative cleanup outputs must stay visual-only and full-bleed when they are candidates for active motion use.

## House CRT Signal Texture

The house CRT/signal-interruption treatment is the standard final-gate finishing substep for active Cascade Effects Shorts motion. It happens at `video final` entry after a motion proof is approved and before captions or final audio are applied. It is not a replacement for motion review and cannot rescue malformed motion, weak source selection, failed hygiene, or failed frame QA.

Use the shared signal profile registry at `/Users/mike/CascadeEffects/archive/season-01-reference/legacy-style-packages/style-packages/source_preserving_documentary_v1/archival_signal_texture_recipes.json`.

Default recipe policy:

- Use `era_1980s_broadcast_crt_v1` at `visible_but_premium` as the cross-episode house clip texture, calibrated from the Challenger/shuttle treatment.
- Do not use era-specific archival-footage textures as active defaults. Film grain/newsreel, institutional-video, 1990s-news, 2000s-web, and 2010s-mobile profiles are legacy references unless a later explicit global-policy decision reactivates one.
- Use Challenger-style randomized signal interruption only at eligible story-clip cuts. It mutates the outgoing footage's final `0.25s` with horizontal analog signal breaks, varies per cut, and must not become a continuous overlay or full-frame static replacement.

All texture outputs must remain full-bleed, visual-only, no TV frame, no matte, no rounded screen mask, no border, and no reduced image area. A captioned final may advance only when the final-export manifest records a validated house CRT/signal-interruption context or an explicit coordinator waiver.

Record this metadata for every textured candidate:

- `historical_context_year_or_range`
- `source_media_era`
- `historical_signal_profile_id`
- `texture_source_lane`
- `texture_applied_path`
- `signal_texture_strength`
- `texture_application_scope`
- `youtube_survival_proxy_path`
- `texture_visibility_read: pass|tighten|reject|pending_human_review`
- `house_crt_texture_read: pass|tighten|reject|pending_human_review`
- `signal_interruption_read: pass|tighten|reject|not_applicable|pending_human_review`
- `historical_signal_texture_read: pass|tighten|reject|pending_human_review`
- `youtube_survival_read: pass|tighten|reject|pending_human_review`
- `compression_artifact_read: pass|tighten|reject|pending_human_review`
- `detail_survival_read: pass|tighten|reject|pending_human_review`
- `historical_signal_texture_read: pass|tighten|reject|pending_human_review`
- `texture_visibility_read: pass|tighten|reject|pending_human_review`
- `texture_failure_mode`

Reject or downgrade texture when it causes shimmer, mud, scanline banding, fake CRT gimmick read, face/detail loss, vehicle/machinery/plume/debris readability loss, fake text/logo/caption contamination, or signal interruption that reads as a mask over story footage. Fallback order is lower CRT strength, then `conservative_clean`, then `baseline`, then better source search.

## Strategy Values

Use these values consistently:

- `direct_source_clip`: a clean archival clip already solves the beat.
- `source_derived_reanimation`: LTX or another motion backend generates a beat-length handle from clean source frames/keyframes from the same reviewed source span.
- `direct_source_still`: a clean source frame is enough for a still proof or a very low-motion beat.
- `still_driven_i2v`: a selected still is animated, but the requested motion must not invent a new historical event.
- `generated_still`: source media does not provide the needed shot; generated stills are exception-only.
- `hybrid_generated`: generated or composited material is used with explicit source anchors and active ledger approval.

## Required Metadata

Every `source_derived_reanimation` candidate must record:

- `source_clip_id`
- `source_clip_path`
- `source_url_or_origin`
- `source_span_in`
- `source_span_out`
- `footage_family_id`
- `reanimation_backend`
- `motion_pipeline`
- `start_keyframe_path`
- `end_keyframe_path`
- `same_camera_span_confirmed`
- `keyframe_crop_consistency`: `pass|tighten|reject`
- `source_hygiene_status`: `pass|reject`
- `raw_motion_path`
- `normalized_no_audio_path`
- `audio_stream_read`: `none|source_retained|backend_generated|unknown`
- `frame_audit_paths`
- `temporal_coherence_read`: `pass|tighten|reject`
- `physical_plausibility_read`: `pass|tighten|reject`
- `source_motion_alignment_read`: `pass|tighten|reject`
- `archival_fidelity_read`: `pass|tighten|reject`
- `historical_signal_profile_id`, `texture_applied_path`, and texture review reads when `historical_signal_texture` is applied
- `disposition`: `keep|tighten|diagnostic only|reject`

## Hard Rules

- Prefer `direct_source_clip` when a clean archival clip already solves the beat.
- Use `source_derived_reanimation` when the source footage is visually right but the edit needs a different duration, cadence, or beat emphasis.
- Do not use generated stills just to animate a source-complete shot.
- Do not keyframe across different camera angles, different scenes, or different source families.
- Do not use one static still to invent event-level motion such as ignition, liftoff, explosion, machinery collapse, medical action, or human behavior that is not implied by the source.
- All motion candidates are visual-only. Strip backend-generated or source-retained audio before review, contact sheets, proof assembly, or final export.
- Preserve the source shot's visual authority. Apply the house CRT texture only after the underlying motion handle is reviewed as `keep`; do not use CRT or signal interruption to hide failed motion, failed hygiene, or weak source selection.
- Motion candidates must be reviewed from actual MP4 playback plus dense frame sampling. Physics-sensitive, human, machinery, and disaster-event beats require frame-by-frame or near-frame-by-frame QA.
- If reanimation produces identity drift, impossible body motion, impossible machinery behavior, source-defying event invention, warped geometry, absorbed archival contamination, or hidden text/logo leakage, mark the candidate `tighten` or `reject`.

## Human And Clinical Scene Guardrails

For human, clinical, courtroom, office, control-room, or other role-based scenes:

- Keep motion low-amplitude unless a clean source clip explicitly supports larger action.
- Prefer source-derived keyframes from the same camera setup over prompt-driven body motion.
- Preserve role, posture, room layout, equipment position, and subject count.
- Do not invent new people entering/leaving, sitting/standing, medical procedures, patient contact, or facial identity changes unless those actions are present in the source span and approved by the DP.
- For episodes like Therac-25, use archival-style clinical or machine-context footage as the source authority; do not invent a generic glossy clinical room when source media can provide a better historical texture.

## Challenger Teaching Example

The Challenger launch/ascent scout proved the lane:

- Direct source span: `00:03:07.000-00:03:12.000`
- Source family: `launch_exterior_broadcast`
- Method: Apple LTX keyframe dev interpolation from same-camera clean archival start/end frames
- Result: diagnostic no-audio motion handle preserved shuttle stack and plume behavior better than single-still I2V
- Rule learned: launch/ascent/plume beats block single-still I2V event invention and route to direct source clips or source-derived keyframe reanimation

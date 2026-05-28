# Promotion Workflow

Use this workflow after rendering. It turns the source-preserving documentary judgment layer into explicit promotion decisions for stills, motion clips, contact sheets, and video proofs.

During the Challenger-first restart, this file is a legacy reference library unless the active episode constraint ledger imports or activates a specific rule. It may not hydrate context from old folders, old renders, old manifests, experiments, casebooks, keeper registries, or previous episode constraints without an exact DP import.

For Cascade Effects YouTube Shorts, map this workflow to the coordinator sequence:

`fact-checked long-form script -> derived 60-second Short script -> audio -> narration map -> DP scope/research brief -> visual research packet -> production model decision -> visual beatmap -> shot_plan_v2 -> episode constraint ledger -> render authorization check -> stills/keyframe contact sheet -> stills video proof when needed -> motion contact sheet -> shot_timing_edl -> motion video proof -> video final -> keeper lesson capsule`

This workflow owns visual promotion decisions through `motion video proof`. It does not own `video final`; final caption overlays and publishable export route to `/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_final_export_v1/SKILL.md`.

Consult it together with:

- `judgment/subject_render_matrix.md`
- `judgment/review_rubric.md`
- `judgment/casebook.md`
- `judgment/keeper_registry.md`

For restarted Challenger production, consult those files only as scoped references. The active episode constraint ledger decides which rules control generation or promotion.

## Shared Vocabulary

Use only these dispositions:

- `keep`
- `tighten`
- `diagnostic only`
- `reject`

Additional reel class:

- `mixed review reel`: a reel containing any clip that is not `keep`
- `mixed review short`: a Shorts proof containing any still or motion clip that is not `keep`

## Gate 1: Stills Contact Sheet Before Stills Video Proof

Prerequisites:

- short audio is already `keep`
- short audio provenance is recorded and validated: `short_audio_package_path`, `expected_voice_profile_id`, `audio_package_sha256`, `audio_disposition`, `caption_source_path`, and `transcript_sha256`
- workflow scope manifest is DP-approved
- DP research brief is present
- visual research evidence packet is present
- production model decision is present and names the source/generation lane
- active episode constraint ledger is DP-approved and current
- render authorization has passed for the selected source surfaces or generated stills
- all input paths are inside the scope manifest or exact DP-approved imports
- each candidate still has a current review note
- the contact sheet path is recorded
- the default contact sheet review surface shows raw full-frame tiles with beat info visible directly on the sheet as minimal plain-text labels only
- if archival motion is in scope, the archival footage review is present and every sourced or hybrid archival span already has a clip-level hygiene decision

Contact-sheet review questions:

- Does each beat have enough candidate coverage to choose a current best still or name a gap?
- Does the selected still preserve subject identity and expose the mechanism?
- Does the selected still still read as the named research anchor or approved source family?
- If `coverage_class` is `object_cluster`, does the selected still preserve the full cluster read with at least two approved artifacts visible in-frame, rather than collapsing into one isolated hero object?
- Is the carrier still specific enough to avoid anonymous evidence-room drift?
- Does the selected still pass `coverage_read`, `variety_read`, and `engagement_read`, or has the sequence collapsed back into repetitive low-energy evidence coverage?
- Does the contact sheet itself preserve raw full-frame tiles while keeping beat info visible directly on the sheet, without borders, blurred fills, padded presentation cards, or other stylistic review treatments?
- If sourced or hybrid archival footage informed this still, does the source span also pass `hygiene_read` with no logos, stingers, lower-thirds, watermarks, burned captions, end cards, split screens, or channel bugs?
- Does the case keep clean generation authority intact, with `generation_source_paths`, `clean_candidate_path`, and the raw `contact_sheet_tile_path` all pointing to unembellished full-frame stills?
- Are any candidates blocked by text leakage, anatomy corruption, warped geometry, or hidden mechanism?

Promotion rule:

- Only selected or `keep` stills with `anchor_match: pass`, `coverage_read: pass`, `variety_read: pass`, `engagement_read: pass`, and `hygiene_read: pass` can enter `stills video proof`.
- For `coverage_class: object_cluster`, fewer than two visible approved artifacts is an automatic `tighten` or `reject`.
- `tighten`, `diagnostic only`, and `reject` stills stay in the still lane.
- Contact sheets are human-visible selection gates, not final outputs.
- A sidecar index may supplement the contact sheet, but it may not replace on-sheet beat labels on the default review surface.
- Do not apply a promotion rule from this workflow unless the active ledger imports or activates it for the current short.
- If a still has drifted into a generic evidence-room carrier, record `anchor_match: reject`, classify the failure as `anonymous evidence-room drift`, and route back to carrier planning or sourced fallback.
- If a sourced or hybrid still inherits logos, stingers, lower-thirds, watermarks, burned captions, end cards, split screens, or channel bugs from archival reference footage, record `hygiene_read: reject`, classify the failure as `absorbed archival contamination`, and route back to source-span or carrier planning.
- If a styled review plate, blurred-fill composite, framed tile, or other embellished review artifact is being reused as if it were a clean still source, record `generation_surface_read: reject`, classify the failure as `review-surface contamination`, and route back to clean-source preparation.

## Gate 2: Stills Video Proof Before Motion Contact Sheet

Prerequisites:

- the stills/keyframe contact sheet has been reviewed
- selected stills or named gaps are recorded
- the static proof uses approved short audio and preserves the validated package/transcript provenance
- the proof renders from `clean_candidate_path` / `clean_selected_still_path`, not from any embellished review artifact

Proof review questions:

- Does the static proof cover opening, middle, and closing beats?
- Do the selected stills read in the intended sequence against narration?
- Are pacing, timing, beat order, and visual variety acceptable before motion?

Promotion rule:

- Only beats with selected or `keep` source assets can enter motion candidate generation.
- `carrier_mode: sourced` and `carrier_mode: hybrid` are valid still inputs when they were explicitly reviewed and selected upstream.
- A selected sourced still or approved source clip family may advance without any intermediate generated still when the sourced asset already solves the shot.
- The default motion contact-sheet input is the approved source surface for the beat: selected source still, selected source clip, or selected source-derived keyframe pair. Direct source clips and source-derived reanimation handles may enter the motion grid when routed by the active coordinator and recorded upstream.
- Embellished review surfaces are never motion-authorizing still inputs, even when a backward-compatible alias like `copied_image_path` or `selected_contact_plate_path` exists in the manifest. Raw full-frame contact-sheet tiles are acceptable only when they are identical to the clean candidate still.
- If the static proof exposes a weak beat or missing carrier, return to the still lane.
- A diagnostic stills video proof does not authorize motion for unresolved beats.

## Gate 3: Motion Contact Sheet Before Motion Video Proof

Prerequisite:

- the active episode constraint ledger authorizes the motion backend/matrix rules for this short
- the source asset must already be selected or `keep`
- if archival motion is in scope, the source still or clip family must already have `hygiene_read: pass`
- motion contact-sheet candidates must target at least `5.0` seconds each, even when the underlying beat is shorter
- if the active ledger authorizes the legacy default still-driven motion matrix, compare both model families for each eligible still asset: two `distilled` candidates using `mlx-community/LTX-2-distilled-bf16` and two `apple-ltx23-q8-one-stage` candidates using `dgrauet/ltx-2.3-mlx-q8` plus `mlx-community/gemma-3-12b-it-4bit`
- if the active ledger authorizes source-derived archival reanimation, compare approved direct source clips against approved keyframe reanimation handles; record the source span and keyframes instead of treating the candidate as generic still-driven I2V
- the two seed slots must match across model families
- candidate A must use the canonical beat motion prompt
- candidate B must use the beat-class stability prompt for `locked context`, `human/tableau`, or `documentary anomaly`
- hard or motion-brittle beats must have a primary still plus one alternate motion-ready still before the matrix is rendered; hard beats include `human/tableau`, strict historical geometry, locked-context shots, or beats where motion already exposed source-baked defects

Required review questions:

- Was the actual MP4 reviewed end-to-end, rather than only the manifest row or a sparse contact-sheet thumbnail?
- Was dense frame sampling performed, and for launchpad, plume, vehicle, rigid-geometry, historical machinery, explosion, or other physics-sensitive beats, was the candidate checked frame-by-frame or near-frame-by-frame?
- Does each motion candidate preserve canonical subject identity across time?
- Does the anomaly stay plausible under motion?
- Does motion stay physically plausible relative to the source still or approved source clip, rather than inventing a different event?
- For source-derived reanimation, does the output preserve the source span's archival fidelity, camera setup, subject identity, and motion boundaries?
- Does the clip remain aligned with the source shot, or has motion introduced ignition, plume, liftoff, structural drift, or other source-defying behavior?
- Does motion clarify the subject instead of obscuring it?
- Is there temporal text leakage, edge tearing, liquid warping, geometry boil, or short-lived artifacting?
- If archival footage informed the motion, did the clip stay free of logos, stingers, lower-thirds, watermarks, burned captions, end cards, split screens, and channel bugs?
- If the motion problem is inherited from the still, was the still repaired upstream first?
- Did either model family win cleanly, or did both models fail in a way that requires still or carrier repair?
- Does any alternate still produce a better motion outcome without weakening the still-stage read?

Hard blockers:

- temporal anatomy corruption
- motion-induced warped geometry
- inherited still defects left unresolved
- readable text or UI leakage becoming more dominant in motion
- absorbed archival contamination
- source-defying event invention
- physically impossible flame, smoke, plume, or rigid-structure behavior

Promotion rule:

- A motion candidate may enter `motion video proof` only if the source asset is selected or `keep` and motion introduces no blocking artifact.
- Motion contact sheets must be grouped by beat, source asset, model family, prompt variant, and seed, and must preserve the still-stage `carrier_mode` and `anchor_match` record for each source asset.
- Motion contact sheets and motion review notes must also preserve `hygiene_read` for each sourced or hybrid archival lineage.
- Motion candidate notes must record `beat_id`, `motion_strategy`, `source_still_path` or `source_clip_path`, `source_still_variant_role` when applicable, `source_span_in`, `source_span_out`, `start_keyframe_path`, `end_keyframe_path`, `same_camera_span_confirmed`, `keyframe_crop_consistency`, `motion_pipeline`, `model_repo` when applicable, `text_encoder_repo` when applicable, `audio_stream_read`, `normalized_no_audio_path`, `seed`, `prompt_variant_id`, prompt text or prompt path, raw and normalized clip paths, `review_method`, `temporal_coherence_read`, `physical_plausibility_read`, `source_motion_alignment_read`, `archival_fidelity_read`, disposition, and whether the clip is selected for the motion video proof. When historical signal texture is applied, also record `historical_context_year_or_range`, `source_media_era`, `historical_signal_profile_id`, `texture_source_lane`, `texture_applied_path`, `signal_texture_strength`, `texture_visibility_read`, `era_match_read`, `youtube_survival_proxy_path`, `youtube_survival_read`, `compression_artifact_read`, `detail_survival_read`, and `historical_signal_texture_read`. Valid `motion_pipeline` values in the source-first lane are `direct_source_clip`, `direct_source_still`, `distilled`, `apple-ltx23-q8-one-stage`, and `apple-ltx23-keyframe-dev`.
- Valid `motion_strategy` values are `direct_source_clip`, `source_derived_reanimation`, `direct_source_still`, `still_driven_i2v`, `generated_still`, and `hybrid_generated`.
- Historical signal texture is a global optional substep after motion winners are selected and before motion video proof. Use `/Users/mike/Viz_CascadeEffects/references/style_packages/source_preserving_documentary_v1/archival_signal_texture_recipes.json`. Select profiles by era and medium: `era_1980s_broadcast_crt_v1` for Challenger-like 1980s TV/NASA/news footage, `era_1980s_institutional_video_v1` for Therac-like clinical/institutional footage, and later profiles for 1990s news, 2000s digital/web, or 2010s mobile/social sources.
- Texture outputs must be full-bleed, no-audio, and free of TV frames, mattes, rounded masks, borders, or reduced image area. Reject or downgrade texture for `texture_invisible_no_reviewable_historical_signal`, `historical_signal_overpowering_subject`, `compression_shimmer_or_mud`, `historical_signal_cheese`, `detail_loss_from_signal_texture`, `era_mismatch`, fake text/logo/caption contamination, or reduced face/vehicle/machinery/plume/debris readability.
- For launch/ascent/plume event motion, `apple-ltx23-keyframe-dev` candidates must record `start_keyframe_path`, `end_keyframe_path`, `source_clip_path`, `source_span`, and dense frame-audit artifacts. Do not promote a single-still I2V candidate that invents launch/ascent event motion from a static source still.
- The standard four-candidate dual-model matrix counts as one planned comparison pass. Further rerenders require a recorded prompt, still, or carrier decision.
- Use denser sampling than 1fps when short-lived defects matter.
- If motion exposes a source-baked issue, disposition the still as `tighten` and rerender upstream before attempting another motion pass.
- If both model families fail on the same still for the same reason, route back to stills instead of endlessly rerendering motion.
- If a launchpad-, plume-, vehicle-, or machinery-led beat invents ignition, plume, liftoff, or rigid-structure motion that the source still does not contain, route the beat to direct sourced archival motion or a new still/carrier choice instead of another still-driven rerender.
- If a human, clinical, office, courtroom, or control-room beat invents new people, role changes, medical action, sit/stand action, facial identity drift, or room-layout drift, route back to source span/keyframe selection instead of prompt tightening.
- Do not use motion rerenders as anatomy repair.

## Gate 4: Motion Video Proof Before Final Export

Prerequisites:

- every included clip already has a recorded motion review
- every included clip has a current disposition
- the motion proof uses approved short audio and preserves the validated package/transcript provenance
- a beat sheet is generated beside the proof and recorded as `beat_sheet_path`
- any sourced or hybrid archival lineage in the proof has already cleared `hygiene_read: pass`
- the proof is assembled from an approved `shot_timing_edl`
- `contact_sheet_to_proof_parity_read`, `hidden_cut_read`, and `story_shot_duration_read` are all `pass`
- any textured historical-signal lineage in the proof records `historical_signal_profile_id`, `texture_applied_path`, `texture_visibility_read`, `era_match_read`, `youtube_survival_proxy_path`, `historical_signal_texture_read`, `youtube_survival_read`, `compression_artifact_read`, and `detail_survival_read`

Keeper short rule:

- a `keeper short` may contain only `keep` motion clips
- a `keeper short` must use selected motion winners from the reviewed motion contact sheet, not unreviewed comparison clips

Mixed review short rule:

- if any included clip is `tighten`, `diagnostic only`, or `reject`, the proof must be labeled `mixed review short`
- timed A/B comparison proofs that include both model families are diagnostic unless all included clips are independently reviewed as `keep`; they are not final-export inputs until selected winners are assembled into a keeper proof
- mixed review shorts are internal review tools, not final-export inputs

No-placeholder rule:

- diagnostic placeholders are never allowed in a keeper short or `video final`

## Legacy Gate: Still Before Motion

Required review questions:

- Does the subject remain canonical?
- Does the anomaly read as a believable wrong state?
- Is the anomaly visible without prompt explanation?
- Does the camera actually expose the mechanism?
- Is there any text leakage, anatomy corruption, or source-baked defect?

Hard blockers:

- anatomy corruption
- readable text or logo leakage
- warped geometry used as surrogate surrealism
- a camera angle that hides the claimed failure mechanism

Promotion rule:

- Only `keep` source assets are eligible for motion promotion.
- `tighten`, `diagnostic only`, and `reject` stills stay in the still lane.
- If the still is unresolved, no downstream motion clip may be treated as a keeper.

## Legacy Gate: Motion Before Reel

Prerequisite:

- the source asset must already be `keep`

Required review questions:

- Does the clip preserve canonical subject identity across time?
- Does the anomaly stay plausible under motion?
- Does motion clarify the subject instead of obscuring it?
- Is there temporal text leakage, edge tearing, liquid warping, or geometry boil?
- If the motion problem is inherited from the still, was the still repaired upstream first?

Hard blockers:

- temporal anatomy corruption
- motion-induced warped geometry
- inherited still defects left unresolved
- readable text or UI leakage becoming more dominant in motion
- absorbed archival contamination

Promotion rule:

- A motion clip may be `keep` only if the source asset is `keep` and motion introduces no blocking artifact.
- If motion exposes a source-baked issue, disposition the still as `tighten` and rerender upstream before attempting another motion pass.
- Do not use motion rerenders as anatomy repair.

Backend adoption rule:

- Keep `distilled` using `mlx-community/LTX-2-distilled-bf16` as the baseline motion lane.
- Use Apple-native LTX 2.3 MLX Q8, `apple-ltx23-q8-one-stage` with `dgrauet/ltx-2.3-mlx-q8` and `mlx-community/gemma-3-12b-it-4bit`, as the standard comparison lane in motion contact sheets.
- Treat model or backend wins as beat-level carrier evidence first.
- A single hard-case win does not justify a full-short or full-episode rerender on that backend.
- If a broader comparison reel makes previously rational beats read as nonsense, text drift, or invented causality, mark the reel `diagnostic only` or `reject` and keep the prior baseline as the default lane.
- Legacy rule: keep comparison-only manifests out of the active short namespace. During the restart, `shorts/experiments/` remains blocked unless an exact diagnostic path is DP-approved in the workflow scope manifest.
- When reopening prompts for a new backend family, separate motion briefs into `locked context`, `human/tableau`, and `documentary anomaly` carriers instead of reusing one generic restrained-motion prompt.
- For Apple-native LTX 2.3 human/tableau briefs, use concrete role/blocking clauses and fixed-room/object clauses. Avoid abstract micro-body-motion phrases and chair or seat-negation wording that can trigger generic sit-down behavior or furniture hallucination.

## Legacy Gate: Reel Before Downstream Use

Prerequisites:

- every included clip already has a recorded motion review
- every included clip has a current disposition

Keeper reel rule:

- a keeper reel may contain only `keep` clips

Mixed review reel rule:

- if any included clip is `tighten`, `diagnostic only`, or `reject`, the reel must be labeled `mixed review reel`
- mixed review reels are internal review tools, not promoted selects

No-placeholder rule:

- diagnostic placeholders are never allowed in a keeper reel
- diagnostic placeholders are never allowed in a keeper short or `video final`

## Escalation Rules

Use this escalation order:

1. fix the still if the defect is source-baked
2. tighten camera or anomaly carrier if the mechanism is hidden
3. review the stills/keyframe contact sheet before building a stills video proof when needed
4. rerender motion only after the still is trustworthy
5. review the motion contact sheet and build a shot timing EDL before motion video proof
6. update keeper lessons only after the result is genuinely promotable

If a lane keeps failing for the same named reason, add that failure mode to `judgment/casebook.md` before running a broader sweep.

## Required Review Artifacts

Every still, motion, contact sheet, and video proof review should be recorded in the FluxLab note shape at:

- `/Users/mike/FluxLab_CascadeEffects/proofs/suites/_proof_review_template.md`

Required fields:

- `review_type`
- `gate_level`
- `episode_id`
- `case_id`
- `archetype`
- `source_asset`
- `artifact_path`
- `motion_carrier`
- `carrier_mode`
- `anchor_match`
- `contact_sheet_path`
- `proof_video_path`
- `beat_sheet_path`
- `source_baked_issue`
- `disposition`
- `failure_reason`
- `next_action`

## Registry and Casebook Discipline

- Add every current keeper to `judgment/keeper_registry.md`.
- Add every reusable success or failure lesson to `judgment/casebook.md`.
- Do not promote an asset without both a dispositioned review note and a registry decision.

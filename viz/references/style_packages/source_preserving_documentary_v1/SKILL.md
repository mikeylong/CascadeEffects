---
name: "source_preserving_documentary_v1"
description: "Create scoped visual research packets, source-frame/keyframe boards, source-derived archival reanimation handles, and source-preserving still/motion judgments for Shorts proof gates."
---

# SKILL: Source Preserving Documentary v1

## Intent

Generate restrained source-preserving documentary images that stay readable across many episode types. The subject comes first. The anomaly comes second. Style supports the image instead of replacing it. During the Challenger-first restart, this style package may consume only scoped files and active ledger constraints.

For Cascade Effects YouTube Shorts, this skill owns source-preserving visual generation/reanimation and visual judgment for these stages:

`stills/keyframe contact sheet -> stills video proof when needed -> motion contact sheet -> shot_timing_edl -> motion video proof`

For the Challenger restart, the scoped visual sequence is:

`visual research packet -> production model decision -> visual beatmap -> shot_plan_v2 -> episode constraint ledger -> render authorization check -> stills/keyframe contact sheet -> stills video proof when needed -> motion contact sheet -> shot_timing_edl -> motion video proof`

It does not own `script`, `audio`, or `video final`. Final YouTube Shorts-style caption overlays belong only to [/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_final_export_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_final_export_v1/SKILL.md).

When visual work consumes a Shorts manifest or proof, it must preserve the coordinator-approved audio provenance fields: `short_audio_package_path`, `expected_voice_profile_id`, `audio_package_sha256`, `audio_disposition`, `caption_source_path`, and `transcript_sha256`. Visual agents must not swap audio, transcript, or caption source paths while rendering stills, motion, contact sheets, or proof videos.

## Restart Scope Contract

All prior visual constraints are inactive by default for the Challenger restart. This includes previous Challenger prompts/renders, Hyatt/Therac/737 episode constraints, keeper registry lessons, casebook lessons, subject matrix interpretations, model experiment rules, packaging rules, old manifests, and old proof reviews.

Before still generation, require:

- DP-approved workflow scope manifest
- DP research brief
- archival footage review when archival motion is in scope
- visual research evidence packet
- production model decision and research-driven visual beatmap
- DP-approved episode constraint ledger with `ledger_status: active`
- a recognizable source anchor for every beat or shot, unless DP has approved `nonliteral_exception_approved: true`

Visual context may hydrate only from scoped active roots, exact whitelisted source/audio files, and exact DP-approved imports. Do not read from `/archive/`, `/archives/`, `/experiments/`, `/legacy/`, `/retired/`, `/midjourney/`, `/proof_stills/`, diagnostic outputs, mixed-review outputs, old renders, old manifests, or old constraint/casebook files unless the workflow scope manifest lists the exact DP-approved import path.

This style package can suggest constraint proposals from visual research, but only the DP-approved episode constraint ledger can activate them.
Approved sourced carriers are allowed when the active packet and review docs record `carrier_mode: sourced` or `carrier_mode: hybrid`.
When archival motion is in scope, approved archival clips and stills must also pass `strict clean` hygiene review before they may act as sourced or hybrid carriers.
If an approved sourced archival still, clip, or research crop already solves the shot, do not regenerate it in Flux by default. Generated stills are exception-only when the sourced material does not already provide the needed frame. When archival motion has the strongest visual language but the edit needs a different duration or cadence, use source-derived archival reanimation: clean source span, same-camera keyframes, audited no-audio LTX handle.

`carrier_mode` refers to actual visual media: generated stills, sourced stills/clips, or hybrid composites/reanimations. HTML, CSS, SVG, canvas, and other procedural code are not carrier modes for story visuals. They may wrap, time, caption, lay out, mask, or composite approved visual media, but they must not replace the subject, source anchor, anomaly carrier, or production image surface unless the user explicitly requests a code-native diagnostic mockup.

Paper Architecture visual style is not allowed for Shorts video assets. If a scoped Short asks for or inherits `cascade-paper-architectures-ink-lit-v1`, folded-paper/foam-core source art, paper-model tableaux, or Paper Architecture resemblance for stills, keyframes, motion, proof frames, final frames, cover frames, in-video graphics, or thumbnails, record `paper_architecture_visual_style_read: reject`, keep the asset out of motion/proof/final/package eligibility, and route back to the coordinator/DP for a source-preserving documentary carrier. This does not prohibit the registered Paper Architecture music track or music claim notes.

## Core Rule

Use this style when you want:

- one clear renderable subject or scene
- one dominant contradiction, anomaly, or wrong state
- controlled palette and restrained lighting
- a calm frame with tension inside it

Do not use this style as a license to abstract away subject identity or replace a recognizable research anchor with a generic symbolic prop.

Do not let generated stills collapse into foreground administrative props. Clipboards, binders, folders, paperwork stacks, legal pads, trays, and generic evidence-table objects are low-energy default carriers unless the active DP ledger names the exact object as mechanism-critical and records why a stronger subject/event, room, role-based human scene, or active equipment carrier would weaken the beat. Prefer implied action, anticipation, source-recognizable subjects, layered depth, and motion-ready ambient affordances.

## Model-Facing Grammar

Every prompt should be built from:

1. A concrete renderable subject archetype
2. What must remain recognizable
3. One anomaly or contradiction
4. Palette logic
5. Restrained lighting and mood

Do not add layout coordinates, overlay bands, reserved strips, or design-system language to the prompt.

Do not inherit text, logo, UI, caption, poster, palette, carrier, camera, model, or prompt constraints from legacy docs. Use only the current active ledger. Final YouTube Shorts captions remain owned by the final-export stage.

## Mandatory Judgment Step

Before drafting a prompt, consult the approved workflow scope manifest, DP research brief, archival footage review when present, visual research packet, and active episode constraint ledger. `judgment/subject_render_matrix.md`, `judgment/casebook.md`, and `judgment/keeper_registry.md` are legacy reference libraries unless the active ledger imports exact entries.

You are not done choosing an archetype until you have also chosen:

- what must remain canonical for this subject class
- which recognizable source anchor the viewer should still be able to infer
- what anomaly carrier is allowed
- what anomaly carrier is banned
- what camera logic can actually expose the failure mechanism

If the active ledger or scoped visual research says the current camera or anomaly carrier is high-risk for deformation, rewrite the image problem before rendering. If only a legacy matrix/casebook/keeper entry says so, ask the DP to import or reject it before using it.
If the still concept no longer preserves the named source anchor and now reads like a generic evidence-room object, stop and redesign the carrier. Do not prompt through `anonymous evidence-room drift`.
If archival footage is in scope, do not use a clip or frame span that fails `strict clean`, and do not let generated or hybrid outputs inherit visible logos, stingers, lower-thirds, watermarks, burned captions, end cards, split screens, or channel bugs.

After rendering, consult:

- `judgment/review_rubric.md`
- `judgment/promotion_workflow.md`

Record the result in the FluxLab review-note shape at `/Users/mike/FluxLab_CascadeEffects/proofs/suites/_proof_review_template.md`.

For Shorts, visual review should also produce or reference the current contact-sheet or proof artifact:

- `stills/keyframe contact sheet`: compare beat-level clean candidates, sourced stills, or keyframes directly as raw full-frame tiles in the contact sheet. Keep beat info on the contact-sheet surface as minimal plain-text labels only. A sidecar index may exist as supplemental metadata, but it is not a substitute for on-sheet beat labels on the default review surface. Optional review plates are separate diagnostics, not the default selection surface.
- `stills video proof`: review the static proof only as timing, coverage, and sequence evidence, and verify that it renders from clean selected stills rather than review plates.
- `motion contact sheet`: compare motion candidates or filmstrip grids from selected or `keep` source assets.
- `motion video proof`: review the timed motion proof before any final-export request.

Contact sheets are human-visible selection gates. Video proofs are timing and sequence gates. Neither is a publishable final.

If a visual manifest points to diagnostic audio, legacy audio, a long-form audio package, or a package that does not match the active Shorts voice profile, stop and route back to the coordinator/audio stage before rendering a proof.

## Motion Prompting Notes

Motion prompts must preserve the approved source shot first. That source may be a selected sourced clip, a source-derived keyframe pair, a selected sourced still, or a generated still when generation was actually required. The legacy default baseline lane is `distilled` using `mlx-community/LTX-2-distilled-bf16`. The Apple-native lanes are `apple-ltx23-q8-one-stage` for still-driven I2V and `apple-ltx23-keyframe-dev` for source-derived keyframe reanimation. These backend and matrix rules are inactive until the current episode constraint ledger activates them.

Motion candidates must trace back to selected or `keep` source assets from the stills/keyframe contact sheet, proof process, or archival footage review. For the `motion contact sheet` stage, compare approved motion strategies for the beat: `direct_source_clip`, `source_derived_reanimation`, and `still_driven_i2v` where each was planned upstream. Use a generated-still intermediary only when the sourced material does not already provide the needed still or keyframe surface. Use denser sampling than 1fps when short-lived defects matter, especially for artifacts that may only appear between sparse contact-sheet frames. Every surfaced motion candidate must be reviewed from the actual MP4, not only from a contact-sheet thumbnail or manifest row. For launchpad, plume, vehicle, rigid-geometry, historical machinery, explosion, human/tableau, clinical, or other high-risk beats, require frame-by-frame or near-frame-by-frame inspection before any candidate can be treated as review-ready.
Create a shot-level timing EDL before rendering a motion proof. The EDL must list every actual story shot, parent beat, source span, intended and actual duration, continuity vector, and `no_internal_cut_read`. Normal story shots must be at least `2.0` seconds. A source-native camera/edit cut inside an archival span is a real story cut; it must become its own EDL row or be avoided with a cleaner source span or stable source-frame hold. Do not treat a five-second beat rollup as valid timing evidence if it contains hidden sub-shot edits.
Five-second motion contact handles are diagnostic candidate assets, not automatic edit timing. Downstream proof should use the approved EDL timing: each declared story shot must be at least `2.0` seconds unless explicitly waived, no source-native cut may create an unlisted sub-second flash, and the proof must pass contact-sheet-to-proof parity before final export.
For moving-subject archival sequences, preserve the visible continuity vector. Do not cut from a shuttle, vehicle, machine, person, or process moving forward in altitude, scale, damage, or action state back to an earlier/lower/reset view unless the EDL labels it as an intentional reset. If the source contains fades, dissolves, or camera cuts that produce quick flashes, split them into valid EDL shots or choose a cleaner span.
If human review says a timing repair is not materially different, classify the pass as `reject` rather than `tighten`. The next pass must be an editorial rebuild with stronger source selection and sequence logic, not another incremental duration/crop tweak on the same contact sheet.
For Shorts review, apply a scroll-stopping subject test before promoting a motion or proof pass. If a strong subject/event image exists, it should beat a low-energy hearing room, control room, admin table, foreground clipboard, binder, folder, paperwork stack, or process shot unless the lower-energy carrier is visibly more compelling and the DP records an exception. Narration can carry institutional logic; visuals should carry immediate attention. For Challenger-like footage, shuttle/pad/launch/ascent/failure imagery must dominate over room/process coverage.
Motion candidates are visual-only review assets. If an LTX backend or sourced clip carries audio, record `audio_stream_read`, strip the audio into a `normalized_no_audio_path`, and use only that no-audio file for motion contact sheets or proof assembly. The proof's only audio source is the coordinator-approved short audio package.
When archival footage needs perceived sharpness or cleanup, create a conservative `archival_cleanup_scout` before changing the active motion contact sheet or proof. Compare baseline normalized MP4s with `conservative_clean` FFmpeg outputs, keep full-bleed `9:16`, strip audio, and record `source_resolution`, `crop_width_px`, `upscale_factor`, `enhancement_lane`, `restoration_recipe_id`, `enhancement_read`, `artifact_read`, and `source_limit_read`. Reject cleanup that creates halos, waxy faces, temporal shimmer, crushed shadows, added text/logos, or broken vehicle/human geometry. Do not apply AI upscaling, face restoration, synthetic detail invention, pillarbox/matte framing, or a global modern-HD look unless a later explicit scope approves that experiment.
When archival footage families are active, preserve their approved texture influence only on the beats that explicitly reference those families. Do not apply a global VHS or broadcast degradation pass across the full short unless every beat is explicitly archival/broadcast-linked and DP-approved.
Historical signal texture is a global optional finishing substep for approved archival, broadcast-linked, or period-media-derived Shorts motion, not a Challenger-only rule and not a new top-level production stage. It runs only after the underlying motion handle is `keep`, no-audio, source-clean, and frame-audited. Use `/Users/mike/Viz_CascadeEffects/references/style_packages/source_preserving_documentary_v1/archival_signal_texture_recipes.json` as the profile source of truth. Select the profile by `historical_context_year_or_range`, `source_media_era`, source medium, and beat family: Challenger-style 1980s NASA/TV/news footage uses `era_1980s_broadcast_crt_v1`; Therac-style clinical or institutional footage uses `era_1980s_institutional_video_v1` unless the DP records a stronger broadcast rationale; later episodes use 1990s news, 2000s digital news/web, or 2010s mobile/social profiles as appropriate. Every textured output must stay full-bleed, visual-only, no TV frame, no matte, no rounded mask, no border, and no reduced image area. Record `historical_signal_profile_id`, `historical_context_year_or_range`, `source_media_era`, `texture_source_lane`, `texture_applied_path`, `signal_texture_strength`, `texture_visibility_read`, `era_match_read`, `youtube_survival_proxy_path`, `youtube_survival_read`, `compression_artifact_read`, `detail_survival_read`, and `historical_signal_texture_read` before it can enter proof or final.

When the active ledger authorizes the legacy default motion contact sheet matrix, render:

- two `distilled` candidates and two `apple-ltx23-q8-one-stage` candidates
- the same two seed slots across both model families
- candidate A from the canonical beat motion prompt
- candidate B from a beat-class stability prompt for `locked context`, `human/tableau`, or `documentary anomaly`

Group contact sheets by beat, source asset, model family, prompt variant, and seed. Motion candidate notes must record `beat_id`, `source_still_path` or `source_clip_path`, `source_still_variant_role` when applicable, `motion_pipeline`, `model_repo`, `text_encoder_repo` when applicable, `seed`, `prompt_variant_id`, prompt text or prompt path, raw and normalized clip paths, `review_method`, `temporal_coherence_read`, `physical_plausibility_read`, `source_motion_alignment_read`, disposition, and whether the clip is selected for the motion video proof.

For hard or motion-brittle beats, prepare a primary still plus one alternate motion-ready still before motion generation. Hard beats include `human/tableau`, strict historical geometry, locked-context shots, or any beat where motion has already exposed source-baked defects. Do not require an alternate still for every beat. If both motion model families fail on the same still for the same reason, route back to stills instead of treating motion rerenders as repair. If a still-driven motion candidate invents ignition, plume growth, liftoff, catastrophic deformation, or other event-level motion that is not already implied by the source still, reject it as source-defying motion rather than tightening prompts in place. Launchpad-family beats should usually reroute to direct sourced archival motion instead.
For launch, liftoff, ascent, plume, explosion, or other event-level aerospace motion where LTX is still required, use source-derived keyframe interpolation from clean archival start/end frames in the same continuous camera shot. The keyframes must share crop, scale, camera angle, and source family. Do not use one-stage or distilled single-still I2V to invent these events. Record the source clip span, start/end keyframe paths, keyframe pipeline, and dense frame-audit artifacts before surfacing the candidate.
For human, clinical, office, courtroom, control-room, or role-based historical scenes, source-derived reanimation must preserve role, subject count, posture, room layout, equipment position, and camera setup. Keep motion low-amplitude unless the clean source span supports larger action. Reject invented people, facial identity drift, medical action, sit/stand changes, or room-layout drift.

For Apple-native LTX 2.3 human/tableau beats:

- Write concrete social roles and blocking: exactly who is visible, who remains upright, who remains seated, where each figure stays, and what room state remains fixed.
- Prefer room and object locks: all furniture and fixtures stay fixed in their original positions, no objects enter or leave the frame, camera locked.
- Avoid abstract micro-motion phrases such as `breathing posture`, `shoulder weight shift`, `slight weight shift`, or `subtle body shift`; they can push the model toward generic trained behavior sequences instead of controlled motion.
- Avoid naming chairs or seat-approach actions when the goal is to prevent sitting. Phrases like `does not approach a chair` can cause chair or boardroom furniture hallucination. Use `remains upright in the same spot beside the table` plus fixed-furniture clauses instead.
- If a human/tableau motion pass invents furniture, adds new props, or turns a stable meeting scene into sit/stand action, mark it `reject` or `diagnostic only`; do not promote it without beat-local A/B proof.

## Archetypes vs Modifiers

Archetypes answer:

- what kind of thing is in frame
- at what scale
- in what kind of space

Modifiers answer:

- what is wrong
- how tense or calm the frame feels
- how reduced or realistic the image should be

Keep those roles separate.

## Legacy Style Constraint Library

These dimensions describe the historical style package lineage. They are not active constraints for the restarted Challenger short unless the current episode constraint ledger activates them.

1. Dominant Read
- One main subject or scene state must read immediately.
- Supporting elements may exist, but they must stay subordinate.

2. Recognizable Identity
- The main subject must remain identifiable after simplification.
- Reduction is allowed. Identity loss is not.

3. Single Dominant Anomaly
- Use one dominant wrong condition.
- The rest of the image should stay coherent enough that the anomaly matters.

4. Controlled Output
- Apply only the active ledger's controls for text, logos, UI overlays, poster graphics, collage fragments, motion blur, action spectacle, palette, camera, anomaly carriers, and model routing.

5. Thumbnail Clarity
- The image must still read at small size.

## Soft Constraints

- Asymmetry is useful when it improves clarity, but not mandatory.
- Empty space is useful when it improves legibility, but not as a quota.
- Lighting may be flat, soft, or gently directional as long as it stays restrained.
- Human presence can be absent, incidental, or lightly staged depending on the archetype.

## Anti-Patterns

- abstract composition theory as prompt content
- giant empty fields with a weak subject
- multiple surreal events in one frame
- recent-topic bias baked into the style package
- design language that reads like a poster instead of an image

## Working Method

1. Verify the workflow scope manifest allows every source path in context.
2. Verify the DP research brief and visual research packet provide evidence for the beat.
3. Verify the episode constraint ledger is active and names the constraints that control the prompt.
4. Verify each beat has a recognizable source anchor or DP-approved non-literal exception.
5. If archival footage is in scope, verify the beat’s `preferred_clip_ids`, `footage_family_id`, `archive_reference_mode`, and `texture_influence` against the archival footage review before writing or judging a prompt.
6. Choose `carrier_mode`: `generated`, `sourced`, or `hybrid`. Do not classify CSS/SVG/canvas drawings or HTML proof shells as visual carriers.
7. Pick one archetype from `prompts/archetypes.txt` only if the active ledger allows this style package as a reference.
8. Check `judgment/subject_render_matrix.md` only as a scoped reference; request DP import if it would control the prompt.
9. Pick one or two modifiers from `prompts/modifiers.txt` only if they do not conflict with active ledger constraints.
10. Write the subject in concrete nouns.
11. State what must remain recognizable.
12. State the one anomaly using an allowed carrier for that subject class.
13. Keep the palette and lighting clause short.
14. If the prompt would collapse into an anonymous tray, clipboard, binder, folder, paperwork stack, evidence table, or generic prop, stop and redesign the carrier or switch to a sourced still.
15. If a sourced or hybrid archival result absorbs logos, stingers, lower-thirds, watermarks, burned captions, or channel bugs from reference footage, classify it as `absorbed archival contamination` and reject it.
16. If Paper Architecture visual style appears in a Shorts video asset, reject it as wrong workflow scope before promotion. Website/channel-brand/website-gallery Paper Architecture assets belong to their own workflows, not this Shorts style package.
17. If motion later exposes inherited anatomy or source-baked defects, come back and repair the still before attempting another motion pass.
18. Only promote a still to motion if the still review is `keep` and any required `texture_noise_read` is `pass`.
19. Only promote a clip to motion video proof or final-export eligibility if the motion review is `keep` and any required `texture_noise_read` is `pass`.
20. Do not add new keepers or reusable lessons as active constraints; propose them for DP ledger review instead.

If a proof comes back with warped geometry, broken anatomy, or deformation that reads as sampler damage, mark it as a reject even if the anomaly is more legible.

## Output Contract

This skill produces visual candidates, contact-sheet review notes, proof review notes, and promotion recommendations. It returns paths and dispositions to the Shorts coordinator; it does not set coordinator `may_advance` and it does not export captioned finals.

Expected handoff fields:

- `stage`: `stills/keyframe contact sheet|motion contact sheet|stills video proof|motion video proof`
- `workflow_scope_manifest_path`
- `dp_research_brief_path`
- `episode_constraint_ledger_path`
- `exact_dp_imports_used`
- `carrier_mode`
- `anchor_match`
- `hygiene_read`
- `generation_surface_read`
- `texture_noise_read`
- `contact_sheet_path`
- `proof_video_path`
- `review_note_path`
- `historical_context_year_or_range`
- `source_media_era`
- `historical_signal_profile_id`
- `texture_applied_path`
- `youtube_survival_read`
- `compression_artifact_read`
- `detail_survival_read`
- `historical_signal_texture_read`
- `paper_architecture_visual_style_read`
- `texture_visibility_read`
- `era_match_read`
- `texture_visibility_read`
- `era_match_read`
- `disposition`
- `blockers`
- `next_action`

## Edge Cases

- If workflow scope manifest, DP research brief, visual research evidence, or active episode constraint ledger is missing, stop before still generation.
- If archival motion is in scope and the archival footage review is missing, stale, or unresolved, stop before still generation.
- If a prompt or review needs a legacy reference, request DP import for the exact file before using it.
- If a proof shell uses HTML/CSS/SVG/canvas to draw the story subject or anomaly instead of wrapping approved generated, sourced, or hybrid media, classify it as `diagnostic_only` and route back to visual carrier selection before promotion.
- If Paper Architecture appears in a Shorts video asset, reject it before texture QA. For allowed non-Paper-Architecture Cascade Effects brand-generated art, high-frequency speckle, grain, grit, sandy/noisy surfaces, texture-heavy rendering, or texture that competes with the anchor requires `texture_noise_read: tighten|reject` and blocks promotion until repaired.
- If the named source anchor cannot survive generation cleanly, use a sourced carrier or route back to visual research instead of hiding the failure inside a more abstract prop.
- If a contact sheet reads like an unrecognizable evidence room, classify the failure as `anonymous evidence-room drift` and reopen the carrier decision.
- If a sourced or hybrid archival output carries logos, stingers, lower-thirds, end cards, watermarks, split screens, or burned captions, classify the failure as `absorbed archival contamination` and reopen the source span or carrier choice.
- If a styled review plate, framed proof proxy, blurred-fill tile, or any other embellished review artifact enters generation or proof as if it were a clean still, classify the failure as `review-surface contamination` and reopen the clean-source path. Raw full-frame contact-sheet tiles built directly from clean candidates are acceptable review surfaces.
- If a generated still or motion clip contains readable text, UI overlays, logo leakage, or poster-like graphics, mark it as defective rather than treating it as caption-ready.
- If motion exposes a still defect, route back to stills before another motion pass.
- If a new backend succeeds on one beat, keep it beat-local until it wins comparison review.
- If a proof is useful for diagnosis but includes non-`keep` clips, label it mixed review and do not treat it as final-export input.

## Example

Request:

> Review this Challenger motion contact sheet and decide what can enter the motion video proof.

Expected behavior:

- verify each motion candidate traces back to a selected or `keep` still
- mark text leakage, anatomy corruption, source-baked defects, or temporal artifacting as blockers
- return beat-level dispositions and the contact sheet path to the Shorts coordinator
- do not create caption overlays or a video final

## Success Criteria

An image is valid for `source_preserving_documentary_v1` when:

- the subject reads immediately
- the named source anchor or scene family is still inferable
- the anomaly reads clearly
- the anomaly reads as a believable wrong state rather than model corruption
- the frame is restrained rather than spectacular
- the image could belong to many different episodes without changing the style family

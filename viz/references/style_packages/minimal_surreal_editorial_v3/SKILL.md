---
name: "minimal_surreal_editorial_v3"
description: "Generate and judge restrained Cascade Effects stills and motion candidates for Shorts contact sheets and video proof gates."
---

# SKILL: Minimal Surreal Editorial Composition v3

## Intent

Generate restrained documentary-surreal images that stay readable across many episode types. The subject comes first. The anomaly comes second. Style supports the image instead of replacing it.

For Cascade Effects YouTube Shorts, this skill owns visual generation and visual judgment for these stages:

`stills contact sheet -> stills video proof -> motion contact sheet -> motion video proof`

It does not own `script`, `audio`, or `video final`. Final YouTube Shorts-style caption overlays belong only to [/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_final_export_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_final_export_v1/SKILL.md).

When visual work consumes a Shorts manifest or proof, it must preserve the coordinator-approved audio provenance fields: `short_audio_package_path`, `expected_voice_profile_id`, `audio_package_sha256`, `audio_disposition`, `caption_source_path`, and `transcript_sha256`. Visual agents must not swap audio, transcript, or caption source paths while rendering stills, motion, contact sheets, or proof videos.

## Core Rule

Use this style when you want:

- one clear renderable subject or scene
- one dominant contradiction, anomaly, or wrong state
- controlled palette and restrained lighting
- a calm frame with tension inside it

Do not use this style as a license to abstract away subject identity.

## Model-Facing Grammar

Every prompt should be built from:

1. A concrete renderable subject archetype
2. What must remain recognizable
3. One anomaly or contradiction
4. Palette logic
5. Restrained lighting and mood

Do not add layout coordinates, overlay bands, reserved strips, or design-system language to the prompt.

Do not add final caption text, YouTube Shorts captions, readable labels, UI overlays, logos, poster graphics, or caption-safe design instructions to generated still or motion prompts. Text leakage in generated visuals remains a defect even though approved final captions may be added later in the final-export stage.

## Mandatory Judgment Step

Before drafting a prompt, consult `judgment/subject_render_matrix.md`.

You are not done choosing an archetype until you have also chosen:

- what must remain canonical for this subject class
- what anomaly carrier is allowed
- what anomaly carrier is banned
- what camera logic can actually expose the failure mechanism

If the matrix says the current camera or anomaly carrier is high-risk for deformation, rewrite the image problem before rendering.

After rendering, consult:

- `judgment/review_rubric.md`
- `judgment/promotion_workflow.md`

Record the result in the FluxLab review-note shape at `/Users/mike/FluxLab_CascadeEffects/proofs/suites/_proof_review_template.md`.

For Shorts, visual review should also produce or reference the current contact-sheet or proof artifact:

- `stills contact sheet`: compare beat-level still candidates and choose current best stills or named gaps.
- `stills video proof`: review the static proof only as timing, coverage, and sequence evidence.
- `motion contact sheet`: compare motion candidates or filmstrip grids from selected or `keep` stills.
- `motion video proof`: review the timed motion proof before any final-export request.

Contact sheets are human-visible selection gates. Video proofs are timing and sequence gates. Neither is a publishable final.

If a visual manifest points to diagnostic audio, legacy audio, a long-form audio package, or a package that does not match the active Shorts voice profile, stop and route back to the coordinator/audio stage before rendering a proof.

## Motion Prompting Notes

Motion prompts must preserve the approved still first. The default baseline lane is `distilled` using `mlx-community/LTX-2-distilled-bf16`. The standard comparison lane is `apple-ltx23-q8-one-stage` using `dgrauet/ltx-2.3-mlx-q8` plus `mlx-community/gemma-3-12b-it-4bit`. Apple-native LTX 2.3 remains beat-local until it wins beat-local review; one backend win does not authorize a full-short or episode-wide model swap.

Motion candidates must trace back to selected or `keep` stills from the stills contact sheet/proof process. Use denser sampling than 1fps when short-lived defects matter, especially for artifacts that may only appear between sparse contact-sheet frames.

For each eligible source still, render the default motion contact sheet matrix:

- two `distilled` candidates and two `apple-ltx23-q8-one-stage` candidates
- the same two seed slots across both model families
- candidate A from the canonical beat motion prompt
- candidate B from a beat-class stability prompt for `locked context`, `human/tableau`, or `documentary anomaly`

Group contact sheets by beat, source still, model family, prompt variant, and seed. Motion candidate notes must record `beat_id`, `source_still_path`, `source_still_variant_role`, `motion_pipeline`, `model_repo`, `text_encoder_repo` when applicable, `seed`, `prompt_variant_id`, prompt text or prompt path, raw and normalized clip paths, disposition, and whether the clip is selected for the motion video proof.

For hard or motion-brittle beats, prepare a primary still plus one alternate motion-ready still before motion generation. Hard beats include `human/tableau`, strict historical geometry, locked-context shots, or any beat where motion has already exposed source-baked defects. Do not require an alternate still for every beat. If both motion model families fail on the same still for the same reason, route back to stills instead of treating motion rerenders as repair.

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

## Hard Constraints

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
- No text, logos, UI overlays, poster graphics, or noisy collage fragments.
- No motion blur or action spectacle.

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

1. Pick one archetype from `prompts/archetypes.txt`.
2. Check the matching row in `judgment/subject_render_matrix.md`.
3. Pick one or two modifiers from `prompts/modifiers.txt`.
4. Write the subject in concrete nouns.
5. State what must remain recognizable.
6. State the one anomaly using an allowed carrier for that subject class.
7. Keep the palette and lighting clause short.
8. If motion later exposes inherited anatomy or source-baked defects, come back and repair the still before attempting another motion pass.
9. Only promote a still to motion if the still review is `keep`.
10. Only promote a clip to motion video proof or final-export eligibility if the motion review is `keep`.
11. Add new keepers and unresolved lanes to `judgment/keeper_registry.md`.
12. Add reusable lessons to `judgment/casebook.md`.

If a proof comes back with warped geometry, broken anatomy, or deformation that reads as sampler damage, mark it as a reject even if the anomaly is more legible.

## Output Contract

This skill produces visual candidates, contact-sheet review notes, proof review notes, and promotion recommendations. It returns paths and dispositions to the Shorts coordinator; it does not set coordinator `may_advance` and it does not export captioned finals.

Expected handoff fields:

- `stage`: `stills contact sheet|motion contact sheet|stills video proof|motion video proof`
- `contact_sheet_path`
- `proof_video_path`
- `review_note_path`
- `disposition`
- `blockers`
- `next_action`

## Edge Cases

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

An image is valid for v3 when:

- the subject reads immediately
- the anomaly reads clearly
- the anomaly reads as a believable wrong state rather than model corruption
- the frame is restrained rather than spectacular
- the image could belong to many different episodes without changing the style family

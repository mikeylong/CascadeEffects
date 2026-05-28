# ComfyUI / FLUX Workflow Spec v3

## Purpose

This spec is for subject-first documentary-surreal generation. The model should be given concrete image problems, not abstract composition ideology.

## Graph Layout

1. Load checkpoint
2. CLIP text encode positive
3. CLIP text encode negative
4. Empty latent image
5. KSampler
6. VAE decode
7. Save image

Optional:

8. Load image for hidden subject/composition guidance
9. Resize or crop guide image
10. IPAdapter or composition reference node
11. Conditioning combine

## Recommended Baseline

1. Model
- FLUX Dev for quality
- FLUX Schnell for faster prompt iteration

2. Resolution
- 1024 x 1024 for square exploration
- 1024 x 1280 for portrait
- 1024 x 1792 for 9:16 vertical exploration
- 1536 x 864 for widescreen

3. Steps
- 24 to 32

4. CFG / guidance
- 3.5 to 5.5
- Keep guidance moderate so the image does not overcook into decorative detail

5. Seed strategy
- Lock seed while tuning wording
- Unlock seed only after the subject and anomaly both read clearly

## Prompt Recipe

Build prompts in this order:

1. Concrete subject archetype
2. What must remain recognizable
3. One anomaly or contradiction
4. Palette logic
5. Restrained lighting and mood

Before writing step 3, consult `../judgment/subject_render_matrix.md` for the relevant archetype.

After rendering, use `../judgment/review_rubric.md` and `../judgment/promotion_workflow.md` before deciding whether to rerender, animate, or assemble the result.

## Prompt Rules

- Use concrete nouns before style adjectives.
- Use one anomaly only.
- Keep the prompt short enough that the model can hold the whole idea.
- Preserve canonical subject identity before adding contradiction.
- If you need layout control, state it in ordinary visual language such as `close object portrait`, `wide room view`, or `frontal exterior`, not coordinates or quotas.
- Do not prompt reserved bands, overlay geometry, frame strips, or abstract design instructions.
- Do not prompt negative-space percentages.
- Do not force off-center placement unless the subject clearly benefits from it.
- Do not ask the model to hide the failure mechanism behind a camera angle that cannot show it.
- Do not use macro-shape deformation as a shortcut for anomaly.

## Master Prompt Anchor

Use `prompts/master_prompt.txt` as the style anchor, then append one archetype and one to three modifiers.

## Archetype Use

Choose exactly one base archetype from `prompts/archetypes.txt`.

Examples:

- `single_object_or_device`
- `single_human_figure`
- `room_or_interior`
- `vehicle_vessel_or_aircraft`

Then check the archetype row in `../judgment/subject_render_matrix.md` before drafting the anomaly clause.

## Modifier Use

Choose one modifier from each category only if it improves clarity:

- anomaly mode
- emotional temperature
- reduction level
- palette discipline
- human-presence level
- realism level

Editorial meanings such as `aftermath`, `official_normalcy`, or `latent_failure` should be expressed as modifiers attached to a renderable scene, never as the scene category itself.

## Subject-Class Stop Conditions

Stop and rewrite the prompt before rendering when any of these are true:

- the anomaly requires bending, warping, or damaging the canonical body of the subject to read
- the chosen camera makes the claimed wrong-state cue invisible
- the contradiction is only expressible as vague atmosphere rather than a physical cue
- the prompt asks a complex system subject to stay recognizable while also distorting the very geometry that makes it recognizable

High-risk examples:

- full-aircraft “wrongness” that depends on fuselage or tail deformation
- elegant architecture with a hidden structural issue that is not visible at the chosen camera distance
- machine prompts where the whole device is asked to mutate instead of carrying a localized wrong-state cue

Preferred escalation order:

1. keep the subject class and tighten the camera
2. keep the camera and change the anomaly carrier to a more localized cue
3. move to a subsystem or detail view
4. only then change seed or model settings

Do not keep rerendering the same structurally bad image problem.
Do not use motion rerenders as anatomy repair. If the still carries bad hands, faces, or body-adjacent corruption into motion, fix the still first and then reanimate.

## Promotion After Render

Use this sequence:

1. still review
2. motion review
3. reel review

Rules:

- only `keep` stills may advance to motion
- only `keep` motion clips may advance into keeper reels
- any reel containing `tighten`, `diagnostic only`, or `reject` clips must be labeled as a mixed review reel
- record each review in `/Users/mike/FluxLab_CascadeEffects/proofs/suites/_proof_review_template.md`

## Negative Prompt

Use `prompts/negatives.txt` as the default negative list.

## Example Assembly

Pattern:

`[master prompt] + [archetype] + [recognizable subject clause] + [one anomaly clause] + [palette clause] + [lighting clause]`

Good:

- `single_object_or_device, hospital radiotherapy machine remains clearly recognizable, one wrong internal glow at the seam, off-white and steel palette with one restrained red signal, flat clinical light`
- `room_or_interior, airport departure hall remains legible as a public terminal, one impossible destination-board blank zone, weathered neutrals with one amber signal, restrained institutional light`

Bad:

- prompt packed with layout theory, brand language, reserved bands, and palette quotas
- prompt that describes five symbolic ideas but not what is actually in frame
- prompt whose only readable anomaly would require the model to corrupt the subject

## Batch Exploration Matrix

1. Same subject, same seed, anomaly changes
2. Same subject, same anomaly, camera distance changes
3. Same subject, same anomaly, reduction level changes
4. Same subject, same anomaly, palette temperature changes

When a proof fails, use `judgment/review_rubric.md` to label it as `keep`, `tighten`, `diagnostic only`, or `reject` before deciding the next render move.

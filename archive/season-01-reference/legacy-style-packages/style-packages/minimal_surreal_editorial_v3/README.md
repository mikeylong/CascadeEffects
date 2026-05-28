# Minimal Surreal Editorial Package v3

`minimal_surreal_editorial_v3` is a clean-start experimental contract for reusable documentary-surreal image generation across the full episode slate.

This package is intentionally separate from earlier versions:

- `minimal_surreal_editorial` is frozen as historical v1.
- `minimal_surreal_editorial_v2` is frozen as an intermediate experiment.
- `minimal_surreal_editorial_v3` is the current draft reset.

## Design Intent

v3 is built around a simple rule:

- renderable subject archetypes are the base vocabulary
- editorial meaning is added through modifiers
- prompts should stay concrete, short, and model-friendly

The generator should be told what is in frame, what must remain recognizable, and what one thing is wrong. It should not be asked to solve abstract layout theory.

## Anti-Confusion Rules

- `reference inputs` means generation inputs only: source photos, boards, subject plates, composition guides, or other assets used to steer generation.
- `generated outputs` means images produced by a model: drafts, candidate stills, approved stills, or final exported assets.
- Files in this style package are contract and guidance files only. They are not generated outputs.
- This package does not adopt itself into any lane automatically.

## Adoption Status

- No existing workflow spec, generated manifest, short package, or episode package should be switched to `v3` in this pass.
- A later adoption pass must update specs deliberately if `v3` is approved.

## Package Layout

- `SKILL.md`: human-readable style guidance
- `visual.contract.json`: structured contract for the style
- `judgment/subject_render_matrix.md`: archetype-by-archetype rules for preserving subjects while carrying anomaly
- `judgment/casebook.md`: proof-backed examples of what worked, what needed tightening, and what failed
- `judgment/review_rubric.md`: human review checklist and disposition rules
- `judgment/promotion_workflow.md`: still -> motion -> reel gate logic and escalation rules
- `judgment/keeper_registry.md`: current keepers, tighten queue, and unresolved lanes
- `prompts/master_prompt.txt`: shortest generator-facing style anchor
- `prompts/negatives.txt`: default negative terms
- `prompts/archetypes.txt`: renderable subject classes
- `prompts/modifiers.txt`: attachable style/state controls
- `prompts/examples.txt`: cross-domain prompt examples
- `comfyui/workflow-spec.md`: prompt recipe and FLUX/Comfy usage
- `eval/evaluator-spec.json`: evaluation weights and hard fails
- `eval/sample-score-output.json`: sample evaluator payload
- `eval/starter_evaluator.py`: starter evaluator scaffold

## Judgment Layer

v3 now includes a subject-render judgment layer. Use it before writing prompts, not after the model has already drifted.

- `judgment/subject_render_matrix.md` tells you how each archetype should carry anomaly without losing canonical identity.
- `judgment/casebook.md` shows proof-backed examples from recent Challenger, Therac-25, Hyatt Regency, and 737 MAX runs.
- `judgment/review_rubric.md` defines the keep / tighten / diagnostic only / reject decision rules.
- `judgment/promotion_workflow.md` defines what may advance from still to motion and from motion to reel use.
- `judgment/keeper_registry.md` records the current promoted examples and unresolved lanes.

The point of this layer is to prevent repeated failure modes across the full episode slate:

- subject deformation masquerading as surrealism
- camera choices that hide the actual mechanism of failure
- anomaly cues that read as sampler corruption instead of believable wrong-state conditions

FluxLab proof notes should mirror this same disposition vocabulary so review state is consistent across stills, motion clips, and reels.

## Compatibility Note

The linked style profile still carries `caption_safe_defaults` for pipeline compatibility. In v3, that field is downstream frame-safety metadata, not generator-facing prompt guidance.
